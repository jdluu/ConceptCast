from typing import Any

from api.schemas import JobRequest
from infra.ai.factory import get_model
from infra.models.job import JobRecord


def resolve_model_args(
    request: JobRequest, job: JobRecord, model_override: str | None = None
) -> tuple[str, str | None]:
    """Resolves the provider and model ID from job record or request.

    Args:
        request: The initial job request.
        job: The current job record.
        model_override: An optional model ID to override the default.

    Returns:
        tuple: (provider_name, model_id)
    """
    provider = str(
        "mock"
        if job.mode == "mock"
        else (getattr(job, "provider", None) or request.provider)
    )
    model_id = str(model_override or getattr(job, "model_id", None) or request.model_id)
    return provider, model_id


def get_step_model(
    request: JobRequest, job: JobRecord, agent_id: str | None = None
) -> Any:
    """Retrieves an authorized PydanticAI model instance for a workflow step.

    Uses `resolve_model_args` to determine the correct provider and model
    based on the job's execution mode and user preferences.

    Args:
        request: The initial job request.
        job: The current job record from the database.
        agent_id: The identifier of the agent (e.g., 'analyst').

    Returns:
        A configured PydanticAI model instance.
    """
    model_override = None
    if agent_id:
        model_override = getattr(job, f"{agent_id}_model", None) or getattr(
            request, f"{agent_id}_model", None
        )

    provider_name, model_id = resolve_model_args(request, job, model_override)
    return get_model(provider_name=provider_name, model_id=model_id)
