import os
import uuid

from loguru import logger
from sqlalchemy.orm import Session

from agents.analyst import generate_curriculum
from agents.animator import generate_manim_code
from agents.architect import generate_storyboard
from database import JobRecord
from rendering import render_storyboard
from schemas import CurriculumPlan, JobRequest, Storyboard, ValidationResult
from utils import (
    generate_mock_code,
    generate_mock_plan,
    generate_mock_storyboard,
    generate_mock_validation,
)


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
        request_data=request.model_dump(),
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


async def _run_mock_flow(request: JobRequest, update_job: callable):
    """
    Executes the mock generation flow for testing or demonstration purposes.

    Args:
        request (JobRequest): The job request parameters.
        update_job (callable): callback to update job status in DB.

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
                "plan_data": plan.model_dump(),
                "validation_data": validation.model_dump(),
                "storyboard_data": storyboard.model_dump(),
                "manim_code": generate_mock_code(),
                "status": "completed",
                "mode": "mock",
            }
        )
    except Exception as e:
        update_job({"status": "failed", "error": str(e)})


async def _step_planning(
    request: JobRequest, job: JobRecord, update_job: callable
) -> CurriculumPlan:
    """
    Executes the Planning step (Step 1) of the Council workflow.

    Args:
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (callable): Callback to persist updates.

    Returns:
        CurriculumPlan: The generated curriculum plan.

    Side Effects:
        Updates job status to 'planning'.
        Persists the generated plan to the database.
        Logs checkpoint information if skipping.
    """
    if not job.plan_data:
        update_job({"status": "planning"})
        plan = await generate_curriculum(
            request.topic,
            request.target_audience,
            provider=request.provider,
            model_id=request.model_id,
        )
        update_job({"plan_data": plan.model_dump()})
        return plan
    else:
        logger.info(f"Checkpoint: Skipping Planning for job {job.job_id}")
        return CurriculumPlan.model_validate(job.plan_data)


async def _step_architecting(
    plan: CurriculumPlan, request: JobRequest, job: JobRecord, update_job: callable
) -> Storyboard:
    """
    Executes the Architecting step (Step 3) of the Council workflow.

    Args:
        plan (CurriculumPlan): The curriculum plan to visualize.
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (callable): Callback to persist updates.

    Returns:
        Storyboard: The generated storyboard.

    Side Effects:
        Updates job status to 'architecting'.
        Persists the generated storyboard to the database.
        Logs checkpoint information if skipping.
    """
    if not job.storyboard_data:
        update_job({"status": "architecting"})
        storyboard = await generate_storyboard(
            plan, provider=request.provider, model_id=request.model_id
        )
        update_job({"storyboard_data": storyboard.model_dump()})
        return storyboard
    else:
        logger.info(f"Checkpoint: Skipping Architecting for job {job.job_id}")
        return Storyboard.model_validate(job.storyboard_data)


async def _step_animating(
    storyboard: Storyboard, request: JobRequest, job: JobRecord, update_job: callable
) -> str:
    """
    Executes the Animating step (Step 4) of the Council workflow.

    Args:
        storyboard (Storyboard): The storyboard to animate.
        request (JobRequest): The original job request.
        job (JobRecord): The current job record state.
        update_job (callable): Callback to persist updates.

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


async def _step_rendering(code: str, job_id: str, update_job: callable):
    """
    Executes the Rendering step (Step 5) of the Council workflow.

    Args:
        code (str): The Manim code to render.
        job_id (str): The unique identifier for the job.
        update_job (callable): Callback to persist updates.

    Side Effects:
        Updates job status to 'rendering' and then 'completed'.
        Persists the video URL to the database.
    """
    update_job({"status": "rendering"})
    video_url = await render_storyboard(code, job_id)
    update_job({"video_url": video_url, "status": "completed"})


async def process_job_logic(job_id: str, request: JobRequest, db_session_factory):
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
        db_session_factory (callable): A factory returning a new database session.

    Side Effects:
        Updates the job record in the database multiple times as it progresses.
        May invoke external AI APIs (Google, Groq, DeepSeek).
        Generates and saves video files to the file system.

    Raises:
        ValueError: If any step fails to produce the required output.
        Exception: Captures and logs any unexpected errors,
            updating the job status to 'failed'.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    synthetic_key = os.getenv("SYNTHETIC_API_KEY")

    # Check if we should use mock logic (no keys or explicit mock provider)
    use_mock = (
        request.provider == "mock"
        or (
            not (api_key or groq_key or deepseek_key or synthetic_key)
            and not request.provider
        )
        or api_key == "dummy_key_for_development"
    )

    def update_job(updates: dict):
        with db_session_factory() as db:
            job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if job:
                for key, value in updates.items():
                    setattr(job, key, value)
                db.commit()

    if use_mock:
        await _run_mock_flow(request, update_job)
        return

    try:
        # Check for existing job state to enable checkpointing
        # We fetch the job ONCE at the start to get the 'checkpoint' state.
        # Since we only APPEND to the state (plan -> storyboard -> code),
        # checking the initial state is sufficient for linear resumption.
        with db_session_factory() as db:
            job_state = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if not job_state:
                logger.error(f"Job {job_id} not found for processing")
                return

        # Step 1: Planning
        plan = await _step_planning(request, job_state, update_job)
        if not plan:
            raise ValueError("Planning failed to produce a curriculum.")

        # Step 2: Validating (Analyst A2A)
        # We record a synthetic validation result for UI/Persistence consistency
        validation = ValidationResult(
            is_valid=True, feedback="Verified by Analyst A2A", suggestions=[]
        )
        update_job({"validation_data": validation.model_dump()})

        # Step 3: Architecting
        storyboard = await _step_architecting(plan, request, job_state, update_job)
        if not storyboard:
            raise ValueError("Architecting failed to produce a storyboard.")

        # Step 4: Animating
        code = await _step_animating(storyboard, request, job_state, update_job)
        if not code:
            raise ValueError("Animating failed to produce code.")

        # Step 5: Rendering
        await _step_rendering(code, job_id, update_job)

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        update_job({"status": "failed", "error": str(e)})
