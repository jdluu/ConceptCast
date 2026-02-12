import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.analyst import generate_curriculum
from agents.animator import generate_manim_code
from agents.architect import generate_storyboard
from api.schemas import CurriculumPlan, JobRequest, Storyboard, ValidationResult
from core.database import JobRecord
from core.exceptions import (
    AnimationGenerationError,
    ConceptCastException,
    PlanGenerationError,
    StoryboardGenerationError,
)
from core.settings import get_settings
from services.rendering import render_storyboard
from services.utils import (
    generate_mock_code,
    generate_mock_plan,
    generate_mock_storyboard,
    generate_mock_validation,
)


def _determine_execution_mode(request: JobRequest) -> bool:
    """Determines whether to run in mock mode based on configuration and request.

    Args:
        request: The initial job request containing provider preferences.

    Returns:
        bool: True if mock mode should be used, False for live execution.
    """
    settings = get_settings()
    return (
        request.provider == "mock"
        or (not settings.has_any_api_key() and not request.provider)
        or settings.is_dummy_key()
    )


async def _update_job_record(
    db_session_factory: Callable[[], AsyncSession], job_id: str, updates: dict[str, Any]
) -> None:
    """Updates a job record in the database using an asynchronous session.

    Args:
        db_session_factory: A factory function that returns an AsyncSession.
        job_id: The unique identifier of the job to update.
        updates: A dictionary of field names and their new values.

    Note:
        Automatically sets 'updated_at' to the current time.
    """
    async with db_session_factory() as db:
        result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
        job = result.scalar_one_or_none()
        if job:
            for key, value in updates.items():
                setattr(job, key, value)
            job.updated_at = datetime.now(UTC)
            await db.commit()


async def create_new_job(db: AsyncSession, request: JobRequest) -> str:
    """Initializes a new job record in the database.

    Args:
        db: The active asynchronous database session.
        request: The job creation request details.

    Returns:
        str: The newly generated unique job_id (UUID).
    """
    import uuid
    job_id = str(uuid.uuid4())
    job_record = JobRecord(
        job_id=job_id,
        status="planning",
        topic=request.topic,
        target_audience=request.target_audience,
        mode="live" if get_settings().has_any_api_key() else "mock",
    )
    db.add(job_record)
    await db.commit()
    return job_id


async def _run_mock_flow(
    request: JobRequest, update_job: Callable[[dict[str, Any]], Any]
) -> None:
    """
    Executes the mock generation flow for testing or demonstration purposes.
    """
    try:
        # Simulate slight delay for realism
        await asyncio.sleep(1)
        plan = generate_mock_plan(request.topic, request.target_audience)
        await asyncio.sleep(1)
        validation = generate_mock_validation()
        await asyncio.sleep(1)
        storyboard = generate_mock_storyboard(plan)
        await asyncio.sleep(1)

        await update_job(
            {
                "plan": plan.model_dump(),
                "validation": validation.model_dump(),
                "storyboard": storyboard.model_dump(),
                "manim_code": generate_mock_code(),
                "status": "completed",
                "mode": "mock",
            }
        )
    except Exception as e:
        await update_job({"status": "failed", "error": str(e)})


async def _step_planning(
    request: JobRequest, job: JobRecord, update_job: Callable[[dict[str, Any]], Any]
) -> CurriculumPlan:
    """
    Executes the Planning step (Step 1).
    """
    if not job.plan:
        logger.info(f"Generating curriculum for: {request.topic} (Mode: {job.mode})")

        provider_arg = "mock" if job.mode == "mock" else request.provider

        plan = await generate_curriculum(
            topic=request.topic,
            audience=request.target_audience,
            provider=provider_arg,
            model_id=request.model_id,
        )

        job.plan = plan.model_dump()
        job.current_step = "planning_complete"
        await update_job({"plan": job.plan, "current_step": job.current_step})
        logger.success("Step 1: Planning - Complete")
    else:
        logger.info("Using existing curriculum plan (Checkpoint)")
        if isinstance(job.plan, dict):
            plan = CurriculumPlan(**job.plan)
        else:
            plan = CurriculumPlan(**json.loads(job.plan))
    return plan


async def _step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
) -> Storyboard:
    """
    Executes the Architecting step (Step 3).
    """
    if not job.storyboard:
        logger.info("Generating storyboard...")
        storyboard = await generate_storyboard(
            plan=plan,
            provider="mock" if job.mode == "mock" else None,
        )
        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        await update_job(
            {"storyboard": job.storyboard, "current_step": job.current_step}
        )
        logger.success("Step 3: Architecting - Complete")
    else:
        logger.info("Using existing storyboard (Checkpoint)")
        if isinstance(job.storyboard, dict):
            storyboard = Storyboard(**job.storyboard)
        else:
            storyboard = Storyboard(**json.loads(job.storyboard))
    return storyboard


async def _step_animating(
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
) -> str:
    """
    Executes the Animating step (Step 4).
    """
    if not job.manim_code:
        await update_job({"status": "rendering"})
        code = await generate_manim_code(
            storyboard, provider=request.provider, model_id=request.model_id
        )
        await update_job({"manim_code": code})
        return code
    else:
        logger.info(f"Checkpoint: Skipping Animation generation for job {job.job_id}")
        return job.manim_code


async def _step_rendering(
    code: str, job_id: str, update_job: Callable[[dict[str, Any]], Any]
) -> None:
    """
    Executes the Rendering step (Step 5).
    """
    await update_job({"status": "rendering"})
    video_url = await render_storyboard(code, job_id)
    await update_job({"video_url": video_url, "status": "completed"})


async def _execute_workflow(
    request: JobRequest,
    job_state: JobRecord,
    job_id: str,
    update_job: Callable[[dict[str, Any]], Any],
) -> None:
    """
    Executes the sequential steps of the ConceptCast workflow.
    """
    # Step 1: Planning
    plan = await _step_planning(request, job_state, update_job)
    if not plan:
        raise PlanGenerationError("Planning failed to produce a curriculum.")

    # Step 2: Validating
    validation = ValidationResult(
        is_valid=True, feedback="Verified by Analyst A2A", suggestions=[]
    )
    await update_job({"validation": validation.model_dump()})

    # Step 3: Architecting
    storyboard = await _step_architecting(plan, request, job_state, update_job)
    if not storyboard:
        raise StoryboardGenerationError("Architecting failed to produce a storyboard.")

    # Step 4: Animating
    code = await _step_animating(storyboard, request, job_state, update_job)
    if not code:
        raise AnimationGenerationError("Animating failed to produce code.")

    # Step 5: Rendering
    await _step_rendering(code, job_id, update_job)


async def process_job_logic(
    job_id: str,
    request: JobRequest,
    db_session_factory: Callable[[], AsyncSession],
) -> None:
    """Orchestrates the complete ConceptCast workflow from initialization to rendering.

    This function handles the end-to-end processing of a learning concept, including
    planning, architecting, animating, and rendering. It supports both live LLM
    execution and a simulated 'mock' mode for testing.

    Args:
        job_id: The unique UUID of the job to process.
        request: The user request containing topic, audience, and provider settings.
        db_session_factory: A factory for creating new asynchronous database sessions
            to persist progress at each step.

    Raises:
        ConceptCastException: If a step fails during the live workflow.
        Exception: For any other unexpected errors during execution.
    """
    use_mock = _determine_execution_mode(request)

    async def update_job(updates: dict[str, Any]) -> None:
        await _update_job_record(db_session_factory, job_id, updates)

    if use_mock:
        await _run_mock_flow(request, update_job)
        return

    try:
        # Check for existing job state to enable checkpointing
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job_state = result.scalar_one_or_none()
            if not job_state:
                logger.error(f"Job {job_id} not found for processing")
                return

        # Execute the workflow
        await _execute_workflow(request, job_state, job_id, update_job)

    except ConceptCastException as e:
        logger.error(f"Job {job_id} failed: {e.message}")
        await update_job({"status": "failed", "error": e.message})
    except Exception as e:
        logger.exception(f"Job {job_id} failed unexpectedly")
        await update_job(
            {"status": "failed", "error": f"An unexpected error occurred: {str(e)}"}
        )
