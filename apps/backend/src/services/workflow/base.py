from typing import Any

from api.schemas import JobRequest
from infra.ai.factory import get_model
from infra.models.job import JobRecord


def resolve_model_args(request: JobRequest, job: JobRecord) -> tuple[str, str | None]:
    """Resolves the provider and model ID from job record or request.

    Args:
        request: The initial job request.
        job: The current job record.

    Returns:
        tuple: (provider_name, model_id)
    """
    provider = str(
        "mock"
        if job.mode == "mock"
        else (getattr(job, "provider", None) or request.provider)
    )
    model_id = str(getattr(job, "model_id", None) or request.model_id)
    return provider, model_id


def get_step_model(request: JobRequest, job: JobRecord) -> Any:
    """Convenience helper to get a model instance for a workflow step."""
    provider_name, model_id = resolve_model_args(request, job)
    return get_model(provider_name=provider_name, model_id=model_id)
