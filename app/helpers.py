"""A2A utility helpers for Slack Agent.

This module re-exports commonly used A2A (Agent-to-Agent) protocol utilities
for convenient access throughout the application.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskResult(BaseModel):
    """Result from a task execution.

    Attributes:
        success: Whether the task completed successfully.
        message: Human-readable description of the result.
        data: Optional data payload from the task.
        error: Optional error message if task failed.
    """

    model_config = ConfigDict(strict=True)

    success: bool
    message: str
    data: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)


class AgentCard(BaseModel):
    """Agent card describing agent capabilities.

    Attributes:
        name: The agent's name.
        description: Description of what the agent does.
        version: Agent version string.
        capabilities: List of capability strings.
        tools: List of tool names available to the agent.
    """

    model_config = ConfigDict(strict=True)

    name: str
    description: str
    version: str
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


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
        TaskResult: Standardized task result instance.
    """
    return TaskResult(
        success=success,
        message=message,
        data=data,
        error=error,
    )


__all__ = [
    "TaskResult",
    "AgentCard",
    "create_task_result",
]
