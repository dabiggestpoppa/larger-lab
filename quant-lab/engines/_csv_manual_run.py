"""
Run CSV engine through Nautilus framework to isolate the gap.
This uses the same Nautilus bar data and on_bar flow, but calls
the CSV engine's process_bar instead of the Nautilus strategy.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta, timezone

engines_dir = Path(__file__).parent
sys.path.insert(0, str(engines_dir))

from symmetry_trap import (
    SymmetryTrapEngine, Bar, TradeSignal, TradeDirection,
    EngineState, DEFAULT_TIER_CONFIG, KILL_SWITCH_PCT,
    classify_tier_by_impulse, classify_tier_by_ar
)
from symmetry_trap_backtest import load_m5_csv, compute_stats, BacktestResult, TradeRecord

csv_path = str(Path(__file__).parent.parent / 'data' / 'EURUSD_M5.csv')
bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
print(f"Loaded {len(bars)} bars for {sym}")

# Group by EST date (same as CSV runner)
est_offset = -5
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

print(f"Grouped into {len(days)} EST days")

# Run CSV engine day by day (exact same logic as SymmetryTrapBacktest.run)
tier_config = {
    "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 10.0},
    "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 10.0},
    "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 10.0},
}

engine = SymmetryTrapEngine(pip_size=0.0001, tier_config=tier_config, symbol='EURUSD')
all_trades = []

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    engine.initialize_session(ah, al)
    if not engine.session_active:
        continue
    
    active_trade = None
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour + est_offset) % 24
        
        # Skip Asian hours
        if bar_est_h >= 19 or bar_est_h < 3:
            continue
        
        # 4PM cutoff only if in SEARCH state
        if bar_est_h >= 16 and engine.state == EngineState.SEARCH:
            break
        
        signal = engine.process_bar(bar)
        
        if signal is None:
            if active_trade and engine.entry_price is None:
                active_trade['exit_time'] = bar.timestamp
                active_trade['pnl_pips'] = round(
                    (active_trade['exit_price'] - active_trade['entry_price']) / 0.0001
                    * (1 if active_trade['direction'] == 'LONG' else -1), 1)
                all_trades.append(active_trade)
                active_trade = None
            continue
        
        if signal.event == "ENTRY":
            direction = 'LONG' if signal.direction == TradeDirection.LONG else 'SHORT'
            active_trade = {
                'entry_time': bar.timestamp, 'exit_time': bar.timestamp,
                'direction': direction, 'variant': 'SYMMETRY_TRAP',
                'entry_price': signal.entry_price, 'exit_price': signal.entry_price,
                'sl_price': signal.sl_price, 'tp_price': signal.tp_price,
                'result': 'OPEN', 'pnl_pips': 0.0,
                'ar_pips': round(engine.asian_range_pips, 1),
                'tier': engine.tier_name, 'au_pips': signal.au_used,
                'impulse_size_pips': round(engine.impulse_size_pips, 1),
                'est_hour': bar_est_h, 'loop_count': getattr(signal, 'loop_count', 1),
            }
        
        elif signal.event in ("TP_HIT", "SL_HIT"):
            if active_trade:
                active_trade['exit_time'] = bar.timestamp
                active_trade['result'] = signal.event
                active_trade['exit_price'] = (
                    signal.tp_price if signal.event == "TP_HIT" else signal.sl_price
                )
                active_trade['pnl_pips'] = round(
                    (active_trade['exit_price'] - active_trade['entry_price']) / 0.0001
                    * (1 if active_trade['direction'] == 'LONG' else -1), 1)
                all_trades.append(active_trade)
                active_trade = None
    
    if active_trade:
        last = day_bars[-1]
        active_trade['exit_time'] = last.timestamp
        active_trade['exit_price'] = last.close
        active_trade['result'] = 'EOD_EXIT'
        active_trade['pnl_pips'] = round(
            (active_trade['exit_price'] - active_trade['entry_price']) / 0.0001
            * (1 if active_trade['direction'] == 'LONG' else -1), 1)
        all_trades.append(active_trade)

# Compute stats
wins = sum(1 for t in all_trades if t['pnl_pips'] > 0)
losses = sum(1 for t in all_trades if t['pnl_pips'] < 0)
total_pnl = sum(t['pnl_pips'] for t in all_trades)
wr = wins / len(all_trades) * 100 if all_trades else 0

print(f"\n=== CSV ENGINE (via manual runner) ===")
print(f"Trades: {len(all_trades)}")
print(f"W/L: {wins}/{losses}")
print(f"WR: {wr:.1f}%")
print(f"PnL: {total_pnl:+.1f}p")
print(f"Days: {len(days)}")
print(f"Trades/day: {len(all_trades) / len(days):.2f}")

# Load Nautilus result
nautilus_report = Path(__file__).parent.parent / 'reports' / 'NAUTILUS_SYMMETRY_TRAP_EURUSD_20260604_212558.json'
if nautilus_report.exists():
    with open(nautilus_report) as f:
        n = json.load(f)
    print(f"\n=== NAUTILUS RESULTS ===")
    print(f"Trades: {n['strategy_trades']}")
    print(f"WR: {n['strategy_win_rate']:.1f}%")
    print(f"PnL: {n['strategy_pnl_pips']:.1f}p")
    print(f"Bars: {n['bars']}")
    
    print(f"\n=== DELTA ===")
    print(f"Trade diff: {len(all_trades) - n['strategy_trades']}")
    print(f"WR diff: {wr - n['strategy_win_rate']:+.1f}pp")

# Loop distribution
loop_counts = {}
for t in all_trades:
    lc = str(t.get('loop_count', 1))
    loop_counts[lc] = loop_counts.get(lc, 0) + 1
print(f"\n=== LOOP DISTRIBUTION ===")
for lc in sorted(loop_counts.keys(), key=int):
    print(f"  Loop {lc}: {loop_counts[lc]} trades")

# Tier distribution
tier_counts = {}
for t in all_trades:
    tier = t.get('tier', 'T1')
    tier_counts[tier] = tier_counts.get(tier, 0) + 1
print(f"\n=== TIER DISTRIBUTION ===")
for tier in sorted(tier_counts.keys()):
    print(f"  {tier}: {tier_counts[tier]} trades")
