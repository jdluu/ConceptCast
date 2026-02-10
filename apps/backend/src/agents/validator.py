from typing import Optional

from pydantic_ai import Agent

from schemas import CurriculumPlan, ValidationResult

from .factory import get_model

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

validator_agent = Agent(
    get_model(),
    system_prompt=system_prompt,
    output_type=ValidationResult,
)


async def validate_curriculum(
    plan: CurriculumPlan, provider: Optional[str] = None, model_id: Optional[str] = None
) -> ValidationResult:
    """
    Performs a pedagogical audit on a curriculum plan.
    """
    # Use the specific model if provided
    agent = validator_agent
    if provider or model_id:
        agent = Agent(
            get_model(provider, model_id),
            system_prompt=system_prompt,
            output_type=ValidationResult,
        )

    prompt = f"Perform a pedagogical audit on this plan:\n{plan.model_dump_json()}"
    result = await agent.run(prompt)
    return result.data
