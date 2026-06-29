"""
DISCORD SIGNAL BOT — CEREBUS + DMR Scanner Forwarder
=====================================================
Watches data/alerts_history.json and dmr_signals.jsonl, forwards to Discord.
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


def format_dmr_signal(sig):
    """Format DMR-specific signal for Discord."""
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    entry = sig.get("entry_price", 0)
    sl = sig.get("sl_price", 0)
    tp = sig.get("tp_price", 0)
    body = sig.get("body_pips", 0)
    ds = sig.get("ds_level", 0)
    ar = sig.get("asian_range_pips", 0)
    ts = sig.get("timestamp", datetime.now(EST).strftime("%H:%M:%S"))
    emoji = "🟢" if direction == "LONG" else "🔴"
    return (
        "%s **DMR SIGNAL** — %s\n"
        "Direction: **%s** | Entry: **%s**\n"
        "SL: %s | TP: %s\n"
        "Body: %.1fp | DS Level: %s | AR: %.1fp\n"
        "Time: %s EST"
    ) % (emoji, symbol, direction, entry, sl, tp, body, ds, ar, ts)


def scan_files():
    new_signals = []
    
    # ONLY watch DMR signals (ignore generic alerts_history.json to avoid flooding)
    dmr_file = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "dmr_signals.jsonl"
    if dmr_file.exists():
        fkey = str(dmr_file)
        last_pos = file_positions.get(fkey, 0)
        try:
            with open(dmr_file, "r", encoding="utf-8") as f:
                f.seek(last_pos)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            new_signals.append(("dmr", entry))
                        except:
                            pass
                file_positions[fkey] = f.tell()
        except Exception as e:
            print("[DMR SCANNER] Error: %s" % e)
    
    return new_signals


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  DISCORD SIGNAL BOT — DMR Only")
    print("  Discord webhook: %s" % ("SET" if DISCORD_WEBHOOK else "NOT SET"))
    print("  Watching: quant-lab/mt5/live_logs/dmr_signals.jsonl")
    print("=" * 60)

    if args.test:
        msg = "🟢 **CEREBUS BOT TEST** — Online!\nTime: " + datetime.now(EST).strftime("%H:%M:%S EST")
        send_discord(msg)
        print("Test sent.")
        return

    print("\n[BOT] Watching for DMR signals only... (Ctrl+C to stop)\n")
    while True:
        try:
            signals = scan_files()
            for sig_type, sig in signals:
                msg = format_dmr_signal(sig)
                if send_discord(msg):
                    print("[%s] [DMR] %s %s @ %s" % (
                        datetime.now(EST).strftime("%H:%M:%S"),
                        sig.get("symbol", "?"),
                        sig.get("direction", "?"),
                        sig.get("entry_price", "?")))
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n[BOT] Stopped.")
            break
        except Exception as e:
            print("[BOT] Error: %s" % e)
            time.sleep(30)


if __name__ == "__main__":
    main()
