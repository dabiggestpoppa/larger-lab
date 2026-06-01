"""
CEREBUS MT5 Account Tracker
============================
Lightweight account monitor — connects to MT5, pulls account state, outputs JSON.
Designed for hourly cron checks and trade copier sync.

Usage:
  python mt5_account_tracker.py              # Print summary to stdout
  python mt5_account_tracker.py --json       # Output raw JSON
  python mt5_account_tracker.py --positions  # Show open positions only
  python mt5_account_tracker.py --history    # Show today's trade history

Requirements:
  - MT5 terminal must be running and logged in
  - pip install MetaTrader5
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

sys.stdout.reconfigure(encoding="utf-8")

import MetaTrader5 as mt5

# ─── CONFIG ──────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_logs")
STATE_FILE = os.path.join(LOG_DIR, "account_tracker_state.json")


def connect() -> bool:
    """Initialize MT5 connection."""
    if not mt5.initialize():
        print(f"❌ MT5 initialize() failed: {mt5.last_error()}")
        return False
    return True


def get_account_info() -> dict:
    """Pull account summary from MT5."""
    info = mt5.account_info()
    if info is None:
        return {"error": f"Failed to get account info: {mt5.last_error()}"}

    return {
        "login": info.login,
        "server": info.server,
        "balance": info.balance,
        "equity": info.equity,
        "profit": info.profit,
        "margin": info.margin,
        "margin_free": info.margin_free,
        "margin_level": info.margin_level,
        "leverage": info.leverage,
        "currency": info.currency,
        "name": info.name,
        "company": info.company,
    }


def get_open_positions() -> list:
    """Pull all open positions from MT5."""
    positions = mt5.positions_get()
    if positions is None:
        return []

    result = []
    for p in positions:
        result.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
            "volume": p.volume,
            "open_price": p.price_open,
            "current_price": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit,
            "swap": p.swap,
            "magic": p.magic,
            "comment": p.comment,
            "time": datetime.fromtimestamp(p.time).isoformat(),
        })
    return result


def get_today_history() -> list:
    """Pull today's closed trades from MT5 history."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    deals = mt5.history_deals_get(today_start, now)
    if deals is None:
        return []

    result = []
    for d in deals:
        if d.entry == mt5.DEAL_ENTRY_OUT:  # Only closing deals
            result.append({
                "ticket": d.ticket,
                "symbol": d.symbol,
                "type": "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL",
                "volume": d.volume,
                "price": d.price,
                "profit": d.profit,
                "swap": d.swap,
                "commission": d.commission,
                "magic": d.magic,
                "comment": d.comment,
                "time": datetime.fromtimestamp(d.time).isoformat(),
            })
    return result


def get_today_stats(history: list) -> dict:
    """Calculate today's PnL stats from closed trades."""
    if not history:
        return {"trades": 0, "pnl": 0.0, "wins": 0, "losses": 0}

    pnl = sum(d["profit"] + d["swap"] + d["commission"] for d in history)
    wins = sum(1 for d in history if (d["profit"] + d["swap"] + d["commission"]) > 0)
    losses = len(history) - wins

    return {
        "trades": len(history),
        "pnl": round(pnl, 2),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(history) * 100, 1) if history else 0,
    }


def format_report(account: dict, positions: list, history: list, stats: dict) -> str:
    """Format a clean text report for Telegram."""
    lines = []
    lines.append("📊 CEREBUS MT5 ACCOUNT REPORT")
    lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Account
    lines.append("💰 ACCOUNT")
    lines.append(f"  Balance:  ${account.get('balance', 0):,.2f}")
    lines.append(f"  Equity:   ${account.get('equity', 0):,.2f}")
    lines.append(f"  Floating: ${account.get('profit', 0):+,.2f}")
    lines.append(f"  Margin:   ${account.get('margin', 0):,.2f} (Free: ${account.get('margin_free', 0):,.2f})")
    lines.append(f"  Server:   {account.get('server', 'N/A')}")
    lines.append("")

    # Open positions
    lines.append(f"📈 OPEN POSITIONS ({len(positions)})")
    if positions:
        for p in positions:
            emoji = "🟢" if p["profit"] >= 0 else "🔴"
            lines.append(
                f"  {emoji} {p['type']} {p['volume']} {p['symbol']} @ {p['open_price']:.5f}"
                f" | P&L: ${p['profit']:+.2f} | Magic: {p['magic']}"
            )
            if p["sl"] > 0 or p["tp"] > 0:
                lines.append(f"     SL: {p['sl']:.5f} | TP: {p['tp']:.5f}")
    else:
        lines.append("  No open positions")
    lines.append("")

    # Today's closed trades
    lines.append(f"📋 TODAY'S CLOSED TRADES ({stats['trades']})")
    if stats["trades"] > 0:
        lines.append(f"  P&L: ${stats['pnl']:+.2f} | W: {stats['wins']} L: {stats['losses']} | WR: {stats['win_rate']}%")
        for h in history[-5:]:  # Last 5 trades
            emoji = "✅" if (h["profit"] + h["swap"] + h["commission"]) > 0 else "❌"
            net = h["profit"] + h["swap"] + h["commission"]
            lines.append(
                f"  {emoji} {h['type']} {h['volume']} {h['symbol']} @ {h['price']:.5f}"
                f" | ${net:+.2f} | {h['comment']}"
            )
    else:
        lines.append("  No closed trades today")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS MT5 Account Tracker")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--positions", action="store_true", help="Show positions only")
    parser.add_argument("--history", action="store_true", help="Show trade history only")
    parser.add_argument("--save", action="store_true", help="Save state to JSON file")
    args = parser.parse_args()

    if not connect():
        sys.exit(1)

    try:
        account = get_account_info()
        positions = get_open_positions()
        history = get_today_history()
        stats = get_today_stats(history)

        # Build full state
        state = {
            "timestamp": datetime.now().isoformat(),
            "account": account,
            "positions": positions,
            "today_history": history,
            "today_stats": stats,
        }

        # Save state file
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2, default=str)

        # Output
        if args.json:
            print(json.dumps(state, indent=2, default=str))
        elif args.positions:
            print(json.dumps(positions, indent=2, default=str))
        elif args.history:
            print(json.dumps(history, indent=2, default=str))
        else:
            print(format_report(account, positions, history, stats))

    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
