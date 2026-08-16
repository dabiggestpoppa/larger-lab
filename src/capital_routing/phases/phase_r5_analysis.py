"""
CR-RISK-BLOCK2 R5 — Family quality analysis (III-VII).

- III  R5_FAMILY_DISTRIBUTIONS        full per-family return distribution
- IV   R5_FAMILY_EXPECTANCY_QUALITY   expectancy/PF/WR with bootstrap CIs and
                                      per-unit-of-risk contribution
- V    R5_FAMILY_LEFT_TAIL            R2-framework downside comparison + doc
- VI   R5_FAMILY_PROFIT_ANATOMY       R3-framework profit delivery comparison
- VII  R5_FAMILY_TEMPORAL_STABILITY   pre-defined calendar partitions + split

All descriptive. No allocation change, no "best family", no strategy change.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r4_common import RISK_UNIT_BPS, sequential_equity

N_BOOT = 10_000
BOOT_SEED = 20260815

FAMILIES = ["A", "B", "A+B"]


def _fam(df: pd.DataFrame, key: str) -> pd.DataFrame:
    return df[df["family"] == key]


def _r_R(df: pd.DataFrame) -> np.ndarray:
    return (df["pnl_bps"] / df["risk_unit_bps"]).to_numpy(dtype=float)


def _pct(vals: np.ndarray, ps: List[float]) -> Dict[str, float]:
    return {f"p{int(p)}": float(np.percentile(vals, p)) for p in ps}


# ---------------------------------------------------------------------------
# III. Family distributions
# ---------------------------------------------------------------------------

def family_distributions(ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key in FAMILIES:
        df = ledger if key == "A+B" else _fam(ledger, key)
        r = _r_R(df)
        wins = r[r > 0]
        losses = r[r <= 0]
        dd = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
        rows.append({
            "family": key, "N": int(len(df)),
            "date_start": str(pd.to_datetime(df["event_ts"].min(), utc=True).date()),
            "date_end": str(pd.to_datetime(df["event_ts"].max(), utc=True).date()),
            "events_per_year": float(len(df) / ((pd.to_datetime(df["exit_ts"].max(), utc=True)
                                                 - pd.to_datetime(df["entry_ts"].min(), utc=True))
                                                .total_seconds() / (365.25 * 86400.0))),
            "n_wins": int(len(wins)), "n_losses": int(len(losses)),
            "win_rate": float(len(wins) / len(r)),
            "mean_R": float(r.mean()), "median_R": float(np.median(r)),
            "std_R": float(r.std(ddof=1)),
            "downside_deviation_R": float(dd),
            "skew": float(pd.Series(r).skew()), "kurtosis": float(pd.Series(r).kurt()),
            "min_R": float(r.min()), "max_R": float(r.max()),
            **_pct(r, [1, 5, 10, 25, 50, 75, 90, 95, 99]),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# IV. Expectancy quality
# ---------------------------------------------------------------------------

def _bootstrap_ci(vals: np.ndarray, stat, n: int = N_BOOT, seed: int = BOOT_SEED) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = rng.choice(vals, size=(n, len(vals)), replace=True)
    est = np.array([stat(d) for d in draws])
    return float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def expectancy_quality(ledger: pd.DataFrame, years: float) -> pd.DataFrame:
    rows = []
    for key in FAMILIES:
        df = ledger if key == "A+B" else _fam(ledger, key)
        r = _r_R(df)
        wins = r[r > 0]
        losses = r[r <= 0]
        avg_win = float(wins.mean()) if len(wins) else np.nan
        avg_loss = float(losses.mean()) if len(losses) else np.nan
        pf = float(wins.sum() / abs(losses.sum())) if len(losses) else np.nan
        exp_ci = _bootstrap_ci(r, np.mean)
        # PF bootstrap (careful: PF can blow up; use median of bootstrap PF)
        pf_ci = _bootstrap_ci(r, lambda x: float(x[x > 0].sum() / abs(x[x <= 0].sum()))
                              if (x <= 0).any() else np.nan)
        seq = sequential_equity(r, 0.01)
        peak = np.maximum.accumulate(seq)
        max_dd_f1 = float(((peak - seq) / peak).max())
        dd = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
        exp_bps = float(r.mean()) * RISK_UNIT_BPS
        per_100 = float(r.sum() / len(r) * 100.0)
        n_months = max(1.0, years * 12.0)
        per_month = float(r.sum() / n_months)
        rows.append({
            "family": key, "N": int(len(df)),
            "mean_R_per_event": float(r.mean()),
            "median_R_per_event": float(np.median(r)),
            "expectancy_bps_per_event": exp_bps,
            "profit_factor": pf,
            "win_rate": float((r > 0).mean()),
            "avg_win_R": avg_win, "avg_loss_R": avg_loss,
            "payoff_ratio": float(avg_win / abs(avg_loss)) if avg_loss else np.nan,
            "variance_of_expectancy": float(r.var(ddof=1)),
            "exp_CI_low_R": exp_ci[0], "exp_CI_high_R": exp_ci[1],
            "pf_CI_low": pf_ci[0], "pf_CI_high": pf_ci[1],
            "return_per_100_events_R": per_100,
            "return_per_calendar_month_R": per_month,
            "max_dd_at_f1_pct": max_dd_f1 * 100.0,
            "return_per_unit_max_dd_R": float(r.sum() / max_dd_f1) if max_dd_f1 > 0 else np.nan,
            "return_per_unit_downside_dev_R": float(r.sum() / dd) if dd > 0 else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# V. Left-tail comparison (R2 framework)
# ---------------------------------------------------------------------------

def _path_mfe_mae(paths: pd.DataFrame):
    """Path-derived net MFE / MAE (R), identical to Block-I R2/R3 convention
    (running max/min of net_R over the trade's hourly path, cost included)."""
    p = paths.sort_values(["event_id", "h_since_entry"])
    mfe = p.groupby("event_id")["net_R"].max()
    mae = p.groupby("event_id")["net_R"].min()
    return mfe, mae


def _tail_share(r: np.ndarray, q: float) -> float:
    losses = r[r < 0]
    if len(losses) == 0:
        return np.nan
    thr = np.quantile(losses, q)  # q=0.10 -> worst 10% of losses
    deep = r[r <= thr]
    return float(deep.sum() / losses.sum())


def left_tail(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    mfe, mae = _path_mfe_mae(paths)
    rows = []
    for key in FAMILIES:
        df = ledger if key == "A+B" else _fam(ledger, key)
        r = _r_R(df)
        losses = r[r < 0]
        breaches = {t: float((r <= -t).mean()) for t in [0.5, 1.0, 2.0]}
        # failure speed: reveal time = time to first -0.5R from paths (losers
        # only); fast_failure_rate = share of ALL family trades that are FAST
        # (R2 convention: FAST losers / family N)
        pf = paths[paths["event_id"].isin(set(df["event_id"]))]
        reveal = pf[pf["net_R"] <= -0.5].groupby("event_id")["h_since_entry"].min()
        loser_ids = set(df.loc[df["pnl_bps"] <= 0, "event_id"])
        fast_n = int((reveal[reveal.index.isin(loser_ids)] <= 2.0).sum())\
            if len(reveal) else 0
        fast = fast_n / len(df) if len(df) else np.nan
        # loss streaks (within-family chronological)
        streak = _max_streak(r)
        w_mae = mae[mae.index.isin(set(df.loc[df["pnl_bps"] > 0, "event_id"]))]
        l_mae = mae[mae.index.isin(loser_ids)]
        rows.append({
            "family": key, "N": int(len(df)),
            "winner_median_MAE_R": float(w_mae.median()) if len(w_mae) else np.nan,
            "loser_median_MAE_R": float(l_mae.median()) if len(l_mae) else np.nan,
            "median_loss_R": float(np.median(losses)) if len(losses) else np.nan,
            "p90_loss_R": float(np.quantile(losses, 0.10)) if len(losses) else np.nan,
            "p95_loss_R": float(np.quantile(losses, 0.05)) if len(losses) else np.nan,
            "worst_trade_R": float(r.min()),
            "breach_0_5R_freq": breaches[0.5], "breach_1R_freq": breaches[1.0],
            "breach_2R_freq": breaches[2.0],
            "fast_failure_rate": fast,
            "worst1pct_share_of_losses": _tail_share(r, 0.01),
            "worst5pct_share_of_losses": _tail_share(r, 0.05),
            "worst10pct_share_of_losses": _tail_share(r, 0.10),
            "max_loss_streak": streak,
            "median_time_to_neg0_5R_h": float(reveal.median()) if len(reveal) else np.nan,
        })
    return pd.DataFrame(rows)


def _max_streak(r: np.ndarray) -> int:
    best = cur = 0
    for x in r:
        cur = cur + 1 if x < 0 else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------------------
# VI. Profit anatomy (R3 framework)
# ---------------------------------------------------------------------------

def profit_anatomy(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    mfe, _ = _path_mfe_mae(paths)
    rows = []
    for key in FAMILIES:
        df = ledger if key == "A+B" else _fam(ledger, key)
        r = _r_R(df)
        wins = df[df["pnl_bps"] > 0]
        mfe_w = mfe[mfe.index.isin(set(wins["event_id"]))]
        final_R_w = wins["pnl_bps"] / wins["risk_unit_bps"]
        final_R_w = final_R_w.set_axis(mfe_w.index)
        capture = (final_R_w / mfe_w)
        capture = capture[capture > 0]
        giveback = (mfe_w - final_R_w)
        # +1R reach and after-+1R failure (path-derived, net of cost)
        reach1 = float((mfe[mfe.index.isin(set(df["event_id"]))] >= 1.0).mean())
        after1_ids = set(mfe[mfe >= 1.0].index)
        after1 = df[df["event_id"].isin(after1_ids)]
        fail_after1 = float((after1["pnl_bps"] <= 0).mean()) if len(after1) else np.nan
        # hourly delivery from paths
        pf = paths[paths["event_id"].isin(set(df["event_id"]))]
        hour_pnl = pf.groupby("h_since_entry").apply(
            lambda g: float(g["net_bps"].sum()), include_groups=False)
        total_bps = float(df["pnl_bps"].sum())
        cum = hour_pnl.cumsum()
        pct_by_hour = {int(h): float(cum.get(h, 0.0) / total_bps) if total_bps else np.nan
                       for h in range(1, 7)}
        # winner concentration
        pos = r[r > 0]
        conc = {}
        for q in [0.01, 0.05, 0.10]:
            nq = max(1, int(len(pos) * q))
            top = np.sort(pos)[-nq:]
            conc[f"top{int(q*100)}pct_share_of_positive"] = float(top.sum() / pos.sum()) if len(pos) else np.nan
        rows.append({
            "family": key, "N": int(len(df)),
            "winner_median_MFE_R": float(mfe_w.median()),
            "winner_p90_MFE_R": float(mfe_w.quantile(0.90)),
            "winner_median_time_to_MFE_h": float(wins["time_to_mfe_h"].median()),
            "winner_median_capture_ratio": float(capture.median()),
            "winner_median_giveback_R": float(giveback.median()),
            "median_time_to_first_0_25R_h": _first_passage_median(pf, 0.25),
            "median_time_to_first_0_50R_h": _first_passage_median(pf, 0.50),
            "median_time_to_first_1R_h": _first_passage_median(pf, 1.00),
            "reach_0_50R_freq": float((mfe[mfe.index.isin(set(df["event_id"]))] >= 0.5).mean()),
            "reach_1R_freq": reach1,
            "fail_after_1R_freq": fail_after1,
            **{f"pct_final_pnl_by_h{h}": pct_by_hour.get(h, np.nan) for h in range(1, 7)},
            **conc,
        })
    return pd.DataFrame(rows)


def _first_passage_median(paths: pd.DataFrame, level: float) -> float:
    hit = paths[paths["net_R"] >= level]
    if len(hit) == 0:
        return np.nan
    t = hit.groupby("event_id")["h_since_entry"].min()
    return float(t.median())


# ---------------------------------------------------------------------------
# VII. Temporal stability
# ---------------------------------------------------------------------------

PARTITIONS = ["year", "half", "quarter", "split"]


def temporal_stability(ledger: pd.DataFrame) -> pd.DataFrame:
    tb = ledger.copy()
    ts = pd.to_datetime(tb["event_ts"], utc=True)
    tb["year"] = ts.dt.year
    tb["half"] = np.where(ts.dt.month <= 6, f"{ts.dt.year}-H1", f"{ts.dt.year}-H2")
    tb["quarter"] = ts.dt.year.astype(str) + "-Q" + ts.dt.quarter.astype(str)
    tb["split"] = tb["split"].fillna("unknown")
    rows = []
    for part in PARTITIONS:
        for key in ["A", "B"]:
            df = _fam(tb, key)
            for name, g in df.groupby(part):
                r = _r_R(g)
                wins = r[r > 0]
                losses = r[r <= 0]
                pf = float(wins.sum() / abs(losses.sum())) if len(losses) else np.nan
                seq = sequential_equity(r, 0.01)
                peak = np.maximum.accumulate(seq)
                maxdd = float(((peak - seq) / peak).max())
                rows.append({
                    "partition": part, "partition_value": str(name), "family": key,
                    "N": int(len(g)), "mean_R": float(r.mean()),
                    "PF": pf, "win_rate": float((r > 0).mean()),
                    "max_dd_at_f1_pct": maxdd * 100.0,
                    "worst_trade_R": float(r.min()),
                    "tail10_share_of_losses": _tail_share(r, 0.10),
                })
    df = pd.DataFrame(rows)
    # classification: A/B mean-R ranking stability across qualifying partitions
    classification = {}
    for part in PARTITIONS:
        sub = df[df["partition"] == part]
        qual = sub[sub["N"] >= 20]
        pairs = {}
        for v in qual["partition_value"].unique():
            a = qual[(qual.family == "A") & (qual.partition_value == v)]
            b = qual[(qual.family == "B") & (qual.partition_value == v)]
            if len(a) and len(b):
                pairs[v] = (a["mean_R"].iloc[0], b["mean_R"].iloc[0])
        if not pairs:
            classification[part] = "UNSTABLE"
            continue
        agree = sum(1 for a, b in pairs.values() if (a - b) * (1.0) > 0
                    if abs(a - b) > 1e-12)
        total_sign = sum(1 for a, b in pairs.values() if abs(a - b) > 1e-12)
        share = agree / total_sign if total_sign else np.nan
        if share is None or np.isnan(share):
            classification[part] = "UNSTABLE"
        elif share >= 0.8:
            classification[part] = "STABLE"
        elif share >= 0.5:
            classification[part] = "MIXED"
        else:
            classification[part] = "UNSTABLE"
    df.attrs["classification"] = classification
    return df
