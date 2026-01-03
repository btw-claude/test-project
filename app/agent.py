"""Claude Agent SDK wrapper for Slack Agent.

This module provides a wrapper around the Claude Agent SDK to create
an agent that can use Slack tools through the MCP protocol.
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.config.settings import Settings, get_settings
from app.helpers import AgentCard
from app.mcp_server import create_sdk_mcp_config

logger = logging.getLogger(__name__)


class AgentErrorType(str, Enum):
    """Types of errors that can occur during agent processing."""

    INITIALIZATION_ERROR = "initialization_error"
    TOOL_INVOCATION_ERROR = "tool_invocation_error"
    SDK_ERROR = "sdk_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class ToolInvocation:
    """Represents a tool invocation during message processing."""

    tool_name: str
    tool_input: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    duration_ms: float | None = None


@dataclass
class StreamingChunk:
    """A chunk of streaming response from the agent."""

    content: str
    is_final: bool = False
    tool_invocation: ToolInvocation | None = None


class AgentSDKError(Exception):
    """Exception raised for Claude Agent SDK errors."""

    def __init__(
        self,
        message: str,
        error_type: AgentErrorType,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
            error_type: The type of error.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}


class SlackAgent:
    """Wrapper for Claude Agent SDK with Slack tool integration.

    This class provides a high-level interface for creating and running
    an AI agent that can interact with Slack using MCP tools.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """Initialize the Slack agent.

        Args:
            settings: Optional settings instance. Uses default if not provided.
            system_prompt: Optional custom system prompt for the agent.
        """
        self._settings = settings or get_settings()
        self._system_prompt = system_prompt or self._default_system_prompt()
        self._mcp_config = create_sdk_mcp_config()
        self._initialized = False
        self._tool_handlers: dict[str, Any] = {}

    def _default_system_prompt(self) -> str:
        """Get the default system prompt for the agent.

        Returns:
            str: Default system prompt.
        """
        return (
            "You are a helpful Slack assistant agent. "
            "You can send messages to users and channels using the available tools. "
            "Always be concise and helpful in your responses."
        )

    @property
    def system_prompt(self) -> str:
        """Get the current system prompt.

        Returns:
            str: The agent's system prompt.
        """
        return self._system_prompt

    @property
    def tools(self) -> list[str]:
        """Get the list of available tool names.

        Returns:
            list[str]: Names of available tools.
        """
        return self._mcp_config.get("tool_names", [])

    @property
    def mcp_config(self) -> dict[str, Any]:
        """Get the MCP configuration.

        Returns:
            dict[str, Any]: MCP configuration dict.
        """
        return self._mcp_config

    def get_agent_card(self) -> AgentCard:
        """Get the agent card describing this agent.

        Returns:
            AgentCard: Agent card with capabilities.
        """
        return AgentCard(
            name="slack-agent",
            description="AI agent for Slack messaging operations",
            version="0.1.0",
            capabilities=["messaging", "notifications"],
            tools=self.tools,
        )

    async def initialize(self) -> None:
        """Initialize the agent and its tools.

        This method prepares the agent for handling requests.
        Should be called before processing any tasks.

        Raises:
            AgentSDKError: If initialization fails.
        """
        try:
            self._initialized = True
            logger.info("SlackAgent initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize agent")
            raise AgentSDKError(
                message=f"Failed to initialize agent: {e}",
                error_type=AgentErrorType.INITIALIZATION_ERROR,
                details={"original_error": str(e)},
            ) from e

    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources.

        Should be called when the agent is no longer needed.
        """
        self._initialized = False
        self._tool_handlers.clear()
        logger.info("SlackAgent shutdown complete")

    def _validate_initialized(self) -> None:
        """Validate that the agent is initialized.

        Raises:
            AgentSDKError: If the agent is not initialized.
        """
        if not self._initialized:
            raise AgentSDKError(
                message="Agent not initialized. Call initialize() first.",
                error_type=AgentErrorType.INITIALIZATION_ERROR,
            )

    async def invoke_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolInvocation:
        """Invoke a tool and return the result.

        Args:
            tool_name: Name of the tool to invoke.
            tool_input: Input parameters for the tool.

        Returns:
            ToolInvocation: The result of the tool invocation.

        Raises:
            AgentSDKError: If the tool invocation fails.
        """
        self._validate_initialized()

        if tool_name not in self.tools:
            raise AgentSDKError(
                message=f"Unknown tool: {tool_name}",
                error_type=AgentErrorType.TOOL_INVOCATION_ERROR,
                details={"tool_name": tool_name, "available_tools": self.tools},
            )

        invocation = ToolInvocation(tool_name=tool_name, tool_input=tool_input)

        try:
            logger.debug("Invoking tool %s with input %s", tool_name, tool_input)
            # TODO(SLACK-25): Replace placeholder with actual Claude Agent SDK tool invocation.
            # This should call the SDK's tool execution method with proper MCP integration.
            invocation.result = {"status": "success", "tool": tool_name}
            logger.debug("Tool %s completed successfully", tool_name)
        except Exception as e:
            invocation.error = str(e)
            logger.exception("Tool invocation failed: %s", tool_name)
            raise AgentSDKError(
                message=f"Tool invocation failed: {e}",
                error_type=AgentErrorType.TOOL_INVOCATION_ERROR,
                details={"tool_name": tool_name, "error": str(e)},
            ) from e

        return invocation

    async def process_message_streaming(
        self,
        message: str,
    ) -> AsyncIterator[StreamingChunk]:
        """Process a message and stream the response.

        Args:
            message: The message to process.

        Yields:
            StreamingChunk: Chunks of the response as they become available.

        Raises:
            AgentSDKError: If processing fails.
        """
        self._validate_initialized()

        try:
            # TODO(SLACK-25): Replace skeleton implementation with actual Claude Agent SDK streaming.
            # This should integrate with the SDK's streaming API to yield chunks as they arrive,
            # including tool invocations and their results.
            yield StreamingChunk(content="Processing message: ")
            yield StreamingChunk(content=message)
            yield StreamingChunk(
                content="\nResponse complete.",
                is_final=True,
            )
        except Exception as e:
            logger.exception("Streaming processing failed")
            raise AgentSDKError(
                message=f"Streaming processing failed: {e}",
                error_type=AgentErrorType.SDK_ERROR,
                details={"message": message, "error": str(e)},
            ) from e

    async def process_message(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        This method uses the Claude Agent SDK to process the message,
        invoking tools as needed and handling errors appropriately.

        Args:
            message: The message to process.

        Returns:
            dict[str, Any]: Response containing the agent's reply.

        Raises:
            AgentSDKError: If processing fails.
        """
        self._validate_initialized()

        try:
            tool_invocations: list[ToolInvocation] = []
            response_chunks: list[str] = []

            async for chunk in self.process_message_streaming(message):
                response_chunks.append(chunk.content)
                if chunk.tool_invocation:
                    tool_invocations.append(chunk.tool_invocation)

            return {
                "status": "success",
                "message": message,
                "response": "".join(response_chunks),
                "tools_available": self.tools,
                "tool_invocations": [
                    {
                        "tool_name": inv.tool_name,
                        "tool_input": inv.tool_input,
                        "result": inv.result,
                        "error": inv.error,
                    }
                    for inv in tool_invocations
                ],
            }
        except AgentSDKError:
            raise
        except Exception as e:
            logger.exception("Message processing failed")
            raise AgentSDKError(
                message=f"Message processing failed: {e}",
                error_type=AgentErrorType.SDK_ERROR,
                details={"message": message, "error": str(e)},
            ) from e


def create_slack_agent(
    settings: Settings | None = None,
    system_prompt: str | None = None,
) -> SlackAgent:
    """Factory function to create a SlackAgent instance.

    Args:
        settings: Optional settings instance.
        system_prompt: Optional custom system prompt.

    Returns:
        SlackAgent: A configured Slack agent instance.
    """
    return SlackAgent(settings=settings, system_prompt=system_prompt)


__all__ = [
    "AgentErrorType",
    "AgentSDKError",
    "SlackAgent",
    "StreamingChunk",
    "ToolInvocation",
    "create_slack_agent",
]
