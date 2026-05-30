"""
Monte Carlo simulation for CEREBUS FX strategies.
Supports Symmetry Trap, P90, and DMR trade lists.
"""
import csv, random, math, os, sys
from statistics import mean, stdev
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────
MC_ITERATIONS = 10000
ACCOUNT_USD = 85.26
PIP_VALUE_PER_001 = 0.10  # EUR/USD approx $0.10 per 0.01 lot per pip
SEED = 42

def extract_trades_from_csv(csv_path, pnl_col="pnl_pips"):
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                trades.append(float(row[pnl_col]))
            except (ValueError, KeyError):
                continue
    return trades

def monte_carlo(pnl_list, label, lot_size=0.01):
    random.seed(SEED)
    n = len(pnl_list)
    results = []

    for i in range(MC_ITERATIONS):
        sampled = [pnl_list[random.randint(0, n-1)] for _ in range(n)]
        equity = sum(sampled)
        results.append(equity)

    results.sort()

    # Stats
    median_equity = results[MC_ITERATIONS // 2]
    p5 = results[int(MC_ITERATIONS * 0.05)]
    p95 = results[int(MC_ITERATIONS * 0.95)]
    p10 = results[int(MC_ITERATIONS * 0.10)]
    p25 = results[int(MC_ITERATIONS * 0.25)]
    p75 = results[int(MC_ITERATIONS * 0.75)]

    # Max DD distribution
    max_dds = []
    ruin_10 = ruin_20 = ruin_30 = 0
    for _ in range(MC_ITERATIONS):
        sampled = [pnl_list[random.randint(0, n-1)] for _ in range(n)]
        eq = peak = max_dd = 0
        for p in sampled:
            eq += p
            if eq > peak: peak = eq
            dd = peak - eq
            if dd > max_dd: max_dd = dd
        max_dds.append(max_dd)
        pct_loss = max_dd * PIP_VALUE_PER_001 * lot_size / ACCOUNT_USD * 100
        if pct_loss >= 10: ruin_10 += 1
        if pct_loss >= 20: ruin_20 += 1
        if pct_loss >= 30: ruin_30 += 1

    max_dds.sort()
    median_dd = max_dds[MC_ITERATIONS // 2]
    p95_dd = max_dds[int(MC_ITERATIONS * 0.95)]

    # Kelly
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    wr = len(wins) / n if n > 0 else 0
    avg_win = mean(wins) if wins else 0
    avg_loss = abs(mean(losses)) if losses else 0.001
    kelly = wr / avg_loss - (1 - wr) / avg_win if avg_win > 0 else 0

    # Streaks
    max_win_streak = max_loss_streak = 0
    for _ in range(100):  # sample 100 runs for streaks
        sampled = [pnl_list[random.randint(0, n-1)] for _ in range(n)]
        cw = cl = ms = ml = 0
        for p in sampled:
            if p > 0: cw += 1; cl = 0; ms = max(ms, cw)
            elif p < 0: cl += 1; cw = 0; ml = max(ml, cl)
        max_win_streak = max(max_win_streak, ms)
        max_loss_streak = max(max_loss_streak, ml)

    # Sortino (downside deviation)
    returns = pnl_list
    m = mean(returns)
    downside = [min(0, r - m) for r in returns]
    sum_sq = sum(d*d for d in downside)
    dsd = math.sqrt(sum_sq / len(downside)) if downside else 0.001
    sortino = (m / dsd * math.sqrt(252)) if dsd > 0 else 0

    # Calmar
    calmar = (mean(returns) * 252) / median_dd if median_dd > 0 else 0

    print(f"\n{'='*60}")
    print(f"  MONTE CARLO — {label}")
    print(f"  {MC_ITERATIONS:,} iterations | {n} trades | Lot: {lot_size}")
    print(f"{'='*60}")
    print(f"  Equity Distribution (pips):")
    print(f"    5th percentile:  {p5:+.1f}")
    print(f"    10th percentile: {p10:+.1f}")
    print(f"    25th percentile: {p25:+.1f}")
    print(f"    Median:          {median_equity:+.1f}")
    print(f"    75th percentile: {p75:+.1f}")
    print(f"    95th percentile: {p95:+.1f}")
    print(f"  Max DD Distribution:")
    print(f"    Median: {median_dd:.1f}p | 95th: {p95_dd:.1f}p")
    print(f"  Risk of Ruin (lot={lot_size}, account=${ACCOUNT_USD}):")
    print(f"    10% drawdown: {ruin_10/MC_ITERATIONS*100:.1f}% of runs")
    print(f"    20% drawdown: {ruit_20/MC_ITERATIONS*100:.1f}% of runs" if False else f"    20% drawdown: {ruin_20/MC_ITERATIONS*100:.1f}% of runs")
    print(f"    30% drawdown: {ruin_30/MC_ITERATIONS*100:.1f}% of runs")
    print(f"  Kelly Criterion: {kelly:.2f} ({kelly*100:.1f}%)")
    print(f"  Half-Kelly: {kelly*0.5:.2f} ({kelly*50:.1f}%)")
    print(f"  Sortino Ratio: {sortino:.2f}")
    print(f"  Calmar Ratio: {calmar:.2f}")
    print(f"  Avg Win Streak (sample): {max_win_streak}")
    print(f"  Avg Loss Streak (sample): {max_loss_streak}")

    return {
        "p5": p5, "median": median_equity, "p95": p95,
        "median_dd": median_dd, "p95_dd": p95_dd,
        "ruin_10": ruin_10/MC_ITERATIONS*100,
        "ruin_20": ruin_20/MC_ITERATIONS*100,
        "ruin_30": ruin_30/MC_ITERATIONS*100,
        "kelly": kelly, "sortino": sortino, "calmar": calmar,
    }

if __name__ == "__main__":
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

    # Symmetry Trap — need to generate trades from backtest
    # Re-run backtest and capture trades
    print("Generating Symmetry Trap trade list from backtest...")
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines"))
    from symmetry_trap_backtest import SymmetryTrapBacktest
    import io

    bt = SymmetryTrapBacktest(pip_size=0.0001, symbol="EURUSD")
    result = bt.run_from_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "EURUSDPRO_M5_2023_2026.csv"))
    st_pnls = [t.pnl_pips for t in result.trades]
    print(f"Symmetry Trap: {len(st_pnls)} trades extracted")

    # P90
    print("Generating P90 trade list from backtest...")
    from p90_backtest import P90Backtest, load_bars_csv, group_by_session, calc_asian_range
    from p90_engine import P90Engine, P90Signal, P90Variant

    # Simpler: extract from backtest report — use signal_log
    p90_bars = load_bars_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "EURUSDPRO_M5_2023_2026.csv"))
    p90_sessions = group_by_session(p90_bars)
    engine = P90Engine(pip_size=0.0001, symbol="EURUSD")

    completed_signals = []
    for sd, sess in sorted(p90_sessions.items()):
        ah, al = calc_asian_range(sess["asian"])
        engine.initialize_session(ah, al)
        for bar in sess["trading"]:
            sig = engine.process_bar(bar)
            if sig and sig.event in ("TP_HIT", "SL_HIT", "EWS_EXIT", "12PM_EXIT"):
                completed_signals.append(sig)

    p90_pnls = []
    for sig in completed_signals:
        if sig.entry_price is None:
            continue
        if sig.event == "TP_HIT":
            exit_p = sig.tp_price
        elif sig.event == "SL_HIT":
            exit_p = sig.sl_price
        else:
            exit_p = sig.tp_price
        if exit_p is None:
            continue
        if sig.direction.name == "LONG":
            pnl = (exit_p - sig.entry_price) / 0.0001
        else:
            pnl = (sig.entry_price - exit_p) / 0.0001
        p90_pnls.append(round(pnl, 1))
    print(f"P90: {len(p90_pnls)} trades extracted")

    # DMR
    dmr_pnls = extract_trades_from_csv(os.path.join(reports_dir, "dmr_standalone_trades.csv"))
    print(f"DMR: {len(dmr_pnls)} trades extracted")

    # Run MC for each
    print("\n" + "="*60)
    print("  CEREBUS FX — MONTE CARLO SIMULATIONS")
    print(f"  {MC_ITERATIONS:,} iterations | Account: ${ACCOUNT_USD}")
    print("="*60)

    mc_st = monte_carlo(st_pnls, "SYMMETRY TRAP", lot_size=0.03)
    mc_p90 = monte_carlo(p90_pnls, "P90 KINETIC ENGINE", lot_size=0.03)
    mc_dmr = monte_carlo(dmr_pnls, "DMR (STANDALONE)", lot_size=0.03)
