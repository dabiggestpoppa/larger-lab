#!/usr/bin/env python3
"""Start the Primary Observer Telegram Gateway.

Loads .env, then launches the full Telegram Presence System
(telegram_gateway.py) with POAgent, SovereignField, CommandRouter,
Presence Engine, session management, and PID locking.

Usage:
    python scripts/start_telegram_gateway.py
    TELEGRAM_TOKEN=xxx python scripts/start_telegram_gateway.py
"""
import os
import sys

# ── Resolve workspace root and inject into path ──────────────────────────
_ws_root = os.path.dirname(os.path.abspath(__file__))  # scripts/
_project_root = os.path.dirname(_ws_root)               # larger-lab/
sys.path.insert(0, _project_root)

# ── Load .env from project root ──────────────────────────────────────────
_env_path = os.path.join(_project_root, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Verify token ─────────────────────────────────────────────────────────
token = os.environ.get("TELEGRAM_TOKEN")
if not token:
    print("ERROR: TELEGRAM_TOKEN not set in environment or .env file.")
    print("  Create a bot via @BotFather on Telegram and set the token.")
    print("  See docs/reference/TELEGRAM_BOT_SETUP.md for instructions.")
    sys.exit(1)

# ── Launch the gateway ───────────────────────────────────────────────────
from scripts.telegram_gateway import main

if __name__ == "__main__":
    print("=" * 60)
    print("  PRIMARY OBSERVER — TELEGRAM GATEWAY")
    print("=" * 60)
    main()