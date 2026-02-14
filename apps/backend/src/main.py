import asyncio
import json
import os
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, cast

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.factory import get_available_providers_and_models
from api.schemas import (
    AvailableModelsResponse,
    CurriculumPlan,
    JobListResponse,
    JobRequest,
    JobStatus,
    JobSummary,
)
from core.database import AsyncSessionLocal, JobRecord, get_db, init_db
from core.settings import get_settings
from services.orchestrator import prepare_job_for_retry, process_job_logic


async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database.

    Args:
        job_id: The unique identifier of the job to monitor.
        db_session_factory: A factory function that returns an 
            AsyncSession for non-blocking polls.

    Yields:
        str: An SSE-formatted string containing the job status 
            and artifacts in JSON format.
    """
    last_status = None
    last_updated = None
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

            # Stream on first connection (so UI gets state immediately) 
            # or when status/updated_at changed
            if (
                first_emit
                or job.status != last_status
                or job.updated_at != last_updated
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
                    "streamed_thoughts": getattr(job, "streamed_thoughts", None) or [],
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_status = job.status
                last_updated = job.updated_at
                first_emit = False

            if job.status in ["completed", "failed"]:
                break

        await asyncio.sleep(0.5)  # Poll DB for streaming updates


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the FastAPI application lifecycle.

    Initializes the asynchronous database connection and stores the session factory
    in the application state for global access (e.g., in background tasks).

    Args:
        app: The FastAPI application instance.
    """
    await init_db()
    # Store session factory in app state for background tasks
    app.state.db_session_factory = AsyncSessionLocal
    yield


app = FastAPI(title="ConceptCast Backend", lifespan=lifespan)

cors_origins = get_settings().cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job Artifact Storage Configuration (PROJECT_ROOT set in Docker to /app)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", _PROJECT_ROOT))
JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/jobs/artifacts", StaticFiles(directory=str(JOBS_ROOT)), name="job_artifacts"
)

_FRONTEND_DIST = os.environ.get("FRONTEND_DIST")
_FRONTEND_DIST_PATH = Path(_FRONTEND_DIST) if _FRONTEND_DIST else None
_serving_spa = _FRONTEND_DIST_PATH and _FRONTEND_DIST_PATH.is_dir()


@app.get("/models/available", response_model=AvailableModelsResponse)
async def get_available_models() -> AvailableModelsResponse:
    """Retrieves the list of supported AI providers and their models.
    Only includes providers for which the user has an API key configured; 
    mock is always included. No tiered priority.
    """
    settings = get_settings()
    result = get_available_providers_and_models(settings)
    return AvailableModelsResponse(available=result)


if not _serving_spa:

    @app.get("/")
    async def read_root() -> dict[str, str]:
        """Root health-check endpoint (used when frontend is not bundled)."""
        return {"message": "Welcome to ConceptCast Council"}


@app.post("/jobs/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Initializes a new asynchronous video generation job.
    Creates a job record in the database and triggers 
    the background processing workflow.

    Args:
        request: The job configuration (topic, audience, provider).
        background_tasks: FastAPI BackgroundTasks handler.
        db: The asynchronous database session.

    Returns:
        JobStatus: The initial status of the created job.

    Raises:
        HTTPException: If job initialization fails.
    """
    try:
        # Note: create_new_job must be updated to handle async session
        # For now, we inline the creation logic to ensure async compat
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
        session_factory = getattr(app.state, "db_session_factory", AsyncSessionLocal)
        background_tasks.add_task(process_job_logic, job_id, request, session_factory)

        return JobStatus(job_id=job_id, status="planning", mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)) -> JobStatus:
    """Retrieves the current status and artifacts for a specific job.

    Args:
        job_id: The UUID of the job to retrieve.
        db: The asynchronous database session.

    Returns:
        JobStatus: Detailed state including plan, storyboard, 
        and video URL if available.

    Raises:
        HTTPException: If job is not found.
    """
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
    )


@app.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str,
    db_session_factory: Callable[[], AsyncSession] = Depends(lambda: AsyncSessionLocal),
) -> StreamingResponse:
    """Provides a real-time stream of job updates via SSE.

    Args:
        job_id: The UUID of the job to stream events for.
        db_session_factory: Factory for non-blocking DB sessions.

    Returns:
        StreamingResponse: An event-stream connection.
    """
    return StreamingResponse(
        _stream_job_events(job_id, db_session_factory), media_type="text/event-stream"
    )


@app.get("/jobs/{job_id}/plan", response_model=CurriculumPlan)
async def get_plan(job_id: str, db: AsyncSession = Depends(get_db)) -> CurriculumPlan:
    """Retrieves the generated curriculum plan for a specific job.

    Args:
        job_id: The UUID of the job.
        db: The asynchronous database session.

    Returns:
        CurriculumPlan: The parsed curriculum JSON.

    Raises:
        HTTPException: If job or plan is not found.
    """
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job or not job.plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return CurriculumPlan(**job.plan)


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(db: AsyncSession = Depends(get_db)) -> JobListResponse:
    """Lists all jobs sorted by creation date (newest first)."""
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
                )
            )
    except Exception as e:
        print(f"Error serialization job: {e}")
        raise HTTPException(status_code=500, detail=f"Serialization error: {e}") from e

    return JobListResponse(jobs=summary_list)


@app.post("/jobs/{job_id}/retry", response_model=JobStatus)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Retries a failed or stuck job from the last successful checkpoint."""
    # 1. Reset job state
    session_factory = getattr(app.state, "db_session_factory", AsyncSessionLocal)
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


@app.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a job and its associated data."""
    # Check if job exists
    result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete from DB
    await db.delete(job)
    await db.commit()
    return None


if _serving_spa:

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve SPA: static file if it exists, else index.html."""
        if full_path and not full_path.startswith(".."):
            candidate = (_FRONTEND_DIST_PATH / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(_FRONTEND_DIST_PATH):
                return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST_PATH / "index.html")
