from typing import Any

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider

from core.settings import get_settings

# Registry of supported models per provider
AVAILABLE_MODELS: dict[str, list[str]] = {
    "google": ["gemini-2.5-flash", "gemma-3-27b-it"],
    "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "synthetic": ["hf:kimi-k2", "hf:qwen-3-coder", "hf:glm-4.5"],
    "mock": ["mock-llm", "mock-analyst", "mock-critic"],
}


def get_model(
    provider_name: str | None = None, model_id: str | None = None
) -> str | Any | None:
    """
    Returns the appropriate model provider based on configuration and availability.

    Attempts to resolve the model in the following order:
    1. Explicit provider/model request.
    2. Environment variable availability (Gemini > Groq > DeepSeek > Synthetic).
    3. Mock provider only if explicitly requested or no keys are present.

    Args:
        provider_name (str | None): Explicit provider name (e.g., 'google', 'groq').
        model_id (str | None): Explicit model identifier.

    Returns:
        str | Any | None: The configured model instance or None if no provider found.
    """
    settings = get_settings()

    # Explicit routing
    if provider_name == "google" and settings.google_api_key:
        p_google = GoogleProvider(api_key=settings.google_api_key)
        return GoogleModel(model_id or "gemini-2.5-flash", provider=p_google)

    if provider_name == "groq" and settings.groq_api_key:
        p_groq = GroqProvider(api_key=settings.groq_api_key)
        return GroqModel(model_id or "llama-3.3-70b-versatile", provider=p_groq)

    if provider_name == "deepseek" and settings.deepseek_api_key:
        p_ds = DeepSeekProvider(api_key=settings.deepseek_api_key)
        return OpenAIChatModel(model_id or "deepseek-chat", provider=p_ds)

    if provider_name == "synthetic" and settings.synthetic_api_key:
        p_syn = OpenAIProvider(
            base_url="https://api.synthetic.new/openai/v1",
            api_key=settings.synthetic_api_key,
        )
        return OpenAIChatModel(model_id or settings.synthetic_model_name, provider=p_syn)

    # Fallback to tiered priority
    # 1. Gemini
    if settings.google_api_key and not settings.is_dummy_key():
        p_google_fallback = GoogleProvider(api_key=settings.google_api_key)
        return GoogleModel("gemini-2.5-flash", provider=p_google_fallback)

    # 2. Groq
    if settings.groq_api_key:
        p_groq_fallback = GroqProvider(api_key=settings.groq_api_key)
        return GroqModel("llama-3.3-70b-versatile", provider=p_groq_fallback)

    # 3. DeepSeek
    if settings.deepseek_api_key:
        p_ds_fallback = DeepSeekProvider(api_key=settings.deepseek_api_key)
        return OpenAIChatModel(settings.deepseek_model_name, provider=p_ds_fallback)

    # 4. Synthetic
    if settings.synthetic_api_key:
        p_syn_fallback = OpenAIProvider(
            base_url="https://api.synthetic.new/openai/v1",
            api_key=settings.synthetic_api_key,
        )
        return OpenAIChatModel(settings.synthetic_model_name, provider=p_syn_fallback)

    return None
