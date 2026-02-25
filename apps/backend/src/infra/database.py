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
    pass


async def init_db() -> None:
    """Initializes the database tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable WAL (Write-Ahead Logging) for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL;"))

    if "sqlite" in DATABASE_URL:
        await _migrate_sqlite_schema()


async def _migrate_sqlite_schema() -> None:
    """Detects and adds missing columns to the SQLite jobs table."""
    column_definitions = {
        "resolution": "VARCHAR DEFAULT '720p'",
        "frame_rate": "INTEGER DEFAULT 30",
        "render_progress": "INTEGER DEFAULT 0",
    }

    try:
        async with engine.connect() as conn:
            from sqlalchemy import text

            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            existing_columns = {row[1] for row in result.fetchall()}

            for col_name, col_type in column_definitions.items():
                if col_name not in existing_columns:
                    logger.info(
                        f"DB Migration: Adding column '{col_name}' to 'jobs' table"
                    )
                    try:
                        await conn.execute(
                            text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                        )
                        await conn.commit()
                    except Exception as col_err:
                        logger.error(f"Failed to add column '{col_name}': {col_err}")
    except Exception as e:
        logger.error(f"Critical failure during SQLite schema migration: {e}")


async def check_db_health() -> bool:
    """Verifies that the database is reachable and responding."""
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        from loguru import logger

        logger.error(f"Database health check failed: {e}")
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing asynchronous database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
