"""Agent specialized in visual architecting and scene storyboarding.

Transforms abstract pedagogical plans into concrete visual objects and
animations for the Manim engine.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed
from services.workflow.context_injectors import extract_architect_context

system_prompt = load_prompt("architect")


async def generate_storyboard(
    plan: CurriculumPlan,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[Storyboard, RunUsage]:
    """Translates a curriculum plan into a visual storyboard.

    Args:
        plan: The pedagogically sound curriculum plan.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (The structured Storyboard, RunUsage data).
    """
    agent = Agent(
        model.model,
        system_prompt=system_prompt,
        output_type=Storyboard,
        deps_type=GlobalContext,
        retries=3,
    )

    if ctx:
        prompt = extract_architect_context(ctx)
    else:
        prompt = f"Create a storyboard for the following curriculum:\n{plan.model_dump_json()}"

    result, usage = await run_agent_streamed(
        "architect", agent, prompt, on_thought=on_thought, deps=ctx
    )
    return result, usage
