"""Tests for the Slack messaging tools."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.messages import send_channel_message, send_user_message


class TestSendUserMessage:
    """Tests for send_user_message tool."""

    @pytest.mark.asyncio
    async def test_send_user_message_success(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test successful user message sending."""
        mock_response = {
            "ok": True,
            "channel": "U12345",
            "ts": "1234567890.123456",
            "message": {"type": "message", "text": "Hello user!"},
        }

        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.send_message.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await send_user_message("U12345", "Hello user!")

            assert result == mock_response
            mock_client.send_message.assert_called_once_with(
                channel="U12345", text="Hello user!"
            )

    @pytest.mark.asyncio
    async def test_send_user_message_uses_correct_token(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that send_user_message uses the bot token from settings."""
        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.BearerTokenAuth") as mock_auth_class,
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.send_message.return_value = {"ok": True}
            mock_client_class.return_value = mock_client

            await send_user_message("U12345", "Hello")

            mock_auth_class.assert_called_once_with(mock_settings.slack_bot_token)


class TestSendChannelMessage:
    """Tests for send_channel_message tool."""

    @pytest.mark.asyncio
    async def test_send_channel_message_success(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test successful channel message sending."""
        mock_response = {
            "ok": True,
            "channel": "C12345",
            "ts": "1234567890.123456",
            "message": {"type": "message", "text": "Hello channel!"},
        }

        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.send_message.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await send_channel_message("C12345", "Hello channel!")

            assert result == mock_response
            mock_client.send_message.assert_called_once_with(
                channel="C12345", text="Hello channel!"
            )

    @pytest.mark.asyncio
    async def test_send_channel_message_uses_correct_token(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that send_channel_message uses the bot token from settings."""
        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.BearerTokenAuth") as mock_auth_class,
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.send_message.return_value = {"ok": True}
            mock_client_class.return_value = mock_client

            await send_channel_message("C12345", "Hello")

            mock_auth_class.assert_called_once_with(mock_settings.slack_bot_token)

    @pytest.mark.asyncio
    async def test_send_channel_message_creates_new_client(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that each call creates a new SlackClient instance."""
        with (
            patch("app.tools.messages.get_settings", return_value=mock_settings),
            patch("app.tools.messages.SlackClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.send_message.return_value = {"ok": True}
            mock_client_class.return_value = mock_client

            await send_channel_message("C11111", "First")
            await send_channel_message("C22222", "Second")

            assert mock_client_class.call_count == 2
