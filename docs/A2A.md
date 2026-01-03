# A2A Protocol Implementation

This document describes the Agent-to-Agent (A2A) protocol implementation in the Slack Agent.

## Overview

The A2A protocol enables standardized communication between AI agents. This implementation allows other agents to discover, interact with, and utilize the Slack Agent's capabilities.

## Agent Card

The agent card provides metadata about the agent's capabilities and is served at the well-known endpoint.

### Endpoint

```
GET /.well-known/agent-card
```

### Response Format

```json
{
  "name": "slack-agent",
  "description": "AI agent for Slack messaging operations with A2A protocol support",
  "version": "0.1.0",
  "capabilities": [
    "messaging",
    "notifications",
    "channel-management",
    "user-lookup"
  ],
  "tools": [
    "send_message",
    "send_direct_message",
    "list_channels",
    "get_channel_info"
  ]
}
```

## Task Submission

Tasks can be submitted to the agent for asynchronous processing.

### Submit a Task

```
POST /tasks
```

**Request Body:**

```json
{
  "message": "Send a welcome message to user U12345678",
  "metadata": {
    "priority": "high",
    "source": "orchestrator-agent"
  }
}
```

**Response:**

```json
{
  "task_id": "task_abc123",
  "status": "pending"
}
```

### Get Task Status

```
GET /tasks/{task_id}
```

**Response:**

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "result": {
    "success": true,
    "message_ts": "1234567890.123456"
  }
}
```

### Execute Task Immediately

```
POST /tasks/{task_id}/execute
```

**Response:**

```json
{
  "task_id": "task_abc123",
  "result": {
    "success": true,
    "message_ts": "1234567890.123456"
  }
}
```

## Task States

| Status | Description |
|--------|-------------|
| `pending` | Task submitted and waiting for execution |
| `running` | Task is currently being executed |
| `completed` | Task completed successfully |
| `failed` | Task execution failed |
| `cancelled` | Task was cancelled |

## Authentication

The A2A endpoints currently support open access. Future versions will implement:

- API key authentication
- OAuth 2.0 bearer tokens
- Mutual TLS for agent verification

## Error Handling

All endpoints return errors in a consistent format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Task or resource not found |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Agent not initialized |

## Health Check

```
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "agent": "slack-agent",
  "version": "0.1.0"
}
```

## Integration Example

Here's an example of how another agent can interact with the Slack Agent:

```python
import httpx

async def send_slack_notification(slack_agent_url: str, message: str):
    async with httpx.AsyncClient() as client:
        # 1. Check agent capabilities
        card = await client.get(f"{slack_agent_url}/.well-known/agent-card")
        agent_info = card.json()

        # 2. Submit a task
        task_response = await client.post(
            f"{slack_agent_url}/tasks",
            json={"message": message}
        )
        task_id = task_response.json()["task_id"]

        # 3. Execute the task
        result = await client.post(
            f"{slack_agent_url}/tasks/{task_id}/execute"
        )
        return result.json()
```
