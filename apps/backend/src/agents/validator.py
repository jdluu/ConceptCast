from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent

from api.schemas import CurriculumPlan, ValidationResult

from .streaming import run_agent_streamed

# Define the Validator Agent
# "The Critic" - Ensures curricula are pedagogically sound.

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
    model: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
) -> ValidationResult:
    """
    Performs a pedagogical audit on a curriculum plan.
    Streams validator thoughts if on_thought is provided.
    """
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=ValidationResult,
    )
    prompt = f"Perform a pedagogical audit on this plan:\n{plan.model_dump_json()}"
    result = await run_agent_streamed("validator", agent, prompt, on_thought=on_thought)
    return result  # type: ignore
