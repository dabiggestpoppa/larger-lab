#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# OCE Hermes Telegram Operator — Setup Script
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════════════════════════════"
echo "  OCE Hermes Telegram Operator — Setup"
echo "═══════════════════════════════════════════════════════════════════"

# ─── 1. Check Python ──────────────────────────────────────────────────────────
echo ""
echo "[1/6] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3.11+ required. Install from https://python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON_VERSION"

# ─── 2. Install dependencies ──────────────────────────────────────────────────
echo ""
echo "[2/6] Installing Python dependencies..."
cd "$PROJECT_DIR"
if command -v pip3 &>/dev/null; then
    pip3 install -e ".[dev]" 2>/dev/null || pip3 install httpx mcp aiohttp pytest pytest-asyncio
elif command -v pip &>/dev/null; then
    pip install -e ".[dev]" 2>/dev/null || pip install httpx mcp aiohttp pytest pytest-asyncio
else
    echo "  WARNING: pip not found. Install dependencies manually."
fi
echo "  Done."

# ─── 3. Create directories ────────────────────────────────────────────────────
echo ""
echo "[3/6] Creating directories..."
mkdir -p "$PROJECT_DIR/evidence"
mkdir -p "$PROJECT_DIR/logs"
echo "  Done."

# ─── 4. Create .env from template ────────────────────────────────────────────
echo ""
echo "[4/6] Checking environment configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "  Created .env from template."
    echo "  ⚠️  You MUST edit .env and add your secrets before starting."
    echo "     Required: TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS"
else
    echo "  .env already exists."
fi

# ─── 5. Install Hermes Agent ─────────────────────────────────────────────────
echo ""
echo "[5/6] Checking Hermes Agent installation..."
if command -v hermes &>/dev/null; then
    echo "  Hermes Agent: $(hermes --version 2>/dev/null || echo 'installed')"
else
    echo "  Hermes Agent not found."
    echo "  Install with: pip install hermes-agent"
    echo "  Or follow: https://hermes-agent.nousresearch.com/docs/"
    echo "  Continuing without Hermes (MCP facade only)."
fi

# ─── 6. Validate ─────────────────────────────────────────────────────────────
echo ""
echo "[6/6] Running validation..."
python3 "$SCRIPT_DIR/doctor.py" 2>/dev/null || echo "  Doctor script skipped."

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your Telegram bot token and user ID"
echo "  2. Run: ./scripts/start.sh"
echo "  3. Send /start to your bot on Telegram"
echo "═══════════════════════════════════════════════════════════════════"
