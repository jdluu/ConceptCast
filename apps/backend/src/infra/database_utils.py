import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import structlog
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

T = TypeVar("T")


async def run_with_sqlite_retry(
    db: AsyncSession,
    func: Callable[[], Awaitable[T]],
    max_retries: int = 5,
    base_delay: float = 0.1,
) -> T:
    """Retries an async function that performs SQLite operations.

    Handles 'database is locked' (OperationalError) and transient 
    IntegrityErrors during concurrent operations.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func()
        except (OperationalError, IntegrityError) as e:
            last_error = e
            # Mandatory rollback to clear failed transaction state before retry
            await db.rollback()

            is_lock = isinstance(e, OperationalError) and "locked" in str(e).lower()
            is_integrity = isinstance(e, IntegrityError)

            if not (is_lock or is_integrity):
                raise

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) + random.uniform(0, 0.1)
                logger.warning(
                    "sqlite_retry_waiting",
                    attempt=attempt + 1,
                    error=str(e),
                    delay=delay,
                )
                await asyncio.sleep(delay)
            else:
                break

    if last_error:
        raise last_error
    raise RuntimeError("sqlite_retry failed without error")
