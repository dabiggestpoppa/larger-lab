"""
DISCORD SIGNAL BOT — CEREBUS Scanner Forwarder
==============================================
Watches scanner alert files and forwards to Discord.
Sends at regime check times: 3AM, 6AM, 9AM, 12PM EST.

Usage:
    python scripts/discord_signal_bot.py              # run continuously
    python scripts/discord_signal_bot.py --once       # send latest and exit
    python scripts/discord_signal_bot.py --test       # send test message
"""
import os, sys, json, time, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / ".env"

# Load .env
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

SIGNALS_FILES = [
    REPO_ROOT / "data" / "alerts_history.json",
]

LATEST_ALERT_FILE = REPO_ROOT / "data" / "latest_alert.txt"

# Track last processed count per file
file_positions = {}

EST = timezone(timedelta(hours=-5))

# Regime check times (EST): 3AM, 6AM, 9AM, 12PM
CHECK_HOURS = [3, 6, 9, 12]


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


def format_alert(alert: dict) -> str:
    """Format a CEREBUS alert dict into a Discord message."""
    symbol = alert.get("symbol", "?")
    direction = alert.get("direction", "?")
    confidence = alert.get("confidence", 0)
    pathway = alert.get("pathway", "?")
    regime = alert.get("regime", "?")
    regime_ratio = alert.get("regime_ratio", 0)
    asian_range = alert.get("asian_range_pips", 0)
    timestamp = alert.get("timestamp", datetime.now(EST).strftime("%Y-%m-%d %H:%M"))

    emoji = "🟢" if direction == "LONG" else "🔴" if direction == "SHORT" else "📡"

    return (
        f"{emoji} **CEREBUS SCAN** — {symbol}\n"
        f"Direction: **{direction}** | Confidence: **{confidence:.0%}**\n"
        f"Pathway: {pathway} | Regime: {regime} ({regime_ratio:.2f}x)\n"
        f"Asian Range: {asian_range:.1f} pips\n"
        f"Time: {timestamp} EST"
    )


def scan_files():
    """Scan signal files for new entries."""
    new_signals = []
    for fpath in SIGNALS_FILES:
        if not fpath.exists():
            continue
        fkey = str(fpath)
        last_count = file_positions.get(fkey, 0)

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                data = json.loads(content)
                if isinstance(data, list):
                    new_entries = data[last_count:]
                    for entry in new_entries:
                        if isinstance(entry, dict):
                            new_signals.append(entry)
                    file_positions[fkey] = len(data)
        except Exception as e:
            print(f"[SCANNER] Error reading {fpath}: {e}")
    return new_signals


def should_send_now():
    """Check if current EST time is a regime check time."""
    now_est = datetime.now(EST)
    return now_est.hour in CHECK_HOURS


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Send latest and exit")
    parser.add_argument("--test", action="store_true", help="Send test and exit")
    args = parser.parse_args()

    print("=" * 60)
    print("  DISCORD SIGNAL BOT — CEREBUS Scanner")
    print("=" * 60)
    print(f"  Discord webhook: {'SET' if DISCORD_WEBHOOK else 'NOT SET'}")
    print(f"  Check times: 3AM, 6AM, 9AM, 12PM EST")
    print("=" * 60)

    if args.test:
        msg = "🟢 **CEREBUS BOT TEST** — Online!\nTime: " + datetime.now(EST).strftime("%H:%M:%S EST")
        send_discord(msg)
        print("Test sent to Discord.")
        return

    if args.once:
        signals = scan_files()
        for sig in signals[-5:]:
            send_discord(format_alert(sig))
        print(f"Sent {len(signals[-5:])} signals.")
        return

    print("\n[BOT] Watching... sends at 3AM, 6AM, 9AM, 12PM EST")
    last_sent_hour = -1

    while True:
        try:
            now_est = datetime.now(EST)
            current_hour = now_est.hour

            if should_send_now() and current_hour != last_sent_hour:
                signals = scan_files()
                if signals:
                    for sig in signals:
                        send_discord(format_alert(sig))
                        print(f"[{now_est.strftime('%H:%M')}] {sig.get('symbol')} {sig.get('direction')} {sig.get('confidence', 0):.0%}")
                last_sent_hour = current_hour
            elif current_hour not in CHECK_HOURS:
                last_sent_hour = -1

            time.sleep(60)

        except KeyboardInterrupt:
            print("\n[BOT] Stopped.")
            break
        except Exception as e:
            print(f"[BOT] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
