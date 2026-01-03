"""Abstract base class for authentication providers."""

from abc import ABC, abstractmethod
from typing import Any


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
    async def validate_with_api(self, timeout: float = 10.0) -> dict:
        """Validate credentials against the authentication API.

        This method should make an API call to verify the credentials are valid
        and return information about the authenticated identity.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            dict: Response from the authentication API containing identity info.

        Raises:
            Exception: If validation fails or the API request errors.
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
