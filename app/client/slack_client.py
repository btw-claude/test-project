"""Async HTTP client for Slack API."""

from types import TracebackType
from typing import Any

import httpx

from app.auth.base import AuthProvider


class SlackError(Exception):
    """Exception raised for Slack API errors.

    Attributes:
        message: Error message describing what went wrong.
        error_code: Optional Slack API error code (e.g., 'channel_not_found').
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize the SlackError.

        Args:
            message: Error message describing what went wrong.
            error_code: Optional Slack API error code.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"SlackError({self.error_code}): {self.message}"
        return f"SlackError: {self.message}"


class SlackClient:
    """Async HTTP client for Slack Web API.

    This client provides methods to interact with the Slack Web API
    using async HTTP requests. Uses a shared httpx.AsyncClient for
    connection pooling and improved performance.

    Usage:
        async with SlackClient(auth_provider) as client:
            await client.send_message("#general", "Hello!")
    """

    BASE_URL = "https://slack.com/api"

    def __init__(self, auth_provider: AuthProvider) -> None:
        """Initialize the Slack client.

        Args:
            auth_provider: Authentication provider for API requests.
        """
        self._auth_provider = auth_provider
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SlackClient":
        """Enter async context and create shared HTTP client."""
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context and close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send_message(self, channel: str, text: str) -> dict[str, Any]:
        """Send a message to a Slack channel or user.

        Args:
            channel: The channel ID, channel name, or user ID to send the message to.
            text: The message text to send.

        Returns:
            dict[str, Any]: The Slack API response containing message details.

        Raises:
            SlackError: If the API request fails or returns an error.
            RuntimeError: If called outside of async context manager.
        """
        if self._client is None:
            raise RuntimeError(
                "SlackClient must be used as an async context manager. "
                "Use 'async with SlackClient(auth) as client:'"
            )

        url = f"{self.BASE_URL}/chat.postMessage"
        headers = self._auth_provider.get_auth_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "channel": channel,
            "text": text,
        }

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise SlackError(
                f"HTTP error occurred: {e.response.status_code}",
                error_code="http_error",
            ) from e
        except httpx.RequestError as e:
            raise SlackError(
                f"Request failed: {str(e)}",
                error_code="request_error",
            ) from e

        data = response.json()

        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise SlackError(
                f"Slack API error: {error_code}",
                error_code=error_code,
            )

        return data
