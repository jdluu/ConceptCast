from dataclasses import dataclass

from pydantic_ai.models import Model

from api.schemas import ProviderModels
from infra.settings import Settings, get_settings

from .base import BaseProvider
from .providers import (
    DeepSeekModelProvider,
    GroqModelProvider,
    MockModelProvider,
    SyntheticModelProvider,
)

# Registry mapping provider IDs to their handler classes
PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "groq": GroqModelProvider,
    "deepseek": DeepSeekModelProvider,
    "synthetic": SyntheticModelProvider,
    "mock": MockModelProvider,
}


@dataclass(frozen=True)
class ProviderEntry:
    """Single source of truth for a provider: id, settings key,
    models, and optional display name."""

    id: str
    settings_key: str | None  # None for mock (always available)
    models: tuple[str, ...]
    default_model: str
    display_name: str | None = None


PROVIDER_REGISTRY: tuple[ProviderEntry, ...] = (
    ProviderEntry(
        id="groq",
        settings_key="groq_api_key",
        models=(
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
        ),
        default_model="llama-3.3-70b-versatile",
        display_name="Groq",
    ),
    ProviderEntry(
        id="deepseek",
        settings_key="deepseek_api_key",
        models=("deepseek-chat", "deepseek-reasoner"),
        default_model="deepseek-chat",
        display_name="DeepSeek",
    ),
    ProviderEntry(
        id="synthetic",
        settings_key="synthetic_api_key",
        models=(
            "hf:Qwen/Qwen3.5-397B-A17B",
            "hf:moonshotai/Kimi-K2.5",
            "hf:zai-org/GLM-4.7",
            "hf:Qwen/Qwen3-Coder-480B-A35B-Instruct",
        ),
        default_model="hf:Qwen/Qwen3.5-397B-A17B",
        display_name="Synthetic",
    ),
    ProviderEntry(
        id="mock",
        settings_key=None,
        models=("mock-llm", "mock-analyst", "mock-critic"),
        default_model="mock-llm",
        display_name="Mock Demo",
    ),
)


def get_available_providers_and_models(settings: Settings) -> list[ProviderModels]:
    """Returns providers and their models for which the user has an API key (or mock).

    Args:
        settings: The global application settings.

    Returns:
        A list of ProviderModels objects representing active providers.
    """
    result: list[ProviderModels] = []
    for entry in PROVIDER_REGISTRY:
        if entry.settings_key is None:
            result.append(
                ProviderModels(
                    provider=entry.id,
                    models=list(entry.models),
                    display_name=entry.display_name,
                )
            )
        else:
            key_value = getattr(settings, entry.settings_key, None)
            if key_value:
                result.append(
                    ProviderModels(
                        provider=entry.id,
                        models=list(entry.models),
                        display_name=entry.display_name,
                    )
                )
    return result


def _get_registry_entry(provider_name: str) -> ProviderEntry | None:
    """Look up a provider in the registry by id.

    Args:
        provider_name: The ID of the provider to look up.

    Returns:
        The ProviderEntry if found, else None.
    """
    for entry in PROVIDER_REGISTRY:
        if entry.id == provider_name:
            return entry
    return None


def get_provider_for_model(model_id: str) -> BaseProvider | None:
    """Finds the correct provider handler for a given model ID.

    Args:
        model_id: The identifier of the model.

    Returns:
        A BaseProvider implementation for the model, or None.
    """
    for entry in PROVIDER_REGISTRY:
        if model_id in entry.models:
            return get_provider(entry.id)
    return None


def get_provider(provider_name: str) -> BaseProvider | None:
    """Instantiates the specialized provider handler for a given name.

    Args:
        provider_name: The ID of the provider (e.g. 'google', 'openai').

    Returns:
        A BaseProvider implementation, or None.
    """
    provider_cls = PROVIDER_CLASSES.get(provider_name)
    if not provider_cls:
        return None

    settings = get_settings()

    # Pass settings ONLY if the provider class needs them
    # MockModelProvider and others might not need them in __init__
    try:
        # Check if the class accepts settings in __init__
        return provider_cls(settings)  # type: ignore
    except TypeError:
        return provider_cls()


def get_model(
    provider_name: str | None = None, model_id: str | None = None
) -> Model | None:
    """Returns a Pydantic-AI model instance for the given provider and model.

    Args:
        provider_name: The ID of the provider.
        model_id: The specific model identifier. If None, the default for the
            provider is used.

    Returns:
        A configured Pydantic AI Model instance, or None if configuration fails.
    """
    if not provider_name:
        return None

    entry = _get_registry_entry(provider_name)
    if not entry:
        return None

    # Check for API keys
    settings = get_settings()
    if entry.settings_key and not getattr(settings, entry.settings_key, None):
        return None

    provider = get_provider(provider_name)
    if not provider:
        return None

    resolved_model_id = model_id or entry.default_model

    try:
        return provider.create_model(resolved_model_id)
    except Exception:
        return None
