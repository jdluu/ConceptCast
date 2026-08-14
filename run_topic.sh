#!/usr/bin/env bash
# =============================================================================
# ConceptCast — Multi-Topic Benchmark Runner (PARALLEL)
# Runs ALL target open-weight models on a SINGLE topic with bounded
# parallelism, then syncs the database and raw logs into the data git
# repository (results/).
#
# Usage:
#   ./run_topic.sh "<topic>" ["<audience>"]
#   PARALLELISM=4 ./run_topic.sh "<topic>"   # tune concurrency (default 4)
#
# Concurrency: Nano GPT's subscription plan caps ~10 concurrent requests, and
# each job also dispatches render work to a background worker. PARALLELISM
# defaults to 4 to leave headroom under that cap; tune up to ~8 if the plan
# allows and you don't observe "database is locked" or 429s.
#
# Outputs (all land in the data git repo):
#   - Per-model logs -> results/reports/<topic-slug>/<model>.log
#   - Raw e2e_cli reports -> results/reports/  (copied from ./reports)
#   - Database snapshot -> results/data/conceptcast.db
# =============================================================================
set -euo pipefail

TOPIC="${1:?Usage: run_topic.sh <topic> [audience]}"
AUDIENCE="${2:-General Audience}"
PARALLELISM="${PARALLELISM:-4}"

MODELS=(
  "openai/gpt-oss-20b"
  "openai/gpt-oss-120b"
  "google/gemma-4-31b-it:thinking"
  "deepseek/deepseek-v4-flash:thinking"
  "qwen/qwen3.5-122b-a10b:thinking"
  "minimax/minimax-m2.7"
  "zai-org/glm-5.1:thinking"
  "moonshotai/kimi-k2.6:thinking"
  "deepseek/deepseek-v4-pro:thinking"
)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_REPO="$REPO_ROOT/results"
TOPIC_SLUG="$(printf '%s' "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
TOPIC_LOG_DIR="$DATA_REPO/reports/$TOPIC_SLUG"
mkdir -p "$TOPIC_LOG_DIR"

# Refuse to launch jobs until backend and Redis are reachable. This prevents
# queue-delivery failures from being recorded as model failures.
"$REPO_ROOT/scripts/wait_for_conceptcast.sh"

echo "================================================================================"
echo "ConceptCast Benchmark Run (parallel)"
echo "  Topic:       $TOPIC"
echo "  Audience:    $AUDIENCE"
echo "  Models:      ${#MODELS[@]}"
echo "  Parallelism: $PARALLELISM"
echo "  Logs:        $TOPIC_LOG_DIR"
echo "================================================================================"

pids=()
for i in "${!MODELS[@]}"; do
  model="${MODELS[$i]}"
  num=$((i + 1))
  model_slug="$(printf '%s' "$model" | tr '/' '_' | tr ':' '_')"
  logfile="$TOPIC_LOG_DIR/${model_slug}.log"

  echo "[$num/${#MODELS[@]}] Launching $model  ->  $logfile"

  # Launch the model run in a subshell, writing to its own log file.
  (
    make generate topic="$TOPIC" audience="$AUDIENCE" model="$model"
  ) > "$logfile" 2>&1 &
  pids+=($!)

  # Once we have a full batch running, wait for them before starting more.
  if [ "${#pids[@]}" -ge "$PARALLELISM" ]; then
    for pid in "${pids[@]}"; do
      wait "$pid" || echo "  (model run exited non-zero: pid $pid)"
    done
    pids=()
  fi
done

# Wait for the final (partial) batch.
for pid in "${pids[@]}"; do
  wait "$pid" || echo "  (model run exited non-zero: pid $pid)"
done

# --- Sync into the data git repository (results/) ---
echo ""
echo "================================================================================"
echo "Syncing database + raw reports into data repository (results/)..."
echo "================================================================================"

if [ -f "$REPO_ROOT/data/conceptcast.db" ]; then
  python3 "$REPO_ROOT/scripts/snapshot_sqlite.py" \
    "$REPO_ROOT/data/conceptcast.db" "$DATA_REPO/data/conceptcast.db"
  echo "  [ok] data/conceptcast.db -> results/data/conceptcast.db"
else
  echo "  [warn] data/conceptcast.db not found (backend may write elsewhere)"
fi

mkdir -p "$DATA_REPO/reports"
if ls "$REPO_ROOT/reports/"*.txt >/dev/null 2>&1; then
  cp "$REPO_ROOT/reports/"*.txt "$DATA_REPO/reports/"
  echo "  [ok] reports/*.txt -> results/reports/"
fi
if ls "$REPO_ROOT/reports/"*.json >/dev/null 2>&1; then
  cp "$REPO_ROOT/reports/"*.json "$DATA_REPO/reports/"
  echo "  [ok] reports/*.json -> results/reports/"
fi

# Record the exact matrix and source revision alongside the raw outputs.
python3 - "$DATA_REPO/benchmark-manifest.json" "$TOPIC" "$AUDIENCE" "$PARALLELISM" "$REPO_ROOT" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
manifest = json.loads(path.read_text()) if path.exists() else {"runs": []}
try:
    commit = subprocess.check_output(
        ["git", "-C", sys.argv[5], "rev-parse", "HEAD"], text=True
    ).strip()
except subprocess.CalledProcessError:
    commit = "unknown"
manifest["runs"].append({
    "topic": sys.argv[2],
    "audience": sys.argv[3],
    "parallelism": int(sys.argv[4]),
    "models": [
        "openai/gpt-oss-20b", "openai/gpt-oss-120b",
        "google/gemma-4-31b-it:thinking", "deepseek/deepseek-v4-flash:thinking",
        "qwen/qwen3.5-122b-a10b:thinking", "minimax/minimax-m2.7",
        "zai-org/glm-5.1:thinking", "moonshotai/kimi-k2.6:thinking",
        "deepseek/deepseek-v4-pro:thinking",
    ],
    "code_commit": commit,
    "started_at": datetime.now(timezone.utc).isoformat(),
})
path.write_text(json.dumps(manifest, indent=2) + "\n")
PY

echo ""
echo "Done. Review and commit the data repository:"
echo "  git -C results add -A && git -C results commit -m 'benchmark: $TOPIC_SLUG'"
