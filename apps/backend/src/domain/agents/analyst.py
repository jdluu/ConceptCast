"""Agent specialized in curriculum planning and pedagogical deconstruction.

Uses self-correction via a critic tool to ensure the generated learning
dependency graph is logical and effective for the target audience.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, ValidationResult
from domain.agents.validator import validate_curriculum
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed
from services.workflow.context_injectors import extract_analyst_context

system_prompt = load_prompt("analyst")


async def generate_curriculum(
    topic: str,
    audience: str,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[CurriculumPlan, RunUsage]:
    """Generates a pedagogical curriculum plan for a given topic.

    Args:
        topic: The complex technical topic to deconstruct.
        audience: The target knowledge level of the audience.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (The structured CurriculumPlan, RunUsage data).
    """
    agent = Agent(
        model.model,
        system_prompt=system_prompt,
        output_type=CurriculumPlan,
        deps_type=GlobalContext,
        retries=3,
    )

    @agent.tool
    async def consult_critic(
        _ctx: RunContext[GlobalContext], plan: CurriculumPlan
    ) -> ValidationResult:
        """Consults the Validator Agent to review the generated curriculum plan.

        Args:
            _ctx: The run context containing global workflow state.
            plan: The curriculum plan to validate.

        Returns:
            The validation result from the reviewer.
        """
        res, _ = await validate_curriculum(
            plan, model, on_thought=on_thought, ctx=_ctx.deps
        )
        return res

    if ctx:
        prompt = extract_analyst_context(ctx)
    else:
        prompt = (
            f"Explain '{topic}' to a '{audience}' audience. "
            "Remember to consult the critic before finalizing your output."
        )

    result, usage = await run_agent_streamed(
        "analyst", agent, prompt, on_thought=on_thought, deps=ctx
    )
    return result, usage
