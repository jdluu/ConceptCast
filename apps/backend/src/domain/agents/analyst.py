"""Agent specialized in curriculum planning and pedagogical deconstruction.

Uses self-correction via a critic tool to ensure the generated learning
dependency graph is logical and effective for the target audience.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai.usage import RunUsage

from domain.models.curriculum import TeachingStepsDraft
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from services.workflow.context_injectors import extract_analyst_context

from .base import ConceptAgent

# Initialize the shared analyst agent instance
analyst_agent: ConceptAgent[TeachingStepsDraft] = ConceptAgent("analyst", TeachingStepsDraft)


async def generate_curriculum(
    topic: str,
    audience: str,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[TeachingStepsDraft, RunUsage]:
    """Generates a pedagogical curriculum plan for a given topic.

    Args:
        topic: The complex technical topic to deconstruct.
        audience: The target knowledge level of the audience.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (Generated teaching steps draft, RunUsage data).
    """
    if ctx:
        prompt = extract_analyst_context(ctx)
    else:
        prompt = f"Explain '{topic}' to a '{audience}' audience."

    if retry_hint:
        prompt = f"{prompt}\n\nREPAIR INSTRUCTIONS:\n{retry_hint}"

    return await analyst_agent.run(
        model=model, prompt=prompt, on_thought=on_thought, ctx=ctx
    )
