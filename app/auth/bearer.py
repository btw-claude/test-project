"""Bearer token authentication for Slack API."""

import asyncio
import random

import httpx

from app.auth.base import AuthProvider

# Valid Slack token prefixes
VALID_TOKEN_PREFIXES = ("xoxb-", "xoxa-", "xoxp-", "xoxe-")


class BearerTokenAuth(AuthProvider):
    """Bearer token authentication provider for Slack tokens.

    This implementation handles Slack OAuth tokens which are used for
    authenticating API requests to the Slack Web API.

    Supported token types:
        - xoxb-: Bot tokens
        - xoxa-: App-level tokens
        - xoxp-: User tokens
        - xoxe-: Configuration tokens
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

    async def validate_with_api(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ) -> dict:
        """Validate token against Slack's auth.test endpoint.

        This method makes an API call to Slack to verify the token is valid
        and returns information about the authenticated identity. Uses
        exponential backoff with jitter for retry logic on transient failures.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for transient failures.
            base_delay: Base delay in seconds for exponential backoff.
            max_delay: Maximum delay in seconds between retries.

        Returns:
            dict: The auth.test response containing user_id, team_id, etc.

        Raises:
            httpx.HTTPError: If the HTTP request fails after all retries.
            ValueError: If the token is invalid according to Slack's API.
        """
        url = "https://slack.com/api/auth.test"
        headers = self.get_auth_headers()

        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    if not data.get("ok"):
                        error = data.get("error", "unknown_error")
                        raise ValueError(f"Token validation failed: {error}")

                    return data

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                if attempt < max_retries:
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)
                    continue
                raise

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (502, 503, 504) and attempt < max_retries:
                    last_exception = e
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)
                    continue
                raise

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected exit from retry loop")
