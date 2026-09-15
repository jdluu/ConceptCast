#!/usr/bin/env python3
"""Arm A/B v2 re-run launcher: multi-scene, must-render. Sequential A then B."""
import subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MANIFEST = Path("/home/jdluu/projects/ConceptCast-results/manifest/jobs.csv")
TRACE_DIR = Path("/home/jdluu/projects/ConceptCast-results/traces")
UV = "/home/jdluu/.local/bin/uv"

def run(cmd):
    print(f"\n=== {' '.join(str(c) for c in cmd)} ===", flush=True)
    return subprocess.run([str(c) for c in cmd], cwd=REPO).returncode

def main():
    failures = []
    for arm in ("A", "B"):
        rc = run([UV, "run", "python", "src/scripts/benchmark_monolithic_v2.py",
                  "--manifest", MANIFEST, "--arm", arm, "--parallelism", "5",
                  "--trace-dir", TRACE_DIR])
        if rc != 0:
            failures.append(arm)
        time.sleep(60)
    print(f"\n=== A/B v2 DONE. failed arms: {failures or 'none'} ===", flush=True)

if __name__ == "__main__":
    main()
