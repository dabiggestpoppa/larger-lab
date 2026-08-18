"""Pre-economic activation census, signal funnel, and feature
distributions. Descriptive statistics only — no PnL."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _run_lengths(mask: np.ndarray) -> list:
    """Lengths of consecutive True runs."""
    lengths = []
    run = 0
    for v in mask:
        if v:
            run += 1
        elif run:
            lengths.append(run)
            run = 0
    if run:
        lengths.append(run)
    return lengths


def activation_census(ledger: pd.DataFrame) -> pd.DataFrame:
    n = len(ledger)
    rows = []

    k1_valid = ledger["K1_reason"].isin(["ACTIVE", "INACTIVE", "VALID_SAME_MODE_DELTAPHI_ZERO"])
    k1_active = ledger["K1_reason"] == "ACTIVE"
    k2_active = ledger["w1_active"]
    k3_hole = ledger["topology_frozen"] == "NO_HOLE"
    k3_fragile = ledger["topology_frozen"] == "FRAGILE"
    k3_persistent = ledger["topology_frozen"] == "PERSISTENT"
    k3_ols_invalid = ~ledger["K3_OLS_VALID"].astype(bool)
    k3_active = ledger["w2"].abs() > 0
    k4_cluster = ledger["w_total"].abs() >= 0.05

    for kernel, active in [("K1", k1_active), ("K2", k2_active), ("K3", k3_active),
                           ("K4", k4_cluster)]:
        runs = _run_lengths(active.to_numpy())
        rows.append({
            "kernel": kernel,
            "valid_observations": int(n),
            "activation_count": int(active.sum()),
            "activation_rate": round(float(active.mean()), 6),
            "mean_duration_h": round(float(np.mean(runs)), 3) if runs else 0.0,
            "median_duration_h": round(float(np.median(runs)), 3) if runs else 0.0,
            "overlap_with_K1": round(float((k1_active & active).mean()), 6),
            "overlap_with_K2": round(float((k2_active & active).mean()), 6),
            "overlap_with_K3": round(float((k3_active & active).mean()), 6),
            "overlap_with_K4": round(float((k4_cluster & active).mean()), 6),
            "stale_market_fraction": round(float(ledger["stale_W_gt2h"].mean()), 6),
        })

    census = pd.DataFrame(rows)
    census["session_distribution"] = [
        _session_dist(ledger, k1_active),
        _session_dist(ledger, k2_active),
        _session_dist(ledger, k3_active),
        _session_dist(ledger, k4_cluster),
    ]
    census["year_distribution"] = [
        _year_dist(ledger, k1_active),
        _year_dist(ledger, k2_active),
        _year_dist(ledger, k3_active),
        _year_dist(ledger, k4_cluster),
    ]
    return census


def _session_dist(ledger: pd.DataFrame, mask: pd.Series) -> str:
    hours = ledger.loc[mask, "canonical_ny"].dt.hour
    return hours.value_counts().sort_index().to_dict() if len(hours) else {}


def _year_dist(ledger: pd.DataFrame, mask: pd.Series) -> str:
    years = ledger.loc[mask, "canonical_ny"].dt.year
    return years.value_counts().sort_index().to_dict() if len(years) else {}


def signal_funnel(ledger: pd.DataFrame) -> pd.DataFrame:
    n = len(ledger)
    stages = []

    def stage(name, mask, note=""):
        stages.append({
            "stage": name,
            "count": int(mask.sum()),
            "fraction_of_total": round(float(mask.mean()), 6),
            "pre_economic_note": note,
        })

    stage("total_h1_slots", pd.Series(np.ones(n, dtype=bool), index=ledger.index))
    valid_sync = ledger[["W.observed", "E.observed", "C.observed", "I.observed"]].any(axis=1)
    stage("synchronized_valid_slots", valid_sync, ">=1 observed bar across assets")
    k4_cluster = ledger["w_total"].abs() >= 0.05
    stage("K4_cluster_active", k4_cluster)
    k1_ok = ledger["K1_reason"].isin(["ACTIVE", "INACTIVE", "VALID_SAME_MODE_DELTAPHI_ZERO"])
    stage("K1_valid", k1_ok)
    stage("K2_active", ledger["w1_active"])
    k3_state = ledger["topology_frozen"].isin(["PERSISTENT", "FRAGILE"])
    stage("K3_topology_nonzero", k3_state)
    nonzero_target = (ledger[["w_base_0", "w_base_1", "w_base_2"]].abs().sum(axis=1) > 0)
    stage("nonzero_target", nonzero_target)
    gross = (ledger[["w_cap_0", "w_cap_1", "w_cap_2"]].abs().sum(axis=1) > 0)
    scaled = (ledger[["w_base_0", "w_base_1", "w_base_2"]].abs().sum(axis=1) > 1.0 + 1e-12)
    stage("gross_cap_applied", scaled & gross, "sum(abs(W_base)) > 1 scaled to 1.0")
    stage("fade_adjusted", ledger["fade_phase"] > 0)
    stage("DD_adjusted", pd.Series(np.zeros(n, dtype=bool), index=ledger.index),
          "NOT EVALUATED PRE-ECONOMIC (fixture-only overlay; requires NAV)")
    stage("leg_stop_adjusted", pd.Series(np.zeros(n, dtype=bool), index=ledger.index),
          "NOT EVALUATED PRE-ECONOMIC (fixture-only overlay; requires marked equity)")
    executable = (ledger[["w_fade_0", "w_fade_1", "w_fade_2"]].abs().sum(axis=1) > 0)
    stage("executable_target", executable, "pre-economic: W_fade carried through DD/leg-stop")
    return pd.DataFrame(stages)


def feature_distributions(ledger: pd.DataFrame) -> pd.DataFrame:
    features = ["r_W", "r_E", "r_C", "r_I", "r_EC", "sigma_W", "gamma", "gamma_bar",
                "accel", "delta_phi", "D_EC", "D_WE", "D_WC", "epsilon", "alpha2",
                "alpha_D", "RV6_EC", "w1", "w2", "w3", "w_total"]
    rows = []
    for f in features:
        if f not in ledger.columns:
            continue
        s = pd.to_numeric(ledger[f], errors="coerce").dropna()
        if len(s) == 0:
            continue
        q = s.quantile([0.0, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1.0])
        rows.append({"feature": f, "n": int(len(s)), "mean": float(s.mean()),
                     "std": float(s.std()), **{f"q{int(k * 100):02d}": float(v)
                                               for k, v in q.items()}})
    return pd.DataFrame(rows)
