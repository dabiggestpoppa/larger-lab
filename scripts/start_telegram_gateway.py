"""Runner script to start the Telegram gateway against the observer runtime.

Uses the project venv Python and wires the full CommandRouter + AutonomousOrchestrator.
Token is loaded from .env file or TELEGRAM_TOKEN environment variable.

PowerShell:
    .\.venv\Scripts\python.exe scripts\start_telegram_gateway.py
"""
import os
import sys

# Ensure workspace root is on sys.path so `core` is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file if present
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from core.telegram.telegram_gateway import TelegramGateway
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator
from core.observer.command_router import CommandRouter
from core.observer.observer_conversation_runtime import ObserverConversationRuntime
from core.observer.chat_agent import ChatAgent
from core.observer.sovereign_field import SovereignField


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Please set TELEGRAM_TOKEN environment variable and re-run.")
        return

    vault = Vault()
    journal = Journal(vault)
    orchestrator = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orchestrator)
    runtime = ObserverConversationRuntime(vault=vault)
    chat_agent = ChatAgent()
    sovereign = SovereignField()
    gw = TelegramGateway(token)

    def handler(update):
        msg = update.get("message") or {}
        text = msg.get("text") or msg.get("caption")
        chat_id = msg.get("chat", {}).get("id")
        if not text or not chat_id:
            return
        if text.strip().startswith("/"):
            resp = router.handle(text.strip(), meta={"update": update})
        else:
            # Inject sovereign context into chat
            sov_context = sovereign.get_sovereign_context()
            resp = chat_agent.chat(text, meta={"update": update}, sovereign_context=sov_context)
            sovereign.process_message(text, resp)
            journal.record_event({"type": "chat", "text": text[:200], "source": "telegram"})
        gw.send_message(chat_id, resp)

    print("Starting Telegram gateway (polling)... Press Ctrl-C to stop")
    gw.start(handler, background=False)


if __name__ == "__main__":
    main()
