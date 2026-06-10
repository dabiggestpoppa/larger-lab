"""
OCC Buffer Telegram Forwarder
==============================
Watches occ_buffer_signals.jsonl for new signals and forwards to Telegram via OpenClaw CLI.

Usage:
    python occ_buffer_telegram.py
"""
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

LOG_DIR = Path(__file__).resolve().parent / "live_logs"
SIGNAL_FILE = LOG_DIR / "occ_buffer_signals.jsonl"
TELEGRAM_CHAT_ID = "8258195396"

def send_telegram(message: str):
    """Send message via OpenClaw CLI."""
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--to", TELEGRAM_CHAT_ID, "--message", message],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram sent OK")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram send FAILED: {result.stderr.strip()}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram send ERROR: {e}")

def format_signal_message(sig: dict) -> str:
    """Format signal dict as Telegram message."""
    event = sig.get("event", "UNKNOWN")
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    sl_pips = sig.get("sl_pips", 0)
    tp_pips = sig.get("tp_pips", 0)
    rr = sig.get("rr", 0)
    loop = sig.get("loop", 1)
    buf_type = sig.get("buffer_type", "")

    if event == "ENTRY":
        return (
            f"🔔 OCC BUFFER SIGNAL\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 {symbol} {direction}\n"
            f"📍 Entry: {entry}\n"
            f"🛑 SL: {sl} ({sl_pips}p)\n"
            f"🎯 TP: {tp} ({tp_pips}p)\n"
            f"📈 RR: {rr}\n"
            f"🔄 Loop: {loop}\n"
            f"⏰ {sig.get('time', '')}"
        )
    elif event == "TP_HIT":
        return (
            f"✅ TP HIT — {symbol} {direction}\n"
            f"📍 Entry: {entry} | RR: {rr}\n"
            f"⏰ {sig.get('time', '')}"
        )
    elif event == "SL_HIT":
        return (
            f"🛑 SL HIT — {symbol} {direction}\n"
            f"📍 Entry: {entry} | SL: {sl} ({sl_pips}p)\n"
            f"⏰ {sig.get('time', '')}"
        )
    else:
        return f"📡 {event} — {symbol} {direction} @ {entry}"

def main():
    print(f"OCC Buffer Telegram Forwarder")
    print(f"Watching: {SIGNAL_FILE}")
    print(f"Target: Telegram {TELEGRAM_CHAT_ID}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Wait for signal file to exist
    if not SIGNAL_FILE.exists():
        print(f"Signal file doesn't exist yet — waiting...")
        while not SIGNAL_FILE.exists():
            time.sleep(2)
        print(f"Signal file appeared — starting tail...")

    # Tail the file for new lines
    last_size = SIGNAL_FILE.stat().st_size if SIGNAL_FILE.exists() else 0

    while True:
        try:
            if not SIGNAL_FILE.exists():
                time.sleep(2)
                continue

            current_size = SIGNAL_FILE.stat().st_size
            if current_size > last_size:
                with open(SIGNAL_FILE, "r", encoding="utf-8") as f:
                    f.seek(last_size)
                    new_lines = f.read().strip().splitlines()
                    last_size = current_size

                for line in new_lines:
                    if not line.strip():
                        continue
                    try:
                        sig = json.loads(line)
                        event = sig.get("event", "")
                        if event in ("ENTRY", "TP_HIT", "SL_HIT"):
                            msg = format_signal_message(sig)
                            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New signal: {event} {sig.get('symbol')} {sig.get('direction')}")
                            send_telegram(msg)
                    except json.JSONDecodeError:
                        pass

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
