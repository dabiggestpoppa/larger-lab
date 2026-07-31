"""Monte Carlo for CEREBUS FX — all 3 engines"""
import csv, random, math, os, sys
from statistics import mean, stdev
from pathlib import Path

MC_ITERATIONS = 10000
ACCOUNT_USD = 85.26
PIP_VALUE_PER_001 = 0.10
SEED = 42

def mc_sim(pnl_list, label, lot_size=0.01):
    random.seed(SEED)
    n = len(pnl_list)
    equities = []
    max_dds = []
    for _ in range(MC_ITERATIONS):
        sampled = [pnl_list[random.randint(0, n-1)] for _ in range(n)]
        equities.append(sum(sampled))
        running = peak = max_dd = 0
        for p in sampled:
            running += p
            if running > peak: peak = running
            dd = peak - running
            if dd > max_dd: max_dd = dd
        max_dds.append(max_dd)
    equities.sort()
    max_dds.sort()
    median_eq = equities[MC_ITERATIONS // 2]
    p5 = equities[int(MC_ITERATIONS * 0.05)]
    p95 = equities[int(MC_ITERATIONS * 0.95)]
    p25 = equities[int(MC_ITERATIONS * 0.25)]
    p75 = equities[int(MC_ITERATIONS * 0.75)]
    median_dd = max_dds[MC_ITERATIONS // 2]
    p95_dd = max_dds[int(MC_ITERATIONS * 0.95)]
    pip_val = PIP_VALUE_PER_001 * lot_size
    ruin_10 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.10) / MC_ITERATIONS * 100
    ruin_20 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.20) / MC_ITERATIONS * 100
    ruin_30 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.30) / MC_ITERATIONS * 100
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    wr = len(wins) / n if n > 0 else 0
    avg_win = mean(wins) if wins else 0
    avg_loss = abs(mean(losses)) if losses else 0.001
    kelly = (wr * avg_win - (1 - wr) * avg_loss) / avg_win if avg_win > 0 else 0
    m = mean(pnl_list)
    s = stdev(pnl_list) if len(pnl_list) > 1 else 0.001
    sharpe = m / s * math.sqrt(252)
    downside = [min(0, p - m) for p in pnl_list]
    dsd = math.sqrt(sum(d*d for d in downside) / len(downside)) if downside else 0.001
    sortino = m / dsd * math.sqrt(252)
    calmar = (m * 252) / median_dd if median_dd > 0 else 0
    print(f"\n{'='*60}")
    print(f"  MONTE CARLO — {label}")
    print(f"  {MC_ITERATIONS:,} iterations | {n} trades | Lot: {lot_size}")
    print(f"{'='*60}")
    print(f"  Equity (pips): 5th={p5:+.1f} | 25th={p25:+.1f} | Median={median_eq:+.1f} | 75th={p75:+.1f} | 95th={p95:+.1f}")
    print(f"  Max DD (pips): Median={median_dd:.1f} | 95th={p95_dd:.1f}")
    print(f"  Ruin Prob (lot={lot_size}): 10%={ruin_10:.1f}% | 20%={ruin_20:.1f}% | 30%={ruin_30:.1f}%")
    print(f"  Kelly: {kelly:.3f} ({kelly*100:.1f}%) | Half-Kelly: {kelly*0.5:.3f}")
    print(f"  Sharpe: {sharpe:.2f} | Sortino: {sortino:.2f} | Calmar: {calmar:.2f}")
    return {"p5": p5, "median": median_eq, "p95": p95, "median_dd": median_dd, "p95_dd": p95_dd,
            "ruin_10": ruin_10, "ruin_20": ruin_20, "ruin_30": ruin_30,
            "kelly": kelly, "sortino": sortino, "calmar": calmar, "sharpe": sharpe}

base = Path(__file__).parent
data_dir = base / "data"
eng_reports = base / "engines" / "reports"

# Symmetry Trap
print("ST backtest...")
sys.path.insert(0, str(base / "engines"))
from symmetry_trap_backtest import SymmetryTrapBacktest
bt_st = SymmetryTrapBacktest(pip_size=0.0001, symbol="EURUSD")
st_result = bt_st.run_from_csv(str(data_dir / "EURUSDPRO_M5_2023_2026.csv"))
st_pnls = [t.pnl_pips for t in st_result.trades]
print(f"  ST: {len(st_pnls)} trades, WR={st_result.win_rate:.1f}%, PF={st_result.profit_factor:.2f}")

# P90
print("P90 backtest...")
from p90_backtest import load_bars_csv, group_by_session, calc_asian_range
from p90_engine import P90Engine
p90_bars = load_bars_csv(str(data_dir / "EURUSDPRO_M5_2023_2026.csv"))
p90_sessions = group_by_session(p90_bars)
engine = P90Engine(pip_size=0.0001, symbol="EURUSD")
p90_pnls = []
for sd, sess in sorted(p90_sessions.items()):
    ah, al = calc_asian_range(sess["asian"])
    engine.initialize_session(ah, al)
    for bar in sess["trading"]:
        sig = engine.process_bar(bar)
        if sig and sig.event in ("TP_HIT", "SL_HIT", "EWS_EXIT", "12PM_EXIT"):
            if sig.entry_price is None: continue
            exit_p = sig.tp_price if sig.event == "TP_HIT" else sig.sl_price
            if exit_p is None: continue
            pnl = (exit_p - sig.entry_price) / 0.0001 if sig.direction.name == "LONG" else (sig.entry_price - exit_p) / 0.0001
            p90_pnls.append(round(pnl, 1))
p90_wr = sum(1 for p in p90_pnls if p > 0) / len(p90_pnls) * 100 if p90_pnls else 0
print(f"  P90: {len(p90_pnls)} trades, WR={p90_wr:.1f}%")

# DMR
print("DMR backtest...")
dmr_csv = eng_reports / "dmr_standalone_trades.csv"
dmr_pnls = []
with open(dmr_csv) as f:
    for row in csv.DictReader(f):
        dmr_pnls.append(float(row["pnl_pips"]))
dmr_wr = sum(1 for p in dmr_pnls if p > 0) / len(dmr_pnls) * 100 if dmr_pnls else 0
print(f"  DMR: {len(dmr_pnls)} trades, WR={dmr_wr:.1f}%")

# Run MC
print("\n" + "="*60)
print(f"  CEREBUS FX — MONTE CARLO ({MC_ITERATIONS:,} iterations) | Account: ${ACCOUNT_USD}")
print("="*60)
mc_st = mc_sim(st_pnls, "SYMMETRY TRAP", lot_size=0.03)
mc_p90 = mc_sim(p90_pnls, "P90 KINETIC ENGINE", lot_size=0.03)
mc_dmr = mc_sim(dmr_pnls, "DMR (STANDALONE)", lot_size=0.03)
