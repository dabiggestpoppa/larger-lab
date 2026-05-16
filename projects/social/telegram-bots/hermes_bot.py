"""
Hermes Telegram Bot — Architect & Planner
Token: 8851242922:AAGWGZaEwA0LxBYISo460Z08WC4aE_JirvE
"""

import subprocess, sys, re, logging
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"
TOKEN = "8851242922:AAGWGZaEwA0LxBYISo460Z08WC4aE_JirvE"


def read_progress():
    if PROGRESS_FILE.exists():
        return PROGRESS_FILE.read_text(encoding='utf-8')
    return "No progress file found."


def append_progress(entry: str, agent: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n- [{timestamp}] **{agent}**: {entry}"
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    return line


def get_workspace_summary():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.')])
    files = sorted([f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')])
    return dirs[:12], files[:12]


def handle_hermes(text: str) -> str:
    c = text.lower().strip()

    if any(w in c for w in ['status', 'progress', 'update', 'how are we']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-10:]
        return f"🔱 *Hermes Status*\n```\n{chr(10).join(lines)[:1000]}\n```"

    if any(w in c for w in ['help', 'what can', 'commands']):
        return ("🔱 *Hermes — Architect & Planner*\n\n"
                "Commands:\n"
                "`status` — project progress\n"
                "`workspace` — list files/dirs\n"
                "`plan: <text>` — log a plan\n"
                "`decision: <text>` — log decision\n"
                "Or just ask me anything!")

    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"🔱 *Workspace*\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}"

    if c.startswith('plan ') or c.startswith('plan:'):
        plan_text = re.sub(r'^plan[:\s]*', '', c, flags=re.IGNORECASE).strip()
        append_progress(f"PLAN: {plan_text}", "Hermes")
        return f"🔱 Plan logged: {plan_text}"

    if 'decision:' in c or c.startswith('decide'):
        text_clean = re.sub(r'^decide[:\s]*', '', c.split(':', 1)[-1].strip() if ':' in c else c, flags=re.IGNORECASE).strip()
        append_progress(f"DECISION: {text_clean}", "Hermes")
        return f"🔱 Decision logged: {text_clean}"

    return f"🔱 Hermes here. \"{text[:150]}\" — try status, workspace, plan:, decision:"


# ── Telegram handlers ──
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔱 *Hermes — Architect & Planner*\n\n"
        "I coordinate the agent team. Send me a message or use:\n"
        "/status — project progress\n"
        "/workspace — list files\n"
        "/help — all commands",
        parse_mode='Markdown'
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [l for l in read_progress().split('\n') if l.strip()][-10:]
    await update.message.reply_text(
        f"🔱 *Hermes Status*\n```\n{chr(10).join(lines)[:1000]}\n```",
        parse_mode='Markdown'
    )


async def workspace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dirs, files = get_workspace_summary()
    await update.message.reply_text(
        f"🔱 *Workspace*\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}",
        parse_mode='Markdown'
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔱 *Hermes Commands*\n\n"
        "/status — project progress\n"
        "/workspace — list files/dirs\n"
        "/help — this message\n\n"
        "Or just send me text:\n"
        "`status` `workspace` `plan: <text>` `decision: <text>`",
        parse_mode='Markdown'
    )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = handle_hermes(text)
    await update.message.reply_text(response, parse_mode='Markdown')


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("workspace", workspace_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    logger.info("🔱 Hermes bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
