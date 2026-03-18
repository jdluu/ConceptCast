"""Agent specialized in pedagogical auditing and content validation.

Reviews curriculum plans for logical progression, concept clarity, and
visual metaphor effectiveness.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, ValidationResult
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed
from services.workflow.context_injectors import extract_validator_context

system_prompt = load_prompt("validator")


async def validate_curriculum(
    plan: CurriculumPlan,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[ValidationResult, RunUsage]:
    """Audits a curriculum plan for pedagogical and visual alignment.

    Args:
        plan: The curriculum plan to validate.
        model: The ConceptCast model instance for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (The structured ValidationResult, RunUsage data).
    """
    agent = Agent(
        model.model,
        system_prompt=system_prompt,
        output_type=ValidationResult,
        deps_type=GlobalContext,
        retries=3,
    )

    if ctx:
        # Ensure the plan is in the context if not already there
        if not ctx.plan:
            ctx.plan = plan
        prompt = extract_validator_context(ctx)
    else:
        prompt = f"Perform a pedagogical audit on this plan:\n{plan.model_dump_json()}"

    result, usage = await run_agent_streamed(
        "validator", agent, prompt, on_thought=on_thought, deps=ctx
    )
    return result, usage
