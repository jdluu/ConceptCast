"""Agent specialized in visual quality assurance and iterative review.

Compares rendered outputs or execution logs against storyboards to ensure
correctness, readability, and alignment with pedagogical goals.
"""

from collections.abc import Awaitable, Callable
from pathlib import Path

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.messages import BinaryContent, ModelRequestPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from api.schemas import AnimationReview, Storyboard
from infra.ai.streaming import run_agent_streamed
from infra.ai.tools import lint_manim_code, prepare_manim_docs, search_manim_docs

system_prompt = """
You are the **Reviewer Agent** (Visual QA) for ConceptCast.
Your goal is to verify that a generated Manim animation matches the intended storyboard.

**Inputs:**
1. **Storyboard:** The expected visual sequence and narration.
2. **Execution Logs:** The stdout/stderr from the Manim rendering process.
3. **Frame Image:** (Optional) A rendered frame from the animation.

**Review Process:**
1. **Code Validation:** Use the `lint_manim_code` tool to check for syntax errors 
   and common pitfalls (like invalid color names). 
   - DO NOT approve code with lowercase color strings (e.g., "brown"). 
   - Ensure color constants are uppercase (e.g., BROWN).
2. **Authoritative Docs:** Use the `search_manim_docs` tool to verify parameters 
   and color constants if you are unsure.
3. **Log Analysis:** Check the logs for:
   - Python errors or warnings.
   - Manim warnings (e.g., "Mobject not in scene").
   - LaTeX compilation errors.
4. **Visual Verification:** (If frame provided, otherwise infer from logs/storyboard)
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
    model: Model,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> tuple[AnimationReview, RunUsage]:
    """Compares rendered output against the storyboard for visual fidelity.

    Uses sandbox-based linting and vision/log analysis to approve or request
    revisions for generated animations.

    Args:
        storyboard: The target visual sequence the animation should reproduce.
        frame_path: Optional path to a rendered PNG frame for vision analysis.
        execution_logs: Combined stdout/stderr from the Manim render process.
        model: PydanticAI model instance for the review.
        on_thought: Optional callback for real-time thought streaming.

    Returns:
        tuple: (Structured AnimationReview decision, RunUsage data).
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=AnimationReview,
        deps_type=Storyboard,
    )
    agent.tool(lint_manim_code)
    agent.tool(search_manim_docs, prepare=prepare_manim_docs)  # type: ignore

    prompt_parts = [
        "**Perform a Visual QA Review**",
        f"**Execution Logs**:\n```\n{execution_logs}\n```",
    ]

    content_with_images = []
    if frame_path and frame_path.exists():
        prompt_parts.append(
            "**Rendered Frame**: Attached. Please analyze the visual layout, "
            "text readability, and alignment with the storyboard."
        )
        content_with_images.append(str(frame_path))
    else:
        prompt_parts.append("**Rendered Frame**: Not available (Log-based review only)")

    prompt_parts.append(
        f"**Expected Storyboard**:\n{storyboard.model_dump_json(indent=2)}"
    )

    prompt = "\n\n".join(prompt_parts)

    final_prompt: str | list[ModelRequestPart] = prompt
    if content_with_images and frame_path:
        try:
            with Path(frame_path).open("rb") as f:
                image_data = f.read()
            final_prompt = [
                UserPromptPart(content=prompt),
                UserPromptPart(
                    content=[BinaryContent(data=image_data, media_type="image/png")]
                ),
            ]
        except Exception as e:
            logger.warning(f"Failed to read frame image for vision: {e}")

    result, usage = await run_agent_streamed(
        "reviewer",
        agent,
        final_prompt,
        on_thought=on_thought,
        deps=storyboard,
    )
    return result, usage
