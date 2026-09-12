
from infra.settings import Settings


def _clear_key_env(monkeypatch) -> None:
    monkeypatch.delenv("NANO_API_KEY", raising=False)
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)


def test_settings_valid_nano_api_key(monkeypatch) -> None:
    _clear_key_env(monkeypatch)
    """Verifies that valid Nano GPT API key formats are successfully accepted."""
    # Valid new key format
    settings = Settings(nano_api_key="sk-nano-123e4567-e89b-12d3-a456-426614174000")
    assert settings.nano_api_key == "sk-nano-123e4567-e89b-12d3-a456-426614174000"

    # Valid legacy format
    settings = Settings(nano_api_key="123e4567-e89b-12d3-a456-426614174000")
    assert settings.nano_api_key == "123e4567-e89b-12d3-a456-426614174000"

    # None is valid
    settings = Settings(nano_api_key=None)
    assert settings.nano_api_key is None

    # Dummy keys are valid
    settings = Settings(nano_api_key="your_nano_api_key")
    assert settings.nano_api_key == "your_nano_api_key"

    settings = Settings(nano_api_key="your-key-here")
    assert settings.nano_api_key == "your-key-here"


def test_settings_custom_nano_api_key() -> None:
    """Verifies that arbitrary string formats for nano_api_key are correctly populated."""
    settings = Settings(nano_api_key="sk-nano-custom-key-format")
    assert settings.nano_api_key == "sk-nano-custom-key-format"


def test_settings_nano_api_key_env_alias(monkeypatch) -> None:
    """Benchmark v2: .env uses NANOGPT_API_KEY; the field must accept both names."""
    import importlib

    import infra.settings as settings_mod

    monkeypatch.delenv("NANO_API_KEY", raising=False)
    monkeypatch.setenv("NANOGPT_API_KEY", "sk-nan-from-nanogpt-env")
    importlib.reload(settings_mod)
    assert settings_mod.get_settings().nano_api_key == "sk-nan-from-nanogpt-env"

    monkeypatch.setenv("NANO_API_KEY", "sk-nan-from-nano-env")
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    importlib.reload(settings_mod)
    assert settings_mod.get_settings().nano_api_key == "sk-nan-from-nano-env"
