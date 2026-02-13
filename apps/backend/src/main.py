import asyncio
import json
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.factory import AVAILABLE_MODELS
from api.schemas import (
    AvailableModelsResponse,
    CurriculumPlan,
    JobRequest,
    JobStatus,
    ProviderModels,
)
from core.database import AsyncSessionLocal, JobRecord, get_db, init_db
from core.settings import get_settings
from services.orchestrator import process_job_logic


async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database.

    Args:
        job_id: The unique identifier of the job to monitor.
        db_session_factory: A factory function that returns an AsyncSession for non-blocking polls.

    Yields:
        str: An SSE-formatted string containing the job status and artifacts in JSON format.
    """
    last_status = None
    last_updated = None

    while True:
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord).where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            # Only stream if status or update time has changed
            if job.status != last_status or job.updated_at != last_updated:
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
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_status = job.status
                last_updated = job.updated_at

            if job.status in ["completed", "failed"]:
                break

        await asyncio.sleep(1)  # Internal poll for DB changes





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

# Job Artifact Storage Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/jobs/artifacts", StaticFiles(directory=str(JOBS_ROOT)), name="job_artifacts"
)


@app.get("/models/available", response_model=AvailableModelsResponse)
async def get_available_models() -> AvailableModelsResponse:
    """Retrieves the list of supported AI providers and their models.

    Checks configured API keys to filter which providers (Google, Groq, DeepSeek, etc.)
    are available for the current environment. Always includes 'mock' mode.

    Returns:
        AvailableModelsResponse: A list of providers and their associated model IDs.
    """
    result = []
    settings = get_settings()
    key_map = {
        "google": settings.google_api_key,
        "groq": settings.groq_api_key,
        "deepseek": settings.deepseek_api_key,
        "synthetic": settings.synthetic_api_key,
    }
    for provider, models in AVAILABLE_MODELS.items():
        if key_map.get(provider):
            result.append(ProviderModels(provider=provider, models=models))

    # Always include mock if not already present
    if not any(p.provider == "mock" for p in result):
        result.append(ProviderModels(provider="mock", models=AVAILABLE_MODELS["mock"]))

    return AvailableModelsResponse(available=result)


@app.get("/")
async def read_root() -> dict[str, str]:
    """Root health-check endpoint.

    Returns:
        dict: A welcome message if the server is running correctly.
    """
    return {"message": "Welcome to ConceptCast Council"}


@app.post("/jobs/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Initializes a new asynchronous video generation job.

    Creates a job record in the database and triggers the background processing workflow.

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
            mode=mode
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
        JobStatus: Detailed state including plan, storyboard, and video URL if available.

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
