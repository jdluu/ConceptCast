"""Common Pydantic schemas shared across multiple API domains.

Includes shared structures for logging, model capabilities, and generic responses.
"""

from pydantic import BaseModel


class ThoughtLog(BaseModel):
    """A captured reasoning step from the agent council."""

    agent: str
    phase: str
    content: str
    ts: str


class ProviderModels(BaseModel):
    """Capabilities and model list for a specific AI provider."""

    provider: str
    models: list[str]
    display_name: str | None = None


class AvailableModelsResponse(BaseModel):
    """Listing of all reachable AI providers and their models."""

    available: list[ProviderModels]
