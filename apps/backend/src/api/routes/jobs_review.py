"""Routes for preview generation and plan retrieval.

Provides endpoints for low-quality preview rendering and direct plan access
for jobs in the generation pipeline. The human-in-the-loop review gate was
removed from the framework; jobs no longer pause for manual approval.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import CurriculumPlan, JobRequest, JobStatus
from infra.database import AsyncSessionLocal, get_db
from infra.models.job import JobRecord
from services.jobs.serialization import map_job_record_to_status
from services.workflow.orchestrator import process_job_logic

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/{job_id}/preview", response_model=JobStatus)
async def get_job_preview(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobStatus:
    """Triggers or retrieves a low-quality preview frame for a job.

    If a preview frame already exists in the job's artifact directory, its URL
    is returned immediately. Otherwise, it triggers a fast, low-resolution
    Manim render to extract a representative frame for the current code.

    Args:
        job_id: The unique identifier of the job.
        db: The active database session.

    Returns:
        JobStatus: The updated job status record containing the `preview_url`.

    Raises:
        HTTPException: If the job is not found or code hasn't been generated yet.
    """
    from infra.engines.video import render_preview

    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.preview_url:
        return map_job_record_to_status(job)

    if not job.manim_code:
        raise HTTPException(
            status_code=400, detail="Manim code not yet generated for this job."
        )

    # Trigger fast preview render
    preview = await render_preview(job.manim_code, job_id)
    if preview.success and preview.frame_path:
        # Map local path to accessible URL
        job.preview_url = f"/jobs/artifacts/{job_id}/preview_frame.png"
        await db.commit()
        await db.refresh(job)
    else:
        logger.warning("preview_generation_failed", job_id=job_id, error=preview.error)

    return map_job_record_to_status(job)


@router.get("/{job_id}/plan", response_model=CurriculumPlan)
async def get_plan(
    job_id: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> CurriculumPlan:
    """Retrieves the generated curriculum plan for a specific job.

    Args:
        job_id: The unique identifier of the job.
        db: The active database session.

    Returns:
        The curriculum plan as a CurriculumPlan object.

    Raises:
        HTTPException: If the job or plan is not found.
    """
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job or not job.plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return CurriculumPlan.model_validate(job.plan)
