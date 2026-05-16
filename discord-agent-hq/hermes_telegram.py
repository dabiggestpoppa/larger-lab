"""
Hermes Telegram Bot - Architect & Planner
Runs alongside OWL in the same Telegram chat.
"""

import os, re, subprocess, sys, logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s [HERMES] %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"

# ── Hermes Memory ──
HERMES_MEMORY = WORKSPACE / "progress" / "hermes-progress.md"


def read_progress():
    if PROGRESS_FILE.exists():
        return PROGRESS_FILE.read_text(encoding='utf-8')
    return "No progress file found."


def append_progress(entry):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n- [{timestamp}] **Hermes**: {entry}"
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    return line


def get_workspace_summary():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.')])
    files = sorted([f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')])
    return dirs[:12], files[:12]


def hermes_respond(content: str) -> str:
    c = content.lower().strip()

    # -- Status / Progress --
    if any(w in c for w in ['status', 'progress', 'update', 'how are we', 'what are you doing', 'ready']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-15:]
        dirs, files = get_workspace_summary()
        return (
            f"HERMES Status Report\n"
            f"\nRecent Progress:\n" + "\n".join(lines)[:2000] +
            f"\n\nWorkspace: {len(dirs)} dirs, {len(files)} key files\n"
            f"Active Phase: SRRA-OPH Phase 4 (Workspace Integration)\n"
            f"All systems operational. Ready to build."
        )

    # -- Help --
    if any(w in c for w in ['help', 'what can', 'commands']):
        return (
            "HERMES - Architect & Planner\n\n"
            "Commands:\n"
            "/status - Project progress\n"
            "/workspace - List files/dirs\n"
            "/plan <idea> - Log a plan\n"
            "/decision <text> - Log architecture decision\n"
            "/team - Team status\n"
            "/memory - Read Hermes memory\n\n"
            "Or just talk to me directly about the project."
        )

    # -- Workspace --
    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"Workspace\nDirs: {', '.join(dirs)}\nKey Files: {', '.join(files)}"

    # -- Plan --
    if any(w in c for w in ['plan', 'idea', 'proposal', 'suggest']):
        text = re.sub(r'^/?plan[:\s]*', '', c, flags=re.IGNORECASE).strip()
        if text and len(text) > 3:
            return f"Plan logged: {append_progress('PLAN: ' + text)}"
        return "Usage: /plan <your idea>"

    # -- Decision --
    if any(w in c for w in ['decision', 'decide', 'choose']):
        text = c
        if ':' in text:
            text = text.split(':', 1)[-1].strip()
        if text and len(text) > 3:
            return f"Decision logged: {append_progress('DECISION: ' + text)}"
        return "Usage: /decision <your decision>"

    # -- Team --
    if any(w in c for w in ['team', 'agents', 'who']):
        progress_dir = WORKSPACE / "progress"
        agents = []
        if progress_dir.exists():
            for f in progress_dir.glob("*-progress.md"):
                name = f.stem.replace('-progress', '').upper()
                agents.append(name)
        return f"Active Agents: {', '.join(agents) if agents else 'None detected'}\n\nI coordinate the team and track architecture decisions."

    # -- Memory --
    if any(w in c for w in ['memory', 'remember']):
        if HERMES_MEMORY.exists():
            mem = HERMES_MEMORY.read_text(encoding='utf-8')[:2000]
            return f"Hermes Memory\n{mem}"
        return "No dedicated memory file yet. I track everything in the shared workspace progress files."

    # -- Build / Work requests --
    if any(w in c for w in ['build', 'create', 'make', 'start', 'work', 'do', 'ready']):
        return (
            "Ready. What are we building?\n\n"
            "Current focus areas:\n"
            "- SRRA-OPH Phase 4: Workspace Integration\n"
            "- P90 strategy parameter tuning\n"
            "- Agent team coordination\n"
            "\nTell me what you need and I'll architect it."
        )

    # -- Greeting --
    if any(w in c for w in ['hi', 'hello', 'hey', 'yo', 'sup']):
        return "HERMES online. What do you need?"

    # -- Default: actually be useful --
    return (
        f"I heard: \"{content[:150]}\"\n\n"
        f"I'm the Architect & Planner. I can help with:\n"
        f"- Project status and progress tracking\n"
        f"- Architecture decisions and planning\n"
        f"- Team coordination\n"
        f"- Workspace file management\n\n"
        f"Try /status for a full update, or just tell me what you're working on."
    )


# ── Telegram Handlers ──

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "HERMES - Architect & Planner online.\n"
        "I coordinate the agent team and track project architecture.\n"
        "Use /help for commands or just talk to me."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("help"))


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("status"))


async def workspace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("workspace"))


async def plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args) if context.args else ''
    await update.message.reply_text(hermes_respond(f"plan {text}"))


async def decision_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args) if context.args else ''
    await update.message.reply_text(hermes_respond(f"decision: {text}"))


async def team_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("team"))


async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("memory"))


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Don't respond to empty messages or commands
    if not update.message or not update.message.text:
        return
    if update.message.text.startswith('/'):
        return

    text = update.message.text.strip()
    logger.info(f"Message from {update.effective_user.username}: {text[:80]}")

    response = hermes_respond(text)
    await update.message.reply_text(response)


# ── Main ──

def main():
    token = os.getenv("TELEGRAM_HERMES_TOKEN")
    if not token:
        logger.error("TELEGRAM_HERMES_TOKEN not set")
        sys.exit(1)

    logger.info("Starting Hermes Telegram bot...")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("workspace", workspace_cmd))
    app.add_handler(CommandHandler("plan", plan_cmd))
    app.add_handler(CommandHandler("decision", decision_cmd))
    app.add_handler(CommandHandler("team", team_cmd))
    app.add_handler(CommandHandler("memory", memory_cmd))

    # Regular messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logger.info("Hermes bot running. Waiting for messages...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
