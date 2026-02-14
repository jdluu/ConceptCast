"""Shared streaming helpers for agent runs. 
Standardizes streamed thoughts across providers/models."""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import (
    AgentRunResultEvent,
    PartDeltaEvent,
    ThinkingPartDelta,
)


async def run_agent_streamed(
    agent_name: str,
    agent: Any,
    prompt: str,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None,
    **run_kwargs: Any,
) -> Any:
    """Runs an agent with run_stream_events, emits thoughts 
    via on_thought, returns final output.

    Same pattern for every provider/model: stream text and thinking deltas to the UI.
    """
    final = None
    async for event in agent.run_stream_events(prompt, **run_kwargs):
        if isinstance(event, PartDeltaEvent) and hasattr(event.delta, "content_delta"):
            phase = (
                "thinking" if isinstance(event.delta, ThinkingPartDelta) else "output"
            )
            if on_thought and event.delta.content_delta:
                await on_thought(agent_name, phase, event.delta.content_delta)
        elif isinstance(event, AgentRunResultEvent):
            final = event.result.output
    return final
