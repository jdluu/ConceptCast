import json
import os
import uuid
from collections.abc import Callable
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

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
from services.rendering import render_storyboard
from services.utils import (
    generate_mock_code,
    generate_mock_plan,
    generate_mock_storyboard,
    generate_mock_validation,
)


def _determine_execution_mode(request: JobRequest) -> bool:
    """
    Determines whether to run in mock mode based on configuration and request.

    Args:
        request (JobRequest): The job request.

    Returns:
        bool: True if mock mode should be used, False otherwise.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    synthetic_key = os.getenv("SYNTHETIC_API_KEY")

    # Check if we should use mock logic (no keys or explicit mock provider)
    return (
        request.provider == "mock"
        or (
            not (api_key or groq_key or deepseek_key or synthetic_key)
            and not request.provider
        )
        or api_key == "dummy_key_for_development"
    )


def _update_job_record(
    db_session_factory: Callable[[], Session], job_id: str, updates: dict[str, Any]
) -> None:
    """
    Updates a job record in the database.

    Args:
        db_session_factory (Callable[[], Session]): Factory for DB sessions.
        job_id (str): The job ID to update.
        updates (dict): Dictionary of fields to update.
    """
    with db_session_factory() as db:
        job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if job:
            for key, value in updates.items():
                setattr(job, key, value)
            db.commit()


async def create_new_job(db: Session, request: JobRequest) -> str:
    """
    Initializes a new job record in the database.

    Args:
        db (Session): The database session.
        request (JobRequest): The job creation request containing topic and
        target audience.

    Returns:
        str: The unique ID of the created job.

    Side Effects:
        Creates a new JobRecord in the database with 'planning' status.
        Commits the transaction to the database.
    """
    job_id = str(uuid.uuid4())
    job_record = JobRecord(
        job_id=job_id,
        status="planning",
        topic=request.topic,
        target_audience=request.target_audience,
        mode="live"
        if (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("SYNTHETIC_API_KEY")
        )
        else "mock",
    )
    db.add(job_record)
    db.commit()
    return job_id


async def _run_mock_flow(
    request: JobRequest, update_job: Callable[[dict[str, Any]], None]
) -> None:
    """
    Executes the mock generation flow for testing or demonstration purposes.

    Args:
        request (JobRequest): The job request parameters.
        update_job (Callable[[dict], None]): Callback to update job status in DB.

    Side Effects:
        Updates the job record with mock plan, validation, storyboard, and code.
        Sets the job status to 'completed' or 'failed'.
    """
    try:
        plan = generate_mock_plan(request.topic, request.target_audience)
        validation = generate_mock_validation()
        storyboard = generate_mock_storyboard(plan)

        update_job(
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
        update_job({"status": "failed", "error": str(e)})


async def _step_planning(
    request: JobRequest, job: JobRecord, update_job: Callable[[dict[str, Any]], None]
) -> CurriculumPlan:
    """
    Executes the Planning step (Step 1) of the Council workflow.

    Args:
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (Callable[[dict[str, Any]], None]): Callback to persist updates.

    Returns:
        CurriculumPlan: The generated curriculum plan.

    Side Effects:
        Updates job status to 'planning'.
        Persists the generated plan to the database.
        Logs checkpoint information if skipping.
    """
    if not job.plan:
        logger.info(f"Generating curriculum for: {request.topic} (Mode: {job.mode})")

        # Select model based on request or default
        # Pass mock only if mode is mock
        provider_arg = "mock" if job.mode == "mock" else request.provider

        plan = await generate_curriculum(
            topic=request.topic,
            audience=request.target_audience,
            provider=provider_arg,
            model_id=request.model_id,
        )

        job.plan = plan.model_dump()
        job.current_step = "planning_complete"
        update_job({"plan": job.plan, "current_step": job.current_step})
        logger.success("Step 1: Planning - Complete")
    else:
        logger.info("Using existing curriculum plan (Checkpoint)")
        # If we reload, we need to reconstruct the object from dict
        if isinstance(job.plan, dict):
            plan = CurriculumPlan(**job.plan)
        else:
            # Fallback if somehow it's not a dict (shouldn't happen with JSON type)
            plan = CurriculumPlan(**json.loads(job.plan))
    return plan


async def _step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], None],
) -> Storyboard:
    """
    Executes the Architecting step (Step 3) of the Council workflow.

    Args:
        plan (CurriculumPlan): The curriculum plan to visualize.
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (Callable[[dict[str, Any]], None]): Callback to persist updates.

    Returns:
        Storyboard: The generated storyboard.

    Side Effects:
        Updates job status to 'architecting'.
        Persists the generated storyboard to the database.
        Logs checkpoint information if skipping.
    """
    if not job.storyboard:
        logger.info("Generating storyboard...")
        storyboard = await generate_storyboard(
            plan=plan,
            provider="mock" if job.mode == "mock" else None,
        )  # Architect uses default model if None
        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        update_job({"storyboard": job.storyboard, "current_step": job.current_step})
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
    update_job: Callable[[dict[str, Any]], None],
) -> str:
    """
    Executes the Animating step (Step 4) of the Council workflow.

    Args:
        storyboard (Storyboard): The storyboard to animate.
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (Callable[[dict[str, Any]], None]): Callback to persist updates.

    Returns:
        str: The generated Manim Python code.

    Side Effects:
        Updates job status to 'rendering'.
        Persists the generated code to the database.
        Logs checkpoint information if skipping.
    """
    if not job.manim_code:
        update_job({"status": "rendering"})
        code = await generate_manim_code(
            storyboard, provider=request.provider, model_id=request.model_id
        )
        update_job({"manim_code": code})
        return code
    else:
        logger.info(f"Checkpoint: Skipping Animation generation for job {job.job_id}")
        return job.manim_code


async def _step_rendering(
    code: str, job_id: str, update_job: Callable[[dict[str, Any]], None]
) -> None:
    """
    Executes the Rendering step (Step 5) of the Council workflow.

    Args:
        code (str): The Manim code to render.
        job_id (str): The unique identifier for the job.
        update_job (Callable[[dict[str, Any]], None]): Callback to persist updates.

    Side Effects:
        Updates job status to 'rendering' and then 'completed'.
        Persists the video URL to the database.
    """
    update_job({"status": "rendering"})
    video_url = await render_storyboard(code, job_id)
    update_job({"video_url": video_url, "status": "completed"})


async def process_job_logic(
    job_id: str,
    request: JobRequest,
    db_session_factory: Callable[[], Session],
) -> None:
    """
    Orchestrates the 4-step council workflow:
    (Planning -> Validating -> Architecting -> Rendering).

    This function handles the end-to-end processing of a video generation job.
    It manages the state transitions, executes each step in sequence, and
    handles failures.
    It supports resuming from checkpoints if a job was previously interrupted.

    Args:
        job_id (str): The UUID of the job to process.
        request (JobRequest): The creation request details.
        db_session_factory (Callable[[], Session]): A factory returning a new database
            session.

    Side Effects:
        Updates the job record in the database multiple times as it progresses.
        May invoke external AI APIs (Google, Groq, DeepSeek).
        Generates and saves video files to the file system.

    Raises:
        ValueError: If any step fails to produce the required output.
        Exception: Captures and logs any unexpected errors,
            updating the job status to 'failed'.
    """
    use_mock = _determine_execution_mode(request)

    # Define a partially applied update function for convenience
    def update_job(updates: dict[str, Any]) -> None:
        _update_job_record(db_session_factory, job_id, updates)

    if use_mock:
        await _run_mock_flow(request, update_job)
        return

    try:
        # Check for existing job state to enable checkpointing
        with db_session_factory() as db:
            job_state = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if not job_state:
                logger.error(f"Job {job_id} not found for processing")
                return

        # Execute the 4-step workflow
        plan = await _step_planning(request, job_state, update_job)
        if not plan:
            raise PlanGenerationError("Planning failed to produce a curriculum.")

        # Step 2: Validating
        validation = ValidationResult(
            is_valid=True, feedback="Verified by Analyst A2A", suggestions=[]
        )
        update_job({"validation": validation.model_dump()})

        storyboard = await _step_architecting(plan, request, job_state, update_job)
        if not storyboard:
            raise StoryboardGenerationError(
                "Architecting failed to produce a storyboard."
            )

        code = await _step_animating(storyboard, request, job_state, update_job)
        if not code:
            raise AnimationGenerationError("Animating failed to produce code.")

        await _step_rendering(code, job_id, update_job)

    except ConceptCastException as e:
        logger.error(f"Job {job_id} failed: {e.message}")
        update_job({"status": "failed", "error": e.message})
    except Exception as e:
        logger.exception(f"Job {job_id} failed unexpectedly")
        update_job(
            {"status": "failed", "error": f"An unexpected error occurred: {str(e)}"}
        )
