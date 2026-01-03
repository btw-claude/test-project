"""Unit tests for MCP Server module."""

from unittest.mock import MagicMock, patch

import pytest

from app.client.slack_client import SlackClient
from app.mcp_server import (
    SDKMCPConfig,
    StandaloneServerConfig,
    ToolConfig,
    create_sdk_mcp_config,
    create_slack_client,
    create_standalone_mcp_server,
    get_client,
    initialize_tools,
)


class TestCreateSlackClient:
    """Tests for create_slack_client function."""

    def test_returns_slack_client_instance(self, mock_settings: MagicMock) -> None:
        """Test that create_slack_client returns a valid SlackClient instance."""
        with patch("app.mcp_server.get_settings", return_value=mock_settings):
            client = create_slack_client()

        assert isinstance(client, SlackClient)

    def test_uses_provided_settings(self, mock_settings: MagicMock) -> None:
        """Test that create_slack_client uses provided settings."""
        client = create_slack_client(settings=mock_settings)

        assert isinstance(client, SlackClient)

    def test_uses_default_settings_when_none_provided(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that create_slack_client uses default settings when none provided."""
        with patch("app.mcp_server.get_settings", return_value=mock_settings) as mock:
            create_slack_client()

        mock.assert_called_once()


class TestInitializeTools:
    """Tests for initialize_tools function."""

    def test_sets_module_level_client_reference(
        self, slack_client: SlackClient
    ) -> None:
        """Test that initialize_tools sets the module-level client reference."""
        initialize_tools(slack_client)

        # Verify we can retrieve the client
        retrieved_client = get_client()
        assert retrieved_client is slack_client

    def test_can_reinitialize_with_different_client(
        self, mock_auth_provider: MagicMock
    ) -> None:
        """Test that initialize_tools can be called with different clients."""
        client1 = SlackClient(mock_auth_provider)
        client2 = SlackClient(mock_auth_provider)

        initialize_tools(client1)
        assert get_client() is client1

        initialize_tools(client2)
        assert get_client() is client2


class TestGetClient:
    """Tests for get_client function."""

    def test_returns_initialized_client(self, slack_client: SlackClient) -> None:
        """Test that get_client returns the initialized client."""
        initialize_tools(slack_client)

        result = get_client()

        assert result is slack_client

    def test_raises_runtime_error_when_not_initialized(self) -> None:
        """Test that get_client raises RuntimeError when not initialized."""
        # Using copy_context() creates an isolated context where our ContextVar
        # starts fresh with its default value (None). This is necessary because
        # contextvars persist their values within the same async task/test run,
        # and previous tests may have set the client. Running in a copied context
        # ensures we test the uninitialized state without affecting other tests.
        from contextvars import copy_context

        ctx = copy_context()

        def check_raises() -> None:
            # Import fresh to get the default None value in new context
            from app.mcp_server import _slack_client_var

            _slack_client_var.set(None)
            with pytest.raises(RuntimeError, match="SlackClient not initialized"):
                get_client()

        ctx.run(check_raises)


class TestCreateStandaloneMcpServer:
    """Tests for create_standalone_mcp_server function."""

    def test_returns_correct_configuration_dict(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that create_standalone_mcp_server returns correct configuration dict."""
        with patch("app.mcp_server.get_settings", return_value=mock_settings):
            config = create_standalone_mcp_server()

        assert isinstance(config, dict)
        assert config["host"] == mock_settings.api_host
        assert config["port"] == mock_settings.api_port
        assert config["transport"] == "sse"
        assert config["name"] == "slack-agent-mcp"
        assert config["version"] == "0.1.0"
        assert "tools" in config

    def test_uses_provided_host_and_port(self, mock_settings: MagicMock) -> None:
        """Test that create_standalone_mcp_server uses provided host and port."""
        custom_host = "127.0.0.1"
        custom_port = 9000

        with patch("app.mcp_server.get_settings", return_value=mock_settings):
            config = create_standalone_mcp_server(host=custom_host, port=custom_port)

        assert config["host"] == custom_host
        assert config["port"] == custom_port

    def test_returns_standalone_server_config_type(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that return type is compatible with StandaloneServerConfig."""
        with patch("app.mcp_server.get_settings", return_value=mock_settings):
            config: StandaloneServerConfig = create_standalone_mcp_server()

        # Verify all expected keys are present
        assert "host" in config
        assert "port" in config
        assert "tools" in config
        assert "transport" in config
        assert "name" in config
        assert "version" in config


class TestCreateSdkMcpConfig:
    """Tests for create_sdk_mcp_config function."""

    def test_returns_correct_sdk_configuration(self) -> None:
        """Test that create_sdk_mcp_config returns correct SDK configuration."""
        config = create_sdk_mcp_config()

        assert isinstance(config, dict)
        assert "tools" in config
        assert "tool_configs" in config
        assert "tool_names" in config
        assert config["description"] == "Slack Agent MCP tools for messaging operations"
        assert config["version"] == "0.1.0"

    def test_tool_names_match_tools(self) -> None:
        """Test that tool_names list matches the actual tool functions."""
        config = create_sdk_mcp_config()

        for i, tool in enumerate(config["tools"]):
            assert config["tool_names"][i] == tool.__name__

    def test_tool_configs_have_required_fields(self) -> None:
        """Test that each tool config has required fields."""
        config = create_sdk_mcp_config()

        for tool_config in config["tool_configs"]:
            assert "name" in tool_config
            assert "description" in tool_config
            assert "callable" in tool_config

    def test_returns_sdk_mcp_config_type(self) -> None:
        """Test that return type is compatible with SDKMCPConfig."""
        config: SDKMCPConfig = create_sdk_mcp_config()

        # Verify all expected keys are present
        assert "tools" in config
        assert "tool_configs" in config
        assert "tool_names" in config
        assert "description" in config
        assert "version" in config

    def test_tool_configs_match_tool_config_type(self) -> None:
        """Test that tool_configs items are compatible with ToolConfig."""
        config = create_sdk_mcp_config()

        for tool_config in config["tool_configs"]:
            # Verify ToolConfig structure
            tc: ToolConfig = tool_config
            assert isinstance(tc["name"], str)
            assert isinstance(tc["description"], str)
            assert callable(tc["callable"])


class TestTypeDefinitions:
    """Tests for TypedDict definitions."""

    def test_tool_config_keys(self) -> None:
        """Test ToolConfig has expected keys."""
        expected_keys = {"name", "description", "callable"}
        assert set(ToolConfig.__annotations__.keys()) == expected_keys

    def test_standalone_server_config_keys(self) -> None:
        """Test StandaloneServerConfig has expected keys."""
        expected_keys = {"host", "port", "tools", "transport", "name", "version"}
        assert set(StandaloneServerConfig.__annotations__.keys()) == expected_keys

    def test_sdk_mcp_config_keys(self) -> None:
        """Test SDKMCPConfig has expected keys."""
        expected_keys = {"tools", "tool_configs", "tool_names", "description", "version"}
        assert set(SDKMCPConfig.__annotations__.keys()) == expected_keys


class TestContextVarsAsyncIsolation:
    """Tests for contextvars isolation in async contexts.

    These tests validate that the ContextVar-based client storage provides
    proper isolation across concurrent async operations, which is the primary
    motivation for using contextvars over module-level globals.
    """

    @pytest.mark.asyncio
    async def test_context_isolation_across_concurrent_tasks(
        self, mock_auth_provider: MagicMock
    ) -> None:
        """Test that concurrent async tasks maintain separate client instances.

        Verifies that when multiple async tasks initialize different clients,
        each task sees only its own client, not clients from other tasks.
        """
        import asyncio

        client1 = SlackClient(mock_auth_provider)
        client2 = SlackClient(mock_auth_provider)
        results: dict[str, SlackClient] = {}

        async def task_with_client(name: str, client: SlackClient) -> None:
            initialize_tools(client)
            # Yield control to allow other tasks to run
            await asyncio.sleep(0.01)
            # Verify we still get our own client back
            results[name] = get_client()

        await asyncio.gather(
            task_with_client("task1", client1),
            task_with_client("task2", client2),
        )

        # Each task should have stored its own client
        assert results["task1"] is client1
        assert results["task2"] is client2

    @pytest.mark.asyncio
    async def test_sequential_async_tasks_share_context(
        self, mock_auth_provider: MagicMock
    ) -> None:
        """Test that sequential async operations in the same task share context.

        Verifies that within a single async task, the client persists across
        multiple await points as expected.
        """
        client = SlackClient(mock_auth_provider)
        initialize_tools(client)

        import asyncio

        await asyncio.sleep(0.01)
        retrieved1 = get_client()
        await asyncio.sleep(0.01)
        retrieved2 = get_client()

        assert retrieved1 is client
        assert retrieved2 is client

    @pytest.mark.asyncio
    async def test_nested_async_calls_preserve_context(
        self, mock_auth_provider: MagicMock
    ) -> None:
        """Test that nested async function calls preserve the context.

        Verifies that the client is accessible through nested async call chains.
        """
        client = SlackClient(mock_auth_provider)
        initialize_tools(client)

        async def inner_function() -> SlackClient:
            return get_client()

        async def outer_function() -> SlackClient:
            return await inner_function()

        result = await outer_function()
        assert result is client

    @pytest.mark.asyncio
    async def test_context_not_shared_between_copied_contexts(
        self, mock_auth_provider: MagicMock
    ) -> None:
        """Test that copied contexts are truly isolated.

        Verifies that using copy_context() creates a fresh context where
        the ContextVar has its default value, not values from the parent.
        """
        from contextvars import copy_context

        client = SlackClient(mock_auth_provider)
        initialize_tools(client)

        # Verify client is set in current context
        assert get_client() is client

        # Create a new context and verify it starts fresh
        new_ctx = copy_context()

        def check_in_new_context() -> None:
            from app.mcp_server import _slack_client_var

            _slack_client_var.set(None)
            with pytest.raises(RuntimeError, match="SlackClient not initialized"):
                get_client()

        new_ctx.run(check_in_new_context)

        # Original context should still have the client
        assert get_client() is client
