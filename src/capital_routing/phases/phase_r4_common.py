"""
CR-RISK-BLOCK1 R4 — Static Risk Frontier (shared primitives).

Core simulators for the sealed 890-event A/B ledger:

- 1R risk-unit definition: 1R = TARGET_VOL x sqrt(hold) = 24.4949 bps is the
  strategy's normalized expected-move unit, NOT a hard stop. Historical trades
  lose far more than -1R (A worst -3.66R, B worst -3.31R). Account sizing maps
  trade_return_R x f directly into equity: a -3R trade at f = 1% costs ~-3%
  of the account. See R4_RISK_UNIT_DEFINITION.md.
- Two compounding modes:
    sequential: E_{t+1} = E_t * (1 + f * r_R_t) over the chronological per-trade
                return sequence (the brief's formula; used for A-only/B-only and
                as the per-trade reference).
    hourly:     E_{h+1} = E_h * (1 + f * r_h) over the overlap-exact hourly
                portfolio PnL grid (sum of all open trades' incremental net PnL
                each hour, cost charged at entry). Used for the pooled A+B book
                so real overlap (max 3 concurrent) is preserved exactly.
- Resampling schemes for dependency-aware Monte Carlo (deterministic seeds):
    iid            individual trades (baseline only)
    block          chronological stationary block bootstrap (block = 25 trades)
    episode        R1 12h-cluster block bootstrap (episode members stay together)

All compounding is multiplicative; no additive approximations. No alpha change.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# 1R in bps (TARGET_VOL x sqrt(HOLD)); all trades share this risk unit.
RISK_UNIT_BPS = 24.49489742783178
HOLD_H = 6.0

# Static risk-per-R fractions (research ladder, NOT recommendations)
LADDER_PCT = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.75,
              1.00, 1.25, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00]

# Simulation parameters
MC_PATHS = 10_000
MC_PATHS_STRESS = 5_000
MC_SEED = 20260815
BLOCK_SIZE = 25          # chronological block bootstrap block (trades)
EPISODE_INTERVAL_H = 12.0
EDGE_STATES = [1.0, 0.75, 0.50, 0.25]

# Ruin thresholds (percent drawdown / capital loss)
RUIN_DD_PCTS = [10.0, 15.0, 20.0, 30.0, 40.0, 50.0]

PERCENTILES = [5, 25, 50, 75, 90, 95, 99]

# ---------------------------------------------------------------------------
# Trade book
# ---------------------------------------------------------------------------

def trade_book(ledger: pd.DataFrame) -> pd.DataFrame:
    """Chronological per-trade net returns in R (the sealed book, untouched)."""
    tb = ledger[["event_id", "family", "entry_ts", "exit_ts", "pnl_bps",
                 "risk_unit_bps", "r_multiple", "mfe_r", "mae_r"]].copy()
    tb["entry_ts"] = pd.to_datetime(tb["entry_ts"], utc=True)
    tb["exit_ts"] = pd.to_datetime(tb["exit_ts"], utc=True)
    tb["r_R"] = tb["pnl_bps"] / tb["risk_unit_bps"]
    tb = tb.sort_values("entry_ts").reset_index(drop=True)
    tb["is_win"] = tb["r_R"] > 0.0
    return tb


def span_years(entry_ts: Sequence, exit_ts: Sequence) -> float:
    """Calendar span of the trade book in years (for annualization)."""
    t0 = pd.Timestamp(min(entry_ts))
    t1 = pd.Timestamp(max(exit_ts))
    return (t1 - t0).total_seconds() / (365.25 * 86400.0)


# ---------------------------------------------------------------------------
# Compounding
# ---------------------------------------------------------------------------

def sequential_equity(r_R: np.ndarray, f: float) -> np.ndarray:
    """E_{t+1} = E_t * (1 + f * r_R_t). Returns the equity path (start = 1.0)."""
    return np.concatenate([[1.0], np.cumprod(1.0 + f * r_R)])


def hourly_grid(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """Overlap-exact hourly portfolio PnL grid (net bps per hour, cost at entry).

    Each trade contributes its incremental net PnL per hour; the first bar of
    each trade carries the modeled all-in cost (mark_bps(0) = 0, so
    net_bps(0) = -cost). Summing increments over the timeline reproduces the
    sum of sealed net PnLs exactly.
    """
    p = paths[["event_id", "mark_time", "h_since_entry", "net_bps"]].copy()
    p = p.sort_values(["event_id", "h_since_entry"])
    p["mark_time"] = pd.to_datetime(p["mark_time"], utc=True)
    p["inc_bps"] = p.groupby("event_id")["net_bps"].diff()
    first = p.groupby("event_id")["h_since_entry"].transform("min") == p["h_since_entry"]
    p.loc[first, "inc_bps"] = p.loc[first, "net_bps"]
    g = p.groupby("mark_time")["inc_bps"].sum().sort_index()
    idx = pd.date_range(g.index.min(), g.index.max(), freq="h")
    g = g.reindex(idx, fill_value=0.0).rename("net_bps")
    g = g.to_frame()
    g["r_h"] = g["net_bps"] / RISK_UNIT_BPS
    # sanity: hourly increments sum to the sealed book total
    assert abs(float(g["net_bps"].sum()) - float(ledger["pnl_bps"].sum())) < 1e-6
    return g


def hourly_equity(r_h: np.ndarray, f: float) -> np.ndarray:
    """E_{h+1} = E_h * (1 + f * r_h) over the full hourly calendar."""
    return np.concatenate([[1.0], np.cumprod(1.0 + f * r_h)])


# ---------------------------------------------------------------------------
# Equity-path metrics
# ---------------------------------------------------------------------------

def _max_dd(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity) / peak
    return float(dd.max()) if len(dd) else 0.0


def _longest_dd_duration_h(equity: np.ndarray) -> int:
    """Longest consecutive hours below the running peak (recovery time)."""
    peak = np.maximum.accumulate(equity)
    under = equity < peak
    best = cur = 0
    for u in under:
        cur = cur + 1 if u else 0
        if cur > best:
            best = cur
    return best


def _time_to_recover(equity: np.ndarray) -> Optional[float]:
    peak = np.maximum.accumulate(equity)
    trough_idx = int(np.argmax((peak - equity) / np.maximum(peak, 1e-12)))
    if (peak - equity)[trough_idx] <= 1e-12:
        return None
    recover = np.where(equity[trough_idx:] >= peak[trough_idx] - 1e-12)[0]
    if len(recover) == 0:
        return None
    return float(recover[0])  # hours from trough to new peak


def equity_metrics(equity: np.ndarray, years: float,
                   hourly: bool = True) -> Dict:
    """Full account-level metric set from an equity path (start = 1.0)."""
    rets = np.diff(equity) / equity[:-1]
    terminal = float(equity[-1])
    cagr = float(terminal ** (1.0 / years) - 1.0) if terminal > 0 else -1.0
    dd = (np.maximum.accumulate(equity) - equity) / np.maximum.accumulate(equity)
    max_dd = float(dd.max()) if len(dd) else 0.0
    avg_dd = float(dd[dd > 0].mean()) if (dd > 0).any() else 0.0
    # annualization factor
    if hourly:
        ann = 24.0 * 365.25
    else:
        ann = max(1.0, len(rets) / max(years, 1e-9))
    vol = float(np.std(rets, ddof=1) * np.sqrt(ann)) if len(rets) > 1 else 0.0
    sharpe = float(cagr / vol) if vol > 0 else np.nan
    downside = rets[rets < 0]
    ddev = float(np.sqrt(np.mean(downside ** 2)) * np.sqrt(ann)) \
        if len(downside) else 0.0
    sortino = float(cagr / ddev) if ddev > 0 else np.nan
    ulcer = float(np.sqrt(np.mean(dd ** 2)))
    calmar = float(cagr / max_dd) if max_dd > 0 else np.nan
    rec_factor = float((terminal - 1.0) / max_dd) if max_dd > 0 else np.nan
    # calendar aggregates
    daily = _daily_returns(equity, hourly)
    worst_day = float(daily.min()) if len(daily) else 0.0
    best_day = float(daily.max()) if len(daily) else 0.0
    rolling24 = _rolling_loss(equity, hourly, 24)
    rolling48 = _rolling_loss(equity, hourly, 48)
    monthly = _period_returns(equity, hourly, 30)
    worst_month = float(monthly.min()) if len(monthly) else 0.0
    pos_month = float((monthly > 0).mean()) if len(monthly) else np.nan
    consec_neg_months = _max_consecutive_neg(monthly)
    return {
        "terminal_equity": terminal,
        "total_return": terminal - 1.0,
        "cagr": cagr,
        "max_dd": max_dd,
        "avg_dd": avg_dd,
        "longest_dd_duration_h": _longest_dd_duration_h(equity),
        "time_to_recover_h": _time_to_recover(equity),
        "calmar": calmar,
        "sharpe": sharpe,
        "sortino": sortino,
        "ulcer_index": ulcer,
        "recovery_factor": rec_factor,
        "worst_day_pct": worst_day,
        "best_day_pct": best_day,
        "worst_24h_pct": rolling24,
        "worst_48h_pct": rolling48,
        "worst_month_pct": worst_month,
        "positive_month_rate": pos_month,
        "max_consecutive_neg_months": consec_neg_months,
    }


def _daily_returns(equity: np.ndarray, hourly: bool) -> np.ndarray:
    step = 24 if hourly else 1
    e = equity[::step]
    return np.diff(e) / e[:-1]


def _rolling_loss(equity: np.ndarray, hourly: bool, hours: int) -> float:
    step = 24 if hourly else 1
    e = equity[::step]
    if len(e) <= 1:
        return 0.0
    rets = np.diff(e) / e[:-1]
    w = max(1, hours // step)
    if len(rets) < w:
        return float(rets.sum())
    roll = np.convolve(rets, np.ones(w), "valid")
    return float(roll.min())


def _period_returns(equity: np.ndarray, hourly: bool, days: int) -> np.ndarray:
    step = 24 if hourly else 1
    e = equity[::step]
    n = len(e) // days
    if n == 0:
        return np.array([equity[-1] / equity[0] - 1.0])
    groups = e[: n * days].reshape(n, days)
    start = groups[:, 0]
    end = groups[:, -1]
    return (end - start) / start


def _max_consecutive_neg(monthly: np.ndarray) -> int:
    best = cur = 0
    for m in monthly:
        cur = cur + 1 if m < 0 else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------------------
# Dependency-aware resampling (deterministic)
# ---------------------------------------------------------------------------

def sample_sequences(r_R: np.ndarray, scheme: str, n_paths: int, n: int,
                     seed: int, blocks: Optional[List[np.ndarray]] = None) -> np.ndarray:
    """Draw n_paths resampled sequences of length n (trades) from the book.

    scheme: 'iid' | 'block' (stationary chronological blocks) | 'episode'
    (R1 12h clusters kept intact; pass `blocks` for the episode scheme).
    Deterministic per (scheme, seed).
    """
    rng = np.random.default_rng(seed)
    if scheme == "iid":
        return rng.choice(r_R, size=(n_paths, n), replace=True)
    if scheme == "block":
        out = np.empty((n_paths, n))
        n_blocks = int(np.ceil(n / BLOCK_SIZE))
        starts = rng.integers(0, len(r_R), size=(n_paths, n_blocks))
        for p in range(n_paths):
            pieces = [r_R[np.arange(s, s + BLOCK_SIZE) % len(r_R)]
                      for s in starts[p]]
            out[p] = np.concatenate(pieces)[:n]
        return out
    if scheme == "episode":
        assert blocks is not None, "episode scheme requires cluster blocks"
        out = np.empty((n_paths, n))
        for p in range(n_paths):
            picked: List[np.ndarray] = []
            total = 0
            while total < n:
                b = blocks[int(rng.integers(0, len(blocks)))]
                picked.append(r_R[b])
                total += len(b)
            out[p] = np.concatenate(picked)[:n]
        return out
    raise ValueError(f"unknown scheme {scheme}")


# ---------------------------------------------------------------------------
# Portfolio stats helpers
# ---------------------------------------------------------------------------

def max_dd_of_sequence(r_seq: np.ndarray, f: float) -> float:
    eq = sequential_equity(r_seq, f)
    return _max_dd(eq)


def percentile_series(vals: np.ndarray) -> Dict[str, float]:
    return {f"p{p}": float(np.percentile(vals, p)) for p in PERCENTILES}
