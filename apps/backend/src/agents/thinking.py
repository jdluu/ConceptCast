"""
Unified thinking/reasoning using Pydantic AI's model settings, extended per provider.

We start with Pydantic AI's settings types (ModelSettings and provider-specific
GoogleModelSettings, GroqModelSettings, etc.) and only add the thinking-related
fields for each provider. The factory passes these as model-level defaults when
creating the model (see Agents > Model (Run) Settings > Settings precedence:
https://ai.pydantic.dev/agent/ ). Run-time and agent-level overrides still apply.

When implementing or changing provider behavior, use Context7 (or the latest
Pydantic AI docs) for current model settings and thinking APIs.
"""

from typing import Protocol

# Use Pydantic AI's provider-specific settings so we extend
# the framework, not replace it.
from pydantic_ai.models.google import GoogleModelSettings
from pydantic_ai.models.groq import GroqModelSettings
from pydantic_ai.settings import ModelSettings


class ThinkingAdapter(Protocol):
    """Adapter that returns Pydantic AI model settings to enable
    thinking for a provider/model."""

    def __call__(self, provider_id: str, model_id: str) -> ModelSettings | None:
        """Return settings to pass when building the model, or None to skip."""
        ...


def _adapter_deepseek(provider_id: str, model_id: str) -> ModelSettings | None:
    """DeepSeek: enable thinking via extra_body (OpenAI-compatible API)."""
    if provider_id != "deepseek":
        return None
    # ModelSettings.extra_body is the Pydantic AI way to pass provider-specific params.
    # See https://api-docs.deepseek.com/guides/thinking_mode
    return ModelSettings(extra_body={"thinking": {"type": "enabled"}})


def _adapter_google(provider_id: str, model_id: str) -> ModelSettings | None:
    """Google: use Pydantic AI's GoogleModelSettings with google_thinking_config."""
    if provider_id != "google":
        return None
    # https://ai.google.dev/gemini-api/docs/thinking
    return GoogleModelSettings(google_thinking_config={"thinking_budget": 1024})


def _adapter_groq(provider_id: str, model_id: str) -> ModelSettings | None:
    """Groq: use Pydantic AI's GroqModelSettings with groq_reasoning_format."""
    if provider_id != "groq":
        return None
    # https://console.groq.com/docs/reasoning
    return GroqModelSettings(groq_reasoning_format="parsed")


def _adapter_noop(provider_id: str, model_id: str) -> ModelSettings | None:
    """No thinking config (synthetic, mock, or unsupported)."""
    return None


# Registry: provider_id -> adapter.
# Extend with Pydantic AI's settings types per provider.
THINKING_ADAPTERS: dict[str, ThinkingAdapter] = {
    "deepseek": _adapter_deepseek,
    "google": _adapter_google,
    "groq": _adapter_groq,
    "synthetic": _adapter_noop,
    "mock": _adapter_noop,
}


def get_thinking_settings(provider_id: str, model_id: str) -> ModelSettings | None:
    """
    Returns Pydantic AI model settings to enable thinking
    for the given provider and model.

    Uses the adapter for that provider; each adapter returns the appropriate
    framework settings type (ModelSettings or provider-specific settings) with
    only the thinking-related fields set.
    """
    adapter = THINKING_ADAPTERS.get(provider_id)
    if not adapter:
        return None
    return adapter(provider_id, model_id)
