"""Workflow orchestrator for the ConceptCast agent council.

Coordinates the multi-step pedagogical video generation pipeline: topic
refinement, planning, architecting, animating, and rendering dispatch.
Delegates step-specific logic to handler functions while managing session
lifecycle, callbacks, and error recovery.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import structlog
from pydantic_ai.usage import RunUsage
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import JobRequest, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.factory import get_concept_model
from infra.database import AsyncSessionLocal
from infra.exceptions import JobCancelledError, PlanGenerationError
from infra.models.job import JobRecord
from infra.tasks import render_video_task
from services.jobs.topic import refine_topic
from services.workflow.utils import (
    calculate_job_cost,
    merge_usage,
    parse_job_artifact,
)

from ..jobs.manager import (
    perform_job_update,
    prepare_job_for_retry_logic,
    update_job_status,
)
from ..jobs.thoughts import append_job_thought
from .handlers import (
    handle_animating_step,
    handle_architecting_steps,
    handle_planning_step,
    load_job_record,
)

logger = structlog.get_logger(__name__)


async def prepare_job_for_retry(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> JobRecord:
    """Prepares a failed job for re-execution.

    Resets transient state and error flags while preserving foundational
    artifacts from previous successful steps.

    Args:
        job_id: The unique identifier for the job.
        db_session_factory: Factory for providing DB sessions.

    Returns:
        The updated JobRecord in 'pending_retry' state.
    """
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
    logger.info("workflow_background_started", job_id=job_id)

    async with db_session_factory() as session:
        lock = asyncio.Lock()

        async def _update_job_callback(updates: dict[str, object]) -> None:
            """Internal helper to update the job record using the workflow session.

            Args:
                updates: A dictionary of field updates for the JobRecord.
            """
            async with lock:
                await update_job_status(job_id, updates, session)
                await session.commit()

        async def _on_thought_callback(agent: str, phase: str, content: str) -> None:
            """Internal helper to append a thought delta using the workflow session.

            Args:
                agent: The name of the agent generating the thought.
                phase: The current execution phase.
                content: The thought content to append.
            """
            async with lock:
                await append_job_thought(session, job_id, agent, phase, content)
                await session.commit()

        try:
            await execute_workflow(
                session=session,
                job_id=job_id,
                topic=request.topic,
                audience=request.target_audience,
                provider=request.provider or "mock",
                model_id=request.model_id or "default",
                update_job=_update_job_callback,
                on_thought=_on_thought_callback,
            )
        except ExceptionGroup as eg:
            from infra.exceptions import JobCancelledError

            if any(isinstance(exc, JobCancelledError) for exc in eg.exceptions):
                logger.info("workflow_cancelled_by_user", job_id=job_id)
                return

            # Parallel tasks (Validation + Architecting) might fail together
            logger.error("workflow_parallel_error", job_id=job_id, error=str(eg))
            for exc in eg.exceptions:
                logger.error(
                    "workflow_parallel_sub_exception",
                    job_id=job_id,
                    error=str(exc),
                )

            # Use the first exception for the user-facing error message
            first_err = eg.exceptions[0]
            await _update_job_callback({"status": "failed", "error": str(first_err)})
        except Exception as e:
            from infra.exceptions import JobCancelledError

            if isinstance(e, JobCancelledError):
                logger.info("workflow_cancelled_by_user", job_id=job_id)
                return
            logger.error("workflow_background_failed", job_id=job_id, error=str(e))


async def execute_workflow(  # noqa: PLR0915, PLR0913
    session: AsyncSession,
    job_id: str,
    topic: str,
    audience: str,
    provider: str,
    model_id: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> None:
    """Executes the pedagogical video generation workflow."""
    total_usage: RunUsage | None = None

    def add_usage(u: RunUsage | None) -> None:
        nonlocal total_usage
        total_usage = merge_usage(total_usage, u)

    # 1. Fetch Job State
    job_state = await load_job_record(session, job_id)

    # 2. Re-construct Request for agents (used for getting models)
    request = JobRequest(
        topic=topic,
        target_audience=audience,
        provider=provider,
        model_id=model_id,
        hitl_enabled=job_state.hitl_enabled,
        analyst_model=job_state.analyst_model,
        architect_model=job_state.architect_model,
        animator_model=job_state.animator_model,
    )

    # 3. Initialize Global Context (GCO)
    ctx = GlobalContext(
        topic=topic, user_prompt=job_state.user_prompt, target_audience=audience
    )

    # 4. Refine Topic if needed
    if job_state.topic == job_state.user_prompt:
        await on_thought("system", "status", "Refining topic...")
        await update_job({"current_step": "refining_topic"})

        model = get_concept_model(provider, model_id)
        if model:
            refined_topic = await refine_topic(job_state.user_prompt, model)
            await update_job({"topic": refined_topic})
            ctx.topic = refined_topic
            topic = refined_topic
        else:
            logger.warning("refinement_model_unavailable", job_id=job_id)

    try:
        if (
            job_state.current_step == "rendering_failed_needs_fix"
            and job_state.storyboard
        ):
            await _handle_render_repair(
                job_id,
                job_state,
                request,
                provider,
                update_job,
                on_thought,
                ctx,
                add_usage,
            )
            return

        plan, usage_1 = await handle_planning_step(
            job_id, job_state, request, provider, update_job, on_thought, ctx
        )
        add_usage(usage_1)

        # Hard gate: never proceed when curriculum is empty/invalid structurally.
        if not plan.teaching_steps:
            raise PlanGenerationError(
                "Curriculum generation produced no teaching steps after retries."
            )

        # --- Human in the Loop (HITL) Check ---
        if request.hitl_enabled:
            logger.info("workflow_hitl_paused_for_review", job_id=job_id)
            await update_job(
                {"status": "awaiting_review", "current_step": "planning_complete"}
            )
            return
        # ---------------------------------------

        storyboard, usage_3 = await handle_architecting_steps(
            job_id, job_state, request, plan, provider, update_job, on_thought, ctx
        )
        add_usage(usage_3)

        code, usage_4 = await handle_animating_step(
            job_id,
            job_state,
            request,
            storyboard,
            provider,
            update_job,
            on_thought,
            ctx,
            retry_hint=job_state.error,
        )
        add_usage(usage_4)

        # Step 5: Rendering (Dispatched to background worker)
        await render_video_task.kiq(
            job_id=job_id,
            code=code,
            storyboard_dict=storyboard.model_dump(),
            request_dict=request.model_dump(),
        )
        await update_job(
            {"status": "rendering", "current_step": "rendering_dispatched"}
        )

        logger.info("workflow_render_dispatched", job_id=job_id)

        # Update cumulative processing time on success (before final rendering)
        if job_state.started_at:
            started_at = job_state.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            session_duration = (datetime.now(UTC) - started_at).total_seconds()
            await update_job(
                {
                    "total_execution_time": job_state.total_execution_time
                    + session_duration
                }
            )

    except JobCancelledError:
        # Re-raise user-initiated cancellation without logging an error traceback
        raise
    except Exception as e:
        logger.exception("workflow_execution_failed", job_id=job_id, error=str(e))
        final_cost = calculate_job_cost(total_usage)
        session_duration = 0.0
        if job_state.started_at:
            started_at = job_state.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            session_duration = (datetime.now(UTC) - started_at).total_seconds()

        # Update within the same session
        await perform_job_update(
            session,
            job_id,
            {
                "status": "failed",
                "current_step": job_state.current_step or "workflow_failed",
                "error": f"{type(e).__name__}: {e}",
                "cost": final_cost,
                "finished_at": datetime.now(UTC),
                "total_execution_time": job_state.total_execution_time
                + session_duration,
            },
        )
        await session.commit()
        raise


async def _handle_render_repair(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    provider: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    add_usage: Callable[[RunUsage | None], None],
) -> None:
    """Handles the render-repair path for jobs that failed during rendering.

    Reuses the cached storyboard and regenerates animation code with
    render-error hints before re-dispatching to the rendering worker.

    Args:
        job_id: The unique identifier for the job.
        job_state: The current database record for the job.
        request: The reconstructed user request.
        provider: The AI provider to use.
        update_job: Callback for persisting job state updates.
        on_thought: Callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.
        add_usage: Callback for accumulating token usage.
    """
    await on_thought(
        "system",
        "status",
        "Resuming from rendering failure: regenerating animation code with render-error hints.",
    )
    storyboard = parse_job_artifact(job_state.storyboard, Storyboard)
    ctx.storyboard = storyboard
    repair_hint = job_state.error or "Previous rendering attempt failed."
    # Force regeneration instead of reusing the known-bad code.
    await update_job(
        {
            "status": "animating",
            "current_step": "rendering_repair_regenerate_code",
            "manim_code": None,
        }
    )
    code, usage_repair = await handle_animating_step(
        job_id,
        job_state,
        request,
        storyboard,
        provider,
        update_job,
        on_thought,
        ctx,
        retry_hint=(
            f"Repair this render failure. Previous failure details: {repair_hint}"
        ),
    )
    add_usage(usage_repair)
    await render_video_task.kiq(
        job_id=job_id,
        code=code,
        storyboard_dict=storyboard.model_dump(),
        request_dict=request.model_dump(),
    )
    await update_job(
        {
            "status": "rendering",
            "current_step": "rendering_repair_retry_dispatched",
            "error": None,
        }
    )
    logger.info("workflow_repair_render_dispatched", job_id=job_id)
