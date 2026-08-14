#!/usr/bin/env bash
# =============================================================================
# Run ALL 4 new benchmark topics sequentially (36 jobs: 4 topics x 9 models).
# Each topic runs its 9 models with the parallel runner (PARALLELISM default 4),
# then syncs the database + reports into results/ before the next topic starts.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

./scripts/wait_for_conceptcast.sh
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .benchmark_started_at
rm -f .benchmark_notified

echo "================================================================================"
echo "ConceptCast Multi-Topic Benchmark — ALL 4 TOPICS"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Topics: backpropagation, fourier transform, doppler effect, eigenvectors"
echo "================================================================================"

./run_backpropagation.sh
./run_fourier.sh
./run_doppler.sh
./run_eigenvectors.sh

echo ""
echo "================================================================================"
echo "ALL TOPICS COMPLETE: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "================================================================================"
