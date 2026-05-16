"""
OC2 Context Monitor — Watches session context usage and alerts via Telegram
=========================================================================
Run as a background process or called by the OC2 watchdog.

Usage:
  python tools/oc2-context-monitor.py          # One-shot check
  python tools/oc2-context-monitor.py --watch  # Continuous monitoring (60s interval)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────────────────────────────────
SESSIONS_FILE = Path(__file__).parent.parent / ".openclaw-2" / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"
TELEGRAM_TOKEN = "8945439460:AAHZT2Xx0jHaApejRJYi-xORG5FkKNAQ5yM"
TELEGRAM_CHAT_ID = 8258195396  # FBO_MAD
LOG_FILE = Path(__file__).parent.parent / "logs" / "oc2-context-monitor.log"
CHECK_INTERVAL = 120  # seconds in watch mode

# Model context limits (tokens)
MODEL_LIMITS = {
    "openrouter/owl-alpha": 1_000_000,
    "openrouter/anthropic/claude-sonnet-4": 200_000,
    "deepseek/deepseek-v4-flash:free": 128_000,
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": 128_000,
    "poolside/laguna-m.1:free": 32_000,
}

WARNING_THRESHOLD = 0.75
CRITICAL_THRESHOLD = 0.90
AUTO_COMPACT_THRESHOLD = 0.95

# ─── Helpers ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("ok"):
                log(f"Telegram alert sent: {text[:80]}...")
                return True
            else:
                log(f"Telegram API error: {data}")
                return False
    except Exception as e:
        log(f"Telegram send failed: {e}")
        return False

def get_model_limit(model_id: str) -> int:
    # Try exact match first
    if model_id in MODEL_LIMITS:
        return MODEL_LIMITS[model_id]
    # Try partial match
    for key, limit in MODEL_LIMITS.items():
        if key in model_id or model_id in key:
            return limit
    # Default to 1M for unknown models
    return 1_000_000

# ─── Main Logic ───────────────────────────────────────────────────────────────
def check_sessions():
    if not SESSIONS_FILE.exists():
        log(f"Sessions file not found: {SESSIONS_FILE}")
        return

    try:
        with open(SESSIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log(f"Failed to read sessions: {e}")
        return

    alerts_sent = 0

    for session_key, session in data.items():
        if not isinstance(session, dict):
            continue

        # Only check active telegram sessions
        if "telegram" not in session_key.lower():
            continue

        status = session.get("status", "")
        if status in ("done", "idle", "aborted"):
            continue

        context_tokens = session.get("contextTokens", 0)
        model = session.get("model", "unknown")
        max_tokens = get_model_limit(model)

        if max_tokens == 0:
            continue

        pct = context_tokens / max_tokens
        pct_display = round(pct * 100, 1)

        log(f"Session {session_key[-12:]}: {context_tokens:,}/{max_tokens:,} ({pct_display}%) — {status}")

        if pct >= AUTO_COMPACT_THRESHOLD:
            msg = (
                f"🚨 <b>CONTEXT CRITICAL — Auto-compaction needed!</b>\n\n"
                f"Session: <code>{session_key}</code>\n"
                f"Model: <code>{model}</code>\n"
                f"Usage: <b>{context_tokens:,} / {max_tokens:,}</b> tokens ({pct_display}%)\n\n"
                f"⚠️ Session is about to be truncated. Start a new session NOW.\n"
                f"Send <code>/new</code> to start fresh."
            )
            send_telegram(msg)
            alerts_sent += 1

        elif pct >= CRITICAL_THRESHOLD:
            msg = (
                f"🚨 <b>Context Critical!</b>\n\n"
                f"Session: <code>{session_key}</code>\n"
                f"Model: <code>{model}</code>\n"
                f"Usage: <b>{context_tokens:,} / {max_tokens:,}</b> tokens ({pct_display}%)\n\n"
                f"⚠️ Start a new session soon to avoid truncation.\n"
                f"Send <code>/new</code> to start fresh."
            )
            send_telegram(msg)
            alerts_sent += 1

        elif pct >= WARNING_THRESHOLD:
            msg = (
                f"⚠️ <b>Context Warning</b>\n\n"
                f"Session: <code>{session_key}</code>\n"
                f"Model: <code>{model}</code>\n"
                f"Usage: <b>{context_tokens:,} / {max_tokens:,}</b> tokens ({pct_display}%)\n\n"
                f"💡 Consider starting a new session soon.\n"
                f"Send <code>/new</code> to start fresh."
            )
            send_telegram(msg)
            alerts_sent += 1

    if alerts_sent == 0:
        log("All sessions within safe context limits")

# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    watch_mode = "--watch" in sys.argv

    if watch_mode:
        log(f"Context monitor started (watch mode, {CHECK_INTERVAL}s interval)")
        log(f"WARNING threshold: {WARNING_THRESHOLD*100}%")
        log(f"CRITICAL threshold: {CRITICAL_THRESHOLD*100}%")
        log(f"AUTO-COMPACT threshold: {AUTO_COMPACT_THRESHOLD*100}%")

        while True:
            try:
                check_sessions()
            except KeyboardInterrupt:
                log("Monitor stopped by user")
                break
            except Exception as e:
                log(f"Monitor error: {e}")
            time.sleep(CHECK_INTERVAL)
    else:
        check_sessions()
