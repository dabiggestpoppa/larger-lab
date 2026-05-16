"""
Hermes Telegram Bot v3 - Real Agent
Reads workspace state, understands context, responds like a human architect.
"""

import os, re, sys, logging, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s [HERMES] %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy imports for telegram
_application = None
_updater = None

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"
TEAM_CHAT = WORKSPACE / "shared-conversations" / "team-chat.md"
PHASE_STATE = WORKSPACE / ".phase-state.json"
TESTS_DIR = WORKSPACE / "srrs_opc" / "tests"

# Track replied messages to avoid duplicates
_replied = set()


def read_file(path, max_chars=2000):
    try:
        if path.exists():
            return path.read_text(encoding='utf-8')[:max_chars]
    except:
        pass
    return ""


def get_phase():
    try:
        if PHASE_STATE.exists():
            return json.loads(PHASE_STATE.read_text())
    except:
        pass
    return {}


def get_agents():
    agents = {}
    pd = WORKSPACE / "progress"
    if pd.exists():
        for f in pd.glob("*-progress.md"):
            name = f.stem.replace('-progress', '')
            content = f.read_text(encoding='utf-8')
            lines = [l for l in content.split('\n') if l.strip()]
            status = 'unknown'
            recent = []
            for line in lines:
                if 'Status:' in line:
                    status = line.split('Status:', 1)[-1].strip().replace('**', '')
                if '[' in line and ']' in line and ('2026' in line or '2025' in line):
                    recent.append(line.strip()[:120])
            agents[name] = {'status': status, 'recent': recent[-3:]}
    return agents


def get_workspace():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != '.venv'])
    files = sorted([f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')])
    return dirs, files[:15]


def run_tests():
    import subprocess
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'pytest', str(TESTS_DIR), '-q', '--tb=short'],
            capture_output=True, text=True, timeout=60, cwd=str(WORKSPACE)
        )
        out = r.stdout + r.stderr
        passed = re.search(r'(\d+) passed', out)
        failed = re.search(r'(\d+) failed', out)
        p = passed.group(1) if passed else '?'
        f = failed.group(1) if failed else '0'
        return f"{p} passed, {f} failed"
    except Exception as e:
        return f"Error: {e}"


def hermes_think(user_msg):
    """
    Actually think about the message using real workspace context.
    Returns a thoughtful, contextual response.
    """
    c = user_msg.lower().strip()
    phase = get_phase()
    agents = get_agents()
    dirs, files = get_workspace()
    current_phase = phase.get('current_phase', 'Unknown')

    # ── STATUS ──
    if any(w in c for w in ['status', 'progress', 'update', 'how are we', 'whats up', 'what\'s up']):
        agent_lines = "\n".join([f"  {n}: {a['status']}" for n, a in agents.items()]) if agents else "  No agents found"
        recent_progress = read_file(PROGRESS_FILE, 1500)
        recent_lines = [l for l in recent_progress.split('\n') if l.strip() and ('[' in l or l.startswith('-'))][-8:]
        
        return (
            f"Status Report\n"
            f"Phase: {current_phase}\n"
            f"\nAgents:\n{agent_lines}\n"
            f"\nRecent:\n" + "\n".join(recent_lines) +
            f"\n\n{len(dirs)} dirs | {len(files)} key files"
        )

    # ── HELP ──
    if any(w in c for w in ['help', 'commands', 'what can']):
        return (
            "Hermes - Architect & Planner\n\n"
            "/status - Full project status\n"
            "/agents - Agent breakdown\n"
            "/workspace - Project structure\n"
            "/tests - Run test suite\n"
            "/team - Team chat\n"
            "/plan <text> - Log a plan\n"
            "/decision <text> - Log decision\n\n"
            "Or just tell me what you need."
        )

    # ── AGENTS ──
    if any(w in c for w in ['agents', 'team', 'who', 'claude', 'assistant', 'openclaw', 'polymorph', 'as', 'cc', 'oc', 'pm']):
        lines = []
        for name, data in agents.items():
            status = data['status']
            recent = data['recent']
            last = recent[-1] if recent else "No recent activity"
            lines.append(f"{name}: {status}\n  {last}")
        return "Agent Status:\n\n" + "\n\n".join(lines) if lines else "No agent data found."

    # ── WORKSPACE ──
    if any(w in c for w in ['workspace', 'files', 'structure', 'project']):
        return (
            f"Project: {WORKSPACE.name}\n"
            f"\nDirectories ({len(dirs)}):\n" + "\n".join(dirs) +
            f"\n\nKey Files:\n" + "\n".join(files)
        )

    # ── TESTS ──
    if any(w in c for w in ['test', 'tests', 'passing', 'failing']):
        return f"Test Results:\n{run_tests()}"

    # ── TEAM CHAT ──
    if any(w in c for w in ['team chat', 'chat', 'messages', 'conversation']):
        tc = read_file(TEAM_CHAT, 1500)
        msgs = [l for l in tc.split('\n') if l.strip() and ('###' in l or '@' in l or '---' in l)][:15]
        return "Team Chat:\n" + "\n".join(msgs) if msgs else "No recent messages."

    # ── PLAN ──
    if any(w in c for w in ['plan', 'proposal', 'idea', 'suggest', 'we should', 'let\'s', 'lets']):
        if len(c) > 10:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n- [{ts}] Hermes (via Telegram): PLAN: {user_msg}")
            return f"Plan logged: {user_msg[:100]}"
        return "What's your idea? Send: /plan <your idea>"

    # ── DECISION ──
    if any(w in c for w in ['decision', 'decide', 'choose', 'go with', 'pick']):
        if len(c) > 10:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n- [{ts}] Hermes (via Telegram): DECISION: {user_msg}")
            return f"Decision logged: {user_msg[:100]}"
        return "What's the decision? Send: /decision <text>"

    # ── BUILD / WORK ──
    if any(w in c for w in ['build', 'create', 'make', 'start', 'work', 'do', 'ready', 'code', 'develop']):
        return (
            f"Ready. Phase: {current_phase}\n\n"
            f"What should I work on? Give me a specific task and I'll architect it.\n"
            f"Current agents: {', '.join(agents.keys()) if agents else 'none active'}"
        )

    # ── GREETING ──
    if any(w in c for w in ['hi', 'hello', 'hey', 'yo', 'sup', 'yoo']):
        return f"Hermes online. Phase: {current_phase}. What do you need?"

    # ── THINK ABOUT IT ──
    # For anything else, actually reason about the message
    if 'discord' in c:
        return "Discord bot had permission issues. blrr city token was expired, and the on_message handler wasn't firing reliably. We can revisit — the code is solid, just needs proper Discord portal setup."

    if 'phase' in c:
        return f"Current phase: {current_phase}\nPhase details: {json.dumps(phase, indent=2)[:500]}"

    if 'srr' in c or 'oph' in c or 'srra' in c:
        docs = [f.name for f in (WORKSPACE / "srrs_opc" / "docs").glob("*.md")] if (WORKSPACE / "srrs_opc" / "docs").exists() else []
        return f"SRRA-OPH docs: {', '.join(docs) if docs else 'none found'}\nPhase: {current_phase}"

    # ── DEFAULT ──
    return (
        f"Got: \"{user_msg[:100]}\"\n\n"
        f"I'm tracking phase {current_phase}. "
        f"{len(agents)} agents active. What do you need?\n\n"
        "/status /agents /workspace /tests /team /plan /decision"
    )


# ── Telegram Handlers ──

def handle_update(update, context):
    """Main handler for all updates."""
    if not update.message or not update.message.text:
        return

    msg_id = update.message.message_id
    if msg_id in _replied:
        return
    _replied.add(msg_id)
    if len(_replied) > 5000:
        _replied.clear()

    text = update.message.text.strip()
    user = update.effective_user.username or update.effective_user.first_name or "unknown"
    logger_msg = f"{user}: {text[:80]}"

    # Handle commands
    if text.startswith('/'):
        parts = text.split(' ', 1)
        cmd = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if cmd in ['/start']:
            update.message.reply_text(f"Hermes online. Phase: {get_phase().get('current_phase', '?')}. Use /help.")
        elif cmd in ['/help']:
            update.message.reply_text(hermes_think("help"))
        elif cmd in ['/status']:
            update.message.reply_text(hermes_think("status"))
        elif cmd in ['/workspace']:
            update.message.reply_text(hermes_think("workspace"))
        elif cmd in ['/agents']:
            update.message.reply_text(hermes_think("agents"))
        elif cmd in ['/tests']:
            update.message.reply_text("Running tests...")
            update.message.reply_text(hermes_think("tests"))
        elif cmd in ['/team']:
            update.message.reply_text(hermes_think("team"))
        elif cmd in ['/plan']:
            update.message.reply_text(hermes_think(f"plan {rest}" if rest else "plan"))
        elif cmd in ['/decision']:
            update.message.reply_text(hermes_think(f"decision: {rest}" if rest else "decision"))
        else:
            update.message.reply_text(f"Hermes: Unknown command {cmd}. Try /help.")
    else:
        response = hermes_think(text)
        update.message.reply_text(response)


def main():
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    token = os.getenv("TELEGRAM_HERMES_TOKEN")
    if not token:
        logger.error("TELEGRAM_HERMES_TOKEN not set")
        sys.exit(1)

    logger.info("Starting Hermes bot v3...")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("help", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("status", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("workspace", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("agents", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("tests", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("team", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("plan", lambda u, c: handle_update(u, c)))
    app.add_handler(CommandHandler("decision", lambda u, c: handle_update(u, c)))

    # Catch-all for text messages (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update), group=1)

    logger.info("Hermes v3 running.")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message"])


if __name__ == "__main__":
    main()
