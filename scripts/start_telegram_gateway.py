"""Robust Telegram gateway runner for Primary Observer.

Model chain (all free):
1. moonshotai/kimi-k2.6:free
2. openrouter/owl-alpha
3. poolside/laguna-m.1:free
"""
import os
import sys
import time
import json
import requests
import datetime

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
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


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        log("ERROR: TELEGRAM_TOKEN not set")
        return

    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0

    # Initialize components
    log("Initializing components...")
    vault = Vault()
    journal = Journal(vault)
    orchestrator = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orchestrator)
    chat_agent = ChatAgent()
    sovereign = SovereignField()
    log(f"Vault: {vault.path}")
    log("Components ready. Starting poll loop...")

    # Test API connection
    try:
        r = requests.get(f"{base_url}/getMe", timeout=10)
        bot_info = r.json().get("result", {})
        log(f"Bot connected: @{bot_info.get('username')} ({bot_info.get('first_name')})")
    except Exception as e:
        log(f"ERROR: Cannot connect to Telegram API: {e}")
        return

    # Poll loop
    while True:
        try:
            r = requests.get(
                f"{base_url}/getUpdates",
                params={"offset": offset, "limit": 10, "timeout": 15},
                timeout=20,
            )
            data = r.json()

            if not data.get("ok"):
                log(f"API error: {data}")
                time.sleep(5)
                continue

            updates = data.get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption")
                chat_id = msg.get("chat", {}).get("id")

                if not text or not chat_id:
                    continue

                log(f"MSG from {chat_id}: {text[:80]}")

                # Send typing indicator
                try:
                    requests.post(f"{base_url}/sendChatAction",
                                  json={"chat_id": chat_id, "action": "typing"}, timeout=5)
                except Exception:
                    pass

                # Process
                try:
                    if text.strip().startswith("/"):
                        # Slash command
                        resp = router.handle(text.strip())
                        log(f"CMD RESP ({len(resp)} chars): {resp[:80]}")
                        requests.post(
                            f"{base_url}/sendMessage",
                            json={"chat_id": chat_id, "text": resp},
                            timeout=15,
                        )
                    else:
                        # Chat message — get response from chat agent
                        sov_ctx = sovereign.get_sovereign_context()
                        resp = chat_agent.chat(text, sovereign_context=sov_ctx)
                        sovereign.process_message(text, resp)
                        log(f"CHAT RESP ({len(resp)} chars): {resp[:80]}")
                        requests.post(
                            f"{base_url}/sendMessage",
                            json={"chat_id": chat_id, "text": resp},
                            timeout=15,
                        )
                except Exception as e:
                    log(f"ERROR processing message: {e}")
                    try:
                        requests.post(
                            f"{base_url}/sendMessage",
                            json={"chat_id": chat_id, "text": f"❌ Error: {str(e)[:200]}"},
                            timeout=10,
                        )
                    except Exception:
                        pass

        except Exception as e:
            log(f"Poll error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
