"""Utility module for slicing and injecting Global Context into agent prompts.

Provides targeted extraction logic to minimize context window usage while
maintaining visual and pedagogical consistency.
"""

import json
from typing import Any

from api.schemas import Scene, Storyboard
from domain.models.workflow import ErrorEvent, GlobalContext


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

    Provides the target topic, original user prompt, and global style
    constraints to guide the initial curriculum deconstruction.

    Args:
        ctx: The shared Global Context Object.

    Returns:
        str: The serialized context block for the Analyst agent.
    """
    return _format_context(
        {
            "topic": ctx.topic,
            "user_prompt": ctx.user_prompt,
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
            "style_guidelines": ctx.style,
            "pedagogical_plan": ctx.plan,
            "existing_visual_lexicon": ctx.lexicon,
            "recent_decisions": ctx.decisions[-5:],
        }
    )


def _filter_lexicon(  # noqa: PLR0912
    lexicon: dict[str, Any], target_scene: Scene | Storyboard | None
) -> dict[str, Any]:
    """Filters the visual lexicon to include only concepts referenced in the target scene/storyboard."""
    if not target_scene or not lexicon:
        return lexicon

    search_text = []
    if hasattr(target_scene, "scenes"):  # Storyboard
        for scene in target_scene.scenes:
            search_text.append(scene.title or "")
            search_text.append(scene.description or "")
            search_text.append(scene.narration or "")
            for obj in getattr(scene, "objects", []):
                search_text.append(obj.name or "")
                search_text.append(obj.type or "")
                search_text.append(obj.label or "")
                search_text.append(obj.color or "")
                for v in getattr(obj, "parameters", {}).values():
                    if isinstance(v, str):
                        search_text.append(v)
    else:  # Scene
        search_text.append(getattr(target_scene, "title", "") or "")
        search_text.append(getattr(target_scene, "description", "") or "")
        search_text.append(getattr(target_scene, "narration", "") or "")
        for obj in getattr(target_scene, "objects", []):
            search_text.append(obj.name or "")
            search_text.append(obj.type or "")
            search_text.append(obj.label or "")
            search_text.append(obj.color or "")
            for v in getattr(obj, "parameters", {}).values():
                if isinstance(v, str):
                    search_text.append(v)

    combined_text = " ".join(search_text).lower()

    filtered_lexicon = {}
    for concept, symbol in lexicon.items():
        concept_lower = concept.lower()
        if concept_lower in combined_text:
            filtered_lexicon[concept] = symbol
            continue
        if hasattr(symbol, "concept") and symbol.concept.lower() in combined_text:
            filtered_lexicon[concept] = symbol
            continue

    if not filtered_lexicon:
        return lexicon

    return filtered_lexicon


def extract_animator_context(
    ctx: GlobalContext,
    target_scene: Scene | Storyboard | None = None,
    scene_id: int | None = None,
    include_errors: bool = True,
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
    animator_errors = [e for e in ctx.error_buffer if e.agent == "animator"]
    recent_errors = []
    if not include_errors:
        animator_errors = []
    for idx, err in enumerate(animator_errors):
        if idx >= len(animator_errors) - 2:
            recent_errors.append(err)
        else:
            pruned_message = err.message.splitlines()[0] if err.message else ""
            if len(pruned_message) > 150:
                pruned_message = pruned_message[:147] + "..."
            recent_errors.append(
                ErrorEvent(
                    agent=err.agent,
                    step=err.step,
                    error_type=err.error_type,
                    message=f"[Pruned older error] {pruned_message}",
                    context={},
                    timestamp=err.timestamp,
                )
            )

    filtered_lex = _filter_lexicon(ctx.lexicon, target_scene)

    context_data: dict[str, Any] = {
        "style_guidelines": ctx.style,
        "target_scene": target_scene,
        "current_scene_id": scene_id,
        "visual_lexicon": filtered_lex,
    }
    if recent_errors:
        context_data["recent_errors_to_avoid"] = recent_errors[-3:]
    return _format_context(context_data)
