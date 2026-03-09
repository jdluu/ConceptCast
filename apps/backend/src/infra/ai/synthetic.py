from typing import Any, cast

from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.settings import ModelSettings

from infra.settings import Settings

from .base import BaseProvider


class SyntheticModel(OpenAIChatModel):
    """Custom model adapter for Synthetic.new proxies.

    Handles quirks of various Hugging Face models proxied through Synthetic.
    """

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: OpenAIChatModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> Any:
        """Executes the completion request while stripping unsupported parameters.

        Strips 'tool_choice' as many HF proxies are strict and return 400 errors
        if it is present.

        Args:
            messages: List of model messages.
            stream: Whether to stream the response.
            model_settings: Specialized OpenAI model settings.
            model_request_parameters: Standard request parameters.

        Returns:
            The raw provider response.
        """
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


class SyntheticModelProvider(BaseProvider):
    """Provider adapter for Synthetic AI models.

    Points to the OpenAI-compatible proxy at 'https://api.synthetic.new/openai/v1'.
    """

    def __init__(self, settings: Settings):
        """Initializes the Synthetic provider.

        Args:
            settings: Global application settings containing API keys.
        """
        self.settings = settings

    def create_model(self, model_id: str) -> Model:
        """Creates and configures a SyntheticModel.

        Args:
            model_id: The synthetic model identifier.

        Returns:
            A configured SyntheticModel instance.
        """
        return SyntheticModel(
            model_id,
            provider=PydanticOpenAIProvider(
                base_url="https://api.synthetic.new/openai/v1",
                api_key=self.settings.synthetic_api_key,
            ),
            settings=self.get_settings(model_id),
        )

    def get_settings(self, _model_id: str) -> ModelSettings | None:
        """Retrieves Synthetic-specific configurations.

        Args:
            model_id: The model identifier.

        Returns:
            Always returns None for Synthetic.
        """
        return None
