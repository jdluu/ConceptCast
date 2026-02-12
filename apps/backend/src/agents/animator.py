import json

from pydantic_ai import Agent

from api.schemas import Storyboard

from .factory import get_model
from .tools import prepare_manim_docs, search_manim_docs

system_prompt = """
You are the **Animator Agent** for ConceptCast.
Your goal is to transform a visual `Storyboard` into production-ready Python code 
using the **Manim Community** library.

**Rules:**
1. **Header:** Always start with `from manim import *`.
2. **Class Definition:** Create a single class named `SceneGen` 
   inheriting from `Scene`.
3. **Construct Method:** All animation logic must be within 
   the `construct(self)` method.
4. **Pedagogy First:** Ensure animations are slow, clear, 
   and follow the storyboard sequence.
5. **Syntax Verification:** Use the `search_manim_docs` tool to verify the syntax 
   for any Manim objects (e.g., Axes, Dot, FadeIn) before writing the final code.
6. **No Hallucinations:** High-quality valid code is more important than 
   visual complexity.

**Output:**
- You must return ONLY the raw Python code as a string.
"""


async def generate_manim_code(
    storyboard: Storyboard,
    provider: str | None = None,
    model_id: str | None = None,
) -> str:
    """
    Translates a storyboard into executable Manim Python code.

    Uses the Animator Agent to generate Python code that renders the
    storyboard using the Manim library.

    Args:
        storyboard (Storyboard): The visual plan to animate.
        provider (str | None): Optional explicit AI provider.
        model_id (str | None): Optional explicit AI model ID.

    Returns:
        str: The raw Python code implementing the animation.
    """
    animator_agent = Agent(
        get_model(provider, model_id),
        system_prompt=system_prompt,
        output_type=str,
        deps_type=Storyboard,
    )

    # Register the advanced documentation tool
    animator_agent.tool(search_manim_docs, prepare=prepare_manim_docs)  # type: ignore

    result = await animator_agent.run(
        f"Write Manim code for: {json.dumps(storyboard.model_dump())}", deps=storyboard
    )
    return result.data  # type: ignore
