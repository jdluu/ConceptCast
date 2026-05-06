import json

from infra.settings import PROJECT_ROOT

# Get project root from settings
REPORTS_DIR = PROJECT_ROOT / "reports"
EXPERIMENTS_DIR = REPORTS_DIR / "experiments"


def analyze_results() -> None:
    if not EXPERIMENTS_DIR.exists():
        print("No experiments found.")
        return

    summaries = sorted(EXPERIMENTS_DIR.glob("experiment_summary_*.json"))
    if not summaries:
        print("No summary files found.")
        return

    latest_summary = summaries[-1]
    with latest_summary.open() as f:
        data = json.load(f)

    print(f"--- Analysis of {latest_summary.name} ---")

    total = len(data)
    success = len([r for r in data if r.get("status") == "completed"])
    failed = len([r for r in data if r.get("status") == "failed"])
    crashed = len([r for r in data if r.get("status") == "crashed"])

    print(f"Total Runs: {total}")
    print(f"Successes: {success}")
    print(f"Failures: {failed}")
    print(f"Crashes: {crashed}")

    # Identify bottlenecks
    stages: dict[str, int] = {}
    for r in data:
        stage = r.get("failure_stage") or "None"
        stages[stage] = stages.get(stage, 0) + 1

    print("\n--- Failure Stages ---")
    for stage, count in stages.items():
        print(f"{stage}: {count}")

    # Cost and Duration
    costs = [float(r.get("cost", 0)) for r in data if r.get("cost")]
    durations = [
        float(r.get("duration_seconds", 0)) for r in data if r.get("duration_seconds")
    ]

    if costs:
        print(f"\nAvg Cost: ${sum(costs) / len(costs):.4f}")
    if durations:
        print(f"Avg Duration: {sum(durations) / len(durations):.2f}s")


if __name__ == "__main__":
    analyze_results()
