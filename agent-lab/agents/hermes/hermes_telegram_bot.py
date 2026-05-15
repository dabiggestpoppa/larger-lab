#!/usr/bin/env python3
"""
Hermes Telegram Bot - Monitor and control the Hermes MT5 Agent via Telegram.

Commands:
  /start     - Welcome message
  /status    - Current agent status and iteration
  /progress  - Full progress log
  /config    - Show current model configuration
  /pause     - Pause the agent
  /resume    - Resume the agent
  /stop      - Stop the agent
  /help      - Show all commands

Usage:
  1. Set TELEGRAM_BOT_TOKEN env var (get from @BotFather)
  2. Run: python hermes_telegram_bot.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ── Setup ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
# Prefer new summary file; fallback to legacy MT5 progress file
PROGRESS_FILE = BASE_DIR / "hermes_progress_summary.json"
LEGACY_PROGRESS_FILE = BASE_DIR / "hermes_mt5_progress.json"
CONFIG_FILE = BASE_DIR / "hermes_mt5_config.json"

# Global state
_paused = False
_stopped = False
_agent_task = None


def load_json(path: Path) -> dict | list | None:
    """Safely load a JSON file."""
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return None


def get_status_text() -> str:
    """Build a status summary string."""
    config = load_json(CONFIG_FILE) or {}
    progress = load_json(PROGRESS_FILE) or load_json(LEGACY_PROGRESS_FILE) or []

    model_cfg = config.get("model_config", {})
    goal = config.get("goal", "N/A")
    max_iter = config.get("schedule", {}).get("max_iterations", 100)
    profit_target = config.get("schedule", {}).get("profit_target", "N/A")
    backtest_engine = config.get("schedule", {}).get("backtest_engine", "nautilus")

    current_iter = len(progress)
    last_status = progress[-1] if progress else {}
    last_time = last_status.get("timestamp", "Never")

    # Model status indicators
    models = {
        "🟢 Main": model_cfg.get("main_agent", "N/A"),
        "🔵 Orch": model_cfg.get("orchestrator", "N/A"),
        "🟣 Code": model_cfg.get("code_reviewer", "N/A"),
    }

    lines = [
        "⚡ *Hermes Agent Status*",
        "",
        f"🎯 Goal: {goal}",
        f"📈 Iteration: *{current_iter}/{max_iter}*",
        f"⏰ Last update: `{last_time[:19] if last_time else 'N/A'}`",
        f"🎯 Target: {profit_target}",
        f"🔧 Backtest engine: {backtest_engine}",
        "",
        "🤖 *Models:*",
    ]
    for label, model in models.items():
        lines.append(f"  {label}: `{model}`")

    lines.append("")
    if _stopped:
        lines.append("🔴 *Status: STOPPED*")
    elif _paused:
        lines.append("🟡 *Status: PAUSED*")
    else:
        lines.append("🟢 *Status: RUNNING*")

    return "\n".join(lines)


# ── Command Handlers ─────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message."""
    welcome = (
        "⚡ *Hermes MT5 Agent Monitor*\n\n"
        "I'm your gateway to monitoring the Hermes MT5 strategy agent.\n\n"
        "📋 *Commands:*\n"
        "/status  - Current agent status\n"
        "/progress - Full progress log\n"
        "/config  - Model configuration\n"
        "/pause   - Pause the agent\n"
        "/resume  - Resume the agent\n"
        "/stop    - Stop the agent\n"
        "/help    - Show all commands\n"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current agent status."""
    text = get_status_text()
    await update.message.reply_text(text, parse_mode="Markdown")


async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show full progress log."""
    progress = load_json(PROGRESS_FILE) or []

    if not progress:
        await update.message.reply_text("📭 No progress logged yet.")
        return

    lines = ["📊 *Progress Log*\n"]
    for entry in progress[-20:]:  # Last 20 entries
        iter_num = entry.get("iteration", "?")
        ts = entry.get("timestamp", "N/A")[:19]
        status = entry.get("status", "unknown")
        emoji = {"running": "🟢", "paused": "🟡", "stopped": "🔴"}.get(status, "⚪")
        lines.append(f"{emoji} Iter {iter_num} | `{ts}` | {status}")

    if len(progress) > 20:
        lines.append(f"\n_... and {len(progress) - 20} more entries_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show model configuration."""
    config = load_json(CONFIG_FILE) or {}
    model_cfg = config.get("model_config", {})
    schedule = config.get("schedule", {})

    lines = [
        "⚙️ *Hermes Configuration*\n",
        "🤖 *Models:*",
        f"  🟢 Main: `{model_cfg.get('main_agent', 'N/A')}`",
        f"  🔵 Orchestrator: `{model_cfg.get('orchestrator', 'N/A')}`",
        f"  🟣 Code Review: `{model_cfg.get('code_reviewer', 'N/A')}`",
        f"  🔄 Fallback: `{model_cfg.get('fallback', 'N/A')}`",
        "",
        "📅 *Schedule:*",
        f"  Max iterations: {schedule.get('max_iterations', 'N/A')}",
        f"  Check interval: {schedule.get('check_interval_minutes', 'N/A')} min",
        f"  Profit target: {schedule.get('profit_target', 'N/A')}",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def pause_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pause the agent."""
    global _paused
    _paused = True
    await update.message.reply_text("🟡 Agent *paused*. Use /resume to continue.", parse_mode="Markdown")


async def resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resume the agent."""
    global _paused
    _paused = False
    await update.message.reply_text("🟢 Agent *resumed*. Use /pause to pause again.", parse_mode="Markdown")


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the agent."""
    global _stopped
    _stopped = True
    await update.message.reply_text("🔴 Agent *stopped*. Restart the process to run again.", parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help."""
    await start_cmd(update, context)


# ── Notification Sender (called from agent) ──────────────────────────────────

async def send_notification(bot_token: str, chat_id: str, message: str):
    """Send a notification message to Telegram. Can be called from the agent."""
    app = Application.builder().token(bot_token).build()
    await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")


def notify_sync(bot_token: str, chat_id: str, message: str):
    """Synchronous wrapper for send_notification."""
    try:
        asyncio.run(send_notification(bot_token, chat_id, message))
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run the Telegram bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        print("   Get a token from @BotFather on Telegram.")
        print("   Then run: $env:TELEGRAM_BOT_TOKEN='your-token-here'")
        sys.exit(1)

    print("🤖 Starting Hermes Telegram Bot...")
    print("   Send /start to your bot to begin.")

    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("progress", progress_cmd))
    app.add_handler(CommandHandler("config", config_cmd))
    app.add_handler(CommandHandler("pause", pause_cmd))
    app.add_handler(CommandHandler("resume", resume_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
