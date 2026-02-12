
from pydantic_ai import Agent

from api.schemas import CurriculumPlan, Storyboard

from .factory import get_model

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
    plan: CurriculumPlan, provider: str | None = None, model_id: str | None = None
) -> Storyboard:
    """
    Translates a curriculum plan into a visual storyboard.

    Uses the Architect Agent to map teaching steps into concrete Manim scenes
    and visual objects.

    Args:
        plan (CurriculumPlan): The pedagogical plan to visualize.
        provider (str | None): Optional explicit AI provider.
        model_id (str | None): Optional explicit AI model ID.

    Returns:
        Storyboard: A structured list of scenes and visual objects.
    """
    agent = Agent(
        get_model(provider, model_id),
        system_prompt=system_prompt,
        output_type=Storyboard,
    )
    prompt = (
        f"Create a storyboard for the following curriculum:\n{plan.model_dump_json()}"
    )
    result = await agent.run(prompt)
    return result.data  # type: ignore
