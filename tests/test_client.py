"""Tests for the Slack client module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient, SlackError

from .conftest import MockAuthProvider


class TestSlackError:
    """Tests for SlackError exception."""

    def test_slack_error_with_code(self) -> None:
        """Test SlackError with error code."""
        error = SlackError("Test error", error_code="test_error")
        assert error.message == "Test error"
        assert error.error_code == "test_error"
        assert str(error) == "SlackError(test_error): Test error"

    def test_slack_error_without_code(self) -> None:
        """Test SlackError without error code."""
        error = SlackError("Test error")
        assert error.message == "Test error"
        assert error.error_code is None
        assert str(error) == "SlackError: Test error"


class TestBearerTokenAuth:
    """Tests for BearerTokenAuth authentication provider."""

    def test_get_auth_headers(self, bearer_auth: BearerTokenAuth) -> None:
        """Test that auth headers are properly formatted."""
        headers = bearer_auth.get_auth_headers()
        assert headers == {"Authorization": "Bearer xoxb-test-token-12345"}

    def test_validate_valid_token(self, bearer_auth: BearerTokenAuth) -> None:
        """Test validation with valid xoxb token."""
        assert bearer_auth.validate() is True

    def test_validate_invalid_token(self, invalid_bearer_auth: BearerTokenAuth) -> None:
        """Test validation with invalid token prefix."""
        assert invalid_bearer_auth.validate() is False

    def test_validate_empty_token(self) -> None:
        """Test validation with empty token."""
        auth = BearerTokenAuth("")
        assert auth.validate() is False

    def test_get_token(self, bearer_auth: BearerTokenAuth) -> None:
        """Test getting the token value."""
        assert bearer_auth.get_token() == "xoxb-test-token-12345"

    def test_apply_auth(self, bearer_auth: BearerTokenAuth) -> None:
        """Test applying auth to request kwargs."""
        request_kwargs: dict = {"url": "https://example.com"}
        result = bearer_auth.apply_auth(request_kwargs)
        assert result["headers"]["Authorization"] == "Bearer xoxb-test-token-12345"

    def test_apply_auth_preserves_existing_headers(
        self, bearer_auth: BearerTokenAuth
    ) -> None:
        """Test that apply_auth preserves existing headers."""
        request_kwargs: dict = {
            "url": "https://example.com",
            "headers": {"Content-Type": "application/json"},
        }
        result = bearer_auth.apply_auth(request_kwargs)
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["headers"]["Authorization"] == "Bearer xoxb-test-token-12345"

    # Token type extensibility tests
    def test_validate_xoxa_token(self) -> None:
        """Test validation with xoxa (app-level) token."""
        auth = BearerTokenAuth("xoxa-2-test-token-12345")
        assert auth.validate() is True

    def test_validate_xoxp_token(self) -> None:
        """Test validation with xoxp (user) token."""
        auth = BearerTokenAuth("xoxp-test-token-12345")
        assert auth.validate() is True

    def test_validate_with_expected_prefix_string(self) -> None:
        """Test validation with specific expected prefix string."""
        auth = BearerTokenAuth("xoxb-test-token", expected_prefix="xoxb-")
        assert auth.validate() is True
        auth_wrong = BearerTokenAuth("xoxa-test-token", expected_prefix="xoxb-")
        assert auth_wrong.validate() is False

    def test_validate_with_expected_prefix_tuple(self) -> None:
        """Test validation with expected prefix tuple."""
        auth = BearerTokenAuth("xoxp-test-token", expected_prefix=("xoxb-", "xoxp-"))
        assert auth.validate() is True
        auth_wrong = BearerTokenAuth("xoxa-test-token", expected_prefix=("xoxb-", "xoxp-"))
        assert auth_wrong.validate() is False

    # Debug-safe representation tests
    def test_repr_masks_token(self) -> None:
        """Test that __repr__ masks the token for security."""
        auth = BearerTokenAuth("xoxb-1234567890-abcdefgh")
        repr_str = repr(auth)
        # Should not contain the full token
        assert "1234567890-abcdefgh" not in repr_str
        # Should show prefix and suffix
        assert "xoxb-" in repr_str
        assert "efgh" in repr_str
        assert "****" in repr_str

    def test_repr_short_token(self) -> None:
        """Test __repr__ with a short token."""
        auth = BearerTokenAuth("short")
        assert repr(auth) == "BearerTokenAuth(****)"

    def test_repr_empty_token(self) -> None:
        """Test __repr__ with empty token."""
        auth = BearerTokenAuth("")
        assert repr(auth) == "BearerTokenAuth(****)"

    def test_repr_non_xox_prefix(self) -> None:
        """Test __repr__ with non-standard prefix."""
        auth = BearerTokenAuth("other-1234567890-token")
        repr_str = repr(auth)
        assert "other" not in repr_str
        assert "****" in repr_str

    # API validation tests
    @pytest.mark.asyncio
    async def test_validate_with_api_success(self) -> None:
        """Test successful API validation."""
        auth = BearerTokenAuth("xoxb-test-token")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "user_id": "U12345",
            "team_id": "T12345",
            "user": "testbot",
            "team": "Test Team",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await auth.validate_with_api()

            assert result["ok"] is True
            assert result["user_id"] == "U12345"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://slack.com/api/auth.test"

    @pytest.mark.asyncio
    async def test_validate_with_api_invalid_token(self) -> None:
        """Test API validation with invalid token."""
        auth = BearerTokenAuth("xoxb-invalid-token")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": False,
            "error": "invalid_auth",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError) as exc_info:
                await auth.validate_with_api()

            assert "invalid_auth" in str(exc_info.value)


class TestSlackClient:
    """Tests for SlackClient."""

    def test_base_url(self) -> None:
        """Test that BASE_URL is correct."""
        assert SlackClient.BASE_URL == "https://slack.com/api"

    def test_init(self, mock_auth_provider: MockAuthProvider) -> None:
        """Test client initialization."""
        client = SlackClient(mock_auth_provider)
        assert client._auth_provider is mock_auth_provider

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        slack_client: SlackClient,
        mock_httpx_response: MagicMock,
    ) -> None:
        """Test successful message sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response
            mock_client_class.return_value = mock_client

            result = await slack_client.send_message("C12345", "Hello, World!")

            assert result["ok"] is True
            assert result["channel"] == "C12345"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://slack.com/api/chat.postMessage"
            assert call_args[1]["json"]["channel"] == "C12345"
            assert call_args[1]["json"]["text"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_send_message_api_error(
        self,
        slack_client: SlackClient,
        mock_httpx_error_response: MagicMock,
    ) -> None:
        """Test message sending with Slack API error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_error_response
            mock_client_class.return_value = mock_client

            with pytest.raises(SlackError) as exc_info:
                await slack_client.send_message("invalid-channel", "Hello")

            assert exc_info.value.error_code == "channel_not_found"

    @pytest.mark.asyncio
    async def test_send_message_http_error(
        self,
        slack_client: SlackClient,
    ) -> None:
        """Test message sending with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(SlackError) as exc_info:
                await slack_client.send_message("C12345", "Hello")

            assert exc_info.value.error_code == "http_error"

    @pytest.mark.asyncio
    async def test_send_message_request_error(
        self,
        slack_client: SlackClient,
    ) -> None:
        """Test message sending with request error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value = mock_client

            with pytest.raises(SlackError) as exc_info:
                await slack_client.send_message("C12345", "Hello")

            assert exc_info.value.error_code == "request_error"
