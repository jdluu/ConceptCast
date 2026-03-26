"""Utility module for slicing and injecting Global Context into agent prompts.

Provides targeted extraction logic to minimize context window usage while
maintaining visual and pedagogical consistency.
"""

import json

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext


def extract_analyst_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Pedagogical Analyst.

    Provides the target topic, original user prompt, audience, and 
    global style constraints to guide the initial curriculum deconstruction.
    """
    context = {
        "topic": ctx.topic,
        "user_prompt": ctx.user_prompt,
        "target_audience": ctx.target_audience,
        "style_guidelines": ctx.style.model_dump(mode="json") if ctx.style else None,
    }
    return f"WORKFLOW_CONTEXT:\n{json.dumps(context, indent=2)}"


def extract_architect_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Visual Architect.

    Focuses on the pedagogical plan, global branding, and existing lexicon
    to ensure the storyboard remains consistent with previous decisions.
    """
    context = {
        "topic": ctx.topic,
        "target_audience": ctx.target_audience,
        "style_guidelines": ctx.style.model_dump(mode="json") if ctx.style else None,
        "pedagogical_plan": ctx.plan.model_dump(mode="json") if ctx.plan else None,
        "existing_visual_lexicon": {
            k: v.model_dump(mode="json") for k, v in ctx.lexicon.items()
        },
        "recent_decisions": [d.model_dump(mode="json") for d in ctx.decisions[-5:]],
    }
    return f"WORKFLOW_CONTEXT:\n{json.dumps(context, indent=2)}"


def extract_animator_context(
    ctx: GlobalContext, target_scene: Scene | Storyboard | None = None
) -> str:
    """Extracts relevant context for the Animator Agent.

    Focuses on the target scene, branding, and specific lexicon entries
    for the objects being rendered. Includes the error buffer to prevent
    repeated syntax or logic errors.
    """
    context = {
        "style_guidelines": ctx.style.model_dump(mode="json") if ctx.style else None,
        "target_scene": target_scene.model_dump(mode="json") if target_scene else None,
        "current_manim_code": ctx.manim_code,
        "visual_lexicon": {k: v.model_dump(mode="json") for k, v in ctx.lexicon.items()},
        "previous_errors_to_avoid": [
            e.model_dump(mode="json") for e in ctx.error_buffer if e.agent == "animator"
        ],
    }
    return f"WORKFLOW_CONTEXT:\n{json.dumps(context, indent=2)}"


def extract_reviewer_context(ctx: GlobalContext) -> str:
    """Extracts relevant context for the Reviewer Agent.

    Provides the target storyboard and lexicon to verify fidelity, along with
    the error history to ensure revisions are progressing.
    """
    context = {
        "target_storyboard": ctx.storyboard.model_dump(mode="json")
        if ctx.storyboard
        else None,
        "visual_lexicon": {k: v.model_dump(mode="json") for k, v in ctx.lexicon.items()},
        "revision_history": [
            e.model_dump(mode="json")
            for e in ctx.error_buffer
            if e.agent in ["animator", "reviewer"]
        ],
    }
    return f"WORKFLOW_CONTEXT:\n{json.dumps(context, indent=2)}"
