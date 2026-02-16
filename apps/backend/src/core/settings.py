"""Centralized application configuration via Pydantic Settings.

Loads all API keys and configuration from environment variables,
replacing scattered os.getenv() calls across the codebase.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from project root .env
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        google_api_key: Google AI API key for Gemini models.
        groq_api_key: Groq API key for Llama/Mixtral models.
        deepseek_api_key: DeepSeek API key.
        synthetic_api_key: Synthetic provider API key.
        context7_api_key: Context7 API key for doc retrieval (e.g. Manim Community).
        context7_cache_ttl_seconds: TTL for Context7 response cache.
        context7_cache_max_entries: Max Context7 cache entries kept in-memory.
        context7_max_retries: Retries for transient Context7 API failures.
        deepseek_model_name: Override for DeepSeek model name.
        synthetic_model_name: Override for Synthetic model name.
        render_quality: Manim quality profile for rendering (ql/qm/qh).
        streamed_thoughts_max_entries: Max persisted streamed thought deltas per job.
        database_url: SQLAlchemy database URL.
        cors_origins: Comma-separated list of allowed CORS origins.
    """

    google_api_key: str | None = None
    groq_api_key: str | None = None
    deepseek_api_key: str | None = None
    synthetic_api_key: str | None = None
    context7_api_key: str | None = None
    context7_cache_ttl_seconds: int = 1800
    context7_cache_max_entries: int = 256
    context7_max_retries: int = 2
    deepseek_model_name: str = "deepseek-chat"
    synthetic_model_name: str = "hf:deepseek-ai/DeepSeek-V3"
    render_quality: str = "ql"
    streamed_thoughts_max_entries: int = 500
    animation_review_max_iterations: int = 3
    animation_review_enabled: bool = True
    database_url: str = "sqlite:///" + str(PROJECT_ROOT / "conceptcast.db")
    cors_origins: str = "http://localhost:5173"
    data_dir: Path = PROJECT_ROOT / "data"

    @property
    def jobs_dir(self) -> Path:
        """Returns the absolute path to the jobs artifact directory."""
        return self.data_dir / "jobs"

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "extra": "ignore"}

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

    Values are loaded from environment variables and .env file.

    Returns:
        Settings: The application settings.
    """
    return Settings()
