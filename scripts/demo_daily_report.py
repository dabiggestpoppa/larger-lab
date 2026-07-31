"""
Demo Daily Account Report — Weekend Cron Job
Runs daily at 23:00 via Windows Task Scheduler.
Reads demo bridge state and logs, sends summary to team chat.
"""

import json
import os
from datetime import datetime, timedelta

SCRIPT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"
LOG_DIR = os.path.join(SCRIPT_DIR, "demo_logs")
REPORT_FILE = os.path.join(LOG_DIR, "demo_daily_report.txt")
STATE_FILE = os.path.join(LOG_DIR, "demo_bridge_state.json")
BRIDGE_LOG = os.path.join(LOG_DIR, "demo_bridge.log")

def read_bridge_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def read_bridge_log_tail(n=50):
    if not os.path.exists(BRIDGE_LOG):
        return "(no log file)"
    try:
        with open(BRIDGE_LOG, "r") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except:
        return "(error reading log)"

def check_trade_log():
    """Check for any signals or fills in the bridge log today."""
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(BRIDGE_LOG):
        return []
    trades = []
    with open(BRIDGE_LOG, "r") as f:
        for line in f:
            if today in line and ("ENTRY" in line or "TP HIT" in line or "SL HIT" in line or "ORDER" in line):
                trades.append(line.strip()[-120:])
    return trades

def generate_report():
    now = datetime.now()
    state = read_bridge_state()

    report = []
    report.append("=" * 50)
    report.append(f"OC2 DEMO DAILY REPORT — {now.strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 50)

    if state:
        report.append(f"\nBridge Status: {'RUNNING' if state.get('running') else 'STOPPED'}")
        report.append(f"Symbols: {', '.join(state.get('symbols', []))}")
        report.append(f"Daily Stats: {state.get('daily_stats', {})}")

        pos = state.get("positions", {})
        active = [s for s, p in pos.items() if p.get("active")]
        closed = [s for s, p in pos.items() if not p.get("active") and p.get("ticket")]

        report.append(f"\nOpen Positions: {len(active)}")
        for s in active:
            p = pos[s]
            report.append(f"  {s}: {p.get('direction')} @{p.get('entry_price')} SL={p.get('sl')} TP={p.get('tp')}")

        report.append(f"\nClosed Today: {len(closed)}")
        for s in closed:
            p = pos[s]
            report.append(f"  {s}: ticket={p.get('ticket')} result={p.get('profit', 'N/A')}")
    else:
        report.append("\nBridge state file not found — bridge may not have started.")

    # Today's trade log
    trades = check_trade_log()
    report.append(f"\n--- Today's Trade Events ({len(trades)} entries) ---")
    for t in trades:
        report.append(f"  {t}")

    # Summary tail from bridge log
    report.append("\n--- Recent Bridge Log ---")
    log_tail = read_bridge_log_tail(n=20)
    for line in log_tail.strip().split('\n')[-10:]:
        report.append(f"  {line.strip()}")

    report.append("\n" + "=" * 50)
    report.append("End of report.")

    text = "\n".join(report)

    # Write to file
    with open(REPORT_FILE, "w") as f:
        f.write(text)

    print(text)
    return text

if __name__ == "__main__":
    generate_report()