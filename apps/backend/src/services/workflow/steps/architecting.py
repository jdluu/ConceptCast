import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.agents.architect import generate_storyboard
from domain.models.workflow import GlobalContext
from infra.exceptions import StoryboardGenerationError
from infra.models.job import JobRecord
from services.workflow.base import get_step_model
from services.workflow.utils import parse_job_artifact


async def step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    persist: bool = True,
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
        ctx: The Global Context Object (GCO) for shared memory.
        persist: Whether to immediately persist the result to the database.

    Returns:
        tuple: (The generated Storyboard, RunUsage object from the AI).

    Raises:
        StoryboardGenerationError: If the architect fails to produce a storyboard.
    """
    usage: RunUsage | None = None
    if not job.storyboard:
        logger.info(f"Generating storyboard (Mode: {job.mode})")

        architect_model = get_step_model(request, job, agent_id="architect")

        if not architect_model:
            raise StoryboardGenerationError(
                "Could not initialize model. Ensure API keys are configured."
            )

        storyboard, usage = await generate_storyboard(
            plan, architect_model, on_thought=on_thought, ctx=ctx
        )

        if job.mode == "mock" and persist:
            # Simulate incremental "filling in" of the storyboard
            logger.info("Simulating incremental storyboard population...")
            for i in range(1, len(storyboard.scenes) + 1):
                partial_storyboard = storyboard.model_copy(
                    update={"scenes": storyboard.scenes[:i]}
                )
                await update_job({"storyboard": partial_storyboard.model_dump()})
                await asyncio.sleep(0.3)  # Brief pause between scenes

        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        if persist:
            await update_job(
                {
                    "storyboard": job.storyboard,
                    "current_step": job.current_step,
                }
            )
        logger.success("Step 3: Architecting - Complete")
    else:
        logger.info("Using existing storyboard (Checkpoint)")
        storyboard = parse_job_artifact(job.storyboard, Storyboard)
    return storyboard, usage
