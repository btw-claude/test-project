"""Pytest fixtures for slack-agent tests."""

from unittest.mock import MagicMock

import pytest

from app.auth.base import AuthProvider
from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient


class MockAuthProvider(AuthProvider):
    """Mock authentication provider for testing."""

    def __init__(self, token: str = "test-token") -> None:
        self._token = token

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def validate(self) -> bool:
        return bool(self._token)

    def get_token(self) -> str:
        return self._token


@pytest.fixture
def required_env_vars() -> dict[str, str]:
    """Base required environment variables for Settings tests."""
    return {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
    }


@pytest.fixture
def mock_auth_provider() -> MockAuthProvider:
    """Provide a mock authentication provider."""
    return MockAuthProvider()


@pytest.fixture
def bearer_auth() -> BearerTokenAuth:
    """Provide a BearerTokenAuth instance with a test token."""
    return BearerTokenAuth("xoxb-test-token-12345")


@pytest.fixture
def invalid_bearer_auth() -> BearerTokenAuth:
    """Provide a BearerTokenAuth instance with an invalid token."""
    return BearerTokenAuth("invalid-token")


@pytest.fixture
def slack_client(mock_auth_provider: MockAuthProvider) -> SlackClient:
    """Provide a SlackClient instance with mock auth (not initialized)."""
    return SlackClient(mock_auth_provider)


@pytest.fixture
async def async_slack_client(mock_auth_provider: MockAuthProvider) -> SlackClient:
    """Provide an initialized SlackClient instance with mock auth via context manager."""
    async with SlackClient(mock_auth_provider) as client:
        yield client


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Provide a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "ok": True,
        "channel": "C12345",
        "ts": "1234567890.123456",
        "message": {
            "type": "message",
            "text": "Test message",
        },
    }
    return response


@pytest.fixture
def mock_httpx_error_response() -> MagicMock:
    """Provide a mock httpx error response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "ok": False,
        "error": "channel_not_found",
    }
    return response


@pytest.fixture
def mock_settings() -> MagicMock:
    """Provide mock settings."""
    settings = MagicMock()
    settings.slack_bot_token = "xoxb-mock-bot-token"
    settings.slack_app_token = "xapp-mock-app-token"
    settings.slack_signing_secret = "mock-signing-secret"
    settings.app_env = "development"
    settings.app_debug = False
    settings.app_log_level = "INFO"
    settings.api_host = "0.0.0.0"
    settings.api_port = 8000
    return settings
