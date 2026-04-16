"""Agent specialized in generating Manim Python code from visual storyboards.

Enforces strict Manim API usage rules and utilizes pedagogical best practices
for visual clarity and pacing.
"""

import json
from collections.abc import Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed
from infra.ai.tools import prepare_manim_docs, search_manim_docs
from services.workflow.context_injectors import extract_animator_context

system_prompt = load_prompt("animator")


async def generate_manim_code(
    target_scene: Scene | Storyboard,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[str, RunUsage]:
    """Generates Manim Python code derived from a visual storyboard.

    Args:
        target_scene: The specific scene or full storyboard to generate code for.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        retry_hint: Optional feedback for iterative improvement.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple[str, RunUsage]: The generated Python code and token usage metadata.
    """
    animator_agent = Agent(
        model.model,
        system_prompt=system_prompt,
        output_type=str,
        deps_type=GlobalContext,
        retries=3,
    )
    docs_lookup_needed = False
    if retry_hint:
        normalized_hint = retry_hint.lower()
        docs_lookup_needed = any(
            marker in normalized_hint
            for marker in (
                "attributeerror",
                "typeerror",
                "nameerror",
                "manim api",
                "unknown",
                "constructor",
                "parameter",
            )
        )
    if docs_lookup_needed:
        # Dynamically attach documentation search tool if API errors are detected
        animator_agent.tool(prepare=prepare_manim_docs)(search_manim_docs)

    if ctx:
        prompt = extract_animator_context(ctx, target_scene)
    else:
        prompt = f"Write Manim code for scene: {json.dumps(target_scene.model_dump())}"

    if retry_hint:
        prompt = f"{prompt}\n\nIMPORTANT REVISION FEEDBACK: {retry_hint}"

    result, usage = await run_agent_streamed(
        "animator",
        animator_agent,
        prompt,
        on_thought=on_thought,
        deps=ctx,
    )

    # Post-processing: Clean up potential markdown fences
    if isinstance(result, str):
        result = result.strip()
        if result.startswith("```"):
            lines = result.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            result = "\n".join(lines).strip()

    return result, usage
