from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider as PydanticDeepSeekProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class DeepSeekModelProvider(BaseProvider):
    """Provider adapter for DeepSeek models.

    Integrates with Pydantic AI's native DeepSeekProvider for optimized
    handling of 'deepseek-chat' and 'deepseek-reasoner'.
    """

    def __init__(self, settings: Settings):
        """Initializes the DeepSeek provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates and configures a DeepSeek model.

        Args:
            model_id: The DeepSeek model identifier (e.g., 'deepseek-chat').

        Returns:
            A configured OpenAIChatModel instance.
        """
        return OpenAIChatModel(
            model_id,
            provider=PydanticDeepSeekProvider(
                api_key=self.settings.deepseek_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves DeepSeek-specific model configurations.

        Args:
            model_id: The DeepSeek model identifier.

        Returns:
            ModelSettings or None.
        """
        return None
