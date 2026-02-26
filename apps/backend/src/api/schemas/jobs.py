from typing import Any, Literal

from pydantic import BaseModel, Field

from domain.models.curriculum import CurriculumPlan, ValidationResult
from domain.models.storyboard import Storyboard

from .common import ThoughtLog


class JobSummary(BaseModel):
    """Concise representation of a job for listings."""

    job_id: str
    topic: str
    status: str
    mode: str
    created_at: str
    retry_count: int
    error: str | None
    provider: str | None = None
    model_id: str | None = None
    target_audience: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    cost: float = 0.0
    thumbnail_url: str | None = None
    video_url: str | None = None
    video_metadata: dict[str, Any] | None = None
    resolution: str = "720p"
    frame_rate: int = 30
    render_progress: int = 0


class JobListResponse(BaseModel):
    jobs: list[JobSummary]


class JobStatus(BaseModel):
    """Comprehensive state record for a job."""

    job_id: str
    topic: str | None = None
    streamed_thoughts: list[ThoughtLog] = Field(default_factory=list)
    status: Literal[
        "planning",
        "validating",
        "architecting",
        "animating",
        "rendering",
        "reviewing",
        "completed",
        "failed",
        "pending_retry",
    ]
    current_step: str | None = None
    plan: CurriculumPlan | None = None
    validation: ValidationResult | None = None
    storyboard: Storyboard | None = None
    manim_code: str | None = None
    video_url: str | None = None
    error: str | None = None
    mode: Literal["live", "mock"] = "live"
    provider: str | None = None
    model_id: str | None = None
    target_audience: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    cost: float = 0.0
    retry_count: int = 0
    thumbnail_url: str | None = None
    video_metadata: dict[str, Any] | None = None
    resolution: str = "720p"
    frame_rate: int = 30
    render_progress: int = 0


class JobRequest(BaseModel):
    """Parameters for a new generation job."""

    topic: str = Field(..., description="Concept to explain")
    target_audience: str = "Undergraduate CS"
    provider: str | None = None
    model_id: str | None = None
    resolution: Literal["720p", "1080p"] = "720p"
    frame_rate: Literal[30, 60] = 30
    fast_mode: bool = False
