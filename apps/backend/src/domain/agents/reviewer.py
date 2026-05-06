"""Agent specialized in visual quality assurance and iterative review.

Compares rendered outputs or execution logs against storyboards to ensure
correctness, readability, and alignment with pedagogical goals.
"""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import structlog
from pydantic_ai import Agent
from pydantic_ai.messages import BinaryContent
from pydantic_ai.usage import RunUsage

from api.schemas import AnimationReview, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed
from infra.ai.tools import prepare_manim_docs, search_manim_docs
from services.workflow.context_injectors import extract_reviewer_context

logger = structlog.get_logger(__name__)

system_prompt = load_prompt("reviewer")


async def review_animation(
    storyboard: Storyboard,
    frame_path: Path | None,
    execution_logs: str,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
) -> tuple[AnimationReview, RunUsage]:
    """Compares rendered output against the storyboard for visual fidelity.

    Uses vision/log analysis (and docs lookup when needed) to approve or request
    revisions for generated animations.

    Args:
        storyboard: The target visual sequence the animation should reproduce.
        frame_path: Optional path to a rendered PNG frame for vision analysis.
        execution_logs: Combined stdout/stderr from the Manim render process.
        model: ConceptCast model instance for the review.
        on_thought: Optional callback for real-time thought streaming.
        ctx: The Global Context Object (GCO) for the workflow.

    Returns:
        tuple: (Structured AnimationReview decision, RunUsage data).
    """
    agent = Agent(
        model.model,
        system_prompt=system_prompt,
        output_type=AnimationReview,
        deps_type=GlobalContext,
        retries=3,
    )
    agent.tool(prepare=prepare_manim_docs)(search_manim_docs)

    prompt_parts = [
        "**Perform a Visual QA Review**",
        f"**Execution Logs**:\n```\n{execution_logs}\n```",
    ]

    if ctx:
        prompt_parts.append(extract_reviewer_context(ctx))
    else:
        prompt_parts.append(
            f"**Expected Storyboard**:\n{storyboard.model_dump_json(indent=2)}"
        )

    content_with_images = []
    if frame_path and frame_path.exists():
        prompt_parts.append(
            "**Rendered Frame**: Attached. Please analyze the visual layout, "
            "text readability, and alignment with the storyboard."
        )
        content_with_images.append(str(frame_path))
    else:
        prompt_parts.append("**Rendered Frame**: Not available (Log-based review only)")

    prompt = "\n\n".join(prompt_parts)

    final_prompt: Any = prompt
    if content_with_images and frame_path and model.is_multimodal:
        try:
            with Path(frame_path).open("rb") as f:
                image_data = f.read()
            final_prompt = [
                prompt,
                BinaryContent(data=image_data, media_type="image/png"),
            ]
        except Exception as e:
            logger.warning(
                "frame_image_read_failed",
                error=str(e),
                frame_path=str(frame_path),
            )

    result, usage = await run_agent_streamed(
        "reviewer",
        agent,
        final_prompt,
        on_thought=on_thought,
        deps=ctx,
    )
    return result, usage
