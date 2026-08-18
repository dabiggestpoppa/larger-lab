#!/usr/bin/env python3
"""
TB Telegram notifier — push alerts for TB basket lifecycle events.

Loads credentials from a small JSON config in the runtime state dir
(quant-lab/state/tb_telegram.json, gitignored):

    {
      "token": "123456789:ABC...",
      "chat_id": 123456789
    }

Fallbacks (for testing): env vars TB_TELEGRAM_TOKEN / TB_TELEGRAM_CHAT_ID.

The notifier is deliberately defensive: it NEVER raises into the watcher
loop. Send failures are logged and counted; a broken Telegram link must
never stop basket monitoring. Sends use a short timeout so a slow network
cannot block the 10s poll.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

log = logging.getLogger("tb.telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
DEFAULT_CONFIG = "tb_telegram.json"
SEND_TIMEOUT_S = 10.0
MAX_RETRIES = 2


def load_config(config_path: Path | None = None) -> dict:
    """Load token/chat_id from config file, then env fallbacks."""
    cfg: dict = {}
    if config_path is None:
        # Resolve relative to the runtime state dir when known.
        try:
            from tb_runtime_config import STATE_DIR
            candidate = STATE_DIR / DEFAULT_CONFIG
        except Exception:
            candidate = None
        candidates = [candidate] if candidate else []
        # Also try a file next to this module (source-of-truth checkout).
        candidates.append(Path(__file__).resolve().parent / DEFAULT_CONFIG)
    else:
        candidates = [config_path]

    for c in candidates:
        if c and c.is_file():
            try:
                data = json.loads(c.read_text(encoding="utf-8"))
                if data.get("token"):
                    cfg.update(data)
                    log.info("creds loaded from %s", c)
                    break
            except Exception as e:
                log.warning("creds file %s unreadable: %s", c, e)

    if not cfg.get("token"):
        tok = os.environ.get("TB_TELEGRAM_TOKEN") or os.environ.get(
            "TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_HERMES_TOKEN")
        if tok:
            cfg["token"] = tok
            log.info("creds loaded from environment")
    if not cfg.get("chat_id"):
        cid = os.environ.get("TB_TELEGRAM_CHAT_ID") or os.environ.get(
            "TELEGRAM_CHAT_ID")
        if cid:
            try:
                cfg["chat_id"] = int(cid)
            except ValueError:
                log.warning("invalid TELEGRAM_CHAT_ID: %r", cid)
    return cfg


class TelegramNotifier:
    def __init__(self, config_path: Path | None = None,
                 chat_id: int | None = None):
        cfg = load_config(config_path)
        self.token: str = str(cfg.get("token") or "").strip()
        self.chat_id: int | None = (
            chat_id if chat_id is not None
            else (int(cfg["chat_id"]) if cfg.get("chat_id") else None))
        self.enabled: bool = bool(self.token and self.chat_id)
        self.failures: int = 0
        self.sent: int = 0
        self.last_error: str | None = None
        if not self.token:
            log.warning("telegram notifier DISABLED: no token (set "
                        "state/tb_telegram.json or env)")
        elif self.chat_id is None:
            log.warning("telegram notifier DISABLED: no chat_id")
        else:
            log.info("telegram notifier armed (chat_id=%s)", self.chat_id)

    def _send(self, text: str) -> bool:
        if not self.enabled:
            return False
        if requests is None:
            self.last_error = "requests not installed"
            log.error("telegram send failed: %s", self.last_error)
            return False
        url = TELEGRAM_API.format(token=self.token)
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.post(
                    url,
                    json={"chat_id": self.chat_id, "text": text,
                          "disable_web_page_preview": True},
                    timeout=SEND_TIMEOUT_S,
                )
                if r.status_code == 200 and r.json().get("ok"):
                    self.sent += 1
                    return True
                last_exc = RuntimeError(f"HTTP {r.status_code}: "
                                        f"{r.text[:200]}")
            except Exception as e:  # network timeouts etc.
                last_exc = e
            if attempt + 1 < MAX_RETRIES:
                time.sleep(1.0)
        self.failures += 1
        self.last_error = str(last_exc)
        log.error("telegram send failed (chat %s): %s",
                  self.chat_id, self.last_error)
        return False

    def notify(self, text: str) -> bool:
        """Send a push; never raises. Returns True if delivered."""
        try:
            return self._send(text)
        except Exception as e:  # absolute last-resort guard
            self.failures += 1
            self.last_error = str(e)
            log.error("telegram notify crashed: %s", e)
            return False


def send_test(config_path: Path | None = None) -> int:
    """CLI: send a test message. Exit 0 on success, 1/2 otherwise."""
    tg = TelegramNotifier(config_path)
    if not tg.enabled:
        print("notifier not armed (no token/chat_id)")
        return 2
    ok = tg.notify(
        "✅ TB basket watcher telegram armed.\n"
        "You will be notified on basket SIGNAL / OPEN / CLOSE.")
    print(f"test message delivered={ok} sent={tg.sent} failures={tg.failures}")
    return 0 if ok else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(send_test())
