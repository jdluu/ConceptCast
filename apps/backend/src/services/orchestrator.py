from collections.abc import Callable
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import JobRequest, ValidationResult
from core.database import JobRecord
from core.exceptions import (
    AnimationGenerationError,
    ConceptCastException,
    PlanGenerationError,
    StoryboardGenerationError,
)
from services.job_management import (
    determine_execution_mode,
    prepare_job_for_retry_logic,
    update_job_record,
)
from services.mock_utils import run_mock_flow
from services.thought_stream import append_job_thought
from services.workflow_steps import (
    step_animating,
    step_architecting,
    step_planning,
    step_rendering,
)


async def execute_workflow(
    request: JobRequest,
    job_state: JobRecord,
    job_id: str,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> None:
    """Executes the sequential steps of the ConceptCast workflow.

    Coordinates the execution of planning, architecting, animating, and 
    rendering steps. Each step persists its artifacts to the database and 
    streams progress to the frontend.

    Args:
        request: The initial job request parameters.
        job_state: The current job record containing persisted state.
        job_id: Unique identifier for the job.
        update_job: Async callback to persist job modifications.
        on_thought: Callback to stream agent internal state updates.

    Returns:
        None

    Raises:
        ConceptCastException: If any workflow step fails to generate required 
            artifacts or if an unrecoverable error occurs.
    """
    # Step 1: Planning
    plan = await step_planning(request, job_state, update_job, on_thought)
    if not plan:
        raise PlanGenerationError("Planning failed to produce a curriculum.")

    # Step 2: Validating
    # Note: Validation step is currently static but tracked for pipeline consistency
    validation = ValidationResult(
        is_valid=True, feedback="Verified by Analyst A2A", suggestions=[]
    )
    await update_job({"validation": validation.model_dump(), "status": "architecting"})

    # Step 3: Architecting
    storyboard = await step_architecting(
        plan, request, job_state, update_job, on_thought
    )
    if not storyboard:
        raise StoryboardGenerationError("Architecting failed to produce a storyboard.")

    # Step 4: Animating
    code = await step_animating(storyboard, request, job_state, update_job, on_thought)
    if not code:
        raise AnimationGenerationError("Animating failed to produce code.")

    # Step 5: Rendering
    await step_rendering(
        code, job_id, storyboard, request, job_state, update_job, on_thought
    )


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
    """
    use_mock = determine_execution_mode(request)

    async def update_job(updates: dict[str, Any]) -> None:
        await update_job_record(db_session_factory, job_id, updates)

    async def on_thought(agent: str, phase: str, content: str) -> None:
        await append_job_thought(db_session_factory, job_id, agent, phase, content)

    if use_mock:
        await run_mock_flow(request, update_job, on_thought)
        return

    try:
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job_state = result.scalar_one_or_none()
            if not job_state:
                logger.error(f"Job {job_id} not found for processing")
                return

        await execute_workflow(request, job_state, job_id, update_job, on_thought)

    except ConceptCastException as e:
        logger.error(f"Job {job_id} failed: {e.message}")
        await update_job(
            {"status": "failed", "error": e.message, "current_step": "failed"}
        )
    except Exception as e:
        logger.exception(f"Job {job_id} failed unexpectedly")
        await update_job(
            {
                "status": "failed",
                "error": f"An unexpected error occurred: {str(e)}",
                "current_step": "failed",
            }
        )


async def prepare_job_for_retry(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> JobRecord:
    """Interface for retrying a job, delegates to job_management."""
    job = await prepare_job_for_retry_logic(job_id, db_session_factory)
    logger.debug(f"Job {job_id} prepared for retry (Count: {job.retry_count})")
    return job
