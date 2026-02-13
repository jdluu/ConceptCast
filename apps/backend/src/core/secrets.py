import os
from typing import Any, Optional

from infisicalsdk import InfisicalClient
from loguru import logger


class SecretManager:
    """Manages secret retrieval from Infisical with local environment fallback.

    This class handles authentication with Infisical using a token and provides
    methods to fetch secrets for a specific project and environment.
    """

    def __init__(self) -> None:
        self.client: Optional[InfisicalClient] = None
        self.token = os.getenv("INFISICAL_TOKEN")
        self.site_url = os.getenv("INFISICAL_URL", "https://app.infisical.com")
        self.project_id = os.getenv("INFISICAL_PROJECT_ID")
        self.environment = os.getenv("INFISICAL_ENV", "dev")

        if self.token:
            try:
                self.client = InfisicalClient(site_url=self.site_url)
                self.client.auth.login.token(token=self.token)
                logger.info("Authenticated with Infisical")
            except Exception as e:
                logger.error(f"Failed to authenticate with Infisical: {e}")
                self.client = None

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a secret from Infisical or environment variables.

        Args:
            key: The name of the secret to fetch.
            default: The default value to return if not found.

        Returns:
            The value of the secret, or the default if not found.
        """
        # 1. Try Infisical
        if self.client and self.project_id:
            try:
                secret = self.client.secrets.get(
                    secret_name=key,
                    project_id=self.project_id,
                    environment=self.environment,
                )
                if secret and secret.secret_value:
                    return secret.secret_value
            except Exception as e:
                logger.warning(f"Infisical retrieval failed for {key}: {e}")

        # 2. Fallback to Env
        return os.getenv(key, default)


# Global singleton for secret management
secret_manager = SecretManager()
