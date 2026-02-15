import json
from collections.abc import Callable
from typing import Any

from loguru import logger

from agents.architect import generate_storyboard
from agents.factory import get_model
from api.schemas import CurriculumPlan, JobRequest, Storyboard
from core.database import JobRecord
from core.exceptions import StoryboardGenerationError


async def step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> Storyboard:
    """Executes the Architecting step of the lesson generation workflow.

    Translates the pedagogical curriculum plan into a visual storyboard
    consisting of scenes, descriptions, and visual metaphors.

    Args:
        plan: The curriculum plan generated in the previous step.
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        Storyboard: The generated or retrieved visual storyboard.

    Raises:
        StoryboardGenerationError: If the AI provider fails to produce a storyboard.
    """
    if not job.storyboard:
        logger.info("Generating storyboard...")
        provider_arg = (
            "mock"
            if job.mode == "mock"
            else (getattr(job, "provider", None) or request.provider)
        )
        model_arg = getattr(job, "model_id", None) or request.model_id
        arch_model = get_model(
            provider_name=provider_arg,
            model_id=model_arg,
        )

        if not arch_model:
            raise StoryboardGenerationError(
                f"Could not initialize model for provider '{provider_arg}' and "
                f"model_id '{model_arg}'. Ensure API keys are configured."
            )

        storyboard = await generate_storyboard(
            plan=plan,
            model=arch_model,
            on_thought=on_thought,
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
