import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest
from domain.agents.analyst import generate_curriculum
from infra.exceptions import PlanGenerationError
from infra.models.job import JobRecord
from services.workflow.base import get_step_model


async def step_planning(
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> tuple[CurriculumPlan, RunUsage | None]:
    """Executes the curriculum planning phase of the generation workflow.

    Uses an AI analyst to decompose the input topic into a structured,
    pedagogical plan appropriate for the target audience.

    Args:
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.

    Returns:
        tuple: (The generated CurriculumPlan, RunUsage object from the AI).

    Raises:
        PlanGenerationError: If the analyst fails to produce a valid plan.
    """
    usage: RunUsage | None = None
    if not job.plan:
        logger.info(f"Generating curriculum for: {request.topic} (Mode: {job.mode})")

        plan_model = get_step_model(request, job)

        if not plan_model:
            raise PlanGenerationError(
                "Could not initialize model. Ensure API keys are configured."
            )

        plan, usage = await generate_curriculum(
            topic=request.topic,
            audience=request.target_audience,
            model=plan_model,
            on_thought=on_thought,
        )

        if job.mode == "mock":
            # Simulate incremental "filling in" of the plan for realism
            logger.info("Simulating incremental plan population...")
            for i in range(1, len(plan.teaching_steps) + 1):
                partial_plan = plan.model_copy(update={"teaching_steps": plan.teaching_steps[:i]})
                await update_job({"plan": partial_plan.model_dump()})
                await asyncio.sleep(0.4) # Brief pause between steps

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
    return plan, usage
