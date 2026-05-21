"""Agent specialized in generating Manim Python code from visual storyboards.

Enforces strict Manim API usage rules and utilizes pedagogical best practices
for visual clarity and pacing.
"""

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.tools import (
    get_aesthetic_palette,
    lint_manim_code,
    lookup_manim_pattern,
    prepare_manim_docs,
    search_manim_docs,
)
from services.workflow.context_injectors import extract_animator_context

from .base import ConceptAgent

# Initialize the shared animator agent instance
animator_agent: ConceptAgent[str] = ConceptAgent("animator", str)

_CODE_BLOCK_PATTERN = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_python_code(raw: str) -> str:
    """Extracts the last complete Python code block from model output.

    Falls back to the raw content (stripped of markdown fences) when no
    fenced block is detected. Preferring the *last* match handles cases
    where the model emits prose followed by a corrected version.

    Args:
        raw: Raw model output that may contain markdown fences and prose.

    Returns:
        The extracted Python source code.
    """
    blocks = _CODE_BLOCK_PATTERN.findall(raw)
    if blocks:
        return str(blocks[-1]).strip()

    # Fallback: strip leading/trailing fences that were not properly paired
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


async def generate_manim_code(
    target_scene: Scene | Storyboard,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
    message_history: list[ModelMessage] | None = None,
    scene_id: int | None = None,
    usage_limits: UsageLimits | None = None,
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
        usage_limits: Optional pydantic-ai UsageLimits for capping requests/tokens.

    Returns:
        tuple[str, RunUsage]: The generated Python code and token usage metadata.
    """

    def _prepare_agent(agent: Agent[Any, Any]) -> None:
        agent.tool(prepare=prepare_manim_docs)(search_manim_docs)
        agent.tool()(lint_manim_code)
        agent.tool()(lookup_manim_pattern)
        agent.tool()(get_aesthetic_palette)

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
        usage_limits=usage_limits,
    )

    if isinstance(result, str):
        result = extract_python_code(result)

    return result, usage
