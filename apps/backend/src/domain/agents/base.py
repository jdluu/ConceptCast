"""Base infrastructure for ConceptCast Agents.

Provides standardized patterns for agent initialization, prompt loading,
and execution with integrated observability and thought streaming.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel, load_prompt
from infra.ai.streaming import run_agent_streamed

T = TypeVar("T")


class ConceptAgent(Generic[T]):
    """Base class for all ConceptCast specialized agents.

    Encapsulates common boilerplate for PydanticAI agent setup, including
    system prompt loading, dependency injection, and streamed execution.

    Attributes:
        name: Logical name of the agent (used for logs and callbacks).
        output_type: The Pydantic model class or primitive type for structured output.
        system_prompt: The base instructions for this agent.
    """

    def __init__(self, name: str, output_type: Any):
        self.name = name
        self.output_type = output_type
        self.system_prompt = load_prompt(name)

    async def run(
        self,
        model: BaseConceptModel,
        prompt: str,
        on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
        ctx: GlobalContext | None = None,
        retries: int = 3,
        pre_run_hook: Callable[[Agent[Any, Any]], None] | None = None,
        message_history: list[ModelMessage] | None = None,
        usage_limits: UsageLimits | None = None,
    ) -> tuple[T, RunUsage]:
        """Executes the agent with standardized streaming and error handling.

        Args:
            model: The underlying AI model provider.
            prompt: The specific instructions for this run.
            on_thought: Async callback for real-time thought streaming.
            ctx: The Global Context Object (GCO) for shared state.
            retries: Number of internal validation retries.
            pre_run_hook: Optional callback to modify the agent (e.g., add tools) before run.
            message_history: Optional history of messages for stateful multi-turn interactions.
            usage_limits: Optional pydantic-ai UsageLimits for capping requests/tokens.

        Returns:
            tuple: (Parsed output model, total run usage).
        """
        agent = Agent(
            model.model,
            system_prompt=self.system_prompt,
            output_type=self.output_type,
            deps_type=GlobalContext,
            retries=retries,
        )

        if pre_run_hook:
            pre_run_hook(agent)

        # Streaming is now enabled for ALL providers including Nano. The original
        # keep-alive/SSE dropout issue that forced non-stream mode was caused by stale
        # pooled connections — fixed properly in the factory (fresh connection per call,
        # commit 8ab9d2c). Non-stream mode cannot handle thinking models, which buffer
        # their entire reasoning server-side and routinely exceed any sane timeout
        # (observed: >30 min on real animator prompts with an 1800s wall clock).

        result, usage = await run_agent_streamed(
            self.name,
            agent,
            prompt,
            on_thought=on_thought,
            deps=ctx,
            message_history=message_history,
            usage_limits=usage_limits,
            stream=True,
        )
        return result, usage
