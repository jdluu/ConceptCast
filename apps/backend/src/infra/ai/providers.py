
from typing import Any, cast

from pydantic_ai.messages import ModelMessage
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


class GoogleModelProvider(BaseProvider):
    """Provider adapter for Google Gemini models."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a GoogleModel instance.

        Args:
            model_id: The Gemini model identifier.

        Returns:
            A configured GoogleModel instance.
        """
        return GoogleModel(
            model_id,
            provider=PydanticGoogleProvider(api_key=self.settings.google_api_key),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns Gemini-specific thinking configurations.

        Args:
            model_id: The model identifier.

        Returns:
            GoogleModelSettings with thinking budget.
        """
        # https://ai.google.dev/gemini-api/docs/thinking
        return GoogleModelSettings(google_thinking_config={"thinking_budget": 1024})


class GroqModelProvider(BaseProvider):
    """Provider adapter for Groq-hosted models."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates a GroqModel instance.

        Args:
            model_id: The Groq model identifier.

        Returns:
            A configured GroqModel instance.
        """
        return GroqModel(
            model_id,
            provider=PydanticGroqProvider(api_key=self.settings.groq_api_key),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns Groq-specific reasoning configurations.

        Args:
            model_id: The model identifier.

        Returns:
            GroqModelSettings with reasoning format.
        """
        # https://console.groq.com/docs/reasoning
        return GroqModelSettings(groq_reasoning_format="parsed")


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

            self.client.chat.completions = cast(Any, CompletionsProxy())
            try:
                # We still call super() but now with the patched client
                return await super()._completions_create(
                    messages, stream, model_settings, model_request_parameters
                )
            finally:
                self.client.chat.completions = original_completions
        else:
            return await super()._completions_create(
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
        return ModelSettings(tool_choice="auto")


class SyntheticModelProvider(BaseProvider):
    """Provider adapter for Synthetic AI models using the OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates an OpenAIChatModel instance configured for Synthetic AI.

        Args:
            model_id: The Synthetic model identifier.

        Returns:
            A configured OpenAIChatModel instance.
        """
        return OpenAIChatModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.synthetic.ai/v1",
                api_key=self.settings.synthetic_api_key,
            ),
            settings=self.get_settings(model_id),
        )


class MockModelProvider(BaseProvider):
    """Provider adapter for local testing using the TestModel."""

    def create_model(self, model_id: str) -> Model:
        """Creates a TestModel instance for local simulation.

        Args:
            model_id: The mock model identifier.

        Returns:
            A TestModel instance.
        """
        return TestModel()
