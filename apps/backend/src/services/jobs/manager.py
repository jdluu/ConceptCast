from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import JobRequest
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager


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
    updates: dict[str, Any],
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
        await _perform_job_update(session_or_factory, job_id, updates)
    else:
        async with session_or_factory() as db:
            try:
                await _perform_job_update(db, job_id, updates)
                await db.commit()
            except Exception:
                await db.rollback()
                raise


async def _perform_job_update(
    db: AsyncSession, job_id: str, updates: dict[str, Any]
) -> None:
    """Internal helper to apply updates to a job record within a session."""
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()
    if job:
        for key, value in updates.items():
            setattr(job, key, value)
        job.updated_at = datetime.now(UTC)
        await job_event_manager.notify(job_id)


async def update_job_status(
    job_id: str,
    updates: dict[str, Any],
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

    updates: dict[str, Any] = {
        "status": "pending_retry",
        "error": None,
        "current_step": "retrying",
        "retry_count": job.retry_count + 1,
        "streamed_thoughts": [],
        "render_progress": 0,
        "started_at": None,
        "finished_at": None,
    }

    for key, value in updates.items():
        setattr(job, key, value)

    job.updated_at = datetime.now(UTC)
    await job_event_manager.notify(job_id)
    return job
