"""
CEREBUS FX v4.0 — Unified Live Monitor
=======================================
Monitors both Symmetry Trap and P90 CASCADE executors.
Checks: process alive, trades, SL/TP quality, PnL, errors.

Strategies:
  - Symmetry Trap: EURUSD.PRO | Magic 20260531 | Engine B
  - P90 CASCADE:   GBPUSD.PRO | Magic 20260532 | Engine A

Reference: forward_test_monitor.py (DMR pattern)
"""

import sys, json, os, subprocess
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_logs")
STATE_FILE = os.path.join(LOG_DIR, "cerebus_monitor_state.json")

STRATEGIES = [
    {
        "name": "Symmetry Trap",
        "symbol": "EURUSD.PRO",
        "magic": 20260531,
        "engine": "B",
        "sl_type": "Zero-Buffer",
        "tp_type": "1 AU",
    },
    {
        "name": "P90 CASCADE",
        "symbol": "GBPUSD.PRO",
        "magic": 20260532,
        "engine": "A",
        "sl_type": "168% body",
        "tp_type": "-25/-50% AR",
    },
]


def get_est_hour():
    return (datetime.utcnow().hour + (-5)) % 24


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"trades_seen": [], "last_check": None, "alerts": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def check_process_alive(script_name):
    """Check if a Python executor script is running."""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'Get-CimInstance Win32_Process -Filter "Name=\'python.exe\'" | '
             'Select-Object -ExpandProperty CommandLine'],
            capture_output=True, text=True, timeout=5
        )
        return script_name.lower() in result.stdout.lower()
    except Exception:
        return False


def check_strategy(strat, state):
    """Check a single strategy's health. Returns (status_dict, alerts_list)."""
    alerts = []
    status = {
        "name": strat["name"],
        "symbol": strat["symbol"],
        "magic": strat["magic"],
        "engine": strat["engine"],
    }

    # Check process
    script_name = "symmetry_trap_executor.py" if strat["engine"] == "B" else "p90_cascade_executor.py"
    is_alive = check_process_alive(script_name)
    status["process_alive"] = is_alive
    if not is_alive:
        alerts.append(f"⚠️ {strat['name']} executor NOT RUNNING ({script_name})")

    # Connect to MT5 and check positions/orders
    if not mt5.initialize():
        alerts.append("MT5 connection failed")
        return status, alerts

    try:
        # Check open positions
        positions = mt5.positions_get(symbol=strat["symbol"])
        our_positions = [p for p in positions if p.magic == strat["magic"]] if positions else []

        # Check pending orders
        orders = mt5.orders_get(symbol=strat["symbol"])
        our_orders = [o for o in orders if o.magic == strat["magic"]] if orders else []

        status["open_positions"] = len(our_positions)
        status["pending_orders"] = len(our_orders)

        for pos in our_positions:
            # Verify SL/TP set
            tick = mt5.symbol_info_tick(strat["symbol"])
            if tick:
                if pos.sl == 0:
                    alerts.append(f"🚨 {strat['name']} position ticket={pos.ticket} has NO SL!")
                if pos.tp == 0:
                    alerts.append(f"🚨 {strat['name']} position ticket={pos.ticket} has NO TP!")

                # Calculate PnL
                is_short = pos.type == mt5.POSITION_TYPE_SELL
                pnl_pips = round(
                    ((pos.price_open - tick.bid) if is_short else (tick.ask - pos.price_open))
                    * (10000 if strat["symbol"] != "USDJPY" else 100)
                    - (pos.spread if hasattr(pos, 'spread') else 0),
                    1
                )
                dir_str = "SHORT" if is_short else "LONG"
                status["position"] = f"{dir_str} {pos.ticket} PnL={pnl_pips:+.1f}p SL={pos.sl:.5f} TP={pos.tp:.5f}"

        # Check log for recent errors
        log_file = os.path.join(
            LOG_DIR,
            "symmetry_trap_executor.log" if strat["engine"] == "B" else "p90_cascade_executor.log"
        )
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            recent = lines[-20:] if len(lines) > 20 else lines
            errors = [l.strip() for l in recent if "ERROR" in l.upper() or "FATAL" in l.upper() or "FAILED" in l.upper()]
            if errors:
                alerts.append(f"⚠️ {strat['name']} log errors: {errors[-1]}")

        # Check for new trades since last check
        trades_jsonl = os.path.join(
            LOG_DIR,
            "symmetry_trap_signals.jsonl" if strat["engine"] == "B" else "p90_cascade_signals.jsonl"
        )
        if os.path.exists(trades_jsonl):
            with open(trades_jsonl, "r") as f:
                trade_lines = f.readlines()
            known_tickets = set(state.get("trades_seen", []))
            new_trades = []
            for line in trade_lines:
                try:
                    t = json.loads(line.strip())
                    if t.get("type") == "SIGNAL_EXECUTED":
                        sig_id = f"{t.get('ts', '')}_{t.get('signal', {}).get('entry_price', '')}"
                        if sig_id not in known_tickets:
                            new_trades.append(t)
                            known_tickets.add(sig_id)
                except (json.JSONDecodeError, AttributeError):
                    pass
            if new_trades:
                alerts.append(f"✅ {strat['name']}: {len(new_trades)} new trade(s) executed!")
                for nt in new_trades:
                    s = nt.get("signal", {})
                    alerts.append(f"  → {s.get('direction','?')} {s.get('entry_price','?')} SL={s.get('sl','?')} TP={s.get('tp','?')}")
            state["trades_seen"] = list(known_tickets)

    finally:
        mt5.shutdown()

    return status, alerts


def run_monitor():
    """Main monitoring cycle."""
    est_hour = get_est_hour()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"  CEREBUS FX v4.0 — LIVE MONITOR")
    print(f"  {now_str} | EST Hour: {est_hour}")
    print(f"{'='*60}")

    state = load_state()
    all_alerts = []
    all_statuses = []

    try:
        mt5.initialize()
        acct = mt5.account_info()
        if acct:
            print(f"\n  Account: {acct.login} | Balance: ${acct.balance:.2f} | Server: {acct.server}")
        mt5.shutdown()
    except Exception as e:
        print(f"  MT5 Account Check Failed: {e}")

    for strat in STRATEGIES:
        print(f"\n  ── {strat['name']} ({strat['symbol']}) ──")
        try:
            status, alerts = check_strategy(strat, state)
            all_statuses.append(status)
            all_alerts.extend(alerts)

            print(f"    Process: {'✅ RUNNING' if status['process_alive'] else '❌ DEAD'}")
            print(f"    Open Positions: {status.get('open_positions', 0)}")
            print(f"    Pending Orders: {status.get('pending_orders', 0)}")
            if "position" in status:
                print(f"    Position: {status['position']}")
            if alerts:
                for a in alerts:
                    print(f"    {a}")
            else:
                print(f"    ✅ No issues")
        except Exception as e:
            err = f"ERROR checking {strat['name']}: {e}"
            print(f"    {err}")
            all_alerts.append(err)

    # Account-level summary
    try:
        mt5.initialize()
        acct = mt5.account_info()
        if acct:
            print(f"\n  ── ACCOUNT SUMMARY ──")
            print(f"    Balance: ${acct.balance:.2f} | Equity: ${acct.equity:.2f}")
            print(f"    Margin: ${acct.margin:.2f} | Free Margin: ${acct.margin_free:.2f}")

            all_positions = mt5.positions_get()
            our_magic = {20260531, 20260532}
            our_pos = [p for p in all_positions if p.magic in our_magic] if all_positions else []
            if our_pos:
                total_pnl = sum(p.profit for p in our_pos)
                print(f"    Total Open PnL: ${total_pnl:+.2f} ({len(our_pos)} position(s))")
            else:
                print(f"    No open positions")
        mt5.shutdown()
    except Exception:
        pass

    print(f"\n{'='*60}")
    if all_alerts:
        print(f"  ALERTS: {len(all_alerts)}")
        for a in all_alerts:
            print(f"  • {a}")
    else:
        print(f"  STATUS: ✅ ALL CLEAR")
    print(f"{'='*60}")

    state["last_check"] = now_str
    state["alerts"] = all_alerts
    save_state(state)

    return all_statuses, all_alerts


if __name__ == "__main__":
    statuses, alerts = run_monitor()
    print(f"\nDone. {len(alerts)} alert(s).")
