"""
CR-RISK-BLOCK2 R6 — Analysis studies (XIV-XVII, XXII-XXV).

- R6_DIRECTIONAL_OVERLAP (XVI): same-direction vs opposing overlap attribution
  at the event level (admitted set under H0, reference f).
- R6_FAMILY_EPISODE_STRUCTURE (XVII): 12h-cluster composition classes
  (A-only / B-only / A+A / B+B / A+B) and their risk profile.
- R6_EPISODE_POLICY_RESULTS (XV): per-episode accounting under every policy.
- R6_HEAT_EFFICIENCY (XIV): DD reduction vs return sacrifice vs H0.
- R6_REJECTED_EVENT_AUDIT (XXII): ex-post characterization of what each
  constraint sacrifices (never used to modify the policy).
- R6_HEAT_TEMPORAL_STABILITY (XXIII): rejection/performance by partition.
- R6_POLICY_COMPLEXITY_MATRIX (XXV): static complexity levels.

All statistics are descriptive; no policy is selected.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r6_common import (F_GRID, POLICY_GRID, _hourly_heat, run_policy)

TAIL_R = -1.0


def _adm_df(load: Dict, policy: Dict, w_A: float, w_B: float) -> pd.DataFrame:
    res = run_policy(load, policy, w_A, w_B, full_output=True)
    res["year"] = pd.to_datetime(res["entry_ts"], utc=True).dt.year
    res["split"] = load["ba"]["tb"]["split"].to_numpy()
    return res


# ---------------------------------------------------------------------------
# XII. Overlap anatomy (before judging any policy)
# ---------------------------------------------------------------------------

def overlap_anatomy(load: Dict, w_A: float, w_B: float) -> pd.DataFrame:
    """Describe the actual source of risk in the unconstrained book before
    any policy is judged: overlap frequency, time share by active count,
    drawdown attribution by overlap state, and whether the worst day / worst
    24h / worst episode occurred while gross heat exceeded one event-unit.

    Drawdown attribution: for every hour where the account path is below its
    running peak, its return is attributed to the concurrent-position state
    (1 / 2 / 3+ active). The share of the summed in-drawdown hourly loss is
    reported per state.
    """
    ba = load["ba"]
    tb = ba["tb"]
    ep = load["episode_ledger"]
    r1 = load["risk1_heat"]
    n_open = r1["n_open"].to_numpy()
    rows = []
    a = rows.append

    # 1. event-level overlap share
    n = len(tb)
    ov_at_entry = int((ep["concurrent_position_count_at_entry"] >= 1).sum())
    a({"metric": "events_total", "value": float(n), "detail": "sealed 890-event A/B book"})
    a({"metric": "events_with_overlap_at_entry_share",
       "value": ov_at_entry / n, "detail": "share of events entering while >=1 other position active"})
    sizes = ep.groupby("episode_id")["event_id"].count()
    multi = sizes[sizes >= 2].index
    in_multi = int(ep["episode_id"].isin(multi).sum())
    a({"metric": "events_in_multi_event_episodes_share",
       "value": in_multi / n,
       "detail": "share of events whose 12h episode contains >=2 events"})

    # 2. time share by active count (in-market hours)
    hours_in = int((n_open > 0).sum())
    for k, label in [(1, "time_share_1_active"), (2, "time_share_2_active"),
                     (3, "time_share_3plus_active")]:
        a({"metric": label, "value": float((n_open >= k).sum()) / max(hours_in, 1),
           "detail": "share of in-market hours with >=k active positions (R1 hourly frame)"})
    a({"metric": "in_market_hours", "value": float(hours_in),
       "detail": "hours with >=1 position in R1_PORTFOLIO_HEAT"})
    a({"metric": "hours_with_2plus", "value": float((n_open >= 2).sum()),
       "detail": "absolute hours with 2+ positions"})
    a({"metric": "hours_with_3plus", "value": float((n_open >= 3).sum()),
       "detail": "absolute hours with 3+ positions"})

    # 3. drawdown attribution by overlap state (H0, 50/50, f=1%)
    from .phase_r6_common import run_policy
    adm, _ = run_policy(load, {"kind": "H0", "cap_mult": None,
                               "treatment": "REJECT"}, w_A, w_B)
    # authoritative hourly frame = R1_PORTFOLIO_HEAT grid; both the active-
    # position state and the account path are computed on it (identical
    # bucketing as the sealed R1 n_open series).
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    full = pd.to_datetime(r1["ts"], utc=True)
    idx_int = full.to_numpy(dtype="int64")
    state = np.zeros(len(full), dtype=int)
    r_h = np.zeros(len(full))
    for i, f_ in enumerate(adm):
        if f_ <= 0:
            continue
        lo = np.searchsorted(idx_int, int(entry.iloc[i].value))
        hi = np.searchsorted(idx_int, int(exit_.iloc[i].value))
        state[lo:hi] += 1
        g = load["hourly_inc"].get(tb["event_id"].iloc[i])
        if g is None:
            continue
        for t_, v in zip(g["mark_time"].to_numpy(dtype="int64"),
                         g["inc_R"].to_numpy(dtype=float)):
            p = np.searchsorted(idx_int, int(t_))
            if 0 <= p < len(r_h):
                r_h[p] += 0.01 * f_ * v
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r_h)])
    peak_eq = np.maximum.accumulate(eq)
    in_dd = eq[:-1] < peak_eq[:-1] - 1e-12
    dd_hours = np.where(in_dd)[0]
    loss_by_state = {1: 0.0, 2: 0.0, 3: 0.0}
    for h in dd_hours:
        k = int(state[h])
        k = 3 if k >= 3 else (2 if k >= 2 else 1)
        loss_by_state[k] += min(r_h[h], 0.0)
    tot = sum(loss_by_state.values())
    a({"metric": "dd_hours", "value": float(len(dd_hours)),
       "detail": "hours below running peak in H0 50/50 f=1% hourly path"})
    for k, label in [(1, "dd_share_single_position"), (2, "dd_share_2_overlap"),
                     (3, "dd_share_3plus_overlap")]:
        a({"metric": label, "value": -loss_by_state[k] / max(-tot, 1e-12),
           "detail": "share of summed in-drawdown hourly loss occurring with "
                      f"{k} active position(s)"})

    # 4. worst day / worst 24h / worst episode vs gross heat > 1 event-unit
    ret_by_ts = pd.Series(r_h, index=full)
    day_ret = ret_by_ts.groupby(ret_by_ts.index.normalize()).sum()
    worst_day = day_ret.idxmin()
    day_state_max = int(state[(full >= worst_day) & (full < worst_day + pd.Timedelta(days=1))].max())
    a({"metric": "worst_day_return_pct", "value": float(day_ret.min() * 100),
       "detail": "worst calendar-day account return, H0 50/50 f=1%"})
    a({"metric": "worst_day_max_active", "value": float(day_state_max),
       "detail": "max concurrent positions on the worst day"})
    a({"metric": "worst_day_exceeded_1_event_unit",
       "value": float(day_state_max > 1), "detail": "gross heat > 1 event-unit on worst day"})
    # worst rolling 24h
    roll = ret_by_ts.rolling(24, min_periods=1).sum()
    w24_end = roll.idxmin()
    w24_start = w24_end - pd.Timedelta(hours=23)
    w24_state_max = int(state[(full >= w24_start) & (full <= w24_end)].max())
    a({"metric": "worst_24h_return_pct", "value": float(roll.min() * 100),
       "detail": "worst rolling-24h account return, H0 50/50 f=1%"})
    a({"metric": "worst_24h_max_active", "value": float(w24_state_max),
       "detail": "max concurrent positions in the worst 24h window"})
    a({"metric": "worst_24h_exceeded_1_event_unit",
       "value": float(w24_state_max > 1), "detail": "gross heat > 1 event-unit in worst 24h"})
    # worst episode (worst realized 12h cluster loss, H0 admitted set)
    clus = ba["clus"]
    r_R = ba["r_R"]
    cluster_ret = {}
    for i in range(n):
        if adm[i] > 0:
            c = int(clus[i])
            cluster_ret[c] = cluster_ret.get(c, 0.0) + adm[i] * r_R[i]
    worst_c = min(cluster_ret, key=cluster_ret.get)
    ep_peak = int(ep.loc[ep.episode_id == worst_c, "episode_peak_heat"].max())
    a({"metric": "worst_episode_loss_R", "value": float(cluster_ret[worst_c]),
       "detail": f"worst 12h-episode realized loss (admitted f * R), episode {worst_c}"})
    a({"metric": "worst_episode_max_active", "value": float(ep_peak),
       "detail": "peak R1 n_open inside the worst episode"})
    a({"metric": "worst_episode_exceeded_1_event_unit",
       "value": float(ep_peak > 1), "detail": "gross heat > 1 event-unit in worst episode"})
    return pd.DataFrame(rows, columns=["metric", "value", "detail"])


# ---------------------------------------------------------------------------
# XVI. Directional overlap
# ---------------------------------------------------------------------------

def directional_overlap(load: Dict, w_A: float, w_B: float) -> pd.DataFrame:
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True).to_numpy(dtype="int64")
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True).to_numpy(dtype="int64")
    direc = ba["dir"]
    fam = ba["fam"]
    r_R = ba["r_R"]
    n = len(tb)
    same = np.zeros(n, dtype=bool)
    opp = np.zeros(n, dtype=bool)
    for i in range(n):
        for j in range(i):
            if exit_[j] > entry[i]:
                if direc[j] == direc[i]:
                    same[i] = same[j] = True
                else:
                    opp[i] = opp[j] = True
    neg_total = float(-r_R[r_R < 0].sum())
    rows = []
    for label, mask in [("same_direction", same), ("opposing", opp),
                        ("no_overlap", ~(same | opp))]:
        sub = r_R[mask]
        n_ev = int(mask.sum())
        if n_ev == 0:
            rows.append({"overlap_type": label, "N": 0})
            continue
        neg = sub[sub < 0]
        rows.append({
            "overlap_type": label, "N": n_ev,
            "mean_R": float(sub.mean()), "median_R": float(np.median(sub)),
            "loss_probability": float((sub < 0).mean()),
            "tail_loss_probability": float((sub <= TAIL_R).mean()),
            "mean_episode_CAE_R": float(load["episode_ledger"]
                                        .set_index("event_id").loc[
                                            tb["event_id"][mask], "episode_worst_CAE_R"].mean()),
            "share_of_total_negative_R": float(-neg.sum() / max(neg_total, 1e-12)),
            "mean_R_per_event": float(sub.mean()),
        })
    out = pd.DataFrame(rows)
    out.attrs["overlap_hours"] = {
        "same_direction": float(load["risk1_cc"].iloc[0]["same_direction_overlap_hours"]),
        "opposing": float(load["risk1_cc"].iloc[0]["opposite_direction_overlap_hours"]),
    }
    return out


# ---------------------------------------------------------------------------
# XVII. Family episode structure
# ---------------------------------------------------------------------------

def family_episode_structure(load: Dict, w_A: float, w_B: float) -> pd.DataFrame:
    ba = load["ba"]
    tb = ba["tb"]
    fam = ba["fam"]
    r_R = ba["r_R"]
    clus = ba["clus"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    total_neg = max(-float(r_R[r_R < 0].sum()), 1e-12)
    rows = []
    for c in np.unique(clus):
        m = np.where(clus == c)[0]
        fA = int((fam[m] == "A").sum())
        fB = len(m) - fA
        if fB == 0:
            comp = "A_only" if fA == 1 else "A_A"
        elif fA == 0:
            comp = "B_only" if fB == 1 else "B_B"
        else:
            comp = "A_B"
        r_ = r_R[m]
        # peak heat at 50/50 f=1: max concurrent * 0.5% (weights equal here)
        peak_conc = 0
        for i in m:
            cnt = sum(1 for j in m if exit_.iloc[j] > entry.iloc[i] and j != i)
            peak_conc = max(peak_conc, cnt + 1)
        peak_heat = peak_conc * (w_A if fam[m[0]] == "A" else w_B) / 100.0
        cae = 0.0
        rows.append({
            "cluster_id": int(c), "composition": comp,
            "n_events": len(m), "n_A": fA, "n_B": fB,
            "mean_R": float(r_.mean()), "loss_prob": float((r_ < 0).mean()),
            "tail_prob": float((r_ <= TAIL_R).mean()),
            "peak_heat_pct": peak_heat,
            "worst_CAE_R": cae,
            "cluster_neg_share": float(-r_[r_ < 0].sum() / total_neg) if (r_ < 0).any() else 0.0,
            "cluster_realized_R": float(r_.sum()),
        })
    df = pd.DataFrame(rows)
    agg = df.groupby("composition").agg(
        n_clusters=("cluster_id", "count"), n_events=("n_events", "sum"),
        mean_R=("mean_R", "mean"),
        loss_prob=("loss_prob", "mean"),
        tail_prob=("tail_prob", "mean"),
        peak_heat_p95=("peak_heat_pct", lambda s: np.percentile(s, 95)),
        cluster_neg_share=("cluster_neg_share", "sum"),
    ).reset_index()
    agg["n_events"] = agg["n_events"].astype(int)
    return agg


# ---------------------------------------------------------------------------
# XV. Episode policy results
# ---------------------------------------------------------------------------

def episode_policy_results(load: Dict, policies: List[Dict],
                           w_A: float, w_B: float) -> pd.DataFrame:
    ba = load["ba"]
    tb = ba["tb"]
    r_R = ba["r_R"]
    clus = ba["clus"]
    fam = ba["fam"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    rows = []
    for pol in policies:
        res = run_policy(load, pol, w_A, w_B, full_output=True)
        adm = res["admitted_f"].to_numpy()
        for c in np.unique(clus):
            m = np.where(clus == c)[0]
            n_cand = len(m)
            n_adm = int((adm[m] > 0).sum())
            n_rej = int((adm[m] <= 0).sum())
            fA = int(((fam[m] == "A") & (adm[m] > 0)).sum())
            fB = n_adm - fA
            ep_ret = float((adm[m] * r_R[m]).sum())
            # sequential cumsum in entry order (admitted f * r)
            order = sorted(m, key=lambda i: entry.iloc[i])
            eq = np.concatenate([[0.0], np.cumsum([adm[i] * r_R[i] for i in order])])
            ep_cae = float(eq.min())
            # max gross heat inside episode at reference f=1 (weights applied)
            max_heat = 0.0
            entry_ns = entry.to_numpy(dtype="int64")
            for i in order:
                if adm[i] <= 0:
                    continue
                active = [j for j in order if j != i and
                          entry_ns[j] <= entry_ns[i] <
                          entry_ns[j] + int(6 * 3600 * 1e9)]
                heat = adm[i] + sum(adm[j] for j in active)
                max_heat = max(max_heat, heat)
            rows.append({
                "policy_id": pol["policy_id"], "kind": pol["kind"],
                "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                "episode_id": int(c), "n_candidate_events": n_cand,
                "n_admitted": n_adm, "n_rejected": n_rej,
                "n_A_admitted": fA, "n_B_admitted": fB,
                "max_gross_heat_pct": max_heat,
                "episode_return_R": ep_ret,
                "episode_worst_CAE_R": ep_cae,
                "episode_duration_h": float(load["episode_durations"][int(c)]),
            })
    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# XIV. Heat efficiency vs H0
# ---------------------------------------------------------------------------

def heat_efficiency(load: Dict, policies: List[Dict], w_A: float,
                    w_B: float) -> pd.DataFrame:
    years = load["years"]
    rows = []
    h0 = next(p for p in policies if p["policy_id"] == "H0")
    h0_adm, _ = run_policy(load, h0, w_A, w_B)
    h0m = {f: _policy_metrics_at(load, h0_adm, f, years)
           for f in F_GRID}
    for pol in policies:
        if pol["policy_id"] == "H0":
            continue
        adm, _ = run_policy(load, pol, w_A, w_B)
        for f in F_GRID:
            m = _policy_metrics_at(load, adm, f, years)
            m0 = h0m[f]
            rows.append({
                "policy_id": pol["policy_id"], "kind": pol["kind"],
                "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                "f_pct": f,
                "dd_reduction_pp": (m0["max_dd"] - m["max_dd"]) * 100.0,
                "cagr_reduction_pp": (m0["cagr"] - m["cagr"]) * 100.0,
                "terminal_reduction_pct": (m0["terminal_equity"] - m["terminal_equity"]) / max(m0["terminal_equity"], 1e-12) * 100.0,
                "worst_day_improvement_pp": (m0["worst_day_pct"] - m["worst_day_pct"]) * 100.0,
                "worst_episode_improvement_pp": (m0["worst_episode_pct"] - m["worst_episode_pct"]) * 100.0,
                "dd_reduction_per_cagr_pp":
                    (m0["max_dd"] - m["max_dd"]) / max(m0["cagr"] - m["cagr"], 1e-9),
            })
    return pd.DataFrame(rows)


def _policy_metrics_at(load: Dict, admitted_f: np.ndarray, f: float,
                       years: float) -> Dict:
    from .phase_r6_common import policy_metrics
    return policy_metrics(load, admitted_f, f / 100.0, years)


# ---------------------------------------------------------------------------
# XXII. Rejected-event audit
# ---------------------------------------------------------------------------

def rejected_event_audit(load: Dict, policies: List[Dict],
                         w_A: float, w_B: float) -> pd.DataFrame:
    ba = load["ba"]
    tb = ba["tb"]
    r_R = ba["r_R"]
    fam = ba["fam"]
    rows = []
    for pol in policies:
        res = run_policy(load, pol, w_A, w_B, full_output=True)
        rej = res[res["decision"] == "REJECT_HEAT_CAP"]
        sca = res[res["decision"] == "ACCEPT_SCALED"]
        for tag, sub in [("rejected", rej), ("scaled", sca)]:
            if len(sub) == 0:
                rows.append({
                    "policy_id": pol["policy_id"], "kind": pol["kind"],
                    "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                    "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                    "group": tag, "N": 0,
                })
                continue
            r_ = sub["r_final"].to_numpy()
            w_ = sub["requested_f"].to_numpy()
            pos, neg = r_[r_ > 0], r_[r_ < 0]
            w_pos, w_neg = w_[r_ > 0], w_[r_ < 0]
            rows.append({
                "policy_id": pol["policy_id"], "kind": pol["kind"],
                "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                "group": tag, "N": int(len(sub)),
                "mean_original_R": float(r_.mean()),
                "win_rate": float((r_ > 0).mean()),
                "profit_factor": float(pos.sum() / max(-neg.sum(), 1e-12)),
                "loss_contribution_avoided_R": float((w_neg * neg).sum()),
                "profit_contribution_missed_R": float((w_pos * pos).sum()),
                "share_B": float((sub["family"] == "B").mean()),
                "share_inner_sel": float((sub["split"] == "inner_sel").mean()),
                "share_inner_val": float((sub["split"] == "inner_val").mean()),
                "share_oos": float((sub["split"] == "RELATIONSHIP_CONFIRMED_OOS").mean()),
                "mean_episode_size": float(sub["episode_id"].map(
                    load["cluster_sizes"]).mean()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# XXIII. Temporal stability
# ---------------------------------------------------------------------------

def temporal_stability(load: Dict, policies: List[Dict], w_A: float,
                       w_B: float) -> pd.DataFrame:
    ba = load["ba"]
    tb = ba["tb"]
    r_R = ba["r_R"]
    years = load["years"]
    rows = []
    for pol in policies:
        res = run_policy(load, pol, w_A, w_B, full_output=True)
        res["year"] = pd.to_datetime(res["entry_ts"], utc=True).dt.year
        for part_col in ["split", "year"]:
            for part, sub in res.groupby(part_col):
                adm = sub["admitted_f"].to_numpy()
                r_ = sub["r_final"].to_numpy()
                seq_r = adm * r_
                eq = np.concatenate([[1.0], np.cumprod(1.0 + seq_r)])
                peak = np.maximum.accumulate(eq)
                max_dd = float(((peak - eq) / peak).max())
                worst_ep = 0.0
                for _, g in sub.groupby("episode_id"):
                    worst_ep = min(worst_ep, float((g["admitted_f"] * g["r_final"]).sum()))
                rows.append({
                    "policy_id": pol["policy_id"], "kind": pol["kind"],
                    "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                    "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                    "partition_type": part_col, "partition": str(part),
                    "N": int(len(sub)),
                    "N_rejected": int((adm <= 0).sum()),
                    "reject_rate": float((adm <= 0).mean()),
                    "mean_admitted_f": float(adm[adm > 0].mean()) if (adm > 0).any() else 0.0,
                    "within_partition_max_dd": max_dd,
                    "worst_episode_R": worst_ep,
                    "partition_net_R": float((adm * r_).sum()),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# XXV. Complexity matrix
# ---------------------------------------------------------------------------

COMPLEXITY_LEVEL = {"H0": 0, "H1": 1, "H2": 2, "H3": 2, "H4": 3, "H5": 4}


def complexity_matrix(policies: List[Dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "policy_id": p["policy_id"], "kind": p["kind"],
        "cap_mult": p["cap_mult"], "treatment": p["treatment"],
        "complexity_level": COMPLEXITY_LEVEL[p["kind"]],
        "description": {
            "H0": "unconstrained static (no heat cap)",
            "H1": "gross heat cap",
            "H2": "same-direction heat cap",
            "H3": "family-B heat cap",
            "H4": "12h episode budget",
            "H5": "hybrid gross + same-direction",
        }[p["kind"]],
    } for p in policies])
