"""Centralized application configuration via Pydantic Settings.

Loads all API keys and configuration from environment variables,
replacing scattered os.getenv() calls across the codebase.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


def _discover_project_root() -> Path:
    """Traverses upward from the current file to discover the project root directory.

    Heuristically identifies the root by searching for 'pnpm-workspace.yaml',
    '.git', or 'pyproject.toml' in combination with an 'apps' directory.

    Returns:
        Path: The absolute path to the discovered project root.
    """
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pnpm-workspace.yaml").exists() or (current / ".git").exists():
            return current
        if (current / "pyproject.toml").exists() and (current.parent / "apps").exists():
            return current.parent.parent
        if current.parent == current:
            break
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent.parent.parent


PROJECT_ROOT = _discover_project_root()
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Application settings and secrets loaded from environment variables and .env.

    Attributes:
        nano_api_key: Nano GPT provider API key.
        context7_api_key: Context7 API key for high-quality package documentation.
        context7_cache_ttl_seconds: Seconds before cached documentation expires.
        context7_cache_max_entries: Max entries kept in the documentation cache.
        context7_max_retries: Retry limit for transient Context7 API errors.
        nano_model_name: Overridable model identifier for the Nano GPT provider.
        render_quality: Default Manim render quality (low, medium, high).
        streamed_thoughts_max_entries: Max thought deltas stored per job execution.
        database_url: SQLAlchemy compatible database connection string.
        redis_url: Connection URL for the Taskiq Redis backend.
        cors_origins: List of allowed origins for cross-origin requests.
        data_dir: Absolute path for storing application state and artifacts.
        pricing_input_rate: Estimated USD cost per 1k input tokens.
        pricing_output_rate: Estimated USD cost per 1k output tokens.
        pricing_render_rate_per_min: Estimated rendering cost per minute.
        pricing_base_overhead: Fixed processing overhead per job.
    """

    nano_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("nano_api_key", "NANO_API_KEY", "NANOGPT_API_KEY"),
    )
    context7_api_key: str | None = None
    context7_cache_ttl_seconds: int = 1800
    context7_cache_max_entries: int = 256
    context7_max_retries: int = 2
    nano_model_name: str = "openai/gpt-oss-120b"
    render_quality: str = "ql"
    streamed_thoughts_max_entries: int = 500
    # Max outer-loop attempts for animator self-correction (preview + review loop).
    animation_review_max_iterations: int = 10
    # Max attempts to repair Manim code after a render failure (patch-first loop).
    render_repair_max_attempts: int = 10

    # Per-agent pydantic-ai request limits.
    # Each unit corresponds to one model round-trip (prompt + tool calls + retries).
    agent_request_limit_analyst: int = 10
    agent_request_limit_architect: int = 10
    agent_request_limit_animator: int = 25

    curriculum_validation_enabled: bool = False

    # Benchmark v2 sampling pins (parity across arms). None = provider default.
    benchmark_temperature: float | None = None
    benchmark_seed: int | None = None
    benchmark_trace_dir: str | None = None
    database_url: str = "sqlite:///" + str(PROJECT_ROOT / "data" / "conceptcast.db")
    redis_url: str = "redis://localhost:6379"
    cors_origins: str = "http://localhost:5173"
    data_dir: Path = PROJECT_ROOT / "data"

    # Pricing Estimation Constants (USD)
    pricing_input_rate: float = 0.005 / 1000
    pricing_output_rate: float = 0.015 / 1000
    pricing_render_rate_per_min: float = 0.10
    pricing_base_overhead: float = 0.02

    # Domain Constants
    mock_topic: str = "Quantum Entanglement"

    @property
    def jobs_dir(self) -> Path:
        """Absolute path to the dedicated storage for job artifacts."""
        return self.data_dir / "jobs"

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "extra": "ignore",
        "env_prefix": "",
        "case_sensitive": False,
    }

    def has_any_api_key(self) -> bool:
        """Determines if any valid AI provider API key is available.

        Returns:
            bool: True if at least one API key is detected.
        """
        return bool(self.nano_api_key)

    def is_dummy_key(self) -> bool:
        """Checks if configured API keys are placeholders.

        Returns:
            bool: True if keys match known dummy values (e.g., 'your-key-here', 'your_').
        """
        val = self.nano_api_key
        if not val:
            return True
        v = val.lower()
        return "your-key-here" in v or v.startswith("your_")


@lru_cache
def get_settings() -> Settings:
    """Returns a memoized singleton instance of the application settings.

    Environment variables are parsed on first call and cached for subsequent use.

    Returns:
        Settings: The parsed application configuration.
    """
    return Settings()
