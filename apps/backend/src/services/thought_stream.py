from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ThoughtLog
from core.database import JobRecord
from core.settings import get_settings


async def append_job_thought(
    db_session_factory: Callable[[], AsyncSession],
    job_id: str,
    agent: str,
    phase: str,
    content: str,
) -> None:
    """Appends a streamed thought to the job's streamed_thoughts and persists it."""
    max_entries = max(1, get_settings().streamed_thoughts_max_entries)
    entry = ThoughtLog(
        agent=agent,
        phase=phase,
        content=content,
        ts=datetime.now(UTC).isoformat(),
    )
    # Convert to dict for JSON storage in DB
    entry_dict = entry.model_dump()
    async with db_session_factory() as db:
        try:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                current = getattr(job, "streamed_thoughts", None) or []
                new_list = (list(current) + [entry_dict])[-max_entries:]
                job.streamed_thoughts = new_list
                job.updated_at = datetime.now(UTC)
                await db.commit()
        except Exception:
            await db.rollback()
            raise
