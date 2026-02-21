from abc import ABC, abstractmethod

from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings


class BaseProvider(ABC):
    """Abstract base class for AI model providers.

    Encapsulates model creation and provider-specific configurations
    like thinking settings and runtime parameters.
    """

    @abstractmethod
    def create_model(self, model_id: str) -> Model:
        """Creates a Pydantic AI model instance for the given model ID.

        Args:
            model_id: The identifier of the model to create.

        Returns:
            A configured Pydantic AI Model instance.
        """
        pass

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Returns model-level settings (e.g. thinking/reasoning).

        Args:
            model_id: The identifier of the model to fetch settings for.

        Returns:
            A ModelSettings object or None if no specific settings are required.
        """
        return None
