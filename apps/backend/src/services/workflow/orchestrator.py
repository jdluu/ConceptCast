import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, cast

from loguru import logger
from pydantic_ai.usage import RunUsage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import JobRequest
from infra.database import AsyncSessionLocal
from infra.exceptions import (
    AnimationGenerationError,
    PlanGenerationError,
    StoryboardGenerationError,
)
from infra.models.job import JobRecord
from services.workflow.utils import calculate_job_cost, merge_usage

from ..jobs.manager import (
    append_job_thought,
    prepare_job_for_retry_logic,
    update_job_record,
    update_job_status,
)
from .steps.animating import step_animating
from .steps.architecting import step_architecting
from .steps.planning import step_planning
from .steps.rendering import step_rendering
from .steps.validating import step_validating


async def prepare_job_for_retry(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> JobRecord:
    """Wrapper for the job-reset logic to satisfy API expectations."""
    return await prepare_job_for_retry_logic(job_id, db_session_factory)


async def process_job_logic(
    job_id: str,
    request: JobRequest,
    db_session_factory: Callable[[], AsyncSession] = AsyncSessionLocal,
) -> None:
    """Entry point for background execution of the pedagogical video workflow.

    Initializes callbacks for state updates and thought streaming, then
    delegates execution to the internal workflow engine.

    Args:
        job_id: The unique identifier for the rendering job.
        request: The initial user request details.
        db_session_factory: Factory function for database sessions.
    """
    logger.info(f"Starting background orchestration for job {job_id}")

    async def _update_job_callback(updates: dict[str, Any]) -> None:
        await update_job_status(job_id, updates, db_session_factory)

    async def _on_thought_callback(agent: str, phase: str, content: str) -> None:
        await append_job_thought(db_session_factory, job_id, agent, phase, content)

    try:
        await execute_workflow(
            job_id=job_id,
            topic=request.topic,
            audience=request.target_audience,
            provider=request.provider or "mock",
            model_id=request.model_id or "default",
            update_job=_update_job_callback,
            on_thought=_on_thought_callback,
        )
    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}")


async def execute_workflow(
    job_id: str,
    topic: str,
    audience: str,
    provider: str,
    model_id: str,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> None:
    """Executes the 4-step pedagogical video generation workflow.

    Coordinates between planning, validating, architecting, and animating agents,
    managing state updates and usage tracking throughout the lifecycle.

    Args:
        job_id: The unique identifier for the job.
        topic: The complex technical topic to explain.
        audience: The target knowledge level.
        provider: The selected AI provider (e.g., 'openai', 'groq').
        model_id: The specific model to use (e.g., 'gpt-4o').
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent thoughts to the UI.

    Raises:
        PlanGenerationError: If the curriculum planning phase fails.
        StoryboardGenerationError: If the visual architecting phase fails.
        AnimationGenerationError: If the Manim code generation or rendering fails.
    """
    total_usage: RunUsage | None = None

    def add_usage(u: RunUsage | None) -> None:
        nonlocal total_usage
        total_usage = merge_usage(total_usage, u)

    async with AsyncSessionLocal() as session:
        # 1. Fetch Job State
        stmt = select(JobRecord).where(JobRecord.job_id == job_id)
        res = await session.execute(stmt)
        job_state = res.scalar_one_or_none()

        if not job_state:
            logger.error(f"Job {job_id} not found in database.")
            return

        # 2. Re-construct Request for agents (used for getting models)
        request = JobRequest(
            topic=topic,
            target_audience=audience,
            provider=provider,
            model_id=model_id,
            resolution=cast(Any, job_state.resolution),
            frame_rate=cast(Any, job_state.frame_rate),
            fast_mode=False,
        )

        try:
            # Step 1: Planning
            await update_job(
                {
                    "status": "planning",
                    "current_step": "planning_start",
                    "started_at": datetime.now(UTC),
                }
            )
            if provider == "mock":
                await asyncio.sleep(2)

            plan, usage = await step_planning(
                request, job_state, update_job, on_thought
            )
            if not plan:
                raise PlanGenerationError("Planning failed to produce curriculum.")
            add_usage(usage)

            # Step 2 & 3: Validating and Architecting (Concurrent)
            await update_job(
                {"status": "architecting", "current_step": "parallel_execution"}
            )

            async def run_validating() -> Any:
                if provider == "mock":
                    await asyncio.sleep(2)
                return await step_validating(
                    plan, request, job_state, update_job, on_thought
                )

            async def run_architecting() -> Any:
                if provider == "mock":
                    await asyncio.sleep(2)
                res = await step_architecting(
                    plan, request, job_state, update_job, on_thought
                )
                if not res[0]:
                    raise StoryboardGenerationError(
                        "Architecting failed to produce a storyboard."
                    )
                return res

            async with asyncio.TaskGroup() as tg:
                val_task = tg.create_task(run_validating())
                arch_task = tg.create_task(run_architecting())

            validation, v_usage = val_task.result()
            storyboard, a_usage = arch_task.result()

            add_usage(v_usage)
            add_usage(a_usage)

            # Step 4: Animating
            await update_job({"status": "animating", "current_step": "animating_start"})
            if provider == "mock":
                await asyncio.sleep(2)

            code, m_usage = await step_animating(
                storyboard, request, job_state, update_job, on_thought
            )
            if not code:
                raise AnimationGenerationError("Animating failed to produce code.")
            add_usage(m_usage)

            await update_job({"manim_code": code})

            # Step 5: Rendering (Dispatched to background worker)
            from infra.tasks import render_video_task
            
            await render_video_task.kiq(
                job_id=job_id,
                code=code,
                storyboard_dict=storyboard.model_dump(),
                request_dict=request.model_dump(),
                resolution=cast(str, job_state.resolution),
                frame_rate=cast(int, job_state.frame_rate),
            )
            
            logger.info(f"Job {job_id}: Rendering dispatched to Taskiq worker.")

        except Exception as e:
            logger.exception(f"Workflow failed for job {job_id}: {e}")
            final_cost = calculate_job_cost(total_usage)
            await update_job_record(
                db_session_factory=AsyncSessionLocal,
                job_id=job_id,
                updates={
                    "status": "failed",
                    "error": str(e),
                    "cost": final_cost,
                    "finished_at": datetime.now(UTC),
                },
            )
            raise
