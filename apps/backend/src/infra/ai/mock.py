import asyncio
import json
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
from pydantic_ai import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelResponsePart,
    ModelResponseStreamEvent,
    PartStartEvent,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models import (
    Model,
    ModelRequestParameters,
    StreamedResponse,
)

from api.schemas import (
    CurriculumPlan,
    Storyboard,
    TeachingStepsDraft,
)
from domain.models.curriculum import ValidationResult

from .base import BaseConceptModel, BaseProvider
from .mock_responses import get_realistic_response

logger = structlog.get_logger(__name__)


@dataclass
class MockStreamedResponse(StreamedResponse):
    """Mock implementation of a streamed model response.

    Simulates the atomic delivery of response parts for testing.

    Attributes:
        _model_name: The name of the mock model.
        _timestamp: Response creation timestamp.
        _parts: The list of parts to stream.
    """

    _model_name: str
    _timestamp: datetime
    _parts: list[ModelResponsePart]

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        """Yields events simulated from the predefined parts with realistic delays."""
        for i, part in enumerate(self._parts):
            if isinstance(part, (TextPart, ThinkingPart)):
                # Split content into parts, preserving the delimiters (newlines or sentence-ending spaces)
                # This ensures Python code blocks (Manim) preserve their syntax.
                content = part.content
                parts_list = re.split(r"((?<=[.!?])\s+|\n)", content)
                for part_chunk in parts_list:
                    if not part_chunk:
                        continue

                    if isinstance(part, TextPart):
                        events = self._parts_manager.handle_text_delta(
                            vendor_part_id=i, content=part_chunk
                        )
                    else:
                        events = self._parts_manager.handle_thinking_delta(
                            vendor_part_id=i, content=part_chunk
                        )

                    for event in events:
                        yield event

                    # Small delay between chunks for realism
                    await asyncio.sleep(0.1)
            elif isinstance(part, ToolCallPart):
                await asyncio.sleep(0.5)  # Simulate "thinking" before tool call
                yield self._parts_manager.handle_tool_call_part(
                    vendor_part_id=i,
                    tool_name=part.tool_name,
                    args=part.args,
                    tool_call_id=part.tool_call_id,
                )
            else:
                yield PartStartEvent(index=i, part=part)

    @property
    def model_name(self) -> str:
        """Returns the internal name of the mock model."""
        return self._model_name

    @property
    def provider_name(self) -> str | None:
        """Identifies the provider as mock for testing."""
        return "mock"

    @property
    def provider_url(self) -> str | None:
        """No provider URL is required for local mock execution."""
        return None

    @property
    def timestamp(self) -> datetime:
        """The simulation timestamp for this response."""
        return self._timestamp


class RealisticMockModel(Model):
    """An advanced mock model delivering realistic pedagogical data.

    Inspects incoming prompts to decide which mock response to return,
    supporting multi-turn simulations for Analyst and Animator agents.
    """

    @property
    def model_name(self) -> str:
        """The identifier for the realistic mock model."""
        return "realistic-mock"

    @property
    def system(self) -> str:
        """Return 'mock' as the system identifier."""
        return "mock"

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: Any | None,
        model_request_parameters: ModelRequestParameters,
        _run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Simulates a streamed request by yielding a MockStreamedResponse."""
        response = await self.request(
            messages, model_settings, model_request_parameters
        )

        yield MockStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=self.model_name,
            _timestamp=response.timestamp,
            _parts=list(response.parts),
        )

    async def request(  # noqa: C901, PLR0912
        self,
        messages: list[ModelMessage],
        _model_settings: Any | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Processes a model request and returns a matching mock response.

        Analyzes the system prompt and conversation history to determine
        if it should return structured tool calls or plain text.

        Args:
            messages: Conversation history.
            model_settings: Ignored in mock.
            model_request_parameters: Details on expected output format.

        Returns:
            A ModelResponse populated with mock data.
        """
        system_text = ""
        user_topic = None
        has_previous_model_response = False

        for msg in messages:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, SystemPromptPart):
                        system_text += part.content
                    elif isinstance(part, UserPromptPart) and isinstance(
                        part.content, str
                    ):
                        match = re.search(r"['\"](.*?)['\"]", part.content)
                        if match:
                            user_topic = match.group(1)
            elif isinstance(msg, ModelResponse):
                has_previous_model_response = True

        is_analyst = "Analyst Agent" in system_text
        is_animator = "Animator Agent" in system_text
        is_first_turn = not has_previous_model_response

        agent_label = (
            "Analyst" if is_analyst else "Animator" if is_animator else "Other"
        )
        logger.info(
            "mock_model_request",
            agent=agent_label,
            turn="1" if is_first_turn else "N",
            topic=user_topic,
        )

        if is_analyst and is_first_turn:
            response_json = get_realistic_response("", TeachingStepsDraft, user_topic)
            return ModelResponse(
                parts=[
                    ThinkingPart(
                        content=(
                            f"Analyzing the topic '{user_topic or 'Unknown'}' for pedagogical structure. "
                            "Breaking down key concepts and identifying logical dependencies. "
                            "I will now consult the Validator to ensure the plan is sound."
                        )
                    ),
                    ToolCallPart(
                        tool_name="consult_critic",
                        args=json.loads(response_json),
                        tool_call_id="mock_call_1",
                    ),
                ]
            )

        output_object = model_request_parameters.output_object

        target_type: type | None = None
        if output_object:
            name = output_object.name
            if name in ("TeachingStepsDraft", "final_result") and is_analyst:
                target_type = TeachingStepsDraft
            elif name in ("Storyboard", "final_result") and "Architect" in system_text:
                target_type = Storyboard
            elif (
                name in ("ValidationResult", "final_result")
                and "Validator" in system_text
            ):
                target_type = ValidationResult

            elif name == "TeachingStepsDraft":
                target_type = TeachingStepsDraft
            elif name == "CurriculumPlan":
                target_type = CurriculumPlan
            elif name == "Storyboard":
                target_type = Storyboard
            elif name == "ValidationResult":
                target_type = ValidationResult

        response_text = get_realistic_response(
            system_text, target_type or str, user_topic
        )

        if output_object and model_request_parameters.output_tools:
            tool_name = output_object.name
            actual_tool = next(
                (
                    t
                    for t in model_request_parameters.output_tools
                    if t.name == tool_name
                ),
                None,
            )

            if actual_tool:
                return ModelResponse(
                    parts=[
                        ThinkingPart(
                            content=f"Preparing final {target_type.__name__ if target_type else 'output'} based on council feedback."
                        ),
                        ToolCallPart(
                            tool_name=actual_tool.name,
                            args=json.loads(response_text),
                            tool_call_id="mock_call_final",
                        ),
                    ]
                )

        return ModelResponse(
            parts=[
                ThinkingPart(
                    content=f"Synthesizing {agent_label} outputs for '{user_topic or 'the topic'}'. Finalizing artifacts."
                ),
                TextPart(content=response_text),
            ]
        )

    def name(self) -> str:
        return "realistic-mock"


class MockConceptModel(BaseConceptModel):
    """Mock model wrapper for ConceptCast."""

    @property
    def is_thinking(self) -> bool:
        """Mock models are designed to emit thoughts for diagnostic purposes."""
        return True


class MockModelProvider(BaseProvider):
    """Provider adapter for local testing and demonstration.

    Returns the RealisticMockModel which provides canned outputs.
    """

    def create_model(self, model_id: str) -> MockConceptModel:
        """Creates a RealisticMockModel instance.

        Args:
            model_id: The mock model identifier.

        Returns:
            A MockConceptModel instance.
        """
        pydantic_model = RealisticMockModel()
        return MockConceptModel(pydantic_model, model_id, self.get_settings(model_id))
