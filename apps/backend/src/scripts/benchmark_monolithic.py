#!/usr/bin/env python3
"""Benchmark v2 orchestrator — Arms A & B (monolithic generation).

Arm A: one call per job — topic prompt → complete Manim script. No GCO, no
validation, no repair, no retries (infrastructure retries only).

Arm B: same generation as A, then the SAME AST sanitizer + compile check used
by the council wraps the script; on failure the model is asked to repair the
FULL script with SEARCH/REPLACE blocks, bounded by the same attempt limit as
the council's per-scene loop (settings.animation_review_max_iterations).

Both arms:
- Read their (topic, model, arm, rep) tuples from the pre-registered manifest.
- Skip tuples already recorded in the outcomes journal (resumable).
- Persist per-call JSONL traces via infra.ai.trace (same schema as Arm C).
- Write one outcome JSON per job under <trace-dir>/outcomes/.

Usage:
  python3 scripts/benchmark_monolithic.py --manifest <jobs.csv> --arm A \
      [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

PROMPT_TEMPLATE = (
    "Create a complete, executable Manim CE Python script for a single-scene "
    "educational animation that teaches: {topic}.\n"
    "Requirements:\n"
    "- One Scene class subclassing manim.Scene with a construct() method.\n"
    "- The animation must be self-contained and runnable as-is.\n"
    "- Output ONLY Python code, no prose."
)

REPAIR_INSTRUCTIONS = (
    "The previous script failed validation. Fix it and output the FULL corrected "
    "script as Python code only. Use one or more SEARCH/REPLACE blocks in this format:\n"
    "<<<<<<< SEARCH\n[exact lines to replace]\n=======\n[corrected lines]\n>>>>>>> REPLACE\n\n"
    "Validation errors:\n{errors}"
)


def sha(text: str | None) -> str | None:
    return hashlib.sha256(text.encode()).hexdigest()[:16] if text else None


def load_manifest(manifest_path: Path, arm: str) -> list[dict[str, str]]:
    with manifest_path.open(newline="") as f:
        return [r for r in csv.DictReader(f) if r["arm"] == arm]


def outcomes_dir(trace_dir: Path) -> Path:
    d = trace_dir / "outcomes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def already_done(out_dir: Path, seq: int) -> bool:
    return (out_dir / f"job-{seq}.json").exists()


async def call_llm(model_id: str, prompt: str) -> tuple[str | None, dict[str, object], float]:
    """One completion via the Nano GPT OpenAI-compatible API. Returns (text, usage, latency_ms)."""
    import time

    import httpx

    from infra.settings import get_settings

    settings = get_settings()
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": settings.benchmark_temperature,
    }
    if settings.benchmark_seed is not None:
        body["seed"] = settings.benchmark_seed
    headers = {"Authorization": f"Bearer {settings.nano_api_key}"}
    usage: dict[str, object] = {}
    text = None
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(
                "https://nano-gpt.com/api/v1/chat/completions", json=body, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
        except Exception as e:  # noqa: BLE001
            usage = {"error": f"{type(e).__name__}: {e}"}
    return text, usage, (time.perf_counter() - t0) * 1000.0


def extract_code(response: str | None) -> str | None:
    """Strip markdown fences if the model wrapped the code."""
    if not response:
        return None
    if "```" in response:
        parts = response.split("```")
        for raw in parts[1::2]:
            part = raw.removeprefix("python\n").removeprefix("python\r\n")
            if "class " in part and "def construct" in part.replace(" ", ""):
                return part
        return parts[1].removeprefix("python\n") if len(parts) > 1 else response
    return response


def validate_script(code: str) -> list[str]:
    """Same checks the council's validator applies, minus vision: AST parse +
    structural requirements (Scene subclass, construct method)."""
    import ast

    errors: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if not any(
        any(
            (getattr(b, "id", None) == "Scene" or getattr(b, "attr", None) == "Scene")
            for b in n.bases
        )
        for n in classes
    ):
        errors.append("no Scene subclass found")
    if not any(n.name in {"construct", "construct(self)"} for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        errors.append("no construct() method found")
    return errors


async def apply_repair(model_id: str, code: str, errors: list[str]) -> tuple[str | None, dict[str, object], float]:
    """One repair turn: ask the model to fix the full script.

    Returns (fixed_code, usage, latency_ms).
    """
    prompt = REPAIR_INSTRUCTIONS.format(errors="\n".join(errors)) + "\n\nCurrent script:\n" + code
    text, usage, latency = await call_llm(model_id, prompt)
    return extract_code(text), usage, latency


def append_trace(trace_dir: Path, record: dict[str, object]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    run_id = os.environ.get("BENCH_RUN_ID") or datetime.now(UTC).strftime("bench-%Y%m%d-%H%M%S")
    with (trace_dir / f"{run_id}.jsonl").open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")


async def run_one(row: dict[str, str], arm: str, trace_dir: Path, max_attempts: int, dry_run: bool) -> dict[str, object]:
    seq = int(row["job_seq"])
    out = outcomes_dir(trace_dir) / f"job-{seq}.json"
    topic = row["topic"]
    model = row["model"]

    if dry_run:
        return {"job_seq": seq, "status": "dry-run", "arm": arm, "model": model, "topic": topic}

    prompt = PROMPT_TEMPLATE.format(topic=topic)
    text, usage, latency = await call_llm(model, prompt)
    code = extract_code(text)
    append_trace(trace_dir, {
        "ts": datetime.now(UTC).isoformat(), "arm": arm, "rep": int(row["rep"]),
        "topic": topic, "model": model, "stage": "generate", "attempt": 1,
        "job_seq": seq, "prompt_sha256": sha(prompt), "prompt_chars": len(prompt),
        "response_sha256": sha(text), "temperature": os.environ.get("BENCH_TEMPERATURE"),
        "latency_ms": round(latency, 1), **{k: v for k, v in usage.items() if k != "error"},
    })

    if arm == "A":
        outcome = {
            "job_seq": seq, "arm": arm, "rep": int(row["rep"]), "topic": topic, "model": model,
            "status": "completed" if code and not validate_script(code) else "failed",
            "first_pass": code is not None and not validate_script(code or ""),
            "validation_errors": validate_script(code) if code else ["no code returned"],
            "attempts": 1,
        }
        out.write_text(json.dumps(outcome, indent=2) + "\n")
        return outcome

    # Arm B: validate → repair loop with the council's attempt bound.
    errors = validate_script(code or "")
    first_pass_ok = code is not None and not errors
    attempts = 1
    while errors and attempts < max_attempts:
        attempts += 1
        fixed, usage, latency = await apply_repair(model, code or "", errors)
        append_trace(trace_dir, {
            "ts": datetime.now(UTC).isoformat(), "arm": arm, "rep": int(row["rep"]),
            "topic": topic, "model": model, "stage": "repair", "attempt": attempts,
            "job_seq": seq, "prompt_sha256": sha(REPAIR_INSTRUCTIONS.format(errors="\n".join(errors))),
            "response_sha256": sha(fixed), "temperature": os.environ.get("BENCH_TEMPERATURE"),
            "latency_ms": round(latency, 1), **{k: v for k, v in usage.items() if k != "error"},
        })
        code = fixed
        errors = validate_script(code or "")

    outcome = {
        "job_seq": seq, "arm": arm, "rep": int(row["rep"]), "topic": topic, "model": model,
        "status": "completed" if code and not errors else "failed",
        "first_pass": first_pass_ok,
        "validation_errors": errors,
        "attempts": attempts,
    }
    out.write_text(json.dumps(outcome, indent=2) + "\n")
    return outcome


async def main_async(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.exit(f"manifest not found: {manifest_path}")
    trace_dir = Path(args.trace_dir) if args.trace_dir else REPO / "reports" / "monolithic"
    out_dir = outcomes_dir(trace_dir)

    from infra.settings import get_settings

    settings = get_settings()
    if settings.benchmark_temperature is not None:
        os.environ.setdefault("BENCH_TEMPERATURE", str(settings.benchmark_temperature))
    max_attempts = 10  # council parity: settings.animation_review_max_iterations

    rows = [r for r in load_manifest(manifest_path, args.arm) if not already_done(out_dir, int(r["job_seq"]))]
    if args.limit:
        rows = rows[: args.limit]
    print(f"{len(rows)} pending arm-{args.arm} jobs")

    sem = asyncio.Semaphore(args.parallelism)

    async def bounded(row: dict[str, str]) -> dict[str, object]:
        async with sem:
            return await run_one(row, args.arm, trace_dir, max_attempts, args.dry_run)

    outcomes = await asyncio.gather(*(bounded(r) for r in rows))
    done = sum(1 for o in outcomes if o.get("status") == "completed")
    print(f"completed {done}/{len(outcomes)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--arm", required=True, choices=["A", "B"])
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--trace-dir", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
