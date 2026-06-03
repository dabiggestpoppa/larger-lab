"""Telegram gateway for Primary Observer — OC2-style output with work display.

Shows intermediate steps (scanning, checking files) before final response.
Matches OC2's telegram interaction pattern.
"""
import os, sys, time, json, requests, datetime
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
                        # OC2-style: show command being executed
                        send(base_url, cid, f"⚡ `{cmd}`")
                        typing(base_url, cid)
                        resp = router.handle(cmd)
                        send(base_url, cid, resp)
                    else:
                        # OC2-style: show thinking, then scan work, then response
                        send(base_url, cid, "🧠 *Thinking...*")
                        typing(base_url, cid)
                        # Do vault scan first and show it
                        ctx = sov.get_sovereign_context()
                        resp = agent.chat(text, sovereign_context=ctx)
                        sov.process_message(text, resp)
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
