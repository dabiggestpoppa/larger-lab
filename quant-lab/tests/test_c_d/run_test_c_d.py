"""
TEST C + TEST D — Isolate the real bottlenecks
================================================
Uses COPIED engine in test_c_d/ to preserve original.

TEST C: AR Gate Bypass (ar_max=999 for all tiers, original triggers, 12PM cutoff)
TEST D: Low Triggers + 4PM Cutoff (8/10/13p triggers, original ar_max, 4PM cutoff)
TEST C+D: Combined (no AR gate + low triggers + 4PM cutoff)

Baseline: 1,125 tr | 84.6% WR | +5,100p | PF 8.18
"""
import sys, os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEST_DIR)

from symmetry_trap import DEFAULT_TIER_CONFIG, TEST_CD_TIER_CONFIG
from symmetry_trap_backtest import SymmetryTrapBacktest

CSV_PATH = os.path.join(TEST_DIR, '..', '..', 'data', 'EURUSD_M5.csv')

# Original tiers for reference
ORIGINAL_TIERS = DEFAULT_TIERS = {
    "T1": {"ar_max": 20.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 30.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 45.0, "trigger": 19.0, "au": 15.0},
}

# Test C: AR gate removed, original triggers
TEST_C_TIERS = {
    "T1": {"ar_max": 999.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 999.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 999.0, "trigger": 19.0, "au": 15.0},
}

# Test D: Original AR gate, low triggers
TEST_D_TIERS = {
    "T1": {"ar_max": 20.0, "trigger": 8.0, "au": 6.0},
    "T2": {"ar_max": 30.0, "trigger": 10.0, "au": 8.0},
    "T3": {"ar_max": 45.0, "trigger": 13.0, "au": 10.0},
}

# Test C+D: No AR gate + low triggers
TEST_CD_TIERS = TEST_CD_TIERS = {
    "T1": {"ar_max": 999.0, "trigger": 8.0, "au": 6.0},
    "T2": {"ar_max": 999.0, "trigger": 10.0, "au": 8.0},
    "T3": {"ar_max": 999.0, "trigger": 13.0, "au": 10.0},
}


def run_test(label, tiers, session_cutoff=12):
    bt = SymmetryTrapBacktest(
        pip_size=0.0001,
        tier_config=tiers,
        symbol="EURUSD",
        config={"pip_value": 0.0001, "tiers": tiers}
    )
    bt.session_cutoff = session_cutoff
    
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
    
    print("{}".format("=" * 60))
    print(label)
    print("=" * 60)
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
    
    return {'td': td, 'days': days, 'wr': wr, 'pnl': pnl, 'pf': pf, 'dd': dd,
            'avg_w': avg_w, 'avg_l': avg_l, 'exp': exp, 'tier': tier}


if __name__ == '__main__':
    print("TEST C + D — Isolating Real Bottlenecks")
    print("Baseline: 1,125 tr | 84.6% WR | +5,100p | PF 8.18 | 1,341 days")
    print("")
    
    # TEST C: AR gate removed
    results_c = run_test(
        "TEST C — AR Gate Removed (ar_max=999, orig triggers, 12PM cutoff)",
        TEST_C_TIERS, session_cutoff=12
    )
    
    # TEST D: Low triggers + 4PM cutoff
    results_d = run_test(
        "TEST D — Low Triggers (8/10/13p) + 4PM Cutoff (orig AR gate)",
        TEST_D_TIERS, session_cutoff=16
    )
    
    # TEST C+D: Combined
    results_cd = run_test(
        "TEST C+D — No AR Gate + Low Triggers + 4PM Cutoff",
        TEST_CD_TIERS, session_cutoff=16
    )
    
    # ── COMPARISON ──
    baseline = {'td': 1125, 'days': 1341, 'wr': 84.6, 'pnl': 5100.0, 'pf': 8.18, 'exp': 4.5}
    
    print("\n{}".format("=" * 75))
    print("COMPARISON vs BASELINE (1,125 tr | 84.6% WR | +5,100p | PF 8.18)")
    print("=" * 75)
    print("{:<35} {:>8} {:>8} {:>10} {:>8} {:>8}".format(
        "Test", "Trades", "WR%", "PnL(pips)", "PF", "Exp"))
    print("{:<35} {:>8} {:>8} {:>10} {:>8} {:>8}".format(
        "------", "-------", "----", "---------", "--", "---"))
    print("{:<35} {:>8} {:>8.1f} {:>10.1f} {:>8.2f} {:>8.1f}".format(
        "Baseline", baseline['td'], baseline['wr'], baseline['pnl'], baseline['pf'], baseline['exp']))
    
    for lbl, r in [
        ("C: No AR gate", results_c),
        ("D: Low trig + 4PM", results_d),
        ("C+D: Combined", results_cd)
    ]:
        print("{:<35} {:>8} {:>8.1f} {:>10.1f} {:>8.2f} {:>8.1f}".format(
            lbl, r['td'], r['wr'], r['pnl'], r['pf'], r['exp']))
    
    print("\n--- Delta vs Baseline ---")
    for lbl, r in [
        ("C: No AR gate", results_c),
        ("D: Low trig + 4PM", results_d),
        ("C+D: Combined", results_cd)
    ]:
        d_tr = r['td'] - baseline['td']
        d_pnl = r['pnl'] - baseline['pnl']
        d_pf = r['pf'] - baseline['pf']
        print("{}: {:+d} trades ({:+.1f}%) | {:+.1f}p PnL | PF {:+.2f} | WR {:+.1f}%".format(
            lbl, d_tr, (d_tr/baseline['td']*100) if baseline['td'] else 0,
            d_pnl, d_pf, r['wr'] - baseline['wr']))
