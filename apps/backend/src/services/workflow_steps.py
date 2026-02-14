import json
from collections.abc import Callable
from typing import Any

from loguru import logger

from agents.analyst import generate_curriculum
from agents.animator import generate_manim_code
from agents.architect import generate_storyboard
from agents.factory import get_model
from agents.reviewer import review_animation
from api.schemas import CurriculumPlan, JobRequest, Storyboard
from core.database import JobRecord
from core.exceptions import (
    AnimationGenerationError,
    PlanGenerationError,
    StoryboardGenerationError,
)
from core.settings import get_settings
from services.rendering import (
    extract_and_validate_manim_code,
    render_preview,
    render_storyboard,
)


async def step_planning(
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> CurriculumPlan:
    """Executes the Planning step of the lesson generation workflow.

    This step generates a curriculum plan based on the user's topic and 
    target audience. It handles checkpointing by returning an existing plan 
     if one is already associated with the job.

    Args:
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        CurriculumPlan: The generated or retrieved curriculum.

    Raises:
        PlanGenerationError: If the AI provider fails to produce a plan.
    """
    if not job.plan:
        logger.info(f"Generating curriculum for: {request.topic} (Mode: {job.mode})")

        provider_arg = (
            "mock"
            if job.mode == "mock"
            else (getattr(job, "provider", None) or request.provider)
        )
        model_arg = getattr(job, "model_id", None) or request.model_id

        plan_model = get_model(
            provider_name=provider_arg,
            model_id=model_arg,
        )

        if not plan_model:
            raise PlanGenerationError(
                f"Could not initialize model for provider '{provider_arg}' and "
                f"model_id '{model_arg}'. Ensure API keys are configured."
            )

        plan = await generate_curriculum(
            topic=request.topic,
            audience=request.target_audience,
            model=plan_model,
            on_thought=on_thought,
        )

        job.plan = plan.model_dump()
        job.current_step = "planning_complete"
        await update_job(
            {
                "plan": job.plan,
                "current_step": job.current_step,
                "status": "validating",
            }
        )
        logger.success("Step 1: Planning - Complete")
    else:
        logger.info("Using existing curriculum plan (Checkpoint)")
        if isinstance(job.plan, dict):
            plan = CurriculumPlan(**job.plan)
        else:
            plan = CurriculumPlan(**json.loads(job.plan))
    return plan


async def step_architecting(
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> Storyboard:
    """Executes the Architecting step of the lesson generation workflow.

    Translates the pedagogical curriculum plan into a visual storyboard 
    consisting of scenes, descriptions, and visual metaphors.

    Args:
        plan: The curriculum plan generated in the previous step.
        request: The initial job request parameters.
        job: The current job record from the database.
        update_job: Async callback to persist state changes to the database.
        on_thought: Callback to stream agent internal reasoning to the frontend.

    Returns:
        Storyboard: The generated or retrieved visual storyboard.

    Raises:
        StoryboardGenerationError: If the AI provider fails to produce a storyboard.
    """
    if not job.storyboard:
        logger.info("Generating storyboard...")
        provider_arg = (
            "mock"
            if job.mode == "mock"
            else (getattr(job, "provider", None) or request.provider)
        )
        model_arg = getattr(job, "model_id", None) or request.model_id
        arch_model = get_model(
            provider_name=provider_arg,
            model_id=model_arg,
        )

        if not arch_model:
            raise StoryboardGenerationError(
                f"Could not initialize model for provider '{provider_arg}' and "
                f"model_id '{model_arg}'. Ensure API keys are configured."
            )

        storyboard = await generate_storyboard(
            plan=plan,
            model=arch_model,
            on_thought=on_thought,
        )
        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        await update_job(
            {"storyboard": job.storyboard, "current_step": job.current_step}
        )
        logger.success("Step 3: Architecting - Complete")
    else:
        logger.info("Using existing storyboard (Checkpoint)")
        if isinstance(job.storyboard, dict):
            storyboard = Storyboard(**job.storyboard)
        else:
            storyboard = Storyboard(**json.loads(job.storyboard))
    return storyboard


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
        video_url = await render_storyboard(code, job_id)
        await update_job(
            {
                "video_url": video_url,
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
            provider_arg = (
                "mock"
                if job.mode == "mock"
                else (getattr(job, "provider", None) or request.provider)
            )
            model_arg = getattr(job, "model_id", None) or request.model_id
            anim_model = get_model(provider_name=provider_arg, model_id=model_arg)
            if anim_model:
                retry_code = await generate_manim_code(
                    storyboard,
                    model=anim_model,
                    on_thought=on_thought,
                    retry_hint=(
                        f"Rendering failed with error: {error_msg}. "
                        "Fix the Manim API usage - check parameter names and use "
                        ".set_*() methods for styling instead of constructor kwargs."
                    ),
                )
                retry_code = extract_and_validate_manim_code(retry_code)
                await update_job(
                    {
                        "manim_code": retry_code,
                        "status": "rendering",
                        "current_step": "rendering_retry",
                    }
                )
                video_url = await render_storyboard(retry_code, job_id)
                await update_job(
                    {
                        "video_url": video_url,
                        "status": "completed",
                        "current_step": "rendering_complete",
                    }
                )
            else:
                raise
        else:
            raise
