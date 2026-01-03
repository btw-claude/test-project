"""MCP tools for Slack Agent."""

from app.tools.messages import send_channel_message, send_user_message

ALL_TOOLS = [
    send_user_message,
    send_channel_message,
]

__all__ = [
    "ALL_TOOLS",
    "send_user_message",
    "send_channel_message",
]
