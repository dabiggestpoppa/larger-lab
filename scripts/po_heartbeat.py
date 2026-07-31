"""
PO Heartbeat Worker — keeps PO alive and aware in the field.
Runs on a loop, checks the workspace, posts updates to Telegram + team chat.

Usage: python scripts/po_heartbeat.py [--interval 300] [--once] [--no-telegram]
"""
import subprocess, sys, time, json, hashlib, os, socket
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
TEAM_CHAT = REPO_ROOT / "shared-conversations" / "team-chat.md"
MEMORY_FILE = REPO_ROOT / "MEMORY.md"
STATE_FILE = REPO_ROOT / ".po_heartbeat_state.json"
HEARTBEAT_LOG = REPO_ROOT / "heartbeat.md"
DEFAULT_INTERVAL = 300  # 5 minutes


def utcnow_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def run_cmd(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return r.stdout.strip()


def load_env():
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def send_telegram(text):
    import requests
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token:
        return False
    try:
        if not chat_id or chat_id == "0":
            r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5", timeout=10)
            data = r.json()
            if data.get("ok") and data.get("result"):
                chat_id = str(data["result"][0]["message"]["chat"]["id"])
                os.environ["TELEGRAM_CHAT_ID"] = chat_id
            else:
                return False
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=15)
        return True
    except Exception as e:
        print(f"[heartbeat] Telegram error: {e}")
        return False


def git_status():
    return [l for l in run_cmd(["git", "status", "--porcelain"]).splitlines() if l.strip()]


def git_log_last(n=3):
    return run_cmd(["git", "log", f"-{n}", "--oneline"]).splitlines()


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_check": None, "last_status_hash": None, "checks_done": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def check_field():
    state = load_state()
    state["checks_done"] = state.get("checks_done", 0) + 1
    report = [f"**Field Check #{state['checks_done']}** — {utcnow_str()}"]
    actions = []

    # Git status
    status = git_status()
    h = hashlib.md5("".join(status).encode()).hexdigest()
    prev = state.get("last_status_hash")
    if not status:
        report.append("✅ Workspace clean")
    elif h == prev:
        report.append(f"⚠️ {len(status)} files unchanged")
    else:
        report.append(f"🔄 {len(status)} files changed:")
        for l in status[:10]:
            report.append(f"  {l}")
    state["last_status_hash"] = h

    # Recent commits
    commits = git_log_last(3)
    if commits:
        report.append("\n📋 Recent commits:")
        for c in commits:
            report.append(f"  {c}")

    # Memory
    if MEMORY_FILE.exists():
        mtime = datetime.fromtimestamp(MEMORY_FILE.stat().st_mtime)
        report.append(f"\n🧠 Memory: modified {mtime.strftime('%Y-%m-%d %H:%M')}")

    # Services
    report.append("\n🔌 Services:")
    for name, port in [("OCE Backend", 8000), ("OCE Frontend", 3000), ("SRRA-OPH", 3001)]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", port))
            report.append(f"  ✅ {name} :{port}")
        except Exception:
            report.append(f"  ❌ {name} :{port} DOWN")
        finally:
            s.close()

    state["last_check"] = utcnow_str()
    save_state(state)

    full = "\n".join(report)
    if actions:
        full += "\n\n**Actions:** " + "; ".join(actions)
    return full, len(status) == 0


def run_once(telegram=True):
    print(f"[heartbeat] Check at {utcnow_str()}")
    load_env()
    report, clean = check_field()
    # Team chat
    ts = utcnow_str()
    entry = f"\n---\n\n### [PO] {ts}\n{report}\n"
    if TEAM_CHAT.exists():
        TEAM_CHAT.write_text(TEAM_CHAT.read_text(encoding="utf-8", errors="replace") + entry, encoding="utf-8")
    # Telegram short summary
    if telegram:
        short = f"🔄 *PO Heartbeat* — {ts}\n\n{report[:800]}"
        send_telegram(short)
    # Local log
    if HEARTBEAT_LOG.exists():
        HEARTBEAT_LOG.write_text(HEARTBEAT_LOG.read_text(encoding="utf-8") + f"\n## {ts}\n{report}\n", encoding="utf-8")
    else:
        HEARTBEAT_LOG.write_text(f"# PO Heartbeat Log\n\n## {ts}\n{report}\n", encoding="utf-8")
    print(f"[heartbeat] Done. Clean: {clean}")
    return clean


def run_loop(interval=DEFAULT_INTERVAL, telegram=True):
    print(f"[heartbeat] Starting — interval {interval}s")
    load_env()
    if telegram:
        send_telegram(f"🟢 *PO Heartbeat started*\n\nI'm in the field. Checking every {interval//60} minutes.\n\nI'll report changes, check services, and keep the field running.")
    try:
        while True:
            run_once(telegram=telegram)
            print(f"[heartbeat] Sleeping {interval}s...")
            time.sleep(interval)
    except KeyboardInterrupt:
        if telegram:
            send_telegram("🔴 PO Heartbeat stopped")
        print("[heartbeat] Stopped.")


if __name__ == "__main__":
    args = sys.argv[1:]
    interval = DEFAULT_INTERVAL
    telegram = "--no-telegram" not in args
    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])
    if "--once" in args:
        run_once(telegram=telegram)
    else:
        run_loop(interval=interval, telegram=telegram)
