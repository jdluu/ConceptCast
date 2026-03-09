import json
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

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
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models import (
    Model,
    ModelRequestParameters,
    StreamedResponse,
)
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.groq import GroqProvider as PydanticGroqProvider
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class ConceptGroqModel(GroqModel):
    """Custom GroqModel for specialized ConceptCast behaviors."""

    pass


class GroqModelProvider(BaseProvider):
    """Provider adapter for Groq-hosted models."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a ConceptGroqModel instance.

        Args:
            model_id: The Groq model identifier.

        Returns:
            A configured ConceptGroqModel instance.
        """
        return ConceptGroqModel(
            model_id,
            provider=PydanticGroqProvider(api_key=self.settings.groq_api_key),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns Groq-specific reasoning configurations.

        Args:
            model_id: The model identifier.

        Returns:
            GroqModelSettings with reasoning format if applicable.
        """
        # DeepSeek-R1 and specialized reasoning models on Groq
        if "deepseek-r1" in model_id.lower() or "reasoning" in model_id.lower():
            # https://console.groq.com/docs/reasoning
            return GroqModelSettings(groq_reasoning_format="parsed")
        return None


class DeepSeekModel(OpenAIChatModel):
    """Custom OpenAI-compatible model for DeepSeek to handle API quirks."""

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: OpenAIChatModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> Any:
        """Strips tool_choice for deepseek-reasoner to avoid 400 errors.

        Note: pydantic-ai calculates tool_choice locally in its own _completions_create
        and ignores the value in model_settings. We use a proxy to intercept the call.
        """
        if self.model_name == "deepseek-reasoner":
            original_completions = self.client.chat.completions

            class CompletionsProxy:
                def __getattr__(self, name: str) -> Any:
                    return getattr(original_completions, name)

                async def create(self, **kwargs: Any) -> Any:
                    kwargs.pop("tool_choice", None)
                    return await original_completions.create(**kwargs)

            self.client.chat.completions = cast(Any, CompletionsProxy())  # type: ignore[misc]
            try:
                # We still call super() but now with the patched client
                return await super()._completions_create(  # type: ignore[call-overload]
                    messages, stream, model_settings, model_request_parameters
                )
            finally:
                self.client.chat.completions = original_completions  # type: ignore[misc]
        else:
            return await super()._completions_create(  # type: ignore[call-overload]
                messages, stream, model_settings, model_request_parameters
            )


class DeepSeekModelProvider(BaseProvider):
    """Provider adapter for DeepSeek models using the OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a DeepSeekModel instance.

        Args:
            model_id: The DeepSeek model identifier.

        Returns:
            A configured DeepSeekModel instance.
        """
        return DeepSeekModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.deepseek.com",
                api_key=self.settings.deepseek_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns DeepSeek-specific settings, including tool choice overrides.

        Args:
            model_id: The model identifier.

        Returns:
            ModelSettings with thinking mode or tool choice overrides.
        """
        if model_id == "deepseek-reasoner":
            # DeepSeek-Reasoner (R1) supports tool calls and JSON mode,
            # but strictly prohibits sending the tool_choice parameter.
            # We return empty settings and strip tool_choice in DeepSeekModel.
            return ModelSettings()
        # deepseek-chat supports tool calling and works best with tool_choice='auto'.
        return ModelSettings(tool_choice="auto")  # type: ignore[typeddict-unknown-key]


class SyntheticModel(OpenAIChatModel):
    """Custom model for Synthetic.new to handle any Hugging Face or OpenAI quirks."""

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: OpenAIChatModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> Any:
        """Proxies completions to strip tool_choice for proxy-hosted models.

        Some Hugging Face models behind the synthetic.new proxy may return 400
        errors if tool_choice is explicitly provided.
        """
        original_completions = self.client.chat.completions

        class CompletionsProxy:
            def __getattr__(self, name: str) -> Any:
                return getattr(original_completions, name)

            async def create(self, **kwargs: Any) -> Any:
                # Remove tool_choice as many HF proxies are strict
                kwargs.pop("tool_choice", None)
                return await original_completions.create(**kwargs)

        self.client.chat.completions = cast(Any, CompletionsProxy())  # type: ignore[misc]
        try:
            return await super()._completions_create(  # type: ignore[call-overload]
                messages, stream, model_settings, model_request_parameters
            )
        finally:
            self.client.chat.completions = original_completions  # type: ignore[misc]


class SyntheticModelProvider(BaseProvider):
    """Provider adapter for Synthetic AI models using the OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a SyntheticModel instance configured for Synthetic.new.

        Args:
            model_id: The Synthetic model identifier.

        Returns:
            A configured SyntheticModel instance.
        """
        return SyntheticModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.synthetic.new/openai/v1",
                api_key=self.settings.synthetic_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns Synthetic-specific configurations.

        Args:
            model_id: The model identifier.

        Returns:
            ModelSettings for the model.
        """
        return None


@dataclass
class MockStreamedResponse(StreamedResponse):
    """Mock implementation of StreamedResponse for RealisticMockModel."""

    _model_name: str
    _timestamp: datetime
    _parts: list[ModelResponsePart]

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        """Yields events via parts manager for each mock part."""
        for i, part in enumerate(self._parts):
            if isinstance(part, TextPart):
                # Yield text deltas via parts manager
                events = self._parts_manager.handle_text_delta(
                    vendor_part_id=i, content=part.content
                )
                for event in events:
                    yield event
            elif isinstance(part, ToolCallPart):
                # Yield tool call via parts manager
                yield self._parts_manager.handle_tool_call_part(
                    vendor_part_id=i,
                    tool_name=part.tool_name,
                    args=part.args,
                    tool_call_id=part.tool_call_id,
                )
            else:
                # Fallback for other parts if any
                yield PartStartEvent(index=i, part=part)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str | None:
        return "mock"

    @property
    def provider_url(self) -> str | None:
        return None

    @property
    def timestamp(self) -> datetime:
        return self._timestamp


class RealisticMockModel(Model):
    """A more advanced mock model that returns realistic pedagogical data."""

    @property
    def model_name(self) -> str:
        return "realistic-mock"

    @property
    def system(self) -> str:
        return "mock"

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Implements request_stream by proxying to request."""
        response = await self.request(
            messages, model_settings, model_request_parameters
        )

        yield MockStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=self.model_name,
            _timestamp=response.timestamp,
            _parts=list(response.parts),
        )

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Correctly implements the Model.request interface for realistic mockery."""
        from loguru import logger

        from .mock_responses import get_realistic_response

        # 1. Inspect messages to identify agent and turn
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
                        # Extract topic from user prompt (usually in single quotes)
                        match = re.search(r"'(.*?)'", part.content)
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
            f"Mock Request: agent={agent_label}, "
            f"turn={'1' if is_first_turn else 'N'}, topic={user_topic}"
        )

        # 2. Handle Analyst Turn 1: Mock 'consult_critic' tool call
        if is_analyst and is_first_turn:
            from api.schemas import CurriculumPlan

            response_json = get_realistic_response("", CurriculumPlan, user_topic)
            logger.info("Mock: Returning Analyst Turn 1 tool call (consult_critic)")
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="consult_critic",
                        args=json.loads(response_json),
                        tool_call_id="mock_call_1",
                    )
                ]
            )

        # 3. Determine target type for other agents or final turns
        output_object = model_request_parameters.output_object

        from api.schemas import (
            AnimationReview,
            CurriculumPlan,
            Storyboard,
            ValidationResult,
        )

        target_type: type | None = None
        if output_object:
            if output_object.name == "CurriculumPlan":
                target_type = CurriculumPlan
            elif output_object.name == "Storyboard":
                target_type = Storyboard
            elif output_object.name == "ValidationResult":
                target_type = ValidationResult
            elif output_object.name == "AnimationReview":
                target_type = AnimationReview

        # 4. Generate the mock text/JSON
        response_text = get_realistic_response(
            system_text, target_type or str, user_topic
        )

        # 5. Return either as Result Tool Call (if structured) or Plain Text
        if output_object and model_request_parameters.output_tools:
            # PydanticAI structured output uses a tool call for the final result
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
                logger.info(
                    f"Mock: Returning structured tool call ({actual_tool.name})"
                )
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            tool_name=actual_tool.name,
                            args=json.loads(response_text),
                            tool_call_id="mock_call_final",
                        )
                    ]
                )

        # For non-structured agents like Animator (output_type=str) or plain text turns
        logger.info(
            f"Mock: Returning plain text response (first 50 chars: "
            f"{response_text[:50].strip()}...)"
        )
        return ModelResponse(parts=[TextPart(content=response_text)])

    def name(self) -> str:
        return "realistic-mock"


class MockModelProvider(BaseProvider):
    """Provider adapter for local testing using the RealisticMockModel."""

    def create_model(self, model_id: str) -> Model:
        """Creates a RealisticMockModel instance for local simulation.

        Args:
            model_id: The mock model identifier.

        Returns:
            A RealisticMockModel instance.
        """
        return RealisticMockModel()
