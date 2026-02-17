"""Shared streaming helpers for agent runs.
Standardizes streamed thoughts across providers/models."""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    PartDeltaEvent,
    TextPartDelta,
    ThinkingPartDelta,
)
from pydantic_ai.usage import RunUsage


async def run_agent_streamed(
    agent_name: str,
    agent: Agent[Any, Any],
    prompt: Any,  # Use Any to satisfy the complex Union from run_stream_events
    on_thought: Callable[[str, str, str], Awaitable[None]] | None,
    accumulated_usage: RunUsage | None = None,
    **run_kwargs: Any,
) -> tuple[Any, RunUsage]:
    """Runs an agent with run_stream_events, emits thoughts via on_thought,
    and returns results.

    Args:
        agent_name: Logical name of the agent (for logging/UI).
        agent: The Pydantic AI agent instance to run.
        prompt: The input prompt or messages for the agent.
        on_thought: Async callback to handle streamed thinking/output parts.
        accumulated_usage: If provided, usage from this run will be added
            to this object.
        **run_kwargs: Additional parameters for the agent run.

    Returns:
        A tuple of (final_result, usage).
    """
    usage = RunUsage()
    final = None
    async for event in agent.run_stream_events(prompt, **run_kwargs):
        if isinstance(event, PartDeltaEvent):
            if (
                isinstance(event.delta, ThinkingPartDelta)
                and on_thought
                and event.delta.content_delta
            ):
                await on_thought(agent_name, "thinking", event.delta.content_delta)
            elif (
                isinstance(event.delta, TextPartDelta)
                and on_thought
                and event.delta.content_delta
            ):
                await on_thought(agent_name, "output", event.delta.content_delta)
        elif isinstance(event, AgentRunResultEvent):
            final = event.result.output
            usage = event.result.usage()

    if accumulated_usage:
        usage.incr(accumulated_usage)

    return final, usage
