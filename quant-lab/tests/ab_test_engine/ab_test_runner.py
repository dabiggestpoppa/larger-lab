"""
A/B TEST RUNNER — Uses COPIED engine to preserve original
==========================================================

Test A: Pure Option B (no 4h timeout, no 80% kill, flat 20-50% DZ)
Test B: Current engine (all extras active) — imports from ORIGINAL engines/

The copied engine in this directory is modified for Test A.
The original engine in quant-lab/engines/ is NEVER touched.

This way, if anything goes wrong, the original engine is preserved.
"""
import sys, os

# ── PATH SETUP ──────────────────────────────────────────────────────────
# Test A uses the COPIED engine in this directory (ab_test_engine/)
# Test B uses the ORIGINAL engine in quant-lab/engines/
AB_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
QUANTLAB_ROOT = os.path.abspath(os.path.join(AB_TEST_DIR, '..', '..'))
ENGINES_ORIGINAL = os.path.join(QUANTLAB_ROOT, 'engines')
CONFIGS_DIR = os.path.join(QUANTLAB_ROOT, 'configs')

sys.path.insert(0, AB_TEST_DIR)       # For Test A (copied engine)
sys.path.insert(0, ENGINES_ORIGINAL)  # For Test B (original engine)
sys.path.insert(0, CONFIGS_DIR)

# ── DATA ────────────────────────────────────────────────────────────────
CSV_PATH = os.path.join(QUANTLAB_ROOT, 'data', 'EURUSD_M5.csv')

# EURUSD tier config
EURUSD_TIERS = {
    "T1": {"ar_max": 20.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 30.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 45.0, "trigger": 19.0, "au": 15.0},
}
EURUSD_CONFIG = {"pip_value": 0.0001, "tiers": EURUSD_TIERS}


def run_test_b_original():
    """Test B: Run with ORIGINAL engine (quant-lab/engines/symmetry_trap.py)."""
    # Import from ORIGINAL engine directory
    # We manipulate sys.path so 'import symmetry_trap' resolves to the original
    import importlib
    
    # Remove ab_test_engine from path temporarily so original is found first
    original_path = sys.path.copy()
    if AB_TEST_DIR in sys.path:
        sys.path.remove(AB_TEST_DIR)
    
    # Clear any cached modules from previous imports
    for key in list(sys.modules.keys()):
        if 'symmetry_trap' in key or 'symmetry_trap_backtest' in key:
            del sys.modules[key]
    
    # Now import from original
    import symmetry_trap as st_orig
    from symmetry_trap_backtest import SymmetryTrapBacktest
    
    # Restore path
    sys.path[:] = original_path
    
    print("=" * 60)
    print("TEST B — ORIGINAL ENGINE (from quant-lab/engines/)")
    print("  4h timeout: ON | 80% kill: ON | Dynamic DZ: ON")
    print("=" * 60)
    sys.stdout.flush()
    
    bt = SymmetryTrapBacktest(
        pip_size=0.0001,
        tier_config=EURUSD_TIERS,
        symbol="EURUSD_B",
        config=EURUSD_CONFIG
    )
    result = bt.run_from_csv(CSV_PATH)
    
    td = result.total_trades
    days = result.data_days
    wr = result.win_rate
    pnl = result.total_pnl_pips
    pf = result.profit_factor
    dd = result.max_drawdown_pct
    avg_w = result.avg_win_pips
    avg_l = result.avg_loss_pips
    exp = result.expectancy_pips
    tier = {t: sum(1 for tr in result.trades if getattr(tr, 'tier', '') == t) for t in ['T1', 'T2', 'T3']}
    loops = result.loop_stats or {}
    
    print("Trades: {} | Days: {} | {:.3f} tr/day".format(td, days, td/days if days else 0))
    print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr, pnl, pf, dd))
    print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_w, avg_l, exp))
    print("Tiers: {}".format(tier))
    for i in range(1, 6):
        ls = loops.get(i, {})
        if ls:
            print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(
                i, ls.get('trades', 0), ls.get('wr', 0), ls.get('pnl', 0)))
    sys.stdout.flush()
    
    return {
        'td': td, 'days': days, 'wr': wr, 'pnl': pnl,
        'pf': pf, 'dd': dd, 'avg_w': avg_w, 'avg_l': avg_l,
        'exp': exp, 'tier': tier, 'loops': loops
    }


def run_test_a_pure():
    """Test A: Run with COPIED engine (ab_test_engine/symmetry_trap.py — Pure Option B)."""
    import importlib
    
    # Clear cached modules
    for key in list(sys.modules.keys()):
        if 'symmetry_trap' in key or 'symmetry_trap_backtest' in key:
            del sys.modules[key]
    
    # Import from ab_test_engine (copied engine with extras disabled)
    # ab_test_engine is already first in sys.path
    import symmetry_trap as st_pure
    from symmetry_trap_backtest import SymmetryTrapBacktest
    
    print("\n" + "=" * 60)
    print("TEST A — PURE OPTION B (from ab_test_engine/)")
    print("  4h timeout: OFF | 80% kill: OFF | Flat 20-50% DZ")
    print("=" * 60)
    sys.stdout.flush()
    
    bt = SymmetryTrapBacktest(
        pip_size=0.0001,
        tier_config=EURUSD_TIERS,
        symbol="EURUSD_A",
        config=EURUSD_CONFIG
    )
    result = bt.run_from_csv(CSV_PATH)
    
    td = result.total_trades
    days = result.data_days
    wr = result.win_rate
    pnl = result.total_pnl_pips
    pf = result.profit_factor
    dd = result.max_drawdown_pct
    avg_w = result.avg_win_pips
    avg_l = result.avg_loss_pips
    exp = result.expectancy_pips
    tier = {t: sum(1 for tr in result.trades if getattr(tr, 'tier', '') == t) for t in ['T1', 'T2', 'T3']}
    loops = result.loop_stats or {}
    
    print("Trades: {} | Days: {} | {:.3f} tr/day".format(td, days, td/days if days else 0))
    print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr, pnl, pf, dd))
    print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_w, avg_l, exp))
    print("Tiers: {}".format(tier))
    for i in range(1, 6):
        ls = loops.get(i, {})
        if ls:
            print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(
                i, ls.get('trades', 0), ls.get('wr', 0), ls.get('pnl', 0)))
    sys.stdout.flush()
    
    return {
        'td': td, 'days': days, 'wr': wr, 'pnl': pnl,
        'pf': pf, 'dd': dd, 'avg_w': avg_w, 'avg_l': avg_l,
        'exp': exp, 'tier': tier, 'loops': loops
    }


def compare(results_a, results_b):
    """Print A/B comparison table."""
    print("\n" + "=" * 60)
    print("A/B COMPARISON")
    print("=" * 60)
    print("{:<25} {:>12} {:>12}".format("Metric", "Pure A", "Current B"))
    print("{:<25} {:>12} {:>12}".format("------", "-------", "-------"))
    print("{:<25} {:>12} {:>12}".format("Trades", results_a['td'], results_b['td']))
    print("{:<25} {:>12.3f} {:>12.3f}".format("Tr/day",
        results_a['td']/results_a['days'] if results_a['days'] else 0,
        results_b['td']/results_b['days'] if results_b['days'] else 0))
    print("{:<25} {:>11.1f}% {:>11.1f}%".format("WR", results_a['wr'], results_b['wr']))
    print("{:<25} {:>12.1f} {:>12.1f}".format("PnL (pips)", results_a['pnl'], results_b['pnl']))
    print("{:<25} {:>12.2f} {:>12.2f}".format("Profit Factor", results_a['pf'], results_b['pf']))
    print("{:<25} {:>11.1f}% {:>11.1f}%".format("Max DD", results_a['dd'], results_b['dd']))
    print("{:<25} {:>12.1f} {:>12.1f}".format("Avg Win", results_a['avg_w'], results_b['avg_w']))
    print("{:<25} {:>12.1f} {:>12.1f}".format("Avg Loss", results_a['avg_l'], results_b['avg_l']))
    print("{:<25} {:>12.1f} {:>12.1f}".format("Expectancy", results_a['exp'], results_b['exp']))
    
    diff = results_a['td'] - results_b['td']
    pct = (results_a['td']/results_b['td'] - 1)*100 if results_b['td'] else 0
    print("\nTrade count delta: {} ({:+.1f}%)".format(diff, pct))
    if diff > 50:
        print(">>> Pure Option B produces SIGNIFICANTLY MORE trades")
        print(">>> The 3 extras ARE suppressing trade frequency")
    elif diff > 0:
        print(">>> Pure Option B produces slightly more trades")
    elif diff < -50:
        print(">>> Current engine produces SIGNIFICANTLY MORE trades")
    elif diff < 0:
        print(">>> Current engine produces slightly more trades")
    else:
        print(">>> IDENTICAL trade count — extras have zero impact")


if __name__ == '__main__':
    print("A/B TEST — Engine Copy Method (Original Preserved)")
    print("Test A: ab_test_engine/symmetry_trap.py (Pure Option B)")
    print("Test B: quant-lab/engines/symmetry_trap.py (Original)")
    print("Data: EURUSD M5")
    print("")
    
    # Run Test B first (original engine)
    results_b = run_test_b_original()
    
    # Run Test A (copied engine with extras disabled)
    results_a = run_test_a_pure()
    
    # Compare
    compare(results_a, results_b)
