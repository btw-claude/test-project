"""Claude Agent SDK wrapper for Slack Agent.

This module provides a wrapper around the Claude Agent SDK to create
an agent that can use Slack tools through the MCP protocol.
"""

from typing import Any

from app.config.settings import Settings, get_settings
from app.helpers import AgentCard, create_agent_card
from app.mcp_server import create_sdk_mcp_config


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
        return create_agent_card(
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
        """
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources.

        Should be called when the agent is no longer needed.
        """
        self._initialized = False

    async def process_message(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        This is a placeholder for actual Claude Agent SDK integration.
        The actual implementation would use the SDK to process the
        message and invoke tools as needed.

        Args:
            message: The message to process.

        Returns:
            dict[str, Any]: Response containing the agent's reply.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        return {
            "status": "success",
            "message": message,
            "response": "Message processed successfully",
            "tools_available": self.tools,
        }


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
    "SlackAgent",
    "create_slack_agent",
]
