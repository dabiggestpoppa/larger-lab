#!/usr/bin/env python
"""ALT_MECH_18 - EDGE-LAW & RESPONSE-LAW CARTOGRAPHY base module.

Reuses MECH-17 base (data load, forcing families, traffic objects, caches)
and adds MECH-18 primitives: daily exit-distribution series (forward window),
Jensen-Shannon divergence, memory kernels, and edge-transition helpers.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import os, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

ROOT = Path(__file__).resolve().parents[1]           # mech_18/
sys.path.insert(0, str(ROOT.parent / "mech_17" / "scripts"))
import _m17base as M17
from _m17base import (load_frame, load_band, forcing_families,
                      activation_surface, DEPTH_ORDER, SUBPERIODS,
                      FINE2PATCH, STATE_CODE, W2022_LO, W2022_HI)

OUT = ROOT

# --------------------------------------------------------------------- caches
def load_caches():
    """MECH-17 aligned caches (2196 rows each)."""
    with open(ROOT.parent / "mech_17" / "cache_act17.pkl", "rb") as fh:
        act = pickle.load(fh)
    with open(ROOT.parent / "mech_17" / "cache_fams17.pkl", "rb") as fh:
        fams = pickle.load(fh)
    with open(ROOT.parent / "mech_17" / "cache_demand17.pkl", "rb") as fh:
        demand = pickle.load(fh)
    with open(ROOT.parent / "mech_17" / "cache_bm6_17.pkl", "rb") as fh:
        bm6 = pickle.load(fh)
    with open(ROOT.parent / "mech_17" / "cache_bm8_17.pkl", "rb") as fh:
        bm8 = pickle.load(fh)
    return act, fams, demand, bm6, bm8


# ------------------------------------------------------------------ utilities
def _z(s):
    s = np.asarray(s, dtype=float)
    sd = np.nanstd(s)
    return (s - np.nanmean(s)) / sd if sd > 0 else s * 0.0


def _rho(a, b, min_n=30):
    from scipy.stats import spearmanr
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    m = ~(np.isnan(a) | np.isnan(b))
    if m.sum() < min_n:
        return np.nan
    return float(spearmanr(a[m], b[m])[0])


def _partial_rho(x, y, c, min_n=40):
    """Partial Spearman: residualize x,y on c (linear), then rank-corr."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    c = np.asarray(c, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y) | np.isnan(c))
    if m.sum() < min_n:
        return np.nan, int(m.sum())
    C = np.column_stack([np.ones(m.sum()), c[m]])
    try:
        bx = np.linalg.lstsq(C, x[m], rcond=None)[0]
        by = np.linalg.lstsq(C, y[m], rcond=None)[0]
        rx = x[m] - C @ bx; ry = y[m] - C @ by
        return _rho(rx, ry, min_n=20), int(m.sum())
    except Exception:
        return np.nan, int(m.sum())


def js_divergence(p, q):
    """Jensen-Shannon divergence (natural log) between two probability vectors."""
    p = np.asarray(p, dtype=float); q = np.asarray(q, dtype=float)
    if len(p) == 0 or len(q) == 0:
        return np.nan
    if p.sum() <= 0 or q.sum() <= 0:
        return np.nan
    p = p / p.sum(); q = q / q.sum()
    m = 0.5 * (p + q)
    def kl(a, b):
        a = np.clip(a, 1e-12, None); b = np.clip(b, 1e-12, None)
        return float(np.sum(a * (np.log(a) - np.log(b))))
    j = 0.5 * kl(p, m) + 0.5 * kl(q, m)
    return float(np.clip(j, 0.0, None))


# -------------------------------------------------- daily exit distributions
def exit_dist_series(seq, horizon=7):
    """For each day t, distribution of states observed in (t, t+horizon]
    (normalized over observed exits, including current state as STAY option).
    Returns dict: 'dist' -> dict[t] = {state: prob}, 'labels' -> list states,
    'matrix' -> DataFrame aligned to seq.index."""
    s = np.asarray(seq, dtype=object)
    n = len(s)
    labels = []
    for i in range(n):
        w = s[i + 1: min(i + 1 + horizon, n)]
        for v in w:
            if v not in labels:
                labels.append(v)
    labels = sorted(labels, key=str)
    mat = np.full((n, len(labels)), np.nan)
    for i in range(n):
        w = s[i + 1: min(i + 1 + horizon, n)]
        if len(w) < 3:
            continue
        vc = pd.Series(w).value_counts()
        tot = vc.sum()
        for lab in labels:
            mat[i, labels.index(lab)] = vc.get(lab, 0) / tot
    return mat, labels


# ---------------------------------------------------------------- memory
def memory_kernels(f, horizons=(5, 10, 20, 40)):
    """Build weighted-memory forcing series: m(t) = sum_s w(s) f(t-s).
    Returns dict of name -> aligned Series (same index as f)."""
    f = pd.Series(f).astype(float)
    out = {}
    n = len(f)
    t = np.arange(n)
    for h in horizons:                       # exponential decay, half-life h
        w = 0.5 ** (t / h)
        conv = np.convolve(f.fillna(0).to_numpy(), w[::-1], mode="full")[:n]
        norm = np.convolve(np.ones(n), w[::-1], mode="full")[:n]
        out[f"EXP_HL{h}"] = pd.Series(conv / norm, index=f.index)
    for a in (0.3, 0.5, 0.7):                # power-law decay
        w = (t + 1.0) ** (-a)
        conv = np.convolve(f.fillna(0).to_numpy(), w[::-1], mode="full")[:n]
        norm = np.convolve(np.ones(n), w[::-1], mode="full")[:n]
        out[f"POW_{a}"] = pd.Series(conv / norm, index=f.index)
    for wd in (7, 14, 30):                   # flat window
        out[f"FLAT_{wd}"] = f.rolling(wd, min_periods=3).mean()
    return out


# ---------------------------------------------------------------- edges
def edge_table(df, col, ncol, demand=None, forcing_series=None,
               patch_act_field=None, entropy_series=None):
    """1-day edge registry from col -> ncol. Returns DataFrame of per-edge
    statistics with conditional probabilities."""
    rows = []
    states = sorted(df[col].dropna().unique().tolist(), key=str)
    nxt = sorted(df[ncol].dropna().unique().tolist(), key=str)
    demand = pd.Series(demand).to_numpy() if demand is not None else None
    fc = pd.Series(forcing_series).to_numpy() if forcing_series is not None else None
    ent = pd.Series(entropy_series).to_numpy() if entropy_series is not None else None
    # time-in-state (duration of current run)
    g = df[col].to_numpy(); run = np.zeros(len(df), dtype=int)
    for i in range(1, len(df)):
        run[i] = run[i - 1] + 1 if g[i] == g[i - 1] else 0
    # entry day of current run
    entry = np.full(len(df), -1)
    for i in range(len(df)):
        entry[i] = i if i == 0 or g[i] != g[i - 1] else entry[i - 1]
    dq = pd.to_numeric(df["d"], errors="coerce").to_numpy()
    for s in states:
        for t in nxt:
            sel = (g == s) & (df[ncol].to_numpy() == t) & df[ncol].notna().to_numpy()
            sel = sel & pd.notna(df[ncol]).to_numpy()
            n = int(sel.sum())
            if n == 0:
                continue
            prob = n / int((g == s).sum())
            # subperiod coverage
            subp = df.loc[sel, "subperiod"].value_counts()
            cover = float(subp.index.isin(SUBPERIODS).sum()) / len(SUBPERIODS)
            # median time-to-transition from entry of the run
            durs = []
            for i in np.where(sel)[0]:
                durs.append(int(i - entry[i]))
            durs = [d for d in durs if d >= 0]
            mt = float(np.median(durs)) if durs else np.nan
            cond = dict(n=n, prob=round(prob, 4), subperiod_coverage=round(cover, 2),
                        median_days_to_exit=round(mt, 1) if mt == mt else np.nan)
            if demand is not None:
                dm = demand[sel]
                q = np.nanquantile(demand, [0.33, 0.67])
                cond["prob_demand_lo"] = round(float(prob), 4)
                cond["prob_demand_hi"] = round(float(prob), 4)
                lo = sel & (demand <= q[0]); hi = sel & (demand >= q[1])
                nlo = int((g == s)[lo].sum()); nhi = int((g == s)[hi].sum())
                if nlo >= 10: cond["prob_demand_lo"] = round(float(lo[sel].sum() / nlo if nlo else np.nan), 4)
              
                if nhi >= 10: cond["prob_demand_hi"] = round(float(hi[sel].sum() / nhi if nhi else np.nan), 4)
            if fc is not None:
                rise = np.zeros(len(df), dtype=bool)
                rise[1:] = fc[1:] >= fc[:-1]
                nr = int((g == s)[rise].sum()); nf = int((g == s)[~rise].sum())
                cond["prob_rising"] = round(float(rise[sel].sum() / nr if nr else np.nan), 4)
                cond["prob_falling"] = round(float((~rise)[sel].sum() / nf if nf else np.nan), 4)
            if ent is not None:
                qe = np.nanquantile(ent, [0.33, 0.67])
                elo = sel & (ent <= qe[0]); ehi = sel & (ent >= qe[1])
                nelo = int((g == s)[elo].sum()); nehi = int((g == s)[ehi].sum())
                cond["prob_ent_lo"] = round(float(elo[sel].sum() / nelo if nelo else np.nan), 4)
                cond["prob_ent_hi"] = round(float(ehi[sel].sum() / nehi if nehi else np.nan), 4)
            cond["from_state"] = s; cond["to_state"] = t
            rows.append(cond)
    out = pd.DataFrame(rows)
    if len(out):
        cls_map = {}
        for s in states:
            g2 = out[out["from_state"] == s].sort_values("prob", ascending=False)
            if len(g2) == 0:
                continue
            p1 = g2.iloc[0]["prob"]
            for _, r in g2.iterrows():
                if r["to_state"] == r["from_state"]:
                    cls_map[(s, r["to_state"])] = "STAY"
                elif r["prob"] >= 0.6 * p1:
                    cls_map[(s, r["to_state"])] = "PRIMARY"
                elif r["prob"] >= 0.25 * p1:
                    cls_map[(s, r["to_state"])] = "SECONDARY"
                elif r["prob"] >= 0.02:
                    cls_map[(s, r["to_state"])] = "MINOR"
                else:
                    cls_map[(s, r["to_state"])] = "NEAR_ZERO"
        out["edge_class"] = [cls_map.get((r["from_state"], r["to_state"]), "NEAR_ZERO") for _, r in out.iterrows()]
    return out


def _fmean(arr, mask):
    a = np.asarray(arr, dtype=float)[np.asarray(mask, dtype=bool)]
    a = a[~np.isnan(a)]
    return float(a.mean()) if len(a) else np.nan
