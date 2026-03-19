from collections.abc import Awaitable, Callable
from difflib import SequenceMatcher
from typing import Any

import structlog
from pydantic_ai.usage import RunUsage

from api.schemas import JobRequest, Storyboard
from domain.agents.animator import generate_manim_code
from domain.agents.reviewer import review_animation
from domain.models.workflow import GlobalContext
from infra.engines.video import render_preview
from infra.exceptions import AnimationGenerationError
from infra.models.job import JobRecord
from infra.security.sanitizer import sanitize_manim_code
from infra.settings import get_settings
from services.workflow.base import get_step_model

logger = structlog.get_logger(__name__)

MAX_MANIM_CODE_LINES = 600
MAX_MANIM_CODE_CHARS = 50000


def _looks_like_large_rewrite(old: str, new: str) -> bool:
    if not old.strip() or not new.strip():
        return False
    ratio = SequenceMatcher(a=old, b=new).ratio()
    # Heuristic: if similarity drops too low, the model likely rewrote
    # instead of applying a minimal patch.
    return ratio < 0.55


def _objective_animation_issues(code: str, storyboard: Storyboard) -> list[str]:
    issues: list[str] = []
    if "class SceneGen(Scene):" not in code:
        issues.append("Code must define class SceneGen(Scene).")
    if "def construct(self):" not in code:
        issues.append("Code must define construct(self).")
    play_calls = code.count("self.play(")
    if play_calls == 0:
        issues.append("Code must include at least one self.play(...) animation call.")

    # Lightweight scene-coverage heuristic: non-trivial storyboard should not map
    # to a single animation beat.
    if len(storyboard.scenes) >= 3 and play_calls < 2:
        issues.append(
            "Storyboard has multiple scenes but code has too few animation beats."
        )
    return issues


def _enforce_code_budget(code: str) -> None:
    line_count = len(code.splitlines())
    if line_count > MAX_MANIM_CODE_LINES:
        raise AnimationGenerationError(
            "Generated code exceeds line budget "
            f"({line_count} > {MAX_MANIM_CODE_LINES})."
        )
    if len(code) > MAX_MANIM_CODE_CHARS:
        raise AnimationGenerationError(
            "Generated code exceeds character budget "
            f"({len(code)} > {MAX_MANIM_CODE_CHARS})."
        )


async def step_animating(  # noqa: PLR0912, PLR0915
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, Any]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    initial_hint: str | None = None,
) -> tuple[str, RunUsage]:
    """Executes the AI-driven animation phase with iterative self-correction.

    Combines Manim code generation, sandboxed rendering, and automated visual
    review to ensure the final animation aligns with the storyboard and is
    syntactically correct.

    Args:
        storyboard: The visual architectural plan for the video.
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.
        ctx: The Global Context Object (GCO) for shared memory.

    Returns:
        tuple: (The final sanitized Manim code, Total RunUsage from the loop).

    Raises:
        AnimationGenerationError: If valid code cannot be generated or rendered
            within the iteration limit.
    """
    logger.info("animating_loop_started", mode=job.mode)

    model = get_step_model(request, job, agent_id="animator")
    if not model:
        raise AnimationGenerationError("Could not initialize animation model")

    current_code = ""
    total_usage = RunUsage()
    max_iterations = get_settings().animation_review_max_iterations
    hint = initial_hint
    previous_code = ""
    approved = False

    for i in range(max_iterations):
        logger.info(
            "animating_attempt_started",
            attempt=i + 1,
            max_iterations=max_iterations,
        )
        await update_job({"current_step": f"animating_attempt_{i + 1}"})

        try:
            # Keep latest known code in context so retries can patch in-place.
            if previous_code:
                ctx.manim_code = previous_code

            patch_prefix = (
                "PATCH MODE: Start from the current_manim_code in context. "
                "Apply the smallest possible edits to fix the reported failures. "
                "Do not rewrite unrelated scenes or transitions. "
            )
            effective_hint = f"{patch_prefix}{hint}" if hint else None
            current_code, usage = await generate_manim_code(
                storyboard,
                model,
                on_thought=on_thought,
                retry_hint=effective_hint,
                ctx=ctx,
            )
            total_usage.incr(usage)
            current_code = sanitize_manim_code(current_code)
            _enforce_code_budget(current_code)
            if previous_code and _looks_like_large_rewrite(previous_code, current_code):
                hint = (
                    "Your last output looks like a full rewrite. "
                    "PATCH MODE requires minimal targeted edits starting from current_manim_code. "
                    "Apply only the smallest diff needed to fix the latest failure."
                )
                await on_thought(
                    "system",
                    "Review",
                    "Rejected: output was a large rewrite; patch required.",
                )
                continue
            if previous_code and current_code == previous_code:
                hint = (
                    "The previous code output is identical to the prior attempt. "
                    "Apply concrete patch changes based on the latest failure details."
                )
                await on_thought("system", "Review", "Skipped duplicate code attempt.")
                continue
            previous_code = current_code

        except Exception as e:
            logger.warning(
                "animating_syntax_check_failed",
                error=str(e),
                attempt=i + 1,
            )
            ctx.add_error("animator", "syntax_check", e)
            hint = (
                f"Previous code had syntax errors: {e}. "
                "Patch only the syntax/API lines needed to pass parsing."
            )
            await on_thought("system", "Syntax Check", f"Failed: {e}")
            if i == max_iterations - 1:
                raise AnimationGenerationError(
                    f"Failed to generate valid code after {max_iterations} attempts"
                ) from e
            continue

        # Preview and Review
        preview_result = await render_preview(current_code, str(job.job_id))
        if not preview_result.success:
            logger.warning(
                "animating_preview_failed",
                error=preview_result.error,
                attempt=i + 1,
            )
            # Extract last few lines of logs for context
            log_tail = "\n".join(preview_result.logs.splitlines()[-10:])
            hint = (
                f"Animation failed to render: {preview_result.error}\nLogs:\n{log_tail}"
            )
            ctx.add_error(
                "animator",
                "preview_render",
                RuntimeError(preview_result.error or "Preview render failed."),
            )
            await on_thought(
                "system", "Preview", f"Failed: {preview_result.error}\n{log_tail}"
            )
            if i == max_iterations - 1:
                raise AnimationGenerationError(
                    f"Failed to render valid preview: {preview_result.error}"
                )
            continue

        review, r_usage = await review_animation(
            storyboard=storyboard,
            frame_path=preview_result.frame_path,
            execution_logs=preview_result.logs,
            model=model,
            on_thought=on_thought,
            ctx=ctx,
        )
        total_usage.incr(r_usage)

        if review.approved:
            objective_issues = _objective_animation_issues(current_code, storyboard)
            if objective_issues:
                hint = (
                    "Objective code checks failed. Apply a targeted patch to fix these issues: "
                    + "; ".join(objective_issues)
                )
                await on_thought("system", "Review", "\n".join(objective_issues))
                logger.warning(
                    "animating_objective_checks_failed_after_reviewer_approval",
                    objective_issues=objective_issues,
                    attempt=i + 1,
                )
                continue
            logger.info("animating_reviewer_approved", attempt=i + 1)
            await update_job({"manim_code": current_code})
            approved = True
            break

        logger.info(
            "animating_revision_requested",
            issues=review.issues,
            attempt=i + 1,
        )
        hint = (
            "Reviewer feedback indicates scene/code mismatch. "
            "Patch only the affected scenes/animations. "
            f"Reviewer instructions: {review.revision_instructions}"
        )
        if review.issues:
            ctx.add_error(
                "reviewer",
                "visual_review",
                RuntimeError("; ".join(review.issues)),
            )
        await on_thought("system", "Review", "\n".join(review.issues))

    if not approved:
        raise AnimationGenerationError(
            "Animation did not receive reviewer approval within retry budget."
        )

    return current_code, total_usage
