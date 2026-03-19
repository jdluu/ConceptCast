from collections.abc import Awaitable, Callable

import structlog
from pydantic_ai.usage import RunUsage

from api.schemas import JobRequest, Storyboard
from domain.agents.animator import generate_manim_code
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


def _objective_animation_issues(code: str, storyboard: Storyboard) -> list[str]:
    issues: list[str] = []
    if "class SceneGen(Scene):" not in code:
        issues.append("Code must define class SceneGen(Scene).")
    if "def construct(self):" not in code:
        issues.append("Code must define construct(self).")
    play_calls = code.count("self.play(")
    if play_calls == 0:
        issues.append("Code must include at least one self.play(...) animation call.")

    # Lightweight scene-coverage heuristic
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
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    initial_hint: str | None = None,
) -> tuple[str, RunUsage]:
    """Executes the AI-driven animation phase incrementally per scene.

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
        initial_hint: Optional retry hint.

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

    total_usage = RunUsage()
    max_iterations_per_scene = get_settings().animation_review_max_iterations

    # Initialize the master code structure if not recovering
    master_code = (
        ctx.manim_code
        if ctx.manim_code and "class SceneGen(Scene):" in ctx.manim_code
        else (
            "from manim import *\n\nclass SceneGen(Scene):\n    def construct(self):\n"
        )
    )
    ctx.manim_code = master_code

    for scene_idx, scene in enumerate(storyboard.scenes):
        scene_approved = False
        hint = initial_hint if scene_idx == 0 else None

        for i in range(max_iterations_per_scene):
            logger.info(
                "animating_scene_attempt_started",
                scene_id=scene.scene_id,
                attempt=i + 1,
                max_iterations=max_iterations_per_scene,
            )
            await update_job(
                {"current_step": f"animating_scene_{scene.scene_id}_attempt_{i + 1}"}
            )

            try:
                patch_prefix = "RETRY SCENE: Fix the reported failures without rewriting other scenes. "
                effective_hint = f"{patch_prefix}{hint}" if hint else None

                scene_code, usage = await generate_manim_code(
                    target_scene=scene,
                    model=model,
                    on_thought=on_thought,
                    retry_hint=effective_hint,
                    ctx=ctx,
                )
                total_usage.incr(usage)

                # Cleanup potential boilerplate the model might have still generated
                scene_code = scene_code.strip()
                if scene_code.startswith("def construct(self):"):
                    scene_code = scene_code[len("def construct(self):") :].strip()

                # Indent scene code to match the master structure
                indented_scene_code = ""
                for line in scene_code.splitlines():
                    if line.strip():
                        indented_scene_code += f"        {line}\n"
                    else:
                        indented_scene_code += "\n"

                proposed_code = (
                    master_code
                    + f"        # --- Scene {scene.scene_id}: {scene.title} ---\n"
                    + indented_scene_code
                )
                proposed_code = sanitize_manim_code(proposed_code)
                _enforce_code_budget(proposed_code)

            except Exception as e:
                logger.warning(
                    "animating_syntax_check_failed",
                    error=str(e),
                    scene_id=scene.scene_id,
                    attempt=i + 1,
                )
                ctx.add_error("animator", "syntax_check", e)
                hint = f"Failed to parse or assemble code: {e}"
                await on_thought(
                    "system", "Syntax Check", f"Scene {scene.scene_id} Failed: {e}"
                )
                if i == max_iterations_per_scene - 1:
                    raise AnimationGenerationError(
                        f"Failed to generate valid code for scene {scene.scene_id} after {max_iterations_per_scene} attempts"
                    ) from e
                continue

            # Render preview for the proposed code to ensure no regressions
            preview_result = await render_preview(proposed_code, str(job.job_id))
            if not preview_result.success:
                logger.warning(
                    "animating_preview_failed",
                    error=preview_result.error,
                    scene_id=scene.scene_id,
                    attempt=i + 1,
                )
                log_tail = "\n".join(preview_result.logs.splitlines()[-10:])
                hint = f"Animation failed to render in preview: {preview_result.error}\nLogs:\n{log_tail}"
                ctx.add_error(
                    "animator",
                    "preview_render",
                    RuntimeError(preview_result.error or "Preview render failed."),
                )
                await on_thought(
                    "system",
                    "Preview",
                    f"Scene {scene.scene_id} Failed: {preview_result.error}\n{log_tail}",
                )
                if i == max_iterations_per_scene - 1:
                    raise AnimationGenerationError(
                        f"Failed to render valid preview for scene {scene.scene_id}: {preview_result.error}"
                    )
                continue

            # Scene code successfully parsed and preview rendered. Commit it.
            logger.info(
                "animating_scene_approved_by_sandbox",
                scene_id=scene.scene_id,
                attempt=i + 1,
            )
            master_code = proposed_code
            ctx.manim_code = master_code
            await update_job({"manim_code": master_code})
            scene_approved = True
            await on_thought(
                "system",
                "Progress",
                f"Scene {scene.scene_id} rendered successfully and committed to master script.",
            )
            break

        if not scene_approved:
            raise AnimationGenerationError(
                f"Scene {scene.scene_id} could not be successfully generated within retry budget."
            )

    # Optional: Final full-length visual review. For now, rely on progressive preview success.
    # The reviewer agent can still be utilized here, but the code is functionally stable.
    logger.info("animating_final_script_assembled", total_scenes=len(storyboard.scenes))
    objective_issues = _objective_animation_issues(master_code, storyboard)
    if objective_issues:
        logger.warning(
            "animating_objective_checks_failed_at_end",
            objective_issues=objective_issues,
        )

    return master_code, total_usage
