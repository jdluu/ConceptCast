"""Pydantic schemas for job-related API requests and responses.

Defines the structure for job summaries, comprehensive status records, and
creation requests.
"""

from typing import Literal

from pydantic import BaseModel, Field

from domain.models.curriculum import CurriculumPlan
from domain.models.storyboard import Storyboard

from .common import ThoughtLog


class JobSummary(BaseModel):
    """Concise representation of a job for listings."""

    job_id: str
    topic: str
    user_prompt: str | None = None
    status: str
    current_step: str | None = None
    mode: str
    created_at: str
    retry_count: int
    error: str | None
    provider: str | None = None
    model_id: str | None = None
    analyst_model: str | None = None
    architect_model: str | None = None
    animator_model: str | None = None
    benchmark_job_seq: int | None = None
    benchmark_arm: str | None = None
    benchmark_rep: int | None = None

    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    cost: float = 0.0
    thumbnail_url: str | None = None
    video_url: str | None = None
    preview_url: str | None = None
    video_metadata: dict[str, object] | None = None
    render_progress: int = 0
    failure_stage: str | None = None
    failure_type: str | None = None
    failure_summary: str | None = None
    architect_fallback_used: bool = False
    architect_attempts: int = 0
    architect_original_error: str | None = None
    architect_transport: str | None = None


class JobListResponse(BaseModel):
    """Wrapper response for a paginated or filtered list of jobs."""

    jobs: list[JobSummary]


class JobStatus(BaseModel):
    """Comprehensive state record for a job."""

    job_id: str
    topic: str | None = None
    user_prompt: str | None = None
    streamed_thoughts: list[ThoughtLog] = Field(default_factory=list)
    status: Literal[
        "planning",
        "architecting",
        "animating",
        "rendering",
        "reviewing",
        "awaiting_review",
        "completed",
        "failed",
        "pending_retry",
    ]
    current_step: str | None = None
    plan: CurriculumPlan | None = None
    storyboard: Storyboard | None = None
    manim_code: str | None = None
    video_url: str | None = None
    error: str | None
    mode: Literal["live", "mock"] = "live"
    provider: str | None = None

    model_id: str | None = None
    analyst_model: str | None = None
    architect_model: str | None = None
    animator_model: str | None = None
    benchmark_job_seq: int | None = None
    benchmark_arm: str | None = None
    benchmark_rep: int | None = None

    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    cost: float = 0.0
    retry_count: int = 0
    thumbnail_url: str | None = None
    preview_url: str | None = None
    video_metadata: dict[str, object] | None = None
    render_progress: int = 0
    failure_stage: str | None = None
    failure_type: str | None = None
    failure_summary: str | None = None
    architect_fallback_used: bool = False
    architect_attempts: int = 0
    architect_original_error: str | None = None
    architect_transport: str | None = None


class JobRequest(BaseModel):
    """Parameters for a new generation job."""

    topic: str = Field(..., description="Concept to explain")
    provider: str | None = None
    model_id: str | None = None
    analyst_model: str | None = None
    architect_model: str | None = None
    animator_model: str | None = None
    benchmark_job_seq: int | None = None
    benchmark_arm: str | None = None
    benchmark_rep: int | None = None
