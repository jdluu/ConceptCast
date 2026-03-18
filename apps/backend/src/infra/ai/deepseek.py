import httpx
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider as PydanticDeepSeekProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseConceptModel, BaseProvider


class DeepSeekConceptModel(BaseConceptModel):
    """DeepSeek model wrapper for ConceptCast."""

    @property
    def is_thinking(self) -> bool:
        """Returns True if the model is 'deepseek-reasoner'."""
        return "reasoner" in self._model_id.lower()


class DeepSeekModelProvider(BaseProvider):
    """Provider adapter for DeepSeek models."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def create_model(self, model_id: str) -> DeepSeekConceptModel:
        """Creates and configures a DeepSeek model."""
        client = httpx.AsyncClient(timeout=60.0)
        pydantic_model = OpenAIChatModel(
            model_id,
            provider=PydanticDeepSeekProvider(
                api_key=self.settings.deepseek_api_key,
                http_client=client,
            ),
        )
        return DeepSeekConceptModel(
            pydantic_model, model_id, self.get_settings(model_id)
        )

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        return None
