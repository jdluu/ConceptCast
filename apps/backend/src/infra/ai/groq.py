from pydantic_ai.models import Model
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.providers.groq import GroqProvider as PydanticGroqProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class ConceptGroqModel(GroqModel):
    """Custom GroqModel for specialized ConceptCast behaviors.

    Provides a hook for potential future overrides of Groq-specific
    request/response handling.
    """

    pass


class GroqModelProvider(BaseProvider):
    """Provider adapter for Groq-hosted models.

    Handles instantiation of Llama and DeepSeek models hosted on Groq,
    applying necessary reasoning format settings.
    """

    def __init__(self, settings: Settings):
        """Initializes the Groq provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates and configures a ConceptGroqModel.

        Args:
            model_id: The Groq model identifier (e.g., 'llama-3.3-70b-versatile').

        Returns:
            A configured ConceptGroqModel instance.
        """
        return ConceptGroqModel(
            model_id,
            provider=PydanticGroqProvider(api_key=self.settings.groq_api_key),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Retrieves Groq-specific model configurations.

        Enables 'parsed' reasoning format for DeepSeek-R1 models.

        Args:
            model_id: The Groq model identifier.

        Returns:
            GroqModelSettings or None if no specialization is required.
        """
        if "deepseek-r1" in model_id.lower() or "reasoning" in model_id.lower():
            return GroqModelSettings(groq_reasoning_format="parsed")
        return None
