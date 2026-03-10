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
    db_session_factory: Callable[[], AsyncSession], job_id: str, updates: dict[str, Any]
) -> None:
    """Updates a job record in the database using an asynchronous session.

    Args:
        db_session_factory: A factory function that returns an AsyncSession.
        job_id: The unique identifier of the job to update.
        updates: A dictionary of field names and their new values.
    """
    async with db_session_factory() as db:
        try:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                for key, value in updates.items():
                    setattr(job, key, value)
                job.updated_at = datetime.now(UTC)
                await db.commit()
                await job_event_manager.notify(job_id)
        except Exception:
            await db.rollback()
            raise


async def update_job_status(
    job_id: str,
    updates: dict[str, Any],
    session_factory: Callable[[], AsyncSession],
) -> None:
    """Alias for update_job_record for backward compatibility and semantic clarity."""
    await update_job_record(session_factory, job_id, updates)


async def prepare_job_for_retry_logic(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> JobRecord:
    """Resets a failed job to a state where it can be retried safely.

    Clears error messages, render artifacts, and transient state while
    preserving foundational artifacts (like the plan) if they were completed.
    Increments the retry counter and resets the status to 'pending_retry'.

    Returns:
        JobRecord: The updated job record in its reset state.

    Raises:
        ValueError: If the job_id does not exist in the database.
    """
    async with db_session_factory() as db:
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
        await db.commit()
        await job_event_manager.notify(job_id)
        await db.refresh(job)
        return job
