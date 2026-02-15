from collections.abc import Callable
from typing import Any

from loguru import logger

from agents.animator import generate_manim_code
from agents.factory import get_model
from agents.reviewer import review_animation
from api.schemas import JobRequest, Storyboard
from core.database import JobRecord
from core.exceptions import AnimationGenerationError
from core.settings import get_settings
from services.rendering import (
    extract_and_validate_manim_code,
    render_preview,
)


async def step_animating(
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> str:
    """Executes the Animating step with an iterative review and repair loop.

    Generates Manim Python code based on the storyboard and performs
    automated review and self-correction iterations to ensure code correctness.

    Args:
        storyboard: The visual storyboard to animate.
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        str: The final validated Manim Python code.

    Raises:
        AnimationGenerationError: If valid code cannot be produced within
            the maximum allowed iterations.
    """
    settings = get_settings()
    provider_arg = getattr(job, "provider", None) or request.provider
    model_arg = getattr(job, "model_id", None) or request.model_id
    model = get_model(provider_arg, model_arg)

    max_iterations = settings.animation_review_max_iterations
    review_enabled = settings.animation_review_enabled

    current_code = job.manim_code or ""
    revision_instructions: str | None = None

    for i in range(max_iterations):
        iteration_label = f"{i + 1}/{max_iterations}"
        job.current_step = f"animating_iter_{i + 1}"
        await update_job({"current_step": job.current_step})

        phase_name = "Animation Generation" if i == 0 else "Animation Revision"
        await on_thought(
            "animator",
            phase_name,
            f"Generating Manim code (Iteration {iteration_label})...",
        )

        try:
            hint = revision_instructions if i > 0 else None
            current_code = await generate_manim_code(
                storyboard, model, on_thought=on_thought, retry_hint=hint
            )
            extract_and_validate_manim_code(current_code)

        except Exception as e:
            logger.warning(f"Animation generation failed syntax check: {e}")
            revision_instructions = f"Previous code had syntax errors: {e}. Fix them."
            await on_thought("system", "Syntax Check", f"Failed: {e}")
            if i == max_iterations - 1:
                raise AnimationGenerationError(
                    f"Failed to generate valid code after {max_iterations} "
                    f"attempts: {e}"
                ) from e
            continue

        if not review_enabled:
            logger.info("Animation review disabled. Accepting first draft.")
            break

        job.current_step = f"animating_preview_{i + 1}"
        await update_job({"current_step": job.current_step})
        await on_thought(
            "system",
            "Preview Rendering",
            f"Rendering preview for review ({iteration_label})...",
        )

        preview_result = await render_preview(current_code, job.job_id)

        if not preview_result.success:
            logger.warning(f"Preview rendering failed: {preview_result.error}")
            revision_instructions = (
                "The code failed to render. Fix these errors:\n\n"
                f"{preview_result.logs}\n\n"
                f"Error: {preview_result.error}"
            )
            await on_thought(
                "system", "Preview Failed", f"Error: {preview_result.error}"
            )

            if i == max_iterations - 1:
                raise AnimationGenerationError(
                    f"Failed to render valid animation after {max_iterations} attempts."
                )
            continue

        job.current_step = f"animating_review_{i + 1}"
        await update_job({"current_step": job.current_step})
        await on_thought(
            "reviewer",
            "Visual QA",
            f"Reviewing animation correctness ({iteration_label})...",
        )

        review = await review_animation(
            storyboard=storyboard,
            frame_path=preview_result.frame_path,
            execution_logs=preview_result.logs,
            model=model,
            on_thought=on_thought,
        )

        if review.approved:
            await on_thought(
                "reviewer",
                "Visual QA",
                "Animation approved! Proceeding to final render.",
            )
            break
        else:
            issues_str = "\n- ".join(review.issues)
            await on_thought(
                "reviewer", "Visual QA", f"Changes requested:\n- {issues_str}"
            )
            revision_instructions = (
                f"The previous animation was rejected by the reviewer.\n"
                f"Issues found:\n- {issues_str}\n\n"
                f"Instructions: {review.revision_instructions}"
            )

            if i == max_iterations - 1:
                logger.warning(
                    "Max iterations reached. Proceeding with best effort "
                    "despite review failure."
                )
                await on_thought(
                    "system",
                    "Timeout",
                    "Max iterations reached. Using current version.",
                )
                break

    await update_job({"manim_code": current_code, "current_step": "animating_complete"})
    return current_code
