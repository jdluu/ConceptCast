from dataclasses import dataclass

from pydantic_ai.models import Model

from api.schemas import ProviderModels
from infra.settings import Settings, get_settings

from .base import BaseConceptModel, BaseProvider
from .mock import MockModelProvider
from .nano import NanoModelProvider

PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
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
        id="nano",
        settings_key="nano_api_key",
        models=(
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "deepseek/deepseek-v3.2:thinking",
            "deepseek/deepseek-v3.2-speciale",
            "nvidia/nemotron-3-super-120b-a12b:thinking",
            "minimax/minimax-m2.7",
            "qwen/qwen3.5-122b-a10b:thinking",
            "zai-org/glm-5:thinking",
            "moonshotai/kimi-k2.5:thinking",
        ),
        default_model="openai/gpt-oss-120b",
        display_name="Nano GPT",
    ),
    ProviderEntry(
        id="mock",
        settings_key=None,
        models=("mock-model",),
        default_model="mock-model",
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


def get_concept_model(
    provider_name: str | None = None, model_id: str | None = None
) -> BaseConceptModel | None:
    """Creates a ConceptCast model wrapper.

    Args:
        provider_name: The identifier of the provider.
        model_id: Specific model identifier.

    Returns:
        A BaseConceptModel instance or None.
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


def get_model(
    provider_name: str | None = None, model_id: str | None = None
) -> Model | None:
    """Creates a configured PydanticAI model instance.

    Args:
        provider_name: The identifier of the provider.
        model_id: Specific model identifier.

    Returns:
        A configured Model instance or None.
    """
    concept_model = get_concept_model(provider_name, model_id)
    if concept_model:
        return concept_model.model
    return None
