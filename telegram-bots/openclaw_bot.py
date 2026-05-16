"""
OpenClaw Telegram Bot — Builder & Executor
Token: 8883788073:AAF11_ZrLXgDrs_SZUj_V6m9_YzKq9mMvy8
"""

import subprocess, sys, re, logging
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"
TOKEN = "8883788073:AAF11_ZrLXgDrs_SZUj_V6m9_YzKq9mMvy8"


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


def handle_openclaw(text: str) -> str:
    c = text.lower().strip()

    if any(w in c for w in ['status', 'progress', 'what are you doing']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
        return f"🦀 *OpenClaw Status*\n```\n{chr(10).join(lines)[:800]}\n```"

    if any(w in c for w in ['help', 'what can', 'commands']):
        return ("🦀 *OpenClaw — Builder & Executor*\n\n"
                "Commands:\n"
                "`status` — check progress\n"
                "`workspace` — list files\n"
                "`run <script.py>` — run a script\n"
                "`edit: <text>` — add to progress\n"
                "`create: <file> | <content>` — create file")

    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"🦀 *Workspace*\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}"

    if c.startswith('run '):
        script = text[4:].strip()
        sp = WORKSPACE / script
        if sp.exists():
            try:
                r = subprocess.run([sys.executable, str(sp)], capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE))
                out = r.stdout[:1200] or r.stderr[:1200] or "(no output)"
                return f"🦀 Ran `{script}`:\n```\n{out}\n```"
            except subprocess.TimeoutExpired:
                return f"🦀 `{script}` timed out (30s)"
            except Exception as e:
                return f"🦀 Error: {e}"
        return f"🦀 Script not found: `{script}`"

    if c.startswith('edit:') or c.startswith('edit progress:'):
        edit_text = re.sub(r'^edit( progress)?[:\s]*', '', c, flags=re.IGNORECASE).strip()
        append_progress(edit_text, "OpenClaw")
        return f"🦀 Progress updated: {edit_text}"

    if c.startswith('create:') or c.startswith('create file:'):
        parts = re.sub(r'^create( file)?[:\s]*', '', c, flags=re.IGNORECASE).strip().split('|', 1)
        fname = parts[0].strip()
        fcontent = parts[1].strip() if len(parts) > 1 else "# Created by OpenClaw\n"
        try:
            (WORKSPACE / fname).write_text(fcontent, encoding='utf-8')
            return f"🦀 Created: `{fname}`"
        except Exception as e:
            return f"🦀 Error: {e}"

    return f"🦀 OpenClaw here. \"{text[:150]}\" — try status, workspace, run <script>, edit: <text>"


# ── Telegram handlers ──
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 *OpenClaw — Builder & Executor*\n\n"
        "I handle building, execution, and implementation. Send me a message or use:\n"
        "/status — check progress\n"
        "/workspace — list files\n"
        "/help — all commands",
        parse_mode='Markdown'
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
    await update.message.reply_text(
        f"🦀 *OpenClaw Status*\n```\n{chr(10).join(lines)[:800]}\n```",
        parse_mode='Markdown'
    )


async def workspace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dirs, files = get_workspace_summary()
    await update.message.reply_text(
        f"🦀 *Workspace*\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}",
        parse_mode='Markdown'
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 *OpenClaw Commands*\n\n"
        "/status — check progress\n"
        "/workspace — list files/dirs\n"
        "/help — this message\n\n"
        "Or just send me text:\n"
        "`status` `workspace` `run <script>` `edit: <text>` `create: <file> | <content>`",
        parse_mode='Markdown'
    )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = handle_openclaw(text)
    await update.message.reply_text(response, parse_mode='Markdown')


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("workspace", workspace_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    logger.info("🦀 OpenClaw bot starting...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
