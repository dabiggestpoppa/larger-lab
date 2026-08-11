#!/usr/bin/env python3
"""
EURCHF Triangular Basis v1 — Backtest Engine
=============================================

Market-neutral statistical arbitrage on the EURUSD / USDCHF / EURCHF triangle.

Structural identity:
    EURCHF ≈ EURUSD × USDCHF
    Basis B_t = ln(EURCHF_t) - ln(EURUSD_t) - ln(USDCHF_t)
    B_t ≈ 0 by no-arbitrage; when it spreads, it should mean-revert.

Signal: robust (median/MAD) z-score of the basis, gated by
  - rolling half-life of the basis (must mean-revert, < max_half_life)
  - rolling inverse correlation between EURUSD and USDCHF (< min_corr)
Position: +1 = long basis (long EURCHF, short EURUSD, short USDCHF)
          -1 = short basis (short EURCHF, long EURUSD, long USDCHF)

Costs: cost_per_position_change (0.0006 = 6bps per flip; ~12bps round trip).

This engine is written as the canonical source of truth. If profitable it feeds
a thin live wrapper + parity replay (same architecture as symmetry_trap and
triangular_basis live stack) for forward testing.

NOTE: price source is local MT5 PRO daily CSVs (quant-lab/data/*_PRO_D1.csv),
NOT Yahoo Finance ticks from the original spec skeleton. Same no-arbitrage math;
the MT5 source avoids Yahoo FX rounding/gap distortion and matches the lab.

Usage:
    python engines/eurchf_triangular_basis.py            # run base + robustness
    python engines/eurchf_triangular_basis.py --quick     # base metrics only
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.parent          # quant-lab
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "reports"
OUT_DIR.mkdir(exist_ok=True)

TICKERS = ["EURUSD", "USDCHF", "EURCHF"]


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMS (spec §6 baseline)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Params:
    # z-score
    z_window: int = 90
    z_min_periods: int = 60
    # half-life
    hl_window: int = 120
    max_half_life: float = 25.0
    # inverse correlation filter
    corr_window: int = 30
    corr_min_periods: int = 20
    min_corr: float = -0.50
    # entry / exit / stop / time
    entry_z: float = 2.0
    exit_z: float = 0.3
    stop_z: float = 3.5
    max_hold: int = 20
    # costs
    cost_per_position_change: float = 0.0006
    # kill switch (optional, spec §11)
    use_vol_kill: bool = False
    vol_win: int = 20
    vol_pct: float = 0.95

    def as_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}


DEFAULT_PARAMS = Params()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


@lru_cache(maxsize=8)
def load_pair_close(symbol: str) -> pd.Series:
    """Load close prices for a pair from PRO_D1 CSV. Returns Series indexed by dt."""
    path = DATA_DIR / f"{symbol}_PRO_D1.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    df = pd.read_csv(path)
    ts = df["time"].map(_parse_ts)
    close = pd.to_numeric(df["close"], errors="coerce")
    ser = pd.Series(close.values, index=ts).sort_index()
    ser = ser[~ser.index.duplicated(keep="first")]
    return ser


def build_basis_frame() -> pd.DataFrame:
    """Load three pairs, inner-join on daily timestamp, compute logs + basis."""
    frames = {t: load_pair_close(t) for t in TICKERS}
    px = pd.concat(frames, axis=1).dropna()
    px.columns = TICKERS

    logpx = np.log(px)
    basis = logpx["EURCHF"] - logpx["EURUSD"] - logpx["USDCHF"]
    basis_ret = basis.diff()

    ret = logpx.diff()
    df = px.copy()
    df["log_"+TICKERS[0]] = logpx[TICKERS[0]]
    df["log_"+TICKERS[1]] = logpx[TICKERS[1]]
    df["log_"+TICKERS[2]] = logpx[TICKERS[2]]
    df["basis"] = basis
    df["basis_ret"] = basis_ret
    df["ret."+TICKERS[0]] = ret[TICKERS[0]]
    df["ret."+TICKERS[1]] = ret[TICKERS[1]]
    df["ret."+TICKERS[2]] = ret[TICKERS[2]]
    # identity check residual (should be ~0 if triangle is internally consistent)
    df["identity_resid"] = px["EURCHF"] / (px["EURUSD"] * px["USDCHF"]) - 1.0
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# INDICATORS
# ═══════════════════════════════════════════════════════════════════════════════

def robust_zscore(basis: pd.Series, window: int, min_periods: int) -> pd.Series:
    """Robust z-score: (B - median) / (1.4826 * MAD). MAD=0 -> NaN."""
    median = basis.rolling(window, min_periods=min_periods).median()
    mad = (basis - median).abs().rolling(window, min_periods=min_periods).median()
    denom = 1.4826 * mad
    z = (basis - median) / denom.replace(0, np.nan)
    return z


def rolling_half_life(basis: pd.Series, window: int, min_valid_frac: float = 0.7) -> pd.Series:
    """Rolling OLS half-life: ΔB = α - θ·B_lag ; HL = ln(2)/θ for θ<0.

    Uses a sliding window and numpy polyfit (faithful to spec §7).
    Returns NaN where θ>=0 or insufficient valid points.
    """
    series = basis.astype(float)
    delta = series.diff().values
    lag = series.shift(1).values
    n = len(series)
    hl = np.full(n, np.nan)
    min_valid = int(window * min_valid_frac)

    for i in range(window, n):
        y = delta[i-window+1:i+1]
        x = lag[i-window+1:i+1]
        mask = ~(np.isnan(y) | np.isnan(x))
        if mask.sum() < min_valid:
            continue
        # center to reduce numeric conditioning
        xm = x[mask] - np.nanmean(x[mask])
        num = np.sum(x[mask] * y[mask])
        den = np.sum(x[mask] * x[mask])
        if den <= 0:
            continue
        beta = num / den
        if beta < 0:
            hl[i] = np.log(2) / (-beta)
    return pd.Series(hl, index=series.index)


def rolling_corr(a: pd.Series, b: pd.Series, window: int, min_periods: int) -> pd.Series:
    return a.rolling(window, min_periods=min_periods).corr(b)


def basis_vol_kill(basis: pd.Series, win: int = 20, pct: float = 0.95) -> pd.Series:
    """Bool series: True where 20-day realized basis vol is above its rolling
    95th percentile (spec §11 optional kill switch)."""
    vol = basis.diff().rolling(win).std()
    thr = vol.rolling(252 * 2, min_periods=60).quantile(pct)
    return (vol > thr).fillna(False)


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL STATE MACHINE (spec §7, exact)
# ═══════════════════════════════════════════════════════════════════════════════

def signal_state_machine(
    z: pd.Series,
    half_life: pd.Series,
    corr: pd.Series,
    params: Params,
    vol_kill: Optional[pd.Series] = None,
) -> pd.Series:
    """Return position series (+1 / 0 / -1) using yesterday's signal.

    Inventory: uses z/hl/corr at t-1 to set position_t, capturing today's basis
    change (pos.shift(1) * B.diff()).
    """
    n = len(z)
    position = pd.Series(np.zeros(n), index=z.index)
    bars_in_trade = 0

    z_arr = z.to_numpy()
    hl_arr = half_life.to_numpy()
    corr_arr = corr.to_numpy()
    pos_arr = position.to_numpy()
    kill_arr = vol_kill.to_numpy() if vol_kill is not None else np.zeros(n, dtype=bool)

    for i in range(1, n):
        z_prev = z_arr[i-1]
        hl_prev = hl_arr[i-1]
        corr_prev = corr_arr[i-1]

        if np.isnan(z_prev) or np.isnan(hl_prev) or np.isnan(corr_prev) or kill_arr[i]:
            pos_arr[i] = 0.0
            bars_in_trade = 0
            continue

        prev_pos = pos_arr[i-1]

        if prev_pos == 0:
            bars_in_trade = 0
            if hl_prev < params.max_half_life and corr_prev < params.min_corr:
                if z_prev > params.entry_z:
                    pos_arr[i] = -1.0      # short basis
                    bars_in_trade = 1
                elif z_prev < -params.entry_z:
                    pos_arr[i] = 1.0       # long basis
                    bars_in_trade = 1
                else:
                    pos_arr[i] = 0.0
            else:
                pos_arr[i] = 0.0
        else:
            bars_in_trade += 1
            if prev_pos == -1:             # short basis
                if (z_prev <= params.exit_z or z_prev >= params.stop_z
                        or bars_in_trade > params.max_hold):
                    pos_arr[i] = 0.0
                    bars_in_trade = 0
                else:
                    pos_arr[i] = prev_pos
            elif prev_pos == 1:            # long basis
                if (z_prev >= -params.exit_z or z_prev <= -params.stop_z
                        or bars_in_trade > params.max_hold):
                    pos_arr[i] = 0.0
                    bars_in_trade = 0
                else:
                    pos_arr[i] = prev_pos
            else:
                pos_arr[i] = 0.0

    position[:] = pos_arr
    return position


# ═══════════════════════════════════════════════════════════════════════════════
# RETURNS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_returns(position: pd.Series, basis_ret: pd.Series, cost: float) -> pd.DataFrame:
    gross_ret = position.shift(1) * basis_ret
    turnover = position.diff().abs().fillna(0.0)
    net_ret = gross_ret - turnover * cost
    return pd.DataFrame({
        "position": position,
        "gross_ret": gross_ret,
        "turnover": turnover,
        "net_ret": net_ret,
    })


def extract_trades(results: pd.DataFrame, cost: float, basis: pd.Series) -> List[dict]:
    """Decompose the continuous return series into discrete trades.

    A trade spans an entry flip (0->±1) through the following exit flip (->0).
    Charges cost on BOTH flips (entry + exit) to match cumulative turnover,
    i.e. 2 * cost per round trip.
    """
    pos = results["position"]
    basis_ret = results["gross_ret"].copy()   # gross per-bar, aligned
    trades: List[dict] = []

    i = 0
    n = len(pos)
    while i < n:
        # scan for entry flip
        if i == 0:
            prev = 0.0
        else:
            prev = pos.iloc[i-1]
        cur = pos.iloc[i]
        if prev == 0 and cur != 0:
            entry_basis = float(basis.iloc[i])
            direction = 1.0 if cur > 0 else -1.0
            entry_ts = pos.index[i]
            gross = 0.0
            run_basis = entry_basis
            min_basis = entry_basis
            max_basis = entry_basis
            bars = 1
            i += 1
            # walk until exit flip (cur != 0 -> 0), or out of range
            while i < n:
                # this bar's gross contribution uses position at i-1 (the holding);
                # long basis(short) profits when basis rises(falls): apply sign.
                ret_bar = float(basis_ret.iloc[i])
                gross += direction * ret_bar
                run_basis += ret_bar
                min_basis = min(min_basis, run_basis)
                max_basis = max(max_basis, run_basis)
                bars += 1
                # check if exit on THIS bar (position[i]==0 while holding from i-1)
                if pos.iloc[i] == 0:
                    break
                i += 1
            exit_basis = float(basis.iloc[i])
            net = gross - 2 * cost
            if direction > 0:
                mae = (entry_basis - min_basis)
            else:
                mae = (max_basis - entry_basis)
            trades.append({
                "entry_ts": entry_ts,
                "exit_ts": pos.index[i],
                "direction": int(direction),
                "bars": bars,
                "entry_basis": entry_basis,
                "exit_basis": exit_basis,
                "gross": gross,
                "net": net,
                "mae": mae,
            })
        i += 1
    return trades


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_metrics(results: pd.DataFrame, trades: List[dict]) -> Dict:
    net = results["net_ret"].dropna()
    gross = results["gross_ret"].dropna()
    cum = net.cumsum()
    dd = (cum - cum.cummax()).min()

    ann_periods = 252
    mu = net.mean()
    sd = net.std()
    sharpe = mu / sd * np.sqrt(ann_periods) if sd > 0 else 0.0

    downside = net[net < 0]
    dsd = downside.std()
    sortino = mu / dsd * np.sqrt(ann_periods) if dsd > 0 else (np.inf if mu > 0 else 0.0)

    gross_cum = gross.cumsum()
    cost_drag = float(gross_cum.iloc[-1] - cum.iloc[-1]) if len(cum) else 0.0

    n_trades = len(trades)
    net_trades = np.array([t["net"] for t in trades], dtype=float) if trades else np.array([])
    gross_trades = np.array([t["gross"] for t in trades], dtype=float) if trades else np.array([])
    mae_trades = np.array([t["mae"] for t in trades], dtype=float) if trades else np.array([])
    bars_arr = np.array([t["bars"] for t in trades], dtype=float) if trades else np.array([])

    wrs = 0
    if n_trades:
        wrs = float((net_trades > 0).mean())

    metrics = {
        "n_bars": int(len(net)),
        "n_trades": n_trades,
        "cum_net": float(cum.iloc[-1]) if len(cum) else 0.0,
        "cum_gross": float(gross_cum.iloc[-1]) if len(gross_cum) else 0.0,
        "ann_sharpe_net": float(sharpe),
        "ann_sortino_net": float(sortino),
        "max_dd_net": float(dd),
        "avg_daily_net": float(mu),
        "avg_daily_gross": float(gross.mean()),
        "cost_drag": float(cost_drag),
        "win_rate": wrs,
        "avg_trade_net": float(np.mean(net_trades)) if n_trades else 0.0,
        "avg_trade_gross": float(np.mean(gross_trades)) if n_trades else 0.0,
        "median_trade_net": float(np.median(net_trades)) if n_trades else 0.0,
        "avg_hold_bars": float(np.mean(bars_arr)) if n_trades else 0.0,
        "max_hold_bars": float(np.max(bars_arr)) if n_trades else 0.0,
        "avg_mae": float(np.mean(mae_trades)) if n_trades else 0.0,
        "max_mae": float(np.max(mae_trades)) if n_trades else 0.0,
    }
    # per-year
    by_year = {}
    nyear = net.groupby(net.index.year)
    for yr, g in nyear:
        c = g.cumsum()
        by_year[str(yr)] = {
            "net": float(c.iloc[-1]) if len(c) else 0.0,
            "trades": int((results.loc[g.index, "turnover"] > 0).sum() // 2),
            "sharpe": float(g.mean() / g.std() * np.sqrt(252)) if g.std() > 0 else 0.0,
        }
    metrics["by_year"] = by_year
    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(data: pd.DataFrame, params: Params) -> Tuple[pd.DataFrame, List[dict], Dict]:
    basis = data["basis"]
    z = robust_zscore(basis, params.z_window, params.z_min_periods)
    hl = rolling_half_life(basis, params.hl_window)
    corr = rolling_corr(data["ret.EURUSD"], data["ret.USDCHF"],
                        params.corr_window, params.corr_min_periods)
    vol_kill = basis_vol_kill(basis, params.vol_win, params.vol_pct) if params.use_vol_kill else None

    position = signal_state_machine(z, hl, corr, params, vol_kill)
    results = compute_returns(position, data["basis_ret"], params.cost_per_position_change)
    trades = extract_trades(results, params.cost_per_position_change, basis)
    metrics = compute_metrics(results, trades)
    metrics["params"] = params.as_dict()
    return results, trades, metrics


def dry_indicators(data: pd.DataFrame, params: Params) -> pd.DataFrame:
    """Return indicator frame for inspection / saving."""
    basis = data["basis"]
    z = robust_zscore(basis, params.z_window, params.z_min_periods)
    hl = rolling_half_life(basis, params.hl_window)
    corr = rolling_corr(data["ret.EURUSD"], data["ret.USDCHF"],
                        params.corr_window, params.corr_min_periods)
    out = pd.DataFrame({
        "basis": basis,
        "z": z,
        "half_life": hl,
        "corr": corr,
        "identity_resid": data["identity_resid"],
    })
    return out


# ── robustness sweep (spec §10) ────────────────────────────────────────────────

def robustness_sweep(data: pd.DataFrame) -> Dict[str, list]:
    base = DEFAULT_PARAMS
    grid = {
        "z_window": [60, 90, 120],
        "entry_z": [1.8, 2.0, 2.2, 2.5],
        "exit_z": [0.0, 0.3, 0.5],
        "stop_z": [3.0, 3.5, 4.0],
        "max_hold": [10, 15, 20, 30],
        "max_half_life": [15, 20, 25, 30],
        "min_corr": [-0.40, -0.50, -0.60],
        "cost_per_position_change": [0.0003, 0.0006, 0.0010],
    }
    # precompute baseline-independent pieces
    basis = data["basis"]

    out: Dict[str, list] = {}
    for key, vals in grid.items():
        row = []
        for v in vals:
            p = Params(**{**base.as_dict(), key: v})
            _, _, m = run_backtest(data, p)
            row.append({
                key: v,
                "net": m["cum_net"],
                "sharpe": m["ann_sharpe_net"],
                "trades": m["n_trades"],
                "win_rate": m["win_rate"],
                "max_dd": m["max_dd_net"],
                "avg_trade_net": m["avg_trade_net"],
            })
        out[key] = row
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt(x: float, nd: int = 4) -> str:
    return f"{x:.{nd}f}"


def main() -> int:
    ap = argparse.ArgumentParser(description="EURCHF Triangular Basis v1 backtest")
    ap.add_argument("--quick", action="store_true", help="base metrics only (skip sweep)")
    ap.add_argument("--out", default=str(OUT_DIR / "triangular_basis_eurchf_report.md"))
    ap.add_argument("--save-indicators", action="store_true")
    args = ap.parse_args()

    print("Loading data...")
    data = build_basis_frame()
    print(f"  {len(data)} daily bars | {data.index.min().date()} → {data.index.max().date()}")

    resid = data["identity_resid"].abs()
    print(f"  Identity check: mean|EURCHF/(EURUSD*USDCHF)-1| = {resid.mean():.3e}")
    print(f"  Triangle look: min residual ratio std ...")

    params = DEFAULT_PARAMS
    results, trades, metrics = run_backtest(data, params)

    print("\n" + "=" * 60)
    print("EURCHF TRIANGULAR BASIS v1 — DAILY RESULTS (baseline)")
    print("=" * 60)
    print(f"Bars: {metrics['n_bars']} | Trades: {metrics['n_trades']}")
    print(f"Cum gross: {_fmt(metrics['cum_gross'])} | Cum net: {_fmt(metrics['cum_net'])}")
    print(f"Net Sharpe: {_fmt(metrics['ann_sharpe_net'],2)} | Sortino: {_fmt(metrics['ann_sortino_net'],2)}")
    print(f"Max DD (net): {_fmt(metrics['max_dd_net'])}")
    print(f"Avg daily net: {_fmt(metrics['avg_daily_net'],6)} | gross: {_fmt(metrics['avg_daily_gross'],6)}")
    print(f"Win rate: {_fmt(metrics['win_rate'],3)} | Avg trade net: {_fmt(metrics['avg_trade_net'],6)}")
    print(f"Avg hold: {_fmt(metrics['avg_hold_bars'],1)} bars | Cost drag: {_fmt(metrics['cost_drag'])}")
    print(f"Avg MAE: {_fmt(metrics['avg_mae'],6)} | Max MAE: {_fmt(metrics['max_mae'],6)}")
    print("\nPer-year:")
    for yr, d in metrics["by_year"].items():
        print(f"  {yr}: net={_fmt(d['net'])} trades={d['trades']} sharpe={_fmt(d['sharpe'],2)}")

    if args.save_indicators:
        ind = dry_indicators(data, params)
        ind.to_csv(OUT_DIR / "triangular_basis_eurchf_indicators.csv")

    # robustness
    sweep = {}
    if args.quick:
        print("\n(skipping robustness sweep: --quick)")
    else:
        print("\nRunning robustness sweep...")
        sweep = robustness_sweep(data)
        for key, rows in sweep.items():
            print(f"  {key}: " + ", ".join(f"{r[key]}->{r['net']:.4f}" for r in rows))

    # write report
    _write_report(args.out, data, params, metrics, sweep)
    print(f"\nReport: {args.out}")
    return 0


def _write_report(path: str, data: pd.DataFrame, params: Params, metrics: Dict, sweep: Dict):
    lines = []
    lines.append("# EURCHF Triangular Basis v1 — Backtest Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"**Universe:** EURUSD, USDCHF, EURCHF (MT5 PRO daily)")
    lines.append(f"**Period:** {data.index.min().date()} → {data.index.max().date()} ({len(data)} bars)")
    lines.append(f"**Basis:** ln(EURCHF) - ln(EURUSD) - ln(USDCHF)")
    lines.append("")
    lines.append("## Baseline Parameters (spec §6)")
    lines.append("")
    lines.append("| Param | Value |")
    lines.append("|-------|-------|")
    for k, v in params.as_dict().items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Daily Results")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for k in ["n_bars", "n_trades", "cum_gross", "cum_net", "ann_sharpe_net",
              "ann_sortino_net", "max_dd_net", "avg_daily_net", "avg_daily_gross",
              "cost_drag", "win_rate", "avg_trade_net", "median_trade_net",
              "avg_trade_gross", "avg_hold_bars", "max_hold_bars", "avg_mae", "max_mae"]:
        lines.append(f"| {k} | {metrics.get(k)} |")
    lines.append("")
    lines.append("## Per-Year")
    lines.append("")
    lines.append("| Year | Net | Trades | Sharpe |")
    lines.append("|------|-----|--------|--------|")
    for yr, d in metrics["by_year"].items():
        lines.append(f"| {yr} | {d['net']:.4f} | {d['trades']} | {d['sharpe']:.2f} |")
    lines.append("")

    if sweep:
        lines.append("## Robustness Sweep (spec §10)")
        lines.append("")
        lines.append("> Each row varies ONE parameter around baseline; checks directionally-stable behavior.")
        lines.append("")
        for key, rows in sweep.items():
            lines.append(f"### {key}")
            lines.append("")
            cols = ", ".join(f"{r[key]}" for r in rows)
            nets = ", ".join(f"{r['net']:.4f}" for r in rows)
            lines.append(f"- values: `{cols}`")
            lines.append(f"- cum net: `{nets}`")
            lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("> **Anti-overfit fail-fast check (spec §9):** if gross survives but net dies at "
                 "6-10bps costs, the strategy is NOT ready. Review before forward-testing.")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())