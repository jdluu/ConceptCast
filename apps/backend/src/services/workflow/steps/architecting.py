import json
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.agents.architect import generate_storyboard
from infra.exceptions import StoryboardGenerationError
from infra.models.job import JobRecord
from services.workflow.base import get_step_model


async def step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> tuple[Storyboard, RunUsage | None]:
    """Executes the visual architecting phase of the generation workflow.

    Uses an AI architect to transform a pedagogical plan into a detailed
    storyboard, defining the visual elements and timing for each scene.

    Args:
        plan: The curriculum plan generated in the previous step.
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.

    Returns:
        tuple: (The generated Storyboard, RunUsage object from the AI).

    Raises:
        StoryboardGenerationError: If the architect fails to produce a storyboard.
    """
    usage: RunUsage | None = None
    if not job.storyboard:
        logger.info(f"Generating storyboard (Mode: {job.mode})")

        architect_model = get_step_model(request, job)

        if not architect_model:
            raise StoryboardGenerationError(
                "Could not initialize model. Ensure API keys are configured."
            )

        storyboard, usage = await generate_storyboard(
            plan, architect_model, on_thought=on_thought
        )

        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        await update_job(
            {
                "storyboard": job.storyboard,
                "current_step": job.current_step,
            }
        )
        logger.success("Step 3: Architecting - Complete")
    else:
        logger.info("Using existing storyboard (Checkpoint)")
        if isinstance(job.storyboard, dict):
            storyboard = Storyboard(**job.storyboard)
        else:
            storyboard = Storyboard(**json.loads(job.storyboard))
    return storyboard, usage
