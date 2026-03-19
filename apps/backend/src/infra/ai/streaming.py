"""Shared streaming helpers for agent runs.
Standardizes streamed thoughts across providers/models."""

import json
from collections.abc import Awaitable, Callable
from typing import Any, cast

import structlog
from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent, AgentRunResultEvent, exceptions
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

logger = structlog.get_logger(__name__)


async def run_agent_streamed(  # noqa: C901, PLR0912, PLR0915
    agent_name: str,
    agent: Agent[Any, Any],
    prompt: Any,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None,
    *,
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
    final: Any = None
    tool_names: dict[int, str] = {}
    # Some models/providers emit the same `final_result` tool-call multiple times
    # during structured-output completion. We only want to show the "commit" once
    # to avoid log spam (the actual structured payload is emitted separately).
    final_result_commit_emitted = False

    def _tool_phase(tool_name: str) -> str:
        """Normalizes thought phase names for tool-call observability.

        `final_result` is emitted by structured-output runs and is not a user
        tool lookup. Tagging it separately keeps E2E logs interpretable.
        """
        return "structured_output" if tool_name == "final_result" else "tool_call"

    def _tool_message(tool_name: str) -> str:
        if tool_name == "final_result":
            return "Structured output commit: final_result\n"
        return f"Invoking tool: {tool_name}...\n"

    def _serialize_structured_output(payload: Any) -> str:
        """Serializes structured output for observability streaming."""
        if payload is None:
            return ""
        if isinstance(payload, BaseModel):
            return payload.model_dump_json(indent=2)
        model_dump_json = getattr(payload, "model_dump_json", None)
        if callable(model_dump_json):
            return str(model_dump_json(indent=2))
        try:
            return json.dumps(payload, default=str, indent=2)
        except Exception:
            return str(payload)

    try:
        async for event in agent.run_stream_events(prompt, **run_kwargs):
            logger.debug(
                "agent_stream_event",
                agent_name=agent_name,
                event_type=type(event).__name__,
            )
            if isinstance(event, PartStartEvent):
                if isinstance(event.part, ToolCallPart):
                    tool_name = event.part.tool_name
                    tool_names[event.index] = tool_name
                    if on_thought:
                        if tool_name == "final_result":
                            if not final_result_commit_emitted:
                                phase = _tool_phase(tool_name)
                                await on_thought(
                                    agent_name, phase, _tool_message(tool_name)
                                )
                                final_result_commit_emitted = True
                            # Mark as notified immediately to avoid duplicate from Delta
                            tool_names[event.index] = "notified"
                        else:
                            phase = _tool_phase(tool_name)
                            await on_thought(
                                agent_name, phase, _tool_message(tool_name)
                            )
                            # Mark as notified immediately to avoid duplicate from Delta
                            tool_names[event.index] = "notified"
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
                    if tool_name != "notified":
                        phase = _tool_phase(tool_name)
                        await on_thought(
                            agent_name,
                            phase,
                            _tool_message(tool_name),
                        )
                        tool_names[event.index] = "notified"

                    if event.delta.args_delta and tool_name != "notified":
                        arg_str = (
                            event.delta.args_delta
                            if isinstance(event.delta.args_delta, str)
                            else json.dumps(event.delta.args_delta)
                        )
                        phase = _tool_phase(tool_name)
                        await on_thought(agent_name, phase, arg_str)
            elif isinstance(event, AgentRunResultEvent):
                final = event.result.output
                usage = event.result.usage()
                if on_thought and final is not None:
                    payload_json = _serialize_structured_output(final)
                    if payload_json:
                        await on_thought(
                            agent_name,
                            "structured_output",
                            f"Structured output result:\n{payload_json}\n",
                        )
    except exceptions.UnexpectedModelBehavior as e:
        logger.error(
            "agent_unexpected_model_behavior",
            agent_name=agent_name,
            error=str(e),
        )
        raise ValueError(
            f"Model failed output validation after multiple retries: {e}"
        ) from e
    except ValidationError as e:
        logger.error(
            "agent_invalid_output_format",
            agent_name=agent_name,
            error=str(e),
        )
        raise ValueError(f"Agent output did not match expected schema: {e}") from e
    except Exception as e:
        logger.error("agent_runtime_error", agent_name=agent_name, error=str(e))
        raise

    if accumulated_usage:
        usage = RunUsage(
            input_tokens=(usage.input_tokens or 0)
            + (accumulated_usage.input_tokens or 0),
            output_tokens=(usage.output_tokens or 0)
            + (accumulated_usage.output_tokens or 0),
            requests=(usage.requests or 0) + (accumulated_usage.requests or 0),
        )

    return cast(Any, final), usage
