"""Background task definitions for asynchronous video rendering and orchestration.

Utilizes taskiq for distributed task execution and long-running job processing.
"""

from typing import Any

from sqlalchemy import select
from taskiq_redis import ListQueueBroker

from api.schemas import JobRequest, Storyboard
from infra.database import AsyncSessionLocal
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.manager import update_job_record
from services.jobs.thoughts import append_job_thought
from services.workflow.steps.rendering import step_rendering

settings = get_settings()

broker = ListQueueBroker(url=settings.redis_url)


@broker.task
async def render_video_task(
    job_id: str,
    code: str,
    storyboard_dict: dict[str, Any],
    request_dict: dict[str, Any],
) -> None:
    """Asynchronous background task to perform Manim rendering for a specific job.

    Args:
        job_id: Unique identifier for the job.
        code: The generated Manim Python code to render.
        storyboard_dict: Dictionary representation of the visual storyboard.
        request_dict: Dictionary representation of the original job request.
    """
    storyboard = Storyboard(**storyboard_dict)
    request = JobRequest(**request_dict)

    async def update_job(updates: dict[str, Any]) -> None:
        """Helper to update the job record within the background task."""
        await update_job_record(AsyncSessionLocal, job_id, updates)

    async def on_thought(agent: str, phase: str, content: str) -> None:
        """Callback to store agent thought deltas during background rendering."""
        await append_job_thought(AsyncSessionLocal, job_id, agent, phase, content)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(JobRecord).where(JobRecord.job_id == job_id))
        job = result.scalar_one()

    await step_rendering(
        code=code,
        job_id=job_id,
        storyboard=storyboard,
        request=request,
        job=job,
        update_job=update_job,
        on_thought=on_thought,
    )
