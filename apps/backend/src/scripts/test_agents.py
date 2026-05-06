"""Diagnostic script to verify agent intelligence and event streaming.

Tests the low-level Pydantic AI event loop for all council agents to ensure
thinking and output parts are correctly emitted and captured.
"""

import argparse
import asyncio
import contextlib
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import structlog
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    AnimationReview,
    CurriculumPlan,
    Storyboard,
)
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.factory import get_concept_model
from infra.ai.mock import MockConceptModel, RealisticMockModel
from infra.ai.streaming import run_agent_streamed
from infra.models.job import JobRecord
from services.workflow.orchestrator import execute_workflow

logger = structlog.get_logger(__name__)


async def test_agent_logic(  # noqa: C901, PLR0912
    agent_name: str,
    system_prompt: str,
    output_type: type,
    topic: str = "Linear Algebra",
    provider: str = "mock",
    model_id: str | None = None,
) -> bool:
    """Simulates a single agent run and validates the event stream."""
    logger.info(
        "diagnostic_agent_test_started", agent=agent_name.upper(), provider=provider
    )

    if provider == "mock":
        concept_model: BaseConceptModel | None = MockConceptModel(
            RealisticMockModel(), f"mock-{agent_name}"
        )
    else:
        concept_model = get_concept_model(provider, model_id)

    if not concept_model:
        logger.error("diagnostic_agent_test_failed_model_not_found", provider=provider)
        return False

    agent = Agent(
        concept_model.model,
        system_prompt=system_prompt,
        output_type=output_type,
        deps_type=GlobalContext,
        retries=3,
    )

    # We use a simple prompt that will trigger the mock model
    prompt = f"Explain '{topic}'"

    captured_thoughts = []
    captured_output_chunks = 0

    async def on_thought(_name: str, phase: str, content: str) -> None:
        if phase == "thinking":
            captured_thoughts.append(content)
            # Print thoughts in a dimmed style to indicate internal reasoning
            print(f"    \033[2m[Thought] {content}\033[0m", flush=True)  # noqa: T201
        elif phase == "output":
            nonlocal captured_output_chunks
            captured_output_chunks += 1

    # Add dependencies if needed by the agent
    kwargs: dict[str, Any] = {}
    if agent_name == "architect":
        kwargs["deps"] = CurriculumPlan(
            concept_title=topic, target_audience="Beginner", teaching_steps=[]
        )
    elif agent_name == "reviewer":
        # Reviewer requires a storyboard with at least one scene
        from api.schemas import Scene

        kwargs["deps"] = Storyboard(
            concept_title=topic,
            scenes=[
                Scene(
                    scene_id=1,
                    title="Intro",
                    description="Visual intro",
                    narration="Let's start.",
                    objects=[],
                )
            ],
        )

    ctx = GlobalContext(topic=topic, target_audience="Beginner")

    # If the agent needs specific artifacts (like curriculum or storyboard),
    # we should ideally put them inside the ctx (GCO) now.
    if "deps" in kwargs:
        artifact = kwargs.pop("deps")
        if isinstance(artifact, CurriculumPlan):
            ctx.plan = artifact
        elif isinstance(artifact, Storyboard):
            ctx.storyboard = artifact

    result, usage = await run_agent_streamed(
        agent_name, agent, prompt, on_thought=on_thought, deps=ctx, **kwargs
    )

    # Verbose Artifact Output
    print("  \033[1m[Artifact]\033[0m")  # noqa: T201
    try:
        if hasattr(result, "model_dump_json"):
            print(f"{result.model_dump_json(indent=4)}")  # noqa: T201
        elif isinstance(result, (dict, list)):
            import json

            print(f"{json.dumps(result, indent=4)}")  # noqa: T201
        else:
            print(f"{result}")  # noqa: T201
    except Exception as e:
        print(f"  (Failed to serialize artifact: {e})")  # noqa: T201
        print(f"{result}")  # noqa: T201
    print()  # noqa: T201

    # Assertions
    if not captured_thoughts:
        logger.error(
            "diagnostic_agent_test_failed_no_thinking_parts",
            agent=agent_name,
        )
        return False

    if not result:
        logger.error("diagnostic_agent_test_failed_no_result", agent=agent_name)
        return False

    # Structural Validation
    if agent_name == "architect" and (
        not isinstance(result, Storyboard) or len(result.scenes) == 0
    ):
        logger.error(
            "diagnostic_agent_test_failed_invalid_storyboard",
            agent=agent_name,
        )
        return False

    logger.info(
        "diagnostic_agent_test_passed",
        agent=agent_name,
        thought_blocks=len(captured_thoughts),
    )
    return True


async def test_full_workflow(topic: str = "Quantum Entanglement") -> bool:
    """Tests the entire orchestration workflow (Step 1-4) in mock mode.

    Verifies that the orchestrator correctly flows information through all agents
    and persists the results into the JobRecord.
    """
    from datetime import UTC, datetime
    from unittest.mock import patch

    logger.info("diagnostic_workflow_test_started", topic=topic)

    # 1. Setup Mock JobRecord
    job_id = "test-workflow-uuid"
    job = JobRecord(
        job_id=job_id,
        topic=topic,
        target_audience="Beginner",
        status="pending",
        mode="mock",
        provider="mock",
        model_id="mock-model",
        hitl_enabled=False,
        started_at=datetime.now(UTC),
        total_execution_time=0.0,
    )

    # 2. Mock DB Session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = job
    mock_session.execute.return_value = mock_result

    # 3. Callbacks for tracking
    captured_thoughts = []

    async def on_thought(agent: str, phase: str, content: str) -> None:
        captured_thoughts.append((agent, phase))
        if phase == "thinking":
            print(f"    \033[2m[{agent}] {content[:100]}...\033[0m", flush=True)  # noqa: T201

    async def update_job(updates: dict[str, object]) -> None:
        for k, v in updates.items():
            setattr(job, k, v)

    # 4. Execute Workflow with mocked renderer
    with patch("services.workflow.orchestrator.render_video_task") as mock_render_task:
        mock_render_task.kiq = AsyncMock()

        try:
            await execute_workflow(
                session=mock_session,
                job_id=job_id,
                topic=topic,
                audience="Beginner",
                provider="mock",
                model_id="mock-model",
                update_job=update_job,
                on_thought=on_thought,
            )
        except Exception as e:
            logger.error("diagnostic_workflow_test_crashed", error=str(e))
            return False

        # 5. Assertions
        if not job.plan:
            logger.error("diagnostic_workflow_test_failed_missing_plan")
            return False
        if not job.storyboard:
            logger.error("diagnostic_workflow_test_failed_missing_storyboard")
            return False
        if not job.manim_code:
            logger.error("diagnostic_workflow_test_failed_missing_manim_code")
            return False

        # Verify renderer was dispatched
        mock_render_task.kiq.assert_called_once()

        logger.info(
            "diagnostic_workflow_test_passed",
            thoughts_captured=len(captured_thoughts),
        )
        return True


async def run_diagnostics(args: argparse.Namespace) -> None:
    """Runs a full suite of agent diagnostics."""
    logger.info("diagnostic_suite_started")

    provider = "nano" if args.no_mock else "mock"
    model_id = args.model_id

    tests = [
        ("analyst", "Analyst Agent", CurriculumPlan),
        ("architect", "Architect Agent", Storyboard),
        ("animator", "Animator Agent", str),
        ("reviewer", "Reviewer Agent", AnimationReview),
    ]

    results = []
    for name, prompt, out_type in tests:
        success = await test_agent_logic(
            name, prompt, out_type, provider=provider, model_id=model_id
        )
        results.append(success)
        await asyncio.sleep(0.2)  # Small delay for readability

    # --- FULL WORKFLOW INTEGRATION TEST ---
    # We only run workflow integration in mock mode to avoid high token costs for a sanity check
    workflow_success = await test_full_workflow("Quantum Entanglement")
    results.append(workflow_success)

    if all(results):
        logger.info("diagnostic_suite_passed")
    else:
        logger.error("diagnostic_suite_failed")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ConceptCast Agent Diagnostic Suite")
    parser.add_argument(
        "--no-mock", action="store_true", help="Run with real AI providers"
    )
    parser.add_argument(
        "--model-id", type=str, default=None, help="Specific model to test"
    )
    cmd_args = parser.parse_args()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_diagnostics(cmd_args))
