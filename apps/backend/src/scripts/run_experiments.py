"""Automated Experiment Suite for ConceptCast Thesis Chapter 5.

This script runs a matrix of pedagogical topics across different AI models
to gather empirical metrics on success rates, costs, and execution times.
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

# We reuse the logic from e2e_cli but wrap it for aggregation
from e2e_cli import REPORTS_DIR, run_single_simulation

EXPERIMENT_RESULTS_DIR = REPORTS_DIR / "experiments"
EXPERIMENT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Define the experiment matrix
TOPICS = [
    {"topic": "Pythagorean Theorem", "audience": "Beginner", "complexity": "low"},
    {
        "topic": "Binary Search Algorithm",
        "audience": "Intermediate",
        "complexity": "medium",
    },
    {
        "topic": "Backpropagation in Neural Networks",
        "audience": "Advanced",
        "complexity": "high",
    },
]

# We will test with Mock for local verification, but this is designed for real models
MODELS = [
    {"provider": "mock", "model_id": "mock-model"},
    # Add real models here if INFISICAL is configured and you want to run real tests
    # {"provider": "nano", "model_id": "gpt-4o"},
    # {"provider": "nano", "model_id": "claude-3-5-sonnet"}
]


async def run_suite() -> None:
    print("\n\033[1m🧪 Starting ConceptCast Experiment Suite\033[0m")
    print(f"Time: {datetime.now(UTC).isoformat()}\n")

    summary_results: list[dict[str, Any]] = []

    for model in MODELS:
        for topic_info in TOPICS:
            print(f"--- Running: {topic_info['topic']} with {model['model_id']} ---")

            try:
                # Run the simulation
                # Note: This assumes the backend server is running (make dev)
                result = await run_single_simulation(
                    provider=model["provider"],
                    model_id=model["model_id"],
                    topic=topic_info["topic"],
                    audience=topic_info["audience"],
                )

                # Detect fallback in summary
                summary_text = str(result.get("failure_summary") or "").lower()
                result["fallback_used"] = "fallback" in summary_text

                # Add metadata
                result["complexity"] = topic_info["complexity"]
                result["timestamp"] = datetime.now(UTC).isoformat()

                summary_results.append(result)

                # Small delay between runs
                await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Experiment failed for {topic_info['topic']}: {e}")
                summary_results.append(
                    {
                        "topic": topic_info["topic"],
                        "model_id": model["model_id"],
                        "status": "crashed",
                        "error": str(e),
                    }
                )

    # Save Aggregate Summary
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    summary_path = EXPERIMENT_RESULTS_DIR / f"experiment_summary_{ts}.json"

    with summary_path.open("w") as f:
        json.dump(summary_results, f, indent=2)

    print("\n\033[1;92m✅ Experiment Suite Complete!\033[0m")
    print(f"Summary saved to: {summary_path}")

    # Print Quick Stats
    completed: list[dict[str, Any]] = [
        r for r in summary_results if r.get("status") == "completed"
    ]
    failed: list[dict[str, Any]] = [
        r
        for r in summary_results
        if r.get("status") == "failed" or r.get("status") == "crashed"
    ]

    print("\n--- Aggregate Stats ---")
    print(f"Total Runs: {len(summary_results)}")
    print(f"Successes: {len(completed)}")
    print(f"Failures:  {len(failed)}")

    if completed:
        avg_time = sum(
            [float(r.get("duration_seconds") or 0) for r in completed]
        ) / len(completed)
        avg_cost = sum([float(r.get("cost") or 0) for r in completed]) / len(completed)
        print(f"Avg Success Duration: {avg_time:.2f}s")
        print(f"Avg Success Cost:     ${avg_cost:.4f}")


if __name__ == "__main__":
    asyncio.run(run_suite())
