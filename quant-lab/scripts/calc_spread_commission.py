"""
Spread + Commission Cost Estimator
===================================
1. Pull current spread from MT5 symbol_info for each pair
   (Best available proxy — historical tick spread sampling from MT5
    is extremely slow and rate-limited)
2. Take backtrade trade results, apply $0.07 commission per trade
   Recalculate net PnL

Simple scripts. Basic calculations. Done.
"""

import MetaTrader5 as mt5
import json
import os

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PAIRS = [
    "EURUSD.PRO", "USDJPY.PRO", "CHFJPY.PRO",
    "NZDUSD.PRO", "AUDUSD.PRO", "USDCHF.PRO", "GBPJPY.PRO"
]

PAIR_DISPLAY = {
    "EURUSD.PRO": "EURUSD",
    "USDJPY.PRO": "USDJPY",
    "CHFJPY.PRO": "CHFJPY",
    "NZDUSD.PRO": "NZDUSD",
    "AUDUSD.PRO": "AUDUSD",
    "USDCHF.PRO": "USDCHF",
    "GBPJPY.PRO": "GBPJPY",
}

COMMISSION_PER_TRADE = 0.07  # $0.07 per round-turn trade


def get_pip_size(symbol):
    return 0.01 if "JPY" in symbol else 0.0001


def get_spread_from_mt5():
    """Get current spread from MT5 symbol_info."""
    if not mt5.initialize():
        print("ERROR: MT5 init failed")
        return {}

    spreads = {}
    for sym in PAIRS:
        info = mt5.symbol_info(sym)
        if info:
            pip = get_pip_size(sym)
            spread_pips = round(info.spread * info.point / pip, 2)
            spreads[sym] = {
                "spread_pips": spread_pips,
                "spread_points": info.spread,
                "digits": info.digits,
            }
            print(f"  {PAIR_DISPLAY[sym]}: {spread_pips} pips ({info.spread} pts)")
        else:
            print(f"  {PAIR_DISPLAY[sym]}: NOT FOUND IN MT5")
    mt5.shutdown()
    return spreads


def apply_commission():
    """Find backtest trade files and apply commission."""
    # Look for the sweep result files which have trade-level data
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    # Check for backtest trade CSVs
    trade_files = []
    for f in os.listdir(data_dir):
        if f.endswith('.csv') and any(p.replace('.PRO','').replace('_PRO','') in f for p in PAIRS):
            trade_files.append(os.path.join(data_dir, f))

    # Also check reports for JSON with trade lists
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

    print("\n  Looking for backtest trade data...")

    # Try to find any JSON with trade-level data
    if os.path.exists(reports_dir):
        json_files = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
        for jf in json_files[:10]:  # Check first 10
            jpath = os.path.join(reports_dir, jf)
            try:
                with open(jpath) as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'trades' in data and len(data['trades']) > 100:
                    print(f"  Found: {jf} ({len(data['trades'])} trades)")
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'pnl' in str(data[0]):
                    print(f"  Found: {jf} ({len(data)} entries)")
            except:
                pass


if __name__ == "__main__":
    print("=" * 60)
    print("SPREAD + COMMISSION ESTIMATE")
    print("=" * 60)

    # ── 1. Spread ──
    print("\n[1] CURRENT SPREAD FROM MT5")
    print("-" * 40)
    spreads = get_spread_from_mt5()

    # ── 2. Commission on backtest trades ──
    print("\n[2] COMMISSION IMPACT")
    print("-" * 40)
    print(f"  Rate: ${COMMISSION_PER_TRADE} per round-turn trade")
    print(f"  (1 round turn = 1 entry + 1 exit = $0.07 total)")

    # Load the main backtest report
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

    # Find the best backtest file with trade data
    best_file = None
    if os.path.exists(reports_dir):
        for f in sorted(os.listdir(reports_dir), reverse=True):
            if 'symmetry_trap' in f.lower() and f.endswith('.json'):
                fpath = os.path.join(reports_dir, f)
                try:
                    with open(fpath) as fh:
                        data = json.load(fh)
                    if isinstance(data, dict):
                        trades = data.get('trades', data.get('closed_trades', []))
                        if len(trades) > 50:
                            best_file = (f, data, trades)
                            break
                except:
                    pass

    if best_file:
        fname, data, trades = best_file
        total = len(trades)
        wins = sum(1 for t in trades if (t.get('pnl_pips', 0) or t.get('pnl', 0) or 0) > 0)
        losses = total - wins
        gross_pnl = sum(t.get('pnl_pips', 0) or t.get('pnl', 0) or 0 for t in trades)

        # Commission: $0.07 per trade
        total_commission = total * COMMISSION_PER_TRADE

        # Convert to pips: on 0.01 lot, 1 pip = $0.10 for EUR/USD
        # So $0.07 = 0.7 pips per trade on 0.01 lot
        pip_value = 0.10  # $0.10 per pip per 0.01 lot
        commission_pips = total_commission / pip_value
        net_pnl = gross_pnl - commission_pips

        print(f"\n  File: {fname}")
        print(f"  Trades: {total} (W:{wins} L:{losses} WR:{round(wins/total*100,1)}%)")
        print(f"  Gross PnL: {round(gross_pnl, 1)} pips")
        print(f"  Commission: ${round(total_commission, 2)} total = {round(commission_pips, 1)} pips")
        print(f"  Net PnL:   {round(net_pnl, 1)} pips")
        print(f"  Impact:    {round(commission_pips/gross_pnl*100, 1)}% of gross profit" if gross_pnl > 0 else "")
    else:
        print("  No backtest trade file found with trade-level data")
        print("  Will need to specify which file to use")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("SPREAD SUMMARY")
    print("-" * 40)
    if spreads:
        for sym in PAIRS:
            if sym in spreads:
                s = spreads[sym]
                print(f"  {PAIR_DISPLAY[sym]}: {s['spread_pips']} pips")
    print(f"\n  Commission: ${COMMISSION_PER_TRADE}/trade")
    print("=" * 60)
