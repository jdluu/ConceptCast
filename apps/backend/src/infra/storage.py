from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, cast

from loguru import logger
from sqlalchemy import JSON, DateTime, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from infra.settings import get_settings

if TYPE_CHECKING:
    from api.schemas import JobStatus

DATABASE_URL = get_settings().database_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Initializes the database tables asynchronously.

    Creates all tables defined in the SQLAlchemy models if they do not already exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable WAL (Write-Ahead Logging) for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL;"))

    # Simple migration logic for SQLite to handle missing columns
    # that create_all doesn't add to existing tables.
    if "sqlite" in DATABASE_URL:
        await _migrate_sqlite_schema()


async def _migrate_sqlite_schema() -> None:
    """Detects and adds missing columns to the SQLite jobs table.
    
    SQLite does not support 'IF NOT EXISTS' for ADD COLUMN in older versions,
    and SQLAlchemy's create_all() does not perform migrations for existing tables.
    This shim ensures that as the JobRecord model evolves, existing local
    databases remain compatible without requiring a full Alembic setup.
    """
    column_definitions = {
        "resolution": "VARCHAR DEFAULT '720p'",
        "frame_rate": "INTEGER DEFAULT 30",
        "render_progress": "INTEGER DEFAULT 0",
    }

    try:
        async with engine.connect() as conn:
            from sqlalchemy import text

            # Check existing schema
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
                        # Continue to other columns even if one fails
    except Exception as e:
        logger.error(f"Critical failure during SQLite schema migration: {e}")


async def check_db_health() -> bool:
    """Verifies that the database is reachable and responding.

    Returns:
        bool: True if connected, False otherwise.
    """
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
    """Dependency for providing asynchronous database sessions.

    Yields:
        AsyncSession: A context-managed SQLAlchemy asynchronous session.
    """
    async with AsyncSessionLocal() as session:
        yield session


class JobRecord(Base):
    """
    SQLAlchemy model for storing job state and artifacts.

    Attributes:
        job_id (str): Unique identifier for the job (UUID).
        topic (str): The main concept topic requested.
        target_audience (str): The target audience for the explanation.
        status (str): Current status of the job (e.g., 'planning', 'completed').
        current_step (str | None): The specific step currently executing.
        plan (dict | None): The generated curriculum plan JSON.
        validation (dict | None): The validation results JSON.
        storyboard (dict | None): The generated storyboard JSON.
        manim_code (str | None): The generated Manim Python code.
        video_url (str | None): URL to the rendered video file.
        error (str | None): Error message if the job failed.
        mode (str): Execution mode ('live' or 'mock').
        provider (str | None): AI provider requested at job creation
            (e.g. 'deepseek', 'google').
        model_id (str | None): Model ID requested at job creation.
        streamed_thoughts (list | None): Live stream of agent thoughts/deltas
            for the UI.
        cost (float): Estimated generation cost in USD.
        thumbnail_url (str | None): URL to the generated preview image.
        video_metadata (dict | None): JSON field for resolution, bit rate,
            file size, etc.
        created_at (datetime): Timestamp when the job was created.
        updated_at (datetime): Timestamp when the job was last updated.
    """

    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    target_audience: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="planning")
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    storyboard: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    manim_code: Mapped[str | None] = mapped_column(String, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, default="live")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    streamed_thoughts: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    cost: Mapped[float] = mapped_column(default=0.0)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    video_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[str] = mapped_column(String, default="720p")
    frame_rate: Mapped[int] = mapped_column(Integer, default=30)
    render_progress: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_status_schema(self) -> "JobStatus":
        """Converts the database record to the JobStatus Pydantic schema."""
        from api.schemas import (
            CurriculumPlan,
            JobStatus,
            Storyboard,
            ThoughtLog,
            ValidationResult,
        )

        status_literal = cast(
            Literal[
                "planning",
                "validating",
                "architecting",
                "animating",
                "rendering",
                "reviewing",
                "completed",
                "failed",
                "pending_retry",
            ],
            self.status,
        )
        mode_literal = cast(Literal["live", "mock"], self.mode)

        thoughts = [ThoughtLog(**t) for t in (self.streamed_thoughts or [])]

        return JobStatus(
            job_id=self.job_id,
            topic=self.topic,
            status=status_literal,
            plan=CurriculumPlan(**self.plan) if self.plan else None,
            validation=ValidationResult(**self.validation) if self.validation else None,
            storyboard=Storyboard(**self.storyboard) if self.storyboard else None,
            manim_code=self.manim_code,
            video_url=self.video_url,
            error=self.error,
            mode=mode_literal,
            streamed_thoughts=thoughts,
            provider=self.provider,
            model_id=self.model_id,
            target_audience=self.target_audience,
            resolution=self.resolution,
            frame_rate=self.frame_rate,
            started_at=self.started_at.isoformat() if self.started_at else None,
            finished_at=self.finished_at.isoformat() if self.finished_at else None,
            duration_seconds=(
                (self.finished_at - self.started_at).total_seconds()
                if self.started_at and self.finished_at
                else None
            ),
            cost=self.cost,
            retry_count=self.retry_count,
            thumbnail_url=self.thumbnail_url,
            video_metadata=self.video_metadata,
            render_progress=self.render_progress,
        )
