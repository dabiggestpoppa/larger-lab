"""
CR-RISK-BLOCK2 R6 — Tail stress (XX) and adversarial episode tests (XXI).

Tail stress: deterministic synthetic overlays on the historical hourly path.
Admission is outcome-independent, so each policy's admitted set is identical
across variants; the variants alter the RETURN of admitted events (or insert
synthetic events AFTER admission, labelled as overlays). Winners are never
invented; losses are amplified only. Variants:

- historical (no change)
- worst5_x1_50 / worst5_x2_00: worst 5% of admitted losses, hourly path scaled
- insert_worst_1: worst admitted loss event's hourly contribution duplicated
- insert_p99_loss_cluster: 5 synthetic p99-magnitude loss events (flat 6h
  bleed) inserted at the worst cluster's window, at the worst event's f
- worstA_cluster / worstB_cluster / mixed_AB_cluster: the worst 12h cluster by
  composition (>=2 A / >=2 B / >=1 each), all admitted members scaled x2.0

Adversarial tests scan the REAL book for the brief's adverse sequences (12h
cluster, entry order): A loss -> B loss -> B loss; A loss -> A loss -> B loss;
3 same-direction concurrent losers; mixed-direction concurrent losses. No
fabricated timestamps; NO_OBSERVED_INSTANCE rows are emitted for absent
patterns.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r6_common import (EPISODE_INTERVAL_H, _hourly_heat, book_arrays,
                              run_policy)

TAIL_F = [0.50, 1.00, 2.00]


def _admitted_series(load: Dict, admitted_f: np.ndarray):
    """Per-event (ts_ns, values) hourly contribution series for admitted events."""
    ba = load["ba"]
    tb = ba["tb"]
    hourly_inc = load["hourly_inc"]
    series = []
    for i, eid in enumerate(tb["event_id"]):
        f_ = admitted_f[i]
        if f_ <= 0:
            continue
        g = hourly_inc.get(eid)
        if g is None or len(g) == 0:
            continue
        ts = pd.to_datetime(g["mark_time"], utc=True).to_numpy(dtype="int64")
        series.append((ts, f_ * g["inc_R"].to_numpy(dtype=float)))
    return series


def _assemble(series: List[Tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    if not series:
        return np.zeros(1)
    t_min = min(s[0].min() for s in series)
    t_max = max(s[0].max() for s in series)
    full = pd.date_range(pd.Timestamp(t_min, tz="UTC"),
                         pd.Timestamp(t_max, tz="UTC"), freq="h")
    idx = full.to_numpy(dtype="int64")
    total = np.zeros(len(full))
    for ts, v in series:
        pos = np.searchsorted(idx, ts)
        for k, p in enumerate(pos):
            total[p] += v[k]
    return total


def _equity_from_r(r_h: np.ndarray, years: float) -> Dict:
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r_h)])
    peak = np.maximum.accumulate(eq)
    max_dd = float(((peak - eq) / peak).max())
    return {"terminal_equity": float(eq[-1]), "max_dd": max_dd}


def heat_tail_stress(load: Dict, policies: List[Dict],
                     w_A: float, w_B: float) -> pd.DataFrame:
    """Tail stress per (policy, f): historical + synthetic overlays."""
    years = load["years"]
    ba = load["ba"]
    r_R = ba["r_R"]
    rows = []
    for pol in policies:
        admit, _ = run_policy(load, pol, w_A, w_B)
        series = _admitted_series(load, admit)
        adm_r = r_R[admit > 0]
        # worst-5% of ADMITTED losses (series index = admitted-subset index)
        loss_mask = (adm_r <= np.quantile(adm_r[adm_r < 0], 0.05)) \
            if (adm_r < 0).any() else np.zeros(len(adm_r), dtype=bool)
        variants: Dict[str, List[Tuple[np.ndarray, np.ndarray]]] = {
            "historical": series}
        for mult in [1.50, 2.00]:
            v = []
            for i, (ts, vals) in enumerate(series):
                if loss_mask[i] and vals.sum() < 0:
                    v.append((ts, vals * mult))
                else:
                    v.append((ts, vals))
            variants[f"worst5_x{mult:.2f}".replace(".", "_")] = v
        # insert worst admitted loss (duplicated at its timestamps)
        worst_i = int(np.argmin(adm_r))
        book_i = int(np.where(admit > 0)[0][worst_i])
        w_series = series[worst_i]
        variants["insert_worst_1"] = series + [w_series]
        # p99 loss cluster: 5 flat 6h bleeds at the p99 loss magnitude
        p99 = float(np.quantile(r_R[r_R < 0], 0.01))
        f_worst = float(admit[book_i])
        clus_worst = int(ba["clus"][book_i])
        members = np.where(ba["clus"] == clus_worst)[0]
        t_start = pd.to_datetime(ba["tb"]["entry_ts"].iloc[members[0]], utc=True)
        extra = []
        for k in range(5):
            t0 = t_start + pd.Timedelta(hours=k)
            ts = (t0 + pd.to_timedelta(np.arange(7), unit="h")).to_numpy(dtype="int64")
            vals = np.full(7, -(f_worst * p99) / 6.0)
            extra.append((ts, vals))
        variants["insert_p99_loss_cluster"] = series + extra
        # worst clusters by composition
        fam = ba["fam"]
        admitted_idx = np.where(admit > 0)[0]
        for tag, need in [("worstA_cluster", "A"), ("worstB_cluster", "B"),
                          ("mixed_AB_cluster", "AB")]:
            best_c = None
            best_loss = 0.0
            for c in np.unique(ba["clus"]):
                m = np.where(ba["clus"] == c)[0]
                am = [i for i in m if admit[i] > 0]
                if not am:
                    continue
                fA = sum(1 for i in am if fam[i] == "A")
                fB = len(am) - fA
                if need == "A" and fA < 2:
                    continue
                if need == "B" and fB < 2:
                    continue
                if need == "AB" and (fA < 1 or fB < 1):
                    continue
                loss = float(sum(admit[i] * r_R[i] for i in am if r_R[i] < 0))
                if loss < best_loss:
                    best_loss = loss
                    best_c = c
            v = []
            if best_c is None:
                v = series
            else:
                hot = set(int(i) for i in np.where(ba["clus"] == best_c)[0])
                for i, (ts, vals) in enumerate(series):
                    v.append((ts, vals * 2.0 if i in hot else vals))
            variants[tag] = v
        for f in TAIL_F:
            base_dd = _equity_from_r(f / 100.0 * _assemble(series), years)["max_dd"]
            for name, v in variants.items():
                r_h = _assemble(v)
                m = _equity_from_r(f / 100.0 * r_h, years)
                rows.append({
                    "policy_id": pol["policy_id"], "kind": pol["kind"],
                    "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                    "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                    "f_pct": f, "variant": name,
                    "max_dd": m["max_dd"], "terminal_equity": m["terminal_equity"],
                    "max_dd_ratio_vs_historical": m["max_dd"] / max(base_dd, 1e-12),
                })
    return pd.DataFrame(rows)


def _overlap3(a: Tuple[float, float], b: Tuple[float, float],
              c: Tuple[float, float]) -> bool:
    return max(a[0], b[0], c[0]) < min(a[1], b[1], c[1])


def adversarial_episode_tests(load: Dict, w_A: float, w_B: float) -> pd.DataFrame:
    """Scan the REAL book for the brief's adverse sequences; report observed
    instances (up to 5 worst by realized loss) + counts + policy admission."""
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    r_R = ba["r_R"]
    fam = ba["fam"]
    direc = ba["dir"]
    clus = ba["clus"]
    patterns = {
        "A_loss_B_loss_B_loss": [("A", -1), ("B", -1), ("B", -1)],
        "A_loss_A_loss_B_loss": [("A", -1), ("A", -1), ("B", -1)],
    }
    rows = []
    for c in np.unique(clus):
        m = np.where(clus == c)[0]
        order = sorted(m, key=lambda i: entry.iloc[i])
        if len(order) < 3:
            continue
        seq = [(fam[i], np.sign(r_R[i])) for i in order]
        for pat_name, pat in patterns.items():
            for k in range(len(order) - 2):
                if seq[k:k + 3] == pat:
                    ids = [tb["event_id"].iloc[order[k + j]] for j in range(3)]
                    loss = float(sum(r_R[order[k + j]] for j in range(3)))
                    rows.append(_adversarial_row(load, "seq", pat_name, c, ids,
                                                 order[k:k + 3], loss, w_A, w_B))
    # 3 same-direction concurrent losers
    for c in np.unique(clus):
        m = np.where(clus == c)[0]
        if len(m) < 3:
            continue
        for combo in _combos(m, 3):
            if not (r_R[list(combo)] < 0).all():
                continue
            d0 = direc[combo[0]]
            if not (direc[list(combo)] == d0).all():
                continue
            ints = [(entry.iloc[i].value, exit_.iloc[i].value) for i in combo]
            if not _overlap3(*ints):
                continue
            ids = [tb["event_id"].iloc[i] for i in combo]
            loss = float(sum(r_R[i] for i in combo))
            rows.append(_adversarial_row(load, "overlap", "3_same_dir_losers", c,
                                         ids, list(combo), loss, w_A, w_B))
    # mixed-direction concurrent losses (>=1 A + >=1 B, all losers, overlap)
    for c in np.unique(clus):
        m = np.where(clus == c)[0]
        if len(m) < 2:
            continue
        for combo in _combos(m, 2):
            if not (r_R[list(combo)] < 0).all():
                continue
            if set(fam[list(combo)]) != {"A", "B"}:
                continue
            ints = [(entry.iloc[i].value, exit_.iloc[i].value) for i in combo]
            if not (max(ints[0][0], ints[1][0]) < min(ints[0][1], ints[1][1])):
                continue
            ids = [tb["event_id"].iloc[i] for i in combo]
            loss = float(sum(r_R[i] for i in combo))
            rows.append(_adversarial_row(load, "overlap", "mixed_dir_concurrent", c,
                                         ids, list(combo), loss, w_A, w_B))
    out = pd.DataFrame(rows) if rows else pd.DataFrame()
    # pattern presence summary
    present = set(out["pattern"]) if len(out) else set()
    for pat in ["A_loss_B_loss_B_loss", "A_loss_A_loss_B_loss",
                "3_same_dir_losers", "mixed_dir_concurrent"]:
        if pat not in present:
            out = pd.concat([out, pd.DataFrame([{
                "pattern": pat, "mode": "scan", "n_observed": 0,
                "note": "NO_OBSERVED_INSTANCE in the sealed 890-event book"}])],
                ignore_index=True)
    return out


def _combos(m: np.ndarray, k: int):
    from itertools import combinations
    return list(combinations(m.tolist(), k))


def _adversarial_row(load: Dict, mode: str, pattern: str, cluster: int,
                     ids: List[str], idx_list: List[int], loss: float,
                     w_A: float, w_B: float) -> Dict:
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    req_mult = np.where(ba["fam"] == "A", w_A, w_B)
    f0 = 0.01  # reference f=1%
    pre_heat = 0.0
    admitted = {}
    for pid in ["H0", "H1-1.00-REJ", "H2-1.00-REJ", "H4-1.00-REJ"]:
        from .phase_r6_common import POLICY_GRID
        pol = next(p for p in POLICY_GRID if p["policy_id"] == pid)
        from .phase_r6_common import _admit_sweep
        f_ = _admit_sweep(ba["entry"], ba["exit_"], ba["fam"], ba["dir"],
                          ba["clus"], req_mult, pol, 1.0)
        admitted[pid] = {int(i): float(f_[i]) for i in idx_list}
    # peak CAE within cluster (R units, unscaled)
    members = np.where(ba["clus"] == cluster)[0]
    caes = []
    for i in members:
        g = load["hourly_inc"].get(tb["event_id"].iloc[i])
        if g is not None:
            caes.extend(g["inc_R"].to_numpy(dtype=float))
    peak_cae = float(min(caes)) if caes else 0.0
    return {
        "pattern": pattern, "mode": mode, "n_observed": 1,
        "cluster_id": int(cluster),
        "event_ids": "|".join(ids),
        "families": "|".join(ba["fam"][idx_list]),
        "directions": "|".join(str(int(d)) for d in ba["dir"][idx_list]),
        "r_R_seq": "|".join(f"{ba['r_R'][i]:.2f}" for i in idx_list),
        "realized_loss_R": loss,
        "account_loss_at_f1_pct": loss * 0.01 * 100.0,
        "admitted_H0": "|".join(f"{admitted['H0'][i]:.3f}" for i in idx_list),
        "admitted_H1_1x": "|".join(f"{admitted['H1-1.00-REJ'][i]:.3f}" for i in idx_list),
        "admitted_H2_1x": "|".join(f"{admitted['H2-1.00-REJ'][i]:.3f}" for i in idx_list),
        "admitted_H4_1x": "|".join(f"{admitted['H4-1.00-REJ'][i]:.3f}" for i in idx_list),
        "cluster_peak_CAE_R": peak_cae,
    }
