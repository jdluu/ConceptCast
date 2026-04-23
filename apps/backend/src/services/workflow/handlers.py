"""Step handler functions for the orchestration workflow.

These handlers wrap the core step modules (planning, architecting, animating)
with retry logic, caching, GCO state management, and progress reporting.
They form the bridge between the orchestrator's callback system and the
individual agent step implementations.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import structlog
from pydantic_ai.usage import RunUsage
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.models.workflow import GlobalContext
from infra.exceptions import (
    AnimationGenerationError,
    PlanGenerationError,
    StoryboardGenerationError,
)
from infra.models.job import JobRecord
from services.workflow.utils import merge_usage, parse_job_artifact

from .steps.animating import step_animating
from .steps.architecting import step_architecting
from .steps.planning import step_planning

logger = structlog.get_logger(__name__)

#: Type alias for the job update callback used throughout the workflow.
UpdateJobFn = Callable[[dict[str, object]], Awaitable[None]]

#: Type alias for the thought streaming callback.
OnThoughtFn = Callable[[str, str, str], Awaitable[None]]


async def handle_planning_step(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    _provider: str,
    update_job: UpdateJobFn,
    on_thought: OnThoughtFn,
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
        tuple[CurriculumPlan, RunUsage | None]: The generated plan and total token usage.

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
    is_valid, issues = plan.is_structurally_valid()
    if not is_valid:
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


async def handle_architecting_steps(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    plan: CurriculumPlan,
    _provider: str,
    update_job: UpdateJobFn,
    on_thought: OnThoughtFn,
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
        tuple[Storyboard, RunUsage | None]: The generated storyboard and total token usage.

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


async def handle_animating_step(
    job_id: str,
    job_state: JobRecord,
    request: JobRequest,
    storyboard: Storyboard,
    _provider: str,
    update_job: UpdateJobFn,
    on_thought: OnThoughtFn,
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
        retry_hint: Optional hint from a previous failed render attempt.

    Returns:
        tuple[str, RunUsage | None]: The generated Manim code and total token usage.

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


async def load_job_record(session: AsyncSession, job_id: str) -> JobRecord:
    """Fetches a JobRecord or raises a descriptive error.

    Args:
        session: The active database session.
        job_id: The unique identifier for the job.

    Returns:
        The fetched JobRecord.

    Raises:
        RuntimeError: If the job is not found.
    """
    from sqlalchemy import select

    stmt = select(JobRecord).where(JobRecord.job_id == job_id)
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        logger.error("workflow_job_not_found", job_id=job_id)
        raise RuntimeError(f"Job {job_id} not found in database.")
    return job
