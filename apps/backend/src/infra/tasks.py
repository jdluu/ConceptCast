"""Background task definitions for asynchronous video rendering and orchestration.

Utilizes taskiq for distributed task execution and long-running job processing.
"""

import asyncio
from typing import Any

import structlog
from sqlalchemy import select
from taskiq_redis import ListQueueBroker

from api.schemas import JobRequest, Storyboard
from infra.database import AsyncSessionLocal
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.jobs.manager import update_job_status
from services.jobs.thoughts import append_job_thought
from services.workflow.steps.rendering import RenderRepairRequiredError, step_rendering

logger = structlog.get_logger(__name__)

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

    async with AsyncSessionLocal() as session:
        lock = asyncio.Lock()

        async def update_job(updates: dict[str, Any]) -> None:
            """Helper to update the job record using the task's persistent session.

            Args:
                updates: A dictionary of field updates for the JobRecord.
            """
            async with lock:
                await update_job_status(job_id, updates, session)
                await session.commit()

        async def on_thought(agent: str, phase: str, content: str) -> None:
            """Callback to store agent thought deltas using the task's persistent session.

            Args:
                agent: The name of the agent generating the thought.
                phase: The current execution phase.
                content: The thought content to append.
            """
            async with lock:
                await append_job_thought(session, job_id, agent, phase, content)
                await session.commit()

        # Fetch job within the same session
        result = await session.execute(
            select(JobRecord).where(JobRecord.job_id == job_id)
        )
        job = result.scalar_one()

        try:
            await step_rendering(
                code=code,
                job_id=job_id,
                storyboard=storyboard,
                request=request,
                job=job,
                update_job=update_job,
                on_thought=on_thought,
            )
        except RenderRepairRequiredError as e:
            logger.error(
                "render_repair_required",
                job_id=job_id,
                exception_type=type(e).__name__,
                error_type=e.error_type,
                error=str(e),
            )
            details = f"{e.error_type}: {e}. Suggested action: {e.suggestion}"
            await update_job(
                {
                    "status": "awaiting_review",
                    "current_step": "rendering_failed_needs_fix",
                    "error": details,
                }
            )
            await on_thought(
                "system",
                "status",
                f"Rendering failed and paused for repair.\n{details}",
            )
        except Exception as e:
            logger.exception(
                "render_task_unexpected_failure",
                job_id=job_id,
                exception_type=type(e).__name__,
                error=str(e),
            )
            details = f"{type(e).__name__}: {e}"
            await update_job(
                {
                    "status": "awaiting_review",
                    "current_step": "rendering_failed_needs_fix",
                    "error": details,
                }
            )
            await on_thought(
                "system",
                "status",
                f"Rendering failed unexpectedly and paused for repair.\n{details}",
            )
