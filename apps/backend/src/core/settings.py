"""Centralized application configuration via Pydantic Settings.

Loads all API keys and configuration from environment variables,
replacing scattered os.getenv() calls across the codebase.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        google_api_key: Google AI API key for Gemini models.
        groq_api_key: Groq API key for Llama/Mixtral models.
        deepseek_api_key: DeepSeek API key.
        synthetic_api_key: Synthetic provider API key.
        deepseek_model_name: Override for DeepSeek model name.
        synthetic_model_name: Override for Synthetic model name.
        database_url: SQLAlchemy database URL.
        cors_origins: Comma-separated list of allowed CORS origins.
    """

    google_api_key: str | None = None
    groq_api_key: str | None = None
    deepseek_api_key: str | None = None
    synthetic_api_key: str | None = None
    deepseek_model_name: str = "deepseek-chat"
    synthetic_model_name: str = "kimi-k2"
    database_url: str = "sqlite:///../../conceptcast.db"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": "../../.env", "extra": "ignore"}

    def has_any_api_key(self) -> bool:
        """Returns True if at least one real AI provider API key is set."""
        return bool(
            self.google_api_key
            or self.groq_api_key
            or self.deepseek_api_key
            or self.synthetic_api_key
        )

    def is_dummy_key(self) -> bool:
        """Returns True if the Google key is the development placeholder."""
        return self.google_api_key == "dummy_key_for_development"


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton Settings instance.

    Values are prioritized from Infisical if configured, otherwise from .env.

    Returns:
        Settings: The application settings.
    """
    from core.secrets import secret_manager

    return Settings(
        google_api_key=secret_manager.get_secret("GOOGLE_API_KEY"),
        groq_api_key=secret_manager.get_secret("GROQ_API_KEY"),
        deepseek_api_key=secret_manager.get_secret("DEEPSEEK_API_KEY"),
        synthetic_api_key=secret_manager.get_secret("SYNTHETIC_API_KEY"),
        database_url=secret_manager.get_secret("DATABASE_URL", "sqlite:///../../conceptcast.db"),
        cors_origins=secret_manager.get_secret("CORS_ORIGINS", "http://localhost:5173"),
    )
