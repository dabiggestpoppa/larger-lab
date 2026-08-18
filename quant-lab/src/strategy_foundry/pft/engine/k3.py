"""K3 — Vietoris-Rips topology + EUR/CAD distance divergence kernel.

A1.F09.VR_DISTANCE      6-step path distance on 720-slot z-scores
A1.F10.VR_CLASSIFICATION epsilon filtration, beta1 checks, classes
A1.F11.K3_OLS           literal causal OLS with fail-closed singular rule
A1.F12.K3_ALPHA         alpha2/base2/w2 sizing with topology multiplier

Classification schedule: noon snapshot (H1 candle ending 12:00 NY, slot
with ny_hour 11) is frozen until the 13:00 bar (ny_hour 13); the
11:00-13:00 gap retains the prior class.
"""

from __future__ import annotations

import numpy as np

STATE_WINDOW = 720          # canonical 720-slot rolling state
PATH_WINDOW = 6             # tau = 0..5
MEDIAN_COEFF = 0.45
SIGMA_COEFF = 0.015
PERSISTENCE_SCALE = 1.15
OLS_LAG = 20
BASE2_SCALE = 0.30
ALPHA2_DIVISOR = 0.002
W2_CLIP = 0.30
TOPOLOGY_MULT = {"PERSISTENT": 1.8, "FRAGILE": 0.6, "NO_HOLE": 0.0}
OLS_COND_TOL = 1e12        # preregistered stable-inversion tolerance

# Pair order for the 6 unordered pairs among {W, E, C, I}.
PAIRS = [("W", "E"), ("W", "C"), ("W", "I"), ("E", "C"), ("E", "I"), ("C", "I")]
PAIR_INDEX = {p: i for i, p in enumerate(PAIRS)}


def zscore_720(returns: np.ndarray, valid: np.ndarray) -> tuple:
    """Rolling z-scores over the 720-slot state (population std, ddof=0,
    current slot included). Std==0 -> z=0 (deterministic)."""
    n = len(returns)
    z = np.full(n, np.nan)
    z_valid = np.zeros(n, dtype=bool)
    for t in range(n):
        if t < STATE_WINDOW - 1:
            continue
        window = returns[t - STATE_WINDOW + 1 : t + 1]
        win_valid = valid[t - STATE_WINDOW + 1 : t + 1]
        if not np.all(np.isfinite(window[win_valid])):
            continue
        if not win_valid.all():
            continue  # z-state requires fully valid window (fail closed)
        mean = window.mean()
        std = window.std(ddof=0)
        if std == 0.0:
            z[t] = 0.0
        else:
            z[t] = (returns[t] - mean) / std
        z_valid[t] = True
    return z, z_valid


def vr_distances(z_dict: dict, path_window: int = PATH_WINDOW) -> tuple:
    """Per-slot D_ij for all 6 pairs. z_dict maps asset -> z array.

    Returns ((n,6) array in PAIRS order, validity mask).
    """
    assets = list(z_dict)
    n = len(z_dict[assets[0]])
    out = np.full((n, 6), np.nan)
    valid = np.zeros(n, dtype=bool)
    for t in range(n):
        if t < path_window - 1:
            continue
        ok = True
        for k, (i, j) in enumerate(PAIRS):
            seg_i = z_dict[i][t - path_window + 1 : t + 1]
            seg_j = z_dict[j][t - path_window + 1 : t + 1]
            if not (np.all(np.isfinite(seg_i)) and np.all(np.isfinite(seg_j))):
                ok = False
                break
            out[t, k] = float(np.sqrt(((seg_i - seg_j) ** 2).sum()))
        if ok:
            valid[t] = True
    return out, valid


NODE_INDEX = {"W": 0, "E": 1, "C": 2, "I": 3}


def beta1_of_complex(edge: np.ndarray) -> float:
    """beta1 of the VR complex on 4 nodes with all vertices included.

    edge: bool array of 6 entries in PAIRS order.
    beta1 = beta0 - (V - E + F - T), V=4, F=#3-cliques, T=1 if all edges.
    """
    e = np.asarray(edge, dtype=bool)
    e_idx = {p: bool(e[PAIR_INDEX[p]]) for p in PAIRS}
    # connected components over edges (isolated vertices are components)
    parent = list(range(4))
    edges_used = 0

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (i, j) in PAIRS:
        if e_idx[(i, j)]:
            edges_used += 1
            ri, rj = NODE_INDEX[i], NODE_INDEX[j]
            ri, rj = find(ri), find(rj)
            if ri != rj:
                parent[ri] = rj
    components = len({find(k) for k in range(4)})
    triangles = 0
    for a in range(4):
        for b in range(a + 1, 4):
            for c in range(b + 1, 4):
                nodes = "WECI"
                if (e_idx[(nodes[a], nodes[b])] and e_idx[(nodes[a], nodes[c])]
                        and e_idx[(nodes[b], nodes[c])]):
                    triangles += 1
    tetra = 1 if edges_used == 6 else 0
    beta0 = float(components)
    chi = 4 - edges_used + triangles - tetra
    beta1 = beta0 - chi
    return float(beta1)


def classify_distances(d: np.ndarray, eps: float) -> str:
    """PERSISTENT / FRAGILE / NO_HOLE from beta1 at eps and 1.15*eps."""
    b1 = beta1_of_complex(d <= eps)
    b1_wide = beta1_of_complex(d <= PERSISTENCE_SCALE * eps)
    if b1 > 0 and b1_wide > 0:
        return "PERSISTENT"
    if b1 > 0 and b1_wide == 0:
        return "FRAGILE"
    return "NO_HOLE"


def frozen_classification(snapshot_class: np.ndarray, ny_hour: np.ndarray,
                          default: str = "NO_HOLE") -> np.ndarray:
    """Effective per-slot classification honoring the noon snapshot schedule.

    The classification computed at a noon snapshot slot s (ny_hour 11)
    applies from slot s+2 (13:00 bar open) until the next snapshot's
    application; slots before the first application use `default`.
    """
    n = len(snapshot_class)
    effective = np.full(n, default, dtype=object)
    events = [(t, snapshot_class[t]) for t in range(n)
              if ny_hour[t] == 11 and snapshot_class[t] not in ("", None)]
    idx = 0
    for t in range(n):
        while idx < len(events) and events[idx][0] + 2 <= t:
            idx += 1
        if idx > 0:
            effective[t] = events[idx - 1][1]
    return effective


def k3_ols(dec: np.ndarray, dwe: np.ndarray, dwc: np.ndarray, valid: np.ndarray) -> dict:
    """Literal causal OLS per slot. Returns per-slot beta, Dhat, validity."""
    n = len(dec)
    beta = np.full((n, 3), np.nan)
    dhat = np.full(n, np.nan)
    ok = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < OLS_LAG:
            reasons[t] = "INVALID: insufficient history (<20 bars)"
            continue
        seg = np.arange(t - OLS_LAG, t)  # t-1 .. t-20 (current t EXCLUDED)
        y = dec[seg]
        x1 = dwe[seg]
        x2 = dwc[seg]
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x1))
                and np.all(np.isfinite(x2))):
            reasons[t] = "INVALID: non-finite lagged inputs"
            continue
        xmat = np.column_stack([np.ones(OLS_LAG), x1, x2])
        xtx = xmat.T @ xmat
        cond = np.linalg.cond(xtx)
        if not np.isfinite(cond) or cond > OLS_COND_TOL:
            reasons[t] = f"K3_OLS_VALID=false: X^T X unstable (cond={cond:.3e})"
            continue
        try:
            xtx_inv = np.linalg.inv(xtx)
        except np.linalg.LinAlgError:
            reasons[t] = "K3_OLS_VALID=false: singular X^T X (literal inverse failed)"
            continue
        b = xtx_inv @ (xmat.T @ y)
        if not np.all(np.isfinite(b)):
            reasons[t] = "K3_OLS_VALID=false: non-finite coefficients"
            continue
        # Prediction uses CURRENT D_WE(t), D_WC(t) — allowed by the contract.
        if not (np.isfinite(dwe[t]) and np.isfinite(dwc[t])):
            reasons[t] = "INVALID: current inputs non-finite"
            continue
        beta[t] = b
        dhat[t] = b[0] + b[1] * dwe[t] + b[2] * dwc[t]
        ok[t] = True
        reasons[t] = "VALID"
    return {"beta": beta, "dhat": dhat, "valid": ok, "reason": reasons}


def k3_alpha(dec: np.ndarray, dhat: np.ndarray, r_e: np.ndarray, r_c: np.ndarray,
             topology_mult: np.ndarray, valid: np.ndarray) -> tuple:
    """alpha2, base2, w2 with topology multiplier and clip."""
    n = len(dec)
    alpha2 = np.zeros(n)
    base2 = np.zeros(n)
    w2 = np.zeros(n)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if not valid[t] or not np.isfinite(dhat[t]) or not np.isfinite(dec[t]):
            reasons[t] = "INACTIVE: OLS invalid or inputs non-finite"
            continue
        if not (np.isfinite(r_e[t]) and np.isfinite(r_c[t])):
            reasons[t] = "INACTIVE: r_E/r_C non-finite"
            continue
        alpha2[t] = np.sign(r_e[t] + r_c[t]) * abs(dec[t] - dhat[t])
        base2[t] = BASE2_SCALE * np.sign(alpha2[t]) * (abs(alpha2[t]) / ALPHA2_DIVISOR)
        w2[t] = np.clip(base2[t] * topology_mult[t], -W2_CLIP, W2_CLIP)
        reasons[t] = "ACTIVE"
    return w2, alpha2, base2, reasons
