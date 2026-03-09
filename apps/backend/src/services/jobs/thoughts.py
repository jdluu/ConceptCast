from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ThoughtLog
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager


async def append_job_thought(
    db_session_factory: Callable[[], AsyncSession],
    job_id: str,
    agent: str,
    phase: str,
    content: str,
) -> None:
    """Appends a streamed thought to the job's streamed_thoughts and persists it.

    Supports aggregation of sequential thoughts from the same agent/phase within
    a short time window (10s) to reduce noise in the UI and database.

    Args:
        db_session_factory: Factory function for providing DB sessions.
        job_id: The unique identifier for the generation job.
        agent: Name of the agent (e.g., 'analyst', 'animator').
        phase: Current generation phase or sub-task.
        content: Reasoning content to append or add.
    """
    settings = get_settings()
    max_entries = max(1, settings.streamed_thoughts_max_entries)
    aggregation_window = 10.0  # seconds

    async with db_session_factory() as db:
        try:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                return

            thoughts = list(getattr(job, "streamed_thoughts", None) or [])
            now = datetime.now(UTC)

            should_aggregate = False
            if thoughts:
                last = thoughts[-1]
                try:
                    last_ts = datetime.fromisoformat(last.get("ts", ""))
                    time_diff = (now - last_ts).total_seconds()

                    if (
                        last.get("agent") == agent
                        and last.get("phase") == phase
                        and time_diff < aggregation_window
                    ):
                        should_aggregate = True
                except (ValueError, TypeError):
                    pass

            if should_aggregate:
                thoughts[-1]["content"] += content
                thoughts[-1]["ts"] = now.isoformat()
            else:
                entry = ThoughtLog(
                    agent=agent,
                    phase=phase,
                    content=content,
                    ts=now.isoformat(),
                )
                thoughts.append(entry.model_dump())

            # Enforce max entries limit
            job.streamed_thoughts = thoughts[-max_entries:]
            job.updated_at = now
            await db.commit()
            await job_event_manager.notify(job_id)
        except Exception:
            await db.rollback()
            raise
