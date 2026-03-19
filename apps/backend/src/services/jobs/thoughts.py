from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ThoughtLog
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager


async def append_job_thought(
    session_or_factory: AsyncSession | Callable[[], AsyncSession],
    job_id: str,
    agent: str,
    phase: str,
    content: str,
) -> None:
    """Appends a streamed thought to the job's streamed_thoughts and persists it.

    Supports aggregation of sequential thoughts from the same agent/phase within
    a short time window (10s) to reduce noise in the UI and database.
    """
    if isinstance(session_or_factory, AsyncSession):
        await _perform_thought_append(session_or_factory, job_id, agent, phase, content)
    else:
        async with session_or_factory() as db:
            try:
                await _perform_thought_append(db, job_id, agent, phase, content)
                await db.commit()
            except Exception:
                await db.rollback()
                raise


async def _perform_thought_append(
    db: AsyncSession,
    job_id: str,
    agent: str,
    phase: str,
    content: str,
) -> None:
    """Internal helper to apply thought updates within a session."""
    settings = get_settings()
    max_entries = max(1, settings.streamed_thoughts_max_entries)
    aggregation_window = 10.0  # seconds

    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return

    def _merge_thought_content(existing: str, incoming: str) -> str:
        """Merges streaming thought content without duplicating cumulative chunks.

        Different providers may emit pure deltas or resend the full cumulative
        text. We normalize both behaviors into a monotonic thought body.
        """
        if not incoming:
            return existing
        if not existing:
            return incoming
        if incoming == existing:
            return existing
        # Provider resent cumulative content: replace with the latest full text.
        if incoming.startswith(existing):
            return incoming
        # Exact duplicate snippet already captured.
        if incoming in existing:
            return existing
        # Rare reset / alternative chunking: append as best effort.
        return existing + incoming

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
                and phase != "structured_output"
                and time_diff < aggregation_window
            ):
                should_aggregate = True
        except (ValueError, TypeError):
            pass

    if should_aggregate:
        existing_content = str(thoughts[-1].get("content", ""))
        thoughts[-1]["content"] = _merge_thought_content(existing_content, content)
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

    await job_event_manager.notify(job_id)
