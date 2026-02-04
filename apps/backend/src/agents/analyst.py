from pydantic_ai import Agent

from schemas import CurriculumPlan

# Define the Analyst Agent
# "The Pedagogue" - Deconstructs topics into pedagogical steps.

system_prompt = """
You are the **Analyst Agent** (The Pedagogue) for ConceptCast.
Your goal is to deconstruct complex technical topics into a clear, 
sequential dependency graph for visual learning.

**Philosophy:**
- You do NOT provide answers directly. You show the *derivation*.
- Use "The Whiteboard Standard": Clear, sequential logic. No flashy cinematics.
- Focus on *visual metaphors* that map abstract math/logic to concrete 
  physical interactions.

**Output:**
- You must generate a `CurriculumPlan` containing a series of `TeachingStep`s.
- Ensure the steps are logically ordered (prerequisites first).
"""

analyst_agent = Agent(
    "google-gla:gemini-1.5-pro",
    system_prompt=system_prompt,
    output_type=CurriculumPlan,
)


async def generate_curriculum(topic: str, audience: str) -> CurriculumPlan:
    """
    Generates a curriculum plan for a given topic and audience.

    Args:
        topic: The subject matter to explain.
        audience: The target audience level.

    Returns:
        CurriculumPlan: A structured plan containing teaching steps.
    """
    prompt = f"Explain '{topic}' to a '{audience}' audience."
    result = await analyst_agent.run(prompt)
    return result.data
