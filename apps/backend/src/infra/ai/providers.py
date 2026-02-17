
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
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


class DeepSeekModelProvider(BaseProvider):
    """Provider adapter for DeepSeek models using the OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        """Initializes the provider with system settings.

        Args:
            settings: The global application settings.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates an OpenAIChatModel instance configured for DeepSeek.

        Args:
            model_id: The DeepSeek model identifier.

        Returns:
            A configured OpenAIChatModel instance.
        """
        return OpenAIChatModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.deepseek.com",
                api_key=self.settings.deepseek_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns DeepSeek-specific settings, including tool choice quirks.

        Args:
            model_id: The model identifier.

        Returns:
            ModelSettings with thinking mode or tool choice overrides.
        """
        if model_id == "deepseek-reasoner":
            # The reasoner model has thinking enabled by default.
            # It also rejects tool_choice='required'.
            return ModelSettings(tool_choice="auto")
        # deepseek-chat supports thinking mode via extra_body.
        return ModelSettings(extra_body={"thinking": {"type": "enabled"}})


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
