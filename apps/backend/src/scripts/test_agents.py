"""Diagnostic script to verify agent intelligence and event streaming.

Tests the low-level Pydantic AI event loop for all council agents to ensure
thinking and output parts are correctly emitted and captured.
"""

import asyncio
import contextlib
import sys
from typing import Any

from loguru import logger
from pydantic_ai import Agent

from api.schemas import AnimationReview, CurriculumPlan, Storyboard, ValidationResult
from infra.ai.mock import RealisticMockModel
from infra.ai.streaming import run_agent_streamed


async def test_agent_logic(
    agent_name: str, 
    system_prompt: str, 
    output_type: type, 
    topic: str = "Linear Algebra"
) -> bool:
    """Simulates a single agent run and validates the event stream."""
    logger.info(f"--- Testing {agent_name.upper()} Agent ---")
    
    model = RealisticMockModel()
    agent = Agent(
        model,
        system_prompt=system_prompt,
        output_type=output_type,
    )
    
    # We use a simple prompt that will trigger the mock model
    prompt = f"Explain '{topic}'"
    
    captured_thoughts = []
    captured_output_chunks = 0
    
    async def on_thought(_name: str, phase: str, content: str) -> None:
        if phase == "thinking":
            captured_thoughts.append(content)
        elif phase == "output":
            nonlocal captured_output_chunks
            captured_output_chunks += 1

    # Add dependencies if needed by the agent
    kwargs: dict[str, Any] = {}
    if agent_name in {"validator", "architect"}:
        kwargs["deps"] = CurriculumPlan(concept_title=topic, target_audience="Beginner", teaching_steps=[])
    elif agent_name == "reviewer":
        kwargs["deps"] = Storyboard(concept_title=topic, scenes=[])

    result, usage = await run_agent_streamed(
        agent_name, 
        agent, 
        prompt, 
        on_thought=on_thought,
        **kwargs
    )
    
    # Assertions
    if not captured_thoughts:
        logger.error(f"FAIL: {agent_name} emitted NO thinking parts.")
        return False
    
    if not result:
        logger.error(f"FAIL: {agent_name} produced NO final result.")
        return False

    # Structural Validation
    if agent_name == "validator" and not isinstance(result, ValidationResult):
        logger.error(f"FAIL: {agent_name} result is not a ValidationResult.")
        return False
    if agent_name == "architect" and (not isinstance(result, Storyboard) or len(result.scenes) == 0):
        logger.error(f"FAIL: {agent_name} produced an empty or invalid Storyboard.")
        return False

    logger.success(f"PASS: {agent_name} verified. ({len(captured_thoughts)} thought blocks)")
    return True


async def run_diagnostics() -> None:
    """Runs a full suite of agent diagnostics."""
    logger.info("Starting Council Intelligence Diagnostics...")
    
    tests = [
        ("analyst", "Analyst Agent", CurriculumPlan),
        ("validator", "Validator Agent", ValidationResult),
        ("architect", "Architect Agent", Storyboard),
        ("animator", "Animator Agent", str),
        ("reviewer", "Reviewer Agent", AnimationReview),
    ]
    
    results = []
    for name, prompt, out_type in tests:
        success = await test_agent_logic(name, prompt, out_type)
        results.append(success)
        await asyncio.sleep(0.2) # Small delay for readability
        
    if all(results):
        logger.success("\nAll Agent Intelligence Tests Passed!")
    else:
        logger.error("\nSome diagnostic tests failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_diagnostics())
