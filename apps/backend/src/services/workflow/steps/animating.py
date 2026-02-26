from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai.usage import RunUsage

from api.schemas import JobRequest, Storyboard
from domain.agents.animator import generate_manim_code
from domain.agents.reviewer import review_animation
from infra.engines.video import mock_render_preview, render_preview
from infra.exceptions import AnimationGenerationError
from infra.models.job import JobRecord
from infra.security.sanitizer import sanitize_manim_code


async def step_animating(
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
) -> tuple[str, RunUsage]:
    """Executes the Animating step with iterative self-correction."""
    logger.info(f"Starting animation generation loop (Mode: {job.mode})")

    from services.workflow.base import get_step_model

    model = get_step_model(request, job)
    if not model:
        raise AnimationGenerationError("Could not initialize animation model")

    current_code = ""
    total_usage = RunUsage()
    max_iterations = 3
    hint = None

    for i in range(max_iterations):
        logger.info(f"Generation attempt {i + 1}/{max_iterations}")

        try:
            current_code, usage = await generate_manim_code(
                storyboard, model, on_thought=on_thought, retry_hint=hint
            )
            total_usage.incr(usage)
            sanitize_manim_code(current_code)

        except Exception as e:
            logger.warning(f"Animation generation failed syntax check: {e}")
            hint = f"Previous code had syntax errors: {e}. Fix them."
            await on_thought("system", "Syntax Check", f"Failed: {e}")
            if i == max_iterations - 1:
                raise AnimationGenerationError(
                    f"Failed to generate valid code after {max_iterations} attempts"
                ) from e
            continue

        # Preview and Review
        if job.mode == "mock":
            preview_result = await mock_render_preview()
        else:
            preview_result = await render_preview(current_code, str(job.job_id))
        if not preview_result.success:
            logger.warning(f"Preview failed: {preview_result.error}")
            hint = f"Animation failed to render: {preview_result.error}"
            await on_thought("system", "Preview", f"Failed: {preview_result.error}")
            if i == max_iterations - 1:
                raise AnimationGenerationError("Failed to render valid preview")
            continue

        review, r_usage = await review_animation(
            storyboard=storyboard,
            frame_path=preview_result.frame_path,
            execution_logs=preview_result.logs,
            model=model,
            on_thought=on_thought,
        )
        total_usage.incr(r_usage)

        if review.approved:
            logger.success("Animation approved by Reviewer")
            break

        logger.info(f"Revision requested: {review.issues}")
        hint = f"Reviewer feedback: {review.revision_instructions}"
        await on_thought("system", "Review", "\n".join(review.issues))

    return current_code, total_usage
