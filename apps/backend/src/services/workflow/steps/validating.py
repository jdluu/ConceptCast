from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, ValidationResult
from domain.agents.validator import validate_curriculum
from infra.models.job import JobRecord
from services.workflow.base import get_step_model


async def step_validating(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> tuple[ValidationResult, RunUsage | None]:
    """Executes the Validation step of the lesson generation workflow."""
    usage: RunUsage | None = None
    logger.info(f"Validating curriculum plan (Mode: {job.mode})")

    validator_model = get_step_model(request, job)

    validation, usage = await validate_curriculum(
        plan, validator_model, on_thought=on_thought
    )

    return validation, usage
