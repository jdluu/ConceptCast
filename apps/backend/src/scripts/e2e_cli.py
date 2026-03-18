"""E2E CLI simulation for the ConceptCast pedagogical workflow.

This script runs the full multi-agent workflow for a specified topic across
all available AI providers and models by making actual API requests to the
running backend server. Results are logged to the e2e_reports directory.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from infra.ai.factory import get_available_providers_and_models
from infra.settings import get_settings

# Configuration
BASE_URL = "http://localhost:8000"
REPORTS_DIR = Path(__file__).parent.parent.parent / "e2e_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BLUE = "\033[94m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_CYAN = "\033[96m"
CLR_MAGENTA = "\033[95m"
CLR_WHITE = "\033[97m"
CLR_BOLD = "\033[1m"
CLR_DIM = "\033[2m"

AGENT_COLORS = {
    "Analyst": CLR_BLUE,
    "Validator": CLR_GREEN,
    "Architect": CLR_CYAN,
    "Animator": CLR_MAGENTA,
}


class E2EWorkflowLogger:
    """Handles logging of workflow events to terminal and file."""

    def __init__(self, provider: str, model_id: str, topic: str):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "_").replace(":", "_")
        self.filename = REPORTS_DIR / f"{timestamp}_{provider}_{safe_model}.txt"
        self.topic = topic
        self.provider = provider
        self.model_id = model_id
        self.last_step = None
        self.printed_thoughts_count = 0
        self.last_progress = -1
        self.last_thought_content = ""

        with self.filename.open("w", encoding="utf-8") as f:
            f.write("ConceptCast E2E API Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Model: {model_id}\n")
            f.write("=" * 30 + "\n\n")

        print(f"\n{CLR_BOLD}{CLR_CYAN}🚀 Starting Workflow: {topic}{CLR_RESET}")  # noqa: T201
        print(f"{CLR_DIM}Model: {provider}/{model_id}{CLR_RESET}\n")  # noqa: T201

    def log_event(self, event_data: dict[str, Any]) -> None:  # noqa: C901, PLR0912
        """Logs an event from the SSE stream to the report file and terminal."""
        status = event_data.get("status")
        step = event_data.get("current_step")
        progress = event_data.get("render_progress", 0)

        # Log to file
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now(UTC).isoformat()}] STATUS: {status} | STEP: {step}\n"
            )
            thoughts = event_data.get("streamed_thoughts", [])
            if len(thoughts) > self.printed_thoughts_count:
                for i in range(self.printed_thoughts_count, len(thoughts)):
                    t = thoughts[i]
                    f.write(
                        f"  THOUGHT - {t.get('agent')} ({t.get('phase')}): {t.get('content')}\n"
                    )
            elif thoughts and self.printed_thoughts_count > 0:
                # Log content delta for the last thought
                last_t = thoughts[-1]
                f.write(
                    f"  THOUGHT DELTA - {last_t.get('agent')}: {last_t.get('content')}\n"
                )

        # Log to terminal
        if step != self.last_step and step:
            if self.last_step:
                print("\n")  # Newline before next step  # noqa: T201
            icon = (
                "📝"
                if "plan" in step
                else "✅"
                if "valid" in step
                else "🎨"
                if "arch" in step
                else "🎬"
                if "anim" in step
                else "⚙️"
            )
            print(f"{CLR_BOLD}{icon} Step: {step.replace('_', ' ').title()}{CLR_RESET}")  # noqa: T201
            self.last_step = step

        # Handle thoughts
        thoughts = event_data.get("streamed_thoughts", [])
        if not thoughts:
            return

        # 1. Handle NEW thoughts (appended to the list)
        if len(thoughts) > self.printed_thoughts_count:
            # If we were already printing a thought, end it
            if self.printed_thoughts_count > 0:
                print()  # noqa: T201

            for i in range(self.printed_thoughts_count, len(thoughts)):
                t = thoughts[i]
                agent = t.get("agent", "Unknown")
                phase = t.get("phase", "reasoning")
                content = t.get("content", "")

                # Visual style based on phase
                if agent == "system" and phase == "status":
                    header = f"{CLR_BOLD}{CLR_WHITE}󰋼 SYSTEM:{CLR_RESET}"
                    content_style = CLR_DIM
                else:
                    color = AGENT_COLORS.get(agent, CLR_RESET)
                    icon = (
                        "󰚩"
                        if phase == "thinking"
                        else "󱐋"
                        if phase == "tool_call"
                        else "󰙨"
                    )
                    header = f"{color}{CLR_BOLD}{icon} {agent} ({phase}):{CLR_RESET}"
                    content_style = ""

                # Newline for subsequent thoughts in this batch
                if i > self.printed_thoughts_count:
                    print()  # noqa: T201

                print(f"  {header} {content_style}{content}", end="", flush=True)  # noqa: T201
                self.last_thought_content = content

            self.printed_thoughts_count = len(thoughts)

        # 2. Handle UPDATED content in the LAST thought (aggregation)
        elif self.printed_thoughts_count > 0:
            last_t = thoughts[-1]
            full_content = last_t.get("content", "")

            # Find the delta since we last printed for this thought
            if hasattr(self, "last_thought_content") and full_content.startswith(
                self.last_thought_content
            ):
                delta = full_content[len(self.last_thought_content) :]
                if delta:
                    print(delta, end="", flush=True)  # noqa: T201
                    self.last_thought_content = full_content
            else:
                # If prefix match fails (unexpected), just store full content
                self.last_thought_content = full_content

        # Handle progress
        if status == "rendering" and progress > self.last_progress:
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            sys.stdout.write(
                f"\r  {CLR_YELLOW}Rendering Progress: [{bar}] {progress}%{CLR_RESET}"
            )
            sys.stdout.flush()
            self.last_progress = progress

    def log_error(self, error: str) -> None:
        """Logs a critical error to the report file and terminal."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL FAILURE: {error}\n")
        print(f"\n\n{CLR_RED}{CLR_BOLD}❌ FAILED: {error}{CLR_RESET}\n")  # noqa: T201

    def log_success(self, final_data: dict[str, Any]) -> None:
        """Logs final job completion details."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write("\nCOMPLETED SUCCESSFULLY\n")
            f.write(f"Final Cost: ${final_data.get('cost', 0.0):.4f}\n")
            f.write(f"Duration: {final_data.get('duration_seconds', 0.0):.2f}s\n")
            if final_data.get("video_url"):
                f.write(f"Video URL: {final_data.get('video_url')}\n")

        print(  # noqa: T201
            f"\n\n{CLR_GREEN}{CLR_BOLD}✨ Workflow Completed Successfully!{CLR_RESET}"
        )
        print(f"   {CLR_DIM}Cost: ${final_data.get('cost', 0.0):.4f}{CLR_RESET}")  # noqa: T201
        if final_data.get("video_url"):
            print(  # noqa: T201
                f"   {CLR_BOLD}Video: {BASE_URL}{final_data.get('video_url')}{CLR_RESET}"
            )
        print("")  # noqa: T201


async def monitor_job(job_id: str, e2e_logger: E2EWorkflowLogger) -> dict[str, Any]:
    """Monitors a job's progress via the SSE endpoint."""
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream(
                "GET", f"{BASE_URL}/jobs/{job_id}/events"
            ) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise Exception(
                        f"Failed to connect to SSE: {response.status_code} {error_detail.decode()}"
                    )

                last_event_data = {}
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        event_data = json.loads(data_str)

                        if "error" in event_data and event_data["error"]:
                            e2e_logger.log_error(event_data["error"])
                            return cast(dict[str, Any], event_data)

                        e2e_logger.log_event(event_data)
                        last_event_data = event_data

                        if event_data.get("status") in ["completed", "failed"]:
                            if event_data.get("status") == "completed":
                                e2e_logger.log_success(event_data)
                            return cast(dict[str, Any], event_data)
                return cast(dict[str, Any], last_event_data)
        except Exception as e:
            e2e_logger.log_error(str(e))
            raise


async def run_single_simulation(
    provider: str, model_id: str, topic: str, audience: str
) -> None:
    """Runs a single simulation for one provider/model."""
    e2e_logger = E2EWorkflowLogger(provider, model_id, topic)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/jobs/create",
                json={
                    "topic": topic,
                    "target_audience": audience,
                    "provider": provider,
                    "model_id": model_id,
                    "analyst_model": None,
                    "validator_model": None,
                    "architect_model": None,
                    "animator_model": None,
                    "hitl_enabled": False,
                },
            )
            if response.status_code != 200:
                e2e_logger.log_error(
                    f"Job creation failed: {response.status_code} {response.text}"
                )
                return

            job_data = response.json()
            job_id = job_data["job_id"]

            await monitor_job(job_id, e2e_logger)

        except Exception as e:
            e2e_logger.log_error(f"Request failed: {str(e)}")


async def run_full_simulation(
    topic: str, audience: str, include_mock: bool = True
) -> None:
    """Runs simulations across all active models sequentially."""
    settings = get_settings()
    active_providers = get_available_providers_and_models(settings)

    # Ensure backend is up
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{BASE_URL}/health")
        except Exception:
            print(  # noqa: T201
                f"{CLR_RED}Backend server not found at {BASE_URL}. Please start it with 'make dev' first.{CLR_RESET}"
            )
            return

    for provider_info in active_providers:
        provider = provider_info.provider
        if provider == "mock" and not include_mock:
            continue

        for model_id in provider_info.models:
            await run_single_simulation(provider, model_id, topic, audience)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ConceptCast E2E Workflow API Simulation"
    )
    parser.add_argument("--topic", type=str, required=True, help="Pedagogical topic")
    parser.add_argument(
        "--audience", type=str, default="Beginner", help="Target audience"
    )
    parser.add_argument("--no-mock", action="store_true", help="Skip the mock provider")

    args = parser.parse_args()

    try:
        asyncio.run(run_full_simulation(args.topic, args.audience, not args.no_mock))
    except KeyboardInterrupt:
        print(f"\n{CLR_YELLOW}Simulation interrupted by user.{CLR_RESET}")  # noqa: T201
        sys.exit(1)
