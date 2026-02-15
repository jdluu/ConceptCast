import json
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Literal, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    CurriculumPlan,
    JobListResponse,
    JobRequest,
    JobStatus,
    JobSummary,
)
from core.database import AsyncSessionLocal, JobRecord, get_db
from services.orchestrator import prepare_job_for_retry, process_job_logic

router = APIRouter()


# Helper for SSE
async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database."""
    import asyncio

    last_status = None
    last_updated = None
    last_thought_count = 0
    first_emit = True

    while True:
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            thoughts = getattr(job, "streamed_thoughts", None) or []
            thought_count = len(thoughts)

            # Stream on first connection or when any relevant field changes
            if (
                first_emit
                or job.status != last_status
                or job.updated_at != last_updated
                or thought_count != last_thought_count
            ):
                data = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "plan": job.plan,
                    "validation": job.validation,
                    "storyboard": job.storyboard,
                    "manim_code": job.manim_code,
                    "video_url": job.video_url,
                    "error": job.error,
                    "mode": job.mode,
                    "streamed_thoughts": thoughts,
                    "provider": job.provider,
                    "model_id": job.model_id,
                    "target_audience": job.target_audience,
                    "started_at": (
                        job.started_at.isoformat() if job.started_at else None
                    ),
                    "finished_at": (
                        job.finished_at.isoformat() if job.finished_at else None
                    ),
                    "duration_seconds": (
                        (job.finished_at - job.started_at).total_seconds()
                        if job.started_at and job.finished_at
                        else None
                    ),
                    "cost": job.cost,
                    "thumbnail_url": job.thumbnail_url,
                    "video_metadata": job.video_metadata,
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_status = job.status
                last_updated = job.updated_at
                last_thought_count = thought_count
                first_emit = False

            if job.status in ["completed", "failed"]:
                break

        await asyncio.sleep(0.5)  # Poll DB for streaming updates


@router.post("/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    req: Request,  # To access app.state
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Initializes a new asynchronous video generation job."""
    try:
        job_id = str(uuid.uuid4())

        mode = "mock" if request.provider == "mock" else "live"
        new_job = JobRecord(
            job_id=job_id,
            topic=request.topic,
            target_audience=request.target_audience,
            status="planning",
            mode=mode,
            provider=request.provider,
            model_id=request.model_id,
        )

        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)

        # Use the session factory from app state for background task
        session_factory = getattr(
            req.app.state, "db_session_factory", AsyncSessionLocal
        )
        background_tasks.add_task(process_job_logic, job_id, request, session_factory)

        return JobStatus(
            job_id=job_id,
            status="planning",
            mode=mode,
            provider=request.provider,
            model_id=request.model_id,
            target_audience=request.target_audience,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)) -> JobStatus:
    """Retrieves the current status and artifacts for a specific job."""
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    status_literal = cast(
        Literal[
            "planning",
            "validating",
            "architecting",
            "rendering",
            "reviewing",
            "completed",
            "failed",
        ],
        job.status,
    )
    mode_literal = cast(Literal["live", "mock"], job.mode)

    return JobStatus(
        job_id=job.job_id,
        status=status_literal,
        plan=job.plan,
        validation=job.validation,
        storyboard=job.storyboard,
        manim_code=job.manim_code,
        video_url=job.video_url,
        error=job.error,
        mode=mode_literal,
        streamed_thoughts=getattr(job, "streamed_thoughts", None) or [],
        provider=job.provider,
        model_id=job.model_id,
        target_audience=job.target_audience,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        duration_seconds=(
            (job.finished_at - job.started_at).total_seconds()
            if job.started_at and job.finished_at
            else None
        ),
        cost=job.cost,
        thumbnail_url=job.thumbnail_url,
        video_metadata=job.video_metadata,
    )


@router.get("/{job_id}/events")
async def job_events(
    job_id: str,
    db_session_factory: Callable[[], AsyncSession] = Depends(lambda: AsyncSessionLocal),
) -> StreamingResponse:
    """Provides a real-time stream of job updates via SSE.

    Args:
        job_id: The unique identifier of the job to stream.
        db_session_factory: Dependency for creating database sessions.

    Returns:
        StreamingResponse: An SSE event stream.
    """
    return StreamingResponse(
        _stream_job_events(job_id, db_session_factory), media_type="text/event-stream"
    )


@router.get("/{job_id}/plan", response_model=CurriculumPlan)
async def get_plan(job_id: str, db: AsyncSession = Depends(get_db)) -> CurriculumPlan:
    """Retrieves the generated curriculum plan for a specific job."""
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job or not job.plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return CurriculumPlan(**job.plan)


@router.get("", response_model=JobListResponse)
async def list_jobs(db: AsyncSession = Depends(get_db)) -> JobListResponse:
    """Lists all jobs sorted by creation date (newest first).

    Args:
        db: The active database session.

    Returns:
        JobListResponse: A paginated or list of job summaries.
    """
    # Select all jobs, ordered by created_at desc
    result = await db.execute(select(JobRecord).order_by(JobRecord.created_at.desc()))
    jobs = result.scalars().all()

    summary_list = []
    try:
        for job in jobs:
            # Handle potential missing retry_count on old records
            retry_count_val = job.retry_count if job.retry_count is not None else 0

            summary_list.append(
                JobSummary(
                    job_id=job.job_id,
                    topic=job.topic,
                    status=job.status,
                    mode=job.mode,
                    created_at=job.created_at.isoformat(),
                    retry_count=retry_count_val,
                    error=job.error,
                    provider=job.provider,
                    model_id=job.model_id,
                    target_audience=job.target_audience,
                    started_at=(job.started_at.isoformat() if job.started_at else None),
                    finished_at=(
                        job.finished_at.isoformat() if job.finished_at else None
                    ),
                    duration_seconds=(
                        (job.finished_at - job.started_at).total_seconds()
                        if job.started_at and job.finished_at
                        else None
                    ),
                    cost=job.cost,
                    thumbnail_url=job.thumbnail_url,
                    video_metadata=job.video_metadata,
                )
            )
    except Exception as e:
        logger.error(f"Error serializing job: {e}")
        raise HTTPException(status_code=500, detail=f"Serialization error: {e}") from e

    return JobListResponse(jobs=summary_list)


@router.post("/{job_id}/retry", response_model=JobStatus)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    req: Request,  # To access app.state
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Retries a failed or stuck job from the last successful checkpoint."""
    # 1. Reset job state
    session_factory = getattr(req.app.state, "db_session_factory", AsyncSessionLocal)
    job = await prepare_job_for_retry(job_id, session_factory)

    # 2. Reconstruct JobRequest from stored record
    # We need this to reconstruct the request for reprocessing
    request = JobRequest(
        topic=job.topic,
        target_audience=job.target_audience or "General Audience",
        provider=job.provider,
        model_id=job.model_id,
    )

    # 3. Trigger background processing
    background_tasks.add_task(process_job_logic, job_id, request, session_factory)

    status_literal = cast(
        Literal[
            "planning",
            "validating",
            "architecting",
            "rendering",
            "reviewing",
            "completed",
            "failed",
            "pending_retry",
        ],
        job.status,
    )
    mode_literal = cast(Literal["live", "mock"], job.mode)

    return JobStatus(
        job_id=job.job_id,
        status=status_literal,
        plan=job.plan,
        validation=job.validation,
        storyboard=job.storyboard,
        manim_code=job.manim_code,
        video_url=job.video_url,
        error=job.error,
        mode=mode_literal,
        retry_count=job.retry_count,
        streamed_thoughts=[],
    )


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a job and its associated filesystem data.

    Args:
        job_id: The unique identifier of the job to delete.
        db: The active database session.

    Returns:
        None
    """
    # Check if job exists
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete associated files if they exist
    import os
    import shutil
    from pathlib import Path

    # We need to access JOBS_ROOT, which was defined in main.py
    # Re-definition here or import from settings
    _PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
    PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", _PROJECT_ROOT))
    JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"

    job_dir = JOBS_ROOT / job_id
    if job_dir.exists() and job_dir.is_dir():
        try:
            shutil.rmtree(job_dir)
        except Exception as e:
            # We log but continue deletion from DB to avoid stuck records
            logger.warning(f"Error deleting job artifacts for {job_id}: {e}")

    # Delete from DB
    await db.delete(job)
    await db.commit()
    return None


@router.delete("", status_code=204)
async def delete_all_jobs(db: AsyncSession = Depends(get_db)):
    """Deletes ALL jobs from the database and clears the entire jobs filesystem root.

    Args:
        db: The active database session.

    Returns:
        None
    """
    import os
    import shutil
    from pathlib import Path

    # Re-definition of JOBS_ROOT
    _PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
    PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", _PROJECT_ROOT))
    JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"

    # Efficient bulk delete
    await db.execute(delete(JobRecord))
    await db.commit()

    # Clear filesystem
    if JOBS_ROOT.exists() and JOBS_ROOT.is_dir():
        for item in JOBS_ROOT.iterdir():
            if item.is_dir():
                try:
                    shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Error deleting job dir {item}: {e}")

    return None
