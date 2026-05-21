"""Agent specialized in visual architecting and scene storyboarding.

Transforms abstract pedagogical plans into concrete visual objects and
animations for the Manim engine.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai.usage import RunUsage, UsageLimits

from api.schemas import CurriculumPlan, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.tools import get_aesthetic_palette
from services.workflow.context_injectors import extract_architect_context

from .base import ConceptAgent

# Initialize the shared architect agent instance
architect_agent: ConceptAgent[Storyboard] = ConceptAgent("architect", Storyboard)


async def generate_storyboard(
    plan: CurriculumPlan,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
    retry_hint: str | None = None,
    usage_limits: UsageLimits | None = None,
) -> tuple[Storyboard, RunUsage]:
    """Translates a curriculum plan into a visual storyboard.

    Args:
        plan: The pedagogically sound curriculum plan.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.
        usage_limits: Optional pydantic-ai UsageLimits for capping requests/tokens.

    Returns:
        tuple: (The structured Storyboard, RunUsage data).
    """
    if ctx:
        prompt = extract_architect_context(ctx)
    else:
        prompt = f"Create a storyboard for the following curriculum:\n{plan.model_dump_json()}"

    if retry_hint:
        prompt = f"{prompt}\n\nREPAIR INSTRUCTIONS:\n{retry_hint}"

    def _prepare_agent(agent: Any) -> None:
        agent.tool()(get_aesthetic_palette)

    return await architect_agent.run(
        model=model,
        prompt=prompt,
        on_thought=on_thought,
        ctx=ctx,
        pre_run_hook=_prepare_agent,
        usage_limits=usage_limits,
    )
