#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# OCE Hermes Telegram Operator — Status Script
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_DIR/.pids"

echo "═══════════════════════════════════════════════════════════════════"
echo "  OCE Hermes Telegram Operator — Status"
echo "═══════════════════════════════════════════════════════════════════"

check_process() {
    local name=$1
    local pid_file="$PID_DIR/$2"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  ✅ $name: RUNNING (PID: $pid)"
            return 0
        else
            echo "  ❌ $name: DEAD (stale PID: $pid)"
            return 1
        fi
    else
        echo "  ⚠️  $name: NOT STARTED"
        return 1
    fi
}

check_process "OCE MCP Facade" "oce-mcp-facade.pid"
check_process "Hermes Agent" "hermes-operator.pid"

# Check port binding
echo ""
echo "  Network listeners:"
if command -v ss &>/dev/null; then
    ss -tlnp 2>/dev/null | grep -E "127\.0\.0\.1:(9090|8000)" || echo "    No relevant ports bound"
elif command -v netstat &>/dev/null; then
    netstat -tlnp 2>/dev/null | grep -E "127\.0\.0\.1:(9090|8000)" || echo "    No relevant ports bound"
else
    echo "    (ss/netstat not available)"
fi

# Check .env
echo ""
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "  ✅ .env: EXISTS"
    if grep -q "TELEGRAM_BOT_TOKEN=." "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  ✅ TELEGRAM_BOT_TOKEN: SET"
    else
        echo "  ❌ TELEGRAM_BOT_TOKEN: NOT SET"
    fi
    if grep -q "TELEGRAM_ALLOWED_USERS=." "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  ✅ TELEGRAM_ALLOWED_USERS: SET"
    else
        echo "  ❌ TELEGRAM_ALLOWED_USERS: NOT SET"
    fi
else
    echo "  ❌ .env: NOT FOUND — run ./scripts/setup.sh first"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
