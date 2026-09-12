from collections.abc import Awaitable, Callable
from difflib import SequenceMatcher

from api.schemas import JobRequest, Storyboard
from domain.agents.animator import generate_manim_code
from domain.models.workflow import GlobalContext
from infra.engines.video import render_preview, render_storyboard
from infra.models.job import JobRecord
from infra.security.sanitizer import sanitize_manim_code
from infra.settings import get_settings
from services.workflow.base import get_step_model
from services.workflow.utils import (
    apply_search_replace_patch,
    calculate_job_cost,
    merge_usage,
)


class RenderRepairRequiredError(RuntimeError):
    """Raised when rendering fails and requires manual/agent code repair."""

    def __init__(
        self,
        message: str,
        *,
        suggestion: str,
        error_type: str,
        logs: str | None = None,
    ) -> None:
        super().__init__(message)
        self.suggestion = suggestion
        self.error_type = error_type
        self.logs = logs


def _is_recoverable_render_error(message: str) -> bool:
    lower = message.lower()
    return any(
        token in lower
        for token in (
            "rendering failed",
            "typeerror",
            "attributeerror",
            "python syntax error",
            "indentationerror",
            "syntaxerror",
        )
    )


def _render_error_hint(message: str, logs: str | None = None) -> str:
    log_tail = ""
    if logs:
        tail_lines = logs.splitlines()[-12:]
        if tail_lines:
            log_tail = "\n".join(tail_lines)
    if log_tail:
        return f"{message}\nRecent logs:\n{log_tail}"
    return message


def _looks_like_large_rewrite(old: str, new: str) -> bool:
    if not old.strip() or not new.strip():
        return False
    ratio = SequenceMatcher(a=old, b=new).ratio()
    return ratio < 0.35


async def step_rendering(
    code: str,
    job_id: str,
    storyboard: Storyboard,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
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
    await update_job({"status": "rendering", "current_step": "rendering_start"})

    current_code = sanitize_manim_code(code)
    await update_job({"manim_code": current_code})

    # Trigger a fast preview to give immediate visual feedback
    try:
        await on_thought("system", "status", "Generating quick visual preview...")
        preview = await render_preview(current_code, job_id)
        if preview.success and preview.frame_path:
            await update_job(
                {"preview_url": f"/jobs/artifacts/{job_id}/preview_frame.png"}
            )
            await on_thought("system", "status", "Visual preview ready.")
    except Exception as e:
        import structlog

        structlog.get_logger(__name__).debug(
            "automatic_preview_failed", job_id=job_id, error=str(e)
        )

    await update_job({"status": "rendering", "current_step": "rendering_full"})

    max_repair_attempts = get_settings().render_repair_max_attempts
    repair_attempt = 0
    total_usage = None

    while True:
        try:
            # We always attempt a real render now, even in mock mode,
            # because the mock Manim code is actually valid.
            render_result = await render_storyboard(
                current_code,
                job_id,
                update_job=update_job,
                resolution="1080p",
                frame_rate=60,
            )

            raw_duration = (
                render_result.metadata.get("duration", 0.0)
                if render_result.metadata
                else 0.0
            )
            render_duration = (
                float(raw_duration) if isinstance(raw_duration, int | float) else 0.0
            )

            total_cost = calculate_job_cost(
                usage=total_usage,
                render_duration=render_duration,
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
            return
        except Exception as e:
            error_msg = str(e)
            logs = getattr(e, "logs", None)

            if not _is_recoverable_render_error(error_msg):
                raise RenderRepairRequiredError(
                    f"Unrecoverable rendering error: {error_msg}",
                    suggestion=(
                        "Inspect sanitization/preview logs and regenerate working "
                        "Manim code before rendering again."
                    ),
                    error_type=type(e).__name__,
                    logs=logs,
                ) from e

            if repair_attempt >= max_repair_attempts:
                raise RenderRepairRequiredError(
                    f"Render repair attempts exhausted. Last error: {error_msg}",
                    suggestion=(
                        "Patch failed repeatedly. Pause for review, then retry with "
                        "more targeted API/syntax fixes."
                    ),
                    error_type=type(e).__name__,
                    logs=logs,
                ) from e

            repair_attempt += 1
            await on_thought(
                "system",
                "status",
                (
                    "Rendering failed; routing back to animator for targeted patch "
                    f"(attempt {repair_attempt}/{max_repair_attempts})."
                ),
            )

            anim_model = get_step_model(request, job, agent_id="animator")
            if not anim_model:
                raise RenderRepairRequiredError(
                    f"Rendering failed and no animator model available: {error_msg}",
                    suggestion=(
                        "Regenerate Manim code with targeted syntax/API fixes, "
                        "then retry rendering."
                    ),
                    error_type=type(e).__name__,
                    logs=logs,
                ) from e

            retry_ctx = GlobalContext(
                topic=request.topic,
                storyboard=storyboard,
                manim_code=current_code,
            )
            retry_hint = (
                "Fix the rendering error in the code. Focus ONLY on correcting the problematic sections. "
                "You MUST output your edits as one or more SEARCH/REPLACE blocks using this format:\n"
                "<<<<<<< SEARCH\n"
                "[exact lines of original code to replace]\n"
                "=======\n"
                "[corrected lines of code]\n"
                ">>>>>>> REPLACE\n\n"
                f"Error details: {_render_error_hint(error_msg, logs)}"
            )
            retry_code, retry_usage = await generate_manim_code(
                storyboard,
                model=anim_model,
                on_thought=on_thought,
                ctx=retry_ctx,
                retry_hint=retry_hint,
            )
            total_usage = merge_usage(total_usage, retry_usage)

            patched_code = apply_search_replace_patch(current_code, retry_code)
            current_code = sanitize_manim_code(patched_code)
            await update_job(
                {
                    "manim_code": current_code,
                    "status": "animating",
                    "current_step": f"rendering_repair_attempt_{repair_attempt}",
                    "error": None,
                }
            )
            await update_job(
                {
                    "status": "rendering",
                    "current_step": f"rendering_retry_{repair_attempt}",
                }
            )
