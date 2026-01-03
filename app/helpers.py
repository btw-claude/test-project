"""A2A utility helpers for Slack Agent.

This module re-exports commonly used A2A (Agent-to-Agent) protocol utilities
for convenient access throughout the application.
"""

from typing import Any, NotRequired, Required, TypedDict


class TaskResult(TypedDict, total=True):
    """Result from a task execution.

    Required fields:
        success: Whether the task completed successfully.
        message: Human-readable description of the result.

    Optional fields:
        data: Optional data payload from the task.
        error: Optional error message if task failed.
    """

    success: Required[bool]
    message: Required[str]
    data: NotRequired[dict[str, Any]]
    error: NotRequired[str | None]


class AgentCard(TypedDict, total=True):
    """Agent card describing agent capabilities.

    Required fields:
        name: The agent's name.
        description: Description of what the agent does.
        version: Agent version string.

    Optional fields:
        capabilities: List of capability strings.
        tools: List of tool names available to the agent.
    """

    name: Required[str]
    description: Required[str]
    version: Required[str]
    capabilities: NotRequired[list[str]]
    tools: NotRequired[list[str]]


def create_task_result(
    success: bool,
    message: str,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> TaskResult:
    """Create a standardized task result.

    Args:
        success: Whether the task completed successfully.
        message: Human-readable description of the result.
        data: Optional data payload from the task.
        error: Optional error message if task failed.

    Returns:
        TaskResult: Standardized task result dict.
    """
    result: TaskResult = {
        "success": success,
        "message": message,
    }
    if data is not None:
        result["data"] = data
    if error is not None:
        result["error"] = error
    return result


def create_agent_card(
    name: str,
    description: str,
    version: str,
    capabilities: list[str] | None = None,
    tools: list[str] | None = None,
) -> AgentCard:
    """Create an agent card describing the agent's capabilities.

    Args:
        name: The agent's name.
        description: Description of what the agent does.
        version: Agent version string.
        capabilities: List of capability strings.
        tools: List of tool names available to the agent.

    Returns:
        AgentCard: Agent card dict.
    """
    return AgentCard(
        name=name,
        description=description,
        version=version,
        capabilities=capabilities or [],
        tools=tools or [],
    )


__all__ = [
    "TaskResult",
    "AgentCard",
    "create_task_result",
    "create_agent_card",
]
