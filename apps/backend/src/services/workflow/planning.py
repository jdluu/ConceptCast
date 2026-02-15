import json
from collections.abc import Callable
from typing import Any

from loguru import logger

from agents.analyst import generate_curriculum
from agents.factory import get_model
from api.schemas import CurriculumPlan, JobRequest
from core.database import JobRecord
from core.exceptions import PlanGenerationError


async def step_planning(
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> CurriculumPlan:
    """Executes the Planning step of the lesson generation workflow.

    This step generates a curriculum plan based on the user's topic and
    target audience. It handles checkpointing by returning an existing plan
    if one is already associated with the job.

    Args:
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        CurriculumPlan: The generated or retrieved curriculum.

    Raises:
        PlanGenerationError: If the AI provider fails to produce a plan.
    """
    if not job.plan:
        logger.info(f"Generating curriculum for: {request.topic} (Mode: {job.mode})")

        provider_arg = (
            "mock"
            if job.mode == "mock"
            else (getattr(job, "provider", None) or request.provider)
        )
        model_arg = getattr(job, "model_id", None) or request.model_id

        plan_model = get_model(
            provider_name=provider_arg,
            model_id=model_arg,
        )

        if not plan_model:
            raise PlanGenerationError(
                f"Could not initialize model for provider '{provider_arg}' and "
                f"model_id '{model_arg}'. Ensure API keys are configured."
            )

        plan = await generate_curriculum(
            topic=request.topic,
            audience=request.target_audience,
            model=plan_model,
            on_thought=on_thought,
        )

        job.plan = plan.model_dump()
        job.current_step = "planning_complete"
        await update_job(
            {
                "plan": job.plan,
                "current_step": job.current_step,
            }
        )
        logger.success("Step 1: Planning - Complete")
    else:
        logger.info("Using existing curriculum plan (Checkpoint)")
        if isinstance(job.plan, dict):
            plan = CurriculumPlan(**job.plan)
        else:
            plan = CurriculumPlan(**json.loads(job.plan))
    return plan
