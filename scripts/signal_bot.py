"""
SIGNAL BOT — Trading Engine → Telegram Forwarder
================================================
Watches quant-lab/mt5/live_logs/signals.jsonl for new signals
and forwards them to Telegram via the Hermes bot.

Uses HERMES_TELEGRAM_TOKEN from .env (independent of PO/OC2).
Auto-discovers chat_id on first message if not set.

Usage:
    python scripts/signal_bot.py              # run continuously
    python scripts/signal_bot.py --once       # send latest signal and exit
    python scripts/signal_bot.py --test       # send test message and exit
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
SIGNALS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "signals.jsonl"
PID_FILE = REPO_ROOT / ".signal_bot.pid"

# ── Load .env ──────────────────────────────────────────────────────
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Config ─────────────────────────────────────────────────────────
TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")
POLL_INTERVAL = 5  # seconds between file checks


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def discover_chat_id(token: str) -> str:
    """Auto-discover chat_id from recent bot messages."""
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5",
            timeout=10,
        )
        data = r.json()
        if data.get("ok") and data.get("result"):
            cid = str(data["result"][0]["message"]["chat"]["id"])
            log(f"Auto-discovered chat_id: {cid}")
            return cid
    except Exception as e:
        log(f"getUpdates error: {e}")
    return ""


def send_telegram(text: str) -> bool:
    """Send a message to Telegram. Auto-discovers chat_id if needed."""
    global CHAT_ID
    if not TOKEN:
        log("ERROR: HERMES_TELEGRAM_TOKEN not set")
        return False

    if not CHAT_ID:
        CHAT_ID = discover_chat_id(TOKEN)
        if not CHAT_ID:
            log("ERROR: No CHAT_ID — message the bot first to register")
            return False

    # Telegram limit = 4096 chars
    chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "HTML"},
                timeout=15,
            )
            if not r.json().get("ok"):
                log(f"Telegram API error: {r.json()}")
                return False
        except Exception as e:
            log(f"Send error: {e}")
            return False
    return True


def format_signal(sig: dict) -> str:
    """Format a signal dict into a readable Telegram message."""
    event = sig.get("event", "?")
    symbol = sig.get("symbol", "?").replace(".PRO", "")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    ts = sig.get("time", "?")
    engine = sig.get("engine", "?")

    # Emoji by event
    if event == "ENTRY":
        emoji = "🟢" if direction == "BUY" else "🔴"
        label = f"ENTRY {direction}"
    elif event == "TP_HIT":
        emoji = "✅"
        label = "TAKE PROFIT"
    elif event == "SL_HIT":
        emoji = "🛑"
        label = "STOP HIT"
    elif event == "KILL_SWITCH":
        emoji = "⛔"
        label = "KILL SWITCH"
    else:
        emoji = "📊"
        label = event

    # Calculate pips
    def calc_pips(a, b, sym):
        pip = 0.01 if "JPY" in sym else 0.0001
        return round(abs(a - b) / pip, 1) if pip else 0

    sl_pips = calc_pips(entry, sl, symbol) if sl else 0
    tp_pips = calc_pips(entry, tp, symbol) if tp else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0

    lines = [
        f"{emoji} <b>{label}</b> — {symbol}",
        f"",
        f"Engine: {engine}",
        f"Direction: <b>{direction}</b>",
        f"Entry: {entry}",
        f"SL: {sl} ({sl_pips}p)",
        f"TP: {tp} ({tp_pips}p)",
        f"RR: {rr}",
        f"",
        f"⏰ {ts}",
    ]

    if event == "ENTRY":
        loop = sig.get("loop", "?")
        lines.insert(3, f"Loop: {loop}")

    return "\n".join(lines)


def tail_signals(filepath: Path, last_pos: int = 0):
    """Generator that yields new JSON lines from a file, tracking position."""
    if not filepath.exists():
        return last_pos, []

    with open(filepath, "r", encoding="utf-8") as f:
        f.seek(last_pos)
        lines = f.readlines()
        new_pos = f.tell()

    signals = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return new_pos, signals


def run_once():
    """Read the latest signal and send it."""
    if not SIGNALS_FILE.exists():
        log(f"Signals file not found: {SIGNALS_FILE}")
        return False

    with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if not lines:
        log("No signals in file")
        return False

    # Send the last signal
    try:
        sig = json.loads(lines[-1])
    except json.JSONDecodeError:
        log("Could not parse last signal")
        return False

    msg = format_signal(sig)
    log(f"Sending latest signal: {sig.get('event')} {sig.get('symbol')}")
    return send_telegram(msg)


def run_daemon():
    """Continuously watch signals.jsonl and forward new signals to Telegram."""
    log("=" * 50)
    log("SIGNAL BOT — Trading Engine → Telegram")
    log(f"Token: {TOKEN[:10]}...{TOKEN[-5:]}" if len(TOKEN) > 15 else "NOT SET")
    log(f"Signals file: {SIGNALS_FILE}")
    log(f"Poll interval: {POLL_INTERVAL}s")
    log("=" * 50)

    if not TOKEN:
        log("FATAL: HERMES_TELEGRAM_TOKEN not set in .env")
        sys.exit(1)

    if not SIGNALS_FILE.exists():
        log(f"Signals file not found — waiting for it to appear...")

    last_pos = 0
    last_signal_key = None  # dedup: (symbol, event, time)

    # If file already exists, seek to end (don't flood with old signals)
    if SIGNALS_FILE.exists():
        with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2)  # seek to end
            last_pos = f.tell()
        log(f"Starting at position {last_pos} (skipping existing signals)")

    # Send startup notification
    send_telegram(
        "📡 <b>Signal Bot Started</b>\n\n"
        f"Watching: {SIGNALS_FILE.name}\n"
        f"Engine: SymmetryTrap\n"
        f"Symbols: EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, GBPCAD\n\n"
        "New signals will appear here in real-time."
    )

    log("Watching for new signals...")
    try:
        while True:
            if not SIGNALS_FILE.exists():
                time.sleep(POLL_INTERVAL)
                continue

            last_pos, signals = tail_signals(SIGNALS_FILE, last_pos)

            for sig in signals:
                # Dedup key
                sig_key = (sig.get("symbol"), sig.get("event"), sig.get("time"))
                if sig_key == last_signal_key:
                    continue
                last_signal_key = sig_key

                msg = format_signal(sig)
                event = sig.get("event", "?")
                symbol = sig.get("symbol", "?")
                log(f"Signal: {event} {symbol}")
                send_telegram(msg)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log("Stopped.")
        send_telegram("🔴 Signal Bot stopped.")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--test" in args:
        log("Sending test message...")
        ok = send_telegram(
            "🧪 <b>Signal Bot Test</b>\n\n"
            "This is a test from the signal forwarder.\n"
            "If you see this, the bot is working!"
        )
        log(f"Test: {'OK' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)

    if "--once" in args:
        ok = run_once()
        sys.exit(0 if ok else 1)

    run_daemon()
