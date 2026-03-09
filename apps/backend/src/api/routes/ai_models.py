"""API endpoints for discovering available AI providers and their models.

Dynamically filters models based on configured API keys and local capability.
"""

from fastapi import APIRouter

from api.schemas import AvailableModelsResponse
from infra.ai.factory import get_available_providers_and_models
from infra.settings import get_settings

router = APIRouter()


@router.get("", response_model=AvailableModelsResponse)
async def get_available_models() -> AvailableModelsResponse:
    """Retrieves the list of supported AI providers and their models.

    Only includes providers for which the user has an API key configured;
    mock is always included.

    Returns:
        AvailableModelsResponse containing the list of available providers and models.
    """
    settings = get_settings()
    result = get_available_providers_and_models(settings)
    return AvailableModelsResponse(available=result)
