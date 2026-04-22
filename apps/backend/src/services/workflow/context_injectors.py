"""Utility module for slicing and injecting Global Context into agent prompts.

Provides targeted extraction logic to minimize context window usage while
maintaining visual and pedagogical consistency.
"""

import json
from typing import Any

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext


def _format_context(data: dict[str, Any]) -> str:
    """Serializes a dictionary to a formatted context block, handling Pydantic models.

    Traverses the input data recursively to ensure all Pydantic models are converted
    to JSON-compatible primitives before serialization.

    Args:
        data: The dictionary of context variables to serialize.

    Returns:
        str: A human-readable JSON block prefixed with WORKFLOW_CONTEXT.
    """

    def _dump(obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        if isinstance(obj, list):
            return [_dump(item) for item in obj]
        if isinstance(obj, dict):
            return {k: _dump(v) for k, v in obj.items()}
        return obj

    cleaned = {k: _dump(v) for k, v in data.items()}
    return f"<workflow_context>\n{json.dumps(cleaned, indent=2)}\n</workflow_context>"


def extract_analyst_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Pedagogical Analyst.

    Provides the target topic, original user prompt, audience, and
    global style constraints to guide the initial curriculum deconstruction.

    Args:
        ctx: The shared Global Context Object.

    Returns:
        str: The serialized context block for the Analyst agent.
    """
    return _format_context(
        {
            "topic": ctx.topic,
            "user_prompt": ctx.user_prompt,
            "target_audience": ctx.target_audience,
            "style_guidelines": ctx.style,
        }
    )


def extract_architect_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Visual Architect.

    Focuses on the pedagogical plan, global branding, and existing lexicon
    to ensure the storyboard remains consistent with previous decisions.

    Args:
        ctx: The shared Global Context Object.

    Returns:
        str: The serialized context block for the Architect agent.
    """
    return _format_context(
        {
            "topic": ctx.topic,
            "target_audience": ctx.target_audience,
            "style_guidelines": ctx.style,
            "pedagogical_plan": ctx.plan,
            "existing_visual_lexicon": ctx.lexicon,
            "recent_decisions": ctx.decisions[-5:],
        }
    )


def extract_animator_context(
    ctx: GlobalContext,
    target_scene: Scene | Storyboard | None = None,
    scene_id: int | None = None,
) -> str:
    """Extracts relevant context for the Animator Agent.

    Focuses on the target scene, branding, and specific lexicon entries
    for the objects being rendered. Includes the scene occupancy map,
    current scene ID, and the error buffer to prevent repeated syntax or
    logic errors.

    Args:
        ctx: The shared Global Context Object.
        target_scene: The specific scene or storyboard to generate code for.
        scene_id: The index of the scene currently being generated.

    Returns:
        str: The serialized context block for the Animator agent.
    """
    return _format_context(
        {
            "style_guidelines": ctx.style,
            "target_scene": target_scene,
            "current_scene_id": scene_id,
            "scene_occupancy_map": ctx.scene_occupancy,
            "current_manim_code": ctx.manim_code,
            "visual_lexicon": ctx.lexicon,
            "previous_errors_to_avoid": [
                e for e in ctx.error_buffer if e.agent == "animator"
            ],
        }
    )


def extract_reviewer_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Reviewer Agent.

    Provides the target storyboard and lexicon to verify fidelity, along with
    the error history to ensure revisions are progressing.

    Args:
        ctx: The shared Global Context Object.

    Returns:
        str: The serialized context block for the Reviewer agent.
    """
    return _format_context(
        {
            "target_storyboard": ctx.storyboard,
            "visual_lexicon": ctx.lexicon,
            "revision_history": [
                e for e in ctx.error_buffer if e.agent in ["animator", "reviewer"]
            ],
        }
    )
