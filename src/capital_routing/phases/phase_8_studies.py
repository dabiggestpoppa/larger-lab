"""
Phase 8 - primitive overlay studies (brief sections 3-15, 17-20).

All studies evaluate multiple outcomes (never win-rate alone): baseline PnL,
expectancy, PF, MFE, MAE, time-to-MFE/MAE, failure rates, coverage.
Discovery happens on DISCOVERY only; CONFIRMATION and OOS are separated by the
orchestrator.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_8_stats import bootstrap_ci, permutation_p, MIN_SUPPORT

OUTCOME_COLS = ["baseline_vol_bps", "baseline_vol_mfe_bps",
                "baseline_vol_mae_bps", "baseline_win",
                "baseline_time_to_mfe_h", "baseline_time_to_mae_h"]


def _metrics(sub: pd.DataFrame, family_n: int) -> Dict[str, float]:
    """Outcome metrics for a qualified subset (vol-normalized, sealed baseline)."""
    n = len(sub)
    ret = sub["baseline_vol_bps"].to_numpy(dtype=float)
    ret = ret[np.isfinite(ret)]
    mfe = sub["baseline_vol_mfe_bps"].to_numpy(dtype=float)
    mae = sub["baseline_vol_mae_bps"].to_numpy(dtype=float)
    wins = sub["baseline_win"].to_numpy(dtype=float)
    wins = wins[np.isfinite(wins)]
    pos = ret[ret > 0].sum() if len(ret) else 0.0
    neg = -ret[ret < 0].sum() if len(ret) else 0.0
    return {
        "n": n,
        "coverage": float(n / family_n) if family_n else np.nan,
        "win_rate": float(wins.mean()) if len(wins) else np.nan,
        "expectancy_bps": float(ret.mean()) if len(ret) else np.nan,
        "median_bps": float(np.median(ret)) if len(ret) else np.nan,
        "profit_factor": float(pos / neg) if neg > 0 else np.nan,
        "mfe_bps": float(np.nanmean(mfe)) if len(mfe) else np.nan,
        "mae_bps": float(np.nanmean(mae)) if len(mae) else np.nan,
        "time_to_mfe_h": float(np.nanmean(sub["baseline_time_to_mfe_h"])) if len(sub) else np.nan,
        "time_to_mae_h": float(np.nanmean(sub["baseline_time_to_mae_h"])) if len(sub) else np.nan,
        "failure_rate": float((ret < 0).mean()) if len(ret) else np.nan,
    }


def _add_ci(row: Dict, ret: np.ndarray) -> Dict:
    ci = bootstrap_ci(ret)
    row["expect_ci_low"] = ci["ci_low"]
    row["expect_ci_high"] = ci["ci_high"]
    row["expect_se"] = ci["se"]
    return row


def daily_tier_results(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 3: baseline performance conditioned on daily tier."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        tiers = ["T1", "T2", "T3", "NO-GO", "NA"]
        for t in tiers:
            sub = g[g["daily_tier"] == t]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["daily_tier"] = t
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            rows.append(r)
        # all tiers combined (baseline reference)
        r = _metrics(g, fam_n)
        r["family"] = fid
        r["daily_tier"] = "ALL"
        r = _add_ci(r, g["baseline_vol_bps"].to_numpy(dtype=float))
        rows.append(r)
    return pd.DataFrame(rows)


def _print_study(fp: pd.DataFrame, col: str, categories: List[str]) -> pd.DataFrame:
    """Brief sections 4-5: outcome by primitive count category + continuous."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        base_ret = g["baseline_vol_bps"].to_numpy(dtype=float)
        base = _metrics(g, fam_n)
        for cat in categories:
            sub = g[g[col] == cat]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["count_category"] = cat
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            # vs baseline (all events of the family)
            r["p_vs_baseline"] = permutation_p(
                sub["baseline_vol_bps"].to_numpy(dtype=float), base_ret)
            rows.append(r)
    out = pd.DataFrame(rows)
    return out


def tier_print_study(fp: pd.DataFrame) -> pd.DataFrame:
    return _print_study(fp, "tier_impulse_total", [0, 1, 2, 3, 4, "4+"])


def p90_print_study(fp: pd.DataFrame) -> pd.DataFrame:
    return _print_study(fp, "p90_total", [0, 1, 2, 3, "3+"])


def tier_p90_combinatorics(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 6: simple state combos + count combos, min-support rules."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        t = g["tier_impulse_total"]
        p = g["p90_total"]
        combos = {
            "Tier>=1_P90>=1": (t >= 1) & (p >= 1),
            "Tier>=1_P90=0": (t >= 1) & (p == 0),
            "Tier=0_P90>=1": (t == 0) & (p >= 1),
            "Tier=0_P90=0": (t == 0) & (p == 0),
            "1T_1P": (t == 1) & (p == 1),
            "2T_1P": (t == 2) & (p == 1),
            "1T_2P": (t == 1) & (p == 2),
            "2T_2P": (t == 2) & (p == 2),
            "3+T_0P": (t >= 3) & (p == 0),
            "0T_2+P": (t == 0) & (p >= 2),
            "3+T_3+P": (t >= 3) & (p >= 3),
        }
        for name, mask in combos.items():
            sub = g[mask]
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["combo"] = name
            r["eligible"] = bool(len(sub) >= MIN_SUPPORT)
            r["status"] = "research" if r["eligible"] else "exploratory"
            rows.append(r)
    return pd.DataFrame(rows)


def ratio_study(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 7: quantile bins of the four descriptive ratios."""
    ratios = ["tier_to_p90_ratio", "p90_to_tier_ratio",
              "aligned_commitment_ratio", "opposition_ratio"]
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for col in ratios:
            v = g[col].to_numpy(dtype=float)
            # qcut with duplicates dropped may yield fewer bins; label by rank
            q = pd.qcut(pd.Series(v, index=g.index), q=4, labels=False,
                        duplicates="drop")
            nq = int(q.nunique())
            for qi in range(nq):
                qname = f"Q{qi + 1}"
                sub = g[q == qi]
                if len(sub) == 0:
                    continue
                r = _metrics(sub, fam_n)
                r["family"] = fid
                r["ratio"] = col
                r["quantile"] = qname
                r["ratio_min"] = float(sub[col].min())
                r["ratio_max"] = float(sub[col].max())
                rows.append(r)
    return pd.DataFrame(rows)


def sequence_grammar(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief sections 8 + 11: sequence codes (depth <= 4) with outcomes."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for code, sub in g.groupby("sequence_code"):
            if code == "" or code != code:  # NaN
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["sequence_code"] = code
            r["eligible"] = bool(len(sub) >= MIN_SUPPORT)
            r["status"] = "research" if r["eligible"] else "exploratory"
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            rows.append(r)
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("n", ascending=False).reset_index(drop=True)
    return out


def midpoint_study(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 9: midpoint start state, confirmation latency, whips."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for st in ["above", "below", "na"]:
            sub = g[g["midpoint_start_state"] == st]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["midpoint_start_state"] = st
            rows.append(r)
        # aligned midpoint confirmation within 60m
        alg = (g["mid_cross_aligned"] >= 1) & (g["mid_cross_first_min"] <= 60)
        for name, mask in [("aligned_confirm_60m", alg),
                           ("no_aligned_confirm_60m", ~alg),
                           ("mid_cross_present", g["mid_cross_total"] >= 1),
                           ("mid_cross_absent", g["mid_cross_total"] == 0)]:
            sub = g[mask]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["midpoint_start_state"] = name
            rows.append(r)
        # multiple whips: cross count >= 3
        sub = g[g["mid_cross_total"] >= 3]
        if len(sub):
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["midpoint_start_state"] = "multiple_whips_3+"
            rows.append(r)
    return pd.DataFrame(rows)


def rekey_study(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 10: rekey presence, alignment, success/failure."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        combos = {
            "rekey_present": g["rekey_total"] >= 1,
            "rekey_absent": g["rekey_total"] == 0,
            "aligned_rekey": g["rekey_aligned"] >= 1,
            "opposed_rekey": g["rekey_opposed"] >= 1,
            "rekey_success": g["rekey_success"] >= 1,
            "rekey_failure_only": (g["rekey_failure"] >= 1)
                                  & (g["rekey_success"] == 0),
            "aligned_seq_no_rekey": (g["tier_impulse_aligned"] >= 1)
                                    & (g["rekey_total"] == 0),
        }
        for name, mask in combos.items():
            sub = g[mask]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["rekey_state"] = name
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            rows.append(r)
    return pd.DataFrame(rows)


def tier_conditioned_fingerprints(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 12: daily tier x intrawindow fingerprint combos."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for tier in ["T1", "T2", "T3", "NO-GO", "NA"]:
            g_t = g[g["daily_tier"] == tier]
            if len(g_t) == 0:
                continue
            conds = {
                "baseline": g_t["daily_tier"] == tier,
                "tier_impulse_present": g_t["tier_impulse_total"] >= 1,
                "aligned_tier_impulse": g_t["tier_impulse_aligned"] >= 1,
                "p90_present": g_t["p90_total"] >= 1,
                "aligned_p90": g_t["p90_aligned"] >= 1,
                "aligned_midpoint_p90": (g_t["mid_cross_aligned"] >= 1)
                                        & (g_t["p90_total"] >= 1),
                "aligned_rekey_p90": (g_t["rekey_aligned"] >= 1)
                                     & (g_t["p90_total"] >= 1),
                "high_print_no_p90": (g_t["tier_impulse_total"] >= 2)
                                     & (g_t["p90_total"] == 0),
            }
            for cname, mask in conds.items():
                sub = g_t[mask]
                if len(sub) == 0:
                    continue
                r = _metrics(sub, fam_n)
                r["family"] = fid
                r["daily_tier"] = tier
                r["fingerprint"] = cname
                r["eligible"] = bool(len(sub) >= MIN_SUPPORT)
                r["status"] = "research" if r["eligible"] else "exploratory"
                rows.append(r)
    return pd.DataFrame(rows)


def time_to_primitive(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 13: P(win | primitive before x minutes)."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for pt in ["p90", "tier_impulse", "rekey", "mid_cross"]:
            col = f"{pt}_first_min"
            for x in [15, 30, 45, 60, 90, 120]:
                sub = g[g[col] <= x]
                if len(sub) == 0:
                    continue
                r = _metrics(sub, fam_n)
                r["family"] = fid
                r["primitive"] = pt
                r["within_min"] = x
                rows.append(r)
            # never occurs within 120m
            sub = g[g[col].isna() | (g[col] > 120)]
            if len(sub):
                r = _metrics(sub, fam_n)
                r["family"] = fid
                r["primitive"] = pt
                r["within_min"] = "none_120m"
                rows.append(r)
    return pd.DataFrame(rows)


def missing_primitive_vetoes(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 14: absence states as potential VETO logic."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        states = {
            "no_tier_by_30m": (g["tier_impulse_total"] == 0)
                              | (g["tier_impulse_first_min"] > 30),
            "no_tier_by_60m": (g["tier_impulse_total"] == 0)
                              | (g["tier_impulse_first_min"] > 60),
            "tier_no_p90_by_60m": (g["tier_impulse_total"] >= 1)
                                  & ((g["p90_total"] == 0)
                                     | (g["p90_first_min"] > 60)),
            "p90_no_tier": (g["p90_total"] >= 1) & (g["tier_impulse_total"] == 0),
            "tier_p90_no_midpoint": (g["tier_impulse_total"] >= 1)
                                    & (g["p90_total"] >= 1)
                                    & (g["mid_cross_total"] == 0),
            "tier_p90_mid_no_rekey": (g["tier_impulse_total"] >= 1)
                                     & (g["p90_total"] >= 1)
                                     & (g["mid_cross_total"] >= 1)
                                     & (g["rekey_total"] == 0),
            "opposed_rekey_after_aligned": (g["tier_impulse_aligned"] >= 1)
                                           & (g["rekey_opposed"] >= 1),
        }
        for name, mask in states.items():
            sub = g[mask]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["absence_state"] = name
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            rows.append(r)
    return pd.DataFrame(rows)


def saturation_study(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 15: nonlinearity in primitive counts."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for col, cats in [("tier_impulse_total", [0, 1, 2, 3, 4, "4+"]),
                          ("p90_total", [0, 1, 2, 3, "3+"])]:
            for cat in cats:
                sub = g[g[col] == cat]
                if len(sub) == 0:
                    continue
                r = _metrics(sub, fam_n)
                r["family"] = fid
                r["primitive"] = col
                r["count"] = cat
                r["density_mean"] = float(sub["primitive_density"].mean())
                rows.append(r)
    return pd.DataFrame(rows)


def incremental_information(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 19: sequential incremental information."""
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        stages = {
            "baseline_routing_event": pd.Series(True, index=g.index),
            "+daily_tier_known": g["daily_tier"].isin(["T1", "T2", "T3", "NO-GO"]),
            "+tier_stream": g["tier_impulse_total"] >= 1,
            "+p90_stream": (g["tier_impulse_total"] >= 1) & (g["p90_total"] >= 1),
            "+midpoint": (g["tier_impulse_total"] >= 1) & (g["p90_total"] >= 1)
                         & (g["mid_cross_aligned"] >= 1),
            "+rekey": (g["tier_impulse_total"] >= 1) & (g["p90_total"] >= 1)
                      & (g["mid_cross_aligned"] >= 1) & (g["rekey_aligned"] >= 1),
        }
        for name, mask in stages.items():
            sub = g[mask]
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["stage"] = name
            rows.append(r)
    return pd.DataFrame(rows)


def equal_weight_score(fp: pd.DataFrame) -> pd.DataFrame:
    """Brief section 20: simple equal-weight primitive score (descriptive only)."""
    def _score(r):
        s = 0.0
        if r["tier_impulse_aligned"] >= 1:
            s += 1
        if r["tier_impulse_opposed"] >= 1:
            s -= 1
        if r["p90_aligned"] >= 1:
            s += 1
        if r["p90_opposed"] >= 1:
            s -= 1
        if r["mid_cross_aligned"] >= 1:
            s += 1
        if r["mid_cross_opposed"] >= 1:
            s -= 1
        if r["rekey_aligned"] >= 1:
            s += 1
        if r["rekey_opposed"] >= 1:
            s -= 1
        return s

    fp = fp.copy()
    fp["primitive_score"] = fp.apply(_score, axis=1)
    rows = []
    for fid, g in fp.groupby("family"):
        fam_n = len(g)
        for score in sorted(g["primitive_score"].unique()):
            sub = g[g["primitive_score"] == score]
            if len(sub) == 0:
                continue
            r = _metrics(sub, fam_n)
            r["family"] = fid
            r["score"] = int(score)
            r = _add_ci(r, sub["baseline_vol_bps"].to_numpy(dtype=float))
            rows.append(r)
        # monotonicity check: spearman(score, expectancy) across score cells
        cells = []
        for score, sub in g.groupby("primitive_score"):
            cells.append((score, float(sub["baseline_vol_bps"].mean())))
        cells = sorted(cells)
        if len(cells) >= 3:
            from numpy import corrcoef
            xs = np.array([c[0] for c in cells])
            ys = np.array([c[1] for c in cells])
            if xs.std() > 0 and ys.std() > 0:
                rho = float(corrcoef(xs, ys)[0, 1])
            else:
                rho = np.nan
            rows.append({"family": fid, "score": "SPEARMAN",
                         "n": fam_n, "coverage": 1.0,
                         "expectancy_bps": rho})
    return pd.DataFrame(rows)
