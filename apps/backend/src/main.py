import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from agents.factory import AVAILABLE_MODELS
from api.schemas import (
    AvailableModelsResponse,
    CurriculumPlan,
    JobRequest,
    JobStatus,
    ProviderModels,
)
from core.database import JobRecord, SessionLocal, get_db, init_db
from core.settings import get_settings
from services.orchestrator import create_new_job, process_job_logic


async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], Session]
) -> AsyncGenerator[str, None]:
    """
    Generates SSE events for a specific job by polling the database.

    Args:
        job_id (str): The job ID to monitor.
        db_session_factory (Callable): Factory for DB sessions.

    Yields:
        str: SSE formatted string.
    """
    last_status = None
    last_updated = None

    while True:
        with db_session_factory() as db:
            job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
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


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the application lifecycle.

    Initializes the database connection and session factory on startup.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    init_db()
    app.state.db_session_factory = SessionLocal
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
# Defined here relative to the project root and mounted as a static directory.
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)


@app.get("/models/available", response_model=AvailableModelsResponse)
async def get_available_models() -> AvailableModelsResponse:
    """
    Retrieves the list of supported AI providers and their models.

    Filters providers based on the presence of their respective API keys
    in the environment. The mock provider is always included.

    Returns:
        AvailableModelsResponse: A list of available providers and their models.
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
    """
    Root endpoint for health checking and welcoming.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to ConceptCast Council"}


@app.post("/jobs/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    db_session_factory: Callable[[], Session] = Depends(lambda: SessionLocal),
) -> JobStatus:
    """
    Initializes a new video generation job.

    Creates a database record and queues the orchestration logic for
    asynchronous background execution.

    Args:
        request (JobRequest): Job parameters (topic, audience, model).
        db_session_factory (Callable[[], Session]): Factory for creating database
            sessions.

    Returns:
        JobStatus: The initial status of the created job.

    Raises:
        HTTPException: If job initialization fails.
    """
    try:
        with db_session_factory() as db:
            job_id = await create_new_job(db, request)

        # Use the session factory from app state
        session_factory = getattr(app.state, "db_session_factory", SessionLocal)
        background_tasks.add_task(process_job_logic, job_id, request, session_factory)

        return JobStatus(job_id=job_id, status="planning", mode="live")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatus:
    """
    Retrieves the current state and all generated artifacts for a specific job.

    Args:
        job_id (str): The unique identifier of the job.
        db (Session): Database session.

    Returns:
        JobStatus: Comprehensive job state including plan, storyboard, and video URL.

    Raises:
        HTTPException: If the job is not found.
    """
    job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
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
    db_session_factory: Callable[[], Session] = Depends(lambda: SessionLocal),
) -> StreamingResponse:
    """
    Provides a real-time stream of job status updates via Server-Sent Events (SSE).

    Polls the database and emits updates only when the job state or
    timestamp changes. The stream terminates upon job completion or failure.

    Args:
        job_id (str): The unique identifier of the job to monitor.
        db_session_factory (Callable[[], Session]): Factory for creating database
            sessions.

    Returns:
        StreamingResponse: An SSE stream of job status objects.
    """

    return StreamingResponse(
        _stream_job_events(job_id, db_session_factory), media_type="text/event-stream"
    )


@app.get("/jobs/{job_id}/plan", response_model=CurriculumPlan)
async def get_plan(job_id: str, db: Session = Depends(get_db)) -> CurriculumPlan:
    """
    Retrieves the generated curriculum plan for a specific job.

    Args:
        job_id (str): The unique identifier of the job.
        db (Session): Database session.

    Returns:
        CurriculumPlan: The structured pedagogical plan.

    Raises:
        HTTPException: If the job or plan is not found.
    """
    job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
    if not job or not job.plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return CurriculumPlan(**job.plan)


app.mount("/jobs", StaticFiles(directory=str(JOBS_ROOT)), name="jobs")
