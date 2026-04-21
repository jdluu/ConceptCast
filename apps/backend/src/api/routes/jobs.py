"""API endpoints for managing pedagogical video generation jobs.

Provides routes for job creation, status monitoring, real-time update streaming,
and resource lifecycle management.
"""

import json
import shutil
import time
import uuid
from collections.abc import AsyncGenerator, Callable
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
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    CurriculumPlan,
    JobListResponse,
    JobRequest,
    JobReviewRequest,
    JobStatus,
)
from infra.database import AsyncSessionLocal, get_db
from infra.database_utils import run_with_sqlite_retry
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.events import job_event_manager
from services.jobs.manager import determine_execution_mode, get_job_summaries
from services.jobs.serialization import (
    map_job_record_to_status,
    map_job_record_to_summary,
)
from services.workflow.orchestrator import prepare_job_for_retry, process_job_logic

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database.

    Args:
        job_id: The unique identifier of the job to monitor.
        db_session_factory: Factory function for creating database sessions.

    Yields:
        SSE events as strings formatted for the client.
    """
    last_status = None
    last_step = None
    last_thought_count = 0
    last_thought_content_len = 0
    last_artifact_state: tuple[bool, bool, bool, bool, bool, int] | None = None
    first_emit = True
    last_emit_monotonic = 0.0
    min_emit_interval_seconds = 0.35

    while True:
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord)
                .options(selectinload(JobRecord.thoughts))
                .where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            thoughts = job.thoughts or []
            current_thought_content_len = len(thoughts[-1].content) if thoughts else 0

            status_changed = job.status != last_status
            step_changed = job.current_step != last_step
            thought_count_changed = len(thoughts) != last_thought_count
            thought_content_changed = (
                current_thought_content_len != last_thought_content_len
            )
            artifact_state = (
                job.plan is not None,
                CurriculumPlan.model_validate(job.plan).is_structurally_valid()[0]
                if job.plan
                else False,
                job.storyboard is not None,
                bool(job.manim_code),
                bool(job.error),
                int(job.render_progress or 0),
            )
            artifact_changed = artifact_state != last_artifact_state

            should_emit = (
                first_emit
                or status_changed
                or step_changed
                or artifact_changed
                or thought_count_changed
                or thought_content_changed
            )

            # Throttle noisy high-frequency thought-content-only updates.
            now_monotonic = time.monotonic()
            only_content_delta = (
                not first_emit
                and not status_changed
                and not step_changed
                and not artifact_changed
                and not thought_count_changed
                and thought_content_changed
            )
            if only_content_delta and (
                now_monotonic - last_emit_monotonic < min_emit_interval_seconds
            ):
                should_emit = False

            if should_emit:
                status_payload = map_job_record_to_status(job)
                yield f"data: {status_payload.model_dump_json()}\n\n"
                last_status = job.status
                last_step = job.current_step
                last_thought_count = len(thoughts)
                last_thought_content_len = current_thought_content_len
                last_artifact_state = artifact_state
                first_emit = False
                last_emit_monotonic = now_monotonic

            if job.status in ["completed", "failed"]:
                break

        await job_event_manager.wait_for_update(job_id, timeout=15.0)


@router.post("/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobStatus:
    """Initializes a new asynchronous video generation job.

    Implements idempotency: If a pending or completed job with the same topic
    and target audience already exists (created within the last hour), that
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
        idempotency_stmt = (
            select(JobRecord)
            .where(
                JobRecord.user_prompt == request.topic,
                JobRecord.target_audience == request.target_audience,
                JobRecord.mode == mode,
                JobRecord.status != "failed",
            )
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
        
        # Initialize job with the raw prompt as the initial topic; orchestration will refine it.
        new_job = JobRecord(
            job_id=job_id,
            topic=request.topic,
            user_prompt=request.topic,
            target_audience=request.target_audience,
            status="planning",
            mode=mode,
            hitl_enabled=request.hitl_enabled,
            provider=request.provider,
            model_id=request.model_id,
            analyst_model=request.analyst_model,
            architect_model=request.architect_model,
            animator_model=request.animator_model,
        )

        async def _save_job() -> None:
            db.add(new_job)
            await db.commit()
            await db.refresh(new_job)

        try:
            await run_with_sqlite_retry(db, _save_job)
        except Exception as e:
            # The transaction was rolled back by run_with_sqlite_retry, 
            # but we use a fresh session just in case to avoid any 'session is closed' or 'invalid' states.
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


@router.post("/{job_id}/review", response_model=JobStatus)
async def review_job(
    job_id: str,
    review: JobReviewRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobStatus:
    """Handles human-in-the-loop review actions for a paused job."""
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "awaiting_review":
        raise HTTPException(
            status_code=400,
            detail=f"Job is in state '{job.status}', not awaiting review.",
        )

    session_factory = getattr(req.app.state, "db_session_factory", AsyncSessionLocal)

    if review.action == "approve":
        # Apply edits if provided
        if review.edited_plan:
            job.plan = review.edited_plan.model_dump()
            # Edited plan invalidates all downstream artifacts.
            job.storyboard = None
            job.manim_code = None
            job.video_url = None
            job.thumbnail_url = None
            job.video_metadata = None
            job.render_progress = 0

        job.status = "architecting"
        job.current_step = "planning_complete"
        await db.commit()
        await db.refresh(job)

        # Resume workflow from Step 2
        background_tasks.add_task(
            process_job_logic,
            job_id,
            JobRequest(
                topic=job.topic,
                target_audience=job.target_audience or "General",
                provider=job.provider,
                model_id=job.model_id,
                hitl_enabled=job.hitl_enabled,
                analyst_model=job.analyst_model,
                architect_model=job.architect_model,
                animator_model=job.animator_model,
            ),
            session_factory,
        )

    elif review.action == "regenerate":
        # Reset plan and downstream artifacts to trigger full regeneration.
        job.plan = None
        job.storyboard = None
        job.manim_code = None
        job.video_url = None
        job.thumbnail_url = None
        job.video_metadata = None
        job.render_progress = 0
        job.status = "planning"

        await db.commit()
        await db.refresh(job)

        background_tasks.add_task(
            process_job_logic,
            job_id,
            JobRequest(
                topic=f"{job.topic} (Feedback: {review.feedback})"
                if review.feedback
                else job.topic,
                target_audience=job.target_audience or "General",
                provider=job.provider,
                model_id=job.model_id,
                hitl_enabled=job.hitl_enabled,
                analyst_model=job.analyst_model,
                architect_model=job.architect_model,
                animator_model=job.animator_model,
            ),
            session_factory,
        )

    return map_job_record_to_status(job)


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


@router.get("/{job_id}/events")
async def job_events(
    job_id: str,
    db_session_factory: Annotated[
        Callable[[], AsyncSession], Depends(lambda: AsyncSessionLocal)
    ],
) -> StreamingResponse:
    """Provides a real-time stream of job updates via Server-Sent Events (SSE).

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


@router.get("", response_model=JobListResponse)
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
        db: The active database session.

    Returns:
        The updated JobStatus after resetting for retry.
    """
    session_factory = getattr(req.app.state, "db_session_factory", AsyncSessionLocal)
    job = await prepare_job_for_retry(job_id, session_factory)

    request = JobRequest(
        topic=job.topic,
        target_audience=job.target_audience or "General Audience",
        provider=job.provider,
        model_id=job.model_id,
        hitl_enabled=job.hitl_enabled,
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


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
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
