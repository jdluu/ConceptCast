"""Cross-process job event notification system using Redis pub/sub.

Replaces the in-process asyncio.Condition approach with Redis pub/sub to
enable notifications from both the FastAPI API process and the separate
Taskiq worker process. Falls back to asyncio.Event polling if Redis is
unavailable.
"""

import asyncio
from collections import defaultdict
from typing import Any, cast

import structlog
from redis.asyncio import ConnectionError as RedisConnectionError
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from infra.settings import get_settings

logger = structlog.get_logger(__name__)

_CHANNEL_PREFIX = "conceptcast:job:"


class JobEventManager:
    """Manages cross-process job update notifications via Redis pub/sub.

    Uses Redis pub/sub as the primary notification mechanism, enabling the
    Taskiq worker process to notify the API process of state changes. Falls
    back to in-process asyncio.Event signaling if Redis is unreachable.
    """

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._fallback_events: dict[str, asyncio.Event] = defaultdict(asyncio.Event)

    def _get_redis(self) -> Redis:
        """Lazily initializes and returns the Redis client singleton.

        Returns:
            Redis: An async Redis client connected to the configured URL.
        """
        if self._redis is None:
            settings = get_settings()
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
        return self._redis

    async def notify(self, job_id: str) -> None:
        """Publishes a job update notification to Redis and the local fallback.

        Args:
            job_id: The unique identifier of the updated job.
        """
        # Always signal the local fallback for in-process subscribers.
        event = self._fallback_events.get(job_id)
        if event:
            event.set()

        try:
            redis = self._get_redis()
            await redis.publish(f"{_CHANNEL_PREFIX}{job_id}", "updated")
        except (RedisConnectionError, OSError, ConnectionRefusedError):
            logger.debug("redis_publish_fallback", job_id=job_id)

    async def wait_for_update(self, job_id: str, timeout: float = 30.0) -> bool:
        """Waits for a job update notification from Redis pub/sub.

        Subscribes to the Redis channel for this job and blocks until a
        message arrives or the timeout expires. Falls back to a local
        asyncio.Event if Redis is unavailable.

        Args:
            job_id: The unique identifier of the job to monitor.
            timeout: Maximum seconds to wait before returning.

        Returns:
            True if a notification was received, False on timeout.
        """
        try:
            return await self._wait_redis(job_id, timeout)
        except (RedisConnectionError, OSError, ConnectionRefusedError):
            logger.debug("redis_subscribe_fallback", job_id=job_id)
            return await self._wait_fallback(job_id, timeout)

    async def _wait_redis(self, job_id: str, timeout: float) -> bool:
        """Subscribes to the Redis channel and waits for a single message.

        Args:
            job_id: The unique identifier of the job to monitor.
            timeout: Maximum seconds to wait.

        Returns:
            True if notified, False on timeout.
        """
        redis = self._get_redis()
        channel = f"{_CHANNEL_PREFIX}{job_id}"
        pubsub = redis.pubsub()

        try:
            await pubsub.subscribe(channel)
            message = await asyncio.wait_for(
                self._read_next_message(pubsub), timeout=timeout
            )
            return message is not None
        except TimeoutError:
            return False
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    @staticmethod
    async def _read_next_message(pubsub: PubSub) -> dict[str, Any] | None:
        """Reads messages from a pub/sub subscription, skipping control messages.

        Args:
            pubsub: An active Redis pub/sub subscription.

        Returns:
            The first data message received, or None.
        """
        async for message in pubsub.listen():
            if message["type"] == "message":
                return cast(dict[str, Any], message)
        return None

    async def _wait_fallback(self, job_id: str, timeout: float) -> bool:
        """Falls back to an in-process asyncio.Event when Redis is unavailable.

        Args:
            job_id: The unique identifier of the job to monitor.
            timeout: Maximum seconds to wait.

        Returns:
            True if the event was set, False on timeout.
        """
        event = self._fallback_events[job_id]
        event.clear()
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return True
        except TimeoutError:
            return False


# Global instance shared across the application.
job_event_manager = JobEventManager()
