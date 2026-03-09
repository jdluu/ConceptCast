from typing import Any, cast

from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class DeepSeekModel(OpenAIChatModel):
    """Custom OpenAI-compatible model for DeepSeek.

    Handles specific DeepSeek API requirements, such as stripping tool_choice
    for reasoner models.
    """

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: OpenAIChatModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> Any:
        """Executes the completion request, handling model-specific quirks.

        Strips 'tool_choice' for 'deepseek-reasoner' to prevent 400 errors.

        Args:
            messages: List of model messages.
            stream: Whether to stream the response.
            model_settings: Specialized OpenAI model settings.
            model_request_parameters: Standard request parameters.

        Returns:
            The raw provider response.
        """
        if self.model_name == "deepseek-reasoner":
            original_completions = self.client.chat.completions

            class CompletionsProxy:
                def __getattr__(self, name: str) -> Any:
                    return getattr(original_completions, name)

                async def create(self, **kwargs: Any) -> Any:
                    kwargs.pop("tool_choice", None)
                    return await original_completions.create(**kwargs)

            self.client.chat.completions = cast(Any, CompletionsProxy())  # type: ignore[misc]
            try:
                return await super()._completions_create(  # type: ignore[call-overload]
                    messages, stream, model_settings, model_request_parameters
                )
            finally:
                self.client.chat.completions = original_completions  # type: ignore[misc]
        else:
            return await super()._completions_create(  # type: ignore[call-overload]
                messages, stream, model_settings, model_request_parameters
            )


class DeepSeekModelProvider(BaseProvider):
    """Provider adapter for DeepSeek models.

    Uses the OpenAI-compatible API at 'https://api.deepseek.com'.
    """

    def __init__(self, settings: Settings):
        """Initializes the DeepSeek provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates and configures a DeepSeekModel.

        Args:
            model_id: The DeepSeek model identifier (e.g., 'deepseek-chat').

        Returns:
            A configured DeepSeekModel instance.
        """
        return DeepSeekModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.deepseek.com",
                api_key=self.settings.deepseek_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, model_id: str) -> ModelSettings | None:
        """Retrieves DeepSeek-specific model configurations.

        Args:
            model_id: The DeepSeek model identifier.

        Returns:
            ModelSettings with tool calling configuration.
        """
        if model_id == "deepseek-reasoner":
            return ModelSettings()
        return ModelSettings(tool_choice="auto")  # type: ignore[typeddict-unknown-key]
