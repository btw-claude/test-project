"""Abstract base class for authentication providers."""

from abc import ABC, abstractmethod
from typing import Any


class AuthenticationError(Exception):
    """Exception raised when authentication fails.

    This exception is raised when credentials are invalid, expired, or revoked
    during API validation.
    """

    pass


class AuthProvider(ABC):
    """Abstract base class for authentication providers.

    All authentication implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            dict[str, str]: A dictionary of HTTP headers for authentication.
        """
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Validate that the authentication credentials are properly configured.

        Returns:
            bool: True if credentials are valid and configured, False otherwise.
        """
        ...

    @abstractmethod
    def get_token(self) -> str:
        """Get the authentication token.

        Returns:
            str: The authentication token.
        """
        ...

    @abstractmethod
    async def validate_with_api(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ) -> dict:
        """Validate credentials against the authentication API.

        This method should make an API call to verify the credentials are valid
        and return information about the authenticated identity. Implementations
        should support retry logic with exponential backoff for transient failures.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for transient failures.
            base_delay: Base delay in seconds for exponential backoff.
            max_delay: Maximum delay in seconds between retries.

        Returns:
            dict: Response from the authentication API containing identity info.

        Raises:
            app.auth.base.AuthenticationError: If credentials are invalid, expired, or revoked.
            ConnectionError: If network issues persist after all retry attempts.
            TimeoutError: If the request times out after all retry attempts.
            ValueError: If the authentication configuration is invalid.
        """
        ...

    def apply_auth(self, request_kwargs: dict[str, Any]) -> dict[str, Any]:
        """Apply authentication to request kwargs.

        Args:
            request_kwargs: The keyword arguments for the request.

        Returns:
            dict[str, Any]: Updated request kwargs with authentication applied.
        """
        headers = request_kwargs.get("headers", {})
        headers.update(self.get_auth_headers())
        request_kwargs["headers"] = headers
        return request_kwargs
