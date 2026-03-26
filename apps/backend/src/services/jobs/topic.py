"""Service for refining and interpreting user prompts into concise topics.
"""

import structlog
from pydantic_ai import Agent

from infra.ai.base import BaseConceptModel, load_prompt

logger = structlog.get_logger(__name__)

system_prompt = load_prompt("topic_refiner")


async def refine_topic(user_prompt: str, model: BaseConceptModel) -> str:
    """Uses an LLM to transform a raw user prompt into a concise topic title.

    Args:
        user_prompt: The raw prompt from the user.
        model: The ConceptCast model to use for refinement.

    Returns:
        str: A concise, professional title.
    """
    try:
        agent = Agent(
            model.model,
            system_prompt=system_prompt,
            retries=2,
        )

        result = await agent.run(user_prompt)
        refined = result.data.strip()

        # Sanity check: if it's too long or empty, fallback to raw prompt
        if not refined or len(refined.split()) > 10:
            logger.warning(
                "topic_refinement_unusual_output",
                raw=user_prompt,
                refined=refined,
            )
            return user_prompt[:100]

        return refined
    except Exception as e:
        logger.error("topic_refinement_failed", error=str(e), raw=user_prompt)
        # Fallback to a truncated version of the raw prompt
        return user_prompt[:100]
