"""Application entry point for Slack Agent.

This module provides the main entry point for running the Slack Agent
as an A2A (Agent-to-Agent) server with MCP tool integration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.agent import SlackAgent, create_slack_agent
from app.agent_executor import AgentExecutor, create_agent_executor
from app.config.settings import Settings, get_settings
from app.helpers import AgentCard, create_agent_card
from app.mcp_server import create_standalone_mcp_server, initialize_tools, create_slack_client


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)



def get_agent_card() -> AgentCard:
    """Create the agent card with skills for the Slack Agent.

    Returns:
        AgentCard: Agent card describing capabilities and skills.
    """
    return create_agent_card(
        name="slack-agent",
        description="AI agent for Slack messaging operations with A2A protocol support",
        version="0.1.0",
        capabilities=[
            "messaging",
            "notifications",
            "channel-management",
            "user-lookup",
        ],
        tools=[
            "send_message",
            "send_direct_message",
            "list_channels",
            "get_channel_info",
        ],
    )


async def agent_card_endpoint(request: Request) -> JSONResponse:
    """Endpoint to retrieve the agent card.

    Args:
        request: The incoming request.

    Returns:
        JSONResponse: Agent card as JSON.
    """
    card = get_agent_card()
    return JSONResponse(dict(card))


async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint.

    Args:
        request: The incoming request.

    Returns:
        JSONResponse: Health status.
    """
    return JSONResponse({
        "status": "healthy",
        "agent": "slack-agent",
        "version": "0.1.0",
    })


async def task_submit_endpoint(request: Request) -> JSONResponse:
    """Submit a task for execution via A2A protocol.

    Args:
        request: The incoming request containing task data.

    Returns:
        JSONResponse: Task submission result with task ID.
    """
    executor: AgentExecutor | None = getattr(request.app.state, "executor", None)
    if executor is None:
        return JSONResponse(
            {"error": "Agent executor not initialized"},
            status_code=503,
        )

    try:
        body = await request.json()
        message = body.get("message", "")
        metadata = body.get("metadata", {})

        if not message:
            return JSONResponse(
                {"error": "Message is required"},
                status_code=400,
            )

        task_id = executor.submit_task(message, metadata)
        return JSONResponse({
            "task_id": task_id,
            "status": "pending",
        })
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


async def task_status_endpoint(request: Request) -> JSONResponse:
    """Get the status of a submitted task.

    Args:
        request: The incoming request with task_id path parameter.

    Returns:
        JSONResponse: Task status information.
    """
    executor: AgentExecutor | None = getattr(request.app.state, "executor", None)
    if executor is None:
        return JSONResponse(
            {"error": "Agent executor not initialized"},
            status_code=503,
        )

    task_id = request.path_params.get("task_id", "")

    try:
        status = executor.get_task_status(task_id)
        result = executor.get_task_result(task_id)

        response: dict[str, Any] = {
            "task_id": task_id,
            "status": status.value,
        }

        if result is not None:
            response["result"] = dict(result)

        return JSONResponse(response)
    except KeyError:
        return JSONResponse(
            {"error": f"Task not found: {task_id}"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


async def task_execute_endpoint(request: Request) -> JSONResponse:
    """Execute a submitted task immediately.

    Args:
        request: The incoming request with task_id path parameter.

    Returns:
        JSONResponse: Task execution result.
    """
    executor: AgentExecutor | None = getattr(request.app.state, "executor", None)
    if executor is None:
        return JSONResponse(
            {"error": "Agent executor not initialized"},
            status_code=503,
        )

    task_id = request.path_params.get("task_id", "")

    try:
        result = await executor.execute_task(task_id)
        return JSONResponse({
            "task_id": task_id,
            "result": dict(result),
        })
    except KeyError:
        return JSONResponse(
            {"error": f"Task not found: {task_id}"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


async def mcp_info_endpoint(request: Request) -> JSONResponse:
    """MCP server information endpoint.

    Args:
        request: The incoming request.

    Returns:
        JSONResponse: MCP server configuration info.
    """
    mcp_config = create_standalone_mcp_server()
    return JSONResponse({
        "name": mcp_config["name"],
        "version": mcp_config["version"],
        "transport": mcp_config["transport"],
        "tools": [tool.__name__ for tool in mcp_config["tools"]],
    })


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Application lifespan manager for startup and shutdown.

    Args:
        app: The Starlette application.

    Yields:
        None
    """
    logger.info("Starting Slack Agent...")

    # Initialize settings and Slack client
    settings = get_settings()
    client = create_slack_client(settings)
    initialize_tools(client)

    # Create and start the executor, store in app.state
    executor = create_agent_executor(settings=settings)
    await executor.start()
    app.state.executor = executor

    logger.info("Slack Agent started successfully")
    logger.info(f"Agent card: {get_agent_card()}")

    yield

    # Shutdown
    logger.info("Shutting down Slack Agent...")
    executor = getattr(app.state, "executor", None)
    if executor is not None:
        await executor.stop()
    logger.info("Slack Agent shutdown complete")


def create_app(settings: Settings | None = None) -> Starlette:
    """Create and configure the Starlette application.

    Args:
        settings: Optional settings instance.

    Returns:
        Starlette: Configured application instance.
    """
    if settings is None:
        settings = get_settings()

    # Define routes
    routes = [
        # A2A protocol endpoints
        Route("/.well-known/agent-card", agent_card_endpoint, methods=["GET"]),
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/tasks", task_submit_endpoint, methods=["POST"]),
        Route("/tasks/{task_id}", task_status_endpoint, methods=["GET"]),
        Route("/tasks/{task_id}/execute", task_execute_endpoint, methods=["POST"]),

        # MCP integration endpoint
        Route("/mcp/info", mcp_info_endpoint, methods=["GET"]),
    ]

    # Configure middleware
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    # Create application
    app = Starlette(
        debug=settings.app_debug,
        routes=routes,
        middleware=middleware,
        lifespan=lifespan,
    )

    return app


def main() -> None:
    """Main entry point for running the application."""
    settings = get_settings()

    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.app_debug}")

    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.app_log_level.lower(),
    )


if __name__ == "__main__":
    main()
