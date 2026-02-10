from typing import Optional

from pydantic_ai import Agent, RunContext

from schemas import CurriculumPlan

from .factory import get_model
from .validator import ValidationResult, validator_agent

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
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
) -> CurriculumPlan:
    """
    Generates a curriculum plan for a given topic and audience.
    """
    agent = Agent(
        get_model(provider, model_id),
        system_prompt=system_prompt,
        output_type=CurriculumPlan,
    )

    @agent.tool
    async def consult_critic(
        ctx: RunContext[None], plan: CurriculumPlan
    ) -> ValidationResult:
        """
        Consults the Validator Agent (The Critic) to audit the curriculum plan.
        Returns pedagogical feedback and suggestions.
        """
        prompt = f"Perform a pedagogical audit on this plan:\n{plan.model_dump_json()}"
        # Delegate to the validator agent
        result = await validator_agent.run(prompt)
        return result.data

    prompt = (
        f"Explain '{topic}' to a '{audience}' audience. "
        "Remember to consult the critic before finalizing your output."
    )
    result = await agent.run(prompt)
    return result.data
