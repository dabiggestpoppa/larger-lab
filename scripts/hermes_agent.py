"""
HERMES — Raw Agent (OCE-Backed)
================================
Standalone agent that connects to the OCE backend (port 8000).
No Telegram, no OpenClaw — just a raw agent loop with tool-calling,
memory, and workspace access via OCE's API.

Usage:
    python scripts/hermes_agent.py                  # interactive REPL
    python scripts/hermes_agent.py --loop           # autonomous loop
    python scripts/hermes_agent.py --once "task"   # single task, then exit
"""
import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
OCE_CHAT_URL = "http://localhost:8000/api/po/chat"
OCE_HEALTH_URL = "http://localhost:8000/health"

# ── Load .env ──────────────────────────────────────────────────────
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Config ─────────────────────────────────────────────────────────
SESSION_ID = f"hermes-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
MODEL = "po"


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [HERMES] {msg}", flush=True)


def check_oce_health() -> bool:
    try:
        r = requests.get(OCE_HEALTH_URL, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def chat_with_oce(message: str, session_id: str = "") -> str:
    """Send a message to OCE's PO chat endpoint and get the response."""
    sid = session_id or SESSION_ID
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": message}],
        "stream": False,
        "temperature": 0.7,
        "session_id": sid,
    }

    try:
        r = requests.post(OCE_CHAT_URL, json=payload, timeout=120)
        if r.status_code != 200:
            log(f"OCE error: {r.status_code} {r.text[:200]}")
            return ""
        data = r.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""
    except requests.exceptions.Timeout:
        log("OCE request timed out")
        return ""
    except Exception as e:
        log(f"OCE request error: {e}")
        return ""


def get_workspace_context() -> str:
    ctx = []
    try:
        r = subprocess.run(["git", "status", "--porcelain"],
                          capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10)
        ctx.append(f"Git: {len(r.stdout.strip().splitlines())} changed files" if r.stdout.strip() else "Git: clean")
    except Exception:
        pass
    try:
        r = subprocess.run(["git", "log", "-3", "--oneline"],
                          capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10)
        if r.stdout.strip():
            ctx.append("Recent commits:")
            for line in r.stdout.strip().splitlines():
                ctx.append(f"  {line}")
    except Exception:
        pass
    ctx.append("Services:")
    for name, url in [("OCE Backend", "http://localhost:8000/health"),
                       ("SRRA-OPH API", "http://localhost:8001/health"),
                       ("OCE Frontend", "http://localhost:3000")]:
        try:
            r = requests.get(url, timeout=3)
            status = "OK" if r.status_code == 200 else "WARN"
        except Exception:
            status = "DOWN"
        ctx.append(f"  {status} {name}")
    return "\n".join(ctx)


def run_interactive():
    print("=" * 50)
    print("  HERMES — Raw Agent (OCE-Backed)")
    print(f"  Session: {SESSION_ID}")
    print(f"  OCE: {OCE_CHAT_URL}")
    print("=" * 50)
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'context' to see workspace state.\n")

    if not check_oce_health():
        log("WARNING: OCE backend not reachable!")
        return

    while True:
        try:
            msg = input("\n[you] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not msg:
            continue
        if msg.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break
        if msg.lower() == "context":
            print(get_workspace_context())
            continue
        print()
        response = chat_with_oce(msg)
        if response:
            print(f"[hermes] {response}")
        else:
            print("[hermes] (no response)")


def run_once(task: str):
    if not check_oce_health():
        log("OCE backend not reachable!")
        sys.exit(1)
    log(f"Task: {task}")
    response = chat_with_oce(task)
    if response:
        print(f"[hermes] {response}")
    else:
        print("(no response)")
        sys.exit(1)


def run_autonomous():
    log("Starting autonomous loop...")
    if not check_oce_health():
        log("OCE backend not reachable — retrying in 30s")
        time.sleep(30)
        if not check_oce_health():
            log("OCE still down — exiting")
            sys.exit(1)
    ctx = get_workspace_context()
    chat_with_oce(
        f"[SYSTEM] Hermes agent started. Session: {SESSION_ID}\n\n"
        f"Workspace context:\n{ctx}\n\n"
        "I'm online and connected to OCE. Ready for tasks."
    )
    while True:
        try:
            time.sleep(300)
            if not check_oce_health():
                log("OCE unreachable — skipping cycle")
                continue
            ctx = get_workspace_context()
            chat_with_oce(
                f"[SYSTEM] Hermes heartbeat — {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n"
                f"Workspace:\n{ctx}"
            )
        except KeyboardInterrupt:
            log("Stopped.")
            break


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--once" in args:
        idx = args.index("--once")
        run_once(args[idx + 1] if idx + 1 < len(args) else "")
    elif "--loop" in args:
        run_autonomous()
    else:
        run_interactive()
