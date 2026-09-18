#!/usr/bin/env python3
"""Benchmark orchestrator v2 (Arms A/B — multi-scene, must-render).

Re-run of Arms A/B matched to Arm C's task: generate a MULTI-SCENE Manim
script, then RENDER it. A video artifact is required for `completed`.

Differences from v1 (bench-20260913):
- Prompt requires multiple scenes (default 5-10, matching the council's
  storyboard practice: C jobs average 7.5 scenes).
- Every job is rendered with the same sandboxed Manim engine Arm C uses
  (podman/docker manimcommunity image, local fallback).
- `completed` requires a rendered video file, not merely a parseable script.
- Collects the same artifacts as Arm C: generated code, video, tokens,
  latency, validation/render errors.

Resumable via per-job outcome files (traces/outcomes_v2/job-<seq>.json).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from infra.engines.sandbox import LocalSandbox

REPO = Path(__file__).resolve().parent.parent  # apps/backend
sys.path.insert(0, str(REPO / "src"))

PROMPT_TEMPLATE = (
    "Create a complete, executable Manim CE Python script for an educational "
    "animation that teaches: {topic}.\n"
    "Requirements:\n"
    "- Exactly ONE Scene class named SceneGen subclassing manim.Scene with a "
    "construct(self) method.\n"
    "- The construct() method must present MULTIPLE distinct scenes "
    "({min_scenes}-{max_scenes}), one per lesson step, ordered from first "
    "principles toward the final concept. Separate scenes with self.clear().\n"
    "- Each scene must be substantial: introduce objects, animate them with "
    "multiple self.play() calls, and remove or transform them before the next "
    "scene begins. No near-empty scenes.\n"
    "- Each scene must teach one step and build on the previous scene's ideas.\n"
    "- Use only Manim Community v0.20.1 classes. Color constants are UPPERCASE "
    "(RED, BLUE, ...).\n"
    "- The script must be self-contained, runnable as-is, and free of syntax "
    "errors.\n"
    "- Output ONLY Python code, no prose."
)

REPAIR_INSTRUCTIONS = (
    "The previous script failed with the error(s) below. Fix it and output the "
    "FULL corrected script as Python code only. Keep ALL scenes; do not drop "
    "scenes to make the error go away. Use one or more SEARCH/REPLACE blocks in "
    "this format:\n"
    "<<<<<<< SEARCH\n[exact lines to replace]\n=======\n[corrected lines]\n"
    ">>>>>>> REPLACE\n\n"
    "Validation/render errors:\n{errors}"
)


def sha(text: str | None) -> str | None:
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest()[:16] if text else None


def load_topic_prompts(manifest_path: Path) -> dict[str, str]:
    data = json.loads((manifest_path.parent / "topics.json").read_text())
    return {t["manifest_topic"]: t["topic_prompt"] for t in data["topics"]}


def load_manifest(manifest_path: Path, arm: str) -> list[dict[str, str]]:
    with manifest_path.open(newline="") as f:
        return [r for r in csv.DictReader(f) if r["arm"] == arm]


def outcomes_dir(trace_dir: Path) -> Path:
    d = trace_dir / "outcomes_v2"
    d.mkdir(parents=True, exist_ok=True)
    return d


def extract_code(response: str | None) -> str | None:
    if not response:
        return None
    if "```" in response:
        parts = response.split("```")
        for raw in parts[1::2]:
            part = raw.removeprefix("python\n").removeprefix("python\r\n")
            if "class " in part and "construct" in part.replace(" ", ""):
                return part
        return parts[1].removeprefix("python\n") if len(parts) > 1 else response
    return response


def validate_script(code: str) -> list[str]:
    """Structural checks: AST parse, at least 2 Scene subclasses, construct()."""
    import ast

    errors: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    scene_classes = [
        n
        for n in classes
        if any(
            getattr(b, "id", None) in {"Scene", "ThreeDScene"}
            or getattr(b, "attr", None) in {"Scene", "ThreeDScene"}
            for b in n.bases
        )
    ]
    if len(scene_classes) != 1:
        errors.append(
            f"expected exactly 1 Scene class named SceneGen, found {len(scene_classes)}"
        )
    for n in scene_classes:
        if not any(
            isinstance(f, ast.FunctionDef) and f.name == "construct" for f in n.body
        ):
            errors.append(f"{n.name} has no construct() method")
    return errors


async def call_llm(
    model_id: str, prompt: str
) -> tuple[str | None, dict[str, object], float]:
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
    async with httpx.AsyncClient(timeout=900.0) as client:
        try:
            resp = await client.post(
                "https://nano-gpt.com/api/v1/chat/completions",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
        except Exception as e:  # noqa: BLE001
            usage = {"error": f"{type(e).__name__}: {e}"}
    return text, usage, (time.perf_counter() - t0) * 1000.0


def append_trace(trace_dir: Path, record: dict[str, object]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    run_id = os.environ.get("BENCH_RUN_ID") or datetime.now(UTC).strftime(
        "bench-%Y%m%d-%H%M%S"
    )
    with (trace_dir / f"{run_id}.jsonl").open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _trace_base(
    r: dict[str, str], seq: int, arm: str, topic: str, model: str, attempt: int
) -> dict[str, object]:
    return {
        "ts": datetime.now(UTC).isoformat(),
        "arm": arm,
        "rep": int(r["rep"]),
        "topic": topic,
        "model": model,
        "stage": "generate",
        "attempt": attempt,
        "job_seq": seq,
        "prompt_sha256": sha(r.get("_prompt", "")),
        "response_sha256": sha(r.get("_response")),
        "temperature": os.environ.get("BENCH_TEMPERATURE"),
    }


async def run_one(  # noqa: PLR0912, PLR0915 — linear per-job benchmark step
    row: dict[str, str],
    arm: str,
    trace_dir: Path,
    max_attempts: int,
    dry_run: bool,
    topic_prompts: dict[str, str],
    min_scenes: int,
    sandbox: LocalSandbox,
) -> dict[str, object]:
    seq = int(row["job_seq"])
    out = outcomes_dir(trace_dir) / f"job-{seq}.json"
    if out.exists():
        return cast("dict[str, object]", json.loads(out.read_text()))  # resumable

    topic = row["topic"]
    model = row["model"]
    topic_prompt = topic_prompts.get(topic, topic)
    if dry_run:
        return {
            "job_seq": seq,
            "arm": arm,
            "model": model,
            "topic": topic,
            "status": "dry-run",
        }

    prompt = PROMPT_TEMPLATE.format(
        topic=topic_prompt, min_scenes=min_scenes, max_scenes=min_scenes + 5
    )
    code = None
    errors: list[str] = []
    first_pass = False
    attempts = 0
    http_error = None
    render_error = None
    video_relpath = None
    status = "failed"
    job_dir = trace_dir / "renders" / f"job-{seq}"

    while attempts < max_attempts:
        attempts += 1
        text, usage, latency = await call_llm(model, prompt)
        http_error = usage.pop("error", None) if "error" in usage else None
        code = extract_code(text)
        append_trace(
            trace_dir,
            {
                **_trace_base(row, seq, arm, topic, model, attempts),
                "prompt_sha256": sha(prompt),
                "prompt_chars": len(prompt),
                "response_sha256": sha(text),
                "latency_ms": round(latency, 1),
                "error": http_error,
                **usage,
            },
        )
        if not code:
            errors = ["no code returned"]
            if arm == "A":
                break
            prompt = (
                REPAIR_INSTRUCTIONS.format(errors="no code was returned")
                + "\n\nCurrent script:\n"
                + (code or "")
            )
            continue

        errors = validate_script(code)
        if errors:
            if arm == "A":
                break  # no repair in Arm A
            prompt = (
                REPAIR_INSTRUCTIONS.format(errors="\n".join(errors))
                + "\n\nCurrent script:\n"
                + code
            )
            continue

        # validation passed -> render
        job_dir.mkdir(parents=True, exist_ok=True)
        code_file = job_dir / f"scene_{seq}.py"
        code_file.write_text(code)
        try:
            await sandbox.run_rendering(
                job_dir,
                code_file.name,
                scene_name="SceneGen",
                timeout=900,
            )
            videos = (
                sorted((job_dir / "videos").rglob("*.mp4"))
                if (job_dir / "videos").exists()
                else []
            )
            if videos:
                status = "completed"
                video_relpath = str(videos[0])
                first_pass = attempts == 1
                shutil.copy(code_file, job_dir / "final_code.py")
                break
            render_error = "render produced no video files"
        except RuntimeError as e:
            render_error = str(e)[:400]
        except Exception as e:  # noqa: BLE001 — sandbox unavailable etc.
            render_error = f"{type(e).__name__}: {e}"[:400]

        append_trace(
            trace_dir,
            {
                "ts": datetime.now(UTC).isoformat(),
                "arm": arm,
                "rep": int(row["rep"]),
                "topic": topic,
                "model": model,
                "stage": "render",
                "attempt": attempts,
                "job_seq": seq,
                "error": render_error,
            },
        )

        if arm == "A":
            break  # no repair in Arm A
        # render failure feeds back to the repair loop (matches Arm C's render-repair)
        prompt = (
            REPAIR_INSTRUCTIONS.format(errors="Render failed:\n" + (render_error or ""))
            + "\n\nCurrent script:\n"
            + code
        )

    if status != "completed":
        status = "failed"
        if not errors and not render_error and not http_error:
            errors = ["attempts exhausted"]

    outcome = {
        "job_seq": seq,
        "arm": arm,
        "rep": int(row["rep"]),
        "topic": topic,
        "model": model,
        "status": status,
        "first_pass": first_pass,
        "validation_errors": errors if errors else [],
        "render_error": render_error,
        "attempts": attempts,
        "video": video_relpath,
        "code_chars": len(code or ""),
    }
    out.write_text(json.dumps(outcome, indent=2) + "\n")
    return outcome


async def main_async(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    trace_dir = Path(args.trace_dir)
    from infra.settings import get_settings

    settings = get_settings()
    if settings.benchmark_temperature is not None:
        os.environ.setdefault("BENCH_TEMPERATURE", str(settings.benchmark_temperature))

    topic_prompts = load_topic_prompts(manifest_path)
    rows = [
        r
        for r in load_manifest(manifest_path, args.arm)
        if not (outcomes_dir(trace_dir) / f"job-{int(r['job_seq'])}.json").exists()
    ]
    if args.limit:
        rows = rows[: args.limit]
    print(f"{len(rows)} pending arm-{args.arm} jobs")

    from infra.engines.sandbox import LocalSandbox

    sandbox = LocalSandbox()
    if not sandbox.is_healthy():
        sys.exit("sandbox unhealthy: no podman/docker/local manim available")

    # Sweep containers orphaned by a crashed or killed client in an earlier run;
    # nothing else can ever claim them, so they would run until the host reboots.
    reaped = sandbox.reap_orphans()
    if reaped:
        print(f"reaped {reaped} orphaned manim container(s)")

    sem = asyncio.Semaphore(args.parallelism)

    async def bounded(row: dict[str, str]) -> dict[str, object]:
        async with sem:
            return await run_one(
                row,
                args.arm,
                trace_dir,
                args.max_attempts,
                args.dry_run,
                topic_prompts,
                args.min_scenes,
                sandbox,
            )

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
    ap.add_argument("--min-scenes", type=int, default=5)
    ap.add_argument("--max-attempts", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
