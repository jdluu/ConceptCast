from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, ValidationResult
from domain.agents.validator import validate_curriculum
from domain.models.workflow import GlobalContext
from infra.models.job import JobRecord
from services.workflow.base import get_step_model


async def step_validating(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    persist: bool = True,
) -> tuple[ValidationResult, RunUsage | None]:
    """Executes the curriculum validation phase of the generation workflow.

    Uses an AI validator to review the pedagogical plan for technical accuracy,
    clarity, and alignment with the target audience.

    Args:
        plan: The curriculum plan to validate.
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.
        ctx: The Global Context Object (GCO) for shared memory.
        persist: Whether to immediately persist the result to the database.

    Returns:
        tuple: (The ValidationResult, RunUsage object from the AI).
    """
    usage: RunUsage | None = None
    logger.info(f"Validating curriculum plan (Mode: {job.mode})")

    validator_model = get_step_model(request, job, agent_id="validator")
    if not validator_model:
        raise ValueError("Could not initialize validator model")

    validation, usage = await validate_curriculum(
        plan, validator_model, on_thought=on_thought, ctx=ctx
    )

    if persist:
        await update_job({"validation": validation.model_dump()})

    logger.success("Step 2: Validating - Complete")

    return validation, usage
