"""
DISCORD SIGNAL BOT — CEREBUS Scanner Forwarder
==============================================
Watches data/alerts_history.json and forwards new alerts to Discord immediately.
Checks every 10 seconds. Sends as soon as scanner fires.
"""
import os, sys, json, time, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / ".env"

if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
EST = timezone(timedelta(hours=-5))
file_positions = {}


def send_discord(message):
    if not DISCORD_WEBHOOK:
        return False
    try:
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print("[DISCORD] Error: %s" % e)
        return False


def format_alert(alert):
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
        "%s **CEREBUS SCAN** — %s\n"
        "Direction: **%s** | Confidence: **%d%%**\n"
        "Pathway: %s | Regime: %s (%.2fx)\n"
        "Asian Range: %.1f pips\n"
        "Time: %s EST"
    ) % (emoji, symbol, direction, int(confidence * 100), pathway, regime, regime_ratio, asian_range, timestamp)


def scan_files():
    new_signals = []
    alerts_file = REPO_ROOT / "data" / "alerts_history.json"
    if not alerts_file.exists():
        return new_signals
    fkey = str(alerts_file)
    last_count = file_positions.get(fkey, 0)
    try:
        with open(alerts_file, "r", encoding="utf-8") as f:
            data = json.loads(f.read().strip())
            if isinstance(data, list):
                for entry in data[last_count:]:
                    if isinstance(entry, dict):
                        new_signals.append(entry)
                file_positions[fkey] = len(data)
    except Exception as e:
        print("[SCANNER] Error: %s" % e)
    return new_signals


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  DISCORD SIGNAL BOT — CEREBUS Scanner")
    print("  Discord webhook: %s" % ("SET" if DISCORD_WEBHOOK else "NOT SET"))
    print("  Watching: data/alerts_history.json (10s interval)")
    print("=" * 60)

    if args.test:
        msg = "🟢 **CEREBUS BOT TEST** — Online!\nTime: " + datetime.now(EST).strftime("%H:%M:%S EST")
        send_discord(msg)
        print("Test sent.")
        return

    print("\n[BOT] Watching for scanner alerts... (Ctrl+C to stop)\n")
    while True:
        try:
            signals = scan_files()
            for sig in signals:
                if send_discord(format_alert(sig)):
                    print("[%s] %s %s %d%%" % (
                        datetime.now(EST).strftime("%H:%M:%S"),
                        sig.get("symbol"), sig.get("direction"), int(sig.get("confidence", 0) * 100)))
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n[BOT] Stopped.")
            break
        except Exception as e:
            print("[BOT] Error: %s" % e)
            time.sleep(30)


if __name__ == "__main__":
    main()
