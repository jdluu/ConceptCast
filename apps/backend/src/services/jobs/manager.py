from collections.abc import Callable
from datetime import UTC, datetime

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from api.schemas import JobRequest
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager

logger = structlog.get_logger(__name__)


async def get_job_summaries(
    db: AsyncSession, mode: str | None = None
) -> list[JobRecord]:
    """Fetches a list of job records optimized for summary views.

    Explicitly defers loading of heavy JSON columns (plan, storyboard, code)
    to reduce database bandwidth and memory usage during list operations.

    Args:
        db: The active database session.
        mode: Optional filter for 'live' or 'mock' jobs.

    Returns:
        list[JobRecord]: A list of job records with only summary fields loaded.
    """
    stmt = select(JobRecord).order_by(JobRecord.created_at.desc())

    # Defer loading of heavy columns
    stmt = stmt.options(
        defer(JobRecord.plan),
        defer(JobRecord.storyboard),
        defer(JobRecord.manim_code),
        defer(JobRecord.validation),
    )

    if mode:
        stmt = stmt.where(JobRecord.mode == mode)

    result = await db.execute(stmt)
    return list(result.scalars().all())


def determine_execution_mode(request: JobRequest) -> bool:
    """Determines whether to run in mock mode based on configuration and request.

    Args:
        request: The initial job request containing provider preferences.

    Returns:
        bool: True if mock mode should be used, False for live execution.
    """
    settings = get_settings()
    return (
        request.provider == "mock"
        or not settings.has_any_api_key()
        or settings.is_dummy_key()
    )


async def update_job_record(
    session_or_factory: AsyncSession | Callable[[], AsyncSession],
    job_id: str,
    updates: dict[str, object],
) -> None:
    """Updates a job record in the database.

    Supports either a direct AsyncSession or a factory function. If a session
    is provided, it is assumed the caller manages the transaction and commit.

    Args:
        session_or_factory: An active AsyncSession or a factory function.
        job_id: The unique identifier of the job to update.
        updates: A dictionary of field names and their new values.
    """
    if isinstance(session_or_factory, AsyncSession):
        await perform_job_update(session_or_factory, job_id, updates)
    else:
        async with session_or_factory() as db:
            try:
                await perform_job_update(db, job_id, updates)
                await db.commit()
            except Exception:
                await db.rollback()
                raise


async def perform_job_update(
    db: AsyncSession, job_id: str, updates: dict[str, object]
) -> None:
    """Internal helper to apply updates to a job record atomically."""
    # Check for active cancellation first
    result = await db.execute(
        select(JobRecord.status, JobRecord.error).where(JobRecord.job_id == job_id)
    )
    row = result.first()
    if row:
        status, error = row
        if (
            status == "failed"
            and error
            and ("cancelled" in str(error).lower() or "cancel" in str(error).lower())
        ):
            from infra.exceptions import JobCancelledError

            raise JobCancelledError("Job was cancelled by the user.")

    # Add updated_at to the updates if not already present
    now = datetime.now(UTC)
    full_updates = {**updates, "updated_at": now}

    stmt = update(JobRecord).where(JobRecord.job_id == job_id).values(**full_updates)
    await db.execute(stmt)
    await job_event_manager.notify(job_id)


async def update_job_status(
    job_id: str,
    updates: dict[str, object],
    session_or_factory: AsyncSession | Callable[[], AsyncSession],
) -> None:
    """Alias for update_job_record for backward compatibility and semantic clarity."""
    await update_job_record(session_or_factory, job_id, updates)


async def prepare_job_for_retry_logic(
    job_id: str, session_or_factory: AsyncSession | Callable[[], AsyncSession]
) -> JobRecord:
    """Resets a failed job to a state where it can be retried safely.

    Returns:
        JobRecord: The updated job record in its reset state.
    """
    if isinstance(session_or_factory, AsyncSession):
        return await _perform_retry_prep(session_or_factory, job_id)

    async with session_or_factory() as db:
        try:
            job = await _perform_retry_prep(db, job_id)
            await db.commit()
            await db.refresh(job)
            return job
        except Exception:
            await db.rollback()
            raise


async def _perform_retry_prep(db: AsyncSession, job_id: str) -> JobRecord:
    """Internal helper to prepare a job for retry within a session."""
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise ValueError(f"Job {job_id} not found")

    is_render_repair = (
        job.status == "awaiting_review"
        and job.current_step == "rendering_failed_needs_fix"
    )
    current_step = (job.current_step or "").lower()
    error_text = (job.error or "").lower()

    failure_stage = "unknown"
    if is_render_repair:
        failure_stage = "rendering_repair"
    elif (
        "animat" in current_step
        or "preview" in current_step
        or "manim" in current_step
        or "animation" in error_text
        or "preview" in error_text
        or "syntax error" in error_text
        or "indentationerror" in error_text
    ):
        failure_stage = "animating"
    elif "render" in current_step or "render" in error_text:
        failure_stage = "rendering"
    elif "architect" in current_step or "storyboard" in current_step:
        failure_stage = "architecting"
    elif "plan" in current_step or "curriculum" in current_step:
        failure_stage = "planning"

    keep_storyboard = bool(job.storyboard) and (
        is_render_repair or failure_stage == "animating"
    )

    from infra.models.thought import ThoughtRecord

    # Delete old thoughts to cleanly start over
    await db.execute(delete(ThoughtRecord).where(ThoughtRecord.job_id == job_id))

    updates: dict[str, object] = {
        "status": "pending_retry",
        # Keep the error message as retry hint for all retry stages.
        "error": job.error,
        "current_step": "rendering_failed_needs_fix"
        if is_render_repair
        else "retrying",
        "retry_count": job.retry_count + 1,
        "render_progress": 0,
        "started_at": None,
        "finished_at": None,
        # Keep the plan checkpoint always; keep storyboard when retrying
        # from animating/render-repair checkpoints.
        "storyboard": job.storyboard if keep_storyboard else None,
        "manim_code": None,
        "video_url": None,
        "thumbnail_url": None,
        "video_metadata": None,
    }

    for key, value in updates.items():
        setattr(job, key, value)

    logger.info(
        "retry_prep",
        job_id=job_id,
        stage=failure_stage,
        kept_plan=bool(job.plan),
        kept_storyboard=keep_storyboard,
        cleared_artifacts=[
            "manim_code",
            "video_url",
            "thumbnail_url",
            "video_metadata",
        ],
        current_step=str(updates["current_step"]),
    )

    job.updated_at = datetime.now(UTC)
    await job_event_manager.notify(job_id)
    return job
