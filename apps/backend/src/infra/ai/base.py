"""Abstract base classes and core interfaces for the ConceptCast AI provider system.

Defines the contract for model providers, ensuring consistent instantiation and
configuration of LLMs across different backends.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings


class BaseConceptModel(ABC):
    """Base class for all models used in ConceptCast.

    Wraps a Pydantic AI Model instance and provides additional metadata
    and behaviors specific to the ConceptCast orchestration.
    """

    def __init__(
        self,
        model: Model,
        model_id: str,
        settings: ModelSettings | None = None,
    ):
        self._model = model
        self._model_id = model_id
        self._settings = settings

    @property
    def model(self) -> Model:
        """Returns the underlying Pydantic AI Model."""
        return self._model

    @property
    def model_id(self) -> str:
        """Returns the model identifier."""
        return self._model_id

    @property
    def settings(self) -> ModelSettings | None:
        """Returns the model settings."""
        return self._settings

    @property
    @abstractmethod
    def is_thinking(self) -> bool:
        """Returns True if the model supports native 'thinking' or reasoning."""
        pass

    @property
    def supports_artifacts(self) -> bool:
        """Returns True if the model supports system-level artifacts (e.g. Claude)."""
        return False


class BaseProvider(ABC):
    """Abstract base class for AI model provider adapters.

    This class defines the interface for creating and configuring ConceptCast
    models from different backend services.
    """

    @abstractmethod
    def create_model(self, model_id: str) -> BaseConceptModel:
        """Creates and configures a ConceptCast model instance.

        Args:
            model_id: The specific model identifier to instantiate.

        Returns:
            A configured BaseConceptModel instance.
        """
        pass

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves provider-specific settings for a given model.

        Args:
            model_id: The model identifier to fetch settings for.

        Returns:
            A ModelSettings object or None.
        """
        return None


def load_prompt(name: str) -> str:
    """Loads a system prompt from the src/prompts/ directory.

    Args:
        name: The filename without extension (e.g., 'analyst').

    Returns:
        The content of the prompt file as a string.
    """
    path = Path(__file__).parent.parent.parent / "prompts" / f"{name}.txt"
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        from loguru import logger

        logger.warning(f"Failed to load prompt '{name}' from {path}: {e}")
        return f"You are the {name} agent."
