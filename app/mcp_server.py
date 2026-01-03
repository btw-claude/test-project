"""MCP Server for Slack Agent tool registration.

This module provides functionality to create and configure an MCP server
that exposes Slack tools for use by AI agents.
"""

from contextvars import ContextVar
from typing import Any, Callable, TypedDict

from app.auth.bearer import BearerTokenAuth
from app.client.slack_client import SlackClient
from app.config.settings import Settings, get_settings
from app.tools import ALL_TOOLS

# Thread-safe client reference using contextvars for async contexts
_slack_client_var: ContextVar[SlackClient | None] = ContextVar(
    "_slack_client", default=None
)


class ToolConfig(TypedDict):
    """Configuration for a single tool."""

    name: str
    description: str
    callable: Callable[..., Any]


class StandaloneServerConfig(TypedDict):
    """Configuration for standalone HTTP/SSE MCP server."""

    host: str
    port: int
    tools: list[Callable[..., Any]]
    transport: str
    name: str
    version: str


class SDKMCPConfig(TypedDict):
    """Configuration for Claude Agent SDK MCP integration."""

    tools: list[Callable[..., Any]]
    tool_configs: list[ToolConfig]
    tool_names: list[str]
    description: str
    version: str


__all__ = [
    "create_slack_client",
    "initialize_tools",
    "get_client",
    "create_standalone_mcp_server",
    "create_sdk_mcp_config",
    "ToolConfig",
    "StandaloneServerConfig",
    "SDKMCPConfig",
]


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

    Sets the context-local client reference that tools can use
    for making API calls. Uses contextvars for thread-safety in
    async contexts.

    Args:
        client: The SlackClient instance to use for tool operations.
    """
    _slack_client_var.set(client)


def get_client() -> SlackClient:
    """Get the initialized SlackClient instance.

    Returns:
        SlackClient: The initialized client instance.

    Raises:
        RuntimeError: If initialize_tools has not been called in the current context.
    """
    client = _slack_client_var.get()
    if client is None:
        raise RuntimeError(
            "SlackClient not initialized. Call initialize_tools() first."
        )
    return client


def create_standalone_mcp_server(
    host: str | None = None,
    port: int | None = None,
) -> StandaloneServerConfig:
    """Create configuration for a standalone HTTP/SSE MCP server.

    Creates a server configuration dict that can be used to run
    an MCP server exposing Slack tools over HTTP with SSE transport.

    Args:
        host: Optional host address. Defaults to settings.api_host.
        port: Optional port number. Defaults to settings.api_port.

    Returns:
        StandaloneServerConfig: Server configuration containing:
            - host: The server host address
            - port: The server port number
            - tools: List of tool functions to expose
            - transport: The transport type (sse)
            - name: The server name
            - version: The server version
    """
    settings = get_settings()

    return StandaloneServerConfig(
        host=host or settings.api_host,
        port=port or settings.api_port,
        tools=ALL_TOOLS,
        transport="sse",
        name="slack-agent-mcp",
        version="0.1.0",
    )


def create_sdk_mcp_config() -> SDKMCPConfig:
    """Create MCP configuration for A2A agent internal use.

    Creates a configuration dict suitable for use with the
    Claude Agent SDK's MCP client integration.

    Returns:
        SDKMCPConfig: SDK configuration containing:
            - tools: List of tool functions available
            - tool_configs: List of tool configuration dicts
            - tool_names: List of tool names for registration
            - description: Server description
            - version: SDK version
    """
    tool_configs: list[ToolConfig] = []
    tool_names: list[str] = []

    for tool in ALL_TOOLS:
        tool_configs.append(_create_tool_config(tool))
        tool_names.append(tool.__name__)

    return SDKMCPConfig(
        tools=ALL_TOOLS,
        tool_configs=tool_configs,
        tool_names=tool_names,
        description="Slack Agent MCP tools for messaging operations",
        version="0.1.0",
    )


def _create_tool_config(tool: Callable[..., Any]) -> ToolConfig:
    """Create a tool configuration from a callable.

    Args:
        tool: The tool function to create configuration for.

    Returns:
        ToolConfig: Tool configuration with name, description, and callable.
    """
    return ToolConfig(
        name=tool.__name__,
        description=tool.__doc__ or "",
        callable=tool,
    )
