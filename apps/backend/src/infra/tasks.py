import os
from typing import Any
from taskiq import AsyncBroker
from taskiq_redis import ListQueueBroker
from infra.settings import get_settings
from infra.database import AsyncSessionLocal

settings = get_settings()

broker = ListQueueBroker(
    url=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6374"
)

@broker.task
async def render_video_task(
    job_id: str,
    code: str,
    storyboard_dict: dict[str, Any],
    request_dict: dict[str, Any],
    resolution: str,
    frame_rate: int,
) -> None:
    """Background task to perform Manim rendering."""
    from api.schemas import JobRequest, Storyboard
    from services.workflow.steps.rendering import step_rendering
    from services.jobs.manager import update_job_record
    
    # Reconstruct objects
    storyboard = Storyboard(**storyboard_dict)
    request = JobRequest(**request_dict)
    
    async def update_job(updates: dict[str, Any]) -> None:
        await update_job_record(AsyncSessionLocal, job_id, updates)
        
    async def on_thought(agent: str, phase: str, content: str) -> None:
        # In a background task, we might want to log thoughts differently 
        # or just append them to the job record.
        from services.jobs.manager import append_job_thought
        await append_job_thought(AsyncSessionLocal, job_id, agent, phase, content)

    # We need a job record dummy or fetch it
    from sqlalchemy import select
    from infra.models.job import JobRecord
    
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
