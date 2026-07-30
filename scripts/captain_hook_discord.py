"""
CAPTAIN HOOK DISCORD BOT — Clean Signal Forwarding
===================================================
Simple workflow:
1. Wait for DMR signals from dmr_signals.jsonl
2. One signal = one log entry = one Discord message (no spam, no duplicates)
3. 5 PM EST daily: simple trade review (signals sent, trades triggered)
"""
import os
import sys
import json
import time
import requests
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

# Files to watch
DMR_SIGNALS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "dmr_signals.jsonl"
STATS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "dmr_daily_stats.json"

# Track file position to only read new lines
file_position = 0

# Track sent signals to prevent duplicates (key = symbol|event|timestamp)
sent_signals = set()

# Daily counters
daily_signals_sent = 0
daily_trades_triggered = 0
last_eod_date = None


def send_discord(message):
    """Send message to Discord webhook."""
    if not DISCORD_WEBHOOK:
        print("[DISCORD] Webhook not configured")
        return False
    try:
        if len(message) > 1900:
            message = message[:1900] + "\n... (truncated)"
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[DISCORD] Error: {e}")
        return False


def format_entry_signal(sig):
    """Format DMR entry signal for Discord."""
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
        "```\n"
        "%s DMR ENTRY — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Direction:  %s\n"
        "Entry:      %s\n"
        "SL:         %s\n"
        "TP:         %s\n"
        "Body:       %.1fp\n"
        "DS Level:   %s\n"
        "AR:         %.1fp\n"
        "Time:       %s EST\n"
        "```"
    ) % (emoji, symbol, direction, entry, sl, tp, body, ds, ar, ts)


def format_result_signal(sig):
    """Format TP/SL/HARD_EXIT result for Discord."""
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    result = sig.get("event", sig.get("result", "?"))
    pnl = sig.get("pnl_pips", sig.get("profit", 0))
    entry = sig.get("entry_price", sig.get("entry", 0))
    exit_price = sig.get("exit_price", sig.get("price", 0))
    ts = sig.get("timestamp", datetime.now(EST).strftime("%H:%M:%S"))
    
    if result in ("TP_HIT", "DMR_TP_HIT", "TP"):
        emoji = "✅ TP HIT"
        color = "🟢"
    elif result in ("SL_HIT", "DMR_SL_HIT", "SL"):
        emoji = "❌ SL HIT"
        color = "🔴"
    elif result in ("HARD_EXIT", "EWS_EXIT"):
        emoji = "⏰ HARD EXIT"
        color = "🟡"
    else:
        emoji = f"📊 {result}"
        color = "⚪"
    
    return (
        "```\n"
        "%s DMR RESULT — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Result:     %s\n"
        "PnL:        %+.1f pips\n"
        "Entry:      %s\n"
        "Exit:       %s\n"
        "Time:       %s EST\n"
        "```"
    ) % (color, symbol, emoji, pnl, entry, exit_price, ts)


def format_eod_report():
    """Format end-of-day summary."""
    now = datetime.now(EST)
    date_str = now.strftime("%Y-%m-%d")
    
    # Load stats from engine
    stats = {"signals_detected": 0, "orders_placed": 0, "tp_hits": 0, "sl_hits": 0, "skipped_stale": 0}
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except:
            pass
    
    total_signals = stats.get("signals_detected", 0)
    orders_placed = stats.get("orders_placed", 0)
    tp_hits = stats.get("tp_hits", 0)
    sl_hits = stats.get("sl_hits", 0)
    skipped = stats.get("skipped_stale", 0)
    
    return (
        "```\n"
        "📊 CAPTAIN HOOK EOD REPORT — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Signals Sent:     %d\n"
        "Orders Placed:    %d\n"
        "TP Hits:          %d\n"
        "SL Hits:          %d\n"
        "Skipped (stale):  %d\n"
        "```"
    ) % (date_str, total_signals, orders_placed, tp_hits, sl_hits, skipped)


def scan_new_signals():
    """Read new signals from JSONL file."""
    global file_position, daily_signals_sent, daily_trades_triggered
    new_signals = []
    
    if not DMR_SIGNALS_FILE.exists():
        return new_signals
    
    try:
        with open(DMR_SIGNALS_FILE, "r", encoding="utf-8") as f:
            f.seek(file_position)
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        new_signals.append(entry)
                    except:
                        pass
            file_position = f.tell()
    except Exception as e:
        print(f"[SCAN] Error: {e}")
    
    return new_signals


def process_signals(signals):
    """Process and send new signals to Discord."""
    global daily_signals_sent, daily_trades_triggered, sent_signals
    
    for sig in signals:
        # Create unique key to prevent duplicates
        sig_key = f"{sig.get('symbol','?')}|{sig.get('event','?')}|{sig.get('timestamp','?')}"
        if sig_key in sent_signals:
            continue
        sent_signals.add(sig_key)
        
        event = sig.get("event", "DMR_ENTRY")
        
        if event == "DMR_ENTRY":
            msg = format_entry_signal(sig)
            daily_signals_sent += 1
        elif event in ("TP_HIT", "DMR_TP_HIT", "SL_HIT", "DMR_SL_HIT", "HARD_EXIT", "EWS_EXIT"):
            msg = format_result_signal(sig)
            daily_trades_triggered += 1
        else:
            continue
        
        if send_discord(msg):
            print(f"[{datetime.now(EST).strftime('%H:%M:%S')}] SENT: {event} {sig.get('symbol','?')} {sig.get('direction','')}")
        else:
            print(f"[{datetime.now(EST).strftime('%H:%M:%S')}] FAILED: {event} {sig.get('symbol','?')}")


def check_eod():
    """Check if it's 5 PM EST and send EOD report."""
    global last_eod_date
    now = datetime.now(EST)
    
    if now.hour == 17 and now.minute == 0 and last_eod_date != now.date():
        last_eod_date = now.date()
        msg = format_eod_report()
        if send_discord(msg):
            print(f"[{now.strftime('%H:%M:%S')}] EOD report sent")
        else:
            print(f"[{now.strftime('%H:%M:%S')}] EOD report FAILED")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Send test message and exit")
    parser.add_argument("--eod", action="store_true", help="Send EOD report and exit")
    args = parser.parse_args()

    print("=" * 60)
    print("  CAPTAIN HOOK DISCORD BOT")
    print("  Webhook: %s" % ("SET" if DISCORD_WEBHOOK else "NOT SET"))
    print("  Watching: quant-lab/mt5/live_logs/dmr_signals.jsonl")
    print("  EOD: 5 PM EST daily")
    print("=" * 60)

    if args.test:
        send_discord("🟢 **CAPTAIN HOOK ONLINE** — Watching for DMR signals!")
        print("Test sent.")
        return

    if args.eod:
        send_discord(format_eod_report())
        return

    # Initialize file position to end of file (don't replay history)
    global file_position
    if DMR_SIGNALS_FILE.exists():
        with open(DMR_SIGNALS_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            file_position = f.tell()
    
    print("\n[CAPTAIN HOOK] Watching for DMR signals... (Ctrl+C to stop)\n")
    
    while True:
        try:
            # 1) Scan for new signals
            signals = scan_new_signals()
            if signals:
                process_signals(signals)
            
            # 2) Check for EOD (5 PM EST)
            check_eod()
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n[CAPTAIN HOOK] Stopped.")
            break
        except Exception as e:
            print(f"[CAPTAIN HOOK] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()