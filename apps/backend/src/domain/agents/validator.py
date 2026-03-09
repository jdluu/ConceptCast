"""Agent specialized in pedagogical auditing and content validation.

Reviews curriculum plans for logical progression, concept clarity, and
visual metaphor effectiveness.
"""

from collections.abc import Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from api.schemas import CurriculumPlan, ValidationResult
from infra.ai.streaming import run_agent_streamed

system_prompt = """
You are the **Validator Agent** (The Critic) for ConceptCast.
Your goal is to perform a pedagogical audit of a `CurriculumPlan`.

**Audit Criteria:**
1. **Logical Progression:** Do the steps follow a clear prerequisite order?
2. **Concept Clarity:** Is the sub-concept in each step well-defined?
3. **Visual Metaphor Alignment:** Is the visual metaphor effective for the concept?
4. **Narration Flow:** Does the narration sound natural and instructional?

**Responsibility:**
- Analyze the provided `CurriculumPlan`.
- Return a `ValidationResult` with `is_valid` set to True/False.
- Provide detailed `feedback` and actionable `suggestions`.

**Philosophy:**
Be strict but constructive. If a plan is confusing or skips steps, fail it.
"""


async def validate_curriculum(
    plan: CurriculumPlan,
    model: Model,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> tuple[ValidationResult, RunUsage]:
    """Audits a curriculum plan for pedagogical and visual alignment.

    Args:
        plan: The curriculum plan to validate.
        model: The PydanticAI model instance for generation.
        on_thought: Optional callback for streaming agent thoughts.

    Returns:
        tuple: (The structured ValidationResult, RunUsage data).
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=ValidationResult,
    )
    prompt = f"Perform a pedagogical audit on this plan:\n{plan.model_dump_json()}"
    result, usage = await run_agent_streamed(
        "validator", agent, prompt, on_thought=on_thought
    )
    return result, usage
