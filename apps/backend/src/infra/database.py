"""Database configuration and lifecycle management for the ConceptCast backend.

Configures SQLAlchemy async engine, session factory, and provides utilities for
database initialization and health checks.
"""

from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from infra.settings import get_settings

DATABASE_URL = get_settings().database_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""

    pass


async def init_db() -> None:
    """Initializes the database tables and ensures WAL mode is enabled.

    This function creates all tables defined in the metadata (as a fallback)
    and sets the SQLite journal mode to WAL for improved concurrency support.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL;"))


async def check_db_health() -> bool:
    """Verifies that the database connection is alive.

    Returns:
        True if the database responds to a simple query, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session for dependency injection.

    Yields:
        An active SQLAlchemy AsyncSession instance.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
