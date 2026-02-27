import json
import re
from datetime import datetime, timezone
from typing import Any, cast

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, TextPart
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider as PydanticGoogleProvider
from pydantic_ai.providers.groq import GroqProvider as PydanticGroqProvider
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class GeminiModel(GoogleModel):
    """Custom GoogleModel for Gemini to handle specific behaviors or overrides."""

    pass


class GoogleModelProvider(BaseProvider):
    """Provider adapter for Google Gemini models using the Generative Language API."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a GeminiModel instance.

        Args:
            model_id: The Gemini model identifier.

        Returns:
            A configured GeminiModel instance.
        """
        return GeminiModel(
            model_id,
            provider=PydanticGoogleProvider(api_key=self.settings.google_api_key),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns Gemini-specific configurations.

        Args:
            model_id: The model identifier.

        Returns:
            GoogleModelSettings with thinking and safety configurations.
        """
        # Default safety: be lenient for educational technical deconstructions
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Thinking capable models (Gemini 2.0 Thinking or 3.x Pro/Flash)
        is_thinking_capable = (
            "thinking" in model_id.lower() 
            or "gemini-3.1" in model_id.lower()
            or "gemini-3-flash" in model_id.lower()
        )

        if is_thinking_capable:
            return GoogleModelSettings(
                google_thinking_config={"thinking_budget": 1024},
                google_safety_settings=safety_settings,  # type: ignore
            )

        return GoogleModelSettings(google_safety_settings=safety_settings)  # type: ignore


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


from pydantic_ai.messages import (
    ModelMessage, 
    ModelResponse, 
    ToolCallPart, 
    TextPart, 
    ModelRequest, 
    SystemPromptPart, 
    UserPromptPart,
    ToolReturnPart
)
from pydantic_ai.models import Model, ModelRequestParameters

class RealisticMockModel(Model):
    """A more advanced mock model that returns realistic pedagogical data."""

    @property
    def model_name(self) -> str:
        return "realistic-mock"

    @property
    def system(self) -> str:
        return "mock"

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Correctly implements the Model.request interface for realistic mockery."""
        from .mock_responses import get_realistic_response
        from loguru import logger

        # 1. Inspect messages to identify agent and turn
        system_text = ""
        user_topic = None
        has_previous_model_response = False
        
        for msg in messages:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, SystemPromptPart):
                        system_text += part.content
                    elif isinstance(part, UserPromptPart):
                        # Extract topic from user prompt (usually in single quotes)
                        match = re.search(r"'(.*?)'", part.content)
                        if match:
                            user_topic = match.group(1)
            elif isinstance(msg, ModelResponse):
                has_previous_model_response = True

        is_analyst = "Analyst Agent" in system_text
        is_animator = "Animator Agent" in system_text
        is_first_turn = not has_previous_model_response

        logger.info(f"Mock Request: agent={'Analyst' if is_analyst else 'Animator' if is_animator else 'Other'}, turn={'1' if is_first_turn else 'N'}, topic={user_topic}")

        # 2. Handle Analyst Turn 1: Mock 'consult_critic' tool call
        if is_analyst and is_first_turn:
            from api.schemas import CurriculumPlan
            response_json = get_realistic_response("", CurriculumPlan, user_topic)
            logger.info("Mock: Returning Analyst Turn 1 tool call (consult_critic)")
            return ModelResponse(parts=[
                ToolCallPart(
                    tool_name="consult_critic", 
                    args=json.loads(response_json)
                )
            ])

        # 3. Determine target type for other agents or final turns
        output_object = model_request_parameters.output_object
        
        from api.schemas import CurriculumPlan, Storyboard, ValidationResult
        
        target_type = None
        if output_object:
            if output_object.name == "CurriculumPlan":
                target_type = CurriculumPlan
            elif output_object.name == "Storyboard":
                target_type = Storyboard
            elif output_object.name == "ValidationResult":
                target_type = ValidationResult

        # 4. Generate the mock text/JSON
        response_text = get_realistic_response(system_text, target_type, user_topic)
        
        # 5. Return either as Result Tool Call (if structured) or Plain Text
        if output_object and model_request_parameters.output_tools:
            # PydanticAI structured output uses a tool call for the final result
            tool_name = output_object.name
            actual_tool = next((t for t in model_request_parameters.output_tools if t.name == tool_name), model_request_parameters.output_tools[0])
            
            logger.info(f"Mock: Returning structured tool call ({actual_tool.name})")
            return ModelResponse(parts=[
                ToolCallPart(
                    tool_name=actual_tool.name,
                    args=json.loads(response_text)
                )
            ])
            
        # For non-structured agents like Animator (output_type=str) or plain text turns
        logger.info(f"Mock: Returning plain text response (first 50 chars: {response_text[:50]}...)")
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
