"""A2A protocol adapter for Slack Agent.

This module provides an executor that implements the Agent-to-Agent (A2A)
protocol, allowing the Slack agent to receive and process tasks from
other agents or orchestrators.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agent import SlackAgent, create_slack_agent
from app.config.settings import Settings, get_settings
from app.helpers import TaskResult, create_task_result


class TaskStatus(str, Enum):
    """Status of a task in the executor."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task submitted to the executor."""

    id: str
    message: str
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentExecutor:
    """A2A protocol adapter for executing tasks with the Slack agent.

    This executor handles the A2A protocol lifecycle including task
    submission, status tracking, and result retrieval.
    """

    def __init__(
        self,
        agent: SlackAgent | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the agent executor.

        Args:
            agent: Optional pre-configured SlackAgent instance.
            settings: Optional settings instance.
        """
        self._settings = settings or get_settings()
        self._agent = agent or create_slack_agent(self._settings)
        self._tasks: dict[str, Task] = {}
        self._running = False

    @property
    def agent(self) -> SlackAgent:
        """Get the underlying Slack agent.

        Returns:
            SlackAgent: The agent instance.
        """
        return self._agent

    @property
    def is_running(self) -> bool:
        """Check if the executor is running.

        Returns:
            bool: True if running.
        """
        return self._running

    async def start(self) -> None:
        """Start the executor and initialize the agent.

        Prepares the executor to accept and process tasks.
        """
        await self._agent.initialize()
        self._running = True

    async def stop(self) -> None:
        """Stop the executor and shutdown the agent.

        Cancels any pending tasks and releases resources.
        """
        self._running = False
        await self._agent.shutdown()

        for task in self._tasks.values():
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                task.status = TaskStatus.CANCELLED
                task.result = create_task_result(
                    success=False,
                    message="Task cancelled due to executor shutdown",
                    error="Executor shutdown",
                )

    def submit_task(
        self,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a new task for execution.

        Args:
            message: The task message/prompt to process.
            metadata: Optional metadata to attach to the task.

        Returns:
            str: The unique task ID.

        Raises:
            RuntimeError: If the executor is not running.
        """
        if not self._running:
            raise RuntimeError("Executor is not running. Call start() first.")

        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            message=message,
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        return task_id

    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get the status of a task.

        Args:
            task_id: The task ID to check.

        Returns:
            TaskStatus: The current task status.

        Raises:
            KeyError: If the task ID is not found.
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id}")
        return self._tasks[task_id].status

    def get_task_result(self, task_id: str) -> TaskResult | None:
        """Get the result of a completed task.

        Args:
            task_id: The task ID to get results for.

        Returns:
            TaskResult | None: The task result, or None if not complete.

        Raises:
            KeyError: If the task ID is not found.
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id}")
        return self._tasks[task_id].result

    async def execute_task(self, task_id: str) -> TaskResult:
        """Execute a submitted task.

        Args:
            task_id: The task ID to execute.

        Returns:
            TaskResult: The execution result.

        Raises:
            KeyError: If the task ID is not found.
            RuntimeError: If the executor is not running.
        """
        if not self._running:
            raise RuntimeError("Executor is not running.")

        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id}")

        task = self._tasks[task_id]

        if task.status != TaskStatus.PENDING:
            return task.result or create_task_result(
                success=False,
                message="Task is not in pending state",
                error=f"Current status: {task.status.value}",
            )

        task.status = TaskStatus.RUNNING

        try:
            response = await self._agent.process_message(task.message)
            task.result = create_task_result(
                success=True,
                message="Task completed successfully",
                data=response,
            )
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.result = create_task_result(
                success=False,
                message="Task execution failed",
                error=str(e),
            )
            task.status = TaskStatus.FAILED

        return task.result

    async def run_task(
        self,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> TaskResult:
        """Submit and immediately execute a task.

        Convenience method that combines submit_task and execute_task.

        Args:
            message: The task message/prompt to process.
            metadata: Optional metadata to attach to the task.

        Returns:
            TaskResult: The execution result.
        """
        task_id = self.submit_task(message, metadata)
        return await self.execute_task(task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """List all tasks, optionally filtered by status.

        Args:
            status: Optional status to filter by.

        Returns:
            list[Task]: List of tasks matching the filter.
        """
        if status is None:
            return list(self._tasks.values())
        return [t for t in self._tasks.values() if t.status == status]


def create_agent_executor(
    agent: SlackAgent | None = None,
    settings: Settings | None = None,
) -> AgentExecutor:
    """Factory function to create an AgentExecutor instance.

    Args:
        agent: Optional pre-configured SlackAgent.
        settings: Optional settings instance.

    Returns:
        AgentExecutor: A configured executor instance.
    """
    return AgentExecutor(agent=agent, settings=settings)


__all__ = [
    "TaskStatus",
    "Task",
    "AgentExecutor",
    "create_agent_executor",
]
