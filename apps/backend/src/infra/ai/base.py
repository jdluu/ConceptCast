"""Abstract base classes and core interfaces for the ConceptCast AI provider system.

Defines the contract for model providers, ensuring consistent instantiation and
configuration of LLMs across different backends.
"""

from abc import ABC, abstractmethod

from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings


class BaseProvider(ABC):
    """Abstract base class for AI model provider adapters.

    This class defines the interface for creating and configuring PydanticAI
    models from different backend services (e.g., Groq, DeepSeek).
    """

    @abstractmethod
    def create_model(self, model_id: str) -> Model:
        """Creates and configures a PydanticAI Model instance.

        Args:
            model_id: The specific model identifier to instantiate.

        Returns:
            A configured Model instance ready for execution.
        """
        pass

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves provider-specific settings for a given model.

        Settings may include specific token limits, temperature, or
        backend-specific parameters like reasoning formats.

        Args:
            model_id: The model identifier to fetch settings for.

        Returns:
            A ModelSettings object or None if default settings are sufficient.
        """
        return None
