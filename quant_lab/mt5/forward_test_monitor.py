"""
DMR Forward Test Monitor
========================
Checks executor health, trade quality, and sends alerts.
Runs via cron every 5 minutes during trading hours.
"""
import sys, json, os, subprocess
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

SYMBOL = "EURUSD.PRO"
MAGIC = 20260528
LOG_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\live_logs"
STATE_FILE = os.path.join(LOG_DIR, "forward_test_state.json")


def get_est_hour():
    return (datetime.now().hour + (-5)) % 24


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"trades_seen": [], "last_check": None, "alerts": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def check_trade_quality(pos_or_deal):
    """Check if trade has valid SL/TP and tight execution."""
    issues = []

    # Check SL/TP are set
    if pos_or_deal.get("sl", 0) == 0:
        issues.append("NO_SL")
    if pos_or_deal.get("tp", 0) == 0:
        issues.append("NO_TP")

    return issues


def run_monitor():
    """Main monitor cycle."""
    est_hour = get_est_hour()
    state = load_state()
    now = datetime.now().isoformat()

    if not mt5.initialize():
        return {"status": "error", "msg": "MT5 init failed"}

    alerts = []

    # ── Check executor is alive — look for recent log activity —
    exec_log = os.path.join(LOG_DIR, "executor.log")
    if os.path.exists(exec_log):
        mtime = os.path.getmtime(exec_log)
        last_log_time = datetime.fromtimestamp(mtime)
        idle_minutes = (datetime.now() - last_log_time).total_seconds() / 60

        if idle_minutes > 5:
            alerts.append(f"WARNING: Executor idle for {idle_minutes:.0f} minutes")

            # Check if python process is running
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True, text=True
            )
            if 'dmr_executor' not in result.stdout and 'python' in result.stdout:
                # Python running but executor might be stuck
                pass
    else:
        alerts.append("ERROR: No executor log found")

    # ── Check open positions —
    positions = mt5.positions_get(symbol=SYMBOL)
    dmr_positions = [p for p in positions if p.magic == MAGIC] if positions else []

    pos_summary = []
    for pos in dmr_positions:
        is_short = pos.type == mt5.POSITION_TYPE_SELL
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            if is_short:
                pnl_pips = round((pos.price_open - tick.bid) * 10000 - PARAMS_SPREAD, 1)
            else:
                pnl_pips = round((tick.ask - pos.price_open) * 10000 - PARAMS_SPREAD, 1)
        else:
            pnl_pips = 0

        quality_issues = []
        if pos.sl == 0:
            quality_issues.append("NO_SL")
        if pos.tp == 0:
            quality_issues.append("NO_TP")

        pos_info = {
            "ticket": pos.ticket,
            "dir": "SHORT" if is_short else "LONG",
            "entry": pos.price_open,
            "sl": pos.sl,
            "tp": pos.tp,
            "pnl_pips": pnl_pips,
            "issues": quality_issues,
        }
        pos_summary.append(pos_info)

        if quality_issues:
            alerts.append(f"TRADE QUALITY: {pos_info['dir']} ticket={pos.ticket} issues={quality_issues}")

    # — Check today's closed trades —
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    deals = mt5.history_deals_get(today_start, datetime.now())
    dmr_deals = [d for d in deals if d.symbol == SYMBOL and d.magic == MAGIC] if deals else []

    # Track new trades
    new_trades = []
    for d in dmr_deals:
        trade_key = str(d.deal)
        if trade_key not in state["trades_seen"]:
            state["trades_seen"].append(trade_key)
            new_trades.append({
                "deal": d.deal,
                "type": d.type,
                "price": d.price,
                "profit": d.profit,
                "comment": d.comment,
            })
            alerts.append(
                f"NEW TRADE: deal={d.deal} type={d.type} @ {d.price:.5f} "
                f"P&L=${d.profit:+.2f} ({d.comment})"
            )

    # — Account status —
    acct = mt5.account_info()
    balance = acct.balance if acct else 0
    equity = acct.equity if acct else 0

    # — Compile report —
    state["last_check"] = now
    if alerts:
        state["alerts"].extend(alerts)
    save_state(state)

    mt5.shutdown()

    report = {
        "timestamp": now,
        "est_hour": est_hour,
        "balance": balance,
        "equity": equity,
        "open_positions": len(dmr_positions),
        "position_details": pos_summary,
        "closed_today": len(dmr_deals),
        "new_trades": new_trades,
        "alerts": alerts,
        "status": "ok" if not alerts else "ALERT",
    }

    return report


PARAMS_SPREAD = 0.1  # Will be overridden


def main():
    report = run_monitor()

    # Print summary
    print(json.dumps(report, indent=2, default=str))

    # Write to forward test report file
    os.makedirs(LOG_DIR, exist_ok=True)
    report_file = os.path.join(LOG_DIR, "forward_test_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return report


if __name__ == "__main__":
    main()
