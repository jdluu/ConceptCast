"""Agent specialized in generating Manim Python code from visual storyboards.

Enforces strict Manim API usage rules and utilizes pedagogical best practices
for visual clarity and pacing.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.tools import prepare_manim_docs, search_manim_docs
from services.workflow.context_injectors import extract_animator_context

from .base import ConceptAgent

# Initialize the shared animator agent instance
animator_agent: ConceptAgent[str] = ConceptAgent("animator", str)


async def generate_manim_code(
    target_scene: Scene | Storyboard,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
    message_history: list[ModelMessage] | None = None,
    scene_id: int | None = None,
) -> tuple[str, RunUsage]:
    """Generates Manim Python code derived from a visual storyboard.

    Args:
        target_scene: The specific scene or full storyboard to generate code for.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        retry_hint: Optional feedback for iterative improvement.
        ctx: The Global Context Object (GCO) for the workflow.
        message_history: Optional history for stateful multi-turn retries.
        scene_id: Optional scene identifier for context injection.

    Returns:
        tuple[str, RunUsage]: The generated Python code and token usage metadata.
    """

    def _prepare_agent(agent: Agent[Any, Any]) -> None:
        agent.tool(prepare=prepare_manim_docs)(search_manim_docs)

    if ctx:
        prompt = extract_animator_context(ctx, target_scene, scene_id=scene_id)
    else:
        prompt = f"Write Manim code for scene: {json.dumps(target_scene.model_dump())}"

    if retry_hint:
        prompt = f"{prompt}\n\nIMPORTANT REVISION FEEDBACK: {retry_hint}"

    result, usage = await animator_agent.run(
        model=model,
        prompt=prompt,
        on_thought=on_thought,
        ctx=ctx,
        pre_run_hook=_prepare_agent,
        message_history=message_history,
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
