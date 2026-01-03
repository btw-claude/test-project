#!/bin/bash
# Start the Slack Agent server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.slack-agent.pid"
LOG_FILE="$SCRIPT_DIR/slack-agent.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Slack Agent is already running (PID: $PID)"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Warning: .env file not found. Copy .env.example to .env and configure it."
    echo "Using default configuration."
fi

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Verify that the app module can be imported before starting
echo "Checking Python module dependencies..."
if ! python -c "import app" 2>/dev/null; then
    echo "Error: Cannot import 'app' module."
    echo "Please ensure all dependencies are installed:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "Starting Slack Agent..."

# Start the server in the background
cd "$SCRIPT_DIR"
nohup python -m app > "$LOG_FILE" 2>&1 &
PID=$!

# Save the PID
echo $PID > "$PID_FILE"

# Wait briefly and check if process started successfully
sleep 2
if ps -p "$PID" > /dev/null 2>&1; then
    echo "Slack Agent started successfully (PID: $PID)"
    echo "Logs: $LOG_FILE"
    echo "Health check: http://localhost:8000/health"
else
    echo "Failed to start Slack Agent"
    rm -f "$PID_FILE"
    echo "Check logs for details: $LOG_FILE"
    exit 1
fi
