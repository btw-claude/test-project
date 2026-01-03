#!/bin/bash
# Check the status of the Slack Agent server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.slack-agent.pid"
LOG_FILE="$SCRIPT_DIR/slack-agent.log"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"

echo "=== Slack Agent Status ==="
echo

# Check PID file
if [ ! -f "$PID_FILE" ]; then
    echo "Status: STOPPED (no PID file)"
    exit 1
fi

PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Status: STOPPED (stale PID file)"
    rm -f "$PID_FILE"
    exit 1
fi

echo "Status: RUNNING"
echo "PID: $PID"
echo

# Check health endpoint
echo "Health check..."
if command -v curl > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "Health: HEALTHY"
        echo
        echo "Response:"
        curl -s --max-time 5 "$HEALTH_URL" | python3 -m json.tool 2>/dev/null || curl -s --max-time 5 "$HEALTH_URL"
    elif [ "$HTTP_CODE" = "000" ]; then
        echo "Health: UNREACHABLE (connection failed)"
    else
        echo "Health: UNHEALTHY (HTTP $HTTP_CODE)"
    fi
else
    echo "Health: UNKNOWN (curl not available)"
fi

echo
echo "Log file: $LOG_FILE"

# Show recent log entries
if [ -f "$LOG_FILE" ]; then
    echo
    echo "Recent logs (last 10 lines):"
    echo "---"
    tail -10 "$LOG_FILE"
fi
