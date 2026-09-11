#!/usr/bin/env python3
"""Benchmark v2 orchestrator (Arm C — council).

Reads the pre-registered manifest (manifest/jobs.csv), skips jobs already
recorded as completed in the database, and drives the remaining Arm C jobs
through the normal ConceptCast pipeline via the e2e API client.

Design guarantees (see benchmark-v2 EXPERIMENT_PLAN.md):
- Manifest is the single source of truth for the job grid (topic × model × arm × rep).
- Resumable: completed (topic, model, arm, rep) tuples are never re-run.
- Per-job provenance (benchmark_job_seq/arm/rep) is persisted on the job record
  so analysis joins are exact — no timestamp-window cohort isolation.
- Sampling pins (temperature/seed/trace dir) are exported to the environment
  once; the trace emitter and model settings pick them up per call.

Usage:
  python3 scripts/benchmark_council.py --manifest <jobs.csv> \
      [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
BASE_URL = os.environ.get("CONCEPTCAST_BASE_URL", "http://localhost:8000")


def load_pending(manifest_path: Path, completed: set[tuple[str, str, str, str]], arm_filter: str = "C") -> list[dict[str, str]]:
    """Manifest rows not yet completed, in manifest order (interleaving preserved)."""
    with manifest_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    pending: list[dict[str, str]] = []
    for r in rows:
        key = (r["topic"], r["model"], r["arm"], r["rep"])
        if r["arm"] != arm_filter or key in completed or r.get("status") == "completed":
            continue
        pending.append(r)
    return pending


def fetch_completed() -> set[tuple[str, str, str, str]]:
    """Ask the API for the (topic, model, arm, rep) keys already done."""
    import urllib.request

    with urllib.request.urlopen(f"{BASE_URL}/jobs/", timeout=30) as resp:
        payload = json.loads(resp.read())
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else payload
    done = set()
    for j in jobs:
        if j.get("benchmark_arm") and j.get("status") in ("completed", "fallback-completed"):
            done.add((j.get("topic", ""), j.get("model_id", ""), j["benchmark_arm"], str(j.get("benchmark_rep", ""))))
    return done


import json  # noqa: E402  (used above)


async def wait_for_terminal(client: httpx.AsyncClient, job_id: str, poll: float = 15.0, timeout: float = 7200.0) -> dict[str, object]:
    """Poll job status until a terminal state or timeout. Returns final status dict."""
    elapsed = 0.0
    while elapsed < timeout:
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}/status")
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status in ("completed", "failed", "fallback-completed"):
            return dict(data)
        if status == "awaiting_review" and data.get("current_step") == "rendering_failed_needs_fix":
            # Render-repair pause is part of the workflow, not a stop state.
            pass
        await asyncio.sleep(poll)
        elapsed += poll
    return {"status": "timeout", "job_id": job_id}


async def run_job(client: httpx.AsyncClient, row: dict[str, str], dry_run: bool) -> dict[str, object]:
    """Create + monitor one benchmark job. Returns an outcome record."""
    seq = int(row["job_seq"])
    payload = {
        "topic": row["topic"],
        "provider": "nano",
        "model_id": row["model"],
        "benchmark_job_seq": seq,
        "benchmark_arm": row["arm"],
        "benchmark_rep": int(row["rep"]),
    }
    if dry_run:
        return {"job_seq": seq, "status": "dry-run", **payload}

    resp = await client.post(f"{BASE_URL}/jobs/create", json=payload)
    if resp.status_code != 200:
        return {"job_seq": seq, "status": "create-failed", "detail": resp.text[:200], **payload}
    job = resp.json()
    job_id = job["job_id"]
    print(f"[seq {seq}] created {job_id} (arm {row['arm']}, rep {row['rep']}, {row['model']})", flush=True)
    final = await wait_for_terminal(client, job_id)
    print(f"[seq {seq}] → {final.get('status')}", flush=True)
    return {
        "job_seq": seq,
        "job_id": job_id,
        "status": final.get("status"),
        "cost": final.get("cost"),
        "duration": final.get("duration_seconds"),
        "topic": row["topic"],
        "model": row["model"],
        "arm": row["arm"],
        "rep": row["rep"],
    }


async def main_async(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.exit(f"manifest not found: {manifest_path}")

    try:
        completed = fetch_completed()
    except Exception as e:  # noqa: BLE001 — backend may be cold; start from zero only if truly unreachable
        sys.exit(f"cannot reach backend at {BASE_URL}: {e}")

    pending = load_pending(manifest_path, completed, arm_filter=args.arm)
    if args.limit:
        pending = pending[: args.limit]
    print(f"{len(pending)} pending arm-{args.arm} jobs ({len(completed)} already completed)")

    # Export benchmark env for this process (backend gets pins via its own settings/env;
    # the runner exports them so created jobs' telemetry context is consistent).
    if args.trace_dir:
        os.environ.setdefault("BENCH_TRACE_DIR", args.trace_dir)
    if args.temperature is not None:
        os.environ.setdefault("BENCH_TEMPERATURE", str(args.temperature))

    outcomes: list[dict[str, object]] = []
    semaphore = asyncio.Semaphore(args.parallelism)

    async with httpx.AsyncClient(timeout=60.0) as client:
        async def bounded(row: dict[str, str]) -> dict[str, object]:
            async with semaphore:
                return await run_job(client, row, args.dry_run)

        results = await asyncio.gather(*(bounded(row) for row in pending))
        outcomes = list(results)

    # Persist an outcome journal next to the manifest (resumability audit trail).
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = manifest_path.parent / f"council-outcomes-{stamp}.json"
    out.write_text(json.dumps({"arm": args.arm, "n": len(outcomes), "results": outcomes}, indent=2) + "\n")
    print(f"outcomes → {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="path to manifest/jobs.csv")
    ap.add_argument("--arm", default="C", help="arm filter (default C; A/B use benchmark_monolithic.py)")
    ap.add_argument("--parallelism", type=int, default=4, help="concurrent jobs (default 4; Nano GPT caps ~10)")
    ap.add_argument("--limit", type=int, default=None, help="max jobs this invocation")
    ap.add_argument("--trace-dir", default=None, help="BENCH_TRACE_DIR for per-call traces")
    ap.add_argument("--temperature", type=float, default=None, help="BENCH_TEMPERATURE pin")
    ap.add_argument("--dry-run", action="store_true", help="list pending jobs without running")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
