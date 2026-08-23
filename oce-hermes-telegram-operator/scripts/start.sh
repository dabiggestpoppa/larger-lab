#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# OCE Hermes Telegram Operator — Start Script
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_DIR/.pids"
LOG_DIR="$PROJECT_DIR/logs"

# ─── Load .env ────────────────────────────────────────────────────────────────
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# ─── Pre-flight checks ───────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════"
echo "  OCE Hermes Telegram Operator — Starting"
echo "═══════════════════════════════════════════════════════════════════"

# Check required env vars
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "  FATAL: TELEGRAM_BOT_TOKEN not set. Edit .env first."
    exit 1
fi

if [ -z "${TELEGRAM_ALLOWED_USERS:-}" ]; then
    echo "  FATAL: TELEGRAM_ALLOWED_USERS not set. Edit .env first."
    exit 1
fi

if [ "${TELEGRAM_ALLOW_ALL_USERS:-false}" = "true" ]; then
    echo "  FATAL: TELEGRAM_ALLOW_ALL_USERS=true is rejected."
    exit 1
fi

# ─── Create directories ──────────────────────────────────────────────────────
mkdir -p "$PID_DIR" "$LOG_DIR" "$PROJECT_DIR/evidence"

# ─── Check for running instances ─────────────────────────────────────────────
FACADE_PID_FILE="$PID_DIR/oce-mcp-facade.pid"
HERMES_PID_FILE="$PID_DIR/hermes-operator.pid"

if [ -f "$FACADE_PID_FILE" ]; then
    OLD_PID=$(cat "$FACADE_PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "  OCE MCP Facade already running (PID: $OLD_PID)"
        echo "  Use ./scripts/stop.sh first."
        exit 1
    fi
fi

# ─── Start OCE MCP Facade ────────────────────────────────────────────────────
echo ""
echo "[1/2] Starting OCE MCP Facade..."
cd "$PROJECT_DIR"
python3 -m src.oce_mcp_facade.facade > "$LOG_DIR/facade.log" 2>&1 &
FACADE_PID=$!
echo "$FACADE_PID" > "$FACADE_PID_FILE"
echo "  Facade PID: $FACADE_PID"

# Wait for facade to be ready
sleep 2
if ! kill -0 "$FACADE_PID" 2>/dev/null; then
    echo "  ERROR: Facade failed to start. Check logs/facade.log"
    exit 1
fi
echo "  Facade is running."

# ─── Start Hermes Agent ──────────────────────────────────────────────────────
echo ""
echo "[2/2] Starting Hermes Agent..."
if command -v hermes &>/dev/null; then
    hermes gateway --profile oce-operator > "$LOG_DIR/hermes.log" 2>&1 &
    HERMES_PID=$!
    echo "$HERMES_PID" > "$HERMES_PID_FILE"
    echo "  Hermes PID: $HERMES_PID"
    echo "  Hermes is starting..."
else
    echo "  WARNING: Hermes Agent not installed."
    echo "  The MCP facade is running on 127.0.0.1:9090"
    echo "  Install Hermes to enable Telegram integration."
fi

# ─── Save startup state ─────────────────────────────────────────────────────
cat > "$PROJECT_DIR/evidence/startup.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "facade_pid": $FACADE_PID,
  "hermes_pid": ${HERMES_PID:-null},
  "mock_mode": ${USE_MOCK:-true},
  "config_validated": true
}
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  System is running!"
echo ""
echo "  Facade: http://127.0.0.1:9090"
echo "  Logs:   $LOG_DIR/"
echo "  Stop:   ./scripts/stop.sh"
echo "  Status: ./scripts/status.sh"
echo "═══════════════════════════════════════════════════════════════════"
