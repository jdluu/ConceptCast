"""Agent specialized in curriculum planning and pedagogical deconstruction.

Uses self-correction via a critic tool to ensure the generated learning
dependency graph is logical and effective for the target audience.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, ValidationResult
from domain.agents.validator import validate_curriculum
from infra.ai.streaming import run_agent_streamed

system_prompt = """
You are the **Analyst Agent** (The Pedagogue) for ConceptCast.
Your goal is deconstructing complex technical topics into a clear, 
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
    model: Model,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> tuple[CurriculumPlan, RunUsage]:
    """Generates a pedagogical curriculum plan for a given topic.

    Args:
        topic: The complex technical topic to deconstruct.
        audience: The target knowledge level of the audience.
        model: The PydanticAI model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.

    Returns:
        tuple: (The structured CurriculumPlan, RunUsage data).
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=CurriculumPlan,
    )

    @agent.tool
    async def consult_critic(
        _ctx: RunContext[None], plan: CurriculumPlan
    ) -> ValidationResult:
        """Consults the Validator Agent to review the generated curriculum plan.

        Args:
            ctx: The run context.
            plan: The curriculum plan to validate.

        Returns:
            The validation result from the reviewer.
        """
        res, _ = await validate_curriculum(plan, model, on_thought=on_thought)
        return res

    prompt = (
        f"Explain '{topic}' to a '{audience}' audience. "
        "Remember to consult the critic before finalizing your output."
    )
    result, usage = await run_agent_streamed(
        "analyst", agent, prompt, on_thought=on_thought
    )
    return result, usage
