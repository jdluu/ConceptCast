from collections.abc import Callable
from typing import Any

from loguru import logger

from api.schemas import JobRequest, Storyboard
from domain.agents.animator import generate_manim_code
from infra.engines.video import mock_render_storyboard, render_storyboard
from infra.models.job import JobRecord
from infra.security.sanitizer import sanitize_manim_code
from services.workflow.base import get_step_model
from services.workflow.utils import calculate_job_cost


async def step_rendering(
    code: str,
    job_id: str,
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> None:
    """Executes the final Rendering step of the workflow.

    Triggers the video generation process using the validated Manim code.
    Includes a fallback/retry mechanism that provides specific error
    feedback to the animator if rendering fails due to common Manim API
    errors.

    Args:
        code: The validated Manim Python code to render.
        job_id: Unique identifier for the job (used for file paths).
        storyboard: The storyboard context (used if a retry is needed).
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        None

    Raises:
        RuntimeError: If rendering fails and cannot be recovered via retry.
    """
    await update_job({"status": "rendering", "current_step": "rendering"})
    try:
        # We always attempt a real render now, even in mock mode,
        # because the mock Manim code is actually valid.
        render_result = await render_storyboard(
            code,
            job_id,
            update_job=update_job,
            resolution=job.resolution,
            frame_rate=job.frame_rate,
        )

        total_cost = calculate_job_cost(
            render_duration=render_result.metadata.get("duration", 0)
            if render_result.metadata
            else 0
        )

        await update_job(
            {
                "video_url": render_result.video_url,
                "thumbnail_url": render_result.thumbnail_url,
                "video_metadata": render_result.metadata,
                "cost": total_cost,
                "status": "completed",
                "current_step": "rendering_complete",
            }
        )
    except RuntimeError as e:
        error_msg = str(e)
        if (
            "Rendering failed" in error_msg
            or "TypeError" in error_msg
            or "AttributeError" in error_msg
        ):
            logger.warning(
                f"Rendering failed, retrying animator with error feedback: {error_msg}"
            )
            anim_model = get_step_model(request, job)
            if anim_model:
                retry_code, retry_usage = await generate_manim_code(
                    storyboard,
                    model=anim_model,
                    on_thought=on_thought,
                    retry_hint=(
                        f"Rendering failed with error: {error_msg}. "
                        "Fix the Manim API usage - check parameter names and use "
                        ".set_*() methods for styling instead of constructor kwargs."
                    ),
                )
                retry_code = sanitize_manim_code(retry_code)
                await update_job(
                    {
                        "manim_code": retry_code,
                        "status": "rendering",
                        "current_step": "rendering_retry",
                    }
                )
                render_result = await render_storyboard(
                    retry_code,
                    job_id,
                    update_job=update_job,
                    resolution=job.resolution,
                    frame_rate=job.frame_rate,
                )

                duration = (
                    render_result.metadata.get("duration", 0)
                    if render_result.metadata
                    else 0
                )
                total_cost = calculate_job_cost(
                    usage=retry_usage, render_duration=duration
                )

                await update_job(
                    {
                        "video_url": render_result.video_url,
                        "thumbnail_url": render_result.thumbnail_url,
                        "video_metadata": render_result.metadata,
                        "cost": total_cost,
                        "status": "completed",
                        "current_step": "rendering_complete",
                    }
                )
            else:
                raise
        else:
            raise
