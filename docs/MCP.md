# MCP Integration

This document describes the Model Context Protocol (MCP) server implementation in the Slack Agent.

## Overview

The Slack Agent exposes its tools via MCP, allowing AI assistants and other agents to discover and invoke Slack operations.

## MCP Server Configuration

### Server Information

```
GET /mcp/info
```

**Response:**

```json
{
  "name": "slack-agent-mcp",
  "version": "0.1.0",
  "transport": "sse",
  "tools": [
    "send_user_message",
    "send_channel_message"
  ]
}
```

## Available Tools

### send_user_message

Send a direct message to a Slack user.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | The Slack user ID (e.g., `U12345678`) |
| `text` | string | Yes | The message text to send |

**Returns:**

```json
{
  "ok": true,
  "channel": "D12345678",
  "ts": "1234567890.123456",
  "message": {
    "text": "Hello!",
    "user": "U87654321",
    "type": "message"
  }
}
```

### send_channel_message

Send a message to a Slack channel.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | Yes | The Slack channel ID (e.g., `C12345678`) |
| `text` | string | Yes | The message text to send |

**Returns:**

```json
{
  "ok": true,
  "channel": "C12345678",
  "ts": "1234567890.123456",
  "message": {
    "text": "Hello, channel!",
    "user": "U87654321",
    "type": "message"
  }
}
```

## Transport

The MCP server uses Server-Sent Events (SSE) transport for real-time communication. This enables:

- Persistent connections for efficient tool invocation
- Streaming responses for long-running operations
- Event-driven architecture

## Tool Registration

Tools are registered at startup and exposed through the MCP protocol:

```python
from app.mcp_server import create_sdk_mcp_config

# Get MCP configuration for SDK integration
mcp_config = create_sdk_mcp_config()

# Available properties:
# - tools: List of tool functions
# - tool_names: List of tool name strings
# - tool_configs: Detailed tool configurations
# - description: Server description
# - version: Server version
```

## SDK Integration

To integrate the MCP tools with the Claude Agent SDK:

```python
from app.mcp_server import (
    create_slack_client,
    initialize_tools,
    create_sdk_mcp_config,
)
from app.config.settings import get_settings

# 1. Initialize the Slack client
settings = get_settings()
client = create_slack_client(settings)
initialize_tools(client)

# 2. Get MCP configuration
mcp_config = create_sdk_mcp_config()

# 3. Use with Claude Agent SDK
# The tool_configs can be passed to the SDK for tool registration
```

## Standalone MCP Server

For running a standalone MCP server:

```python
from app.mcp_server import create_standalone_mcp_server

# Create server configuration
server_config = create_standalone_mcp_server(
    host="0.0.0.0",
    port=8001  # Separate port from A2A server
)

# Configuration includes:
# - host: Server bind address
# - port: Server port
# - tools: List of tool functions
# - transport: Transport type (sse)
# - name: Server name
# - version: Server version
```

## Error Handling

MCP tools raise `SlackError` for API failures:

```python
from app.client.slack_client import SlackError

try:
    result = await send_channel_message("C12345", "Hello!")
except SlackError as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.error_code}")
```

Common error codes:

| Error Code | Description |
|------------|-------------|
| `channel_not_found` | The specified channel doesn't exist |
| `not_in_channel` | The bot is not a member of the channel |
| `user_not_found` | The specified user doesn't exist |
| `msg_too_long` | Message text exceeds Slack's limit |
| `rate_limited` | Too many requests, slow down |
| `http_error` | HTTP request failed |
| `request_error` | Network or connection error |

## Security

The MCP server inherits authentication from the Slack Bot Token configured in the environment. Ensure:

1. Bot tokens are kept secure and not exposed in logs
2. The server is not publicly accessible without additional authentication
3. Minimal OAuth scopes are granted to the bot
