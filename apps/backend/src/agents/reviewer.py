from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from pydantic_ai import Agent

from api.schemas import AnimationReview, Storyboard

from .streaming import run_agent_streamed

system_prompt = """
You are the **Reviewer Agent** (Visual QA) for ConceptCast.
Your goal is to verify that a generated Manim animation matches the intended storyboard.

**Inputs:**
1. **Storyboard:** The expected visual sequence and narration.
2. **Execution Logs:** The stdout/stderr from the Manim rendering process.
3. **Frame Image:** (Optional) A rendered frame from the animation.

**Review Process:**
1. **Log Analysis:** Check the logs for:
   - Python errors or warnings.
   - Manim warnings (e.g., "Mobject not in scene").
   - LaTeX compilation errors.
2. **Visual Verification:** (If frame provided, otherwise infer from logs/storyboard)
   - Did the code run successfully?
   - Does the content match the storyboard description?
   - Are there any layout issues (overlapping text, off-screen elements)?

**Output:**
Return an `AnimationReview` object:
- `approved`: True if the animation is acceptable 
  (visually correct + no critical errors).
- `issues`: A list of specific problems found (e.g., "LaTeX error", "Text overlaps").
- `revision_instructions`: Clear instructions for the Animator Agent to fix the issues. 
   If approved, this can be empty or a compliment.

**Philosophy:**
- Be pedantic about errors. A crashing animation is a failed animation.
- Be helpful to the Animator. Don't just say "it failed", 
  say "fix the LaTeX error in scene 2".
"""


async def review_animation(
    storyboard: Storyboard,
    frame_path: Path | None,
    execution_logs: str,
    model: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> AnimationReview:
    """
    Validates a generated animation against the storyboard and execution logs.
    Streams reviewer thoughts if on_thought is provided.
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=AnimationReview,
        deps_type=Storyboard,
    )

    # Construct the review prompt
    prompt_parts = [
        "**Perform a Visual QA Review**",
        f"**Execution Logs**:\n```\n{execution_logs}\n```",
    ]

    if frame_path:
        prompt_parts.append(
            f"**Rendered Frame**: [Image at {frame_path}] "
            "(Vision analysis not yet implemented)"
        )
    else:
        prompt_parts.append("**Rendered Frame**: Not available (Log-based review only)")

    prompt_parts.append(
        f"**Expected Storyboard**:\n{storyboard.model_dump_json(indent=2)}"
    )

    prompt = "\n\n".join(prompt_parts)

    result = await run_agent_streamed(
        "reviewer",
        agent,
        prompt,
        on_thought=on_thought,
        deps=storyboard,
    )
    return result  # type: ignore
