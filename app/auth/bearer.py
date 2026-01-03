"""Bearer token authentication for Slack API."""

from app.auth.base import AuthProvider


class BearerTokenAuth(AuthProvider):
    """Bearer token authentication provider for Slack xoxb tokens.

    This implementation handles Slack Bot OAuth tokens (xoxb-...) which
    are used for authenticating API requests to the Slack Web API.
    """

    def __init__(self, token: str) -> None:
        """Initialize the bearer token authentication provider.

        Args:
            token: The Slack bot token (xoxb-...).
        """
        self._token = token

    def get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers with bearer token.

        Returns:
            dict[str, str]: Headers with Authorization bearer token.
        """
        return {"Authorization": f"Bearer {self._token}"}

    def validate(self) -> bool:
        """Validate that the token is properly configured.

        Checks that the token is non-empty and has the expected xoxb prefix
        for Slack bot tokens.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        if not self._token:
            return False
        return self._token.startswith("xoxb-")

    def get_token(self) -> str:
        """Get the bearer token.

        Returns:
            str: The Slack bot token.
        """
        return self._token
