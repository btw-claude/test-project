"""Bearer token authentication for Slack API."""

import httpx

from app.auth.base import AuthProvider

# Valid Slack token prefixes
VALID_TOKEN_PREFIXES = ("xoxb-", "xoxa-", "xoxp-")


class BearerTokenAuth(AuthProvider):
    """Bearer token authentication provider for Slack tokens.

    This implementation handles Slack OAuth tokens which are used for
    authenticating API requests to the Slack Web API.

    Supported token types:
        - xoxb-: Bot tokens
        - xoxa-: App-level tokens
        - xoxp-: User tokens
    """

    def __init__(
        self, token: str, expected_prefix: str | tuple[str, ...] | None = None
    ) -> None:
        """Initialize the bearer token authentication provider.

        Args:
            token: The Slack token (xoxb-..., xoxa-..., or xoxp-...).
            expected_prefix: Optional prefix or tuple of prefixes to validate against.
                           If None, validates against all valid Slack token prefixes.
        """
        self._token = token
        self._expected_prefix = expected_prefix

    def __repr__(self) -> str:
        """Return a debug-safe string representation.

        The token is masked to prevent accidental exposure in logs or debug output.

        Returns:
            str: A string representation with masked token.
        """
        if not self._token or len(self._token) < 10:
            return "BearerTokenAuth(****)"
        # Show prefix and last 4 chars for identification
        prefix = self._token[:5] if self._token[:5].startswith("xox") else "****"
        suffix = self._token[-4:]
        return f"BearerTokenAuth({prefix}****...{suffix})"

    def get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers with bearer token.

        Returns:
            dict[str, str]: Headers with Authorization bearer token.
        """
        return {"Authorization": f"Bearer {self._token}"}

    def validate(self) -> bool:
        """Validate that the token is properly configured.

        Checks that the token is non-empty and has a valid Slack token prefix.
        If expected_prefix was provided, validates against that specific prefix(es).

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        if not self._token:
            return False

        if self._expected_prefix is not None:
            if isinstance(self._expected_prefix, str):
                return self._token.startswith(self._expected_prefix)
            return self._token.startswith(self._expected_prefix)

        return self._token.startswith(VALID_TOKEN_PREFIXES)

    def get_token(self) -> str:
        """Get the bearer token.

        Returns:
            str: The Slack token.
        """
        return self._token

    async def validate_with_api(self, timeout: float = 10.0) -> dict:
        """Validate token against Slack's auth.test endpoint.

        This method makes an API call to Slack to verify the token is valid
        and returns information about the authenticated identity.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            dict: The auth.test response containing user_id, team_id, etc.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            ValueError: If the token is invalid according to Slack's API.
        """
        url = "https://slack.com/api/auth.test"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                raise ValueError(f"Token validation failed: {error}")

            return data
