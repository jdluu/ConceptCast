import asyncio
from collections import defaultdict

from loguru import logger


class JobEventManager:
    """
    Manages job-specific events to support event-driven SSE streams.
    Uses asyncio.Condition to allow multiple subscribers to wait for updates.
    """

    def __init__(self) -> None:
        self._conditions: dict[str, asyncio.Condition] = defaultdict(asyncio.Condition)
        self._last_update_ts: dict[str, float] = {}

    async def notify(self, job_id: str) -> None:
        """Notifies all subscribers that a job has been updated."""
        condition = self._conditions[job_id]
        async with condition:
            condition.notify_all()
            logger.trace(f"Notified subscribers for job {job_id}")

    async def wait_for_update(self, job_id: str, timeout: float = 30.0) -> bool:
        """
        Waits for a notification for the given job_id.
        Returns True if notified, False if timeout.
        """
        condition = self._conditions[job_id]
        async with condition:
            try:
                return await asyncio.wait_for(condition.wait(), timeout=timeout)
            except TimeoutError:
                return False


# Global instance
job_event_manager = JobEventManager()
