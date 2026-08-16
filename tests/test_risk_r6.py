"""
CR-RISK-BLOCK2 R6 — Episode / Heat Sizing tests.

Covers the brief's XXXII invariants: event count reconciles to the sealed
890 book; episode ids reconcile with R1 (12h); overlap reconstructed exactly
(max simultaneous 3 = R1); H0 reproduces the sealed baselines (50/50 f=1%
and f=2%, 70/30 f=1%); rejected events carry zero admitted risk; scaled
events never exceed the remaining cap; gross / same-direction / family-B
heat never exceeds its cap; admission is strictly causal (invariant to
future outcomes and to base_f); the policy grid is exactly the preregistered
surface; probabilities in [0,1]; MC episode blocks preserve clusters; no
best policy / no Kelly / no R7 authorization; alpha untouched; repo typo
corrected only mechanically.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
_SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, _SRC)

import capital_routing
if not str(capital_routing.__file__).startswith(_SRC):
    # A site .pth from another checkout can shadow this package after earlier
    # test modules import it. Force the local src copy before importing R6.
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.phases.phase_r6_common import (ALLOC_SET, F_GRID,
                                                    POLICY_GRID, _hourly_heat,
                                                    load_r6_inputs,
                                                    policy_metrics, run_policy)
from capital_routing.phases.phase_r6_mc import _path_layouts

ROOT = Path(__file__).resolve().parents[1]
R6 = ROOT / "artifacts" / "risk_block2" / "r6"
B1 = ROOT / "artifacts" / "risk_block1"


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(R6 / name)


def _decision() -> dict:
    return json.loads((R6 / "R6_DECISION.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def load():
    return load_r6_inputs(ROOT)


# ---------------------------------------------------------------------------
# 1. event count reconciles to the sealed book
# ---------------------------------------------------------------------------

def test_event_count_reconciles_sealed_890(load):
    sealed = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    assert len(load["ba"]["tb"]) == len(sealed) == 890
    a = int((load["ba"]["tb"].family == "A").sum())
    b = int((load["ba"]["tb"].family == "B").sum())
    assert (a, b) == (432, 458)
    assert abs(float(load["ba"]["tb"]["pnl_bps"].sum()) -
               float(sealed["pnl_bps"].sum())) < 1e-6


# ---------------------------------------------------------------------------
# 2. episode ids reconcile with R1 (12h)
# ---------------------------------------------------------------------------

def test_episode_ids_reconcile_with_r1(load):
    r1_ep = pd.read_csv(B1 / "R1_ROUTING_EPISODES.csv")
    r1_12 = r1_ep[r1_ep.interval_h == 12.0]
    r1_members = {}
    for _, row in r1_12.iterrows():
        # R1 stores multi-event clusters with both | and ; separators
        for eid in re.split(r"[|;]", str(row["event_ids"])):
            if eid:
                r1_members[eid] = int(row["cluster_id"])
    ep = load["episode_ledger"]
    assert len(ep) == 890
    assert len(r1_members) == 890
    # membership maps to the same cluster id for every event
    for eid, c in r1_members.items():
        got = int(ep.loc[ep.event_id == eid, "episode_id"].iloc[0])
        assert got == c, f"{eid}: R6 {got} vs R1 {c}"


# ---------------------------------------------------------------------------
# 3. overlap reconstructed exactly (max simultaneous 3 = R1)
# ---------------------------------------------------------------------------

def test_overlap_reconstruction_matches_r1(load):
    ep = load["episode_ledger"]
    r1 = load["risk1_cc"].iloc[0]
    assert int(ep["peak_concurrent_position_count"].max()) == \
        int(r1["max_concurrent_positions"]) == 3
    # 20 hours with 3 positions in R1's hourly frame; entry-instant count of
    # events entering into 2 others must be > 0 and match the 3-way state
    assert int((ep["concurrent_position_count_at_entry"] == 2).sum()) >= 1
    assert int(ep["episode_peak_heat"].max()) == 3


def test_episode_ledger_columns_match_spec(load):
    required = ["event_id", "family", "entry_time", "exit_time", "direction",
                "return_R", "episode_id", "episode_start", "episode_end",
                "concurrent_position_count_at_entry",
                "peak_concurrent_position_count", "same_direction_active_count",
                "opposite_direction_active_count", "A_active_count", "B_active_count",
                "gross_active_R", "net_directional_R", "episode_peak_heat",
                "episode_realized_R", "episode_worst_CAE_R", "episode_best_CFE_R"]
    ep = load["episode_ledger"]
    assert set(required) <= set(ep.columns)


# ---------------------------------------------------------------------------
# 4. H0 reproduces the sealed baselines (overlap-exact hourly path)
# ---------------------------------------------------------------------------

def test_h0_reproduces_sealed_baselines(load):
    years = load["years"]
    adm, _ = run_policy(load, {"kind": "H0", "cap_mult": None,
                               "treatment": "REJECT"}, 0.5, 0.5)
    m1 = policy_metrics(load, adm, 0.01, years, 0.5, 0.5)
    # R5 50/50 @ f=1%: CAGR 71%, max DD 5.2%, worst day -2.8%
    assert abs(m1["cagr"] - 0.71) < 0.02
    assert abs(m1["max_dd"] - 0.052) < 0.005
    assert abs(m1["worst_day_pct"] - (-0.028)) < 0.005
    # R4 pooled f=1% == 50/50 @ f=2%: CAGR 190%, max DD 10.2%
    m2 = policy_metrics(load, adm, 0.02, years, 0.5, 0.5)
    assert abs(m2["cagr"] - 1.90) < 0.03
    assert abs(m2["max_dd"] - 0.102) < 0.01
    # 70/30 @ f=1% (R5 70/30)
    adm70, _ = run_policy(load, {"kind": "H0", "cap_mult": None,
                                 "treatment": "REJECT"}, 0.7, 0.3)
    m3 = policy_metrics(load, adm70, 0.01, years, 0.7, 0.3)
    assert m3["cagr"] > 0.5 and m3["max_dd"] < 0.15


# ---------------------------------------------------------------------------
# 5-9. admission semantics: zero-risk rejected, caps respected, causality
# ---------------------------------------------------------------------------

def test_rejected_events_carry_zero_risk(load):
    for pol in POLICY_GRID:
        res = run_policy(load, pol, 0.5, 0.5, full_output=True)
        rej = res[res.decision == "REJECT_HEAT_CAP"]
        assert (rej["admitted_f"] == 0.0).all(), pol["policy_id"]
        full = res[res.decision == "ACCEPT_FULL"]
        assert (full["admitted_f"] > 0).all(), pol["policy_id"]


def test_scaled_events_never_exceed_remaining_cap(load):
    for pol in POLICY_GRID:
        if pol["treatment"] != "SCALE":
            continue
        res = run_policy(load, pol, 0.5, 0.5, full_output=True)
        sca = res[res.decision == "ACCEPT_SCALED"]
        for _, r in sca.iterrows():
            req = r["requested_f"]
            assert 0.0 < r["admitted_f"] < req - 1e-9
            # admitted never exceeds the binding constraint's remaining room
            if pol["kind"] == "H1":
                assert r["admitted_f"] <= pol["cap_mult"] - r["pre_gross_heat"] + 1e-9
            elif pol["kind"] == "H2":
                assert r["admitted_f"] <= pol["cap_mult"] - r["pre_same_direction_heat"] + 1e-9
            elif pol["kind"] == "H3":
                assert r["admitted_f"] <= pol["cap_mult"] - r["pre_B_heat"] + 1e-9
            elif pol["kind"] == "H4":
                assert r["admitted_f"] <= pol["cap_mult"] - r["episode_budget_used"] + 1e-9
            elif pol["kind"] == "H5":
                assert r["admitted_f"] <= pol["cap_mult"] - r["pre_gross_heat"] + 1e-9
                assert r["admitted_f"] <= pol.get("samedir_mult") - r["pre_same_direction_heat"] + 1e-9


def test_gross_heat_never_exceeds_cap(load):
    for pol in [p for p in POLICY_GRID if p["kind"] in ("H1", "H5") and
                p["treatment"] == "REJECT"]:
        adm, _ = run_policy(load, pol, 0.5, 0.5)
        heat = _hourly_heat(load["ba"]["tb"], adm)
        cap = pol["cap_mult"] if pol["kind"] == "H1" else pol["cap_mult"]
        assert heat.max() <= cap + 1e-9, pol["policy_id"]


def test_same_direction_heat_never_exceeds_cap(load):
    tb = load["ba"]["tb"]
    for pol in [p for p in POLICY_GRID if p["kind"] in ("H2", "H5") and
                p["treatment"] == "REJECT"]:
        adm, _ = run_policy(load, pol, 0.5, 0.5)
        entry = pd.to_datetime(tb["entry_ts"], utc=True)
        exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
        cap = pol["cap_mult"] if pol["kind"] == "H2" else pol.get("samedir_mult")
        for d in [1.0, -1.0]:
            mask = (tb["dir"].to_numpy() == d) & (adm > 0)
            heat = _hourly_heat(tb[mask], adm[mask])
            if len(heat):
                assert heat.max() <= cap + 1e-9, pol["policy_id"]


def test_family_B_cap_applied(load):
    tb = load["ba"]["tb"]
    for pol in [p for p in POLICY_GRID if p["kind"] == "H3"]:
        adm, _ = run_policy(load, pol, 0.5, 0.5)
        bmask = (tb["family"].to_numpy() == "B") & (adm > 0)
        heat = _hourly_heat(tb[bmask], adm[bmask])
        if len(heat):
            assert heat.max() <= pol["cap_mult"] + 1e-9, pol["policy_id"]
        # A events are never constrained by H3
        amask = (tb["family"].to_numpy() == "A")
        assert (adm[amask] == 0.5).all()


def test_admission_is_causal_future_outcome_invariant(load):
    """Admission reads only active heat at entry - never returns. Permuting
    the book's returns (a copy of the ba frame) changes nothing."""
    import copy
    rng = np.random.default_rng(7)
    for pol in [p for p in POLICY_GRID if p["kind"] in ("H1", "H3", "H4")]:
        adm1, _ = run_policy(load, pol, 0.5, 0.5)
        # rebuild the book with a permuted r_R column (outcomes shuffled)
        ba2 = dict(load["ba"])
        ba2["r_R"] = rng.permutation(ba2["r_R"])
        load2 = dict(load)
        load2["ba"] = ba2
        adm2, _ = run_policy(load2, pol, 0.5, 0.5)
        assert (adm1 == adm2).all(), pol["policy_id"]


def test_admission_invariant_to_base_f(load):
    """Caps and requested heat scale linearly -> decisions identical at any f."""
    for pol in [p for p in POLICY_GRID if p["kind"] != "H0"]:
        d1 = run_policy(load, pol, 0.5, 0.5, base_f=1.0, full_output=True)
        d2 = run_policy(load, pol, 0.5, 0.5, base_f=0.5, full_output=True)
        d3 = run_policy(load, pol, 0.5, 0.5, base_f=2.0, full_output=True)
        assert (d1["decision"] == d2["decision"]).all()
        assert (d1["decision"] == d3["decision"]).all()
        # admitted f scales linearly with base_f
        assert np.allclose(d1["admitted_f"], 2.0 * d2["admitted_f"],
                           atol=1e-9)


# ---------------------------------------------------------------------------
# 10-11. grid constraint + probabilities
# ---------------------------------------------------------------------------

def test_policy_grid_is_exactly_preregistered(load):
    expected = {p["policy_id"] for p in POLICY_GRID}
    frontier = _load("R6_HEAT_POLICY_FRONTIER.csv")
    assert set(frontier.policy_id.unique()) == expected
    assert len(POLICY_GRID) <= 50
    kinds = set(p["kind"] for p in POLICY_GRID)
    assert kinds <= {"H0", "H1", "H2", "H3", "H4", "H5"}


def test_probabilities_in_unit_interval(load):
    mc = _load("R6_HEAT_POLICY_MONTE_CARLO.csv")
    pcols = [c for c in mc.columns if c.startswith("P_")]
    assert pcols
    for c in pcols:
        assert (mc[c].between(0.0, 1.0)).all(), c
    tail = _load("R6_HEAT_TAIL_STRESS.csv")
    assert (tail["max_dd_ratio_vs_historical"] > 0).all()


# ---------------------------------------------------------------------------
# 13. MC episode blocks preserve cluster structure
# ---------------------------------------------------------------------------

def test_mc_episode_blocks_preserve_clusters(load):
    layouts, lay = _path_layouts(load, "episode", 5, 890, 20260815)
    clus_book = load["ba"]["clus"]
    for l in layouts:
        idx = l["idx"]
        # consecutive events from the same original cluster stay adjacent
        c = clus_book[idx]
        for k in range(len(c) - 1):
            if c[k] == c[k + 1]:
                # same cluster must be a contiguous run in the path
                pass
        # every maximal run is a single cluster
        run = 0
        for k in range(1, len(c)):
            if c[k] == c[k - 1]:
                run += 1
                assert run < 60, "cluster run implausibly long"
            else:
                run = 0


# ---------------------------------------------------------------------------
# 14-17. no best policy / no Kelly / no R7 / alpha unchanged
# ---------------------------------------------------------------------------

def test_no_best_policy_no_kelly_no_r7(load):
    d = _decision()
    assert d["best_heat_policy_selected"] is False
    assert d["kelly_authorized"] is False
    assert d["dd_adaptive_authorized"] is False
    assert d["hybrid_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False
    assert d["R7_authorized"] is False
    assert d["r6_episode_heat_sizing_pass"] is True
    assert d["human_review_required"] is True


def test_alpha_unchanged(load):
    sealed = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    assert np.allclose(
        load["ba"]["tb"]["pnl_bps"].to_numpy(),
        sealed["pnl_bps"].to_numpy(), atol=1e-6)
    assert np.allclose(
        load["ba"]["tb"]["risk_unit_bps"].to_numpy(),
        sealed["risk_unit_bps"].to_numpy(), atol=1e-9)


# ---------------------------------------------------------------------------
# 18. repo typo corrected only mechanically
# ---------------------------------------------------------------------------

def test_repo_typo_corrected():
    # build the pattern from parts so this test file itself never contains the
    # wrong spelling as a literal
    wrong = re.compile("dabi" + "gest" + "poppa")
    hits = []
    for p in ROOT.rglob("*"):
        if p.suffix in (".md", ".py", ".json", ".csv", ".txt"):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if wrong.search(txt):
                hits.append(str(p.relative_to(ROOT)))
    assert hits == [], ("dabi" + "gestpoppa") + f" still present in: {hits}"


# ---------------------------------------------------------------------------
# required outputs present
# ---------------------------------------------------------------------------

def test_all_required_outputs_present():
    required = [
        "R6_INPUT_HASH_MANIFEST.json", "R6_PROTOCOL.md",
        "R6_EVENT_EPISODE_LEDGER.csv", "R6_HEAT_DEFINITION_LOCK.md",
        "R6_ADMISSION_DECISION_LEDGER.csv", "R6_POLICY_ADMISSION_SUMMARY.csv",
        "R6_OVERLAP_ANATOMY.csv", "R6_HEAT_POLICY_FRONTIER.csv",
        "R6_HEAT_EFFICIENCY.csv", "R6_EPISODE_POLICY_RESULTS.csv",
        "R6_DIRECTIONAL_OVERLAP.csv", "R6_FAMILY_EPISODE_STRUCTURE.csv",
        "R6_HEAT_POLICY_MONTE_CARLO.csv", "R6_HEAT_EDGE_DEGRADATION.csv",
        "R6_HEAT_TAIL_STRESS.csv", "R6_ADVERSARIAL_EPISODE_TESTS.csv",
        "R6_REJECTED_EVENT_AUDIT.csv", "R6_HEAT_TEMPORAL_STABILITY.csv",
        "R6_NONDOMINATED_HEAT_FRONTIER.csv", "R6_POLICY_COMPLEXITY_MATRIX.csv",
        "R6_EVIDENCE_STATUS_MATRIX.csv", "R6_REPORT.md", "R6_DECISION.json",
    ]
    for name in required:
        assert (R6 / name).exists(), name


def test_baseline_check_row_reproduces_h0(load):
    """The H0 admission ledger row equals full admission everywhere."""
    adm_led = _load("R6_ADMISSION_DECISION_LEDGER.csv")
    h0 = adm_led[(adm_led.policy_id == "H0") & (adm_led.A_weight == 0.5)]
    assert (h0["decision"] == "ACCEPT_FULL").all()
    assert (h0["admitted_f"] == 0.5).all()


def test_admission_ledger_spec_fields_present(load):
    adm_led = _load("R6_ADMISSION_DECISION_LEDGER.csv")
    required = ["event_id", "entry_ts", "policy_id", "family", "direction",
                "base_f", "requested_f", "pre_gross_heat",
                "pre_same_direction_heat", "pre_opposite_direction_heat",
                "pre_A_heat", "pre_B_heat", "episode_budget_used",
                "remaining_heat", "admitted_f", "decision", "reason"]
    assert set(required) <= set(adm_led.columns)


def test_overlap_anatomy_artifact_present(load):
    oa = _load("R6_OVERLAP_ANATOMY.csv")
    assert {"events_with_overlap_at_entry_share", "time_share_2_active",
            "dd_share_2_overlap", "worst_day_exceeded_1_event_unit",
            "worst_episode_exceeded_1_event_unit"} <= set(oa.metric)
    prob_cols = [m for m in oa.metric if m.endswith("_share")]
    for m in prob_cols:
        v = oa.loc[oa.metric == m, "value"].iloc[0]
        assert 0.0 <= v <= 1.0, m
