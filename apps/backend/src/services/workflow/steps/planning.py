import asyncio
from collections.abc import Awaitable, Callable

import structlog
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, JobRequest, TeachingStep
from domain.agents.analyst import generate_curriculum
from domain.models.workflow import GlobalContext
from infra.exceptions import PlanGenerationError
from infra.models.job import JobRecord
from services.workflow.base import get_step_model
from services.workflow.utils import parse_job_artifact

logger = structlog.get_logger(__name__)


def _is_placeholder_text(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"", "__missing__", "missing", "tbd", "n/a", "..."}


def _normalize_plan_defaults(
    plan: CurriculumPlan, request: JobRequest
) -> CurriculumPlan:
    """Hydrate required top-level plan fields from request defaults when missing."""
    updates: dict[str, str] = {}
    if _is_placeholder_text(plan.concept_title):
        updates["concept_title"] = request.topic.strip()
    if _is_placeholder_text(plan.target_audience):
        updates["target_audience"] = request.target_audience.strip()
    if not updates:
        return plan
    return plan.model_copy(update=updates)


def _plan_structure_issues(plan: CurriculumPlan) -> list[str]:
    """Returns deterministic structural issues for generated curricula."""
    issues: list[str] = []

    concept = plan.concept_title.strip() if plan.concept_title else ""
    audience = plan.target_audience.strip() if plan.target_audience else ""
    if _is_placeholder_text(concept):
        issues.append("concept_title is empty or placeholder")
    if _is_placeholder_text(audience):
        issues.append("target_audience is empty or placeholder")

    if not plan.teaching_steps:
        issues.append("teaching_steps is empty")
        return issues

    if not 5 <= len(plan.teaching_steps) <= 10:
        issues.append(
            f"teaching_steps length must be between 5 and 10 (got {len(plan.teaching_steps)})"
        )

    for index, step in enumerate(plan.teaching_steps, start=1):
        if not step.concept or not step.concept.strip():
            issues.append(f"teaching_steps[{index}].concept is empty")
        if not step.visual_metaphor or not step.visual_metaphor.strip():
            issues.append(f"teaching_steps[{index}].visual_metaphor is empty")
        if not step.narration or not step.narration.strip():
            issues.append(f"teaching_steps[{index}].narration is empty")
    return issues


async def step_planning(
    request: JobRequest,
    job: JobRecord,
    update_job: Callable[[dict[str, object]], Awaitable[None]],
    on_thought: Callable[[str, str, str], Awaitable[None]],
    ctx: GlobalContext,
    force_generate: bool = False,
    retry_hint: str | None = None,
) -> tuple[CurriculumPlan, RunUsage | None]:
    """Executes the curriculum planning phase of the generation workflow.

    Uses an AI analyst to decompose the input topic into a structured,
    pedagogical plan appropriate for the target audience.

    Args:
        request: The initial job request details.
        job: The current job record in the database.
        update_job: Async callback for persisting job state changes.
        on_thought: Async callback for streaming agent reasoning.
        ctx: The Global Context Object (GCO) for shared memory.

    Returns:
        tuple: (The generated CurriculumPlan, RunUsage object from the AI).

    Raises:
        PlanGenerationError: If the analyst fails to produce a valid plan.
    """
    usage: RunUsage | None = None
    if force_generate or not job.plan:
        logger.info(
            "planning_generation_started",
            topic=request.topic,
            mode=job.mode,
        )

        plan_model = get_step_model(request, job, agent_id="analyst")

        if not plan_model:
            raise PlanGenerationError(
                "Could not initialize model. Ensure API keys are configured."
            )

        try:
            steps_draft, usage = await generate_curriculum(
                topic=request.topic,
                audience=request.target_audience,
                model=plan_model,
                on_thought=on_thought,
                retry_hint=retry_hint,
                ctx=ctx,
            )
            plan = CurriculumPlan(
                concept_title=request.topic.strip(),
                target_audience=request.target_audience.strip(),
                teaching_steps=steps_draft.teaching_steps,
            )
        except Exception as e:
            logger.warning(
                "planning_structured_output_failed",
                error=str(e),
                fallback="minimal_structure",
            )
            plan = CurriculumPlan(
                concept_title=request.topic,
                target_audience=request.target_audience,
                teaching_steps=[
                    TeachingStep(
                        step_id=1,
                        concept=f"Introduction to {request.topic}",
                        visual_metaphor="A simple title screen",
                        narration=f"Today we are exploring {request.topic}.",
                    ),
                    TeachingStep(
                        step_id=2,
                        concept=f"Why {request.topic} matters",
                        visual_metaphor="A problem-to-solution bridge made of simple shapes",
                        narration=f"We begin with the core motivation behind {request.topic}.",
                    ),
                    TeachingStep(
                        step_id=3,
                        concept=f"Core mechanics of {request.topic}",
                        visual_metaphor="A layered block diagram revealing one layer at a time",
                        narration=f"Now we unpack how {request.topic} works at a high level.",
                    ),
                    TeachingStep(
                        step_id=4,
                        concept=f"Common pitfalls in {request.topic}",
                        visual_metaphor="A branching path with highlighted incorrect routes",
                        narration="Let's review frequent misconceptions and how to avoid them.",
                    ),
                    TeachingStep(
                        step_id=5,
                        concept=f"Practical application of {request.topic}",
                        visual_metaphor="A pipeline animation moving from input to output",
                        narration=f"Finally, we apply {request.topic} in a realistic scenario.",
                    ),
                ],
            )
            usage = RunUsage()

        plan = _normalize_plan_defaults(plan, request)
        structure_issues = _plan_structure_issues(plan)
        if structure_issues:
            raise PlanGenerationError(
                "Curriculum plan failed structural checks:\n- "
                + "\n- ".join(structure_issues)
            )

        if job.mode == "mock":
            # Simulate incremental "filling in" of the plan for realism
            logger.info(
                "planning_mock_incremental_population_started",
                steps_total=len(plan.teaching_steps),
            )
            for i in range(1, len(plan.teaching_steps) + 1):
                partial_plan = plan.model_copy(
                    update={"teaching_steps": plan.teaching_steps[:i]}
                )
                await update_job({"plan": partial_plan.model_dump()})
                await asyncio.sleep(0.4)  # Brief pause between steps

        job.plan = plan.model_dump()
        job.current_step = "planning_complete"
        await update_job(
            {
                "plan": job.plan,
                "current_step": job.current_step,
            }
        )
        logger.info("planning_step_complete")
    else:
        logger.info("planning_checkpoint_reused")
        plan = parse_job_artifact(job.plan, CurriculumPlan)
    return plan, usage
