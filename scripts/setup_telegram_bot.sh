#!/usr/bin/env bash
# setup_telegram_bot.sh — Helper to validate and configure the PO Telegram bot
# Usage: ./scripts/setup_telegram_bot.sh [--poll] [--webhook] [--validate-only]
#
# This script:
#   1. Checks for TELEGRAM_TOKEN in environment or .env
#   2. Validates the token by calling Telegram's getMe API
#   3. Prints bot info and chat ID instructions
#   4. Optionally sets up webhook or polling mode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$WORKSPACE_DIR/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Primary Observer — Telegram Bot Setup      ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Parse arguments ────────────────────────────────────────────────────────
MODE="poll"  # default: polling mode
VALIDATE_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --poll)     MODE="poll" ;;
        --webhook)  MODE="webhook" ;;
        --validate-only) VALIDATE_ONLY=true ;;
        --help|-h)
            echo "Usage: $0 [--poll] [--webhook] [--validate-only]"
            echo ""
            echo "  --poll          Use polling mode (default, recommended for dev)"
            echo "  --webhook       Use webhook mode (production)"
            echo "  --validate-only Just validate token and exit"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Use --help for usage."
            exit 1
            ;;
    esac
done

# ── Step 1: Find the token ─────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Looking for TELEGRAM_TOKEN...${NC}"

TOKEN=""

# Check environment first
if [ -n "$TELEGRAM_TOKEN" ]; then
    TOKEN="$TELEGRAM_TOKEN"
    echo "  Found in environment variable."
# Then check .env file
elif [ -f "$ENV_FILE" ]; then
    TOKEN=$(grep -i "^TELEGRAM_TOKEN=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2-)
    if [ -n "$TOKEN" ]; then
        echo "  Found in .env file."
        export TELEGRAM_TOKEN="$TOKEN"
    fi
fi

if [ -z "$TOKEN" ]; then
    echo -e "${RED}  ✗ TELEGRAM_TOKEN not found!${NC}"
    echo "  Set it in your environment or add to .env file:"
    echo "    TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    echo "  To get a token, talk to @BotFather on Telegram and use /newbot"
    exit 1
fi

echo "  Token: ${TOKEN:0:10}..."
echo ""

# ── Step 2: Validate token with Telegram API ───────────────────────────────
echo -e "${YELLOW}[2/4] Validating token with Telegram API...${NC}"

API_URL="https://api.telegram.org/bot${TOKEN}"

RESPONSE=$(curl -s -m 15 "${API_URL}/getMe" 2>/dev/null)

if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_USERNAME=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'].get('username','N/A'))" 2>/dev/null || echo "unknown")
    BOT_NAME=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'].get('first_name','N/A'))" 2>/dev/null || echo "unknown")
    BOT_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'].get('id','N/A'))" 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓ Token valid!${NC}"
    echo "  Bot Name:  $BOT_NAME"
    echo "  Username:  @$BOT_USERNAME"
    echo "  Bot ID:    $BOT_ID"
else
    echo -e "  ${RED}✗ Token invalid!${NC}"
    echo "  Response: $RESPONSE"
    echo ""
    echo "  Make sure you:"
    echo "  1. Talked to @BotFather and created a bot"
    echo "  2. Copied the token correctly"
    echo "  3. Haven't revoked the token"
    exit 1
fi
echo ""

# ── Step 3: Check API connectivity ─────────────────────────────────────────
echo -e "${YELLOW}[3/4] Checking API connectivity...${NC}"

# DNS check
if ping -c 1 -W 3 api.telegram.org &>/dev/null; then
    echo -e "  ${GREEN}✓ DNS: api.telegram.org reachable${NC}"
else
    echo -e "  ${RED}✗ DNS: api.telegram.org not reachable${NC}"
    echo "  Check your internet connection or DNS settings."
fi

# HTTPS check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "https://api.telegram.org" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo -e "  ${GREEN}✓ HTTPS: API responding ($HTTP_CODE)${NC}"
else
    echo -e "  ${RED}✗ HTTPS: Unexpected response ($HTTP_CODE)${NC}"
fi

# getUpdates test (what the bot will actually use)
UPDATES=$(curl -s -m 15 "${API_URL}/getUpdates?limit=1&timeout=1" 2>/dev/null)
if echo "$UPDATES" | grep -q '"ok":true'; then
    PENDING=$(echo "$UPDATES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('result',[])))" 2>/dev/null || echo "?")
    echo -e "  ${GREEN}✓ getUpdates: working ($PENDING pending messages)${NC}"
else
    echo -e "  ${RED}✗ getUpdates: failed${NC}"
    echo "  Response: $(echo "$UPDATES" | head -c 200)"
fi
echo ""

# ── Step 4: Chat ID setup ──────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Chat ID setup${NC}"

CHAT_ID=$(grep -i "^TELEGRAM_CHAT_ID=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d ' ' || echo "")

if [ -n "$CHAT_ID" ]; then
    echo "  Chat ID configured: $CHAT_ID"
else
    echo -e "  ${YELLOW}⚠ No TELEGRAM_CHAT_ID in .env${NC}"
    echo "  To find your chat ID:"
    echo "  1. Start a chat with your bot (@$BOT_USERNAME)"
    echo "  2. Send any message"
    echo "  3. Visit: ${API_URL}/getUpdates"
    echo "  4. Look for 'chat':{'id': 123456789}"
    echo ""
    echo "  Then add to .env:"
    echo "    TELEGRAM_CHAT_ID=123456789"
fi
echo ""

# ── Mode selection ─────────────────────────────────────────────────────────
echo -e "${BOLD}Mode: ${MODE}${NC}"
if [ "$MODE" = "poll" ]; then
    echo "  Using polling mode (recommended for development)"
    echo "  Run: python scripts/start_telegram_gateway.py"
else
    echo "  Using webhook mode (production)"
    echo "  You'll need to set WEBHOOK_URL and configure the endpoint"
fi

# ── Final status ───────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${GREEN}Validation complete. Token is valid.${NC}"
else
    echo -e "${GREEN}Setup complete. Ready to start the bot.${NC}"
    echo ""
    echo "  Next step:"
    echo "    python scripts/start_telegram_gateway.py"
    echo ""
    echo "  Or with .env loaded:"
    echo "    set TELEGRAM_TOKEN=${TOKEN}"
    echo "    python scripts/start_telegram_gateway.py"
fi
echo -e "${BOLD}════════════════════════════════════════${NC}"