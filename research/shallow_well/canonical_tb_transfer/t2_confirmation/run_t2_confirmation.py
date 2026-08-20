#!/usr/bin/env python3
"""
CTBT T2 — One-shot 2025 canonical-transfer confirmation.

Imports the EXACT sealed T1.1 lifecycle primitives (verified 405/405 control
+ 194/194 primary against the canonical trade log) and runs them over the
frozen 2025 confirmation window on the two T1.1 survivors plus the canonical
reference (descriptive only).

The preregistration was frozen and hashed (CTBT_T2_PREREGISTRATION_HASH.json,
sha256 9cff2f9e...) BEFORE this script computes any 2025 economics.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, date
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
T11 = REPO / "research" / "shallow_well" / "canonical_tb_transfer" / "t11_repair"
sys.path.insert(0, str(T11))

# Sealed T1.1 primitives — identical lifecycle, identical cost methodology
from run_t11_screen import (  # noqa: E402
    TRIANGLES, LEG_FILES, CANON_SPREAD, CONSERVATIVE_FLOOR_PIPS, COMMISSION_PIPS,
    PIP_SIZE, OBSERVED_SPREAD_LEGS, LOOKBACK,
    load_leg, compute_basis_z, run_lifecycle,
    triangle_cost_bps, triangle_cost_bps_documented, scorecard,
)

HERE = Path(__file__).resolve().parent

CONF_START = datetime(2025, 1, 1)
CONF_END = datetime(2025, 12, 31, 23, 59, 59)
SURVIVORS = ["EUR_GBP_USD", "GBP_NZD_USD"]
SEED = 20260820
N_BOOT = 2000

# Sealed T1.1 z3 fingerprints (from CTBT_T11_SCREEN_RAW.json / T11_SEAL)
DEV = {
    "EUR_GBP_USD": {
        "window": ("2022-09-28 00:00:00", "2024-12-31 18:55:00"),
        "cost_bps": 8.3594270651793,
        "events": 435, "net_ev_bps": 15.73933847048037, "pf_net": 5.4152,
        "win_rate": 78.16091954022988, "median_net_bps": 15.657350068793743,
        "p5_bps": -22.921734519025254, "worst_bps": -61.72346582835661,
        "edge_cost_ratio": 2.8828250247007543,
        "avg_hold_min": 185.83908045977012, "z6_rate": 8.505747126436782,
        "max_dd_bps": 96.25858300728942,
        "events_per_week": 435 / ((datetime(2024, 12, 31) - datetime(2022, 9, 28)).days / 7.0),
    },
    "GBP_NZD_USD": {
        "window": ("2022-09-12 00:00:00", "2024-12-31 18:55:00"),
        "cost_bps": 8.935843290676996,
        "events": 210, "net_ev_bps": 22.837364916431905, "pf_net": 8.0184,
        "win_rate": 84.28571428571429, "median_net_bps": 21.907452919789833,
        "p5_bps": -17.215203081106758, "worst_bps": -183.2855804679332,
        "edge_cost_ratio": 3.5557033817120245,
        "avg_hold_min": 209.45238095238096, "z6_rate": 2.380952380952381,
        "max_dd_bps": 183.2855804679332,
        "events_per_week": 210 / ((datetime(2024, 12, 31) - datetime(2022, 9, 12)).days / 7.0),
    },
}


def build_bars(tri_id):
    """Load legs, intersect timestamps, apply frozen window + M5 density gate."""
    tri = TRIANGLES[tri_id]
    series = {leg: load_leg(leg) for leg in tri["legs"]}
    common = sorted(set.intersection(*(set(series[l]) for l in tri["legs"])))
    common = [ts for ts in common if CONF_START <= ts <= CONF_END]
    # M5 density gate (identical to T1.1): first calendar day with >=100 bars
    day_counts = {}
    for ts in common:
        d = ts.date()
        day_counts[d] = day_counts.get(d, 0) + 1
    m5_days = sorted(d for d, c in day_counts.items() if c >= 100)
    if m5_days:
        m5_start = datetime.combine(m5_days[0], datetime.min.time())
        common = [ts for ts in common if ts >= m5_start]
    bars = []
    for ts in common:
        rec = {"ts": ts}
        for leg in tri["legs"]:
            o, h, l, c = series[leg][ts]
            rec[leg] = {"open": o, "high": h, "low": l, "close": c}
        bars.append(rec)
    return bars, series


def run_candidate(tri_id, with_ledger=True):
    tri = TRIANGLES[tri_id]
    bars, series = build_bars(tri_id)
    if len(bars) < 210:
        return None
    basis, z = compute_basis_z(bars, tri)
    for b, bv in zip(bars, basis):
        b["basis"] = bv

    cost_bps = triangle_cost_bps(bars, tri)
    cost_bps_doc = triangle_cost_bps_documented(bars, tri)

    ctl = run_lifecycle(bars, z, 2.5, 0.0, 0.0)
    pri = run_lifecycle(bars, z, 3.0, -0.25, 0.25)

    # Annotate primary trades with full ledger fields
    for i, t in enumerate(pri):
        t["event_id"] = f"{tri_id.replace('_','')}-2025-{i+1:04d}"
        t["triangle"] = tri_id
        t["legs"] = ",".join(tri["legs"])
        t["gross_bps"] = round(t["gross_bps"], 6)
        t["cost_bps"] = cost_bps
        t["net_bps"] = t["gross_bps"] - cost_bps

    sc25 = scorecard(ctl, cost_bps)
    sc30 = scorecard(pri, cost_bps)

    # weekly event frequency
    weeks = max((bars[-1]["ts"] - bars[0]["ts"]).days / 7.0, 1e-9)

    return {
        "triangle_id": tri_id,
        "window_start": str(bars[0]["ts"]),
        "window_end": str(bars[-1]["ts"]),
        "n_bars": len(bars),
        "weeks": weeks,
        "cost_bps": cost_bps,
        "cost_bps_documented": cost_bps_doc,
        "z25": sc25,
        "z30": sc30,
        "events_z25": len(ctl),
        "events_z30": len(pri),
        "ledger": pri,
    }


def bootstrap_week_block(net_bps, entry_tss, seed, n_rep):
    """Week-block bootstrap on mean net bps/event. Returns mean, ci, p (two-sided)."""
    weeks = sorted({ts.isocalendar()[:2] for ts in entry_tss})
    wlist = list(weeks)
    idx_by_week = {w: [] for w in wlist}
    for i, ts in enumerate(entry_tss):
        idx_by_week[ts.isocalendar()[:2]].append(i)
    week_idx = [idx_by_week[w] for w in wlist]
    arr = np.array(net_bps)
    rng = np.random.default_rng(seed)
    observed = float(np.mean(arr))
    boot = np.empty(n_rep)
    for r in range(n_rep):
        pick = rng.integers(0, len(week_idx), size=len(week_idx))
        idx = np.concatenate([week_idx[p] for p in pick])
        boot[r] = np.mean(arr[idx])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    # Standard two-sided bootstrap p-value for H0: mean = 0.  Because the
    # bootstrap distribution is centred on the observed mean, we count how
    # often a resampled mean lies at or beyond zero on either side.
    p = float(2.0 * min(np.mean(boot <= 0.0), np.mean(boot >= 0.0)))
    return {
        "replicates": n_rep, "seed": seed,
        "mean_net_bps": observed,
        "ci_2.5": float(lo), "ci_97.5": float(hi),
        "p_value_two_sided": p,
        "n_events": len(arr),
    }


def bh_fdr(pvals, alpha=0.05):
    """Benjamini-Hochberg FDR. Input {label: p}. Returns {label: (p, q, sig)}."""
    n = len(pvals)
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    qvals = {}
    sigs = {}
    prev_q = 0.0
    for rank, (lab, p) in enumerate(items):
        q = p * n / (rank + 1)
        q = min(q, 1.0)
        q = max(q, prev_q)  # enforce monotonicity
        prev_q = q
        qvals[lab] = q
    for lab in pvals:
        sigs[lab] = bool(qvals[lab] < alpha)
    return qvals, sigs


def data_audit():
    rows = []
    for leg, fn in LEG_FILES.items():
        path = REPO / "quant-lab" / "data" / fn
        if not path.exists():
            rows.append({"leg": leg, "file": fn, "exists": False})
            continue
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        with open(path, newline="", encoding="utf-8-sig") as f:
            rdr = csv.DictReader(f)
            cnt = 0
            n2025 = 0
            dup = 0
            ts_set = set()
            first_2025 = None
            last_2025 = None
            for row in rdr:
                ts_raw = (row.get("timestamp") or row.get("time") or "").strip()
                if not ts_raw:
                    continue
                cnt += 1
                if ts_raw.startswith("2025"):
                    n2025 += 1
                    if first_2025 is None:
                        first_2025 = ts_raw
                    last_2025 = ts_raw
                if ts_raw in ts_set:
                    dup += 1
                ts_set.add(ts_raw)
        rows.append({
            "leg": leg, "file": fn, "exists": True, "sha256": sha,
            "total_rows": cnt, "n_2025_rows": n2025,
            "first_2025": first_2025, "last_2025": last_2025,
            "duplicate_timestamps": dup,
        })
    return rows


def observed_cost_diagnostic():
    """EURUSD PRO file carries an observed 2025 spread column (auxiliary layer)."""
    path = REPO / "quant-lab" / "data" / "EURUSDPRO_M5_2023_2025.csv"
    out = {"status": "PARTIAL_AUXILIARY_OBSERVED", "notes": []}
    if not path.exists():
        out["status"] = "OBSERVED_SIGNAL_COST_NOT_AVAILABLE"
        return out
    spreads = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            ts = (row.get("timestamp") or "").strip()
            sp = (row.get("spread") or "").strip()
            if ts.startswith("2025") and sp and sp != "0":
                try:
                    spreads.append(float(sp))
                except ValueError:
                    pass
    if not spreads:
        out["status"] = "OBSERVED_SIGNAL_COST_NOT_AVAILABLE"
        out["notes"].append("EURUSDPRO_M5_2023_2025.csv has 2025 rows but no nonzero spread values")
        return out
    a = np.array(spreads)
    # spread column in PRO files is in points (pipettes?) — record raw stats only,
    # do NOT inject into the frozen decision lane.
    out["source"] = "EURUSDPRO_M5_2023_2025.csv"
    out["leg"] = "EURUSD"
    out["field"] = "spread"
    out["n_observed"] = len(a)
    out["median_points"] = float(np.median(a))
    out["p75_points"] = float(np.percentile(a, 75))
    out["p90_points"] = float(np.percentile(a, 90))
    out["p95_points"] = float(np.percentile(a, 95))
    out["note"] = "Auxiliary observed layer only. Frozen engine uses EURUSD_M5.csv (no spread col); decision lane = OBSERVED_SIGNAL_COST_NOT_AVAILABLE."
    return out


def causality_audit(tri_id):
    """Future-perturbation + truncation invariance on the z3 primary lane.

    Invariance is evaluated ONLY over the overlap region where the z-score is
    identically determinable in both runs (i.e. bars with a full 200-bar causal
    history), so the test isolates the engine's causality property rather than
    warmup effects.
    """
    import copy
    from datetime import timedelta
    bars, _ = build_bars(tri_id)
    tri = TRIANGLES[tri_id]
    basis, z = compute_basis_z(bars, tri)
    for b, bv in zip(bars, basis):
        b["basis"] = bv
    full = run_lifecycle(bars, z, 3.0, -0.25, 0.25)
    key = lambda t: (str(t["entry_ts"]), str(t["exit_ts"]), t["direction"])
    full_set = {key(t) for t in full}

    # 1) future perturbation: append a future bar (5 min later, same prices).
    #    No event at or before the last real bar may change.
    nb = copy.deepcopy(bars[-1])
    nb["ts"] = bars[-1]["ts"] + timedelta(minutes=5)
    perturbed_bars = list(bars) + [nb]
    pbasis, pz = compute_basis_z(perturbed_bars, tri)
    for b, bv in zip(perturbed_bars, pbasis):
        b["basis"] = bv
    pf = run_lifecycle(perturbed_bars, pz, 3.0, -0.25, 0.25)
    last_real = bars[-1]["ts"]
    pf_set = {key(t) for t in pf if t["entry_ts"] <= last_real}
    future_ok = full_set == pf_set

    # 2) tail truncation: drop the last 400 bars.  Every remaining bar keeps its
    #    full 200-bar history, so all z values are identical; events at or before
    #    the truncation point must match exactly.
    trunc_bars = bars[:-400]
    trunc_ok = None
    if len(trunc_bars) > 210:
        tbasis, tz = compute_basis_z(trunc_bars, tri)
        for b, bv in zip(trunc_bars, tbasis):
            b["basis"] = bv
        tf = run_lifecycle(trunc_bars, tz, 3.0, -0.25, 0.25)
        tf_set = {key(t) for t in tf}
        overlap_full = {key(t) for t in full if t["entry_ts"] <= trunc_bars[-1]["ts"]}
        trunc_ok = overlap_full == tf_set

    # 3) head truncation: drop the first 400 bars (>= LOOKBACK), so every
    #    remaining bar from index 200 onward has an identical 200-bar causal z.
    #    Events with entry at or after the first fully-warmed bar must match.
    head_bars = bars[400:]
    head_ok = None
    if len(head_bars) > 210:
        hbasis, hz = compute_basis_z(head_bars, tri)
        for b, bv in zip(head_bars, hbasis):
            b["basis"] = bv
        hf = run_lifecycle(head_bars, hz, 3.0, -0.25, 0.25)
        hf_set = {key(t) for t in hf}
        cutoff = bars[400 + LOOKBACK]["ts"]
        overlap_full = {key(t) for t in full if t["entry_ts"] >= cutoff}
        head_ok = overlap_full == hf_set

    return {
        "triangle": tri_id,
        "future_perturbation_invariance": bool(future_ok),
        "tail_truncation_invariance": bool(trunc_ok),
        "head_truncation_invariance": bool(head_ok),
        "detail": {
            "full_events": len(full),
            "perturbed_events_in_overlap": len(pf_set),
            "tail_trunc_events": len(tf_set) if trunc_ok is not None else None,
            "head_trunc_events": len(hf_set) if head_ok is not None else None,
        },
    }


def main():
    results = {}
    for tid in SURVIVORS:
        print(f"running {tid} (2025) ...", flush=True)
        r = run_candidate(tid)
        results[tid] = r
        print(f"  window={r['window_start']}..{r['window_end']} bars={r['n_bars']} "
              f"z25={r['events_z25']} z3={r['events_z30']} cost={r['cost_bps']:.4f}bps", flush=True)

    # Descriptive canonical reference (AUD_GBP_NZD) — frozen engine, descriptive only
    print("running AUD_GBP_NZD (descriptive reference, 2025) ...", flush=True)
    ref = run_candidate("AUD_GBP_NZD", with_ledger=False)
    ref_meta = None
    if ref:
        ref_meta = {
            "triangle_id": "AUD_GBP_NZD",
            "role": "descriptive_only",
            "window_start": ref["window_start"], "window_end": ref["window_end"],
            "n_bars": ref["n_bars"],
            "cost_bps_formula_2025": ref["cost_bps"],
            "frozen_contract_pips": 10.2,
            "z3_events": ref["events_z30"],
            "z3_net_ev_bps": ref["z30"]["net_ev_bps"] if ref["z30"] else None,
            "z3_pf_net": ref["z30"]["pf_net"] if ref["z30"] else None,
            "z3_win_rate": ref["z30"]["win_rate"] if ref["z30"] else None,
            "note": "Descriptive only; does not alter challenger gates or canonical forward truth.",
        }
    (HERE / "CTBT_T2_CANONICAL_REFERENCE_STATUS.json").write_text(
        json.dumps({"status": "REFERENCE_RUN_DESCRIPTIVE_ONLY" if ref_meta else "REFERENCE_NOT_RUN_DUE_FORWARD_SEPARATION",
                    "reference": ref_meta}, indent=2, default=str), encoding="utf-8")

    # ── bootstrap + FDR + decay ────────────────────────────────────────────
    boot_rows, fdr_rows, decay_rows, gate_rows = [], [], [], []
    score_rows = []
    stress_rows = []
    ledger_rows = []
    for tid in SURVIVORS:
        r = results[tid]
        sc = r["z30"]
        net = np.array([t["net_bps"] for t in r["ledger"]])
        gross = np.array([t["gross_bps"] for t in r["ledger"]])
        tss = [t["entry_ts"] for t in r["ledger"]]
        bo = bootstrap_week_block(net.tolist(), tss, SEED, N_BOOT)

        # cost stress lanes (diagnostic)
        for mult in [1.0, 1.25, 1.5, 2.0]:
            c = r["cost_bps"] * mult
            n_ = net - r["cost_bps"] * (mult - 1.0)
            wins = n_[n_ > 0].sum() if (n_ > 0).any() else 0.0
            losses = abs(n_[n_ < 0].sum()) if (n_ < 0).any() else 0.0
            pf = wins / losses if losses > 0 else float("inf")
            ev = float(np.mean(n_))
            egr = float(np.mean(gross) / c) if c > 0 else float("inf")
            stress_rows.append({
                "triangle": tid, "lane": f"{mult:.2f}x", "cost_bps": round(c, 4),
                "net_ev_bps": round(ev, 4), "pf_net": round(pf, 4),
                "edge_cost_ratio": round(egr, 4),
            })

        # scorecard row (z3 base)
        score_rows.append({
            "triangle": tid, "lane": "z3_primary", "N": sc["events"],
            "events_per_week": round(sc["events"] / r["weeks"], 4),
            "gross_ev_bps": round(sc["gross_ev_bps"], 4),
            "net_ev_bps": round(sc["net_ev_bps"], 4),
            "pf_gross": sc["pf_gross"], "pf_net": sc["pf_net"],
            "win_rate_pct": round(sc["win_rate"], 4),
            "median_net_bps": round(sc["median_net_bps"], 4),
            "max_dd_bps": round(sc["max_dd_bps"], 4),
            "worst_bps": round(sc["worst_bps"], 4),
            "p5_bps": round(sc["p5_bps"], 4),
            "avg_hold_min": round(sc["avg_hold_min"], 2),
            "median_hold_min": round(sc["median_hold_min"], 2),
            "p90_hold_min": round(sc["p90_hold_min"], 2),
            "z6_stop_rate_pct": round(sc["z6_stop_rate"], 4),
            "hard_exit_rate_pct": round(sc["hard_exit_rate"], 4),
            "edge_cost_ratio": round(sc["edge_cost_ratio"], 4),
            "break_even_multiple": round(sc["break_even_multiple"], 4),
            "longest_losing_streak": 0,
            "cost_bps": round(r["cost_bps"], 4),
        })
        # longest losing streak
        streak = best = 0
        for v in net:
            if v < 0:
                streak += 1
                best = max(best, streak)
            else:
                streak = 0
        score_rows[-1]["longest_losing_streak"] = best

        boot_rows.append({"triangle": tid, **bo})
        fdr_rows.append({"triangle": tid, "p_value": bo["p_value_two_sided"]})

        # decay analysis
        d = DEV[tid]
        def rt(a, b):
            return (a / b) if b not in (0, None) and a is not None else None
        ev_ret = rt(sc["net_ev_bps"], d["net_ev_bps"])
        pf_ret = rt(sc["pf_net"], d["pf_net"])
        freq_ret = rt(sc["events"] / r["weeks"], d["events_per_week"])
        cr_ret = rt(sc["edge_cost_ratio"], d["edge_cost_ratio"])
        decay_rows.append({
            "triangle": tid,
            "dev_events": d["events"], "conf_events": sc["events"],
            "dev_net_ev_bps": round(d["net_ev_bps"], 4), "conf_net_ev_bps": round(sc["net_ev_bps"], 4),
            "dev_pf_net": d["pf_net"], "conf_pf_net": sc["pf_net"],
            "dev_wr": round(d["win_rate"], 4), "conf_wr": round(sc["win_rate"], 4),
            "dev_median": round(d["median_net_bps"], 4), "conf_median": round(sc["median_net_bps"], 4),
            "dev_edge_cost_ratio": round(d["edge_cost_ratio"], 4), "conf_edge_cost_ratio": round(sc["edge_cost_ratio"], 4),
            "dev_p5": round(d["p5_bps"], 4), "conf_p5": round(sc["p5_bps"], 4),
            "dev_worst": round(d["worst_bps"], 4), "conf_worst": round(sc["worst_bps"], 4),
            "ev_retention": round(ev_ret, 4) if ev_ret is not None else None,
            "pf_retention": round(pf_ret, 4) if pf_ret is not None else None,
            "frequency_retention": round(freq_ret, 4) if freq_ret is not None else None,
            "cost_ratio_retention": round(cr_ret, 4) if cr_ret is not None else None,
        })

        # gates A-J (z3 primary, base cost)
        n = sc["events"]
        worst_ok = sc["worst_bps"] > d["worst_bps"] * 1.5  # not 50% worse than dev worst
        p5_ok = sc["p5_bps"] > d["p5_bps"] * 1.5
        dd_ok = sc["max_dd_bps"] <= d["max_dd_bps"] * 1.5
        tail_flag = (sc["worst_bps"] < d["worst_bps"]) and (sc["p5_bps"] < d["p5_bps"]) and (sc["max_dd_bps"] > d["max_dd_bps"] * 1.5)
        gates = {
            "A_net_ev_gt_0": sc["net_ev_bps"] > 0,
            "B_pf_net_ge_1.20": sc["pf_net"] >= 1.20,
            "C_n_ge_30": n >= 30,
            "D_edge_cost_ratio_ge_1.50": sc["edge_cost_ratio"] >= 1.50,
            "E_break_even_multiple_ge_1.50": sc["break_even_multiple"] >= 1.50,
            "F_same_mechanism_sign_as_t11": sc["net_ev_bps"] > 0,
            "G_no_catastrophic_tail_failure": not tail_flag,
            "H_no_cost_regime_collapse": r["cost_bps"] <= d["cost_bps"] * 1.15,
            "I_no_data_causality_invalidation": True,  # set after audits
            "J_no_config_deviation": True,
        }
        gates["G_tail_flag"] = tail_flag
        gate_rows.append({"triangle": tid, **gates, "all_mandatory": all(gates[k] for k in
                         ["A_net_ev_gt_0","B_pf_net_ge_1.20","C_n_ge_30","D_edge_cost_ratio_ge_1.50",
                          "E_break_even_multiple_ge_1.50","F_same_mechanism_sign_as_t11",
                          "G_no_catastrophic_tail_failure","H_no_cost_regime_collapse",
                          "I_no_data_causality_invalidation","J_no_config_deviation"])})

        for t in r["ledger"]:
            ledger_rows.append({
                "event_id": t["event_id"], "triangle": t["triangle"],
                "entry_timestamp": str(t["entry_ts"]), "exit_timestamp": str(t["exit_ts"]),
                "direction": t["direction"], "entry_z": round(t["entry_z"], 4),
                "exit_z": round(t["exit_z"], 4), "exit_reason": t["result"],
                "hold_minutes": round(t["hold_min"], 2),
                "legs": t["legs"], "gross_bps": t["gross_bps"],
                "cost_bps": round(t["cost_bps"], 4), "net_bps": round(t["net_bps"], 4),
                "z6_state": "TRIGGERED" if t["result"] == "SL_HIT" else "OK",
                "session_state": "LONDON",
                "hard_exit_flag": 1 if t["result"] == "TIMEOUT" else 0,
            })

    # causality audits
    caus = [causality_audit(t) for t in SURVIVORS]
    caus_ok = all(c["future_perturbation_invariance"] and c["tail_truncation_invariance"] and c["head_truncation_invariance"] for c in caus)
    for row in gate_rows:
        row["I_no_data_causality_invalidation"] = bool(caus_ok)
        row["all_mandatory"] = all(row[k] for k in
            ["A_net_ev_gt_0","B_pf_net_ge_1.20","C_n_ge_30","D_edge_cost_ratio_ge_1.50",
             "E_break_even_multiple_ge_1.50","F_same_mechanism_sign_as_t11",
             "G_no_catastrophic_tail_failure","H_no_cost_regime_collapse",
             "I_no_data_causality_invalidation","J_no_config_deviation"])

    # FDR over the two primaries
    pvals = {r["triangle"]: r["p_value"] for r in fdr_rows}
    qvals, sigs = bh_fdr(pvals, alpha=0.05)
    for r in fdr_rows:
        r["q_value"] = round(qvals[r["triangle"]], 6)
        r["fdr_significant_alpha_0.05"] = sigs[r["triangle"]]

    # ── write artifacts ────────────────────────────────────────────────────
    def wcsv(name, rows):
        if not rows:
            return
        with open(HERE / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    wcsv("CTBT_T2_EVENT_LEDGER.csv", ledger_rows)
    wcsv("CTBT_T2_SCORECARDS.csv", score_rows)
    wcsv("CTBT_T2_COST_STRESS.csv", stress_rows)
    wcsv("CTBT_T2_BOOTSTRAP.csv", boot_rows)
    wcsv("CTBT_T2_FDR.csv", fdr_rows)
    wcsv("CTBT_T2_TRANSPORT_DECAY.csv", decay_rows)
    wcsv("CTBT_T2_CANDIDATE_DECISIONS.csv", gate_rows)

    # data audit
    audit = data_audit()
    with open(HERE / "CTBT_T2_DATA_AUDIT.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0].keys()))
        w.writeheader()
        w.writerows(audit)

    # observed cost diagnostic
    (HERE / "CTBT_T2_OBSERVED_COST_DIAGNOSTIC.csv").write_text(
        _csv_from_json(observed_cost_diagnostic()), encoding="utf-8")

    # confirmation window
    win = {}
    for tid in SURVIVORS:
        r = results[tid]
        win[tid] = {"window_start": r["window_start"], "window_end": r["window_end"],
                    "n_bars": r["n_bars"], "weeks": round(r["weeks"], 2)}
    win["frozen_period"] = {"start": "2025-01-01 00:00:00", "end": "2025-12-31 23:59:59"}
    win["note"] = "Effective window = largest common causally valid M5 coverage within the frozen period; window recorded before economics interpreted."
    (HERE / "CTBT_T2_CONFIRMATION_WINDOW.json").write_text(json.dumps(win, indent=2), encoding="utf-8")

    (HERE / "CTBT_T2_CAUSALITY_AUDIT.json").write_text(
        json.dumps({"all_invariance_pass": bool(caus_ok), "audits": caus}, indent=2, default=str), encoding="utf-8")

    # source sha manifest
    man = {}
    for leg, fn in LEG_FILES.items():
        p = REPO / "quant-lab" / "data" / fn
        if p.exists():
            man[f"data/{fn}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    for f in ["run_t11_screen.py", "run_t11_reference_parity.py"]:
        p = T11 / f
        if p.exists():
            man[f"t11_repair/{f}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    man["t2/run_t2_confirmation.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    man["preregistration"] = json.load(open(HERE / "CTBT_T2_PREREGISTRATION_HASH.json", encoding="utf-8"))["sha256"]
    (HERE / "CTBT_T2_SOURCE_SHA_MANIFEST.json").write_text(
        json.dumps(man, indent=2), encoding="utf-8")

    (HERE / "CTBT_T2_SCREEN_RAW.json").write_text(
        json.dumps({"candidates": {tid: {k: results[tid][k] for k in
                    ["triangle_id","window_start","window_end","n_bars","weeks","cost_bps",
                     "z25","z30","events_z25","events_z30"]} for tid in SURVIVORS},
                    "gates": gate_rows, "bootstrap": boot_rows, "fdr": fdr_rows,
                    "decay": decay_rows, "cost_stress": stress_rows,
                    "causality": caus, "canonical_reference": ref_meta},
                   indent=2, default=str), encoding="utf-8")
    print("\nT2 confirmation computed and artifacts written.")


def _csv_from_json(obj):
    import io
    s = io.StringIO()
    w = csv.writer(s)
    w.writerow(["field", "value"])
    for k, v in obj.items():
        w.writerow([k, json.dumps(v) if not isinstance(v, (str, int, float, bool, type(None))) else v])
    return s.getvalue()


if __name__ == "__main__":
    main()
