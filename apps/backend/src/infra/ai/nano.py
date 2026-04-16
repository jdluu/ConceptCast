import httpx
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseConceptModel, BaseProvider


def is_thinking_model(model_id: str) -> bool:
    """Designates models that support native reasoning or 'thinking' fields.

    Matches against known thinking-capable models including OpenAI o1/o3,
    DeepSeek R1, and designated :thinking variants in the Nano GPT catalog.

    Args:
        model_id: The model identifier to check.

    Returns:
        bool: True if the model should be treated as a reasoning model.
    """
    mid = model_id.lower()
    return (
        ":thinking" in mid
        or "r1" in mid
        or "thought" in mid
        or "gpt-5" in mid
        or "o1" in mid
        or "o3" in mid
    )


class NanoConceptModel(BaseConceptModel):
    """Nano GPT model wrapper for the ConceptCast system.

    Provides metadata and configuration for models proxied through the
    Nano GPT subscription service.
    """

    @property
    def is_thinking(self) -> bool:
        """Determines if the underlying model emits a reasoning/thinking field.

        Returns:
            bool: True if the model is a reasoning-capable model.
        """
        return is_thinking_model(self._model_id)


class NanoModelProvider(BaseProvider):
    """Provider adapter for Nano GPT AI models.

    Points to the OpenAI-compatible proxy at 'https://nano-gpt.com/api/v1'.
    """

    def __init__(self, settings: Settings):
        """Initializes the Nano GPT provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> NanoConceptModel:
        """Creates and configures an OpenAIChatModel for Nano GPT.

        Args:
            model_id: The Nano GPT model identifier.

        Returns:
            A configured NanoConceptModel instance.
        """
        # Nano GPT uses reasoning for models like DeepSeek-R1 and GPT-5.
        # We use the subscription-specific endpoint to stay within plan limits.
        profile = None
        if is_thinking_model(model_id):
            profile = OpenAIModelProfile(
                openai_supports_reasoning=True,
                # Current Nano GPT API uses 'reasoning' by default in /api/v1 and /api/subscription/v1
                openai_chat_thinking_field="reasoning",
            )

        # Large thinking models can take a long time to start responding.
        # We use a generous timeout to prevent hanging.
        client = httpx.AsyncClient(timeout=300.0)

        pydantic_model = OpenAIChatModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://nano-gpt.com/api/subscription/v1",
                api_key=self.settings.nano_api_key,
                http_client=client,
            ),
            profile=profile,
        )
        return NanoConceptModel(pydantic_model, model_id, self.get_settings(model_id))

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves Nano GPT-specific configurations.

        Args:
            model_id: The model identifier.

        Returns:
            ModelSettings or None.
        """
        return None
