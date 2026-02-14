from dataclasses import dataclass
from typing import Any

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider

from api.schemas import ProviderModels
from core.settings import get_settings

from .thinking import get_thinking_settings


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
        id="google",
        settings_key="google_api_key",
        models=("gemini-2.5-flash", "gemma-3-27b-it"),
        default_model="gemini-2.5-flash",
        display_name="Google (Gemini)",
    ),
    ProviderEntry(
        id="groq",
        settings_key="groq_api_key",
        models=("llama-3.3-70b-versatile", "mixtral-8x7b-32768"),
        default_model="llama-3.3-70b-versatile",
        display_name="Groq",
    ),
    # DeepSeek: deepseek-reasoner enables thinking mode (CoT) by default; see https://api-docs.deepseek.com/guides/thinking_mode
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
            "hf:deepseek-ai/DeepSeek-V3",
            "hf:Qwen/Qwen2.5-72B-Instruct",
            "hf:moonshot-ai/Kimi-V1-5-Chat-Instruct",
        ),
        default_model="hf:deepseek-ai/DeepSeek-V3",
        display_name="Synthetic",
    ),
    ProviderEntry(
        id="mock",
        settings_key=None,
        models=("mock-llm", "mock-analyst", "mock-critic"),
        default_model="mock-llm",
        display_name="Mock (Fast)",
    ),
)


def get_available_providers_and_models(settings: Any) -> list[ProviderModels]:
    """
    Returns providers and their models for which the user has an API key (or mock).

    No tiered priority; only providers with configured keys (or mock) are included.
    """
    result: list[ProviderModels] = []
    for entry in PROVIDER_REGISTRY:
        if entry.settings_key is None:
            # Mock is always available
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
    """Look up a provider in the registry by id."""
    for entry in PROVIDER_REGISTRY:
        if entry.id == provider_name:
            return entry
    return None


def get_model(
    provider_name: str | None = None, model_id: str | None = None
) -> Any | None:
    """
    Returns a Pydantic-AI model instance for the given provider and model.

    Only resolves explicit provider/model; no tiered fallback. Returns None if
    the provider is not in the registry, has no API key, or construction fails.
    """
    if not provider_name:
        return None

    entry = _get_registry_entry(provider_name)
    if not entry:
        return None

    settings = get_settings()
    if entry.settings_key and not getattr(settings, entry.settings_key, None):
        return None

    resolved_model_id = model_id or entry.default_model
    thinking_settings = get_thinking_settings(entry.id, resolved_model_id)

    # Per-provider construction (or custom adapter for non-first-class providers)
    # Thinking/reasoning is enabled via thinking_settings for a unified experience.
    if entry.id == "google":
        return GoogleModel(
            resolved_model_id,
            provider=GoogleProvider(api_key=settings.google_api_key),
            settings=thinking_settings,
        )
    if entry.id == "groq":
        return GroqModel(
            resolved_model_id,
            provider=GroqProvider(api_key=settings.groq_api_key),
            settings=thinking_settings,
        )
    if entry.id == "deepseek":
        return OpenAIChatModel(
            resolved_model_id,
            provider=DeepSeekProvider(api_key=settings.deepseek_api_key),
            settings=thinking_settings,
        )
    if entry.id == "synthetic":
        provider = OpenAIProvider(
            base_url="https://api.synthetic.new/openai/v1",
            api_key=settings.synthetic_api_key,
        )
        target = resolved_model_id
        if not target.startswith("hf:"):
            target = f"hf:{target}"
        return OpenAIChatModel(target, provider=provider, settings=thinking_settings)
    if entry.id == "mock":
        # Mock has no real model; orchestrator uses mock flow 
        # and should not call get_model for mock.
        # If called anyway, return None so callers get a clear failure.
        return None

    return None
