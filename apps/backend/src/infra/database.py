"""Database configuration and lifecycle management for the ConceptCast backend.

Configures SQLAlchemy async engine, session factory, and provides utilities for
database initialization and health checks.
"""

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infra.settings import get_settings

logger = structlog.get_logger(__name__)

db_url = get_settings().database_url
if db_url.startswith("sqlite://"):
    DATABASE_URL = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    connect_args = {"check_same_thread": False, "timeout": 30}
    pool_args = {}
elif db_url.startswith("postgresql://"):
    DATABASE_URL = db_url.replace("postgresql://", "postgresql+asyncpg://")
    connect_args = {}
    pool_args = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
else:
    DATABASE_URL = db_url
    connect_args = {}
    pool_args = {}

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, **pool_args)

#: Factory for generating new asynchronous database sessions.
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


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
        if engine.dialect.name == "sqlite":
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
        logger.error("database_health_check_failed", error=str(e))
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
