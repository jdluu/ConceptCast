from pydantic_ai import Agent, RunContext

from api.schemas import CurriculumPlan, ValidationResult

from .factory import get_model
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
    provider: str | None = None,
    model_id: str | None = None,
) -> CurriculumPlan:
    """
    Generates a pedagogical curriculum plan for a given topic.

    Uses the Analyst Agent to deconstruct the topic into a sequence of
    teaching steps, each with a visual metaphor and narration.

    Args:
        topic (str): The main concept to explain.
        audience (str): The target audience knowledge level.
        provider (str | None): Optional explicit AI provider.
        model_id (str | None): Optional explicit AI model ID.

    Returns:
        CurriculumPlan: A structured plan containing teaching steps.
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

        Args:
            ctx (RunContext): The agent's execution context.
            plan (CurriculumPlan): The plan to validate.

        Returns:
            ValidationResult: Feedback and pedagogical scores.
        """
        return await validate_curriculum(plan)

    prompt = (
        f"Explain '{topic}' to a '{audience}' audience. "
        "Remember to consult the critic before finalizing your output."
    )
    result = await agent.run(prompt)
    return result.data  # type: ignore
