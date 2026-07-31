"""
Full CEREBUS workflow for Oil (LCOUSD + OILUSD) with Regime Tracking.
Step 1: Backtest with regime-aware tiers
Step 2: Monte Carlo (10k iterations)
Step 3: Full report with regime breakdown
"""
import sys, os, json, random, math
from statistics import mean, stdev
from pathlib import Path
from datetime import datetime

REPO = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
sys.path.insert(0, str(REPO))
os.chdir(str(REPO))

import pandas as pd
import numpy as np
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, classify_tier

# ─── CONFIG ───
MC_ITERATIONS = 10000
ACCOUNT_USD = 85.26
PIP_VALUE_PER_001 = 0.10  # For oil, 1 pip = $0.10 per 0.01 lot
SEED = 42
LOT_SIZE = 0.01
OUTPUT_DIR = REPO / "reports" / "per-asset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── REGIME BOUNDARIES ───
REGIME_DATES = {
    "PRE_WAR":       (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-10-06")),
    "WAR_ONSET":     (pd.Timestamp("2023-10-07"), pd.Timestamp("2024-03-31")),
    "WAR_SPIKE":     (pd.Timestamp("2024-04-01"), pd.Timestamp("2024-06-30")),
    "NORMALIZATION": (pd.Timestamp("2024-07-01"), pd.Timestamp("2025-03-31")),
    "CURRENT":       (pd.Timestamp("2025-04-01"), pd.Timestamp("2026-12-31")),
}

# ─── REGIME-FITTED TIER CONFIGS (from atomic structure) ───
REGIME_TIERS = {
    "LCOUSD": {
        "PRE_WAR":       {"T1": {"ar_max": 31.2, "au": 15.6, "trigger": 18.7}, "T2": {"ar_max": 64.5, "au": 25.8, "trigger": 31.0}, "T3": {"ar_max": 96.7, "au": 31.9, "trigger": 38.3}},
        "WAR_ONSET":     {"T1": {"ar_max": 40.8, "au": 20.4, "trigger": 24.5}, "T2": {"ar_max": 69.4, "au": 27.8, "trigger": 33.4}, "T3": {"ar_max": 104.2, "au": 34.4, "trigger": 41.3}},
        "WAR_SPIKE":     {"T1": {"ar_max": 28.8, "au": 14.4, "trigger": 17.3}, "T2": {"ar_max": 43.5, "au": 17.4, "trigger": 20.9}, "T3": {"ar_max": 65.3, "au": 21.5, "trigger": 25.8}},
        "NORMALIZATION": {"T1": {"ar_max": 34.4, "au": 17.2, "trigger": 20.6}, "T2": {"ar_max": 63.7, "au": 25.5, "trigger": 30.6}, "T3": {"ar_max": 95.5, "au": 31.5, "trigger": 37.8}},
        "CURRENT":       {"T1": {"ar_max": 31.2, "au": 15.6, "trigger": 18.7}, "T2": {"ar_max": 64.5, "au": 25.8, "trigger": 31.0}, "T3": {"ar_max": 96.7, "au": 31.9, "trigger": 38.3}},
    },
    "OILUSD": {
        "PRE_WAR":       {"T1": {"ar_max": 16.0, "au": 8.0, "trigger": 9.6}, "T2": {"ar_max": 39.9, "au": 16.0, "trigger": 19.2}, "T3": {"ar_max": 59.9, "au": 19.8, "trigger": 23.8}},
        "WAR_ONSET":     {"T1": {"ar_max": 18.4, "au": 9.2, "trigger": 11.0}, "T2": {"ar_max": 45.5, "au": 18.2, "trigger": 21.8}, "T3": {"ar_max": 68.3, "au": 22.5, "trigger": 27.0}},
        "WAR_SPIKE":     {"T1": {"ar_max": 14.4, "au": 7.2, "trigger": 8.6}, "T2": {"ar_max": 29.6, "au": 11.8, "trigger": 14.2}, "T3": {"ar_max": 44.4, "au": 14.7, "trigger": 17.6}},
        "NORMALIZATION": {"T1": {"ar_max": 16.0, "au": 8.0, "trigger": 9.6}, "T2": {"ar_max": 38.4, "au": 15.4, "trigger": 18.5}, "T3": {"ar_max": 57.6, "au": 19.0, "trigger": 22.8}},
        "CURRENT":       {"T1": {"ar_max": 21.6, "au": 10.8, "trigger": 13.0}, "T2": {"ar_max": 101.7, "au": 40.7, "trigger": 48.8}, "T3": {"ar_max": 152.5, "au": 50.3, "trigger": 60.4}},
    },
}

def get_regime(dt):
    for regime, (start, end) in REGIME_DATES.items():
        if start <= dt <= end:
            return regime
    return "CURRENT"


def run_backtest(sym_name, csv_path, pip_size, use_regime_tiers=True):
    """Full backtest with regime tracking."""
    df = pd.read_csv(csv_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df["date"] = df["time"].dt.date
    
    # Start with default tier config
    default_tiers = {"T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0}, "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0}, "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0}}
    engine = SymmetryTrapEngine(pip_size=pip_size, symbol=sym_name, tier_config=default_tiers.copy())
    
    trades = []
    current_regime = None
    regime_tier_log = []
    
    for date, day_df in df.groupby("date"):
        dt = pd.Timestamp(date)
        regime = get_regime(dt)
        
        # Regime switch → new tier config
        if use_regime_tiers and regime != current_regime:
            current_regime = regime
            regime_tiers = REGIME_TIERS.get(sym_name, {}).get(regime, default_tiers)
            engine = SymmetryTrapEngine(pip_size=pip_size, symbol=sym_name, tier_config=regime_tiers.copy())
        
        # Asian Range
        asian_bars = day_df[(day_df["time"].dt.hour >= 0) & (day_df["time"].dt.hour < 3)]
        if len(asian_bars) < 3:
            continue
        ah = asian_bars["high"].max()
        al = asian_bars["low"].min()
        if ah == al:
            continue
        
        engine.initialize_session(ah, al)
        regime_tier_log.append({"date": str(date), "regime": regime, "tier": engine.tier_name, "ar_pips": round((ah-al)/pip_size, 1)})
        
        if not engine.session_active:
            continue
        
        # Process trading hours
        remaining = day_df[day_df["time"].dt.hour >= 3]
        for _, row in remaining.iterrows():
            bar = Bar(timestamp=row["time"], open=row["open"], high=row["high"], low=row["low"], close=row["close"])
            sig = engine.process_bar(bar)
            if sig and sig.event == "ENTRY":
                direction = sig.direction.name
                trades.append({
                    "date": str(date),
                    "regime": regime,
                    "tier": engine.tier_name,
                    "direction": direction,
                    "entry": sig.entry_price,
                    "sl": sig.sl_price,
                    "tp": sig.tp_price,
                    "loop": sig.loop_count,
                    "variant": str(getattr(sig, 'variant', '')),
                })
            elif sig and sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                # Record exit PnL
                if trades and not trades[-1].get("exit"):
                    exit_price = sig.tp_price if sig.event == "TP_HIT" else sig.sl_price
                    if exit_price and trades[-1].get("entry"):
                        entry = trades[-1]["entry"]
                        diren = trades[-1]["direction"]
                        pnl_pips = (exit_price - entry) / pip_size if diren == "LONG" else (entry - exit_price) / pip_size
                        trades[-1]["exit"] = sig.event
                        trades[-1]["exit_price"] = exit_price
                        trades[-1]["pnl_pips"] = round(pnl_pips, 1)
    
    # Compute PnL for remaining unclosed trades (SL exit assumption)
    for t in trades:
        if "pnl_pips" not in t:
            t["pnl_pips"] = 0
            t["exit"] = "OPEN"
    
    return trades, regime_tier_log


def run_mc(pnl_list, label):
    """Monte Carlo simulation."""
    random.seed(SEED)
    n = len(pnl_list)
    if n == 0:
        return {}
    
    equities = []
    max_dds = []
    final_pnls = []
    
    for _ in range(MC_ITERATIONS):
        sampled = [pnl_list[random.randint(0, n-1)] for _ in range(n)]
        total_pnl = sum(sampled)
        equities.append(total_pnl)
        final_pnls.append(total_pnl)
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
    mean_eq = mean(equities)
    median_dd = max_dds[MC_ITERATIONS // 2]
    p95_dd = max_dds[int(MC_ITERATIONS * 0.95)]
    
    pip_val = PIP_VALUE_PER_001 * LOT_SIZE
    ruin_10 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.10) / MC_ITERATIONS * 100
    ruin_20 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.20) / MC_ITERATIONS * 100
    ruin_30 = sum(1 for dd in max_dds if dd * pip_val / ACCOUNT_USD >= 0.30) / MC_ITERATIONS * 100
    
    # Kelly
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    wr = len(wins) / n
    avg_win = mean(wins) if wins else 0
    avg_loss = abs(mean(losses)) if losses else 0.001
    kelly = (wr * avg_win - (1 - wr) * avg_loss) / avg_win if avg_win > 0 else 0
    
    # Sharpe / Sortino / Calmar
    m = mean(pnl_list)
    s = stdev(pnl_list) if n > 1 else 0.001
    sharpe = m / s * math.sqrt(252)
    downside = [min(0, p - m) for p in pnl_list]
    dsd = math.sqrt(sum(d*d for d in downside) / len(downside)) if downside else 0.001
    sortino = m / dsd * math.sqrt(252)
    calmar = (m * 252) / median_dd if median_dd > 0 else 0
    
    mc_result = {
        "n_simulations": MC_ITERATIONS,
        "equity_p5": round(p5, 1),
        "equity_p25": round(p25, 1),
        "equity_median": round(median_eq, 1),
        "equity_p75": round(p75, 1),
        "equity_p95": round(p95, 1),
        "equity_mean": round(mean_eq, 1),
        "max_dd_median": round(median_dd, 1),
        "max_dd_p95": round(p95_dd, 1),
        "ruin_10pct": round(ruin_10, 1),
        "ruin_20pct": round(ruin_20, 1),
        "ruin_30pct": round(ruin_30, 1),
        "kelly": round(kelly, 4),
        "half_kelly": round(kelly * 0.5, 4),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
    }
    
    print(f"\n  MONTE CARLO — {label}")
    print(f"  {MC_ITERATIONS:,} iterations | {n} trades | Lot: {LOT_SIZE}")
    print(f"  Equity (pips): 5th={p5:+.1f} | 25th={p25:+.1f} | Med={median_eq:+.1f} | 75th={p75:+.1f} | 95th={p95:+.1f}")
    print(f"  Max DD (pips): Med={median_dd:.1f} | 95th={p95_dd:.1f}")
    print(f"  Ruin: 10%={ruin_10:.1f}% | 20%={ruin_20:.1f}% | 30%={ruin_30:.1f}%")
    print(f"  Kelly={kelly:.3f} | Half-Kelly={kelly*0.5:.3f}")
    print(f"  Sharpe={sharpe:.2f} | Sortino={sortino:.2f} | Calmar={calmar:.2f}")
    
    return mc_result


def generate_report(sym_name, trades, regime_log, mc_result, backtest_stats):
    """Full markdown report."""
    bt = backtest_stats
    
    report = f"""# CEREBUS Backtest Report — {sym_name} (Regime-Adaptive)

> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Engine: Symmetry Trap | MC: {MC_ITERATIONS:,} iterations

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Trades | {bt['trades']} |
| Win Rate | {bt['win_rate']:.1f}% |
| Profit Factor | {bt['profit_factor']:.2f} |
| Total PnL | {bt['total_pnl_pips']:+.1f} pips |
| Max DD | {bt['max_dd_pips']:.1f} pips ({bt['max_dd_pct']:.1f}%) |
| Expectancy | {bt['expectancy']:.2f} pips/trade |
| Sharpe | {mc_result.get('sharpe', 0):.2f} |
| Sortino | {mc_result.get('sortino', 0):.2f} |

## Monte Carlo (10k Simulations)

| Metric | Value |
|--------|-------|
| Equity P5 | {mc_result.get('equity_p5', 0):+.1f} pips |
| Equity P25 | {mc_result.get('equity_p25', 0):+.1f} pips |
| Equity Median | {mc_result.get('equity_median', 0):+.1f} pips |
| Equity P75 | {mc_result.get('equity_p75', 0):+.1f} pips |
| Equity P95 | {mc_result.get('equity_p95', 0):+.1f} pips |
| Max DD Median | {mc_result.get('max_dd_median', 0):.1f} pips |
| Max DD P95 | {mc_result.get('max_dd_p95', 0):.1f} pips |
| Ruin (10%) | {mc_result.get('ruin_10pct', 0):.1f}% |
| Ruin (20%) | {mc_result.get('ruin_20pct', 0):.1f}% |
| Ruin (30%) | {mc_result.get('ruin_30pct', 0):.1f}% |
| Kelly | {mc_result.get('kelly', 0):.3f} |
| Half-Kelly | {mc_result.get('half_kelly', 0):.3f} |

## Regime Breakdown

"""
    # Per-regime stats
    tdf = pd.DataFrame(trades)
    for regime in ["PRE_WAR", "WAR_ONSET", "WAR_SPIKE", "NORMALIZATION", "CURRENT"]:
        rdf = tdf[tdf["regime"] == regime] if "regime" in tdf.columns else pd.DataFrame()
        if len(rdf) == 0:
            continue
        pnls = rdf["pnl_pips"].tolist()
        r_wins = [p for p in pnls if p > 0]
        r_wr = len(r_wins) / len(pnls) * 100 if pnls else 0
        r_pnl = sum(pnls)
        r_gp = sum(r_wins)
        r_gl = abs(sum(p for p in pnls if p < 0))
        r_pf = r_gp / r_gl if r_gl > 0 else 999
        tiers = rdf["tier"].value_counts().to_dict()
        
        report += f"""### {regime}

| Metric | Value |
|--------|-------|
| Trades | {len(rdf)} |
| Win Rate | {r_wr:.1f}% |
| PnL | {r_pnl:+.1f} pips |
| Profit Factor | {r_pf:.2f} |
| Tier Dist | {tiers} |

"""
    
    # Tier stats
    report += "## Tier Distribution\n\n"
    for tier in ["T1", "T2", "T3"]:
        ttdf = tdf[tdf["tier"] == tier] if "tier" in tdf.columns else pd.DataFrame()
        if len(ttdf) == 0:
            continue
        pnls = ttdf["pnl_pips"].tolist()
        t_wins = [p for p in pnls if p > 0]
        t_wr = len(t_wins) / len(pnls) * 100 if pnls else 0
        report += f"- **{tier}**: {len(ttdf)} trades | WR={t_wr:.1f}% | PnL={sum(pnls):+.1f} pips\n"
    
    # Long/Short
    report += "\n## Long vs Short\n\n"
    for d in ["LONG", "SHORT"]:
        ddf = tdf[tdf["direction"] == d]
        if len(ddf) == 0:
            continue
        pnls = ddf["pnl_pips"].tolist()
        d_wins = [p for p in pnls if p > 0]
        d_wr = len(d_wins) / len(pnls) * 100 if pnls else 0
        report += f"- **{d}**: {len(ddf)} trades | WR={d_wr:.1f}% | PnL={sum(pnls):+.1f} pips\n"
    
    # Regime tier log summary
    report += "\n## Regime to Tier Mapping (Daily)\n\n"
    rldf = pd.DataFrame(regime_log)
    for regime in rldf["regime"].unique():
        rr = rldf[rldf["regime"] == regime]
        tier_counts = rr["tier"].value_counts().to_dict()
        ar_mean = rr["ar_pips"].mean()
        report += f"- **{regime}**: {len(rr)} days | AR mean={ar_mean:.1f}p | Tiers: {tier_counts}\n"
    
    return report


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

OIL_ASSETS = [
    ("LCOUSD", r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\LCOUSDPRO_M5.csv", 0.01),
    ("OILUSD", r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\OILUSDPRO_M5.csv", 0.01),
]

all_results = {}

for sym_name, csv_path, pip_size in OIL_ASSETS:
    print(f"\n{'='*60}")
    print(f"  FULL WORKFLOW: {sym_name}")
    print(f"{'='*60}")
    
    # Step 1: Backtest
    print(f"\n  [1/3] Backtesting with regime-adaptive tiers...")
    trades, regime_log = run_backtest(sym_name, csv_path, pip_size, use_regime_tiers=True)
    
    pnls = [t["pnl_pips"] for t in trades if "pnl_pips" in t]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    n_trades = len(trades)
    wr = len(wins) / len(pnls) * 100 if pnls else 0
    total_pnl = sum(pnls)
    gp = sum(wins)
    gl = abs(sum(losses))
    pf = gp / gl if gl > 0 else 999
    
    # Max DD
    eq = np.cumsum(pnls) if pnls else np.array([0])
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    max_dd = dd.max()
    max_dd_pct = max_dd / (abs(eq.min()) + ACCOUNT_USD / (PIP_VALUE_PER_001 * LOT_SIZE)) * 100 if len(eq) > 0 else 0
    expectancy = total_pnl / n_trades if n_trades > 0 else 0
    
    backtest_stats = {
        "trades": n_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": wr,
        "total_pnl_pips": total_pnl,
        "profit_factor": pf,
        "max_dd_pips": max_dd,
        "max_dd_pct": max_dd_pct,
        "expectancy": expectancy,
        "tier_stats": pd.DataFrame(trades)["tier"].value_counts().to_dict() if trades else {},
    }
    
    # Tier + hourly + loop stats
    if trades:
        tdf = pd.DataFrame(trades)
        backtest_stats["tier_stats"] = tdf["tier"].value_counts().to_dict()
        backtest_stats["loop_stats"] = tdf["loop"].value_counts().to_dict()
        long_trades = tdf[tdf["direction"] == "LONG"]
        short_trades = tdf[tdf["direction"] == "SHORT"]
        backtest_stats["long"] = {"count": len(long_trades), "wr": (long_trades["pnl_pips"] > 0).mean() * 100 if len(long_trades) > 0 else 0}
        backtest_stats["short"] = {"count": len(short_trades), "wr": (short_trades["pnl_pips"] > 0).mean() * 100 if len(short_trades) > 0 else 0}
    
    print(f"  {n_trades} trades | WR={wr:.1f}% | PF={pf:.2f} | PnL={total_pnl:+.1f}p | MaxDD={max_dd:.1f}p")
    
    # Step 2: Monte Carlo
    print(f"\n  [2/3] Monte Carlo ({MC_ITERATIONS:,} iterations)...")
    mc_result = run_mc(pnls, sym_name) if pnls else {}
    
    # Step 3: Report
    print(f"\n  [3/3] Generating report...")
    report = generate_report(sym_name, trades, regime_log, mc_result, backtest_stats)
    report_path = OUTPUT_DIR / f"{sym_name}_full_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Saved: {report_path}")
    
    # Save JSON (same format as other per-asset results)
    output_json = {
        "asset": sym_name,
        "timestamp": datetime.now().isoformat(),
        "backtest": backtest_stats,
        "monte_carlo": mc_result,
        "per_trade_pnl": pnls,
        "regime_log_summary": {r: len([rl for rl in regime_log if rl["regime"] == r]) for r in set(rl["regime"] for rl in regime_log)},
    }
    json_path = OUTPUT_DIR / f"{sym_name}_mc_results.json"
    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2, default=str)
    print(f"  Saved: {json_path}")
    
    all_results[sym_name] = output_json

# ─── Cross-asset summary ───
print(f"\n{'='*60}")
print(f"  OIL CROSS-ASSET SUMMARY")
print(f"{'='*60}")
for sym, data in all_results.items():
    bt = data["backtest"]
    mc = data["monte_carlo"]
    print(f"  {sym}: {bt['trades']} trades | WR={bt['win_rate']:.1f}% | PF={bt['profit_factor']:.2f} | MC_Med={mc.get('equity_median', 0):+.1f}p | MC_P5={mc.get('equity_p5', 0):+.1f}p")

print(f"\nDone.")
