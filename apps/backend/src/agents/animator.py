from typing import Optional

from pydantic_ai import Agent

from schemas import Storyboard

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
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
) -> str:
    """
    Translates a storyboard into executable Manim Python code.
    """
    agent = Agent(
        get_model(provider, model_id),
        system_prompt=system_prompt,
        output_type=str,
        deps_type=Storyboard,
    )

    # Register the advanced documentation tool
    agent.tool(search_manim_docs, prepare=prepare_manim_docs)

    prompt = f"Generate Manim code for this storyboard:\n{storyboard.model_dump_json()}"
    result = await agent.run(prompt, deps=storyboard)
    return result.data
