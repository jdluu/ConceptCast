from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.database import Base

if TYPE_CHECKING:
    from infra.models.thought import ThoughtRecord


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
    user_prompt: Mapped[str | None] = mapped_column(String, nullable=True)
    target_audience: Mapped[str] = mapped_column(String, nullable=True)
    benchmark_job_seq: Mapped[int | None] = mapped_column(nullable=True)
    benchmark_arm: Mapped[str | None] = mapped_column(String, nullable=True)
    benchmark_rep: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, default="planning", index=True)
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    plan: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    storyboard: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    manim_code: Mapped[str | None] = mapped_column(String, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, default="live")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    hitl_enabled: Mapped[bool] = mapped_column(default=False)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    analyst_model: Mapped[str | None] = mapped_column(String, nullable=True)
    validator_model: Mapped[str | None] = mapped_column(String, nullable=True)
    architect_model: Mapped[str | None] = mapped_column(String, nullable=True)
    animator_model: Mapped[str | None] = mapped_column(String, nullable=True)

    thoughts: Mapped[list["ThoughtRecord"]] = relationship(
        "ThoughtRecord",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    cost: Mapped[float] = mapped_column(default=0.0)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    video_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_execution_time: Mapped[float] = mapped_column(default=0.0)
    render_progress: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
