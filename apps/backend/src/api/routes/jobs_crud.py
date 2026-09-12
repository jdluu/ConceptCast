"""CRUD routes for job lifecycle management.

Provides endpoints for creating, listing, retrieving, retrying, and deleting
video generation jobs.
"""

import shutil
import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import JobListResponse, JobRequest, JobStatus
from infra.database import AsyncSessionLocal, get_db
from infra.database_utils import run_with_sqlite_retry
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.manager import determine_execution_mode, get_job_summaries
from services.jobs.serialization import (
    map_job_record_to_status,
    map_job_record_to_summary,
)
from services.workflow.orchestrator import prepare_job_for_retry, process_job_logic

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobStatus:
    """Initializes a new asynchronous video generation job.

    Implements idempotency: If a pending or completed job with the same topic
    already exists (created within the last hour), that
    existing job is returned instead of creating a new one.

    Args:
        request: The job creation configuration.
        background_tasks: FastAPI background tasks handler.
        req: FastAPI request to access application state.
        db: The active database session.

    Returns:
        The initial JobStatus of the newly created job.

    Raises:
        HTTPException: If an error occurs during job initialization.
    """
    try:
        is_mock = determine_execution_mode(request)
        mode = "mock" if is_mock else "live"

        # Check for existing job with same parameters (simple idempotency)
        # We limit the search to the last hour to allow for fresh attempts if requested.
        # NOTE: benchmark (seq, rep) pairs must never collide — a rep-2 create must not
        # match a rep-1 record with the same topic/model, so benchmark fields are part
        # of the match whenever the request carries benchmark metadata.
        idempotency_conditions = [
            JobRecord.user_prompt == request.topic,
            JobRecord.mode == mode,
            JobRecord.provider == request.provider,
            JobRecord.model_id == request.model_id,
            JobRecord.analyst_model == request.analyst_model,
            JobRecord.architect_model == request.architect_model,
            JobRecord.animator_model == request.animator_model,
            JobRecord.status != "failed",
        ]
        if request.benchmark_job_seq is not None:
            idempotency_conditions.append(
                JobRecord.benchmark_job_seq == request.benchmark_job_seq
            )
            idempotency_conditions.append(
                JobRecord.benchmark_arm == request.benchmark_arm
            )
            idempotency_conditions.append(
                JobRecord.benchmark_rep == request.benchmark_rep
            )
        idempotency_stmt = (
            select(JobRecord)
            .where(*idempotency_conditions)
            .order_by(JobRecord.created_at.desc())
            .limit(1)
        )
        existing_result = await db.execute(idempotency_stmt)
        existing_job = existing_result.scalar_one_or_none()

        if existing_job:
            created_at = existing_job.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)

            if (datetime.now(UTC) - created_at).total_seconds() < 3600:
                logger.info(
                    "idempotency_match_found",
                    job_id=existing_job.job_id,
                    topic=request.topic,
                )
                return map_job_record_to_status(existing_job)

        job_id = str(uuid.uuid4())

        # Initialize job with the raw prompt as the initial topic;
        # orchestration will refine it.
        new_job = JobRecord(
            job_id=job_id,
            topic=request.topic,
            user_prompt=request.topic,
            status="planning",
            mode=mode,
            provider=request.provider,
            model_id=request.model_id,
            analyst_model=request.analyst_model,
            architect_model=request.architect_model,
            animator_model=request.animator_model,
            benchmark_job_seq=request.benchmark_job_seq,
            benchmark_arm=request.benchmark_arm,
            benchmark_rep=request.benchmark_rep,
        )

        async def _save_job() -> None:
            db.add(new_job)
            await db.commit()
            await db.refresh(new_job)

        try:
            await run_with_sqlite_retry(db, _save_job)
        except Exception as e:
            # The transaction was rolled back by run_with_sqlite_retry,
            # but we use a fresh session to avoid stale session state.
            async with AsyncSessionLocal() as fresh_db:
                existing_result = await fresh_db.execute(idempotency_stmt)
                existing_job = existing_result.scalar_one_or_none()
                if existing_job:
                    logger.info("race_condition_resolved", job_id=existing_job.job_id)
                    return map_job_record_to_status(existing_job)

            logger.error("job_creation_db_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e)) from e

        session_factory = getattr(
            req.app.state, "db_session_factory", AsyncSessionLocal
        )

        # Enqueue with the original request, which will be refined in the orchestrator.
        background_tasks.add_task(
            process_job_logic,
            job_id,
            request,
            session_factory,
        )

        return map_job_record_to_status(new_job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> JobStatus:
    """Retrieves the current status and artifacts for a specific job.

    Args:
        job_id: The unique identifier of the job.
        db: The active database session.

    Returns:
        The current JobStatus.

    Raises:
        HTTPException: If the job is not found.
    """
    result = await db.execute(
        select(JobRecord)
        .options(selectinload(JobRecord.thoughts))
        .where(JobRecord.job_id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return map_job_record_to_status(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    mode: Literal["live", "mock"] | None = None,
) -> JobListResponse:
    """Lists all jobs sorted by creation date (newest first).

    Uses an optimized query that defers heavy columns.

    Args:
        mode: Optional filter to return only 'live' or 'mock' jobs.
        db: The active database session.

    Returns:
        JobListResponse containing a list of job summaries.

    Raises:
        HTTPException: If an error occurs during serialization.
    """
    jobs = await get_job_summaries(db, mode)

    summary_list = []
    try:
        for job in jobs:
            summary_list.append(map_job_record_to_summary(job))
    except Exception as e:
        logger.error("jobs_serialization_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Serialization error: {e}") from e

    return JobListResponse(jobs=summary_list)


@router.post("/{job_id}/retry", response_model=JobStatus)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    req: Request,
    _db: Annotated[AsyncSession, Depends(get_db)],
) -> JobStatus:
    """Retries a failed or stuck job from the last successful checkpoint.

    Resets the job status and triggers background logic again.

    Args:
        job_id: The unique identifier of the job to retry.
        background_tasks: FastAPI background tasks handler.
        req: FastAPI request to access application state.
        _db: The active database session.

    Returns:
        The updated JobStatus after resetting for retry.
    """
    # Fetch job status to ensure we only retry failed or paused/awaiting_review jobs
    result = await _db.execute(
        select(JobRecord.status).where(JobRecord.job_id == job_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    current_status = row[0]
    if current_status not in {"failed", "awaiting_review"}:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Job {job_id} is in state '{current_status}' and cannot be retried. "
                "Only failed or paused jobs can be retried."
            ),
        )

    session_factory = getattr(req.app.state, "db_session_factory", AsyncSessionLocal)
    job = await prepare_job_for_retry(job_id, session_factory)

    request = JobRequest(
        topic=job.topic,
        provider=job.provider,
        model_id=job.model_id,
        analyst_model=job.analyst_model,
        architect_model=job.architect_model,
        animator_model=job.animator_model,
    )

    background_tasks.add_task(process_job_logic, job_id, request, session_factory)

    return map_job_record_to_status(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    """Deletes a job and its associated filesystem data.

    Args:
        job_id: The unique identifier of the job to delete.
        db: The active database session.

    Raises:
        HTTPException: If the job is not found.
    """
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
            logger.warning(
                "job_artifacts_delete_failed",
                job_id=job_id,
                error=str(e),
            )

    await db.delete(job)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    mode: Literal["live", "mock"] | None = None,
) -> None:
    """Deletes multiple jobs and clears their associated filesystem data.

    Args:
        mode: Optional filter to only delete 'live' or 'mock' jobs.
        db: The active database session.
    """
    settings = get_settings()
    jobs_root = settings.jobs_dir

    if mode:
        stmt = select(JobRecord.job_id).where(JobRecord.mode == mode)
        res = await db.execute(stmt)
        ids_to_delete = res.scalars().all()

        await db.execute(delete(JobRecord).where(JobRecord.mode == mode))
        await db.commit()

        for jid in ids_to_delete:
            jdir = jobs_root / jid
            if jdir.exists() and jdir.is_dir():
                try:
                    shutil.rmtree(jdir)
                except Exception as e:
                    logger.warning(
                        "job_artifacts_delete_failed",
                        job_id=jid,
                        error=str(e),
                    )
    else:
        await db.execute(delete(JobRecord))
        await db.commit()

        if jobs_root.exists() and jobs_root.is_dir():
            for item in jobs_root.iterdir():
                if item.is_dir():
                    try:
                        shutil.rmtree(item)
                    except Exception as e:
                        logger.warning(
                            "job_dir_delete_failed",
                            path=str(item),
                            error=str(e),
                        )
