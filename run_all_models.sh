#!/usr/bin/env bash
# ConceptCast Multi-Model Generalization Testing Suite
# Executes E2E generation sequentially on the host for all target open-source models.

set -euo pipefail

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

TOPIC="derivatives"
AUDIENCE="General Audience"

echo "================================================================================"
echo "🧪 Starting ConceptCast Multi-Model Generalization Run"
echo "Topic: $TOPIC | Audience: $AUDIENCE"
echo "Models to evaluate: ${#MODELS[@]}"
echo "================================================================================"

for i in "${!MODELS[@]}"; do
  model="${MODELS[$i]}"
  num=$((i + 1))
  
  echo ""
  echo "--------------------------------------------------------------------------------"
  echo "[$num/${#MODELS[@]}] 🚀 Executing Generation Run with: $model"
  echo "--------------------------------------------------------------------------------"
  
  # Run make generate on the host terminal
  # This relies on the host environment (pnpm, uv, and Infisical credentials)
  if make generate topic="$TOPIC" audience="$AUDIENCE" model="$model"; then
    echo ""
    echo "✅ [SUCCESS] Completed generation run for: $model"
  else
    echo ""
    echo "❌ [FAILURE] Generation run failed for: $model"
  fi
  
  echo "================================================================================"
  sleep 5
done

echo ""
echo "🎉 ConceptCast Generalization Suite finished!"
echo "Please verify log outputs in the reports/ directory."
