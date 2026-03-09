"""E2E CLI simulation for the ConceptCast pedagogical workflow.

This script runs the full multi-agent workflow for a specified topic across
all available AI providers and models, logging the detailed execution
output to the cli_reports directory.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from loguru import logger
from sqlalchemy import insert

from infra.ai.factory import get_available_providers_and_models
from infra.database import AsyncSessionLocal, init_db
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.workflow.orchestrator import execute_workflow

# Ensure CLI reports directory exists
REPORTS_DIR = Path(__file__).parent.parent.parent / "cli_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class CLIWorkflowLogger:
    """Handles logging of workflow events to a file for CLI simulations."""

    def __init__(self, provider: str, model_id: str, topic: str):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "_").replace(":", "_")
        self.filename = REPORTS_DIR / f"{timestamp}_{provider}_{safe_model}.txt"
        self.topic = topic
        self.provider = provider
        self.model_id = model_id

        with self.filename.open("w", encoding="utf-8") as f:
            f.write("ConceptCast E2E CLI Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Model: {model_id}\n")
            f.write("=" * 30 + "\n\n")

    async def update_job(self, updates: dict[str, Any]) -> None:
        """Callback for job state updates."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(UTC).isoformat()}] STATUS UPDATE: {updates}\n")
        logger.info(
            f"[{self.provider}/{self.model_id}] Status: {updates.get('status')}"
        )

    async def on_thought(self, agent: str, phase: str, content: str) -> None:
        """Callback for agent thoughts."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(
                f"\n[{datetime.now(UTC).isoformat()}] THOUGHT - {agent} ({phase}):\n"
            )
            f.write(f"{'-' * 20}\n")
            f.write(f"{content}\n")
            f.write(f"{'-' * 20}\n")
        logger.debug(
            f"[{self.provider}/{self.model_id}] Thought from {agent} in {phase}"
        )


async def run_simulation(topic: str, audience: str) -> None:
    """Runs the simulation across all active models."""
    await init_db()
    settings = get_settings()
    active_providers = get_available_providers_and_models(settings)

    logger.info(f"Starting E2E simulation for topic: '{topic}'")
    logger.info(f"Detected {len(active_providers)} active providers.")

    for provider_info in active_providers:
        provider = provider_info.provider
        # Skip mock for e2e unless explicitly requested (future)
        if provider == "mock":
            continue

        for model_id in provider_info.models:
            job_id = str(uuid4())
            cli_logger = CLIWorkflowLogger(provider, model_id, topic)

            logger.info(
                f"Running simulation for {provider}/{model_id} (Job ID: {job_id})"
            )

            async with AsyncSessionLocal() as session:
                # Create job record
                stmt = insert(JobRecord).values(
                    job_id=job_id,
                    topic=topic,
                    target_audience=audience,
                    provider=provider,
                    model_id=model_id,
                    status="planning",
                    mode="live",
                )
                await session.execute(stmt)
                await session.commit()

            try:
                await execute_workflow(
                    job_id=job_id,
                    topic=topic,
                    audience=audience,
                    provider=provider,
                    model_id=model_id,
                    update_job=cli_logger.update_job,
                    on_thought=cli_logger.on_thought,
                )
                logger.success(f"Simulation COMPLETED for {provider}/{model_id}")
            except Exception as e:
                logger.error(f"Simulation FAILED for {provider}/{model_id}: {e}")
                with cli_logger.filename.open("a", encoding="utf-8") as f:
                    f.write(f"\nCRITICAL FAILURE: {str(e)}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ConceptCast E2E Workflow Simulation")
    parser.add_argument("--topic", type=str, required=True, help=" pediagogical topic")
    parser.add_argument(
        "--audience", type=str, default="Beginner", help="Target audience"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_simulation(args.topic, args.audience))
    except KeyboardInterrupt:
        logger.warning("Simulation interrupted by user.")
        sys.exit(1)
