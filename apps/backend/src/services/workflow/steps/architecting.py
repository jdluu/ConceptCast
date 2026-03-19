import asyncio
from collections.abc import Awaitable, Callable

import structlog
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, Storyboard
from domain.agents.architect import generate_storyboard
from domain.models.workflow import GlobalContext
from infra.exceptions import StoryboardGenerationError
from infra.models.job import JobRecord
from services.workflow.base import get_step_model
from services.workflow.utils import parse_job_artifact

logger = structlog.get_logger(__name__)


def _is_placeholder_text(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"", "__missing__", "missing", "tbd", "n/a", "..."}


def _build_deterministic_storyboard(plan: CurriculumPlan) -> Storyboard:
    from api.schemas import Scene, VisualObject

    scenes: list[Scene] = []
    for idx, step in enumerate(plan.teaching_steps):
        concept = (
            step.concept
            if not _is_placeholder_text(step.concept)
            else f"Step {idx + 1}"
        )
        scenes.append(
            Scene(
                scene_id=idx + 1,
                title=f"Step {idx + 1}: {concept}",
                description=f"Visualizing: {concept}",
                narration=step.narration or f"Now we learn: {concept}.",
                objects=[
                    VisualObject(
                        name=f"concept_text_{idx + 1}",
                        type="Text",
                        position="UP * 2",
                        color="WHITE",
                        label=concept,
                        parameters={"font_size": 34},
                    )
                ],
            )
        )
    return Storyboard(concept_title=plan.concept_title, scenes=scenes)


def _validate_storyboard_completeness(  # noqa: C901, PLR0912
    storyboard: Storyboard, plan: CurriculumPlan
) -> None:
    """Enforces minimum curriculum-to-visual mapping guarantees."""
    teaching_step_count = len(plan.teaching_steps)
    scene_count = len(storyboard.scenes)

    if scene_count < max(1, teaching_step_count):
        raise StoryboardGenerationError(
            f"Storyboard has {scene_count} scenes but requires at least "
            f"{teaching_step_count} to cover teaching steps."
        )

    if not any(scene.objects for scene in storyboard.scenes):
        raise StoryboardGenerationError(
            "Storyboard scenes are missing visual objects. "
            "Add at least one visual object in the storyboard."
        )

    scene_ids = [scene.scene_id for scene in storyboard.scenes]
    if len(scene_ids) != len(set(scene_ids)):
        raise StoryboardGenerationError("Storyboard scene_id values must be unique.")
    if scene_ids != sorted(scene_ids):
        raise StoryboardGenerationError(
            "Storyboard scene_id values must be strictly increasing."
        )
    if scene_ids and scene_ids[0] != 1:
        raise StoryboardGenerationError(
            "Storyboard scene_id must start at 1 and increase sequentially."
        )

    for scene in storyboard.scenes:
        if _is_placeholder_text(scene.title):
            raise StoryboardGenerationError(
                f"Scene {scene.scene_id} has empty/placeholder title."
            )
        if _is_placeholder_text(scene.narration):
            raise StoryboardGenerationError(
                f"Scene {scene.scene_id} has empty/placeholder narration."
            )
        for obj in scene.objects:
            if _is_placeholder_text(obj.name):
                raise StoryboardGenerationError(
                    f"Scene {scene.scene_id} has visual object with empty/placeholder name."
                )
            if _is_placeholder_text(obj.type):
                raise StoryboardGenerationError(
                    f"Scene {scene.scene_id} has visual object with empty/placeholder type."
                )
            if _is_placeholder_text(obj.position):
                raise StoryboardGenerationError(
                    f"Scene {scene.scene_id} has visual object with empty/placeholder position."
                )

    plan_concepts = {
        step.concept.lower() for step in plan.teaching_steps if step.concept
    }
    covered = 0
    coverage_hits: set[str] = set()
    for scene in storyboard.scenes:
        haystack = " ".join(
            [
                scene.title or "",
                scene.description or "",
                scene.narration or "",
            ]
        ).lower()
        for concept in plan_concepts:
            if concept and concept in haystack:
                coverage_hits.add(concept)
        if any(concept in haystack for concept in plan_concepts):
            covered += 1

    if plan_concepts and covered == 0:
        raise StoryboardGenerationError(
            "Storyboard does not reference teaching-step concepts in scene text."
        )
    if plan_concepts:
        coverage_ratio = len(coverage_hits) / len(plan_concepts)
        if coverage_ratio < 0.6:
            raise StoryboardGenerationError(
                "Storyboard concept coverage is too low "
                f"({len(coverage_hits)}/{len(plan_concepts)} concepts covered)."
            )


async def step_architecting(
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
                )
                _validate_storyboard_completeness(storyboard, plan)
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
                # If the model call itself failed, fall back to a deterministic
                # storyboard so the workflow can proceed (and still satisfy gates).
                logger.warning(
                    "architecting_model_call_failed_using_fallback",
                    attempt=current_attempt,
                    retry_prefix=retry_prefix,
                    error=str(e),
                )
                await on_thought(
                    "system",
                    "status",
                    f"{retry_prefix}Architect failed; using deterministic storyboard fallback.",
                )
                storyboard = _build_deterministic_storyboard(plan)
                usage = RunUsage()
                # Deterministic fallback should satisfy completeness gates.
                _validate_storyboard_completeness(storyboard, plan)
                break

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
