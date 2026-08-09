"""
Symmetry Trap — Parity Replay Harness
======================================
Loads historical CSV data and feeds the SAME chronological bars into:
A. Canonical backtest path (SymmetryTrapBacktest)
B. Live wrapper path (SymmetryTrapLiveEngine)

Produces detailed trace comparison to find first divergence.
"""

from __future__ import annotations

import csv
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add engines to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines"))

from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    load_m5_csv,
    compute_stats,
    TradeRecord,
    BacktestResult,
)
from symmetry_trap_live import SymmetryTrapLiveEngine
from symmetry_trap import Bar, TradeSignal, TradeDirection, EngineState
from mt5_data_feed import (
    fetch_m5_bars,
    get_current_est_hour,
    get_symbol_pip_size,
    get_symbol_config,
    build_today_bars,
    calculate_asian_range,
    filter_trading_bars,
)
from trading_costs import apply_costs_to_pnl


class ParityTracer:
    """Records every decision point for comparison."""
    
    def __init__(self, name: str):
        self.name = name
        self.events: List[Dict[str, Any]] = []
        self.bar_index = 0
    
    def record(self, event_type: str, data: Dict[str, Any]):
        """Record a decision event."""
        self.events.append({
            "bar_index": self.bar_index,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
    
    def increment_bar(self):
        self.bar_index += 1
    
    def to_csv(self, filepath: str):
        """Export events to CSV."""
        if not self.events:
            return
        
        # Flatten for CSV
        rows = []
        for e in self.events:
            row = {
                "bar_index": e["bar_index"],
                "event_type": e["event_type"],
                "timestamp": e["timestamp"],
            }
            row.update(e["data"])
            rows.append(row)
        
        # Get all possible columns
        all_keys = set()
        for r in rows:
            all_keys.update(r.keys())
        
        fieldnames = ["bar_index", "event_type", "timestamp"] + sorted(k for k in all_keys if k not in ["bar_index", "event_type", "timestamp"])
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def run_canonical_backtest(symbol: str, csv_path: str, config: Dict) -> tuple:
    """Run the canonical backtest and return result + tracer."""
    tracer = ParityTracer("canonical")
    
    # Load bars
    bars, loaded_symbol = load_m5_csv(csv_path, config.get("pip_value", 0.0001))
    print(f"Loaded {len(bars)} bars for {loaded_symbol}")
    
    # Create backtest engine
    bt = SymmetryTrapBacktest(config=config)
    bt.symbol = symbol
    
    # We need to trace the engine created inside run()
    # Let's monkey-patch SymmetryTrapEngine.process_bar globally
    from symmetry_trap import SymmetryTrapEngine
    original_process_bar = SymmetryTrapEngine.process_bar
    original_init = SymmetryTrapEngine.initialize_session
    original_reset_keep = SymmetryTrapEngine._reset_state_keep_loop
    original_reset = SymmetryTrapEngine._reset_state
    
    def traced_process_bar(self, bar):
        tracer.record("bar_processed", {
            "bar_time": bar.timestamp.isoformat(),
            "bar_open": bar.open,
            "bar_high": bar.high,
            "bar_low": bar.low,
            "bar_close": bar.close,
            "engine_state": self.state.value,
            "swing_origin": self.swing_origin,
            "impulse_direction": self.impulse_direction.value,
            "impulse_extreme": self.impulse_extreme,
            "impulse_size_pips": self.impulse_size_pips,
            "tier_name": self.tier_name,
            "au_pips": self.au_pips,
            "trigger_pips": self.trigger_pips,
            "session_active": self.session_active,
            "loop_count": self.loop_count,
        })
        result = original_process_bar(self, bar)
        if result:
            tracer.record("signal_emitted", {
                "event": result.event,
                "direction": result.direction.value if result.direction else None,
                "entry_price": result.entry_price,
                "sl_price": result.sl_price,
                "tp_price": result.tp_price,
                "au_used": result.au_used,
                "loop_count": result.loop_count,
                "reason": result.reason,
            })
        return result
    
    def traced_init(self, asian_high, asian_low):
        tracer.record("session_init", {
            "asian_high": asian_high,
            "asian_low": asian_low,
            "asian_range_pips": (asian_high - asian_low) / self.pip_size,
        })
        return original_init(self, asian_high, asian_low)
    
    def traced_reset_keep(self, new_origin):
        tracer.record("state_reset_keep_loop", {
            "new_origin": new_origin,
            "loop_count": self.loop_count,
        })
        return original_reset_keep(self, new_origin)
    
    def traced_reset(self, new_origin):
        tracer.record("state_reset", {
            "new_origin": new_origin,
        })
        return original_reset(self, new_origin)
    
    SymmetryTrapEngine.process_bar = traced_process_bar
    SymmetryTrapEngine.initialize_session = traced_init
    SymmetryTrapEngine._reset_state_keep_loop = traced_reset_keep
    SymmetryTrapEngine._reset_state = traced_reset
    
    # Run backtest
    bt = SymmetryTrapBacktest(config=config)
    bt.symbol = symbol
    result = bt.run(bars)
    
    # Restore
    SymmetryTrapEngine.process_bar = original_process_bar
    SymmetryTrapEngine.initialize_session = original_init
    SymmetryTrapEngine._reset_state_keep_loop = original_reset_keep
    SymmetryTrapEngine._reset_state = original_reset
    
    return result, tracer


def run_live_wrapper(symbol: str, csv_path: str, config: Dict) -> tuple:
    """Run the live wrapper path and return result + tracer.
    
    This simulates the live engine processing ALL days in the CSV,
    exactly like the canonical backtest does — day by day.
    """
    tracer = ParityTracer("live")
    
    # Load bars (same as canonical)
    bars, loaded_symbol = load_m5_csv(csv_path, config.get("pip_value", 0.0001))
    print(f"Loaded {len(bars)} bars for {loaded_symbol}")
    
    # We need to trace the SymmetryTrapEngine class globally
    from symmetry_trap import SymmetryTrapEngine
    original_process_bar = SymmetryTrapEngine.process_bar
    original_init = SymmetryTrapEngine.initialize_session
    original_reset_keep = SymmetryTrapEngine._reset_state_keep_loop
    original_reset = SymmetryTrapEngine._reset_state
    
    def traced_process_bar(self, bar):
        tracer.record("bar_processed", {
            "bar_time": bar.timestamp.isoformat(),
            "bar_open": bar.open,
            "bar_high": bar.high,
            "bar_low": bar.low,
            "bar_close": bar.close,
            "engine_state": self.state.value,
            "swing_origin": self.swing_origin,
            "impulse_direction": self.impulse_direction.value,
            "impulse_extreme": self.impulse_extreme,
            "impulse_size_pips": self.impulse_size_pips,
            "tier_name": self.tier_name,
            "au_pips": self.au_pips,
            "trigger_pips": self.trigger_pips,
            "session_active": self.session_active,
            "loop_count": self.loop_count,
        })
        result = original_process_bar(self, bar)
        if result:
            tracer.record("signal_emitted", {
                "event": result.event,
                "direction": result.direction.value if result.direction else None,
                "entry_price": result.entry_price,
                "sl_price": result.sl_price,
                "tp_price": result.tp_price,
                "au_used": result.au_used,
                "loop_count": result.loop_count,
                "reason": result.reason,
            })
        return result
    
    def traced_init(self, asian_high, asian_low):
        tracer.record("session_init", {
            "asian_high": asian_high,
            "asian_low": asian_low,
            "asian_range_pips": (asian_high - asian_low) / self.pip_size,
        })
        return original_init(self, asian_high, asian_low)
    
    def traced_reset_keep(self, new_origin):
        tracer.record("state_reset_keep_loop", {
            "new_origin": new_origin,
            "loop_count": self.loop_count,
        })
        return original_reset_keep(self, new_origin)
    
    def traced_reset(self, new_origin):
        tracer.record("state_reset", {
            "new_origin": new_origin,
        })
        return original_reset(self, new_origin)
    
    SymmetryTrapEngine.process_bar = traced_process_bar
    SymmetryTrapEngine.initialize_session = traced_init
    SymmetryTrapEngine._reset_state_keep_loop = traced_reset_keep
    SymmetryTrapEngine._reset_state = traced_reset
    
    # Create the live engine (this creates self.engine = SymmetryTrapEngine)
    live_engine = SymmetryTrapLiveEngine(
        symbol=symbol,
        est_offset=config.get("est_offset", -5),
        entry_window_start=config.get("entry_window_start", 2),
        entry_window_end=config.get("entry_window_end", 11),
        hard_exit_hour=config.get("hard_exit_hour", 17),
        lot_size=config.get("lot_size", 0.01),
        config_override=config,  # Use same config as canonical backtest
    )
    live_engine.config = config
    live_engine.pip_size = config.get("pip_value", 0.0001)
    
    # Replicate the EXACT same flow as SymmetryTrapBacktest.run()
    # Group bars by EST date (same as backtest)
    est_offset = config.get("est_offset", -5)
    days: Dict[str, List[Bar]] = {}
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=est_offset)
        dk = est_dt.strftime("%Y-%m-%d")
        if dk not in days:
            days[dk] = []
        days[dk].append(bar)
    
    all_trades: List[TradeRecord] = []
    
    # Process each day exactly like backtest
    for dk in sorted(days.keys()):
        day_bars = sorted(days[dk], key=lambda b: b.timestamp)
        
        # Use the SAME _find_asian_range as backtest
        ah, al = live_engine.backtest_engine._find_asian_range(day_bars)
        if ah <= 0 or al >= 99999:
            continue
        
        # Initialize session (same as backtest)
        live_engine.engine.initialize_session(ah, al)
        if not live_engine.engine.session_active:
            continue
        
        active_trade: Optional[TradeRecord] = None
        
        for bar in day_bars:
            bar_est_h = live_engine.backtest_engine._get_est_hour(bar.timestamp)
            
            # Skip Asian hours (19:00-03:00 EST) - same as backtest
            if bar_est_h >= 19 or bar_est_h < 3:
                continue
            
            # 4PM EST cutoff - same as backtest
            if bar_est_h >= 16 and live_engine.engine.state == EngineState.SEARCH:
                break
            
            signal = live_engine.engine.process_bar(bar)
            
            if signal is None:
                if active_trade and live_engine.engine.entry_price is None:
                    active_trade.exit_time = bar.timestamp
                    active_trade.pnl_pips = round(
                        (active_trade.exit_price - active_trade.entry_price) / live_engine.pip_size
                        * (1 if active_trade.direction == "LONG" else -1), 1)
                    all_trades.append(active_trade)
                    active_trade = None
                continue
            
            if signal.event == "KILL_SWITCH":
                if active_trade:
                    active_trade.exit_time = bar.timestamp
                    active_trade.result = "KILL_SWITCH"
                    active_trade.exit_price = bar.close
                    active_trade.pnl_pips = round(
                        (active_trade.exit_price - active_trade.entry_price) / live_engine.pip_size
                        * (1 if active_trade.direction == "LONG" else -1), 1)
                    all_trades.append(active_trade)
                    active_trade = None
            
            elif signal.event == "ENTRY":
                direction = "LONG" if signal.direction == TradeDirection.LONG else "SHORT"
                active_trade = TradeRecord(
                    entry_time=bar.timestamp, exit_time=bar.timestamp,
                    direction=direction, variant="SYMMETRY_TRAP",
                    entry_price=signal.entry_price, exit_price=signal.entry_price,
                    sl_price=signal.sl_price, tp_price=signal.tp_price,
                    result="OPEN", pnl_pips=0.0,
                    ar_pips=round(live_engine.engine.asian_range_pips, 1),
                    tier=live_engine.engine.tier_name, au_pips=signal.au_used,
                    impulse_size_pips=round(live_engine.engine.impulse_size_pips, 1),
                    est_hour=bar_est_h,
                    loop_count=getattr(signal, 'loop_count', 1),
                )
            
            elif signal.event in ("TP_HIT", "SL_HIT"):
                if active_trade:
                    active_trade.exit_time = bar.timestamp
                    active_trade.result = signal.event
                    active_trade.exit_price = (
                        signal.tp_price if signal.event == "TP_HIT"
                        else signal.sl_price if signal.sl_price else bar.close
                    )
                    gross_pnl_pips = round(
                        (active_trade.exit_price - active_trade.entry_price) / live_engine.pip_size
                        * (1 if active_trade.direction == "LONG" else -1), 1)
                    active_trade.pnl_pips = apply_costs_to_pnl(
                        gross_pnl_pips, symbol, active_trade.direction)
                    all_trades.append(active_trade)
                    active_trade = None
        
        # EOD exit
        if active_trade:
            last = day_bars[-1]
            active_trade.exit_time = last.timestamp
            active_trade.exit_price = last.close
            active_trade.result = "EOD_EXIT"
            gross_pnl_pips = round(
                (active_trade.exit_price - active_trade.entry_price) / live_engine.pip_size
                * (1 if active_trade.direction == "LONG" else -1), 1)
            active_trade.pnl_pips = apply_costs_to_pnl(
                gross_pnl_pips, symbol, active_trade.direction)
            all_trades.append(active_trade)
    
    # Restore
    SymmetryTrapEngine.process_bar = original_process_bar
    SymmetryTrapEngine.initialize_session = original_init
    SymmetryTrapEngine._reset_state_keep_loop = original_reset_keep
    SymmetryTrapEngine._reset_state = original_reset
    
    # Compute stats
    result = compute_stats(all_trades)
    result.symbol = symbol
    result.data_bars = len(bars)
    result.data_days = len(days)
    
    return result, tracer


def compare_traces(canonical_tracer: ParityTracer, live_tracer: ParityTracer) -> List[Dict]:
    """Compare two traces and find divergences."""
    divergences = []
    
    # Align by bar_index
    canon_events = {e["bar_index"]: e for e in canonical_tracer.events}
    live_events = {e["bar_index"]: e for e in live_tracer.events}
    
    all_indices = set(canon_events.keys()) | set(live_events.keys())
    
    for idx in sorted(all_indices):
        c = canon_events.get(idx)
        l = live_events.get(idx)
        
        if c and not l:
            divergences.append({
                "bar_index": idx,
                "type": "MISSING_IN_LIVE",
                "canonical_event": c["event_type"],
                "live_event": None,
            })
        elif l and not c:
            divergences.append({
                "bar_index": idx,
                "type": "EXTRA_IN_LIVE",
                "canonical_event": None,
                "live_event": l["event_type"],
            })
        elif c and l:
            if c["event_type"] != l["event_type"]:
                divergences.append({
                    "bar_index": idx,
                    "type": "EVENT_TYPE_MISMATCH",
                    "canonical_event": c["event_type"],
                    "live_event": l["event_type"],
                })
            else:
                # Compare data fields
                c_data = c["data"]
                l_data = l["data"]
                all_keys = set(c_data.keys()) | set(l_data.keys())
                for key in all_keys:
                    cv = c_data.get(key)
                    lv = l_data.get(key)
                    if cv != lv:
                        divergences.append({
                            "bar_index": idx,
                            "type": "FIELD_MISMATCH",
                            "field": key,
                            "canonical_value": cv,
                            "live_value": lv,
                            "event_type": c["event_type"],
                        })
    
    return divergences


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Symmetry Trap Parity Replay")
    parser.add_argument("csv_file", help="Path to M5 CSV data file")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol name")
    parser.add_argument("--pip-size", type=float, default=0.0001, help="Pip size")
    parser.add_argument("--est-offset", type=int, default=-5, help="EST offset from UTC")
    parser.add_argument("--entry-start", type=int, default=2, help="Entry window start hour EST")
    parser.add_argument("--entry-end", type=int, default=11, help="Entry window end hour EST")
    parser.add_argument("--hard-exit", type=int, default=17, help="Hard exit hour EST")
    parser.add_argument("--lot-size", type=float, default=0.01, help="Lot size")
    parser.add_argument("--output-dir", default="artifacts/symmetry_trap", help="Output directory")
    
    args = parser.parse_args()
    
    # Build config
    config = {
        "pip_value": args.pip_size,
        "est_offset": args.est_offset,
        "entry_window_start": args.entry_start,
        "entry_window_end": args.entry_end,
        "hard_exit_hour": args.hard_exit,
        "lot_size": args.lot_size,
        "name": args.symbol,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 12.0, "trigger": 15.0},
            "T3": {"ar_max": 60.0, "au": 15.0, "trigger": 19.0},
        },
    }
    
    print(f"Running parity replay for {args.symbol}")
    print(f"CSV: {args.csv_file}")
    print(f"Config: {config}")
    
    # Run canonical backtest
    print("\n=== Running Canonical Backtest ===")
    canon_result, canon_tracer = run_canonical_backtest(args.symbol, args.csv_file, config)
    print(f"Canonical: {canon_result.total_trades} trades, {canon_result.win_rate:.1f}% WR, {canon_result.total_pnl_pips:.1f} pips")
    
    # Run live wrapper
    print("\n=== Running Live Wrapper ===")
    live_result, live_tracer = run_live_wrapper(args.symbol, args.csv_file, config)
    print(f"Live: {live_result.total_trades} trades, {live_result.win_rate:.1f}% WR, {live_result.total_pnl_pips:.1f} pips")
    
    # Compare
    print("\n=== Comparing Traces ===")
    divergences = compare_traces(canon_tracer, live_tracer)
    print(f"Found {len(divergences)} divergences")
    
    # Output traces
    os.makedirs(args.output_dir, exist_ok=True)
    canon_tracer.to_csv(os.path.join(args.output_dir, "backtest_trace.csv"))
    live_tracer.to_csv(os.path.join(args.output_dir, "live_trace.csv"))
    
    # Output divergences
    if divergences:
        with open(os.path.join(args.output_dir, "parity_diff.csv"), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["bar_index", "type", "field", "canonical_value", "live_value", "event_type", "canonical_event", "live_event"])
            writer.writeheader()
            for d in divergences:
                writer.writerow(d)
        print(f"Divergences written to {args.output_dir}/parity_diff.csv")
        
        # Show first few
        print("\nFirst 10 divergences:")
        for d in divergences[:10]:
            print(f"  Bar {d['bar_index']}: {d['type']} - {d.get('field', d.get('canonical_event', d.get('live_event', '')))}")
    else:
        print("NO DIVERGENCES - PARITY ACHIEVED!")
    
    # Also output summary
    summary = {
        "symbol": args.symbol,
        "csv_file": args.csv_file,
        "config": config,
        "canonical_trades": canon_result.total_trades,
        "canonical_wr": canon_result.win_rate,
        "canonical_pnl": canon_result.total_pnl_pips,
        "live_trades": live_result.total_trades,
        "live_wr": live_result.win_rate,
        "live_pnl": live_result.total_pnl_pips,
        "trade_count_diff": canon_result.total_trades - live_result.total_trades,
        "pnl_diff": canon_result.total_pnl_pips - live_result.total_pnl_pips,
        "divergence_count": len(divergences),
        "first_divergence": divergences[0] if divergences else None,
        "parity_achieved": len(divergences) == 0 and canon_result.total_trades == live_result.total_trades,
    }
    
    with open(os.path.join(args.output_dir, "parity_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\nSummary written to {args.output_dir}/parity_summary.json")
    
    return len(divergences) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)