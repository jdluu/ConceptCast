from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from core.settings import get_settings

DATABASE_URL = get_settings().database_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Initializes the database tables asynchronously.

    Creates all tables defined in the SQLAlchemy models if they do not already exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
