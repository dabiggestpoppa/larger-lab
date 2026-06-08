"""
SIGNAL BOT — Trading Engine -> Telegram Forwarder
===================================================
Watches quant-lab/mt5/live_logs/signals.jsonl for new signals
and forwards them to Telegram via the Hermes bot.

Uses HERMES_TELEGRAM_TOKEN from .env (independent of PO/OC2).
Auto-discovers chat_id on first message if not set.

Shows PnL on exit events. Marks ST SL_HIT as profit-lock.

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

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
SIGNALS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "signals.jsonl"

if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def discover_chat_id(token):
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


def send_telegram(text):
    global CHAT_ID
    if not TOKEN:
        log("ERROR: HERMES_TELEGRAM_TOKEN not set")
        return False
    if not CHAT_ID:
        CHAT_ID = discover_chat_id(TOKEN)
        if not CHAT_ID:
            log("ERROR: No CHAT_ID")
            return False
    try:
        for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "HTML"},
                timeout=15,
            )
            if not r.json().get("ok"):
                log(f"Telegram error: {r.json()}")
                return False
        return True
    except Exception as e:
        log(f"Send error: {e}")
        return False


def format_signal(sig):
    event = sig.get("event", "?")
    symbol = sig.get("symbol", "?").replace(".PRO", "")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    ts = sig.get("time", "?")
    engine = sig.get("engine", "?")
    pnl_pips = sig.get("pnl_pips", None)
    pnl_usd = sig.get("pnl_usd", None)

    if event == "ENTRY":
        emoji = "BUY" if direction == "BUY" else "SELL"
        label = f"ENTRY {direction}"
    elif event == "TP_HIT":
        emoji = "TP"
        label = "TAKE PROFIT"
    elif event == "SL_HIT":
        emoji = "SL"
        label = "STOP HIT"
    elif event == "KILL_SWITCH":
        emoji = "KS"
        label = "KILL SWITCH"
    else:
        emoji = "SIG"
        label = event

    def calc_pips(a, b, sym):
        pip = 0.01 if "JPY" in sym else 0.0001
        return round(abs(a - b) / pip, 1) if pip else 0

    sl_pips = calc_pips(entry, sl, symbol) if sl else 0
    tp_pips = calc_pips(entry, tp, symbol) if tp else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0

    # ST engine: SL is profit-lock (SL_HIT = profit taken at impulse extreme)
    is_profit_lock = engine == "SymmetryTrap" and event == "SL_HIT"

    lines = [
        f"<b>{label}</b> — {symbol}",
        f"",
        f"Engine: {engine}",
        f"Direction: <b>{direction}</b>",
        f"Entry: {entry}",
        f"SL: {sl} ({sl_pips}p){' [PROFIT-LOCK]' if is_profit_lock else ''}",
        f"TP: {tp} ({tp_pips}p)",
        f"RR: {rr}",
    ]

    if event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
        if pnl_pips is not None:
            sign = "+" if pnl_pips >= 0 else ""
            lines.append(f"PnL: {sign}{pnl_pips}p")
        if pnl_usd is not None:
            sign = "+" if pnl_usd >= 0 else ""
            lines.append(f"PnL: {sign}${pnl_usd:.2f}")
        if is_profit_lock and pnl_pips is not None and pnl_pips > 0:
            lines.append(f"Profit lock triggered")

    lines.append(f"")
    lines.append(f"{ts}")

    if event == "ENTRY":
        loop = sig.get("loop", "?")
        lines.insert(3, f"Loop: {loop}")

    return "\n".join(lines)


def tail_signals(filepath, last_pos=0):
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
    if not SIGNALS_FILE.exists():
        log(f"Signals file not found: {SIGNALS_FILE}")
        return False
    with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines:
        log("No signals in file")
        return False
    try:
        sig = json.loads(lines[-1])
    except json.JSONDecodeError:
        log("Could not parse last signal")
        return False
    msg = format_signal(sig)
    log(f"Sending latest signal: {sig.get('event')} {sig.get('symbol')}")
    return send_telegram(msg)


def run_daemon():
    log("=" * 50)
    log("SIGNAL BOT — Trading Engine -> Telegram")
    log(f"Token: {TOKEN[:10]}...{TOKEN[-5:]}")
    log(f"Signals file: {SIGNALS_FILE}")
    log("=" * 50)

    if not TOKEN:
        log("FATAL: HERMES_TELEGRAM_TOKEN not set")
        sys.exit(1)

    last_pos = 0
    last_signal_key = None

    if SIGNALS_FILE.exists():
        with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            last_pos = f.tell()
        log(f"Starting at position {last_pos} (skipping existing signals)")

    send_telegram(
        "Signal Bot Started\n\n"
        f"Watching: {SIGNALS_FILE.name}\n"
        f"Engine: SymmetryTrap\n\n"
        "New signals will appear here in real-time."
    )

    log("Watching for new signals...")
    try:
        while True:
            if not SIGNALS_FILE.exists():
                time.sleep(5)
                continue

            last_pos, signals = tail_signals(SIGNALS_FILE, last_pos)

            for sig in signals:
                sig_key = (sig.get("symbol"), sig.get("event"), sig.get("time"))
                if sig_key == last_signal_key:
                    continue
                last_signal_key = sig_key

                msg = format_signal(sig)
                event = sig.get("event", "?")
                symbol = sig.get("symbol", "?")
                log(f"Signal: {event} {symbol}")
                send_telegram(msg)

            time.sleep(5)

    except KeyboardInterrupt:
        log("Stopped.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--test" in args:
        log("Sending test message...")
        ok = send_telegram(
            "Signal Bot Test\n\n"
            "Signal forwarder is working!"
        )
        log(f"Test: {'OK' if ok else 'FAILED'}")
    elif "--once" in args:
        run_once()
    else:
        run_daemon()
