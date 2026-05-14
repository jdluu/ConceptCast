from dataclasses import dataclass
from typing import cast

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from api.schemas import ProviderModels
from infra.settings import Settings, get_settings

from .base import BaseConceptModel, BaseProvider
from .mock import MockConceptModel, RealisticMockModel


@dataclass
class ProviderEntry:
    """Registry entry for an AI provider and its supported models."""

    id: str
    settings_key: str
    models: tuple[str, ...]
    default_model: str
    display_name: str


def _load_nano_models() -> tuple[str, ...]:
    """Loads Nano GPT models from the root config directory."""
    from infra.settings import PROJECT_ROOT

    models_file = PROJECT_ROOT / "config" / "nano_models.txt"
    if not models_file.exists():
        return ("openai/gpt-oss-120b",)  # Fallback

    with models_file.open() as f:
        return tuple(
            line.strip() for line in f if line.strip() and not line.startswith("#")
        )


PROVIDER_REGISTRY = (
    ProviderEntry(
        id="nano",
        settings_key="nano_api_key",
        models=_load_nano_models(),
        default_model="openai/gpt-oss-120b",
        display_name="Nano GPT",
    ),
    ProviderEntry(
        id="mock",
        settings_key="",  # No key needed
        models=("mock-analyst", "mock-architect", "mock-animator", "mock-reviewer"),
        default_model="mock-analyst",
        display_name="Mock Demo",
    ),
)


class NanoConceptModel(BaseConceptModel):
    """Implementation of BaseConceptModel for NanoGPT."""

    @property
    def is_thinking(self) -> bool:
        return ":thinking" in self.model_id or "-thinking" in self.model_id


class NanoProvider(BaseProvider):
    """Provider for Nano GPT (OpenAI compatible)."""

    def __init__(self, entry: ProviderEntry, settings: Settings):
        self.entry = entry
        self.settings = settings

    def create_model(self, model_id: str) -> BaseConceptModel:
        """Required by BaseProvider interface."""
        return self.get_model(model_id)  # type: ignore

    def get_model(self, model_id: str | None = None) -> BaseConceptModel | None:
        key = self.settings.nano_api_key
        if not key or key == "your_nano_api_key":
            return None

        m_id = model_id or self.entry.default_model

        # In modern PydanticAI (0.1+), base_url is set via the provider.
        provider = OpenAIProvider(
            base_url="https://nano-gpt.com/api/subscription/v1",
            api_key=key,
        )

        return NanoConceptModel(
            model=OpenAIChatModel(m_id, provider=provider),
            model_id=m_id,
        )


def get_available_providers_and_models(settings: Settings) -> list[ProviderModels]:
    """Returns a list of providers and their available models based on settings."""
    available = []
    for entry in PROVIDER_REGISTRY:
        # Check if the required API key is set
        if entry.settings_key:
            key_val = getattr(settings, entry.settings_key, None)
            if not key_val or "your-key-here" in key_val.lower() or key_val.lower().startswith("your_"):
                continue

        available.append(
            ProviderModels(
                provider=entry.id,
                display_name=entry.display_name,
                models=list(entry.models),
            )
        )
    return available


def get_concept_model(
    provider_name: str, model_id: str | None = None
) -> BaseConceptModel | None:
    """Factory function to resolve a specific provider and model."""
    settings = get_settings()
    for entry in PROVIDER_REGISTRY:
        if entry.id == provider_name:
            if entry.id == "nano":
                return NanoProvider(entry, settings).get_model(model_id)
            if entry.id == "mock":
                # Always returns the mock model
                return MockConceptModel(RealisticMockModel(), model_id or "mock-agent")
    return None


def get_pydantic_ai_model(
    provider_name: str, model_id: str | None = None
) -> OpenAIChatModel | None:
    """Helper to get a raw PydanticAI Model instance.

    Args:
        provider_name: Logical name of the provider (e.g., 'nano').
        model_id: Specific model identifier.

    Returns:
        A configured Model instance or None.
    """
    concept_model = get_concept_model(provider_name, model_id)
    if concept_model:
        return cast(OpenAIChatModel, concept_model.model)
    return None
