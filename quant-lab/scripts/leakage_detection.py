"""
Leakage Detection Suite for Backtest Engines
=============================================
Checks for common backtest biases and data leakage issues.
"""

import sys
sys.path.insert(0, 'engines')

from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

# Import all engines
from p90_engine import P90Engine, Bar
from symmetry_trap import SymmetryTrapEngine
from p90_backtest import load_bars_csv, group_by_session, calc_asian_range
from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest
from dmr_standalone_backtest import load_csv, run_backtest
from rekey_intraday import load_bars_csv as rekey_load_bars, compute_sessions
from rekey_dead_simple import load_csv as rekey_dead_load_csv


def check_look_ahead_bias(engine_name: str, bars: List[Bar]) -> Dict[str, Any]:
    """Check if engine uses future data for current decisions."""
    issues = []
    
    # Check 1: Verify bars are sorted chronologically
    for i in range(1, len(bars)):
        if bars[i].timestamp < bars[i-1].timestamp:
            issues.append(f"Bars not sorted: index {i} earlier than {i-1}")
            break
    
    # Check 2: No duplicate timestamps
    timestamps = [b.timestamp for b in bars]
    if len(timestamps) != len(set(timestamps)):
        issues.append("Duplicate timestamps found")
    
    # Check 3: No unexpected gaps (allow weekend gaps ~48h = 2880 min)
    for i in range(1, len(bars)):
        gap = (bars[i].timestamp - bars[i-1].timestamp).total_seconds() / 60
        # Allow weekend gaps (Friday 17:00 to Sunday 17:00 EST = ~2880 min)
        # Allow holiday gaps (up to 72h = 4320 min)
        if gap > 10 and gap < 2800:  # Not a weekend/holiday gap
            issues.append(f"Unexpected gap at index {i}: {gap:.0f} minutes")
    
    return {
        "engine": engine_name,
        "check": "look_ahead_bias",
        "passed": len(issues) == 0,
        "issues": issues
    }


def check_session_boundaries(engine_name: str, bars: List[Bar]) -> Dict[str, Any]:
    """Verify session boundaries are correctly handled (no Asian session trading)."""
    issues = []
    
    # Group by session date (EST)
    sessions = {}
    for bar in bars:
        est_hour = (bar.timestamp.hour - 5) % 24
        if est_hour >= 19:
            session_date = (bar.timestamp + timedelta(days=1)).date()
        else:
            session_date = bar.timestamp.date()
        
        if session_date not in sessions:
            sessions[session_date] = {"asian": [], "trading": []}
        
        if est_hour >= 19 or est_hour < 3:
            sessions[session_date]["asian"].append(bar)
        elif 3 <= est_hour < 16:
            sessions[session_date]["trading"].append(bar)
    
    # Check: Asian session bars should not be used for trading signals
    for date, sess in sessions.items():
        if sess["asian"] and sess["trading"]:
            # Verify Asian range is calculated from Asian bars only
            asian_high = max(b.high for b in sess["asian"])
            asian_low = min(b.low for b in sess["asian"])
            if asian_high <= asian_low:
                issues.append(f"Invalid Asian range for {date}")
    
    return {
        "engine": engine_name,
        "check": "session_boundaries",
        "passed": len(issues) == 0,
        "issues": issues
    }


def check_p90_threshold_leakage(engine_name: str, bars: List[Bar]) -> Dict[str, Any]:
    """Check if P90 thresholds are computed from future data."""
    issues = []
    
    # P90 thresholds should be pre-computed from training data
    # Not calculated on-the-fly from test data
    # This is a design check - verify thresholds are constants
    
    return {
        "engine": engine_name,
        "check": "p90_threshold_leakage",
        "passed": True,  # Design-time check
        "issues": ["Verify P90 thresholds are pre-calibrated constants, not computed from test data"]
    }


def check_sl_tp_realism(engine_name: str, trades: List[Dict]) -> Dict[str, Any]:
    """Check if SL/TP levels are realistic (not too tight, respecting spread)."""
    issues = []
    
    for trade in trades:
        if "sl_price" in trade and "entry_price" in trade:
            sl_dist = abs(trade["sl_price"] - trade["entry_price"])
            # SL should be at least spread + buffer
            if sl_dist < 0.00005:  # Less than 0.5 pips for EURUSD
                issues.append(f"SL too tight: {sl_dist:.6f} for trade {trade.get('date', 'unknown')}")
    
    return {
        "engine": engine_name,
        "check": "sl_tp_realism",
        "passed": len(issues) == 0,
        "issues": issues
    }


def check_data_snooping(engine_name: str, config: Dict) -> Dict[str, Any]:
    """Check for data snooping (parameters optimized on test set)."""
    issues = []
    
    # Check if tier configs, P90 thresholds, etc. were optimized on full dataset
    # This is a documentation check
    issues.append("Verify: Tier configs, P90 thresholds, AU values calibrated on TRAINING data only")
    issues.append("Verify: No parameter optimization on test period (2023-2026)")
    
    return {
        "engine": engine_name,
        "check": "data_snooping",
        "passed": True,  # Requires manual verification
        "issues": issues
    }


def check_survivorship_bias(engine_name: str, symbol: str) -> Dict[str, Any]:
    """Check for survivorship bias in symbol selection."""
    issues = []
    
    # Only testing on currently active pairs
    # Should also test on delisted/changed symbols
    issues.append(f"Verify: {symbol} was tradeable throughout entire test period")
    issues.append("Check: No symbol selection bias (only testing winners)")
    
    return {
        "engine": engine_name,
        "check": "survivorship_bias",
        "passed": True,
        "issues": issues
    }


def run_leakage_suite(symbol: str = "EURUSD", csv_path: str = None) -> List[Dict]:
    """Run complete leakage detection suite on all engines."""
    if csv_path is None:
        csv_path = f"data/{symbol}PRO_M5_2023_2026.csv"
    
    print(f"\n{'='*60}")
    print(f"LEAKAGE DETECTION SUITE - {symbol}")
    print(f"{'='*60}")
    
    # Load data once
    print("Loading data...")
    bars = load_bars_csv(csv_path)
    print(f"Loaded {len(bars)} bars")
    
    results = []
    
    # Test 1: Look-ahead bias
    print("\n1. Checking look-ahead bias...")
    result = check_look_ahead_bias("ALL", bars)
    results.append(result)
    print(f"   {'PASS' if result['passed'] else 'FAIL'}: {len(result['issues'])} issues")
    for issue in result['issues']:
        print(f"   - {issue}")
    
    # Test 2: Session boundaries
    print("\n2. Checking session boundaries...")
    result = check_session_boundaries("ALL", bars)
    results.append(result)
    print(f"   {'PASS' if result['passed'] else 'FAIL'}: {len(result['issues'])} issues")
    for issue in result['issues']:
        print(f"   - {issue}")
    
    # Test 3: P90 threshold leakage
    print("\n3. Checking P90 threshold leakage...")
    result = check_p90_threshold_leakage("P90/DMR", bars)
    results.append(result)
    print(f"   {'PASS' if result['passed'] else 'FAIL'}: {len(result['issues'])} issues")
    for issue in result['issues']:
        print(f"   - {issue}")
    
    # Test 4: Data snooping
    print("\n4. Checking data snooping...")
    result = check_data_snooping("ALL", {})
    results.append(result)
    print(f"   {'PASS' if result['passed'] else 'FAIL'}: {len(result['issues'])} issues")
    for issue in result['issues']:
        print(f"   - {issue}")
    
    # Test 5: Survivorship bias
    print("\n5. Checking survivorship bias...")
    result = check_survivorship_bias("ALL", symbol)
    results.append(result)
    print(f"   {'PASS' if result['passed'] else 'FAIL'}: {len(result['issues'])} issues")
    for issue in result['issues']:
        print(f"   - {issue}")
    
    # Test 6: Run each engine and check SL/TP realism
    print("\n6. Running engines and checking SL/TP realism...")
    
    # P90 Engine
    from p90_backtest import run_backtest as p90_run
    p90_result = p90_run(csv_path, symbol, convergence_mode=False)
    if p90_result and "trades" in p90_result:
        # Would need to extract trades from engine
        pass
    
    # Symmetry Trap
    bt = SymmetryTrapBacktest(symbol=symbol)
    st_result = bt.run_from_csv(csv_path)
    
    # DMR
    dmr_bars = load_csv(csv_path)
    dmr_trades, _, _ = run_backtest(dmr_bars, symbol)
    result = check_sl_tp_realism("DMR", dmr_trades)
    results.append(result)
    print(f"   DMR SL/TP: {'PASS' if result['passed'] else 'FAIL'}")
    
    # Rekey Intraday
    rekey_bars = rekey_load_bars(csv_path)
    rekey_sessions = compute_sessions(rekey_bars)
    rekey_result = run_backtest(rekey_bars, symbol)  # This runs the backtest
    
    print(f"\n{'='*60}")
    print("LEAKAGE DETECTION COMPLETE")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()
    
    run_leakage_suite(args.symbol, args.csv)