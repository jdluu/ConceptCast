import asyncio
from collections.abc import Awaitable, Callable

import structlog
from pydantic_ai.usage import RunUsage, UsageLimits

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.agents.architect import generate_storyboard
from domain.models.workflow import GlobalContext
from infra.exceptions import StoryboardGenerationError
from infra.models.job import JobRecord
from infra.settings import get_settings
from services.workflow.base import get_step_model
from services.workflow.utils import parse_job_artifact

logger = structlog.get_logger(__name__)


def _is_placeholder_text(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"", "__missing__", "missing", "tbd", "n/a", "..."}


def _build_deterministic_storyboard(plan: CurriculumPlan) -> Storyboard:
    """Builds a fallback storyboard when the architect agent fails.

    Uses pedagogically meaningful visual patterns (axes, charts, groups)
    instead of cycling through basic shapes, producing a minimally
    interesting storyboard even in the worst case.
    """
    from api.schemas import Scene, VisualObject

    scenes: list[Scene] = []
    visual_patterns = [
        ("Title", "Text", "ORIGIN", "WHITE", {"font_size": 48}),
        ("Axes", "Axes", "ORIGIN", "BLUE", {"x_range": [-3, 3], "y_range": [-2, 2]}),
        ("NumberLine", "NumberLine", "DOWN", "TEAL", {"x_range": [-5, 5]}),
        ("VGroup", "VGroup", "ORIGIN", "GOLD", {}),
        ("Table", "Table", "ORIGIN", "GREEN", {}),
        ("Arrow", "Arrow", "ORIGIN", "RED", {}),
    ]
    colors = ["#89b4fa", "#fab387", "#f38ba8", "#a6e3a1", "#94e2d5", "#cdd6f4"]

    for idx, step in enumerate(plan.teaching_steps):
        concept = (
            step.concept
            if not _is_placeholder_text(step.concept)
            else f"Step {idx + 1}"
        )
        pattern = visual_patterns[idx % len(visual_patterns)]
        color = colors[idx % len(colors)]

        scenes.append(
            Scene(
                scene_id=idx + 1,
                title=f"Step {idx + 1}: {concept}",
                description=(
                    f"Visualize '{concept}' using {pattern[1]} with supporting labels. "
                    f"Use creative animations (Write, FadeIn, GrowFromCenter) to build the scene."
                ),
                narration=step.narration or f"Now we explore: {concept}.",
                duration=step.estimated_duration or 6.0,
                objects=[
                    VisualObject(
                        name=f"main_{idx + 1}",
                        type=pattern[1],
                        position=pattern[2],
                        color=color,
                        parameters=pattern[4],
                    ),
                    VisualObject(
                        name=f"title_{idx + 1}",
                        type="Text",
                        position="UP * 3",
                        color="WHITE",
                        label=concept,
                        parameters={"font_size": 36},
                    ),
                ],
            )
        )
    return Storyboard(concept_title=plan.concept_title, scenes=scenes)


def _repair_storyboard_placeholders(storyboard: Storyboard) -> None:
    """Surgically repairs common LLM omissions to prevent hard validation failures."""
    for scene in storyboard.scenes:
        if _is_placeholder_text(scene.title):
            scene.title = f"Scene {scene.scene_id}"
        if _is_placeholder_text(scene.narration):
            scene.narration = f"Now let's look at {scene.title}."

        for obj in scene.objects:
            if _is_placeholder_text(obj.name):
                obj.name = f"object_{obj.type.lower()}_{id(obj)}"
            if _is_placeholder_text(obj.type):
                obj.type = "Dot"  # Safe default
            if _is_placeholder_text(obj.position):
                obj.position = "ORIGIN"


def _validate_storyboard_completeness(  # noqa: C901, PLR0912
    storyboard: Storyboard, plan: CurriculumPlan
) -> None:
    """Enforces minimum curriculum-to-visual mapping guarantees."""
    # Repair placeholders before validation to be more resilient
    _repair_storyboard_placeholders(storyboard)

    teaching_step_count = len(plan.teaching_steps)
    scene_count = len(storyboard.scenes)

    if scene_count < max(1, (teaching_step_count // 2)):
        raise StoryboardGenerationError(
            f"Storyboard has {scene_count} scenes but requires at least "
            f"{(teaching_step_count // 2)} (half of teaching steps) to be viable."
        )

    if not any(scene.objects for scene in storyboard.scenes):
        raise StoryboardGenerationError("Storyboard scenes are missing visual objects.")

    scene_ids = [scene.scene_id for scene in storyboard.scenes]
    if len(scene_ids) != len(set(scene_ids)):
        raise StoryboardGenerationError("Storyboard scene_id values must be unique.")


def _populate_scene_occupancy(storyboard: Storyboard, ctx: GlobalContext) -> None:
    """Populates the global context's scene occupancy map from validated storyboard data.

    Iterates over each scene and its visual objects. For objects with a defined
    bounding box, reserves space in the global context to prevent visual overlap
    during subsequent generation steps.

    Args:
        storyboard: The validated storyboard containing scenes and visual objects.
        ctx: The global context object whose scene_occupancy map will be updated.
    """
    for scene in storyboard.scenes:
        for obj in scene.objects:
            if obj.bounding_box is not None:
                width, height = obj.bounding_box
                ctx.reserve_space(
                    scene_id=scene.scene_id,
                    center=obj.position,
                    width=width,
                    height=height,
                    label=obj.name,
                )


async def step_architecting(  # noqa: PLR0912
    plan: CurriculumPlan,
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    persist: bool = True,
) -> tuple[Storyboard, RunUsage | None]:
    """Executes the visual architecting phase of the generation workflow.

    Uses an AI architect to transform a pedagogical plan into a detailed
    storyboard, defining the visual elements and timing for each scene.

    Args:
        plan: The curriculum plan generated in the previous step.
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.
        ctx: The Global Context Object (GCO) for shared memory.
        persist: Whether to immediately persist the result to the database.

    Returns:
        tuple: (The generated Storyboard, RunUsage object from the AI).

    Raises:
        StoryboardGenerationError: If the architect fails to produce a storyboard.
    """
    usage: RunUsage | None = None
    storyboard: Storyboard | None = None
    if not job.storyboard:
        max_retries = 3
        current_attempt = 0
        last_error: str | None = None

        logger.info("architecting_generation_started", mode=job.mode)
        architect_model = get_step_model(request, job, agent_id="architect")

        if not architect_model:
            raise StoryboardGenerationError(
                "Could not initialize model. Ensure API keys are configured."
            )

        while current_attempt < max_retries:
            current_attempt += 1
            retry_prefix = (
                f"[Attempt {current_attempt}/{max_retries}] " if max_retries > 1 else ""
            )
            if current_attempt > 1:
                await on_thought(
                    "system",
                    "status",
                    f"{retry_prefix}Regenerating storyboard after completeness failure...",
                )

            retry_hint = (
                f"Previous storyboard failed completeness checks. "
                f"Error: {last_error or 'unknown'} "
                f"Requirements: produce at least {len(plan.teaching_steps)} scenes "
                f"(>= teaching steps) and ensure each scene has at least one visual object "
                f"and references teaching-step concepts in its scene text."
                if last_error
                else None
            )

            try:
                storyboard, usage = await generate_storyboard(
                    plan,
                    architect_model,
                    on_thought=on_thought,
                    ctx=ctx,
                    retry_hint=retry_hint,
                    usage_limits=UsageLimits(
                        request_limit=get_settings().agent_request_limit_architect
                    ),
                )
                _validate_storyboard_completeness(storyboard, plan)
                _populate_scene_occupancy(storyboard, ctx)
                break
            except StoryboardGenerationError as e:
                last_error = str(e)
                logger.warning(
                    "architecting_completeness_failed",
                    attempt=current_attempt,
                    max_retries=max_retries,
                    error=last_error,
                )
                if current_attempt >= max_retries:
                    logger.warning("architecting_retries_exhausted_using_fallback")
                    await on_thought(
                        "system",
                        "status",
                        "Storyboard retries exhausted; using deterministic storyboard fallback.",
                    )
                    storyboard = _build_deterministic_storyboard(plan)
                    usage = usage or RunUsage()
                    _validate_storyboard_completeness(storyboard, plan)
                    break
                continue
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "architecting_model_call_failed",
                    attempt=current_attempt,
                    max_retries=max_retries,
                    error=last_error,
                )
                await on_thought(
                    "system",
                    "status",
                    f"{retry_prefix}Architect model call failed: {last_error}. Retrying...",
                )
                if current_attempt >= max_retries:
                    logger.warning("architecting_retries_exhausted_using_fallback")
                    await on_thought(
                        "system",
                        "status",
                        "All architect retries exhausted; using deterministic storyboard fallback.",
                    )
                    storyboard = _build_deterministic_storyboard(plan)
                    usage = RunUsage()
                    break
                continue

        if not storyboard:
            raise StoryboardGenerationError(
                "Architecting did not produce a storyboard after retry policy."
            )

        if job.mode == "mock" and persist:
            # Simulate incremental "filling in" of the storyboard
            logger.info(
                "architecting_mock_incremental_population_started",
                scenes_total=len(storyboard.scenes),
            )
            for i in range(1, len(storyboard.scenes) + 1):
                partial_storyboard = storyboard.model_copy(
                    update={"scenes": storyboard.scenes[:i]}
                )
                await update_job({"storyboard": partial_storyboard.model_dump()})
                await asyncio.sleep(0.3)  # Brief pause between scenes

        job.storyboard = storyboard.model_dump()
        job.current_step = "architecting_complete"
        if persist:
            await update_job(
                {"storyboard": job.storyboard, "current_step": job.current_step}
            )
        logger.info("architecting_step_complete")
    else:
        logger.info("architecting_checkpoint_reused")
        storyboard = parse_job_artifact(job.storyboard, Storyboard)
    return storyboard, usage
