from dataclasses import dataclass

from pydantic_ai.models import Model

from api.schemas import ProviderModels
from infra.settings import Settings, get_settings

from .base import BaseProvider
from .deepseek import DeepSeekModelProvider
from .groq import GroqModelProvider
from .mock import MockModelProvider
from .nano import NanoModelProvider

PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "groq": GroqModelProvider,
    "deepseek": DeepSeekModelProvider,
    "nano": NanoModelProvider,
    "mock": MockModelProvider,
}


@dataclass(frozen=True)
class ProviderEntry:
    """Registry entry for an AI provider.

    Attributes:
        id: Unique provider identifier.
        settings_key: The configuration key for the provider's API secret.
        models: Tuple of supported model identifiers.
        default_model: The model to use if none is specified.
        display_name: Human-readable name for the provider.
    """

    id: str
    settings_key: str | None
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
        id="nano",
        settings_key="nano_api_key",
        models=(
            "nvidia/nemotron-3-super-120b-a12b:thinking",
            "minimax/minimax-m2.5",
            "qwen/qwen3.5-397b-a17b-thinking",
            "zai-org/glm-5:thinking",
            "moonshotai/kimi-k2.5:thinking",
        ),
        default_model="nvidia/nemotron-3-super-120b-a12b:thinking",
        display_name="Nano GPT (Subscription)",
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
    """Retrieves providers and models for which a valid API key exists.

    Args:
        settings: The application settings containing API keys.

    Returns:
        A list of active providers and their available models.
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
    """Retrieves a provider's metadata from the registry.

    Args:
        provider_name: The identifier of the provider.

    Returns:
        The matching ProviderEntry or None.
    """
    for entry in PROVIDER_REGISTRY:
        if entry.id == provider_name:
            return entry
    return None


def get_provider_for_model(model_id: str) -> BaseProvider | None:
    """Identifies the appropriate provider for a specific model ID.

    Args:
        model_id: The model identifier to search for.

    Returns:
        A BaseProvider instance or None if no match is found.
    """
    for entry in PROVIDER_REGISTRY:
        if model_id in entry.models:
            return get_provider(entry.id)
    return None


def get_provider(provider_name: str) -> BaseProvider | None:
    """Instantiates the specific provider handler by name.

    Args:
        provider_name: The identifier of the provider to instantiate.

    Returns:
        A BaseProvider implementation or None.
    """
    provider_cls = PROVIDER_CLASSES.get(provider_name)
    if not provider_cls:
        return None

    settings = get_settings()

    try:
        return provider_cls(settings)  # type: ignore
    except TypeError:
        return provider_cls()


def get_model(
    provider_name: str | None = None, model_id: str | None = None
) -> Model | None:
    """Creates a configured PydanticAI model instance.

    Args:
        provider_name: The identifier of the provider.
        model_id: Specific model identifier. Defaults to the provider's default.

    Returns:
        A configured Model instance or None if missing keys or invalid provider.
    """
    if not provider_name:
        return None

    entry = _get_registry_entry(provider_name)
    if not entry:
        return None

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
