"""Shared streaming helpers for agent runs.
Standardizes streamed thoughts across providers/models."""

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pydantic_ai import Agent, AgentRunResultEvent
from pydantic_ai.messages import (
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
)
from pydantic_ai.usage import RunUsage


async def run_agent_streamed(
    agent_name: str,
    agent: Agent[Any, Any],
    prompt: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None,
    accumulated_usage: RunUsage | None = None,
    **run_kwargs: Any,
) -> tuple[Any, RunUsage]:
    """Runs an agent and streams intermediate thoughts and final output.

    Standardizes the handling of 'thinking' and 'output' deltas across
    different AI models and providers.

    Args:
        agent_name: Logical identifier for the agent (e.g., 'analyst').
        agent: The PydanticAI Agent instance.
        prompt: Input string or list of messages.
        on_thought: Async callback receiving (agent, phase, content).
        accumulated_usage: External usage object to increment.
        **run_kwargs: Passed directly to `agent.run_stream_events`.

    Returns:
        A tuple containing the final parsed output and the total run usage.
    """
    usage = RunUsage()
    final = None
    tool_names: dict[int, str] = {}

    async for event in agent.run_stream_events(prompt, **run_kwargs):
        logger.trace(f"Agent Event: {type(event).__name__}")
        if isinstance(event, PartStartEvent):
            if isinstance(event.part, ToolCallPart):
                tool_names[event.index] = event.part.tool_name
            elif (
                isinstance(event.part, ThinkingPart)
                and on_thought
                and event.part.content
            ):
                await on_thought(agent_name, "thinking", event.part.content)
            elif (
                isinstance(event.part, TextPart)
                and on_thought
                and event.part.content
            ):
                await on_thought(agent_name, "output", event.part.content)
        elif isinstance(event, PartDeltaEvent):
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
            elif isinstance(event.delta, ToolCallPartDelta) and on_thought:
                tool_name = tool_names.get(event.index, "unknown_tool")
                # Only notify once per tool call start if possible,
                # but since this is a delta, we might want to only notify on the first delta.
                # For simplicity, we'll notify that the tool is being invoked.
                # To avoid spamming, we can check if we already notified for this index.
                if tool_name != "notified":
                    await on_thought(
                        agent_name,
                        "tool_call",
                        f"Invoking tool: {tool_name}...",
                    )
                    tool_names[event.index] = "notified"
        elif isinstance(event, AgentRunResultEvent):
            final = event.result.output
            usage = event.result.usage()

    if accumulated_usage:
        usage.incr(accumulated_usage)

    return final, usage
