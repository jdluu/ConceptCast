from typing import Optional

from pydantic_ai import Agent

from schemas import CurriculumPlan, Storyboard

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
    plan: CurriculumPlan, provider: Optional[str] = None, model_id: Optional[str] = None
) -> Storyboard:
    """
    Translates a curriculum plan into a visual storyboard.
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
    return result.data
