"""Telegram gateway for Primary Observer — matches OC2 output format."""
import os, sys, time, json, requests, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator
from core.observer.command_router import CommandRouter
from core.observer.chat_agent import ChatAgent
from core.observer.sovereign_field import SovereignField

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def send_msg(base_url, chat_id, text):
    if not text:
        return
    chunks = []
    while len(text) > 4000:
        idx = text.rfind("\n", 0, 4000)
        if idx == -1: idx = 4000
        chunks.append(text[:idx])
        text = text[idx:]
    if text: chunks.append(text)
    for chunk in chunks:
        try:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": chunk}, timeout=15)
        except Exception as e:
            log(f"Send error: {e}")

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        log("ERROR: TELEGRAM_TOKEN not set"); return
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0
    log("Initializing components...")
    vault = Vault(); journal = Journal(vault)
    orchestrator = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orchestrator)
    chat_agent = ChatAgent(); sovereign = SovereignField()
    log(f"Vault: {vault.path}")
    log("Components ready. Starting poll loop...")
    try:
        r = requests.get(f"{base_url}/getMe", timeout=10)
        bot_info = r.json().get("result", {})
        log(f"Bot connected: @{bot_info.get('username')} ({bot_info.get('first_name')})")
    except Exception as e:
        log(f"ERROR: Cannot connect: {e}"); return

    while True:
        try:
            r = requests.get(f"{base_url}/getUpdates", params={"offset": offset, "limit": 10, "timeout": 15}, timeout=20)
            data = r.json()
            if not data.get("ok"):
                log(f"API error: {data}"); time.sleep(5); continue
            updates = data.get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption")
                chat_id = msg.get("chat", {}).get("id")
                if not text or not chat_id: continue
                log(f"MSG from {chat_id}: {text[:80]}")
                try:
                    if text.strip().startswith("/"):
                        cmd = text.strip()
                        cmd_name = cmd.split()[0]
                        send_msg(base_url, chat_id, "⚡ " + cmd)
                        resp = router.handle(cmd)
                        send_msg(base_url, chat_id, resp)
                        log(f"CMD {cmd_name} → {len(resp)} chars")
                    else:
                        thinking = requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🧠 Processing..."}, timeout=10)
                        thinking_id = thinking.json()["result"]["message_id"] if thinking.json().get("ok") else None
                        sov_ctx = sovereign.get_sovereign_context()
                        resp = chat_agent.chat(text, sovereign_context=sov_ctx)
                        sovereign.process_message(text, resp)
                        if thinking_id:
                            try: requests.post(f"{base_url}/deleteMessage", json={"chat_id": chat_id, "message_id": thinking_id}, timeout=5)
                            except: pass
                        send_msg(base_url, chat_id, resp)
                        log(f"CHAT RESP ({len(resp)} chars)")
                except Exception as e:
                    log(f"ERROR: {e}")
                    try: send_msg(base_url, chat_id, "❌ Error: " + str(e)[:200])
                    except: pass
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log(f"Poll error: {e}"); time.sleep(5)

if __name__ == "__main__":
    main()
