"""
DISCORD SIGNAL BOT — Symmetry Trap Signal Forwarder
====================================================
Watches signal files and forwards to Discord via webhook.
Also sends to Telegram (dual broadcast).

Usage:
    python scripts/discord_signal_bot.py              # run continuously
    python scripts/discord_signal_bot.py --once       # send latest and exit
    python scripts/discord_signal_bot.py --test       # send test message

Environment variables (in .env):
    DISCORD_WEBHOOK_URL — Discord webhook URL for the channel
    HERMES_TELEGRAM_TOKEN — Telegram bot token
    HERMES_TELEGRAM_CHAT_ID — Telegram chat ID
"""
import os, sys, json, time, requests
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

# Load .env
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
TG_TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")

SIGNALS_FILES = [
    REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "signals.jsonl",
    REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "occ_buffer_signals.jsonl",
]

# Track last processed position per file
file_positions = {}


def send_discord(message: str):
    """Send message to Discord via webhook."""
    if not DISCORD_WEBHOOK:
        print("[DISCORD] No webhook URL set, skipping")
        return False
    try:
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[DISCORD] Error: {e}")
        return False


def send_telegram(message: str):
    """Send message to Telegram."""
    if not TG_TOKEN or not TG_CHAT:
        print("[TG] No token/chat_id set, skipping")
        return False
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": TG_CHAT, "text": message, "parse_mode": "HTML"}, timeout=10)
        return resp.ok
    except Exception as e:
        print(f"[TG] Error: {e}")
        return False


def format_signal(sig: dict) -> str:
    """Format a signal dict into a readable message."""
    sig_type = sig.get("type", "UNKNOWN")
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    tier = sig.get("tier", "?")
    sl_type = sig.get("sl_type", "OCC+BUFFER")
    timestamp = sig.get("time", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if sig_type == "ENTRY":
        emoji = "🟢" if direction == "LONG" else "🔴"
        return (
            f"{emoji} **{sig_type}** — {symbol}\n"
            f"Direction: **{direction}** | Tier: **{tier}**\n"
            f"Entry: `{entry:.1f}` | SL: `{sl:.1f}` | TP: `{tp:.1f}`\n"
            f"SL Type: {sl_type}\n"
            f"Time: {timestamp}"
        )
    elif sig_type in ("TP_HIT", "SL_HIT"):
        emoji = "✅" if sig_type == "TP_HIT" else "❌"
        pnl = sig.get("pnl_pips", 0)
        return (
            f"{emoji} **{sig_type}** — {symbol} {direction}\n"
            f"PnL: {pnl:+.1f} pips\n"
            f"Time: {timestamp}"
        )
    elif sig_type == "KILL_SWITCH":
        return f"⚠️ **KILL SWITCH** — {symbol} {direction}\nTime: {timestamp}"
    else:
        return f"📡 **{sig_type}** — {symbol}\n{json.dumps(sig, indent=2)[:500]}"


def scan_files():
    """Scan signal files for new entries."""
    new_signals = []
    for fpath in SIGNALS_FILES:
        if not fpath.exists():
            continue
        fkey = str(fpath)
        last_pos = file_positions.get(fkey, 0)

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                f.seek(last_pos)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        sig = json.loads(line)
                        new_signals.append(sig)
                    except json.JSONDecodeError:
                        pass
                file_positions[fkey] = f.tell()
        except Exception as e:
            print(f"[SCANNER] Error reading {fpath}: {e}")

    return new_signals


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Send latest signal and exit")
    parser.add_argument("--test", action="store_true", help="Send test message and exit")
    args = parser.parse_args()

    print("=" * 60)
    print("  DISCORD SIGNAL BOT — Symmetry Trap")
    print("=" * 60)
    print(f"  Discord webhook: {'SET' if DISCORD_WEBHOOK else 'NOT SET'}")
    print(f"  Telegram: {'SET' if TG_TOKEN and TG_CHAT else 'NOT SET'}")
    print(f"  Signal files: {[str(f.name) for f in SIGNALS_FILES]}")
    print("=" * 60)

    if args.test:
        msg = "🟢 **TEST SIGNAL** — Bot is online and ready!\nTime: " + datetime.now().strftime("%H:%M:%S")
        send_discord(msg)
        send_telegram(msg)
        print("Test message sent.")
        return

    if args.once:
        signals = scan_files()
        if signals:
            for sig in signals[-5:]:  # last 5 signals
                msg = format_signal(sig)
                send_discord(msg)
                send_telegram(msg)
                print(f"Sent: {sig.get('type', '?')} {sig.get('symbol', '?')}")
        else:
            print("No new signals found.")
        return

    # Continuous mode
    print("\n[SCANNER] Watching for new signals... (Ctrl+C to stop)")
    while True:
        try:
            signals = scan_files()
            for sig in signals:
                msg = format_signal(sig)
                send_discord(msg)
                send_telegram(msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {sig.get('type', '?')} {sig.get('symbol', '?')} {sig.get('direction', '?')}")

            time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n[SCANNER] Stopped.")
            break
        except Exception as e:
            print(f"[SCANNER] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
