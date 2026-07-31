"""Minimal Telegram gateway for Primary Observer.

This is a lightweight polling-based gateway intended as a runnable stub
for development and integration with the ObserverConversationRuntime.
"""
import os
import sys
import time
import threading
import logging
import requests
from typing import Callable, Optional, Dict, Any

# Ensure logs directory exists
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(_log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_log_dir, "telegram_gateway.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("telegram.gateway")


class TelegramGateway:
    def __init__(self, token: str, poll_interval: float = 1.5):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.poll_interval = poll_interval
        self._offset: Optional[int] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _get_updates(self, timeout: int = 20):
        params = {"timeout": timeout}
        if self._offset:
            params["offset"] = self._offset
        try:
            r = requests.get(f"{self.api_url}/getUpdates", params=params, timeout=timeout + 5)
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                return []
            return data.get("result", [])
        except Exception:
            return []

    def send_message(self, chat_id: int, text: str) -> Dict[str, Any]:
        try:
            logger.info(f"Sending message to chat {chat_id} ({len(text)} chars)")
            r = requests.post(f"{self.api_url}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
            r.raise_for_status()
            result = r.json()
            if result.get("ok"):
                logger.info(f"Message sent successfully to chat {chat_id}")
            else:
                logger.error(f"Telegram API error: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"ok": False, "error": str(e)}

    def _poll_loop(self, handler: Callable[[Dict[str, Any]], None]):
        self._running = True
        logger.info("Polling loop started")
        while self._running:
            try:
                updates = self._get_updates(timeout=10)
                for u in updates:
                    try:
                        self._offset = u["update_id"] + 1
                    except Exception:
                        pass
                    try:
                        handler(u)
                    except Exception as e:
                        logger.error(f"Handler error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Poll loop error: {e}", exc_info=True)
            time.sleep(self.poll_interval)
        logger.info("Polling loop stopped")

    def start(self, handler: Callable[[Dict[str, Any]], None], background: bool = True):
        if background:
            self._thread = threading.Thread(target=self._poll_loop, args=(handler,), daemon=True)
            self._thread.start()
        else:
            self._poll_loop(handler)

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)


def _extract_message_text(update: Dict[str, Any]) -> Optional[str]:
    if "message" in update:
        msg = update["message"]
        return msg.get("text") or msg.get("caption")
    return None


if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Set TELEGRAM_TOKEN environment variable and re-run")
        raise SystemExit(1)

    from core.observer.observer_conversation_runtime import ObserverConversationRuntime
    from core.observer.command_router import CommandRouter
    from core.observer.vault import Vault
    from core.observer.journal import Journal

    vault = Vault()
    journal = Journal(vault)
    runtime = ObserverConversationRuntime(vault_path=vault.path)
    router = CommandRouter(vault=vault, journal=journal)
    gw = TelegramGateway(token)

    def handler(update):
        text = _extract_message_text(update)
        chat_id = None
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
        if not text or not chat_id:
            return
        if text.strip().startswith('/'):
            resp = router.handle(text.strip(), meta={"source": "telegram", "update": update})
        else:
            resp = runtime.process_message(text, meta={"source": "telegram", "update": update})
            # record the interaction
            journal.record_event({"type": "message", "text": text, "source": "telegram"})
        gw.send_message(chat_id, resp)

    print("Starting Telegram gateway (polling)...")
    gw.start(handler, background=False)
