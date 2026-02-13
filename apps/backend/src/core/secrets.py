import os
from typing import Any, Optional
from loguru import logger


class SecretManager:
    """Manages secret retrieval from environment variables.
    
    Simplified to use standard environment variables for prototyping.
    """

    def __init__(self) -> None:
        pass

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a secret from environment variables.

        Args:
            key: The name of the secret to fetch.
            default: The default value to return if not found.

        Returns:
            The value of the secret, or the default if not found.
        """
        return os.getenv(key, default)


# Global singleton for secret management
secret_manager = SecretManager()
