"""Tests for the Slack messaging tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.messages import (
    get_slack_client,
    reset_slack_client,
    send_channel_message,
    send_user_message,
)


class TestGetSlackClient:
    """Tests for get_slack_client factory function."""

    def test_get_slack_client_creates_client_with_correct_auth(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that get_slack_client creates a client with the correct token."""
        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.BearerTokenAuth") as mock_auth_class,
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            # Clear the cache before testing
            reset_slack_client()

            get_slack_client()

            mock_auth_class.assert_called_once_with(mock_settings.slack_bot_token)
            mock_client_class.assert_called_once()

    def test_get_slack_client_caches_instance(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that get_slack_client returns a cached instance on subsequent calls."""
        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            # Clear the cache before testing
            reset_slack_client()

            client1 = get_slack_client()
            client2 = get_slack_client()

            # SlackClient should only be instantiated once
            assert mock_client_class.call_count == 1
            assert client1 is client2


class TestResetSlackClient:
    """Tests for reset_slack_client function."""

    def test_reset_slack_client_clears_cache(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that reset_slack_client clears the cached instance."""
        mock_client_1 = MagicMock()
        mock_client_2 = MagicMock()

        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch(
                "app.tools.messages.SlackClient",
                side_effect=[mock_client_1, mock_client_2],
            ) as mock_client_class,
        ):
            # Clear the cache before testing
            reset_slack_client()

            # Get a client instance
            client1 = get_slack_client()

            # Reset the cache
            reset_slack_client()

            # Get another client instance - should be a new one
            client2 = get_slack_client()

            # SlackClient should be instantiated twice
            assert mock_client_class.call_count == 2
            # The instances should be different objects
            assert client1 is mock_client_1
            assert client2 is mock_client_2
            assert client1 is not client2


class TestSendUserMessage:
    """Tests for send_user_message tool."""

    @pytest.mark.asyncio
    async def test_send_user_message_success(self) -> None:
        """Test successful user message sending."""
        mock_response = {
            "ok": True,
            "channel": "U12345",
            "ts": "1234567890.123456",
            "message": {"type": "message", "text": "Hello user!"},
        }

        mock_client = AsyncMock()
        mock_client.send_message.return_value = mock_response

        with patch("app.tools.messages.get_slack_client", return_value=mock_client):
            result = await send_user_message("U12345", "Hello user!")

            assert result == mock_response
            mock_client.send_message.assert_called_once_with(
                channel="U12345", text="Hello user!"
            )


class TestSendChannelMessage:
    """Tests for send_channel_message tool."""

    @pytest.mark.asyncio
    async def test_send_channel_message_success(self) -> None:
        """Test successful channel message sending."""
        mock_response = {
            "ok": True,
            "channel": "C12345",
            "ts": "1234567890.123456",
            "message": {"type": "message", "text": "Hello channel!"},
        }

        mock_client = AsyncMock()
        mock_client.send_message.return_value = mock_response

        with patch("app.tools.messages.get_slack_client", return_value=mock_client):
            result = await send_channel_message("C12345", "Hello channel!")

            assert result == mock_response
            mock_client.send_message.assert_called_once_with(
                channel="C12345", text="Hello channel!"
            )

    @pytest.mark.asyncio
    async def test_send_channel_message_reuses_cached_client(self) -> None:
        """Test that multiple calls reuse the same cached client instance."""
        mock_client = AsyncMock()
        mock_client.send_message.return_value = {"ok": True}

        with patch(
            "app.tools.messages.get_slack_client", return_value=mock_client
        ) as mock_get_client:
            await send_channel_message("C11111", "First")
            await send_channel_message("C22222", "Second")

            # get_slack_client should be called twice but returns the same cached instance
            assert mock_get_client.call_count == 2
            # The client itself should have send_message called twice
            assert mock_client.send_message.call_count == 2
