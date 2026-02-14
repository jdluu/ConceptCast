import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent

from api.schemas import Storyboard

from .streaming import run_agent_streamed
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

**Critical Manim API Rules:**
- **DO NOT** pass `opacity` as a keyword argument to mobject 
  constructors (Line, Circle, etc.). Use `.set_opacity(value)` after creation.
- **DO NOT** pass `stroke_width` to constructors that don't accept it. 
  Use `.set_stroke(width=...)` instead.
- **DO NOT** pass `fill_opacity` or `stroke_opacity` to constructors. 
  Use `.set_fill(opacity=...)` or `.set_stroke(opacity=...)` instead.
- **ALWAYS** verify parameter names using `search_manim_docs` before 
  using any Manim object.
- Use `.set_color()`, `.set_fill()`, `.set_stroke()` methods for styling, 
  not constructor kwargs unless the docs explicitly show them.

**Output:**
- You must return ONLY the raw Python code as a string.
- No markdown code fences (no ```python or ```).
"""


async def generate_manim_code(
    storyboard: Storyboard,
    model: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
) -> str:
    """
    Translates a storyboard into executable Manim Python code.
    Streams animator thoughts if on_thought is provided.
    retry_hint: If set, appended to the prompt (e.g. after a validation failure).
    """
    animator_agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=str,
        deps_type=Storyboard,
    )
    animator_agent.tool(search_manim_docs, prepare=prepare_manim_docs)

    prompt = f"Write Manim code for: {json.dumps(storyboard.model_dump())}"
    if retry_hint:
        prompt = f"{prompt}\n\nIMPORTANT: {retry_hint}"
    result = await run_agent_streamed(
        "animator",
        animator_agent,
        prompt,
        on_thought=on_thought,
        deps=storyboard,
    )
    return result  # type: ignore
