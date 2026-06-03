"""Telegram gateway for Primary Observer — OC2-style continuous output.

Sends multiple messages during processing:
1. Acknowledgment + plan
2. Progress updates (scanning, checking, analyzing)
3. Intermediate results
4. Final summary

Matches OC2's multi-message telegram interaction pattern.
"""
import os, sys, time, json, requests, datetime, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator
from core.observer.command_router import CommandRouter
from core.observer.chat_agent import ChatAgent
from core.observer.sovereign_field import SovereignField

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def send(base_url, chat_id, text):
    if not text: return
    while len(text) > 4000:
        idx = text.rfind("\n", 0, 4000)
        if idx == -1: idx = 4000
        try: requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": text[:idx]}, timeout=15)
        except: pass
        text = text[idx:]
    if text:
        try: requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
        except: pass

def typing(base_url, chat_id):
    try: requests.post(f"{base_url}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except: pass

def do_workspace_scan(base_url, chat_id, query):
    """Send progress updates while scanning workspace."""
    send(base_url, cid, "🔍 *Scanning workspace...*")
    time.sleep(0.5)

    # Scan team-chat for recent activity
    try:
        tc = os.path.join(os.getcwd(), "shared-conversations", "team-chat.md")
        if os.path.exists(tc):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(tc))
            lines = sum(1 for _ in open(tc, encoding="utf-8", errors="ignore"))
            send(base_url, cid, f"📋 *team-chat.md* — {lines} lines, last updated {mtime.strftime('%H:%M')}")
    except: pass

    # Scan progress files
    try:
        prog_dir = os.path.join(os.getcwd(), "progress")
        if os.path.exists(prog_dir):
            files = sorted(os.listdir(prog_dir), key=lambda f: os.path.getmtime(os.path.join(prog_dir, f)), reverse=True)[:5]
            if files:
                send(base_url, cid, "📁 *Recent progress:*")
                for f in files:
                    fp = os.path.join(prog_dir, f)
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
                    send(base_url, cid, f"  • `{f}` — {mtime.strftime('%H:%M')}")
    except: pass

    # Scan vault
    try:
        v = Vault()
        md_count = sum(1 for _, _, files in os.walk(v.path) for f in files if f.endswith(".md"))
        send(base_url, cid, f"📚 *Vault:* {md_count} notes indexed")
    except: pass

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token: log("ERROR: TELEGRAM_TOKEN not set"); return
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0
    log("Initializing...")
    vault = Vault(); journal = Journal(vault)
    orch = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orch)
    agent = ChatAgent(); sov = SovereignField()
    log(f"Vault: {vault.path}")
    try:
        r = requests.get(f"{base_url}/getMe", timeout=10)
        bi = r.json().get("result", {})
        log(f"Bot connected: @{bi.get('username')} ({bi.get('first_name')})")
    except Exception as e:
        log(f"ERROR: {e}"); return

    while True:
        try:
            r = requests.get(f"{base_url}/getUpdates", params={"offset": offset, "limit": 10, "timeout": 15}, timeout=20)
            data = r.json()
            if not data.get("ok"): time.sleep(5); continue
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption")
                cid = msg.get("chat", {}).get("id")
                if not text or not cid: continue
                log(f"MSG: {text[:80]}")
                try:
                    if text.strip().startswith("/"):
                        cmd = text.strip()
                        send(base_url, cid, f"⚡ `{cmd}`")
                        typing(base_url, cid)
                        resp = router.handle(cmd)
                        send(base_url, cid, resp)
                    else:
                        # Multi-step response like OC2
                        # Step 1: Acknowledge + plan
                        send(base_url, cid, f"🧠 *Processing:* `{text[:60]}`")
                        typing(base_url, cid)

                        # Step 2: Scan workspace (send progress)
                        do_workspace_scan(base_url, cid, text)

                        # Step 3: Get AI response
                        typing(base_url, cid)
                        ctx = sov.get_sovereign_context()
                        resp = agent.chat(text, sovereign_context=ctx)
                        sov.process_message(text, resp)

                        # Step 4: Send final response
                        send(base_url, cid, resp)

                except Exception as e:
                    log(f"ERR: {e}")
                    try: send(base_url, cid, f"❌ *Error:* `{str(e)[:200]}`")
                    except: pass
        except requests.exceptions.Timeout: continue
        except Exception as e:
            log(f"Poll err: {e}"); time.sleep(5)

if __name__ == "__main__":
    main()
