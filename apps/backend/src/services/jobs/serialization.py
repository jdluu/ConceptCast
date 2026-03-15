"""Serialization and mapping logic for job models and schemas.

Handles the conversion of database records to API-ready schemas,
decoupling the domain/storage layer from the transport layer.
"""

from datetime import UTC, datetime
from typing import Literal, cast

from api.schemas import (
    CurriculumPlan,
    JobStatus,
    JobSummary,
    Storyboard,
    ThoughtLog,
    ValidationResult,
)
from infra.models.job import JobRecord


def map_job_record_to_status(job: JobRecord) -> JobStatus:
    """Converts a JobRecord database model to a JobStatus Pydantic schema.

    Args:
        job: The SQLAlchemy JobRecord instance.

    Returns:
        JobStatus: A validated schema for API responses.
    """
    status_literal = cast(
        Literal[
            "planning",
            "validating",
            "architecting",
            "animating",
            "rendering",
            "reviewing",
            "awaiting_review",
            "completed",
            "failed",
            "pending_retry",
        ],
        job.status,
    )
    mode_literal = cast(Literal["live", "mock"], job.mode)

    thoughts = [ThoughtLog(**t) for t in (job.streamed_thoughts or [])]

    # Calculate processing duration
    is_active = status_literal not in ("completed", "failed", "pending_retry")
    current_session_duration = 0.0
    if is_active and job.started_at:
        started_at = job.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        current_session_duration = (datetime.now(UTC) - started_at).total_seconds()

    duration_seconds = job.total_execution_time + current_session_duration

    return JobStatus(
        job_id=job.job_id,
        topic=job.topic,
        status=status_literal,
        plan=CurriculumPlan(**job.plan) if job.plan else None,
        validation=ValidationResult(**job.validation) if job.validation else None,
        storyboard=Storyboard(**job.storyboard) if job.storyboard else None,
        manim_code=job.manim_code,
        video_url=job.video_url,
        error=job.error,
        mode=mode_literal,
        hitl_enabled=job.hitl_enabled,
        streamed_thoughts=thoughts,
        provider=job.provider,
        model_id=job.model_id,
        analyst_model=job.analyst_model,
        validator_model=job.validator_model,
        architect_model=job.architect_model,
        animator_model=job.animator_model,
        target_audience=job.target_audience,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        duration_seconds=max(0.0, duration_seconds),
        cost=job.cost,
        retry_count=job.retry_count,
        thumbnail_url=job.thumbnail_url,
        video_metadata=job.video_metadata,
        render_progress=job.render_progress,
    )


def map_job_record_to_summary(job: JobRecord) -> JobSummary:
    """Converts a JobRecord database model to a JobSummary Pydantic schema.

    Args:
        job: The SQLAlchemy JobRecord instance.

    Returns:
        JobSummary: A lightweight schema for list views.
    """
    retry_count_val = job.retry_count if job.retry_count is not None else 0

    return JobSummary(
        job_id=job.job_id,
        topic=job.topic,
        status=job.status,
        mode=job.mode,
        hitl_enabled=job.hitl_enabled,
        created_at=job.created_at.isoformat(),
        retry_count=retry_count_val,
        error=job.error,
        provider=job.provider,
        model_id=job.model_id,
        analyst_model=job.analyst_model,
        validator_model=job.validator_model,
        architect_model=job.architect_model,
        animator_model=job.animator_model,
        target_audience=job.target_audience,
        started_at=(job.started_at.isoformat() if job.started_at else None),
        finished_at=(job.finished_at.isoformat() if job.finished_at else None),
        duration_seconds=(
            (job.finished_at - job.started_at).total_seconds()
            if job.started_at and job.finished_at
            else None
        ),
        cost=job.cost,
        thumbnail_url=job.thumbnail_url,
        video_url=job.video_url,
        video_metadata=job.video_metadata,
        render_progress=job.render_progress,
    )
