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
)
from infra.models.job import JobRecord


def _classify_failure(  # noqa: C901, PLR0912
    job: JobRecord,
) -> tuple[str | None, str | None, str | None]:
    """Derive normalized failure metadata from current job state."""
    if job.status not in {"failed", "awaiting_review"} and not job.error:
        return None, None, None

    current_step = (job.current_step or "").lower()
    error_text = (job.error or "").strip()
    lower_error = error_text.lower()

    stage = None
    if (
        "plan" in current_step
        or "curriculum" in current_step
        or "preflight" in current_step
        or "audit" in current_step
    ):
        stage = "planning"
    elif "storyboard" in current_step or "architect" in current_step:
        stage = "architecting"
    elif "animat" in current_step:
        stage = "animating"
    elif "render" in current_step:
        stage = "rendering"

    failure_type = "runtime_error"
    if "placeholder" in lower_error or "structural" in lower_error:
        failure_type = "schema_error"
    elif "storyboard" in lower_error or "quality" in lower_error:
        failure_type = "quality_gate"
    elif "provider" in lower_error or "api key" in lower_error:
        failure_type = "provider_error"
    elif (
        "render" in lower_error
        or "manim" in lower_error
        or "syntax error" in lower_error
        or "indentationerror" in lower_error
    ):
        failure_type = "render_error"

    if not stage:
        if failure_type == "render_error":
            stage = "rendering"
        elif "storyboard" in lower_error:
            stage = "architecting"
        elif "curriculum" in lower_error or "teaching_steps" in lower_error:
            stage = "planning"

    summary = None
    if error_text:
        summary = error_text.splitlines()[0].strip()
        if len(summary) > 220:
            summary = f"{summary[:217]}..."
    elif job.status == "awaiting_review":
        summary = "Paused for review."

    return stage, failure_type, summary


def map_job_record_to_status(job: JobRecord) -> JobStatus:
    """Converts a JobRecord database model to a JobStatus Pydantic schema.

    Args:
        job: The SQLAlchemy JobRecord instance.

    Returns:
        JobStatus: A validated schema for API responses.
    """
    normalized_status = "planning" if job.status == "validating" else job.status
    provenance = job.validation if isinstance(job.validation, dict) else {}
    status_literal = cast(
        Literal[
            "planning",
            "architecting",
            "animating",
            "rendering",
            "reviewing",
            "awaiting_review",
            "completed",
            "failed",
            "pending_retry",
        ],
        normalized_status,
    )

    failure_stage, failure_type, failure_summary = _classify_failure(job)

    # Calculate processing duration
    is_active = status_literal not in ("completed", "failed", "pending_retry")
    current_session_duration = 0.0
    if is_active and job.started_at:
        started_at = job.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        current_session_duration = (datetime.now(UTC) - started_at).total_seconds()

    duration_seconds = job.total_execution_time + current_session_duration

    metadata_duration = None
    if isinstance(job.video_metadata, dict):
        raw_duration = job.video_metadata.get("duration")
        if isinstance(raw_duration, int | float):
            metadata_duration = float(raw_duration)

    # job.thoughts is a list of ThoughtRecord models (if loaded)
    thought_logs = []
    if "thoughts" in job.__dict__:
        thought_logs = [
            ThoughtLog(
                agent=t.agent,
                phase=t.phase,
                content=t.content,
                ts=t.ts.isoformat(),
            )
            for t in job.thoughts
        ]

    return JobStatus(
        job_id=job.job_id,
        topic=job.topic,
        user_prompt=job.user_prompt,
        current_step=job.current_step,
        error=job.error,
        mode=cast(Literal["live", "mock"], job.mode),
        hitl_enabled=job.hitl_enabled,
        provider=job.provider,
        model_id=job.model_id,
        analyst_model=job.analyst_model,
        architect_model=job.architect_model,
        animator_model=job.animator_model,
        target_audience=job.target_audience,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        cost=job.cost,
        retry_count=job.retry_count or 0,
        thumbnail_url=job.thumbnail_url,
        video_url=job.video_url,
        preview_url=job.preview_url,
        video_metadata=job.video_metadata,
        render_progress=job.render_progress,
        failure_stage=failure_stage,
        failure_type=failure_type,
        failure_summary=failure_summary,
        architect_fallback_used=bool(provenance.get("architect_fallback_used", False)),
        architect_attempts=int(provenance.get("architect_attempts", 0) or 0),
        architect_original_error=provenance.get("architect_original_error"),
        status=status_literal,
        streamed_thoughts=thought_logs,
        plan=CurriculumPlan.model_validate(job.plan) if job.plan else None,
        storyboard=Storyboard.model_validate(job.storyboard)
        if job.storyboard
        else None,
        manim_code=job.manim_code,
        duration_seconds=max(
            0.0,
            metadata_duration if metadata_duration is not None else duration_seconds,
        ),
    )


def map_job_record_to_summary(job: JobRecord) -> JobSummary:
    """Converts a JobRecord database model to a JobSummary Pydantic schema.

    Args:
        job: The SQLAlchemy JobRecord instance.

    Returns:
        JobSummary: A lightweight schema for list views.
    """
    failure_stage, failure_type, failure_summary = _classify_failure(job)
    provenance = job.validation if isinstance(job.validation, dict) else {}

    metadata_duration = None
    if isinstance(job.video_metadata, dict):
        raw_duration = job.video_metadata.get("duration")
        if isinstance(raw_duration, int | float):
            metadata_duration = float(raw_duration)

    duration_seconds = None
    if metadata_duration is not None:
        duration_seconds = metadata_duration
    elif job.started_at and job.finished_at:
        duration_seconds = (job.finished_at - job.started_at).total_seconds()

    return JobSummary(
        job_id=job.job_id,
        topic=job.topic or "Unknown",
        user_prompt=job.user_prompt,
        current_step=job.current_step,
        error=job.error,
        mode=job.mode,
        created_at=job.created_at.isoformat(),
        hitl_enabled=job.hitl_enabled,
        provider=job.provider,
        model_id=job.model_id,
        analyst_model=job.analyst_model,
        architect_model=job.architect_model,
        animator_model=job.animator_model,
        target_audience=job.target_audience,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        cost=job.cost,
        retry_count=job.retry_count or 0,
        thumbnail_url=job.thumbnail_url,
        video_url=job.video_url,
        video_metadata=job.video_metadata,
        render_progress=job.render_progress,
        failure_stage=failure_stage,
        failure_type=failure_type,
        failure_summary=failure_summary,
        architect_fallback_used=bool(provenance.get("architect_fallback_used", False)),
        architect_attempts=int(provenance.get("architect_attempts", 0) or 0),
        architect_original_error=provenance.get("architect_original_error"),
        status=job.status,
        duration_seconds=duration_seconds,
    )
