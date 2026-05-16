"""
Hermes Telegram Bot - Architect & Planner v2
Reads workspace state, understands context, responds intelligently.
"""

import os, re, subprocess, sys, logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s [HERMES] %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"
TEAM_CHAT = WORKSPACE / "shared-conversations" / "team-chat.md"
HERMES_PROGRESS = WORKSPACE / "progress" / "hermes-progress.md"
ASSISTANT_PROGRESS = WORKSPACE / "progress" / "assistant-progress.md"
CLAUDE_PROGRESS = WORKSPACE / "progress" / "claude-code-progress.md"
OPENCLAW_PROGRESS = WORKSPACE / "progress" / "openclaw-progress.md"
POLYMORPH_PROGRESS = WORKSPACE / "progress" / "polymorph-progress.md"
SRRA_OPC = WORKSPACE / "srrs_opc"
PHASE_STATE = WORKSPACE / ".phase-state.json"


def read_file(path, max_chars=3000):
    if path.exists():
        return path.read_text(encoding='utf-8')[:max_chars]
    return ""


def get_phase_state():
    if PHASE_STATE.exists():
        import json
        return json.loads(PHASE_STATE.read_text())
    return {}


def get_all_progress():
    """Read all agent progress files for full context."""
    agents = {}
    progress_dir = WORKSPACE / "progress"
    if progress_dir.exists():
        for f in progress_dir.glob("*-progress.md"):
            name = f.stem.replace('-progress', '')
            content = f.read_text(encoding='utf-8')
            # Extract status and recent entries
            lines = [l for l in content.split('\n') if l.strip()]
            agents[name] = {
                'file': f.name,
                'lines': lines[-20:],  # last 20 lines
                'status': 'unknown'
            }
            for line in lines:
                if 'Status:' in line:
                    agents[name]['status'] = line.split('Status:')[-1].strip()
                    break
    return agents


def get_workspace_structure():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != '.venv'])
    key_files = []
    for f in WORKSPACE.iterdir():
        if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt', '.yml'):
            key_files.append(f.name)
    return dirs, sorted(key_files)[:15]


def get_test_status():
    """Check if tests are passing."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(SRRA_OPC / 'tests'), '-q', '--tb=no'],
            capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        if 'passed' in output:
            # Extract count
            match = re.search(r'(\d+) passed', output)
            if match:
                return f"{match.group(1)} tests passing"
        return "Test status unknown"
    except:
        return "Could not run tests"


def hermes_respond(user_message: str) -> str:
    """
    Generate intelligent response based on actual workspace state.
    This is NOT a canned response — it reads real files and builds context.
    """
    c = user_message.lower().strip()
    timestamp = datetime.now().strftime('%H:%M')

    # ── Gather real context ──
    phase = get_phase_state()
    agents = get_all_progress()
    dirs, files = get_workspace_structure()
    progress_text = read_file(PROGRESS_FILE, 2000)
    hermes_text = read_file(HERMES_PROGRESS, 1500)
    team_text = read_file(TEAM_CHAT, 1000)

    # ── STATUS / PROGRESS ──
    if any(w in c for w in ['status', 'progress', 'update', 'how are we', 'what are you doing', 'ready']):
        current_phase = phase.get('current_phase', 'Unknown')
        phase_status = phase.get('status', 'Unknown')

        # Build agent status
        agent_lines = []
        for name, data in agents.items():
            status = data.get('status', '?')
            # Clean up status
            status = status.replace('**', '').strip()
            agent_lines.append(f"  {name}: {status}")

        agent_status = "\n".join(agent_lines) if agent_lines else "  No agent progress files found"

        # Get recent progress entries
        recent = [l for l in progress_text.split('\n') if l.strip() and ('[' in l or '-' in l[:5])][-8:]

        return (
            f"HERMES Status Report [{timestamp}]\n"
            f"Phase: {current_phase} ({phase_status})\n"
            f"\nAgents:\n{agent_status}\n"
            f"\nRecent Activity:\n" + "\n".join(recent)[:800] +
            f"\n\nWorkspace: {len(dirs)} dirs | {len(files)} key files"
        )

    # ── HELP ──
    if any(w in c for w in ['help', 'what can', 'commands']):
        return (
            "HERMES - Architect & Planner\n\n"
            "I read from the shared workspace to give you real status.\n\n"
            "Commands:\n"
            "/status - Full project status from all agents\n"
            "/workspace - Workspace structure\n"
            "/agents - Individual agent progress\n"
            "/tests - Run test suite\n"
            "/team - Team chat summary\n"
            "/plan <text> - Log a plan\n"
            "/decision <text> - Log a decision\n\n"
            "Or just ask me anything about the project."
        )

    # ── WORKSPACE ──
    if any(w in c for w in ['workspace', 'files', 'structure', 'dirs']):
        return (
            f"Workspace: {WORKSPACE.name}\n"
            f"\nDirectories ({len(dirs)}):\n" + ", ".join(dirs) +
            f"\n\nKey Files:\n" + ", ".join(files)
        )

    # ── AGENTS ──
    if any(w in c for w in ['agents', 'team', 'who', 'claude', 'assistant', 'openclaw', 'polymorph']):
        lines = []
        for name, data in agents.items():
            status = data.get('status', '?').replace('**', '').strip()
            # Get last activity
            last_activity = ""
            for line in reversed(data['lines']):
                if '[' in line and ']' in line:
                    last_activity = line.strip()[:100]
                    break
            lines.append(f"{name}: {status}\n  Last: {last_activity}")
        return "Agent Status:\n\n" + "\n\n".join(lines)

    # ── TESTS ──
    if any(w in c for w in ['test', 'tests', 'pytest']):
        test_result = get_test_status()
        return f"Test Results: {test_result}\n\nTest files:\n" + "\n".join(
            [f.name for f in (SRRA_OPC / 'tests').glob('*.py')] if (SRRA_OPC / 'tests').exists() else ["No tests found"]
        )

    # ── TEAM CHAT ──
    if any(w in c for w in ['team chat', 'chat', 'messages']):
        recent_msgs = [l for l in team_text.split('\n') if l.strip() and ('@' in l or '###' in l or '---' in l)][:10]
        return "Recent Team Chat:\n" + "\n".join(recent_msgs)[:1500]

    # ── BUILD / WORK REQUESTS ──
    if any(w in c for w in ['build', 'create', 'make', 'start', 'work', 'do', 'ready', 'code']):
        current_phase = phase.get('current_phase', 'Unknown')
        return (
            f"Ready. Current phase: {current_phase}\n\n"
            f"My pending tasks:\n" +
            "\n".join([l.strip() for l in hermes_text.split('\n') if l.strip().startswith('- [ ]')][:5]) +
            f"\n\nWhat do you want me to work on?"
        )

    # ── PLAN ──
    if any(w in c for w in ['plan', 'idea', 'proposal', 'suggest']):
        text = re.sub(r'^plan[:\s]*', '', c, flags=re.IGNORECASE).strip()
        if len(text) > 3:
            append_progress('PLAN: ' + text)
            return f"Plan logged: {text}"
        return "What's your idea? Send: /plan <your idea>"

    # ── DECISION ──
    if any(w in c for w in ['decision', 'decide', 'choose']):
        text = c
        if ':' in text:
            text = text.split(':', 1)[-1].strip()
        if len(text) > 3:
            append_progress('DECISION: ' + text)
            return f"Decision logged: {text}"
        return "What's the decision? Send: /decision <text>"

    # ── GREETING ──
    if any(w in c for w in ['hi', 'hello', 'hey', 'yo', 'sup', 'yoo']):
        current_phase = phase.get('current_phase', 'Unknown')
        return f"HERMES online. Phase: {current_phase}. What do you need?"

    # ── DEFAULT: Context-aware response ──
    # Read the actual project context to give a meaningful response
    current_phase = phase.get('current_phase', 'Unknown')
    active_agents = len(agents)

    return (
        f"I heard: \"{user_message[:100]}\"\n\n"
        f"Current state: Phase {current_phase}, {active_agents} agents active.\n\n"
        f"I can help with:\n"
        f"/status - Full project status\n"
        f"/agents - Agent-by-agent breakdown\n"
        f"/workspace - File structure\n"
        f"/tests - Test results\n"
        f"/team - Team chat\n"
        f"/plan /decision - Log items\n\n"
        f"Or tell me what to build."
    )


def append_progress(entry):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n- [{timestamp}] **Hermes**: {entry}"
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    return line


# ── Telegram Handlers ──

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phase = get_phase_state()
    current = phase.get('current_phase', 'Unknown')
    await update.message.reply_text(
        f"HERMES - Architect & Planner online.\n"
        f"Current phase: {current}\n"
        f"Use /help for commands or just talk to me."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("help"))


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("status"))


async def workspace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("workspace"))


async def agents_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("agents"))


async def tests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("tests"))


async def team_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(hermes_respond("team chat"))


async def plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args) if context.args else ''
    await update.message.reply_text(hermes_respond(f"plan {text}"))


async def decision_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args) if context.args else ''
    await update.message.reply_text(hermes_respond(f"decision: {text}"))


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.message.text.startswith('/'):
        return

    text = update.message.text.strip()
    logger.info(f"Message from {update.effective_user.username}: {text[:80]}")

    response = hermes_respond(text)
    await update.message.reply_text(response)


def main():
    token = os.getenv("TELEGRAM_HERMES_TOKEN")
    if not token:
        logger.error("TELEGRAM_HERMES_TOKEN not set")
        sys.exit(1)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("workspace", workspace_cmd))
    app.add_handler(CommandHandler("agents", agents_cmd))
    app.add_handler(CommandHandler("tests", tests_cmd))
    app.add_handler(CommandHandler("team", team_cmd))
    app.add_handler(CommandHandler("plan", plan_cmd))
    app.add_handler(CommandHandler("decision", decision_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logger.info("Hermes bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
