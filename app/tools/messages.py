"""MCP tools for Slack messaging."""

from functools import lru_cache
from typing import Any

from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient, SlackError
from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_slack_client() -> SlackClient:
    """Get a cached SlackClient instance.

    Returns:
        SlackClient: A cached Slack client configured with the bot token.
    """
    settings = get_settings()
    auth_provider = BearerTokenAuth(settings.slack_bot_token)
    return SlackClient(auth_provider)


async def send_user_message(user_id: str, text: str) -> dict[str, Any]:
    """Send a direct message to a Slack user.

    Args:
        user_id: The Slack user ID to send the message to.
        text: The message text to send.

    Returns:
        dict[str, Any]: The Slack API response containing message details.

    Raises:
        SlackError: If the API request fails or returns an error.
    """
    client = get_slack_client()
    return await client.send_message(channel=user_id, text=text)


async def send_channel_message(channel_id: str, text: str) -> dict[str, Any]:
    """Send a message to a Slack channel.

    Args:
        channel_id: The Slack channel ID to send the message to.
        text: The message text to send.

    Returns:
        dict[str, Any]: The Slack API response containing message details.

    Raises:
        SlackError: If the API request fails or returns an error.
    """
    client = get_slack_client()
    return await client.send_message(channel=channel_id, text=text)
