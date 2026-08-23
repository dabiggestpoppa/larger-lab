#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# OCE Hermes Telegram Operator — Stop Script
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_DIR/.pids"

echo "═══════════════════════════════════════════════════════════════════"
echo "  OCE Hermes Telegram Operator — Stopping"
echo "═══════════════════════════════════════════════════════════════════"

stop_process() {
    local name=$1
    local pid_file="$PID_DIR/$2"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping $name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                echo "  Force killing $name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo "  $name stopped."
        else
            echo "  $name not running (stale PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo "  $name: no PID file found"
    fi
}

stop_process "Hermes Agent" "hermes-operator.pid"
stop_process "OCE MCP Facade" "oce-mcp-facade.pid"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  All services stopped."
echo "═══════════════════════════════════════════════════════════════════"
