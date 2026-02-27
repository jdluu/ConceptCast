import json
import shutil
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
from infra.database import AsyncSessionLocal, get_db
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager
from services.jobs.manager import (
    determine_execution_mode,
    prepare_job_for_retry_logic,
)
from services.workflow.orchestrator import prepare_job_for_retry, process_job_logic

router = APIRouter()


# Helper for SSE
async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database."""

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

            # Stream on first connection or when any relevant field changes
            if (
                first_emit
                or job.status != last_status
                or job.updated_at != last_updated
                or len(thoughts) != last_thought_count
            ):
                # Use get_job_status helper logic for consistent serialization
                # We can't call the endpoint directly easily, so we manually construct
                # or better yet, use a shared helper if we had one.
                # For now, let's just make sure we include EVERYTHING.
                yield f"data: {job.to_status_schema().model_dump_json()}\n\n"
                last_status = job.status
                last_updated = job.updated_at
                last_thought_count = len(thoughts)
                first_emit = False

            if job.status in ["completed", "failed"]:
                break

        # Wait for next event or timeout (keep-alive)
        await job_event_manager.wait_for_update(job_id, timeout=15.0)


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

        is_mock = determine_execution_mode(request)
        mode = "mock" if is_mock else "live"
        new_job = JobRecord(
            job_id=job_id,
            topic=request.topic,
            target_audience=request.target_audience,
            status="planning",
            mode=mode,
            provider=request.provider,
            model_id=request.model_id,
            resolution=request.resolution,
            frame_rate=request.frame_rate,
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
            topic=request.topic,
            status="planning",
            mode=cast(Literal["live", "mock"], mode),
            provider=request.provider,
            model_id=request.model_id,
            target_audience=request.target_audience,
            resolution=request.resolution,
            frame_rate=request.frame_rate,
            retry_count=0,
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

    return job.to_status_schema()


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
                    resolution=job.resolution,
                    frame_rate=job.frame_rate,
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
                    video_url=job.video_url,
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
        resolution=cast(Literal["720p", "1080p"], job.resolution),
        frame_rate=cast(Literal[30, 60], job.frame_rate),
        fast_mode=False,
    )

    # 3. Trigger background processing
    background_tasks.add_task(process_job_logic, job_id, request, session_factory)

    return job.to_status_schema()


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)) -> None:
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

    settings = get_settings()
    job_dir = settings.jobs_dir / job_id
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
async def delete_all_jobs(db: AsyncSession = Depends(get_db)) -> None:
    """Deletes ALL jobs from the database and clears the entire jobs filesystem root.

    Args:
        db: The active database session.

    Returns:
        None
    """
    settings = get_settings()
    jobs_root = settings.jobs_dir

    # Efficient bulk delete
    await db.execute(delete(JobRecord))
    await db.commit()

    # Clear filesystem
    if jobs_root.exists() and jobs_root.is_dir():
        for item in jobs_root.iterdir():
            if item.is_dir():
                try:
                    shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Error deleting job dir {item}: {e}")

    return None
