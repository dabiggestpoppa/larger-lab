"""
Fidelity comparison: Bar-level vs Tick-level DMR simulation
Runs both engines on the same data and compares trade-by-trade.
"""
import sys, os, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
from dmr_backtest_v2 import run_dmr, fetch_bars, PARAMS

def run_tick_sim_on_range(from_dt, to_dt):
    """Run tick-level simulation (from dmr_tick_sim.py logic inline)"""
    from dmr_tick_sim import run_tick_dmr, fetch_m5_bars, fetch_ticks
    
    bars = fetch_m5_bars(from_dt, to_dt)
    if bars is None:
        return None, None
    
    ticks = fetch_ticks(from_dt, to_dt)
    if ticks is None:
        return None, None
    
    return run_tick_dmr(bars, ticks, PARAMS)

def main():
    print("="*60)
    print("FIDELITY COMPARISON: Bar-level vs Tick-level")
    print("="*60)
    
    if not mt5.initialize():
        print("MT5 connection failed")
        sys.exit(1)
    
    # Test on recent data where both bars and ticks are available
    TEST_RANGES = [
        ("1W_May21-28", datetime(2026, 5, 21), datetime(2026, 5, 28)),
        ("1W_May14-21", datetime(2026, 5, 14), datetime(2026, 5, 21)),
        ("1W_May07-14", datetime(2026, 5, 7),  datetime(2026, 5, 14)),
        ("1W_Apr30-07", datetime(2026, 4, 30), datetime(2026, 5, 7)),
        ("2W_May14-28", datetime(2026, 5, 14), datetime(2026, 5, 28)),
    ]
    
    for label, from_dt, to_dt in TEST_RANGES:
        print(f"\n{'─'*60}")
        print(f"Period: {from_dt.strftime('%Y-%m-%d')} to {to_dt.strftime('%Y-%m-%d')}")
        print(f"{'─'*60}")
        
        # Bar-level
        bars = fetch_bars(from_dt, to_dt)
        if bars is None:
            print("  No bar data")
            continue
        
        bar_trades, bar_summary = run_dmr(bars, PARAMS)
        
        # Tick-level
        from dmr_tick_sim import run_tick_dmr, fetch_m5_bars, fetch_ticks
        m5 = fetch_m5_bars(from_dt, to_dt)
        ticks = fetch_ticks(from_dt, to_dt)
        
        if ticks is not None and m5 is not None:
            tick_trades, tick_summary = run_tick_dmr(m5, ticks, PARAMS)
        else:
            tick_trades, tick_summary = None, None
        
        # Compare
        print(f"\n  Bar-level:  {bar_summary['total_trades']:3d} tr | WR: {bar_summary['win_rate']:5.1f}% | P&L: {bar_summary['total_pnl_pips']:+7.1f}p")
        if tick_summary:
            print(f"  Tick-level: {tick_summary['total_trades']:3d} tr | WR: {tick_summary['win_rate']:5.1f}% | P&L: {tick_summary['total_pnl_pips']:+7.1f}p")
            
            # Trade count diff
            tc_diff = tick_summary['total_trades'] - bar_summary['total_trades']
            pnl_diff = tick_summary['total_pnl_pips'] - bar_summary['total_pnl_pips']
            wr_diff = tick_summary['win_rate'] - bar_summary['win_rate']
            
            print(f"  ─────────────────────────────────")
            print(f"  Diff:        {tc_diff:+3d} tr | WR: {wr_diff:+5.1f}% | P&L: {pnl_diff:+7.1f}p")
            
            # Detailed trade comparison
            if bar_trades and tick_trades:
                print(f"\n  Trade-by-trade comparison (first 10):")
                print(f"  {'Date':12s} | Bar P&L | Tick P&L | Δ")
                print(f"  {'-'*12}-+-{'-'*7}-+-{'-'*8}-+-{'-'*6}")
                for i in range(min(len(bar_trades), len(tick_trades), 10)):
                    bt = bar_trades[i]
                    tt = tick_trades[i]
                    delta = tt['pnl_pips'] - bt['pnl_pips']
                    print(f"  {bt['date']:12s} | {bt['pnl_pips']:+7.1f} | {tt['pnl_pips']:+8.1f} | {delta:+6.1f}")
                
                if len(bar_trades) != len(tick_trades):
                    print(f"\n  WARNING: Trade count differs ({len(bar_trades)} bar vs {len(tick_trades)} tick)")
                    print(f"  This means entry/exit conditions trigger at different times")
        else:
            print("  Tick data unavailable for this period")
    
    # Summary
    print(f"\n{'='*60}")
    print("FIDELITY ASSESSMENT")
    print(f"{'='*60}")
    print("""
The bar-level and tick-level simulations should produce identical 
results when:
1. The same bars trigger P90 and DS (they do — both use M5 bars)
2. Entry is at bar close (tick sim uses DS-touch bar close)
3. TP/SL triggers match

Key difference: Tick-level can detect intrabar SL/TP touches that 
the bar-level misses (e.g., price spikes through SL within a bar 
but closes above it).

If differences are small (<5% WR, <10% P&L), the bar-level 
simulation is a VALID predictor for live MT5 execution.
""")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
