"""MCP Server for Slack Agent tool registration.

This module provides functionality to create and configure an MCP server
that exposes Slack tools for use by AI agents.
"""

from typing import Any, Callable

from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient
from app.config.settings import Settings, get_settings
from app.tools import ALL_TOOLS

# Module-level client reference for tools
_slack_client: SlackClient | None = None


def create_slack_client(settings: Settings | None = None) -> SlackClient:
    """Factory function to create a configured SlackClient.

    Creates a SlackClient instance using the provided settings or
    the default application settings.

    Args:
        settings: Optional settings instance. If not provided, uses
            the default application settings.

    Returns:
        SlackClient: A configured Slack client instance.
    """
    if settings is None:
        settings = get_settings()

    auth_provider = BearerTokenAuth(settings.slack_bot_token)
    return SlackClient(auth_provider)


def initialize_tools(client: SlackClient) -> None:
    """Initialize tool modules with a shared SlackClient instance.

    Sets the module-level client reference that tools can use
    for making API calls.

    Args:
        client: The SlackClient instance to use for tool operations.
    """
    global _slack_client
    _slack_client = client


def get_client() -> SlackClient:
    """Get the initialized SlackClient instance.

    Returns:
        SlackClient: The initialized client instance.

    Raises:
        RuntimeError: If initialize_tools has not been called.
    """
    if _slack_client is None:
        raise RuntimeError(
            "SlackClient not initialized. Call initialize_tools() first."
        )
    return _slack_client


def create_standalone_mcp_server(
    host: str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """Create configuration for a standalone HTTP/SSE MCP server.

    Creates a server configuration dict that can be used to run
    an MCP server exposing Slack tools over HTTP with SSE transport.

    Args:
        host: Optional host address. Defaults to settings.api_host.
        port: Optional port number. Defaults to settings.api_port.

    Returns:
        dict[str, Any]: Server configuration containing:
            - host: The server host address
            - port: The server port number
            - tools: List of tool functions to expose
            - transport: The transport type (sse)
    """
    settings = get_settings()

    return {
        "host": host or settings.api_host,
        "port": port or settings.api_port,
        "tools": ALL_TOOLS,
        "transport": "sse",
        "name": "slack-agent-mcp",
        "version": "0.1.0",
    }


def create_sdk_mcp_config() -> dict[str, Any]:
    """Create MCP configuration for A2A agent internal use.

    Creates a configuration dict suitable for use with the
    Claude Agent SDK's MCP client integration.

    Returns:
        dict[str, Any]: SDK configuration containing:
            - tools: List of tool functions available
            - tool_names: List of tool names for registration
            - description: Server description
    """
    tool_configs: list[dict[str, Any]] = []

    for tool in ALL_TOOLS:
        tool_config = _create_tool_config(tool)
        tool_configs.append(tool_config)

    return {
        "tools": ALL_TOOLS,
        "tool_configs": tool_configs,
        "tool_names": [tool.__name__ for tool in ALL_TOOLS],
        "description": "Slack Agent MCP tools for messaging operations",
        "version": "0.1.0",
    }


def _create_tool_config(tool: Callable[..., Any]) -> dict[str, Any]:
    """Create a tool configuration from a callable.

    Args:
        tool: The tool function to create configuration for.

    Returns:
        dict[str, Any]: Tool configuration with name and description.
    """
    return {
        "name": tool.__name__,
        "description": tool.__doc__ or "",
        "callable": tool,
    }
