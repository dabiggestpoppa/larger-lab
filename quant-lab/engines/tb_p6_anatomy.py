#!/usr/bin/env python3
"""
TB-P6-ENTRY-ANATOMY-01
======================
ENTRY RESEARCH ONLY. No exit/hold/stop/pyramiding/scaling/risk work (per
TB-P6-ENTRY-ANATOMY-01 spec and TB_P6_PROTOCOL.md, which pre-registers the
split/metrics/gates BEFORE any outcome is viewed).

Phases (mirrors the protocol git cadence):
  --phase p61   entry-threshold surface (predeclared z grid 1.50..4.00) + plateaus
  --phase p62   further-extension anatomy (paths, convergence surface, hypotheses)
  --phase p63   session-clock timing study
  --phase p64   dislocation-quality fingerprint + quality conditionals +
                cost stress (1.0-3.0x) + execution/lot translation
  --phase seal  candidate classification + TB_P6_DECISION.json + final report
  --phase all   p61 -> p62 -> p63 -> p64 -> seal (full reproduction)

All weights/pnl use the frozen TB-P5 machinery (project_basket with hard
residual guard; flat 10.2 pips cost; causal entry-time construction).
Deterministic: every RNG use seeded (SEED=42).

Run:  python quant-lab/engines/tb_p6_anatomy.py --phase all
Test: python quant-lab/engines/tb_p6_tests.py
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from tb_p5_validate import (  # noqa: E402
    ROOT, ART, LIVE, OUT, LOOKBACK, ENTRY_Z, STOP_Z, EXIT_Z,
    LONDON_START_H_EST, LONDON_END_H_EST, MIN_MINUTES_TO_EXIT,
    MAX_DAILY_LOSS_PIPS, ATR_PERIOD, MAX_TOTAL_LEVERAGE, PIP, COSTS_PIPS,
    CUR_TO_USD, CONTRACT, VOL_MIN, VOL_STEP, EPS_VARIANTS, MODELS, PAIRS,
    load_research_pairs, compute_basis_z, compute_atr, metrics,
    compare_to_log,
)
from verify_tb_04a import (  # noqa: E402
    exposure_matrix, residual_pct, project_basket as _pb_orig, trade_leg_pips,
    basket_pnl,
)


def _null_fast(E: np.ndarray):
    """Exact-neutral point: normalized smallest-right-singular-vector of E
    (E is numerically full-rank, so the 'null space' is the ~0.02% residual
    floor — this reproduces the frozen trust-constr eps=0 solution to ~1e-7
    in weights, within the documented 0.1% guard)."""
    _, _, vh = np.linalg.svd(E)
    v = vh[-1]
    for cand in (v, -v):
        sm = cand.sum()
        if abs(sm) < 1e-12:
            continue
        q = cand / sm
        if np.all(q >= -1e-9):
            q = np.clip(q, 0.0, None)
            q = q / q.sum()
            if residual_pct(q, E) <= 0.1 + 1e-4:
                return q
    return None


def _project_fast(q_alpha: np.ndarray, E: np.ndarray, eps: float):
    """Exact convex projection for eps>0 via active-boundary enumeration
    (3 variables => the feasible polygon's optimum is q_alpha itself, on an
    edge, or at a vertex). Residual cap enforced to 1e-6; returns None if no
    feasible point is found (caller falls back to trust-constr)."""
    if residual_pct(q_alpha, E) <= eps + 1e-12:
        return q_alpha
    t = eps / 100.0
    rows = []
    for j in range(3):
        rows.append((E[j].copy(), t))     # (E q)_j = t
        rows.append((E[j].copy(), -t))    # (E q)_j = -t
    for i in range(3):
        e = np.zeros(3)
        e[i] = 1.0
        rows.append((e, 0.0))             # q_i = 0
    sumrow = np.ones(3)
    best, best_obj = None, np.inf
    cand_sets = ([[i] for i in range(len(rows))]
                 + [[i, j] for i in range(len(rows))
                    for j in range(i + 1, len(rows))])
    for S in cand_sets:
        M = np.vstack([sumrow] + [rows[s][0] for s in S])
        b = np.concatenate([[1.0], [rows[s][1] for s in S]])
        try:
            if M.shape[0] == M.shape[1]:
                q = np.linalg.solve(M, b)
            else:
                q = q_alpha + M.T @ np.linalg.solve(M @ M.T, b - M @ q_alpha)
        except np.linalg.LinAlgError:
            continue
        if np.any(q < -1e-9):
            continue
        if residual_pct(q, E) > eps + 1e-6:
            continue
        obj = float(np.sum((q - q_alpha) ** 2))
        if obj < best_obj:
            best_obj, best = obj, q
    return best


def project_basket(q_alpha: np.ndarray, E: np.ndarray, eps: float) -> np.ndarray:
    """Frozen project_basket semantics with a fast exact path (~10us vs ~30ms
    trust-constr). eps=0 -> smallest-singular-vector exact-neutral point
    (matches the frozen trust-constr solution to ~1e-7 weights); eps>0 -> exact
    boundary enumeration with the residual cap enforced. Falls back to the
    frozen trust-constr solver if no feasible point is found."""
    if eps <= 0:
        q = _null_fast(E)
        if q is not None:
            return 3.0 * q
        return _pb_orig(q_alpha, E, eps)
    q = _project_fast(q_alpha, E, eps)
    if q is not None:
        return 3.0 * q
    return _pb_orig(q_alpha, E, eps)

SEED = 42
GRID = [1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00]
NEUTRAL = ["TB-B"] + [f"TB-C-{e:g}%" for e in EPS_VARIANTS]
COST_MULTS = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
NOTIONALS = [5000, 10000, 25000, 50000, 100000]
CACHE = Path(__file__).parent / "tb_p6_cache"
CACHE.mkdir(parents=True, exist_ok=True)
RESULT_CODE = {"TP_HIT": 0, "SL_HIT": 1, "TIMEOUT": 2}
RESULT_NAME = {v: k for k, v in RESULT_CODE.items()}
P5_HOLDOUT = pd.Timestamp("2025-07-01")


def san(m: str) -> str:
    return m.replace(".", "p").replace("%", "pct").replace("-", "_")


def eps_of(m: str) -> float:
    if m == "TB-A":
        return None
    if m == "TB-B":
        return 0.0
    return float(m.split("%")[0].split("-")[-1])


# ═══════════════════════════════════════════════════════════════════════
# FROZEN-SIGNAL REPLAY, PARAMETERIZED BY ENTRY THRESHOLD (causal)
# ═══════════════════════════════════════════════════════════════════════

def simulate(df: pd.DataFrame, thr: float) -> pd.DataFrame:
    """Mirror of tb_p5_validate.run_frozen_signal with the entry threshold
    parameterized. Uses only past data: rolling-200 z with window ending
    before the current bar, ATR-20 window ending at the entry bar, London
    session 3-12 EST, min 120 min to session end, exit z->0 / |z|->6 /
    session-end timeout, daily -500 pips cap. At thr=2.5 it must reproduce
    the canonical 405-trade log exactly (asserted by load_and_verify)."""
    idx = df.index
    n = len(df)
    basis = (np.log(df["ga"]) - np.log(df["gn"]) + np.log(df["an"])).values
    z = compute_basis_z(pd.Series(basis, index=idx), LOOKBACK).values
    atr = {k: compute_atr(df[f"{l}_h"], df[f"{l}_l"], df[l].shift(1), ATR_PERIOD).values
           for k, l in [("GA", "ga"), ("GN", "gn"), ("AN", "an")]}
    # engine session-date rule (exact): roll to the next calendar day for
    # bars whose EST hour is >= 19 (pre-UTC-midnight bars belong to the
    # following London session day in the engine's daily-PnL accounting)
    est_h = ((df.index.hour - 5) % 24).tolist()
    sdate = [d.toordinal() + (1 if h >= 19 else 0)
             for d, h in zip(df.index.date, est_h)]
    z_l = z.tolist()
    b_l = basis.tolist()
    ga = df["ga"].values
    gn = df["gn"].values
    an = df["an"].values
    daily = defaultdict(float)
    trades = []
    in_trade = False
    t = None
    for i in range(n):
        zi = z_l[i]
        eh = est_h[i]
        if in_trade:
            sd = sdate[i]
            dpl = daily.get(sd, 0.0)
            if dpl <= -MAX_DAILY_LOSS_PIPS:
                in_trade = False
                t = None
                continue
            if eh >= LONDON_END_H_EST:
                tr = _close_t(t, i, idx[i], zi, b_l[i], ga, gn, an, "TIMEOUT")
                daily[sd] = dpl + tr["pnl_net_pips"]
                trades.append(tr)
                in_trade = False
                t = None
                continue
            res = None
            if t["direction"] == "SHORT":
                if zi <= EXIT_Z:
                    res = "TP_HIT"
                elif zi >= STOP_Z:
                    res = "SL_HIT"
            else:
                if zi >= EXIT_Z:
                    res = "TP_HIT"
                elif zi <= -STOP_Z:
                    res = "SL_HIT"
            if res:
                tr = _close_t(t, i, idx[i], zi, b_l[i], ga, gn, an, res)
                daily[sd] = dpl + tr["pnl_net_pips"]
                trades.append(tr)
                in_trade = False
                t = None
        else:
            if not (LONDON_START_H_EST <= eh < LONDON_END_H_EST):
                continue
            if (LONDON_END_H_EST - eh) * 60 < MIN_MINUTES_TO_EXIT:
                continue
            if abs(zi) > thr:
                t = _open_t(i, idx[i], zi, b_l[i], atr, ga, gn, an)
                in_trade = True
    if in_trade and t is not None:
        trades.append(_close_t(t, n - 1, idx[n - 1], z_l[n - 1], b_l[n - 1], ga, gn, an,
                               "TIMEOUT"))
    return pd.DataFrame(trades)


def _open_t(i, ts, zi, bi, atr, ga, gn, an):
    sz = {}
    for k in ["GA", "GN", "AN"]:
        a = float(atr[k][i])
        sz[k] = 1.0 / a if a > 0 else 1.0
    tot = sum(sz.values())
    scale = MAX_TOTAL_LEVERAGE / tot if tot > 0 else 1.0
    return {"entry_idx": i, "entry_time": ts, "direction": "SHORT" if zi > 0 else "LONG",
            "entry_basis": float(bi), "entry_zscore": float(zi),
            "entry_ga": float(ga[i]), "entry_gn": float(gn[i]), "entry_an": float(an[i]),
            "size_ga": sz["GA"] * scale, "size_gn": sz["GN"] * scale,
            "size_an": sz["AN"] * scale}


def _close_t(t, i, ts, zi, bi, ga, gn, an, result):
    e = {"gbpaud": t["entry_ga"], "gbpnzd": t["entry_gn"], "audnzd": t["entry_an"]}
    x = {"gbpaud": float(ga[i]), "gbpnzd": float(gn[i]), "audnzd": float(an[i])}
    leg = trade_leg_pips(e, x, t["direction"])
    s = {"gbpaud": t["size_ga"], "gbpnzd": t["size_gn"], "audnzd": t["size_an"]}
    gross = basket_pnl(s, leg)
    costs = COSTS_PIPS * sum(s.values()) / MAX_TOTAL_LEVERAGE
    return {"entry_time": t["entry_time"], "exit_time": ts, "direction": t["direction"],
            "entry_basis": t["entry_basis"], "exit_basis": float(bi),
            "entry_zscore": t["entry_zscore"], "exit_zscore": float(zi),
            "result": result,
            "pnl_gross_pips": gross, "pnl_costs_pips": costs, "pnl_net_pips": gross - costs,
            "size_ga": t["size_ga"], "size_gn": t["size_gn"], "size_an": t["size_an"],
            "entry_idx": t["entry_idx"], "exit_idx": i,
            "entry_ga": t["entry_ga"], "entry_gn": t["entry_gn"], "entry_an": t["entry_an"]}


# ═══════════════════════════════════════════════════════════════════════
# WEIGHTS (frozen TB-P5 path) + per-model PnL
# ═══════════════════════════════════════════════════════════════════════

def enrich(sim: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Per trade: TB-A/B/C weights (entry-time functions), per-model net/gross
    pnl (basket_pnl - 10.2 flat), residual. Mirrors tb_p5_validate.build_weights_and_pnl."""
    rows = []
    for _, r in sim.iterrows():
        pe = {"gbpaud": r["entry_ga"], "gbpnzd": r["entry_gn"], "audnzd": r["entry_an"]}
        px = {"gbpaud": float(df["ga"].iloc[r["exit_idx"]]),
              "gbpnzd": float(df["gn"].iloc[r["exit_idx"]]),
              "audnzd": float(df["an"].iloc[r["exit_idx"]])}
        q_a = np.array([r["size_ga"], r["size_gn"], r["size_an"]])
        q_a = q_a / q_a.sum()
        E = exposure_matrix(pe, r["direction"])
        leg = trade_leg_pips(pe, px, r["direction"])
        rec = {"entry_time": r["entry_time"], "exit_time": r["exit_time"],
               "entry_idx": r["entry_idx"], "exit_idx": r["exit_idx"],
               "direction": r["direction"], "entry_basis": r["entry_basis"],
               "exit_basis": r["exit_basis"], "entry_zscore": r["entry_zscore"],
               "exit_zscore": r["exit_zscore"], "result": r["result"],
               "entry_ga": r["entry_ga"], "entry_gn": r["entry_gn"], "entry_an": r["entry_an"],
               "q_ga": q_a[0], "q_gn": q_a[1], "q_an": q_a[2]}
        for m in MODELS:
            s = 3.0 * q_a if m == "TB-A" else project_basket(q_a, E, eps_of(m))
            rec[f"{m}_s0"], rec[f"{m}_s1"], rec[f"{m}_s2"] = float(s[0]), float(s[1]), float(s[2])
            gross = basket_pnl({"gbpaud": s[0], "gbpnzd": s[1], "audnzd": s[2]}, leg)
            rec[f"{m}_pnl_net"] = gross - COSTS_PIPS
            rec[f"{m}_pnl_gross"] = gross
            rec[f"{m}_resid"] = residual_pct(s / 3.0, E)
        rows.append(rec)
    return pd.DataFrame(rows)


def model_path_stats(r, s, df):
    """First-order intra-trade PnL path (exact to second order; used for
    MFE/MAE/time-to-extreme; ends at net pnl by construction)."""
    i0, i1 = int(r["entry_idx"]), int(r["exit_idx"])
    seg = df.iloc[i0:i1 + 1]
    b = (np.log(seg["ga"]) - np.log(seg["gn"]) + np.log(seg["an"])).values
    rga = np.log(seg["ga"].values / r["entry_ga"])
    ran = np.log(seg["an"].values / r["entry_an"])
    d = 1.0 if r["direction"] == "LONG" else -1.0
    w = {"gbpaud": s[0] * r["entry_ga"] / PIP, "gbpnzd": s[1] * r["entry_gn"] / PIP,
         "audnzd": s[2] * r["entry_an"] / PIP}
    path = (d * w["gbpnzd"] * (b - r["entry_basis"])
            + d * (w["gbpaud"] - w["gbpnzd"]) * rga
            + d * (w["audnzd"] - w["gbpnzd"]) * ran
            - COSTS_PIPS)
    return float(path.max()), float(path.min()), int(path.argmax()) * 5, int(path.argmin()) * 5


# ═══════════════════════════════════════════════════════════════════════
# CACHE (per-threshold trades; regenerated by --phase all / p61)
# ═══════════════════════════════════════════════════════════════════════

def cache_write(thr: float, pt: pd.DataFrame):
    arrs = {"entry_idx": pt["entry_idx"].values.astype(np.int64),
            "exit_idx": pt["exit_idx"].values.astype(np.int64),
            "entry_ts": pt["entry_time"].values.astype("datetime64[ns]"),
            "exit_ts": pt["exit_time"].values.astype("datetime64[ns]"),
            "entry_ga": pt["entry_ga"].values, "entry_gn": pt["entry_gn"].values,
            "entry_an": pt["entry_an"].values,
            "dir": (pt["direction"] == "SHORT").values.astype(np.int8),
            "entry_basis": pt["entry_basis"].values,
            "exit_basis": pt["exit_basis"].values,
            "entry_z": pt["entry_zscore"].values,
            "result": pt["result"].map(RESULT_CODE).values.astype(np.int8),
            "qa": pt[["q_ga", "q_gn", "q_an"]].values}
    for m in MODELS:
        arrs[f"sizes_{san(m)}"] = pt[[f"{m}_s0", f"{m}_s1", f"{m}_s2"]].values
        arrs[f"pnl_net_{san(m)}"] = pt[f"{m}_pnl_net"].values
        arrs[f"pnl_gross_{san(m)}"] = pt[f"{m}_pnl_gross"].values
        arrs[f"resid_{san(m)}"] = pt[f"{m}_resid"].values
    np.savez(CACHE / f"thr_{thr:g}.npz", **arrs)


def cache_load(thr: float, df: pd.DataFrame) -> pd.DataFrame:
    zf = np.load(CACHE / f"thr_{thr:g}.npz")
    pt = pd.DataFrame({
        "entry_time": pd.to_datetime(zf["entry_ts"]), "exit_time": pd.to_datetime(zf["exit_ts"]),
        "entry_idx": zf["entry_idx"], "exit_idx": zf["exit_idx"],
        "direction": np.where(zf["dir"] == 1, "SHORT", "LONG"),
        "entry_basis": zf["entry_basis"], "exit_basis": zf["exit_basis"],
        "entry_zscore": zf["entry_z"],
        "entry_ga": zf["entry_ga"], "entry_gn": zf["entry_gn"], "entry_an": zf["entry_an"],
        "result": [RESULT_NAME[int(c)] for c in zf["result"]],
        "q_ga": zf["qa"][:, 0], "q_gn": zf["qa"][:, 1], "q_an": zf["qa"][:, 2]})
    for m in MODELS:
        s = zf[f"sizes_{san(m)}"]
        pt[f"{m}_s0"], pt[f"{m}_s1"], pt[f"{m}_s2"] = s[:, 0], s[:, 1], s[:, 2]
        pt[f"{m}_pnl_net"] = zf[f"pnl_net_{san(m)}"]
        pt[f"{m}_pnl_gross"] = zf[f"pnl_gross_{san(m)}"]
        pt[f"{m}_resid"] = zf[f"resid_{san(m)}"]
    return pt


def sizes_of(pt: pd.DataFrame, m: str) -> np.ndarray:
    return pt[[f"{m}_s0", f"{m}_s1", f"{m}_s2"]].values


# ═══════════════════════════════════════════════════════════════════════
# DATA + INTEGRITY GATES (fail-closed)
# ═══════════════════════════════════════════════════════════════════════

def load_and_verify() -> pd.DataFrame:
    bp = pd.read_csv(LIVE / "bar_parity.csv", parse_dates=["timestamp"])
    bp = bp.set_index("timestamp").sort_index()
    bp.columns = ["ga", "gn", "an"]
    syn = load_research_pairs()
    j = syn[["ga", "gn", "an"]].join(bp, lsuffix="_s", rsuffix="_p", how="inner")
    dmax = max((j["ga_s"] - j["ga_p"]).abs().max(), (j["gn_s"] - j["gn_p"]).abs().max(),
               (j["an_s"] - j["an_p"]).abs().max())
    assert dmax < 1e-9, f"sync vs parity close diff {dmax}"
    assert abs(len(syn) - 265809) < 100, f"bar count {len(syn)}"
    sim = simulate(syn, ENTRY_Z)
    log = pd.read_csv(LIVE / "canonical_trade_log.csv",
                      parse_dates=["entry_time", "exit_time"])
    cmp = compare_to_log(sim, log)
    if not cmp["exact_match"]:
        raise SystemExit(f"[P6 FAIL-CLOSED] frozen signal at z=2.5 does not reproduce "
                         f"canonical 405-trade log: {cmp}")
    # independent cross-check vs TB-P5 weights CSV (different implementation).
    # The P6 fast exact-neutral solver reproduces the frozen trust-constr
    # solution to ~1e-5 pips (solver-tolerance scale); gate at 1e-4 pips.
    p5f = OUT / "TB_P5_PER_TRADE_WEIGHTS.csv"
    if p5f.exists():
        p5 = pd.read_csv(p5f, parse_dates=["entry_time"])
        pt0 = enrich(sim, syn)
        merged = pt0.merge(p5[["entry_time", "TB-B_pnl_net"]], on="entry_time", how="inner",
                           suffixes=("", "_p5"))
        assert len(merged) == 405, f"P5 cross-check merge {len(merged)} != 405"
        d = (merged["TB-B_pnl_net"] - merged["TB-B_pnl_net_p5"]).abs().max()
        assert d < 1e-4, f"P6 TB-B pnl vs P5 pnl mismatch {d}"
    print(f"[P6] integrity gates OK: bars={len(syn)}, 405/405 exact, "
          f"TB-B cross-check vs P5 OK")
    return syn


# ═══════════════════════════════════════════════════════════════════════
# P6.1 — ENTRY THRESHOLD SURFACE (predeclared grid) + PLATEAUS
# ═══════════════════════════════════════════════════════════════════════

BASE_IDX = GRID.index(ENTRY_Z)


def _year_blocks(pt: pd.DataFrame, m: str) -> dict:
    ptc = pt.copy()
    ptc["year"] = [d.year for d in ptc["exit_time"]]
    out = {}
    for y, g in ptc.groupby("year"):
        net = g[f"{m}_pnl_net"].values
        if len(net) >= 10:
            mm = metrics(net)
            out[y] = {"ev": mm["expectancy_pips"], "pf": mm["profit_factor"], "n": len(net)}
    return out


def p61(df: pd.DataFrame):
    print("[P6.1] entry-threshold surface...")
    rows = []
    base_n = len(simulate(df, ENTRY_Z))
    for thr in GRID:
        sim = simulate(df, thr)
        pt = enrich(sim, df)
        cache_write(thr, pt)
        dates = pt["exit_time"]
        span = (pt["exit_time"].max() - pt["entry_time"].min()).days / 365.25
        n = len(pt)
        if thr == ENTRY_Z:
            base_n = n
        for m in MODELS:
            mm = metrics(pt[f"{m}_pnl_net"].values, dates, span)
            mfes, maes, tmfe, tmae, conv = [], [], [], [], []
            for _, r in pt.iterrows():
                s = sizes_of(pt, m)[int(r.name)]
                mfe, mae, t1, t2 = model_path_stats(r, s, df)
                mfes.append(mfe); maes.append(mae); tmfe.append(t1); tmae.append(t2)
                if r["result"] == "TP_HIT":
                    conv.append((r["exit_time"] - r["entry_time"]).total_seconds() / 60)
            net = pt[f"{m}_pnl_net"].values
            gross_edge = float(net.sum() + COSTS_PIPS * n)
            cost_share = (COSTS_PIPS * n / gross_edge * 100) if gross_edge > 0 else float("nan")
            fail = float((pt["result"] != "TP_HIT").mean() * 100)
            rows.append({"threshold": thr, "model": m, "n_trades": n,
                         "coverage_pct": n / base_n * 100,
                         "win_rate_pct": mm["win_rate_pct"],
                         "expectancy_pips": mm["expectancy_pips"],
                         "profit_factor": mm["profit_factor"], "net_pips": mm["net_pips"],
                         "median_trade_pips": mm["median_trade_pips"],
                         "avg_win_pips": mm["avg_win_pips"], "avg_loss_pips": mm["avg_loss_pips"],
                         "payoff_ratio": mm["payoff_ratio"], "max_dd_pips": mm["max_dd_pips"],
                         "sharpe_ann": mm["sharpe_ann"], "sortino_ann": mm["sortino_ann"],
                         "mfe_median_pips": float(np.median(mfes)),
                         "mae_median_pips": float(np.median(maes)),
                         "time_to_mfe_median_min": float(np.median(tmfe)),
                         "time_to_mae_median_min": float(np.median(tmae)),
                         "median_convergence_min": float(np.median(conv)) if conv else float("nan"),
                         "failure_rate_pct": fail,
                         "cost_share_of_gross_edge_pct": cost_share,
                         "median_residual_pct": float(np.median(pt[f"{m}_resid"]))})
    surf = pd.DataFrame(rows)
    surf.to_csv(OUT / "P6_ENTRY_THRESHOLD_SURFACE.csv", index=False)
    write_plateaus(surf)
    print(f"[P6.1] surface written ({len(surf)} rows); baseline N={base_n}")


def find_plateaus(evs: list) -> list:
    """Contiguous runs of >= 3 grid points with spread <= 15% of run max and
    run max >= baseline (z=2.5) EV. Maximal runs only."""
    n = len(evs)
    cand = []
    for i in range(n):
        for j in range(i + 2, n):
            run = evs[i:j + 1]
            mx = max(run)
            if mx <= 0:
                continue
            if (max(run) - min(run)) / mx <= 0.15 and mx >= evs[BASE_IDX] - 1e-12:
                cand.append((i, j, (max(run) - min(run)) / mx, mx))
    keep = []
    for c in sorted(cand, key=lambda c: -(c[1] - c[0])):
        if not any(c[0] >= k[0] and c[1] <= k[1] for k in keep):
            keep.append(c)
    return sorted(keep)


def write_plateaus(surf: pd.DataFrame):
    lines = ["# P6.1 — ENTRY-THRESHOLD PLATEAUS", "",
             "Rule (pre-registered in TB_P6_PROTOCOL.md): contiguous run of >= 3 grid "
             "points where EV spread <= 15% of the run max AND run max >= baseline "
             "(z=2.5) EV. Plateaus must also be chronologically stable (EV > 0 in >= 4 "
             "of 5 years; no year N>=10 with PF <= 1).", ""]
    for m in MODELS:
        sub = surf[surf["model"] == m].sort_values("threshold")
        evs = sub["expectancy_pips"].tolist()
        lines.append(f"## {m}")
        lines.append("")
        lines.append("| z | N | coverage | EV/trade | PF | WR | maxDD | MFE | MAE |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['threshold']:.2f} | {r['n_trades']} | {r['coverage_pct']:.0f}% | "
                         f"{r['expectancy_pips']:.2f} | {r['profit_factor']:.2f} | "
                         f"{r['win_rate_pct']:.1f}% | {r['max_dd_pips']:.0f} | "
                         f"{r['mfe_median_pips']:.1f} | {r['mae_median_pips']:.1f} |")
        plats = find_plateaus(evs)
        if plats:
            lines.append("")
            lines.append("**Plateaus (pre-registered rule):**")
            for (i, j, spread, mx) in plats:
                stable, weak = [], []
                for thr in GRID[i:j + 1]:
                    pt = cache_load(thr, None)
                    for y, yb in _year_blocks(pt, m).items():
                        if yb["ev"] > 0:
                            stable.append(y)
                        if yb["pf"] <= 1:
                            weak.append(y)
                lines.append(f"- z {GRID[i]:.2f}..{GRID[j]:.2f}: spread {spread * 100:.1f}% of "
                             f"run max {mx:.2f} pips/trade; stable years (EV>0): "
                             f"{sorted(set(stable))}; weak years (PF<=1): "
                             f"{sorted(set(weak)) or 'none'}.")
        else:
            lines.append("")
            lines.append("- **No plateau** (pre-registered rule) — no contiguous run of >= 3 "
                         "grid points with spread <= 15% and run max >= baseline.")
        # cliffs / monotonic / saturation
        diffs = np.diff(evs)
        if np.all(diffs >= -1e-9):
            shape = "monotonic non-decreasing across the grid"
        elif np.all(diffs <= 1e-9):
            shape = "monotonic non-increasing across the grid"
        else:
            pk = int(np.argmax(evs))
            if np.all(np.diff(evs[:pk + 1]) >= -1e-9) and np.all(np.diff(evs[pk:]) <= 1e-9):
                shape = f"inverted-U (peak at z={GRID[pk]:.2f})"
            else:
                shape = "non-monotonic"
        cliffs = [GRID[i] for i in range(1, len(evs) - 1)
                  if evs[i] > evs[i - 1] and evs[i] > evs[i + 1]
                  and min(evs[i + 1:]) < 0.6 * evs[i]]
        sat = None
        for k in range(len(evs)):
            if all(evs[j] < evs[k] * 1.10 for j in range(k + 1, len(evs))):
                sat = GRID[k]
                break
        lines.append(f"- Shape: {shape}.")
        lines.append(f"- Cliffs (peak followed by >40% drop): {[f'{c:.2f}' for c in cliffs] or 'none'}.")
        lines.append(f"- Saturation point (no further >10% EV improvement beyond): "
                     f"{sat:.2f}" if sat else "- No saturation point detected.")
        lines.append("")
    (OUT / "P6_ENTRY_THRESHOLD_PLATEAUS.md").write_text("\n".join(lines) + "\n",
                                                         encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# SHARED CAUSAL HELPERS (session third, causal expanding tercile, vol)
# ═══════════════════════════════════════════════════════════════════════

def est_min_of(ts) -> int:
    return ((ts.hour - 5) % 24) * 60 + ts.minute


def session_third(ts) -> str:
    mins = est_min_of(ts) - LONDON_START_H_EST * 60
    if mins < 180:
        return "early"
    if mins < 360:
        return "mid"
    return "late"


def basis_vol_5m(df: pd.DataFrame) -> np.ndarray:
    b = np.log(df["ga"]) - np.log(df["gn"]) + np.log(df["an"])
    return b.diff().rolling(20).std().values


def causal_tercile(vals: np.ndarray, min_prior: int = 30):
    """Expanding tercile label using only prior trades' values (future info
    never enters). NaN until min_prior observations exist."""
    out = np.full(len(vals), np.nan, dtype=object)
    for i in range(min_prior, len(vals)):
        lo, hi = np.quantile(vals[:i], [1 / 3, 2 / 3])
        v = vals[i]
        out[i] = "LOW" if v <= lo else ("MED" if v <= hi else "HIGH")
    return out


# ═══════════════════════════════════════════════════════════════════════
# P6.2 — FURTHER-EXTENSION ANATOMY (measurement only)
# ═══════════════════════════════════════════════════════════════════════

LEVELS = [2.75, 3.00, 3.25, 3.50, 4.00, 4.50, 5.00, 6.00]
EXT_BINS = [2.5, 2.75, 3.0, 3.25, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, np.inf]


def _path_class(ext: float, tp: bool) -> str:
    if ext <= 0.1:
        return "IMMEDIATE_CONVERGENCE" if tp else "IMMEDIATE_PERSISTED"
    if ext < 1.0:
        return "SHALLOW_CONVERGED" if tp else "SHALLOW_FAILED"
    return "DEEP_CONVERGED" if tp else "DEEP_FAILED"


def p62(df: pd.DataFrame):
    print("[P6.2] further-extension anatomy...")
    pt = cache_load(ENTRY_Z, df)
    barr = (np.log(df["ga"]) - np.log(df["gn"]) + np.log(df["an"])).values
    zarr = compute_basis_z(pd.Series(barr, index=df.index), LOOKBACK).values
    vol5 = basis_vol_5m(df)
    vterc = causal_tercile(np.array([float(vol5[int(r["entry_idx"])]) for _, r in pt.iterrows()]))
    rows = []
    for k, (_, r) in enumerate(pt.iterrows()):
        i0, i1 = int(r["entry_idx"]), int(r["exit_idx"])
        zpath = zarr[i0:i1 + 1]
        post = zpath[1:]
        ea = abs(float(r["entry_zscore"]))
        if len(post):
            max_abs = float(np.max(np.abs(post)))
            t_max = int(np.argmax(np.abs(post))) + 1
        else:
            max_abs, t_max = ea, 0
        ext = max(0.0, max_abs - ea)
        dur = (r["exit_time"] - r["entry_time"]).total_seconds() / 60
        tp = r["result"] == "TP_HIT"
        row = {"entry_time": r["entry_time"], "direction": r["direction"],
               "entry_abs_z": ea, "max_abs_z": max_abs, "further_ext": ext,
               "time_to_max_ext_min": t_max * 5, "duration_min": dur,
               "result": r["result"], "path_class": _path_class(ext, tp),
               "pnl_tba": r["TB-A_pnl_net"], "pnl_tbb": r["TB-B_pnl_net"],
               "pnl_tbc5": r["TB-C-5%_pnl_net"],
               "vol_tercile": vterc[k] if vterc[k] == vterc[k] else "NA",
               "session_third": session_third(r["entry_time"])}
        for lv in LEVELS:
            row[f"reached_{lv:g}"] = bool(max_abs >= lv)
        for m in ["TB-A", "TB-B", "TB-C-5%"]:
            s = sizes_of(pt, m)[k]
            mfe, mae, _, _ = model_path_stats(r, s, df)
            row[f"{m}_mfe"], row[f"{m}_mae"] = mfe, mae
        rows.append(row)
    paths = pd.DataFrame(rows)
    paths.to_csv(OUT / "P6_FURTHER_EXTENSION_PATHS.csv", index=False)

    # convergence surface: P(conv) + E[PnL] by max-|z| bin
    srows = []
    for lo, hi in zip(EXT_BINS[:-1], EXT_BINS[1:]):
        sub = paths[(paths["max_abs_z"] >= lo) & (paths["max_abs_z"] < hi)]
        if len(sub) == 0:
            continue
        conv = sub[sub["result"] == "TP_HIT"]
        srows.append({"surface": "max_abs_z", "bin_lo": lo, "bin_hi": hi,
                      "n": len(sub), "p_converge": len(conv) / len(sub) * 100,
                      "p_sl": (sub["result"] == "SL_HIT").mean() * 100,
                      "p_timeout": (sub["result"] == "TIMEOUT").mean() * 100,
                      "ev_tba": sub["pnl_tba"].mean(), "ev_tbb": sub["pnl_tbb"].mean(),
                      "ev_tbc5": sub["pnl_tbc5"].mean(),
                      "mfe_tbb_med": sub["TB-B_mfe"].median(),
                      "mae_tbb_med": sub["TB-B_mae"].median(),
                      "conv_med_min": float((conv["duration_min"]).median())
                      if len(conv) else float("nan")})
    # hazard: P(convergence | current |z|, time since first signal)
    zb = [2.5, 3.0, 3.5, 4.0, 5.0, 6.0, np.inf]
    tb = [0, 15, 30, 60, 120, 240, np.inf]
    for zlo, zhi in zip(zb[:-1], zb[1:]):
        for tlo, thi in zip(tb[:-1], tb[1:]):
            obs = []
            for _, r in paths.iterrows():
                i0, i1 = int(pt.loc[r.name, "entry_idx"]), int(pt.loc[r.name, "exit_idx"])
                zseg = np.abs(zarr[i0 + 1:i1 + 1])
                times = np.arange(1, len(zseg) + 1) * 5
                m = (zseg >= zlo) & (zseg < zhi) & (times >= tlo) & (times < thi)
                if m.any():
                    obs.append((r["result"] == "TP_HIT", r["pnl_tbb"]))
            if obs:
                arr = np.array([o[0] for o in obs], dtype=float)
                pnls = np.array([o[1] for o in obs])
                srows.append({"surface": "z_t_hazard", "bin_lo": zlo, "bin_hi": zhi,
                              "bin_lo2": tlo, "bin_hi2": thi, "n": len(obs),
                              "p_converge": arr.mean() * 100, "ev_tbb": pnls.mean(),
                              "p_sl": float("nan"), "p_timeout": float("nan"),
                              "ev_tba": float("nan"), "ev_tbc5": float("nan"),
                              "mfe_tbb_med": float("nan"), "mae_tbb_med": float("nan"),
                              "conv_med_min": float("nan")})
    surf = pd.DataFrame(srows)
    surf.to_csv(OUT / "P6_EXTENSION_CONVERGENCE_SURFACE.csv", index=False)
    write_extension_report(paths, surf)
    print(f"[P6.2] extension anatomy written ({len(paths)} trades, "
          f"{len(surf)} surface cells)")


def write_extension_report(paths: pd.DataFrame, surf: pd.DataFrame):
    lines = ["# P6.2 — FURTHER-EXTENSION ANATOMY REPORT (measurement only)", "",
             "For every baseline (z=2.5) signal: post-entry |z| path, max further "
             "extension, time-to-max, levels reached, outcome, per-model PnL, MFE/MAE.",
             "No entry/exit rule is derived here — this is the measurement layer for a "
             "future (human-approved) optimization phase.", "",
             "## Class summary (path classes)", "",
             "| class | N | share | WR | EV TB-B | EV TB-C-5% | MFE med | MAE med | conv med |",
             "|---|---|---|---|---|---|---|---|---|"]
    for c, g in paths.groupby("path_class"):
        tp = g[g["result"] == "TP_HIT"]
        lines.append(f"| {c} | {len(g)} | {len(g) / len(paths) * 100:.0f}% | "
                     f"{len(tp) / len(g) * 100:.1f}% | {g['pnl_tbb'].mean():.2f} | "
                     f"{g['pnl_tbc5'].mean():.2f} | {g['TB-B_mfe'].median():.1f} | "
                     f"{g['TB-B_mae'].median():.1f} | {tp['duration_min'].median():.0f} |")
    lines += ["", "## P(convergence) and E[PnL] by max |z| reached", ""]
    mz = surf[surf["surface"] == "max_abs_z"]
    lines.append("| max|z| bin | N | P(conv) | P(SL) | P(timeout) | EV TB-A | EV TB-B | EV TB-C5% |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, r in mz.iterrows():
        lines.append(f"| [{r['bin_lo']:.2f}, {r['bin_hi']:.2f}) | {r['n']} | "
                     f"{r['p_converge']:.0f}% | {r['p_sl']:.0f}% | {r['p_timeout']:.0f}% | "
                     f"{r['ev_tba']:.1f} | {r['ev_tbb']:.1f} | {r['ev_tbc5']:.1f} |")
    lines += ["", "## Hypotheses (quantitative, none assumed true)", ""]
    evs = mz.sort_values("bin_lo")
    sp = evs["ev_tbb"].corr(pd.Series(np.arange(len(evs))))
    peak = evs["ev_tbb"].idxmax()
    peak_ev = evs.loc[peak, "ev_tbb"]
    last_ev = evs["ev_tbb"].iloc[-1]
    first_ev = evs["ev_tbb"].iloc[0]
    ext_high = paths[paths["max_abs_z"] >= 4.5]
    ext_low = paths[paths["max_abs_z"] < 4.5]
    p_high = (ext_high["result"] == "TP_HIT").mean()
    p_low = (ext_low["result"] == "TP_HIT").mean()
    lines.append(f"- **A (extension → higher expectancy):** rank correlation of EV(TB-B) vs "
                 f"max-|z| bin = {sp:.2f}; first-bin EV {first_ev:.1f}, last-bin EV "
                 f"{last_ev:.1f} → {'supported' if sp > 0.5 and last_ev > first_ev else 'NOT supported'}.")
    inv_u = (peak_ev > first_ev) and (last_ev < peak_ev * 0.7)
    lines.append(f"- **B (inverted-U / structural failure zone):** peak bin EV {peak_ev:.1f} vs "
                 f"final-bin EV {last_ev:.1f} → {'inverted-U pattern present' if inv_u else 'no inverted-U'}.")
    lines.append(f"- **C (extreme extension = regime break):** max|z| >= 4.5: N={len(ext_high)}, "
                 f"P(conv)={p_high * 100:.0f}% (vs {p_low * 100:.0f}% below 4.5), EV(TB-B) "
                 f"{ext_high['pnl_tbb'].mean():.1f} vs {ext_low['pnl_tbb'].mean():.1f} → "
                 f"{'regime-break evidence' if p_high < 0.5 else 'no regime-break evidence'}.")
    lines.append(f"- **D (differs by vol regime / session):** see class x vol / class x session "
                 f"table below (full data in P6_FURTHER_EXTENSION_PATHS.csv).")
    lines += ["", "## Class x volatility regime / session third (EV TB-B | P(conv))", ""]
    lines.append("| | early | mid | late | LOW vol | MED vol | HIGH vol |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in ["IMMEDIATE_CONVERGENCE", "SHALLOW_CONVERGED", "DEEP_CONVERGED",
              "SHALLOW_FAILED", "DEEP_FAILED"]:
        g = paths[paths["path_class"] == c]
        cells = []
        for col in ["session_third", "vol_tercile"]:
            for v in (["early", "mid", "late"] if col == "session_third"
                      else ["LOW", "MED", "HIGH"]):
                gg = g[g[col] == v]
                if len(gg):
                    cells.append(f"{gg['pnl_tbb'].mean():.1f} | {(gg['result'] == 'TP_HIT').mean() * 100:.0f}%")
                else:
                    cells.append("—")
        lines.append(f"| {c} | " + " | ".join(cells) + " |")
    lines += ["", "## Hazard surface (P(convergence | current |z|, time since signal))", "",
              "Full 2D surface in P6_EXTENSION_CONVERGENCE_SURFACE.csv (surface = "
              "z_t_hazard). Headline cells:"]
    hz = surf[surf["surface"] == "z_t_hazard"].sort_values(["bin_lo", "bin_lo2"])
    lines.append("| |z| bucket | t bucket | N obs | P(conv) | EV TB-B (cond) |")
    lines.append("|---|---|---|---|---|---|")
    for _, r in hz.iterrows():
        lines.append(f"| [{r['bin_lo']:.1f},{r['bin_hi']:.1f}) | [{r['bin_lo2']:.0f},{r['bin_hi2']:.0f}) | "
                     f"{r['n']} | {r['p_converge']:.0f}% | {r['ev_tbb']:.1f} |")
    (OUT / "P6_EXTENSION_ANATOMY_REPORT.md").write_text("\n".join(lines) + "\n",
                                                         encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P6.3 — SESSION CLOCK (entry timing)
# ═══════════════════════════════════════════════════════════════════════


def p63(df: pd.DataFrame):
    print("[P6.3] session-clock study...")
    pt = cache_load(ENTRY_Z, df)
    pt["est_h"] = [est_min_of(ts) // 60 for ts in pt["entry_time"]]
    pt["mins_since_start"] = [est_min_of(ts) - LONDON_START_H_EST * 60
                               for ts in pt["entry_time"]]
    pt["half_hour"] = (pt["mins_since_start"] // 30).astype(int)
    pt["quarter_hour"] = (pt["mins_since_start"] // 15).astype(int)
    pt["third"] = [session_third(ts) for ts in pt["entry_time"]]
    pt["near_5est"] = (pt["mins_since_start"] - 120).abs() <= 30
    pt["near_8est"] = (pt["mins_since_start"] - 300).abs() <= 30
    pt["weekday"] = pt["entry_time"].dt.day_name()
    for m in ["TB-B", "TB-C-5%"]:
        mfes, maes = [], []
        for k, (_, r) in enumerate(pt.iterrows()):
            s = sizes_of(pt, m)[k]
            mfe, mae, _, _ = model_path_stats(r, s, df)
            mfes.append(mfe)
            maes.append(mae)
        pt[f"{m}_mfe"] = mfes
        pt[f"{m}_mae"] = maes
    rows = []
    dims = [("hour_est", "est_h"), ("half_hour", "half_hour"),
            ("quarter_hour", "quarter_hour"), ("third", "third"),
            ("near_5est", "near_5est"), ("near_8est", "near_8est"),
            ("weekday", "weekday")]
    for dim, key in dims:
        for val, g in pt.groupby(key, sort=True):
            n = len(g)
            tp = g[g["result"] == "TP_HIT"]
            rows.append({"dim": dim, "bucket": str(val), "n": n,
                         "coverage_pct": n / len(pt) * 100,
                         "ev_tbb": g["TB-B_pnl_net"].mean(),
                         "ev_tbc5": g["TB-C-5%_pnl_net"].mean(),
                         "pf_tbb": metrics(g["TB-B_pnl_net"].values)["profit_factor"],
                         "pf_tbc5": metrics(g["TB-C-5%_pnl_net"].values)["profit_factor"],
                         "wr_tbb": (g["TB-B_pnl_net"] > 0).mean() * 100,
                         "mfe_med_tbb": g["TB-B_mfe"].median(),
                         "mae_med_tbb": g["TB-B_mae"].median(),
                         "conv_med_min": float(tp["exit_time"].sub(tp["entry_time"])
                                                .dt.total_seconds().median() / 60)
                         if len(tp) else float("nan"),
                         "failure_pct": (g["result"] != "TP_HIT").mean() * 100})
    tod = pd.DataFrame(rows)
    tod.to_csv(OUT / "P6_TIME_OF_DAY_STUDY.csv", index=False)
    write_session_report(tod)
    print(f"[P6.3] session-clock study written ({len(tod)} rows)")


def write_session_report(tod: pd.DataFrame):
    lines = ["# P6.3 — SESSION-CLOCK REPORT", "",
             "Entry quality vs time. Signal preserved; only conditioning is measured. "
             "Spread is NOT in the frozen OHLC feed — recorded as unavailable; the "
             "liquidity-adjacent state variable is 5-min realized basis vol (fingerprint).",
             "", "## Hour-of-day (EST)", "",
             "| hour | N | EV TB-B | EV TB-C5% | PF TB-B | WR | conv med | fail |",
             "|---|---|---|---|---|---|---|---|"]
    h = tod[tod["dim"] == "hour_est"].sort_values("bucket", key=lambda s: s.astype(int))
    for _, r in h.iterrows():
        lines.append(f"| {r['bucket']} | {r['n']} | {r['ev_tbb']:.2f} | {r['ev_tbc5']:.2f} | "
                     f"{r['pf_tbb']:.2f} | {r['wr_tbb']:.1f}% | {r['conv_med_min']:.0f} | "
                     f"{r['failure_pct']:.0f}% |")
    lines += ["", "## Session thirds + transition proximity", ""]
    for dim, label in [("third", "third"), ("near_5est", "within 30m of 5 EST (Tokyo overlap)"),
                       ("near_8est", "within 30m of 8 EST (NY open)")]:
        g = tod[tod["dim"] == dim]
        for _, r in g.iterrows():
            lines.append(f"- **{label} = {r['bucket']}:** N={r['n']}, EV TB-B {r['ev_tbb']:.2f}, "
                         f"PF {r['pf_tbb']:.2f}, conv median {r['conv_med_min']:.0f} min, "
                         f"failure {r['failure_pct']:.0f}%")
    # dead zones / dominance
    dead = tod[(tod["dim"].isin(["half_hour", "quarter_hour"])) & (tod["n"] >= 10)
               & (tod["ev_tbb"] <= 0)]
    lines.append("")
    lines.append("## Dead zones & dominance")
    dz = [f"{r['dim']}={r['bucket']}" for _, r in dead.iterrows()]
    lines.append(f"- Dead zones (bucket N>=10, EV TB-B <= 0): {dz or 'none'}.")
    best = tod[tod["dim"] == "half_hour"].sort_values("ev_tbb", ascending=False).iloc[0]
    lines.append(f"- Best half-hour: {int(best['bucket']) * 30}-{int(best['bucket']) * 30 + 30} min "
                 f"after London open (EV TB-B {best['ev_tbb']:.2f}, N={best['n']}).")
    conv = tod[(tod["dim"] == "third") & (tod["bucket"].isin(["early", "mid", "late"]))]
    conv_late = conv[conv["bucket"] == "late"]["conv_med_min"]
    conv_early = conv[conv["bucket"] == "early"]["conv_med_min"]
    lines.append(f"- Convergence speed: early median {conv_early.iloc[0]:.0f} min vs late "
                 f"{conv_late.iloc[0]:.0f} min → "
                 f"{'early dislocations converge faster' if conv_early.iloc[0] < conv_late.iloc[0] else 'late similar or faster'}.")
    lines += ["", "## Threshold x session third (TB-B / TB-C-5% EV, N)", "",
              "| z | early | mid | late |", "|---|---|---|---|"]
    for thr in GRID:
        pt = cache_load(thr, None)
        pt["third"] = [session_third(ts) for ts in pt["entry_time"]]
        cells = []
        for v in ["early", "mid", "late"]:
            g = pt[pt["third"] == v]
            if len(g):
                cells.append(f"{g['TB-B_pnl_net'].mean():.1f}/{g['TB-C-5%_pnl_net'].mean():.1f} (N={len(g)})")
            else:
                cells.append("—")
        lines.append(f"| {thr:.2f} | " + " | ".join(cells) + " |")
    (OUT / "P6_SESSION_CLOCK_REPORT.md").write_text("\n".join(lines) + "\n",
                                                     encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P6.4 — DISLOCATION-QUALITY FINGERPRINT (causal) + CONDITIONALS
# ═══════════════════════════════════════════════════════════════════════


def build_fingerprint(pt: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    barr = (np.log(df["ga"]) - np.log(df["gn"]) + np.log(df["an"])).values
    zarr = compute_basis_z(pd.Series(barr, index=df.index), LOOKBACK).values
    vol5 = basis_vol_5m(df)
    atr = {k: compute_atr(df[f"{l}_h"], df[f"{l}_l"], df[l].shift(1), ATR_PERIOD).values
           for k, l in [("GA", "ga"), ("GN", "gn"), ("AN", "an")]}
    ga = df["ga"].values
    gn = df["gn"].values
    an = df["an"].values
    vterc = causal_tercile(np.array([float(vol5[int(r["entry_idx"])]) for _, r in pt.iterrows()]))
    rows = []
    prior_exit = None
    for k, (_, r) in enumerate(pt.iterrows()):
        i = int(r["entry_idx"])
        ea = abs(float(r["entry_zscore"]))
        b = barr
        vel1 = b[i] - b[i - 1] if i >= 1 else np.nan
        vel3 = b[i] - b[i - 3] if i >= 3 else np.nan
        vel5 = b[i] - b[i - 5] if i >= 5 else np.nan
        accel = (b[i] - b[i - 1]) - (b[i - 1] - b[i - 2]) if i >= 2 else np.nan
        dur = 0
        j = i
        while j >= 0 and abs(zarr[j]) > ENTRY_Z:
            dur += 1
            j -= 1
        touches = int(np.sum(np.abs(zarr[max(0, i - 19):i + 1]) > ENTRY_Z))
        hsp = (r["entry_time"] - prior_exit).total_seconds() / 3600 if prior_exit is not None else np.nan
        prior_exit = r["exit_time"]
        rGA1 = math.log(ga[i] / ga[i - 1]) if i >= 1 else np.nan
        rGN1 = math.log(gn[i] / gn[i - 1]) if i >= 1 else np.nan
        rAN1 = math.log(an[i] / an[i - 1]) if i >= 1 else np.nan
        db1 = rGA1 - rGN1 + rAN1
        c1 = {"GA": rGA1, "GN": -rGN1, "AN": rAN1}
        s1 = sum(abs(v) for v in c1.values())
        dom1 = max(abs(v) for v in c1.values()) / s1 if s1 > 0 else np.nan
        prim1 = max(c1, key=lambda x: abs(c1[x]))
        RGA = math.log(ga[i] / ga[i - 4]) if i >= 4 else np.nan
        RGN = math.log(gn[i] / gn[i - 4]) if i >= 4 else np.nan
        RAN = math.log(an[i] / an[i - 4]) if i >= 4 else np.nan
        db5 = RGA - RGN + RAN
        c5 = {"GA": RGA, "GN": -RGN, "AN": RAN}
        s5 = sum(abs(v) for v in c5.values())
        dom5 = max(abs(v) for v in c5.values()) / s5 if s5 > 0 else np.nan
        prim5 = max(c5, key=lambda x: abs(c5[x]))
        v5 = float(vol5[i])
        rows.append({"entry_time": r["entry_time"], "entry_abs_z": ea,
                     "vel1_basis": vel1, "vel3_basis": vel3, "vel5_basis": vel5,
                     "accel_basis": accel, "z_vel1": zarr[i] - zarr[i - 1] if i >= 1 else np.nan,
                     "dur_above_thr": dur, "touches_20bar": touches,
                     "hours_since_prior_exit": hsp, "basis_vol5m": v5,
                     "atr_ga": float(atr["GA"][i]), "atr_gn": float(atr["GN"][i]),
                     "atr_an": float(atr["AN"][i]),
                     "rel_vol_gn_ga": float(atr["GN"][i] / atr["GA"][i]),
                     "rel_vol_an_ga": float(atr["AN"][i] / atr["GA"][i]),
                     "vol_tercile": vterc[k] if vterc[k] == vterc[k] else "NA",
                     "dom_1bar": dom1, "primary_1bar": prim1,
                     "contrib_pct_1bar": (c1[prim1] / db1 * 100) if abs(db1) > 1e-12 else np.nan,
                     "dom_5bar": dom5, "primary_5bar": prim5,
                     "contrib_pct_5bar": (c5[prim5] / db5 * 100) if abs(db5) > 1e-12 else np.nan,
                     "session_third": session_third(r["entry_time"]),
                     "weekday": r["entry_time"].day_name(),
                     "month": f"{r['entry_time'].year}-{r['entry_time'].month:02d}"})
    return pd.DataFrame(rows)


def quality_conditionals(pt: pd.DataFrame, fp: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    for m in ["TB-B", "TB-C-5%"]:
        mfes, maes = [], []
        for k, (_, r) in enumerate(pt.iterrows()):
            s = sizes_of(pt, m)[k]
            mfe, mae, _, _ = model_path_stats(r, s, df)
            mfes.append(mfe)
            maes.append(mae)
        fp[f"{m}_mfe"] = mfes
        fp[f"{m}_mae"] = maes
    fp["pnl_tbb"] = pt["TB-B_pnl_net"].values
    fp["pnl_tbc5"] = pt["TB-C-5%_pnl_net"].values
    fp["result"] = pt["result"].values
    fp["duration_min"] = ((pt["exit_time"] - pt["entry_time"]).dt.total_seconds() / 60).values
    vel5 = fp["vel5_basis"].values
    vterc = causal_tercile(vel5)
    fp["vel5_terc"] = [v if v == v else "NA" for v in vterc]
    fp["dur_bin"] = np.where(fp["dur_above_thr"] >= 5, "ge5",
                              np.where(fp["dur_above_thr"] >= 3, "3_4",
                                       np.where(fp["dur_above_thr"] == 2, "2", "1")))
    fp["dom_bin"] = np.where(fp["dom_5bar"] >= 0.6, "dominant",
                              np.where(fp["dom_5bar"] >= 0.4, "mixed", "multi"))
    rows = []
    dims = [("vel5_terc", "vel5_terc"), ("dur_above_thr", "dur_bin"),
            ("vol_tercile", "vol_tercile"), ("leg_dominance", "dom_bin"),
            ("session_third", "session_third"), ("weekday", "weekday")]
    for dim, key in dims:
        for val, g in fp.groupby(key, sort=False):
            if str(val) == "NA" or (isinstance(val, float) and math.isnan(val)):
                continue
            n = len(g)
            tp = g[g["result"] == "TP_HIT"]
            rows.append({"dim": dim, "bucket": str(val), "n": n,
                         "coverage_pct": n / len(fp) * 100,
                         "ev_tbb": g["pnl_tbb"].mean(), "ev_tbc5": g["pnl_tbc5"].mean(),
                         "pf_tbb": metrics(g["pnl_tbb"].values)["profit_factor"],
                         "pf_tbc5": metrics(g["pnl_tbc5"].values)["profit_factor"],
                         "wr_tbb": (g["pnl_tbb"] > 0).mean() * 100,
                         "mfe_med_tbb": g["TB-B_mfe"].median(),
                         "mae_med_tbb": g["TB-B_mae"].median(),
                         "conv_med_min": float(tp["duration_min"].median())
                         if len(tp) else float("nan"),
                         "failure_pct": (g["result"] != "TP_HIT").mean() * 100})
    return pd.DataFrame(rows)


def p64(df: pd.DataFrame):
    print("[P6.4] fingerprint + quality + cost stress + lot translation...")
    pt = cache_load(ENTRY_Z, df)
    fp = build_fingerprint(pt, df)
    fp.to_csv(OUT / "P6_DISLOCATION_FINGERPRINT.csv", index=False)
    qc = quality_conditionals(pt, fp, df)
    qc.to_csv(OUT / "P6_QUALITY_CONDITIONALS.csv", index=False)
    write_cost_stress()
    write_exec_translation(df)
    print(f"[P6.4] fingerprint ({len(fp)} rows) + conditionals ({len(qc)} rows) + "
          f"cost stress + lot translation written")


# ── cost stress (all thresholds x models, 1.0-3.0x, break-even) ─────────

def break_even_mult(gross: np.ndarray) -> float:
    evs = [float(np.mean(gross - COSTS_PIPS * mm)) for mm in COST_MULTS]
    for idx, y in enumerate(evs):
        if y <= 0:
            if idx == 0:
                return 1.0
            return COST_MULTS[idx - 1] + (0 - evs[idx - 1]) * \
                (COST_MULTS[idx] - COST_MULTS[idx - 1]) / (y - evs[idx - 1])
    return float("nan")


def write_cost_stress():
    rows = []
    for thr in GRID:
        pt = cache_load(thr, None)
        for m in MODELS:
            gross = pt[f"{m}_pnl_gross"].values
            row = {"threshold": thr, "model": m, "break_even_mult": break_even_mult(gross)}
            for mult in COST_MULTS:
                net = gross - COSTS_PIPS * mult
                mm = metrics(net)
                row[f"ev_{mult:g}x"] = mm["expectancy_pips"]
                row[f"pf_{mult:g}x"] = mm["profit_factor"]
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "P6_COST_STRESS.csv", index=False)


# ── execution / broker lot translation (TB-B + TB-C-5%, all thresholds) ─

LEG_ORDER = [("GA", "GBPAUD", "gbpaud", 0), ("GN", "GBPNZD", "gbpnzd", 1),
             ("AN", "AUDNZD", "audnzd", 2)]


def lot_metrics(pt: pd.DataFrame, m: str, notional: float, df: pd.DataFrame) -> dict:
    exec_res, rejects, distortion, pnl_ratios = [], 0, [], []
    for k, (_, r) in enumerate(pt.iterrows()):
        pe = df.iloc[r["entry_idx"]]
        px = df.iloc[r["exit_idx"]]
        prices = {"ga": pe["ga"], "gn": pe["gn"], "an": pe["an"]}
        leg_p = trade_leg_pips({"gbpaud": pe["ga"], "gbpnzd": pe["gn"], "audnzd": pe["an"]},
                               {"gbpaud": px["ga"], "gbpnzd": px["gn"], "audnzd": px["an"]},
                               r["direction"])
        s = sizes_of(pt, m)[k]
        q = s / 3.0
        raw, rounded = {}, {}
        for leg, pair, _, j in LEG_ORDER:
            ntl = notional * q[j]
            rate_q = CUR_TO_USD[{"GBPAUD": "AUD", "GBPNZD": "NZD", "AUDNZD": "NZD"}[pair]]
            val_per_lot = CONTRACT[pair] * prices[leg.lower()] * rate_q
            raw[leg] = ntl / val_per_lot if val_per_lot > 0 else 0.0
            rounded[leg] = (max(VOL_MIN, round(raw[leg] / VOL_STEP) * VOL_STEP)
                            if raw[leg] > 0 else 0.0)
        if any(raw[leg] < VOL_MIN for leg in raw):
            rejects += 1
        ccy = {"GBP": 0.0, "AUD": 0.0, "NZD": 0.0}
        gross_usd = 0.0
        for leg, pair, _, _ in LEG_ORDER:
            bu = rounded[leg] * CONTRACT[pair]
            qu = bu * prices[leg.lower()]
            base, quote = {"GBPAUD": ("GBP", "AUD"), "GBPNZD": ("GBP", "NZD"),
                           "AUDNZD": ("AUD", "NZD")}[pair]
            side = 1 if r["direction"] == "LONG" else -1
            if pair == "GBPNZD":
                side = -side
            ccy[base] += side * bu
            ccy[quote] -= side * qu
            gross_usd += qu * CUR_TO_USD[quote]
        exec_res.append(max(abs(ccy[c]) * CUR_TO_USD[c] for c in ccy) / gross_usd * 100
                        if gross_usd > 0 else float("nan"))
        tot_r = sum(rounded.values()) or 1.0
        tot_t = sum(raw.values()) or 1.0
        dist = [abs(rounded[leg] / tot_r - raw[leg] / tot_t) / (raw[leg] / tot_t) * 100
                for leg in raw if raw[leg] / tot_t > 0]
        distortion.append(max(dist) if dist else 0.0)
        if all(raw[leg] > 0 for leg in raw):
            ratio = [rounded[leg] / raw[leg] for leg in raw]
            pnl_exec = sum(ratio[j] * s[j] * leg_p[pair.lower()]
                           for _, pair, _, j in LEG_ORDER)
            pnl_model = basket_pnl({"gbpaud": s[0], "gbpnzd": s[1], "audnzd": s[2]}, leg_p)
            pnl_ratios.append(pnl_exec / pnl_model if abs(pnl_model) > 1e-9 else 1.0)
    return {"median_executable_residual_pct": float(np.median(exec_res)),
            "rejection_rate_pct": rejects / len(pt) * 100,
            "median_weight_distortion_pct": float(np.median(distortion)),
            "median_pnl_ratio_exec_vs_model": float(np.median(pnl_ratios))
            if pnl_ratios else float("nan")}


def write_exec_translation(df: pd.DataFrame):
    rows = []
    for m in ["TB-B", "TB-C-5%"]:
        for thr in GRID:
            pt = cache_load(thr, None)
            for ntl in NOTIONALS:
                lm = lot_metrics(pt, m, ntl, df)
                rows.append({"model": m, "threshold": thr, "notional_usd": ntl, **lm})
    pd.DataFrame(rows).to_csv(OUT / "P6_EXECUTION_TRANSLATION.csv", index=False)


# ═══════════════════════════════════════════════════════════════════════
# SEAL — CANDIDATE CLASSIFICATION + DECISION + FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════


def basis_share_for(pt: pd.DataFrame, m: str, df: pd.DataFrame) -> float:
    pb = pg = pa = 0.0
    for _, r in pt.iterrows():
        pe = df.iloc[r["entry_idx"]]
        px = df.iloc[r["exit_idx"]]
        s = sizes_of(pt, m)[int(r.name)]
        d = 1.0 if r["direction"] == "LONG" else -1.0
        lg = {"gbpaud": math.log(px["ga"] / pe["ga"]),
              "gbpnzd": math.log(px["gn"] / pe["gn"]),
              "audnzd": math.log(px["an"] / pe["an"])}
        db = r["exit_basis"] - r["entry_basis"]
        w = {"gbpaud": s[0] * pe["ga"] / PIP, "gbpnzd": s[1] * pe["gn"] / PIP,
             "audnzd": s[2] * pe["an"] / PIP}
        pb += d * w["gbpnzd"] * db
        pg += d * (w["gbpaud"] - w["gbpnzd"]) * lg["gbpaud"]
        pa += d * (w["audnzd"] - w["gbpnzd"]) * lg["audnzd"]
    tot = pb + pg + pa
    return float(pb / tot * 100) if abs(tot) > 1e-12 else float("nan")


def perm_pval(x: np.ndarray, y: np.ndarray, nperm: int = 2000, seed: int = SEED) -> float:
    rng = np.random.default_rng(seed)
    nx = len(x)
    allv = np.concatenate([x, y])
    obs = float(x.mean() - y.mean())
    M = rng.permuted(np.tile(allv, (nperm, 1)), axis=1)
    d = M[:, :nx].mean(axis=1) - M[:, nx:].mean(axis=1)
    return float((np.abs(d) >= abs(obs)).mean())


def boot_diff_ci(x: np.ndarray, y: np.ndarray, nboot: int = 2000, seed: int = SEED):
    rng = np.random.default_rng(seed)
    nx, ny = len(x), len(y)
    diffs = np.empty(nboot)
    for b in range(nboot):
        diffs[b] = x[rng.integers(0, nx, nx)].mean() - y[rng.integers(0, ny, ny)].mean()
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def bh_fdr(pvals: list) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    qv = p[order] * n / np.arange(1, n + 1)
    for i in range(n - 2, -1, -1):
        qv[i] = min(qv[i], qv[i + 1])
    q[order] = qv
    return q


def _block_ev(pt: pd.DataFrame, m: str, lo: float, hi: float) -> float:
    sub = pt[(pt["entry_time"] >= lo) & (pt["entry_time"] < hi)]
    return float(sub[f"{m}_pnl_net"].mean()) if len(sub) else float("nan")


def build_candidates(df: pd.DataFrame) -> list:
    surf = pd.read_csv(OUT / "P6_ENTRY_THRESHOLD_SURFACE.csv")
    cost = pd.read_csv(OUT / "P6_COST_STRESS.csv")
    cands = []
    for m in NEUTRAL:
        evs = surf[surf["model"] == m].sort_values("threshold")["expectancy_pips"].tolist()
        plats = find_plateaus(evs)
        in_plat = {}
        for idx, thr in enumerate(GRID):
            in_plat[thr] = any(i0 <= idx <= i1 for (i0, i1, _, _) in plats)
        pt_base = cache_load(ENTRY_Z, None)
        net_b = pt_base[f"{m}_pnl_net"].values
        n_b = len(pt_base)
        t0_b, t1_b = pt_base["entry_time"].min(), pt_base["entry_time"].max()
        q_b = np.quantile(np.arange(n_b), [0.6, 0.8])
        b_edges = [t0_b, pt_base["entry_time"].sort_values().iloc[min(int(q_b[0]), n_b - 1)],
                   pt_base["entry_time"].sort_values().iloc[min(int(q_b[1]), n_b - 1)], t1_b]
        p_info = []
        for thr in GRID:
            if thr == ENTRY_Z:
                continue
            pt_t = cache_load(thr, None)
            net_t = pt_t[f"{m}_pnl_net"].values
            p_info.append((thr, pt_t, net_t, perm_pval(net_t, net_b)))
        qvals = bh_fdr([p for (_, _, _, p) in p_info])
        for qi, (thr, pt_t, net_t, pv) in enumerate(p_info):
            n_t = len(pt_t)
            ev_t, ev_b = float(net_t.mean()), float(net_b.mean())
            ci_lo, ci_hi = boot_diff_ci(net_t, net_b)
            qv = float(qvals[qi])
            # blocks on candidate's own set
            t0_t, t1_t = pt_t["entry_time"].min(), pt_t["entry_time"].max()
            qt = np.quantile(np.arange(n_t), [0.6, 0.8])
            t_edges = [t0_t, pt_t["entry_time"].sort_values().iloc[min(int(qt[0]), n_t - 1)],
                       pt_t["entry_time"].sort_values().iloc[min(int(qt[1]), n_t - 1)], t1_t]
            d_ev = _block_ev(pt_t, m, t_edges[0], t_edges[1]) - _block_ev(pt_base, m, b_edges[0], b_edges[1])
            c_ev = _block_ev(pt_t, m, t_edges[1], t_edges[2]) - _block_ev(pt_base, m, b_edges[1], b_edges[2])
            h_ev = _block_ev(pt_t, m, t_edges[2], t_edges[3]) - _block_ev(pt_base, m, b_edges[2], b_edges[3])
            def _same_dir(a, b_, c_):
                vals = [v for v in (a, b_, c_) if v == v]
                return len(vals) >= 2 and all((v > 0) == (vals[0] > 0) for v in vals) and vals[0] != 0
            dir_dch = _same_dir(d_ev, c_ev, h_ev) and n_t >= 60
            # P5 date holdout
            ht = pt_t[pt_t["exit_time"] >= P5_HOLDOUT]
            hb = pt_base[pt_base["exit_time"] >= P5_HOLDOUT]
            if len(ht) >= 20 and len(hb) >= 20:
                hold_ok = (ht[f"{m}_pnl_net"].mean() - hb[f"{m}_pnl_net"].mean()) > 0
            else:
                hold_ok = None
            # top-5% independence
            def _mean_no_top(net):
                keep = np.argsort(-np.abs(net))[int(len(net) * 0.05):]
                return float(net[keep].mean())
            top5 = _mean_no_top(net_t) - _mean_no_top(net_b) > 0
            coverage = n_t / n_b * 100
            be = float(cost[(cost["threshold"] == thr) & (cost["model"] == m)]["break_even_mult"].iloc[0])
            bshare = basis_share_for(pt_t, m, df)
            gates = {
                "uplift": (ci_lo > 0) and (qv < 0.10),
                "dir_dch": bool(dir_dch),
                "holdout": (hold_ok is None) or bool(hold_ok),
                "plateau": bool(in_plat[thr]),
                "coverage": coverage >= 40,
                "cost": be >= 1.5,
                "basis": bshare >= 60,
                "top5": bool(top5),
            }
            n_ok = sum(v for v in [gates["plateau"], gates["coverage"], gates["cost"],
                                   gates["basis"], gates["top5"]] if isinstance(v, bool))
            if all(gates.values()):
                grade = "A"
            elif gates["uplift"] and gates["dir_dch"] and gates["holdout"] and n_ok >= 2:
                grade = "B"
            elif gates["uplift"]:
                grade = "C"
            else:
                grade = "D"
            cands.append({"model": m, "threshold": thr, "grade": grade,
                          "n_trades": n_t, "coverage_pct": coverage,
                          "ev_t": ev_t, "ev_baseline": ev_b, "ev_uplift": ev_t - ev_b,
                          "ev_uplift_ci": [ci_lo, ci_hi], "perm_p": float(pv),
                          "fdr_q": qv, "block_ev_d_c_h": [d_ev, c_ev, h_ev],
                          "holdout_dir_ok": hold_ok, "plateau_member": bool(in_plat[thr]),
                          "break_even_mult": be, "basis_share_pct": bshare, "top5_ok": bool(top5),
                          "gates": gates})
    return cands


def build_decision(cands: list) -> dict:
    cleared = any(c["grade"] in ("A", "B") for c in cands)
    return {"p7_convergence_optimization_cleared": bool(cleared),
           "split": {"discovery": "earliest 60% by entry time",
                      "confirmation": "60-80%", "holdout": "latest 20%",
                      "p5_date_holdout": "exit >= 2025-07-01 (where N>=20)"},
           "candidate_rule": "(neutral model, entry z) vs same model at z=2.5",
           "grades": {c["model"] + "@" + f"{c['threshold']:.2f}": c["grade"] for c in cands},
           "n_candidates_A": sum(c["grade"] == "A" for c in cands),
           "n_candidates_B": sum(c["grade"] == "B" for c in cands),
           "n_candidates_C": sum(c["grade"] == "C" for c in cands),
           "n_candidates_D": sum(c["grade"] == "D" for c in cands),
           "generated": pd.Timestamp.utcnow().isoformat() + "Z"}


def write_final_report(cands: list, decision: dict):
    surf = pd.read_csv(OUT / "P6_ENTRY_THRESHOLD_SURFACE.csv")
    plat = (OUT / "P6_ENTRY_THRESHOLD_PLATEAUS.md").read_text(encoding="utf-8")
    cost = pd.read_csv(OUT / "P6_COST_STRESS.csv")
    exe = pd.read_csv(OUT / "P6_EXECUTION_TRANSLATION.csv")
    qc = pd.read_csv(OUT / "P6_QUALITY_CONDITIONALS.csv")
    lines = [
        "# TB-P6 — ENTRY ANATOMY REPORT", "",
        "**Phase:** TB-P6-ENTRY-ANATOMY-01 (ENTRY RESEARCH ONLY).",
        "**Base:** commit `7868a67d624931d3afc56910de8b805510eabcc7` (TB-P5 accepted).",
        "**Protocol:** `TB_P6_PROTOCOL.md` (pre-registered split/metrics/gates).",
        "**Reproduce:** `python quant-lab/engines/tb_p6_anatomy.py --phase all` + "
        "`python quant-lab/engines/tb_p6_tests.py` (deterministic, seed 42).",
        "**Decision:** `TB_P6_DECISION.json` · Candidates: `P6_CANDIDATE_ENTRY_RULES.json`.", "",
        "## 1. Entry-threshold surface (P6.1)", "",
        "Full grid: `P6_ENTRY_THRESHOLD_SURFACE.csv` (11 z values x 6 models, full metric set). ",
        "Plateau analysis: `P6_ENTRY_THRESHOLD_PLATEAUS.md`.", "",
        "| z | N | EV TB-B | EV TB-C5% | PF TB-B | WR | maxDD | MFE | MAE |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in surf[surf["model"] == "TB-B"].sort_values("threshold").iterrows():
        c5 = surf[(surf["model"] == "TB-C-5%") & (surf["threshold"] == r["threshold"])].iloc[0]
        lines.append(f"| {r['threshold']:.2f} | {r['n_trades']} | {r['expectancy_pips']:.2f} | "
                     f"{c5['expectancy_pips']:.2f} | {r['profit_factor']:.2f} | "
                     f"{r['win_rate_pct']:.1f}% | {r['max_dd_pips']:.0f} | "
                     f"{r['mfe_median_pips']:.1f} | {r['mae_median_pips']:.1f} |")
    lines += ["", "## 2. Further-extension anatomy (P6.2)", "",
              "Per-trade paths: `P6_FURTHER_EXTENSION_PATHS.csv`; convergence surface: ",
              "`P6_EXTENSION_CONVERGENCE_SURFACE.csv`; full write-up: ",
              "`P6_EXTENSION_ANATOMY_REPORT.md` (hypotheses A-D tested quantitatively).", "",
              "## 3. Session clock (P6.3)", "",
              "`P6_TIME_OF_DAY_STUDY.csv` + `P6_SESSION_CLOCK_REPORT.md`. Headlines:"]
    tod = pd.read_csv(OUT / "P6_TIME_OF_DAY_STUDY.csv")
    best = tod[tod["dim"] == "half_hour"].sort_values("ev_tbb", ascending=False).iloc[0]
    dead = tod[(tod["dim"].isin(["half_hour", "quarter_hour"])) & (tod["n"] >= 10)
               & (tod["ev_tbb"] <= 0)]
    lines.append(f"- Best half-hour: {int(best['bucket']) * 30}-{int(best['bucket']) * 30 + 30} min after "
                 f"London open (EV TB-B {best['ev_tbb']:.2f}, N={best['n']}).")
    dz = [f"{r['dim']}={r['bucket']}" for _, r in dead.iterrows()]
    lines.append(f"- Dead zones: {dz or 'none'}.")
    lines += ["", "## 4. Dislocation-quality fingerprint (P6.4)", "",
              "Per-trade causal features: `P6_DISLOCATION_FINGERPRINT.csv`; conditionals: ",
              "`P6_QUALITY_CONDITIONALS.csv`. No future information enters any feature ",
              "(tested in tb_p6_tests.py).", "", "## 5. Cost stress + execution translation (P6.4)", "",
              "Cost stress (1.0-3.0x, break-even): `P6_COST_STRESS.csv`. Lot translation ",
              "(TB-B / TB-C-5%, $5k-$100k): `P6_EXECUTION_TRANSLATION.csv`.", "",
              "| model | z=2.5 break-even | z=3.00 break-even | z=3.50 break-even |",
              "|---|---|---|---|"]
    for m in ["TB-B", "TB-C-5%"]:
        row = cost[cost["model"] == m]
        be25 = row[row["threshold"] == 2.5]["break_even_mult"].iloc[0]
        be30 = row[row["threshold"] == 3.0]["break_even_mult"].iloc[0]
        be35 = row[row["threshold"] == 3.5]["break_even_mult"].iloc[0]
        lines.append(f"| {m} | {be25:.2f}x | {be30:.2f}x | {be35:.2f}x |")
    lines += ["", "## 6. Candidate entry rules (classification)", "",
              "Full detail: `P6_CANDIDATE_ENTRY_RULES.json` (gates, CIs, FDR q, block EVs, ",
              "holdout, plateau, cost, basis, top-5% independence).", "",
              "| candidate | grade | N | coverage | EV uplift | CI | q | D/C/H | holdout | plateau | BE | basis |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(cands, key=lambda c: (c["model"], c["threshold"])):
        dch = "/".join(f"{v:+.1f}" if v == v else "na" for v in c["block_ev_d_c_h"])
        lines.append(f"| {c['model']} @ {c['threshold']:.2f} | **{c['grade']}** | {c['n_trades']} | "
                     f"{c['coverage_pct']:.0f}% | {c['ev_uplift']:+.2f} | "
                     f"[{c['ev_uplift_ci'][0]:+.2f},{c['ev_uplift_ci'][1]:+.2f}] | "
                     f"{c['fdr_q']:.3f} | {dch} | {c['holdout_dir_ok']} | "
                     f"{c['plateau_member']} | {c['break_even_mult']:.2f}x | {c['basis_share_pct']:.0f}% |")
    lines += ["", "## 7. Decision", "",
              f"**p7_convergence_optimization_cleared = {decision['p7_convergence_optimization_cleared']}**",
              "",
              "A/B candidates must improve expectancy or downside profile, survive ",
              "confirmation and the frozen holdout, retain meaningful coverage, lie on a stable ",
              "plateau, preserve basis-reversion attribution, and remain executable.", "",
              "## 8. STOP FOR HUMAN REVIEW", "",
              "P6 is ENTRY RESEARCH ONLY. No exit/hold/stop/pyramiding/scaling/risk/deployment ",
              "work begins. Review `TB_P6_DECISION.json` + this report before any P7 work."]
    (OUT / "TB_P6_ENTRY_ANATOMY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def seal(df: pd.DataFrame):
    print("[P6-seal] candidates + decision + report...")
    cands = build_candidates(df)
    with open(OUT / "P6_CANDIDATE_ENTRY_RULES.json", "w") as f:
        json.dump(cands, f, indent=1, default=str)
    decision = build_decision(cands)
    with open(OUT / "TB_P6_DECISION.json", "w") as f:
        json.dump(decision, f, indent=1, default=str)
    write_final_report(cands, decision)
    print(f"[P6-seal] candidates={len(cands)}, A={decision['n_candidates_A']}, "
          f"B={decision['n_candidates_B']}, C={decision['n_candidates_C']}, "
          f"D={decision['n_candidates_D']}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="TB-P6 entry anatomy")
    ap.add_argument("--phase", default="all",
                    choices=["all", "p61", "p62", "p63", "p64", "seal"])
    args = ap.parse_args()
    df = load_and_verify()
    if args.phase in ("all", "p61"):
        p61(df)
    if args.phase in ("all", "p62"):
        p62(df)
    if args.phase in ("all", "p63"):
        p63(df)
    if args.phase in ("all", "p64"):
        p64(df)
    if args.phase in ("all", "seal"):
        seal(df)
    print("[P6] done. outputs in", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
