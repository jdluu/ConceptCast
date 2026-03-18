import httpx
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.providers.groq import GroqProvider as PydanticGroqProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseConceptModel, BaseProvider


class GroqConceptModel(BaseConceptModel):
    """Groq model wrapper for ConceptCast."""

    @property
    def is_thinking(self) -> bool:
        """Returns True if the model is a reasoning model."""
        mid = self._model_id.lower()
        return "deepseek-r1" in mid or "reasoning" in mid or "gpt-oss" in mid


class GroqModelProvider(BaseProvider):
    """Provider adapter for Groq-hosted models."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def create_model(self, model_id: str) -> GroqConceptModel:
        """Creates and configures a Groq model."""
        client = httpx.AsyncClient(timeout=60.0)
        pydantic_model = GroqModel(
            model_id,
            provider=PydanticGroqProvider(
                api_key=self.settings.groq_api_key,
                http_client=client,
            ),
        )
        return GroqConceptModel(pydantic_model, model_id, self.get_settings(model_id))

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Retrieves Groq-specific settings.

        Increases max_tokens to ensure complex tool calls and artifacts
        are not truncated.
        """
        is_thinking = self.create_model_proxy_thinking(model_id)

        settings = GroqModelSettings(max_tokens=4096)
        if is_thinking:
            settings["groq_reasoning_format"] = "parsed"
        return settings

    def create_model_proxy_thinking(self, model_id: str) -> bool:
        """Helper to check if model should use reasoning format."""
        mid = model_id.lower()
        return "deepseek-r1" in mid or "reasoning" in mid or "gpt-oss" in mid
