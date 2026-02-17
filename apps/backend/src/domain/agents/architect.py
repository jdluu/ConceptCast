from collections.abc import Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, Storyboard
from infra.ai.streaming import run_agent_streamed

# Define the Visual Architect Agent
# "The Scenographer" - Translates pedagogy into visual scenes.

system_prompt = """
You are the **Visual Architect Agent** (The Scenographer) for ConceptCast.
Your goal is to transform a `CurriculumPlan` into a detailed `Storyboard`.

**Responsibility:**
- For each `TeachingStep` in the plan, create one or more `Scene`s.
- Translate abstract concepts and visual metaphors into concrete `VisualObject`s 
  that can be rendered using the Manim engine.
- Assign appropriate Manim types (e.g., 'Axes', 'FunctionGraph', 'Dot', 'Text', 'Arrow')
  and positions.
- Ensure the visual flow is consistent and easy to follow.

**Manim Position Reference:**
- Use constants like 'ORIGIN', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'UL', 'UR', 'DL', 'DR'.
- Combine them with multiplication (e.g., 'UP * 2 + LEFT * 3').

**Output:**
- You must generate a `Storyboard` object.
"""


async def generate_storyboard(
    plan: CurriculumPlan,
    model: Model,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> tuple[Storyboard, RunUsage]:
    """Translates a curriculum plan into a visual storyboard.

    Args:
        plan: The pedagogically sound curriculum plan.
        model: The PydanticAI model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.

    Returns:
        tuple[Storyboard, RunUsage]: The structured storyboard and AI usage data.
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=Storyboard,
    )
    prompt = (
        f"Create a storyboard for the following curriculum:\n{plan.model_dump_json()}"
    )
    result, usage = await run_agent_streamed(
        "architect", agent, prompt, on_thought=on_thought
    )
    return result, usage
