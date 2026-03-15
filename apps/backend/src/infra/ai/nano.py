from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class NanoModelProvider(BaseProvider):
    """Provider adapter for Nano GPT AI models.

    Points to the OpenAI-compatible proxy at 'https://nano-gpt.com/api/subscription/v1'.
    """

    def __init__(self, settings: Settings):
        """Initializes the Nano GPT provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates and configures an OpenAIChatModel for Nano GPT.

        Args:
            model_id: The Nano GPT model identifier.

        Returns:
            A configured OpenAIChatModel instance.
        """
        return OpenAIChatModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://nano-gpt.com/api/subscription/v1",
                api_key=self.settings.nano_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves Nano GPT-specific configurations.

        Args:
            model_id: The model identifier.

        Returns:
            Always returns None for Nano GPT.
        """
        return None
