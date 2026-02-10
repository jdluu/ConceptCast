import os
from typing import Any, Dict, List, Optional

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

# Registry of supported models per provider
AVAILABLE_MODELS: Dict[str, List[str]] = {
    "google": ["gemini-2.5-flash", "gemma-3-27b-it"],
    "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "synthetic": ["kimi-k2", "qwen-3-coder", "glm-4.5"],
    "mock": ["mock-llm", "mock-analyst", "mock-critic"],
}


def get_model(
    provider_name: Optional[str] = None, model_id: Optional[str] = None
) -> Optional[str | Any]:
    """
    Returns the appropriate model provider.
    If provider_name/model_id are given, attempts to use them.
    Otherwise, falls back to tiered priority:
    Gemini > Groq > DeepSeek > Synthetic > None (Mock)
    """
    gemini_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    synthetic_key = os.getenv("SYNTHETIC_API_KEY")

    # Explicit routing
    if provider_name == "google" and gemini_key:
        p = GoogleProvider(api_key=gemini_key)
        return GoogleModel(model_id or "gemini-2.5-flash", provider=p)

    if provider_name == "groq" and groq_key:
        return GroqModel(model_id or "llama-3.3-70b-versatile", api_key=groq_key)

    if provider_name == "deepseek" and deepseek_key:
        p = DeepSeekProvider(api_key=deepseek_key)
        return OpenAIChatModel(model_id or "deepseek-chat", provider=p)

    if provider_name == "synthetic" and synthetic_key:
        p = OpenAIProvider(
            base_url="https://api.synthetic.new/openai/v1", api_key=synthetic_key
        )
        return OpenAIChatModel(model_id or "kimi-k2", provider=p)

    # Fallback to tiered priority
    # 1. Gemini
    if gemini_key and gemini_key != "dummy_key_for_development":
        p = GoogleProvider(api_key=gemini_key)
        return GoogleModel("gemini-2.5-flash", provider=p)

    # 2. Groq
    if groq_key:
        return GroqModel("llama-3.3-70b-versatile", api_key=groq_key)

    # 3. DeepSeek
    if deepseek_key:
        p = DeepSeekProvider(api_key=deepseek_key)
        return OpenAIChatModel(
            os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"), provider=p
        )

    # 4. Synthetic
    if synthetic_key:
        p = OpenAIProvider(
            base_url="https://api.synthetic.new/openai/v1", api_key=synthetic_key
        )
        return OpenAIChatModel(os.getenv("SYNTHETIC_MODEL_NAME", "kimi-k2"), provider=p)

    return None
