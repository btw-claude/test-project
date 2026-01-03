"""MCP tools for Slack messaging."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient, SlackError
from app.config.settings import get_settings


mcp = FastMCP("slack-messaging")


def _get_slack_client() -> SlackClient:
    """Get a configured Slack client instance.

    Returns:
        SlackClient: Configured Slack client with bearer token auth.
    """
    settings = get_settings()
    auth_provider = BearerTokenAuth(settings.slack_bot_token)
    return SlackClient(auth_provider)


@mcp.tool()
async def send_user_message(user_id: str, text: str) -> dict[str, Any]:
    """Send a direct message to a Slack user.

    Args:
        user_id: The Slack user ID to send the message to (e.g., 'U1234567890').
        text: The message text to send.

    Returns:
        dict[str, Any]: The Slack API response containing message details.

    Raises:
        SlackError: If the API request fails or returns an error.
    """
    client = _get_slack_client()
    return await client.send_message(channel=user_id, text=text)


@mcp.tool()
async def send_channel_message(channel_id: str, text: str) -> dict[str, Any]:
    """Send a message to a Slack channel.

    Args:
        channel_id: The Slack channel ID to send the message to (e.g., 'C1234567890').
        text: The message text to send.

    Returns:
        dict[str, Any]: The Slack API response containing message details.

    Raises:
        SlackError: If the API request fails or returns an error.
    """
    client = _get_slack_client()
    return await client.send_message(channel=channel_id, text=text)
