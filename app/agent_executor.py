"""A2A protocol adapter for Slack Agent.

This module provides an executor that implements the Agent-to-Agent (A2A)
protocol, allowing the Slack agent to receive and process tasks from
other agents or orchestrators.
"""

import asyncio
import logging
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agent import AgentSDKError, SlackAgent, create_slack_agent
from app.config.settings import Settings, get_settings
from app.helpers import TaskResult, create_task_result

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY_SECONDS = 1.0
DEFAULT_MAX_DELAY_SECONDS = 60.0
DEFAULT_JITTER_FACTOR = 0.1


class TaskStatus(str, Enum):
    """Status of a task in the executor."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    max_retries: int = DEFAULT_MAX_RETRIES
    base_delay_seconds: float = DEFAULT_BASE_DELAY_SECONDS
    max_delay_seconds: float = DEFAULT_MAX_DELAY_SECONDS
    jitter_factor: float = DEFAULT_JITTER_FACTOR

    def calculate_delay(self, attempt: int) -> float:
        """Calculate the delay before the next retry attempt.

        Uses exponential backoff with jitter.

        Args:
            attempt: The current attempt number (0-indexed).

        Returns:
            float: Delay in seconds before the next retry.
        """
        delay = min(
            self.base_delay_seconds * (2**attempt),
            self.max_delay_seconds,
        )
        jitter = delay * self.jitter_factor * random.random()
        return delay + jitter


@dataclass
class Task:
    """Represents a task submitted to the executor."""

    id: str
    message: str
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    last_error: str | None = None


class AsyncSafeTaskStorage:
    """Thread-safe and async-safe storage for tasks.

    Uses asyncio.Lock to ensure safe concurrent access to the task dictionary.
    """

    def __init__(self) -> None:
        """Initialize the async-safe task storage."""
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def get(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: The task ID to retrieve.

        Returns:
            Task | None: The task if found, None otherwise.
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def set(self, task_id: str, task: Task) -> None:
        """Store a task.

        Args:
            task_id: The task ID.
            task: The task to store.
        """
        async with self._lock:
            self._tasks[task_id] = task

    async def delete(self, task_id: str) -> bool:
        """Delete a task by ID.

        Args:
            task_id: The task ID to delete.

        Returns:
            bool: True if the task was deleted, False if not found.
        """
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    async def list_all(self) -> list[Task]:
        """List all tasks.

        Returns:
            list[Task]: All stored tasks.
        """
        async with self._lock:
            return list(self._tasks.values())

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks filtered by status.

        Args:
            status: The status to filter by.

        Returns:
            list[Task]: Tasks matching the status.
        """
        async with self._lock:
            return [t for t in self._tasks.values() if t.status == status]

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: TaskResult | None = None,
    ) -> bool:
        """Update a task's status and optionally its result.

        Args:
            task_id: The task ID to update.
            status: The new status.
            result: Optional result to set.

        Returns:
            bool: True if the task was updated, False if not found.
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            self._tasks[task_id].status = status
            if result is not None:
                self._tasks[task_id].result = result
            return True

    def get_sync(self, task_id: str) -> Task | None:
        """Synchronously get a task by ID (for non-async contexts).

        Warning: This method does not use locking. Use only when
        you're certain no concurrent access is happening.

        Args:
            task_id: The task ID to retrieve.

        Returns:
            Task | None: The task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def set_sync(self, task_id: str, task: Task) -> None:
        """Synchronously store a task (for non-async contexts).

        Warning: This method does not use locking. Use only when
        you're certain no concurrent access is happening.

        Args:
            task_id: The task ID.
            task: The task to store.
        """
        self._tasks[task_id] = task

    def list_all_sync(self) -> list[Task]:
        """Synchronously list all tasks (for non-async contexts).

        Warning: This method does not use locking. Use only when
        you're certain no concurrent access is happening, such as
        in single-threaded contexts or when the event loop is not
        running concurrently.

        Returns:
            list[Task]: All stored tasks.
        """
        return list(self._tasks.values())


class AgentExecutor:
    """A2A protocol adapter for executing tasks with the Slack agent.

    This executor handles the A2A protocol lifecycle including task
    submission, status tracking, and result retrieval. Uses async-safe
    task storage for concurrent task management.
    """

    def __init__(
        self,
        agent: SlackAgent | None = None,
        settings: Settings | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize the agent executor.

        Args:
            agent: Optional pre-configured SlackAgent instance.
            settings: Optional settings instance.
            retry_config: Optional retry configuration for task execution.
        """
        self._settings = settings or get_settings()
        self._agent = agent or create_slack_agent(self._settings)
        self._task_storage = AsyncSafeTaskStorage()
        self._retry_config = retry_config or RetryConfig()
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

        tasks = await self._task_storage.list_all()
        for task in tasks:
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING):
                task.status = TaskStatus.CANCELLED
                task.result = create_task_result(
                    success=False,
                    message="Task cancelled due to executor shutdown",
                    error="Executor shutdown",
                )
                await self._task_storage.set(task.id, task)

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
        self._task_storage.set_sync(task_id, task)
        return task_id

    async def submit_task_async(
        self,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a new task for execution (async-safe version).

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
        await self._task_storage.set(task_id, task)
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
        task = self._task_storage.get_sync(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task.status

    async def get_task_status_async(self, task_id: str) -> TaskStatus:
        """Get the status of a task (async-safe version).

        Args:
            task_id: The task ID to check.

        Returns:
            TaskStatus: The current task status.

        Raises:
            KeyError: If the task ID is not found.
        """
        task = await self._task_storage.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task.status

    def get_task_result(self, task_id: str) -> TaskResult | None:
        """Get the result of a completed task.

        Args:
            task_id: The task ID to get results for.

        Returns:
            TaskResult | None: The task result, or None if not complete.

        Raises:
            KeyError: If the task ID is not found.
        """
        task = self._task_storage.get_sync(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task.result

    async def get_task_result_async(self, task_id: str) -> TaskResult | None:
        """Get the result of a completed task (async-safe version).

        Args:
            task_id: The task ID to get results for.

        Returns:
            TaskResult | None: The task result, or None if not complete.

        Raises:
            KeyError: If the task ID is not found.
        """
        task = await self._task_storage.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task.result

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable.

        Args:
            error: The exception that occurred.

        Returns:
            bool: True if the error is retryable.
        """
        if isinstance(error, AgentSDKError):
            # Retry transient errors like timeouts, but not validation errors
            non_retryable_types = {"initialization_error", "validation_error"}
            return error.error_type.value not in non_retryable_types
        # Retry generic exceptions as they might be transient
        return True

    async def execute_task(self, task_id: str) -> TaskResult:
        """Execute a submitted task with retry logic.

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

        task = await self._task_storage.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")

        if task.status not in (TaskStatus.PENDING, TaskStatus.RETRYING):
            return task.result or create_task_result(
                success=False,
                message="Task is not in pending or retrying state",
                error=f"Current status: {task.status.value}",
            )

        task.status = TaskStatus.RUNNING
        await self._task_storage.set(task_id, task)

        last_error: Exception | None = None

        for attempt in range(self._retry_config.max_retries + 1):
            try:
                logger.debug(
                    "Executing task %s, attempt %d/%d",
                    task_id,
                    attempt + 1,
                    self._retry_config.max_retries + 1,
                )
                response = await self._agent.process_message(task.message)
                task.result = create_task_result(
                    success=True,
                    message="Task completed successfully",
                    data=response,
                )
                task.status = TaskStatus.COMPLETED
                task.last_error = None
                await self._task_storage.set(task_id, task)
                return task.result

            except Exception as e:
                last_error = e
                task.last_error = str(e)
                task.retry_count = attempt + 1

                if not self._is_retryable_error(e) or attempt >= self._retry_config.max_retries:
                    logger.warning(
                        "Task %s failed after %d attempts: %s",
                        task_id,
                        attempt + 1,
                        e,
                    )
                    break

                delay = self._retry_config.calculate_delay(attempt)
                logger.info(
                    "Task %s failed (attempt %d), retrying in %.2f seconds: %s",
                    task_id,
                    attempt + 1,
                    delay,
                    e,
                )
                task.status = TaskStatus.RETRYING
                await self._task_storage.set(task_id, task)
                await asyncio.sleep(delay)
                task.status = TaskStatus.RUNNING
                await self._task_storage.set(task_id, task)

        # All retries exhausted
        task.result = create_task_result(
            success=False,
            message=f"Task execution failed after {task.retry_count} attempts",
            error=str(last_error) if last_error else "Unknown error",
        )
        task.status = TaskStatus.FAILED
        await self._task_storage.set(task_id, task)
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

        Note: This is a synchronous method for backwards compatibility.
        For concurrent access, use list_tasks_async.

        Args:
            status: Optional status to filter by.

        Returns:
            list[Task]: List of tasks matching the filter.
        """
        all_tasks = self._task_storage.list_all_sync()
        if status is None:
            return all_tasks
        return [t for t in all_tasks if t.status == status]

    async def list_tasks_async(
        self,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """List all tasks, optionally filtered by status (async-safe).

        Args:
            status: Optional status to filter by.

        Returns:
            list[Task]: List of tasks matching the filter.
        """
        if status is None:
            return await self._task_storage.list_all()
        return await self._task_storage.list_by_status(status)


def create_agent_executor(
    agent: SlackAgent | None = None,
    settings: Settings | None = None,
    retry_config: RetryConfig | None = None,
) -> AgentExecutor:
    """Factory function to create an AgentExecutor instance.

    Args:
        agent: Optional pre-configured SlackAgent.
        settings: Optional settings instance.
        retry_config: Optional retry configuration for task execution.

    Returns:
        AgentExecutor: A configured executor instance.
    """
    return AgentExecutor(agent=agent, settings=settings, retry_config=retry_config)


__all__ = [
    "AsyncSafeTaskStorage",
    "RetryConfig",
    "Task",
    "TaskStatus",
    "AgentExecutor",
    "create_agent_executor",
]
