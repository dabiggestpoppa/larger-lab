"""
Phase 7 - baseline strategy test (brief section 7).

Simplest event-driven baseline: entry at frozen delay, fixed holding-period
exit, fixed volatility-normalized risk. No CEREBUS filters, no Kelly sizing,
no pyramiding, no parameter rescue.

Metrics: trades, win rate, expectancy, profit factor, Sharpe, Sortino,
max drawdown, Calmar, MFE/MAE, turnover, cost drag, yearly results.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

TRADES_PER_YEAR = 252  # fallback; replaced by actual event-frequency-based scale


def vol_normalize_position(rv_bps_per_h: float, target_vol_bps_per_h: float = 10.0) -> float:
    """Position size such that one-hour PnL std = target_vol bps."""
    if not np.isfinite(rv_bps_per_h) or rv_bps_per_h <= 0:
        return 1.0
    return target_vol_bps_per_h / rv_bps_per_h


def _downside_std(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    neg = x[x < 0]
    if len(neg) == 0:
        return 0.0
    return float(np.sqrt(np.mean(neg ** 2)))


def _max_drawdown(equity: np.ndarray) -> float:
    eq = np.asarray(equity, dtype=float)
    if len(eq) == 0:
        return 0.0
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq) / peak
    return float(np.nanmax(dd)) if len(dd) else 0.0


def run_baseline(g: pd.DataFrame, family: Dict, delay_h: int, hold_h: int,
                 pair: str, target_vol_bps_per_h: float = 10.0,
                 split: Optional[str] = None) -> Dict:
    """
    Run the baseline on oriented returns. If split is None, runs on all rows
    (for per-split yearly views, pass split explicitly).
    """
    sub = g[(g["delay_h"] == delay_h) & (g["hold_h"] == hold_h)]
    if pair != "BASKET":
        sub = sub[sub["pair"] == pair]
    if split:
        sub = sub[sub["split"] == split]
    sub = sub.dropna(subset=["dir_net_bps"]).copy()
    n = len(sub)
    if n == 0:
        return {"n_trades": 0}

    pos = sub["rv_bps_per_h"].apply(
        lambda v: vol_normalize_position(v, target_vol_bps_per_h))
    pnl = sub["dir_net_bps"].to_numpy(dtype=float) * pos.to_numpy(dtype=float)
    gross = sub["dir_return_bps"].to_numpy(dtype=float) * pos.to_numpy(dtype=float)
    cost = sub["cost_bps"].to_numpy(dtype=float) * pos.to_numpy(dtype=float)

    equity = np.cumsum(pnl)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else np.nan
    std_pnl = float(np.std(pnl, ddof=1)) if n > 1 else np.nan
    sharpe = float(np.mean(pnl) / std_pnl) if std_pnl and np.isfinite(std_pnl) else np.nan
    sortino = float(np.mean(pnl) / _downside_std(pnl)) if _downside_std(pnl) > 0 else np.nan
    max_dd = _max_drawdown(equity)

    # Annualization uses the actual event frequency (events per calendar year),
    # NOT a fixed hourly bar count: Sharpe = per-trade Sharpe * sqrt(trades/yr).
    ts_e = pd.to_datetime(sub["event_start"], utc=True)
    span_years = max((ts_e.max() - ts_e.min()).total_seconds() / (365.25 * 86400), 1.0 / 365.25)
    trades_per_year = n / span_years
    ann_factor = np.sqrt(trades_per_year)
    ann_return = float(np.mean(pnl)) * trades_per_year
    calmar = float(ann_return / max_dd) if max_dd > 0 else np.nan

    # turnover: fraction of notional traded per trade = 1 (full entry/exit)
    turnover = n
    cost_drag = float(cost.sum()) / float(abs(gross).sum()) if abs(gross).sum() > 0 else np.nan

    # yearly results
    sub["year"] = pd.to_datetime(sub["event_start"], utc=True).dt.year
    yearly = []
    for yr, gr in sub.groupby("year"):
        pnl_y = pnl[sub["year"] == yr]
        yearly.append({
            "year": int(yr), "trades": int(len(pnl_y)),
            "total_pnl_bps": float(pnl_y.sum()),
            "mean_pnl_bps": float(pnl_y.mean()),
            "win_prob": float((pnl_y > 0).mean()),
            "sharpe": float(pnl_y.mean() / np.std(pnl_y, ddof=1)) if len(pnl_y) > 1 and np.std(pnl_y, ddof=1) > 0 else np.nan,
        })

    return {
        "family": family["name"], "pair": pair, "delay_h": delay_h, "hold_h": hold_h,
        "split": split or "all",
        "n_trades": n,
        "win_rate": float((pnl > 0).mean()),
        "expectancy_bps": float(np.mean(pnl)),
        "gross_expectancy_bps": float(np.mean(gross)),
        "cost_expectancy_bps": float(np.mean(cost)),
        "profit_factor": profit_factor,
        "sharpe_annualized": sharpe * ann_factor if np.isfinite(sharpe) else np.nan,
        "sortino_annualized": sortino * ann_factor if np.isfinite(sortino) else np.nan,
        "trades_per_year": trades_per_year,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "mean_mfe_bps": float(np.mean(sub["dir_mfe_bps"].to_numpy(dtype=float) * pos.to_numpy(dtype=float))),
        "mean_mae_bps": float(np.mean(sub["dir_mae_bps"].to_numpy(dtype=float) * pos.to_numpy(dtype=float))),
        "turnover": turnover,
        "cost_drag": cost_drag,
        "total_return_bps": float(equity[-1]) if len(equity) else 0.0,
        "yearly": yearly,
    }


def baseline_csv(g: pd.DataFrame, family: Dict, delay_h: int, hold_h: int,
                 pair: str) -> pd.DataFrame:
    """Per-split baseline results as a tidy CSV frame (all + inner_sel + inner_val + untouched)."""
    rows = []
    for split in ["all", "inner_sel", "inner_val", "untouched"]:
        r = run_baseline(g, family, delay_h, hold_h, pair, split=split)
        if r["n_trades"] > 0:
            r = {k: v for k, v in r.items() if k != "yearly"}
            rows.append(r)
    return pd.DataFrame(rows)
