from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.models.job import JobRecord
from infra.models.thought import ThoughtRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager


async def append_job_thought(
    session_or_factory: AsyncSession | Callable[[], AsyncSession],
    job_id: str,
    agent: str,
    phase: str,
    content: str,
) -> None:
    """Appends a streamed thought to the job's thoughts table and persists it.

    Supports aggregation of sequential thoughts from the same agent/phase within
    a short time window (10s) to reduce database volume.
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
    """Internal helper to apply thought updates within a session using the ThoughtRecord table."""
    settings = get_settings()
    max_entries = max(1, settings.streamed_thoughts_max_entries)
    aggregation_window = 10.0  # seconds

    # Check if job exists and update its timestamp
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return

    now = datetime.now(UTC)
    job.updated_at = now

    def _merge_thought_content(existing: str, incoming: str) -> str:
        """Merges streaming thought content without duplicating cumulative chunks."""
        if not incoming:
            return existing
        if not existing:
            return incoming
        if incoming == existing:
            return existing
        if incoming.startswith(existing):
            return incoming
        if incoming in existing:
            return existing
        return existing + incoming

    # Get the latest thought for this job
    latest_thought_result = await db.execute(
        select(ThoughtRecord)
        .where(ThoughtRecord.job_id == job_id)
        .order_by(ThoughtRecord.ts.desc())
        .limit(1)
    )
    latest_thought = latest_thought_result.scalar_one_or_none()

    should_aggregate = False
    if (
        latest_thought
        and latest_thought.agent == agent
        and latest_thought.phase == phase
        and phase != "structured_output"
    ):
        time_diff = (now - latest_thought.ts.replace(tzinfo=UTC)).total_seconds()
        if time_diff < aggregation_window:
            should_aggregate = True

    if should_aggregate and latest_thought:
        latest_thought.content = _merge_thought_content(latest_thought.content, content)
        latest_thought.ts = now
    else:
        new_thought = ThoughtRecord(
            job_id=job_id,
            agent=agent,
            phase=phase,
            content=content,
            ts=now,
        )
        db.add(new_thought)

        # Basic cleanup if we are inserting a new record to avoid unbounded growth
        # We only do this check occasionally or just rely on a simple count.
        # Doing a subquery delete in SQLite is tricky with LIMIT, so we fetch IDs to delete.
        # To avoid overhead on every insert, we could skip it, but let's implement a safe bound.
        count_result = await db.execute(
            select(ThoughtRecord.id)
            .where(ThoughtRecord.job_id == job_id)
            .order_by(ThoughtRecord.ts.desc())
            .offset(max_entries)
            .limit(50)  # Fetch up to 50 old IDs to delete
        )
        ids_to_delete = count_result.scalars().all()
        if ids_to_delete:
            await db.execute(
                delete(ThoughtRecord).where(ThoughtRecord.id.in_(ids_to_delete))
            )

    await job_event_manager.notify(job_id)
