import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

from agents.analyst import generate_curriculum  # noqa: E402
from schemas import CurriculumPlan, JobStatus  # noqa: E402
from utils import generate_mock_plan  # noqa: E402

app = FastAPI(title="ConceptCast Backend")

jobs = {}


class JobRequest(BaseModel):
    """
    Request model for creating a new ConceptCast job.
    """

    topic: str
    target_audience: str = "Undergraduate CS"


@app.get("/")
def read_root():
    """
    Root endpoint to verify API availability.
    """
    return {"message": "Welcome to ConceptCast Council"}


@app.post("/jobs/create", response_model=JobStatus)
async def create_job(request: JobRequest):
    """
    Create a new ConceptCast job for a given topic.

    Triggers the Analyst Agent to generate a curriculum plan.
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {"status": "planning", "request": request.model_dump(), "plan": None}

    api_key = os.getenv("GOOGLE_API_KEY")
    use_mock = not api_key or api_key == "dummy_key_for_development"

    if use_mock:
        print("No valid API Key set. Using mock plan.")
        mock_plan = generate_mock_plan(request.topic, request.target_audience)
        jobs[job_id]["plan"] = mock_plan
        jobs[job_id]["status"] = "reviewing"
        jobs[job_id]["mode"] = "mock"
    else:
        try:
            plan = await generate_curriculum(request.topic, request.target_audience)
            jobs[job_id]["plan"] = plan
            jobs[job_id]["status"] = "reviewing"
            jobs[job_id]["mode"] = "live"
        except Exception as e:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
            raise HTTPException(status_code=500, detail=str(e))

    return JobStatus(job_id=job_id, status=jobs[job_id]["status"])


@app.get("/jobs/{job_id}/plan", response_model=CurriculumPlan)
def get_job_plan(job_id: str):
    """
    Retrieve the generated curriculum plan for a specific job.

    Raises:
        HTTPException: If the job is not found or the plan is not ready.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    plan = jobs[job_id].get("plan")
    if not plan:
        raise HTTPException(status_code=400, detail="Plan not ready")

    return plan


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
def get_job_status(job_id: str):
    """
    Retrieve the current status of a specific job.

    Raises:
        HTTPException: If the job is not found.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(job_id=job_id, status=jobs[job_id]["status"])
