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
from loguru import logger

from infra.ai.factory import get_available_providers_and_models
from infra.settings import get_settings

# Configuration
BASE_URL = "http://localhost:8000"
REPORTS_DIR = Path(__file__).parent.parent.parent / "e2e_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class E2EWorkflowLogger:
    """Handles logging of workflow events to a file for E2E simulations."""

    def __init__(self, provider: str, model_id: str, topic: str):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "_").replace(":", "_")
        self.filename = REPORTS_DIR / f"{timestamp}_{provider}_{safe_model}.txt"
        self.topic = topic
        self.provider = provider
        self.model_id = model_id

        with self.filename.open("w", encoding="utf-8") as f:
            f.write("ConceptCast E2E API Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Model: {model_id}\n")
            f.write("=" * 30 + "\n\n")

    def log_event(self, event_data: dict[str, Any]) -> None:
        """Logs an event from the SSE stream to the report file."""
        status = event_data.get("status")
        step = event_data.get("current_step")

        with self.filename.open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now(UTC).isoformat()}] STATUS: {status} | STEP: {step}\n"
            )

            # Log new thoughts if any
            thoughts = event_data.get("streamed_thoughts", [])
            if thoughts:
                # We only log the last thought to avoid massive duplication in the log
                # since the entire status is sent in each SSE event
                last_thought = thoughts[-1]
                f.write(
                    f"  THOUGHT - {last_thought.get('agent')} ({last_thought.get('phase')}):\n"
                )
                f.write(f"  {last_thought.get('content')[:100]}...\n")

        logger.info(
            f"[{self.provider}/{self.model_id}] Status: {status} | Step: {step}"
        )

    def log_error(self, error: str) -> None:
        """Logs a critical error to the report file."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL FAILURE: {error}\n")
        logger.error(f"[{self.provider}/{self.model_id}] FAILED: {error}")

    def log_success(self, final_data: dict[str, Any]) -> None:
        """Logs final job completion details."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write("\nCOMPLETED SUCCESSFULLY\n")
            f.write(f"Final Cost: ${final_data.get('cost', 0.0):.4f}\n")
            f.write(f"Duration: {final_data.get('duration_seconds', 0.0):.2f}s\n")
            if final_data.get("video_url"):
                f.write(f"Video URL: {final_data.get('video_url')}\n")
        logger.success(f"[{self.provider}/{self.model_id}] COMPLETED")


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
        logger.info(f"Creating job for {provider}/{model_id}...")
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
            logger.info(f"Job {job_id} created. Monitoring...")

            await monitor_job(job_id, e2e_logger)

        except Exception as e:
            e2e_logger.log_error(f"Request failed: {str(e)}")


async def run_full_simulation(
    topic: str, audience: str, include_mock: bool = True
) -> None:
    """Runs simulations across all active models sequentially."""
    settings = get_settings()
    active_providers = get_available_providers_and_models(settings)

    logger.info(f"Starting E2E API simulation for topic: '{topic}'")

    # Ensure backend is up
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{BASE_URL}/health")
        except Exception:
            logger.error(
                f"Backend server not found at {BASE_URL}. Please start it with 'make dev' or 'make dev-backend' first."
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
        logger.warning("Simulation interrupted by user.")
        sys.exit(1)
