from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, cast

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from infra.database import Base

if TYPE_CHECKING:
    from api.schemas import JobStatus


class JobRecord(Base):
    """SQLAlchemy model representing a content generation job.

    Tracks the entire lifecycle of a job, from initial planning through
    validation, architecting, and final rendering. Stores both state
    information and references to generated artifacts (plan, storyboard,
    video URL).
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
    total_execution_time: Mapped[float] = mapped_column(default=0.0)
    resolution: Mapped[str] = mapped_column(String, default="720p")
    frame_rate: Mapped[int] = mapped_column(Integer, default=30)
    render_progress: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_status_schema(self) -> "JobStatus":
        """Converts the database record to a validated Pydantic schema.

        Handles the mapping of internal state and JSON blobs to structured
        objects for API responses.

        Returns:
            A JobStatus instance representing the current state.
        """
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

        # Calculate processing duration
        # If running: total confirmed + duration of current session
        # If terminal: purely the total confirmed time
        is_active = status_literal not in ("completed", "failed", "pending_retry")
        current_session_duration = 0.0
        if is_active and self.started_at:
            started_at = self.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            current_session_duration = (
                datetime.now(UTC) - started_at
            ).total_seconds()

        duration_seconds = self.total_execution_time + current_session_duration

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
            duration_seconds=max(0.0, duration_seconds),
            cost=self.cost,
            retry_count=self.retry_count,
            thumbnail_url=self.thumbnail_url,
            video_metadata=self.video_metadata,
            render_progress=self.render_progress,
        )
