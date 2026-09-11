"""Agent specialized in curriculum planning and pedagogical deconstruction.

Uses self-correction via a critic tool to ensure the generated learning
dependency graph is logical and effective.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai.usage import RunUsage, UsageLimits

from domain.models.curriculum import TeachingStepsDraft
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from services.workflow.context_injectors import extract_analyst_context

from .base import ConceptAgent

# Initialize the shared analyst agent instance
analyst_agent: ConceptAgent[TeachingStepsDraft] = ConceptAgent(
    "analyst", TeachingStepsDraft
)


async def generate_curriculum(
    topic: str,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
    usage_limits: UsageLimits | None = None,
) -> tuple[TeachingStepsDraft, RunUsage]:
    """Generates a pedagogical curriculum plan for a given topic.

    Args:
        topic: The complex technical topic to deconstruct.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.
        usage_limits: Optional pydantic-ai UsageLimits for capping requests/tokens.

    Returns:
        tuple: (Generated teaching steps draft, RunUsage data).
    """
    prompt = extract_analyst_context(ctx) if ctx else f"Explain '{topic}'."

    if retry_hint:
        prompt = f"{prompt}\n\nREPAIR INSTRUCTIONS:\n{retry_hint}"

    return await analyst_agent.run(
        model=model,
        prompt=prompt,
        on_thought=on_thought,
        ctx=ctx,
        usage_limits=usage_limits,
    )
