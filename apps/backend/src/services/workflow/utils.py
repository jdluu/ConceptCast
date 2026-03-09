from pydantic_ai.usage import RunUsage

from infra.settings import get_settings


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
    )


def calculate_job_cost(
    usage: RunUsage | None = None, render_duration: float = 0.0
) -> float:
    """Combines LLM token usage costs with infrastructure and rendering costs.

    Args:
        usage (Usage | None, optional): A usage object from the AI provider containing
            'request_tokens' and 'response_tokens'. Defaults to None.
        render_duration (float): Duration of the rendered video in seconds.
            Used to calculate rendering compute costs. Defaults to 0.0.

    Returns:
        float: Total estimated job cost in USD, rounded to two decimal places.
    """
    settings = get_settings()

    token_cost = 0.0
    if usage:
        prompt_tokens = usage.request_tokens or 0
        completion_tokens = usage.response_tokens or 0
        token_cost = (prompt_tokens * settings.pricing_input_rate) + (
            completion_tokens * settings.pricing_output_rate
        )

    # Rendering Pricing
    render_cost = (render_duration / 60.0) * settings.pricing_render_rate_per_min

    # Base overhead (Model instantiation / Sandbox startup)
    base_cost = settings.pricing_base_overhead if usage or render_duration > 0 else 0.0

    return round(token_cost + render_cost + base_cost, 2)
