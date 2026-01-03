# Slack Agent

An AI-powered Slack agent that provides messaging operations through the A2A (Agent-to-Agent) protocol with MCP (Model Context Protocol) tool integration.

## Features

- Send direct messages to Slack users
- Send messages to Slack channels
- A2A protocol compliant for agent-to-agent communication
- MCP server for tool exposure to AI assistants

## Prerequisites

- Python 3.11 or higher
- A Slack workspace with a bot application configured
- Slack Bot OAuth Token (`xoxb-...`)
- Slack App-Level Token (`xapp-...`)
- Slack Signing Secret

## Installation

### Clone the Repository

```bash
git clone https://github.com/btw-claude/test-project.git
cd test-project
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the package in development mode:

```bash
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Slack credentials:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Application Settings
APP_ENV=development
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Slack App Setup

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Enable "Socket Mode" and generate an App-Level Token
3. Under "OAuth & Permissions", add the following scopes:
   - `chat:write` - Send messages
   - `channels:read` - List channels
   - `users:read` - Look up users
4. Install the app to your workspace
5. Copy the Bot User OAuth Token to your `.env` file

## Usage

### Running the Agent

Start the agent server using the provided script:

```bash
./start.sh
```

Or run directly with Python:

```bash
python -m app
```

The server will start on `http://0.0.0.0:8000` by default.

### Stopping the Agent

```bash
./stop.sh
```

### Checking Status

```bash
./status.sh
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent-card` | GET | Get the agent card (A2A protocol) |
| `/health` | GET | Health check endpoint |
| `/tasks` | POST | Submit a task for execution |
| `/tasks/{task_id}` | GET | Get task status |
| `/tasks/{task_id}/execute` | POST | Execute a submitted task |
| `/mcp/info` | GET | Get MCP server information |

### Example: Submit a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"message": "Send a message to #general saying hello"}'
```

## Architecture

See the following documentation for more details:

- [A2A Protocol](docs/A2A.md) - Agent-to-Agent protocol implementation
- [MCP Integration](docs/MCP.md) - Model Context Protocol server details

## Development

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=html
```

### Code Formatting

```bash
black app tests
ruff check app tests --fix
```

### Type Checking

```bash
mypy app
```

## License

MIT License - see LICENSE file for details.
