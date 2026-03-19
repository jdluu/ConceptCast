"""Orchestration layer for the pedagogical video generation workflow.

Coordinates multiple AI agents and background tasks to transform a topic
into a structured curriculum and eventually a rendered Manim animation.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import structlog
from pydantic_ai.usage import RunUsage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.models.workflow import GlobalContext
from infra.database import AsyncSessionLocal
from infra.exceptions import (
    AnimationGenerationError,
    PlanGenerationError,
    StoryboardGenerationError,
)
from infra.models.job import JobRecord
from infra.tasks import render_video_task
from services.workflow.utils import (
    calculate_job_cost,
    merge_usage,
    parse_job_artifact,
)

from ..jobs.manager import (
    _perform_job_update,
    prepare_job_for_retry_logic,
    update_job_status,
)
from ..jobs.thoughts import append_job_thought
from .steps.animating import step_animating
from .steps.architecting import step_architecting
from .steps.planning import step_planning

logger = structlog.get_logger(__name__)


def _structural_validate_curriculum(plan: CurriculumPlan) -> list[str]:
    """Deterministic, non-LLM checks to avoid endless AI validator loops."""
    issues: list[str] = []
    concept = (plan.concept_title or "").strip().lower()
    audience = (plan.target_audience or "").strip().lower()
    if concept in {"", "__missing__", "missing", "tbd", "n/a", "..."}:
        issues.append("concept_title is empty")
    if audience in {"", "__missing__", "missing", "tbd", "n/a", "..."}:
        issues.append("target_audience is empty")
    if not plan.teaching_steps:
        issues.append("teaching_steps is empty")
    else:
        if not 5 <= len(plan.teaching_steps) <= 10:
            issues.append(
                "teaching_steps length must be between 5 and 10 "
                f"(got {len(plan.teaching_steps)})"
            )
        for i, step in enumerate(plan.teaching_steps, start=1):
            if not step.concept or not step.concept.strip():
                issues.append(f"teaching_steps[{i}].concept is empty")
            if not step.visual_metaphor or not step.visual_metaphor.strip():
                issues.append(f"teaching_steps[{i}].visual_metaphor is empty")
            if not step.narration or not step.narration.strip():
                issues.append(f"teaching_steps[{i}].narration is empty")
    return issues


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
            logger.error("workflow_background_failed", job_id=job_id, error=str(e))


async def _handle_planning_step(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    _provider: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
) -> tuple[CurriculumPlan, RunUsage | None]:
    """Handles Step 1 (Planning) including deterministic structural retries.

    Args:
        job_id: The unique identifier for the job.
        job_state: The current database record for the job.
        request: The initial user request.
        _provider: The AI provider to use.
        update_job: Callback for persisting job state updates.
        on_thought: Callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (CurriculumPlan, Total RunUsage).

    Raises:
        PlanGenerationError: If planning fails to produce a valid curriculum after retries.
    """
    await update_job(
        {
            "status": "planning",
            "current_step": "planning_start",
            "started_at": datetime.now(UTC),
        }
    )

    plan: CurriculumPlan | None = None
    if job_state.plan:
        logger.info("planning_cached_plan_reused", job_id=job_id)
        await on_thought("system", "status", "Using cached pedagogical plan...")
        cached_plan = parse_job_artifact(job_state.plan, CurriculumPlan)
        ctx.plan = cached_plan
        return cached_plan, None

    total_usage = RunUsage()
    max_retries = 3
    current_attempt = 0
    last_feedback = ""

    while current_attempt < max_retries:
        current_attempt += 1
        attempt_prefix = f"[Attempt {current_attempt}/{max_retries}] "
        attempt_prefix_local = attempt_prefix

        async def _on_thought_attempt(
            agent: str,
            phase: str,
            content: str,
            attempt_prefix_local: str = attempt_prefix_local,
        ) -> None:
            if phase == "structured_output" and agent == "analyst":
                await on_thought(agent, phase, f"{attempt_prefix_local}{content}")
                return
            await on_thought(agent, phase, content)

        await on_thought(
            "system",
            "status",
            f"{attempt_prefix}Generating curriculum for: {request.topic}",
        )

        try:
            plan, p_usage = await step_planning(
                request,
                job_state,
                update_job,
                _on_thought_attempt,
                ctx,
                force_generate=current_attempt > 1,
                retry_hint=last_feedback or None,
            )
        except PlanGenerationError as e:
            last_feedback = str(e)
            await on_thought(
                "system",
                "status",
                f"{attempt_prefix}Curriculum generation failed structural checks:\n{last_feedback}",
            )
            logger.warning(
                "planning_attempt_failed",
                job_id=job_id,
                attempt=current_attempt,
                max_retries=max_retries,
                feedback=last_feedback,
            )
            if current_attempt >= max_retries:
                raise
            continue

        total_usage = merge_usage(total_usage, p_usage)
        ctx.plan = plan
        break

    if not plan:
        raise PlanGenerationError(
            "Failed to generate any curriculum plan after retries."
        )

    # Deterministic curriculum preflight pass after a structurally valid plan exists.
    await update_job({"status": "planning", "current_step": "curriculum_preflight"})
    await on_thought(
        "system",
        "status",
        f"[Attempt {current_attempt}/{max_retries}] Structural preflight check for curriculum...",
    )
    issues = _structural_validate_curriculum(plan)
    if issues:
        await on_thought(
            "system",
            "status",
            f"[Attempt {current_attempt}/{max_retries}] Structural preflight issues:\n- "
            + "\n- ".join(issues),
        )
        logger.warning(
            "planning_structural_issues_after_retries",
            job_id=job_id,
            issues=issues,
        )
        raise PlanGenerationError(
            "Structural preflight failed and cannot proceed.\n- " + "\n- ".join(issues)
        )

    # Persist the final state.
    await update_job(
        {
            "plan": plan.model_dump() if plan else None,
            "current_step": "planning_complete",
        }
    )

    return plan, total_usage


async def _handle_architecting_steps(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    plan: CurriculumPlan,
    _provider: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
) -> tuple[Storyboard, RunUsage | None]:
    """Handles Step 3 (Architecting) to produce the visual storyboard.

    Args:
        job_id: The unique identifier for the job.
        job_state: The current database record for the job.
        request: The initial user request.
        plan: The structurally valid curriculum plan.
        _provider: The AI provider to use.
        update_job: Callback for persisting job state updates.
        on_thought: Callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (Storyboard, RunUsage or None).

    Raises:
        StoryboardGenerationError: If architecting fails to produce a valid storyboard.
    """
    if job_state.storyboard:
        logger.info("architecting_cached_storyboard_reused", job_id=job_id)
        await on_thought("system", "status", "Using cached storyboard...")
        arch = parse_job_artifact(job_state.storyboard, Storyboard)
        ctx.storyboard = arch
        return arch, None

    await on_thought("system", "status", "Starting visual architecting...")
    await update_job(
        {"status": "architecting", "current_step": "storyboard_generation"}
    )

    storyboard, a_usage = await step_architecting(
        plan, request, job_state, update_job, on_thought, ctx, persist=True
    )

    if not storyboard or not storyboard.scenes:
        raise StoryboardGenerationError(
            "Architecting failed to produce a valid storyboard with scenes."
        )

    ctx.storyboard = storyboard
    return storyboard, a_usage


async def _handle_animating_step(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    storyboard: Storyboard,
    _provider: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    retry_hint: str | None = None,
) -> tuple[str, RunUsage | None]:
    """Handles Step 4 (Animating) including iterative code generation.

    Args:
        job_id: The unique identifier for the job.
        job_state: The current database record for the job.
        request: The initial user request.
        storyboard: The visual sequence to animate.
        _provider: The AI provider to use.
        update_job: Callback for persisting job state updates.
        on_thought: Callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (The generated Manim Python code, RunUsage data or None).

    Raises:
        AnimationGenerationError: If the animation step fails to produce valid code.
    """
    if job_state.manim_code:
        logger.info("animating_cached_code_reused", job_id=job_id)
        await on_thought("system", "status", "Using cached Manim code...")
        ctx.manim_code = job_state.manim_code
        return job_state.manim_code, None

    await on_thought("system", "status", "Generating Manim animation script...")
    await update_job({"status": "animating", "current_step": "animating_start"})

    code, m_usage = await step_animating(
        storyboard,
        request,
        job_state,
        update_job,
        on_thought,
        ctx,
        initial_hint=retry_hint,
    )
    if not code:
        raise AnimationGenerationError("Animating failed to produce code.")

    ctx.manim_code = code
    await update_job({"manim_code": code})
    return code, m_usage


async def execute_workflow(  # noqa: PLR0915
    session: AsyncSession,
    job_id: str,
    topic: str,
    audience: str,
    provider: str,
    model_id: str,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> None:
    """Executes the pedagogical video generation workflow.

    Coordinates between planning, architecting, and animating agents,
    managing state updates and usage tracking throughout the lifecycle.

    Args:
        session: Active persistent database session.
        job_id: The unique identifier for the job.
        topic: The complex technical topic to explain.
        audience: The target knowledge level.
        provider: The selected AI provider (e.g., 'nano').
        model_id: The specific model to use (e.g., 'nvidia/nemotron-3-super-120b-a12b:thinking').
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent thoughts to the UI.

    Raises:
        PlanGenerationError: If the curriculum planning phase fails.
        StoryboardGenerationError: If the visual architecting phase fails.
        AnimationGenerationError: If the Manim code generation or rendering fails.
    """
    total_usage: RunUsage | None = None

    def add_usage(u: RunUsage | None) -> None:
        """Helper to accumulate token usage across multiple workflow steps.

        Args:
            u: Usage information from a completed AI run.
        """
        nonlocal total_usage
        total_usage = merge_usage(total_usage, u)

    async def sync_cost() -> None:
        """Calculates and persists current cumulative cost."""
        current_cost = calculate_job_cost(total_usage)
        await update_job({"cost": current_cost})

    # 1. Fetch Job State
    stmt = select(JobRecord).where(JobRecord.job_id == job_id)
    res = await session.execute(stmt)
    job_state = res.scalar_one_or_none()

    if not job_state:
        logger.error("workflow_job_not_found", job_id=job_id)
        return

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
    ctx = GlobalContext(topic=topic, target_audience=audience)

    try:
        if (
            job_state.current_step == "rendering_failed_needs_fix"
            and job_state.storyboard
        ):
            await on_thought(
                "system",
                "status",
                "Resuming from rendering failure: regenerating animation code with render-error hints.",
            )
            storyboard = parse_job_artifact(job_state.storyboard, Storyboard)
            ctx.storyboard = storyboard
            repair_hint = job_state.error or "Previous rendering attempt failed."
            # Force regeneration instead of reusing the known-bad code.
            job_state.manim_code = None
            await update_job(
                {
                    "status": "animating",
                    "current_step": "rendering_repair_regenerate_code",
                    "manim_code": None,
                }
            )
            code, usage_repair = await _handle_animating_step(
                job_id,
                job_state,
                request,
                storyboard,
                provider,
                update_job,
                on_thought,
                ctx,
                retry_hint=(
                    "Repair this render failure. "
                    f"Previous failure details: {repair_hint}"
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
            return

        plan, usage_1 = await _handle_planning_step(
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

        storyboard, usage_3 = await _handle_architecting_steps(
            job_id, job_state, request, plan, provider, update_job, on_thought, ctx
        )
        add_usage(usage_3)

        code, usage_4 = await _handle_animating_step(
            job_id,
            job_state,
            request,
            storyboard,
            provider,
            update_job,
            on_thought,
            ctx,
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
        await _perform_job_update(
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
