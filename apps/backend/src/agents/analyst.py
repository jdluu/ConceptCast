from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent, RunContext

from api.schemas import CurriculumPlan, ValidationResult

from .streaming import run_agent_streamed
from .validator import validate_curriculum

# Define the Analyst Agent
# "The Pedagogue" - Deconstructs topics into pedagogical steps.

system_prompt = """
You are the **Analyst Agent** (The Pedagogue) for ConceptCast.
Your goal is to deconstruct complex technical topics into a clear, 
sequential dependency graph for visual learning.

**Responsibility:**
- Create a `CurriculumPlan` with logical `TeachingStep`s.
- Each step must have a `concept`, a `visual_metaphor`, and `narration`.
- **Self-Correction:** Use the `consult_critic` tool to validate your plan 
  before confirming it.
- If the critic provides negative feedback, refine your plan and consult them again.
- Only return the final `CurriculumPlan` once you are confident 
  it is pedagogically sound.
"""


async def generate_curriculum(
    topic: str,
    audience: str,
    model: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> CurriculumPlan:
    """
    Generates a pedagogical curriculum plan for a given topic.
    Streams analyst (and validator, when critic is called) thoughts 
    if on_thought is provided.
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=CurriculumPlan,
    )

    @agent.tool
    async def consult_critic(
        ctx: RunContext[None], plan: CurriculumPlan
    ) -> ValidationResult:
        return await validate_curriculum(plan, model, on_thought=on_thought)

    prompt = (
        f"Explain '{topic}' to a '{audience}' audience. "
        "Remember to consult the critic before finalizing your output."
    )
    result = await run_agent_streamed("analyst", agent, prompt, on_thought=on_thought)
    return result  # type: ignore
