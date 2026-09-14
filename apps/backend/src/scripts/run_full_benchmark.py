#!/usr/bin/env python3
"""Full benchmark launcher: arms A, B, C sequentially. Resumable per arm.

- Arm A/B: benchmark_monolithic.py (self-contained LLM calls + validation; traces+outcomes
  to BENCH_TRACE_DIR; resumable via per-job outcome files)
- Arm C: benchmark_council.py (backend-driven; resumable via completed-tuple check)
- 15-minute settle gap between arms so the backend drains before the next phase.
"""
import os, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # apps/backend
MANIFEST = Path("/home/jdluu/projects/ConceptCast-results/manifest/jobs.csv")
TRACE_DIR = Path(os.environ.get("BENCH_TRACE_DIR", "/home/jdluu/projects/ConceptCast-results/traces"))
UV = "/home/jdluu/.local/bin/uv"

def run(cmd):
    print(f"\n=== {' '.join(str(c) for c in cmd)} ===", flush=True)
    return subprocess.run([str(c) for c in cmd], cwd=REPO).returncode

def main():
    failures = []
    # Arm A
    if run([UV, "run", "python", "src/scripts/benchmark_monolithic.py",
            "--manifest", MANIFEST, "--arm", "A", "--parallelism", "5",
            "--trace-dir", TRACE_DIR]) != 0:
        failures.append("A")
    time.sleep(60)
    # Arm B
    if run([UV, "run", "python", "src/scripts/benchmark_monolithic.py",
            "--manifest", MANIFEST, "--arm", "B", "--parallelism", "5",
            "--trace-dir", TRACE_DIR]) != 0:
        failures.append("B")
    time.sleep(60)
    # Arm C
    if run([UV, "run", "python", "src/scripts/benchmark_council.py",
            "--manifest", MANIFEST, "--arm", "C", "--parallelism", "8"]) != 0:
        failures.append("C")
    print(f"\n=== BENCHMARK DONE. failed arms: {failures or 'none'} ===", flush=True)

if __name__ == "__main__":
    main()
