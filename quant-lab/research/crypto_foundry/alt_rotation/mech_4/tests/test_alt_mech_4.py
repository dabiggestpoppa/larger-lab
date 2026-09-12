#!/usr/bin/env python
"""Integrity tests for CRYPTO-ALT-MECH-4 artifacts and analysis functions.

Terrain/mechanism research only. These tests verify PIT truth, the canonical
event reconciliation (126 entries / 125 exits), the flagship MECH-2/3
reconciliation, the gate/path-memory/duration outputs, and the addendum
(30-40) artifacts.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

REQUIRED_ARTIFACTS = [
    "01_PREREGISTRATION.md", "02_DATA_TRUTH.md", "02_DATA_TRUTH.json",
    "03_RELEASE_EVENT_RECONCILIATION.csv", "04_RELEASE_EVENT_LEDGER.parquet",
    "05_RELEASE_SEQUENCE_MAP.csv", "06_ESCAPE_VS_SNAPBACK.csv",
    "07_RELEASE_DESTINATION_GATE.csv", "08_PROPAGATION_GATE.csv",
    "09_PROPAGATION_DEPTH.csv", "10_CURRENT_STATE_BASELINE.csv",
    "11_PATH_MEMORY_INCREMENT.csv", "12_DURATION_SEMIMARKOV_AUDIT.csv",
    "13_P1_STALL_RELEASE_AUDIT.csv", "14_NATIVE_ACTIVATION_AUDIT.csv",
    "15_PIVOT_PLATEAU_OVERLAP.csv", "16_RELEASE_TRIGGER_VS_ROUTE_GATE.csv",
    "17_VOLATILITY_ROUTING_TEMPERATURE.csv", "18_STATE_ROUTING_GRAPH.csv",
    "19_MECH2_MECH3_FLAGSHIP_RECONCILIATION.json",
    "20_INFORMATION_GAIN_AND_PLATEAU.csv", "21_OBSERVATION_GAP_PRIORITY.md",
    "22_SUBPERIOD_STABILITY.csv", "23_NULL_AND_FAILED_RESULTS.csv",
    "24_CAUSALITY_LADDER.csv", "25_NEW_NODE_MERGE_DISSOLVE.csv",
    "26_FORMALISM_READINESS.md", "27_TEST_COUNT_RECONCILIATION.md",
    "28_MECH4_SUMMARY.md", "29_DECISION.md",
    "30_P1_MICRO_PERTURBATION_ATLAS.csv", "31_TEMPORAL_DELIVERY_LATTICE.csv",
    "32_EVENT_DURATION_DISTRIBUTIONS.csv", "33_FIRST_MOVE_TRUE_DELIVERY.csv",
    "34_ACCUMULATION_LIKE_FINGERPRINT.csv", "35_SECOND_ORDER_ROUTE_MAP.csv",
    "36_ROUTE_LATENCY_MATRIX.csv", "37_PROPAGATION_TERMINATION_ANATOMY.csv",
    "38_POST_TERMINATION_ROUTING.csv", "39_BIFURCATION_STATE_SPACE_AUDIT.csv",
    "40_VOLATILITY_LIFECYCLE_ROLE.csv",
]


# ---------------------------------------------------------------------------
# helper: read the daily routing-state column from the ledger
# ---------------------------------------------------------------------------

def _ledger():
    return pd.read_parquet(ROOT / "04_RELEASE_EVENT_LEDGER.parquet")


# ---------------------------------------------------------------------------
# Artifact presence + scope guards
# ---------------------------------------------------------------------------

def test_required_artifacts_present():
    for name in REQUIRED_ARTIFACTS:
        assert (ROOT / name).exists(), f"missing artifact {name}"


def test_no_strategy_artifacts():
    """No PnL / strategy / alpha-score artifacts are produced."""
    for cand in ROOT.iterdir():
        n = cand.name.lower()
        if cand.is_file():
            assert "pnl" not in n and "sampleroute" not in n, f"unexpected {cand.name}"
            assert not (cand.suffix in (".csv",) and "alpha" in n)


def test_truth_lock_pass():
    tl = json.load(open(ROOT / "02_DATA_TRUTH.json"))
    assert tl["all_pass"] is True
    assert tl["checks"]["pit_rows_1098000"] is True
    assert tl["checks"]["included_dates_2196"] is True


def test_event_reconciliation_counts():
    df = pd.read_csv(ROOT / "03_RELEASE_EVENT_RECONCILIATION.csv")
    ent = df[df.event_type == "ENTRY"].iloc[0]
    ext = df[df.event_type == "EXIT"].iloc[0]
    assert ent.recount == 126
    assert ext.recount == 125
    assert ent.match == ent.canonical_count          # full with MECH-3
    assert ext.match == ext.canonical_count


def test_ledger_destination_taxonomy():
    ld = _ledger()
    dest_counts = ld.first_destination.value_counts().to_dict()
    assert sum(dest_counts.values()) == 125
    # canonical MECH-3 breakdown reproduced
    assert dest_counts["BTC_CONCENTRATION"] == 52
    assert dest_counts["MIXED_NO_CLEAR_ROUTE"] == 44
    assert dest_counts["BROAD_RISK_EXPANSION"] == 18
    alt = sum(v for k, v in dest_counts.items() if k.endswith("ROTATION") or
              k in ("ETH_BROADENING",))
    assert alt <= 12  # alt family stays tiny (n~9)


def test_ledger_no_future_leakage_fields():
    """Ledger carries only PIT observables + forward state-transition labels."""
    ld = _ledger()
    for c in ld.columns:
        assert not c.startswith("obs_future"), f"leak column {c}"


# ---------------------------------------------------------------------------
# Flagship MECH-2 / MECH-3 reconciliation
# ---------------------------------------------------------------------------

def test_flagship_reconciliation_reproduces_numbers():
    r = json.load(open(ROOT / "19_MECH2_MECH3_FLAGSHIP_RECONCILIATION.json"))
    assert r["m2_best_lag"] == -7
    assert abs(r["m2_best_corr"] - (-0.3044)) < 1e-3
    assert r["m3_best_lag"] == 1
    assert abs(r["m3_best_corr"] - 0.1333) < 1e-3
    # conditional values reproduce under both grids
    cond = {c["state"]: c["corr"] for c in r["conditional"]}
    assert cond["BTC_DOWN"] > 0.5
    assert cond["VOL_HIGH"] > 0.5
    assert r["classification"] != "BUG"


# ---------------------------------------------------------------------------
# Hierarchical gates (B)
# ---------------------------------------------------------------------------

def test_gates_delta_logloss_sane():
    g = pd.read_csv(ROOT / "06_ESCAPE_VS_SNAPBACK.csv")
    g3 = g[g.gate == "G3_PROPAGATION_VS_NOT"].iloc[0]
    assert g3.delta_logloss > 0.05          # reproducible gate exists
    assert g3.auc > 0.6                     # fixed AUC (not 0)
    g1 = g[g.gate == "G1_ESCAPE_VS_SNAPBACK"].iloc[0]
    assert g1.auc < 0.8                      # escape vs snapback not nearly perfect


def test_depth_exploratory_only():
    g = pd.read_csv(ROOT / "06_ESCAPE_VS_SNAPBACK.csv")
    g4 = g[g.gate == "G4_BROAD_RISK_VS_ALT_DEPTH"].iloc[0]
    assert g4.n <= 30
    assert g4.classification.startswith("EXPLORATORY")


# ---------------------------------------------------------------------------
# Path memory (C)
# ---------------------------------------------------------------------------

def test_path_memory_descriptive_not_predictive():
    pm = pd.read_csv(ROOT / "11_PATH_MEMORY_INCREMENT.csv")
    assert pm.classification.iloc[0] == "HYSTERESIS_DESCRIPTIVE"
    assert pm.path_perm_p.iloc[0] > 0.05
    assert pm.delta_logloss_M3_vs_M0.iloc[0] <= 0.0   # no held-out gain


def test_nested_models_monotone_no_gain():
    m = pd.read_csv(ROOT / "10_CURRENT_STATE_BASELINE.csv")
    logloss = m.set_index("model").logloss
    # adding path info never improves held-out logloss beyond M0
    assert logloss["M1"] >= logloss["M0"]
    assert logloss["M3"] >= logloss["M0"]


# ---------------------------------------------------------------------------
# Duration / semi-Markov (D)
# ---------------------------------------------------------------------------

def test_escape_probability_declines_with_age():
    t1 = pd.read_csv(ROOT / "12b_ESCAPE_BY_AGE.csv")
    # numeric ordering: first bin is youngest
    t1["_lo"] = t1.age_bin.str.split("-", expand=True)[0].astype(int)
    t1 = t1.sort_values("_lo")
    young = t1.sort_values("_lo").iloc[0]
    oldest = t1.sort_values("_lo", ascending=False)\
        .loc[lambda d: d.age_bin.str.startswith("15")].iloc[0]
    assert young.p_exit_within7d > 0.7
    assert oldest.p_exit_within7d < 0.4
    rho = np.corrcoef(np.arange(len(t1)), t1.p_exit_within7d)[0, 1]
    assert rho < -0.5


def test_reentry_measured_within_window():
    t3 = pd.read_csv(ROOT / "12c_REENTRY_BY_AGE.csv")
    assert "reentry7d_share" in t3.columns
    assert t3.reentry7d_share.min() >= 0.0 and t3.reentry7d_share.max() <= 1.0


# ---------------------------------------------------------------------------
# Activation / stall (E)
# ---------------------------------------------------------------------------

def test_p1_episode_count():
    d = pd.read_csv(ROOT / "13_P1_STALL_RELEASE_AUDIT.csv")
    assert len(d) == 797                     # MECH-3 canonical count reproduced


def test_activation_first_not_robust():
    a = pd.read_csv(ROOT / "14_NATIVE_ACTIVATION_AUDIT.csv")
    # pre-vs-control not significant (>=0.05) OR activation does not add info
    assert a.activation_pre_vs_ctrl_p.iloc[0] >= 0.05 or \
        a.delta_logloss.iloc[0] <= 0.0


# ---------------------------------------------------------------------------
# Trigger vs route (F)
# ---------------------------------------------------------------------------

def test_trigger_route_separation():
    f = pd.read_csv(ROOT / "16_RELEASE_TRIGGER_VS_ROUTE_GATE.csv")
    init = set(f[f.target == "INITIATION_G1"].feature)
    route = set(f[f.target == "ROUTE_G3"].feature)
    assert len(init) > 0 and len(route) > 0
    # breadth30 must be the dominant route (G3) feature and significant
    g3 = f[f.target == "ROUTE_G3"]
    brd = g3[g3.feature == "breadth30"]
    assert float(brd["coef"].iloc[0]) == max(g3.coef.abs())
    assert bool(brd["significant"].iloc[0]) is True


# ---------------------------------------------------------------------------
# Routing graph (H)
# ---------------------------------------------------------------------------

def test_routing_graph_present():
    h = pd.read_csv(ROOT / "18_STATE_ROUTING_GRAPH.csv")
    assert len(h) > 0
    assert "edge" in h.columns


def test_routing_graph_not_overclaimed():
    v = json.load(open(ROOT / "_verdicts.json"))
    # reconfiguration on aggregate threshold was NOT earned
    assert v["H_reconfig"] is False
    assert v["H_new"] >= 50       # but new edges DO appear by state (partial)


# ---------------------------------------------------------------------------
# Addendum artifacts (30-40)
# ---------------------------------------------------------------------------

def test_second_order_route_count():
    m = pd.read_csv(ROOT / "36_ROUTE_LATENCY_MATRIX.csv")
    assert len(m) > 0


def test_first_move_classification_balances():
    d = pd.read_csv(ROOT / "33_FIRST_MOVE_TRUE_DELIVERY.csv")
    assert len(d) == 125
    assert set(d.classification) <= {"IMMEDIATE_DELIVERY", "RETEST_RELOAD",
                                      "FAILED_IGNITION", "FULL_FAILURE"}
    # multi-stage (RETEST_RELOAD) present and non-trivial
    assert (d.classification == "RETEST_RELOAD").sum() > 0


def test_accumulation_like_discriminates():
    d = pd.read_csv(ROOT / "34_ACCUMULATION_LIKE_FINGERPRINT.csv")
    assert "absorption_like_score" in d.columns
    hi = d[d.absorption_like_score >= 0.6]
    lo = d[d.absorption_like_score < 0.6]
    assert len(hi) >= 10 and len(lo) >= 10
    assert hi.stable_outcome.mean() > lo.stable_outcome.mean()


def test_bifurcation_audit_sane():
    v = json.load(open(ROOT / "_verdicts.json"))
    assert "Z_39_sharpest_jump" in v
    assert v["Z_39_sharpest_jump"] >= 0.0 and v["Z_39_sharpest_jump"] <= 1.0


def test_volatility_lifecycle_present():
    v = json.load(open(ROOT / "_verdicts.json"))
    stages = {x["stage"] for x in v["Z_40_lifecycle"]}
    assert "STALL_P1" in stages and "PROPAGATION_BROAD_RISK_EXPANSION" in stages


# ---------------------------------------------------------------------------
# Decision doc guards
# ---------------------------------------------------------------------------

def test_decision_doc_guards():
    txt = open(ROOT / "29_DECISION.md", encoding="utf-8").read().upper()
    assert "NO STRATEGY" in txt or "NO PNL" in txt or "TERRAIN" in txt
    assert "HUMAN_REVIEW_REQUIRED" in txt or "NO PRODUCTION" in txt


def test_summary_and_decision_exist():
    assert (ROOT / "28_MECH4_SUMMARY.md").exists()
    assert (ROOT / "29_DECISION.md").exists()


STATE_FEATURES = ["btc_ret30", "btc_ret7", "top3_share", "top3_share_chg7",
                  "breadth30", "disp30", "sc_chg30", "eth_rel30", "vol_med",
                  "chain_tvl_med_chg7"]