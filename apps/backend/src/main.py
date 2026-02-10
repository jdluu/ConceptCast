import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from agents.factory import AVAILABLE_MODELS
from database import JobRecord, SessionLocal, get_db, init_db
from schemas import (
    AvailableModelsResponse,
    CurriculumPlan,
    JobRequest,
    JobStatus,
    ProviderModels,
)
from service import create_new_job, process_job_logic

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    init_db()
    app.state.db_session_factory = SessionLocal
    yield


app = FastAPI(title="ConceptCast Backend", lifespan=lifespan)

# Job Artifact Storage (Persistent - defined here, mounted at end)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)


@app.get("/models/available", response_model=AvailableModelsResponse)
async def get_available_models():
    """
    Returns the list of available AI providers and their models.
    """
    result = []
    for provider, models in AVAILABLE_MODELS.items():
        # Check if API key is present for this provider
        key_map = {
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "synthetic": "SYNTHETIC_API_KEY",
        }
        if os.getenv(key_map.get(provider, "")):
            result.append(ProviderModels(provider=provider, models=models))

    # Always include mock if not already present
    if not any(p.provider == "mock" for p in result):
        result.append(ProviderModels(provider="mock", models=AVAILABLE_MODELS["mock"]))

    return AvailableModelsResponse(available=result)


@app.get("/")
async def read_root():
    return {"message": "Welcome to ConceptCast Council"}


@app.post("/jobs/create", response_model=JobStatus)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new ConceptCast job and trigger orchestration in the background.
    """
    try:
        job_id = await create_new_job(db, request)

        # Use the session factory from app state
        session_factory = getattr(app.state, "db_session_factory", SessionLocal)
        background_tasks.add_task(process_job_logic, job_id, request, session_factory)

        return JobStatus(job_id=job_id, status="planning")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieve current status and artifacts for a job.
    """
    job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        plan=job.plan_data,
        validation=job.validation_data,
        storyboard=job.storyboard_data,
        manim_code=job.manim_code,
        video_url=job.video_url,
        error=job.error,
        mode=job.mode,
    )


@app.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str, db_session_factory: SessionLocal = Depends(lambda: SessionLocal)
):
    """
    Server-Sent Events stream for real-time job status updates.
    """

    async def event_generator():
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
                        "plan": job.plan_data,
                        "validation": job.validation_data,
                        "storyboard": job.storyboard_data,
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

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/jobs/{job_id}/plan", response_model=CurriculumPlan)
async def get_plan(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the generated curriculum plan for a job.
    """
    job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
    if not job or not job.plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    return CurriculumPlan(**job.plan_data)


app.mount("/jobs", StaticFiles(directory=str(JOBS_ROOT)), name="jobs")
