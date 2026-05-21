import json
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic_ai.usage import RunUsage

from infra.settings import get_settings

T = TypeVar("T", bound=BaseModel)


def parse_job_artifact(data: Any, model_class: type[T]) -> T:
    """Parses a job artifact from either a dict or a JSON string.

    Commonly used when retrieving JSON/JSONB columns from different DB backends.

    Args:
        data: The raw data from the database.
        model_class: The Pydantic model class to parse into.

    Returns:
        An instance of the specified Pydantic model.
    """
    if isinstance(data, dict):
        return model_class(**data)
    if isinstance(data, str):
        return model_class(**json.loads(data))
    raise ValueError(
        f"Expected dict or str for {model_class.__name__}, got {type(data)}"
    )


def merge_usage(base: RunUsage | None, extra: RunUsage | None) -> RunUsage:
    """Aggregates two token usage objects by summing their various counts.

    Args:
        base: The primary usage object to accumulate into.
        extra: The additional usage to add.

    Returns:
        A new RunUsage instance representing the combined usage.
    """
    if not base:
        return extra or RunUsage()
    if not extra:
        return base

    return RunUsage(
        input_tokens=(base.input_tokens or 0) + (extra.input_tokens or 0),
        output_tokens=(base.output_tokens or 0) + (extra.output_tokens or 0),
        requests=(base.requests or 0) + (extra.requests or 0),
    )


def calculate_job_cost(
    usage: RunUsage | None = None, render_duration: float = 0.0
) -> float:
    """Combines LLM token usage costs with infrastructure and rendering costs.

    Args:
        usage: A usage object from the AI provider containing token counts.
        render_duration: Duration of the rendered video in seconds.

    Returns:
        Total estimated job cost in USD, rounded to two decimal places.
    """
    settings = get_settings()

    token_cost = 0.0
    if usage:
        prompt_tokens = usage.input_tokens or 0
        completion_tokens = usage.output_tokens or 0
        token_cost = (prompt_tokens * settings.pricing_input_rate) + (
            completion_tokens * settings.pricing_output_rate
        )

    # Rendering Pricing
    render_cost = (render_duration / 60.0) * settings.pricing_render_rate_per_min

    # Base overhead (Model instantiation / Sandbox startup)
    base_cost = settings.pricing_base_overhead if usage or render_duration > 0 else 0.0

    return round(token_cost + render_cost + base_cost, 2)


def apply_search_replace_patch(original_code: str, patch_content: str) -> str:
    """Parses Search-and-Replace blocks from patch_content and applies them to original_code."""
    import re

    pattern = re.compile(
        r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.DOTALL
    )

    matches = pattern.findall(patch_content)
    if not matches:
        # Fallback: if no search/replace block is found, assume the model outputted full corrected code
        return patch_content

    modified_code = original_code
    import structlog

    logger = structlog.get_logger(__name__)

    for search_block, replace_block in matches:
        search_block_stripped = search_block.strip()
        # Find exact matches
        if search_block_stripped in modified_code:
            modified_code = modified_code.replace(
                search_block_stripped, replace_block.strip()
            )
        elif search_block in modified_code:
            modified_code = modified_code.replace(search_block, replace_block)
        else:
            logger.warning(
                "patch_search_block_not_matched",
                search_block=search_block_stripped,
            )

    return modified_code
