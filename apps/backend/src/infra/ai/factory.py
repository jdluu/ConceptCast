from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import cast

import httpx
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

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
        models=("mock-analyst", "mock-architect", "mock-animator"),
        default_model="mock-analyst",
        display_name="Mock Demo",
    ),
)


class NanoOpenAIChatModel(OpenAIChatModel):
    """Custom OpenAIChatModel for Nano GPT that recovers from API parameter errors.

    If a model (e.g. zai-org/glm-5.1:thinking) returns a 400 Bad Request indicating
    invalid parameters or unsupported features under the thinking proxy, this model
    dynamically retries by stripping the ':thinking' suffix.
    """

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        try:
            return await super().request(
                messages, model_settings, model_request_parameters
            )
        except Exception as e:
            err_str = str(e).lower()
            if ":thinking" in self.model_name and (
                "400" in err_str
                or "invalid request" in err_str
                or "parameter" in err_str
            ):
                original_model = self.model_name
                fallback_model = self.model_name.replace(":thinking", "")
                self._model_name = fallback_model
                try:
                    res = await super().request(
                        messages, model_settings, model_request_parameters
                    )
                    self._model_name = original_model
                    return res
                except Exception:
                    self._model_name = original_model
                    raise
            raise

    @asynccontextmanager
    async def request_stream(  # type: ignore[no-untyped-def]  # pydantic-ai internal protocol
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context=None,
    ):
        try:
            async with super().request_stream(
                messages,
                model_settings,
                model_request_parameters,
                run_context=run_context,
            ) as stream:
                yield stream
        except Exception as e:
            err_str = str(e).lower()
            if ":thinking" in self.model_name and (
                "400" in err_str
                or "invalid request" in err_str
                or "parameter" in err_str
            ):
                original_model = self.model_name
                fallback_model = self.model_name.replace(":thinking", "")
                self._model_name = fallback_model
                try:
                    async with super().request_stream(
                        messages,
                        model_settings,
                        model_request_parameters,
                        run_context=run_context,
                    ) as stream:
                        yield stream
                finally:
                    self._model_name = original_model
            else:
                raise


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
        # Two hardening measures on the shared HTTP client:
        # 1. Timeouts — bound connect/read/write so a dead or silent upstream raises
        #    instead of blocking the workflow coroutine indefinitely (wedged animator
        #    tasks observed for 45+ min before this was added).
        # 2. Short keepalive_expiry — Nano GPT closes idle keep-alive connections
        #    server-side; stale pooled sockets then cause each request to stall through
        #    the SDK's internal retry cycle (observed as 900s wall-clock timeouts that
        #    correlated with 38 lingering CLOSE-WAIT sockets). Expiring idle connections
        #    after 10s forces fresh dials, which probe-testing shows complete promptly.
        # max_keepalive_connections=0 disables keep-alive pooling entirely: every
        # request dials fresh and closes after. This is the deliberate fix for stale
        # pooled sockets — TLS handshake overhead (~100ms) is negligible next to
        # multi-minute LLM calls.
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0),
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=0),
        )
        # max_retries=0: the openai SDK's internal retry cycle (2 retries × 600s
        # default timeout) was silently inflating attempt durations to the wall-clock
        # limit while hiding the underlying stall. The workflow's per-attempt loop owns
        # retries — failures must surface immediately with a clear error.
        openai_client = AsyncOpenAI(
            base_url="https://nano-gpt.com/api/subscription/v1",
            api_key=key,
            http_client=http_client,
            max_retries=0,
        )
        provider = OpenAIProvider(
            openai_client=openai_client,
        )

        return NanoConceptModel(
            model=NanoOpenAIChatModel(m_id, provider=provider),
            model_id=m_id,
        )


def get_available_providers_and_models(settings: Settings) -> list[ProviderModels]:
    """Returns a list of providers and their available models based on settings."""
    available = []
    for entry in PROVIDER_REGISTRY:
        # Check if the required API key is set
        if entry.settings_key:
            key_val = getattr(settings, entry.settings_key, None)
            if (
                not key_val
                or "your-key-here" in key_val.lower()
                or key_val.lower().startswith("your_")
            ):
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
