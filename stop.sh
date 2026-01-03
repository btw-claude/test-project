#!/bin/bash
# Stop the Slack Agent server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.slack-agent.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Slack Agent is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Slack Agent is not running (stale PID file)"
    rm -f "$PID_FILE"
    exit 0
fi

echo "Stopping Slack Agent (PID: $PID)..."

# Send SIGTERM for graceful shutdown
kill "$PID"

# Wait for process to terminate
TIMEOUT=10
COUNT=0
while ps -p "$PID" > /dev/null 2>&1; do
    if [ $COUNT -ge $TIMEOUT ]; then
        echo "Process did not terminate gracefully, sending SIGKILL..."
        kill -9 "$PID" 2>/dev/null
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

rm -f "$PID_FILE"
echo "Slack Agent stopped"
