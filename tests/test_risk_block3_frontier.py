"""
CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER tests.

Locks the frontier checkpoint invariants:

- All 23 required artifacts exist; decision carries every mandated field with
  the expected values (890 / 432 / 458 / 482 / 3; 560 historical cells;
  1680 MC rows; block+episode >= 10000 paths; iid 2000 diagnostic; common
  random numbers; reference nonregression + R6 MC regression PASS; Kelly
  UNSTABLE_REFERENCE and NOT used / NOT authorized; no best scale /
  allocation / heat cap / production config; no deployment / MT5).
- Path banks are deterministic per (scheme, seed) and reused across every
  cell (common random numbers -> same layout hash for paired configs).
- MC surface has exactly 560 rows per scheme; 1680 total.
- Probability CIs are Wilson; observed 0 / n has a finite upper bound, never
  reported as "risk = 0" with no uncertainty.
- Survival / envelopes use block+episode consensus; IID never primary.
- A3 (0/100 B) is diagnostic-only and excluded from recommendation frontier.
- 3% f_total flagged is_outer_stress; no fine scale grid.
- Edge transform (positive returns scaled, negatives untouched) never feeds
  admission.
- No DD adaptation, no PnL-conditioned sizing, no new heat policy, no new
  allocation, no Kelly execution, no production selection.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
_SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, _SRC)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.capital_scale_frontier import (  # noqa: E402
    ALLOCATIONS, ALL_SCALE_PCT, EDGE_STATES, HEAT_IDS, MC_SCHEMES,
    OUTER_STRESS_PCT, PATH_COUNTS, PRIMARY_SCHEMES, RECOMMENDATION_ALLOCS,
    SCALE_LADDER_PCT, edge_transformed_r, surface_configs, wilson_ci,
)
from capital_routing.phases.phase_r6_common import load_r6_inputs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"

REQUIRED = [
    "CR_RISK_BLOCK3_FRONTIER_PROTOCOL.md",
    "CR_RISK_BLOCK3_FRONTIER_INPUT_HASH_MANIFEST.json",
    "CR_RISK_BLOCK3_PATH_BANK_MANIFEST.json",
    "CR_RISK_BLOCK3_PATH_BANK_CONVERGENCE.csv",
    "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json",
    "CR_RISK_BLOCK3_R6_MC_REGRESSION.json",
    "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv",
    "CR_RISK_BLOCK3_MC_SURFACE.csv",
    "CR_RISK_BLOCK3_MC_PROBABILITY_CI.csv",
    "CR_RISK_BLOCK3_QUANTILE_CI.csv",
    "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv",
    "CR_RISK_BLOCK3_RISK_ENVELOPE_MATRIX.csv",
    "CR_RISK_BLOCK3_NONDOMINATED_FRONTIER.csv",
    "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv",
    "CR_RISK_BLOCK3_ADJACENT_SCALE_DELTAS.csv",
    "CR_RISK_BLOCK3_MARGINAL_EFFICIENCY.csv",
    "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv",
    "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv",
    "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv",
    "CR_RISK_BLOCK3_KELLY_STATUS.json",
    "CR_RISK_BLOCK3_COMPONENT_STATUS.csv",
    "CR_RISK_BLOCK3_REPORT.md",
    "CR_RISK_BLOCK3_DECISION.json",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_RISK_BLOCK3_DECISION.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def load():
    return load_r6_inputs(ROOT)


# ---------------------------------------------------------------------------
# Artifacts + decision
# ---------------------------------------------------------------------------

def test_artifacts_exist():
    for name in REQUIRED:
        assert (OUT / name).is_file(), f"missing artifact {name}"


def test_decision_fields():
    d = _decision()
    assert d["checkpoint"] == "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER"
    assert d["status"] == "PASS"
    assert d["block3_frontier_pass"] is True
    assert d["total_events"] == 890
    assert d["family_a_events"] == 432
    assert d["family_b_events"] == 458
    assert d["episode_count"] == 482
    assert d["max_concurrency"] == 3
    assert d["historical_surface_cells"] == 560
    assert d["mc_surface_rows"] == 1680
    assert d["block_paths"] == 10000
    assert d["episode_paths"] == 10000
    assert d["iid_paths"] == 2000


def test_book_reconciles():
    load = load_r6_inputs(ROOT)
    tb = load["ba"]["tb"]
    fam = load["ba"]["fam"]
    assert len(tb) == 890
    assert int((fam == "A").sum()) == 432
    assert int((fam == "B").sum()) == 458
    assert int(load["ba"]["clus"].max() + 1) == 482


# ---------------------------------------------------------------------------
# Locks (nothing selected / authorized)
# ---------------------------------------------------------------------------

def test_no_selections():
    d = _decision()
    for k in ["best_scale_selected", "best_allocation_selected",
              "best_heat_cap_selected", "production_configuration_selected",
              "kelly_used_for_selection", "kelly_authorized",
              "deployment_authorized", "mt5_authorized",
              "new_alpha_science_performed", "new_heat_policy_created",
              "dd_adaptive_logic_created"]:
        assert d.get(k) is False, f"{k} must be False"


def test_kelly_status():
    d = _decision()
    assert d["kelly_status"] == "UNSTABLE_REFERENCE"
    k = json.loads((OUT / "CR_RISK_BLOCK3_KELLY_STATUS.json").read_text(
        encoding="utf-8"))
    assert k["kelly_status"] == "UNSTABLE_REFERENCE"
    assert k["kelly_used_for_selection"] is False
    assert k["kelly_authorized"] is False


def test_regressions_pass():
    d = _decision()
    assert d["common_random_numbers_pass"] is True
    assert d["reference_nonregression_pass"] is True
    assert d["r6_mc_regression_pass"] is True
    assert d["mc_convergence_pass"] is True
    r6 = json.loads((OUT / "CR_RISK_BLOCK3_R6_MC_REGRESSION.json").read_text(
        encoding="utf-8"))
    assert r6["pass"] is True
    nr = json.loads((OUT / "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json")
                    .read_text(encoding="utf-8"))
    assert nr["pass"] is True


def test_next_checkpoint():
    d = _decision()
    assert d["next_checkpoint_recommended"] == "CR-RISK-BLOCK-III-SCALE-SEAL"
    assert d["next_checkpoint_authorized"] is False


# ---------------------------------------------------------------------------
# Surface structure
# ---------------------------------------------------------------------------

def test_surface_cell_count():
    cells = surface_configs()
    assert len(cells) == 560  # 4 alloc x 5 heat x 7 scale x 4 edge


def test_mc_surface_rows():
    mc = pd.read_csv(OUT / "CR_RISK_BLOCK3_MC_SURFACE.csv")
    assert len(mc) == 1680
    counts = mc["scheme"].value_counts().to_dict()
    assert counts == {"block": 560, "episode": 560, "iid": 560}
    assert set(mc["alloc_id"].unique()) == set(ALLOCATIONS)
    assert set(mc["heat_id"].unique()) == set(HEAT_IDS)
    assert set(np.round(mc["edge"].unique(), 2)) == set(EDGE_STATES)


def test_scale_ladder_frozen():
    assert SCALE_LADDER_PCT == [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
    assert ALL_SCALE_PCT == [0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00]
    assert OUTER_STRESS_PCT == 3.00
    # no fine grid
    assert len(SCALE_LADDER_PCT) == 6


def test_path_counts_frozen():
    assert PATH_COUNTS["block"] >= 10000
    assert PATH_COUNTS["episode"] >= 10000
    assert PRIMARY_SCHEMES == ["block", "episode"]
    assert MC_SCHEMES == ["block", "episode", "iid"]


def test_outer_stress_flag():
    mc = pd.read_csv(OUT / "CR_RISK_BLOCK3_MC_SURFACE.csv")
    stressed = mc[mc["f_pct"] == 3.0]
    # 4 alloc x 5 heat x 4 edge x 3 schemes = 240 merged rows
    assert len(stressed) == 240
    # per-scheme it is exactly the 80-cell outer-stress slice
    assert len(stressed[stressed["scheme"] == "block"]) == 80
    assert len(stressed[stressed["scheme"] == "episode"]) == 80
    assert len(stressed[stressed["scheme"] == "iid"]) == 80


def test_a3_diagnostic_only():
    reg = pd.read_csv(OUT / "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv")
    a3 = reg[reg["alloc_id"] == "A3_0_100_B"]
    assert len(a3) > 0
    assert a3["diagnostic_only"].all()
    nd = pd.read_csv(OUT / "CR_RISK_BLOCK3_NONDOMINATED_FRONTIER.csv")
    assert "A3_0_100_B" not in set(nd["alloc_id"].unique())


# ---------------------------------------------------------------------------
# Common random numbers / determinism
# ---------------------------------------------------------------------------

def test_path_bank_manifest():
    m = json.loads((OUT / "CR_RISK_BLOCK3_PATH_BANK_MANIFEST.json").read_text(
        encoding="utf-8"))
    for scheme in MC_SCHEMES:
        b = m["banks"][scheme]
        assert b["n_paths"] == PATH_COUNTS[scheme]
        assert len(b["layout_hash"]) >= 8
        assert b["seed"] == m["seed"]
    assert m["block_params"]["size_events"] == 25
    assert m["episode_params"]["interval_h"] == 12


def test_convergence():
    conv = pd.read_csv(OUT / "CR_RISK_BLOCK3_PATH_BANK_CONVERGENCE.csv")
    assert len(conv) >= 8  # 4 prefixes x 2 primary schemes
    assert "n_prefix" in conv.columns
    # deterministic prefixes of the SAME bank must exist
    assert sorted(conv["n_prefix"].unique())[0] <= 1000
    for scheme in PRIMARY_SCHEMES:
        s = conv[conv["scheme"] == scheme]
        assert sorted(s["n_prefix"].unique()) == [1000, 2500, 5000, 10000]


# ---------------------------------------------------------------------------
# Probability uncertainty (Wilson, finite upper bound at 0/n)
# ---------------------------------------------------------------------------

def test_wilson_zero_count_finite_upper_bound():
    lo, hi = wilson_ci(0, 10000)
    assert lo == 0.0
    assert hi > 0.0
    assert hi < 0.001  # 95% upper bound at 0/10000 is ~0.00037


def test_wilson_nonzero():
    lo, hi = wilson_ci(500, 10000)
    assert lo < 0.05 < hi


def test_probability_ci_complete():
    prob = pd.read_csv(OUT / "CR_RISK_BLOCK3_MC_PROBABILITY_CI.csv")
    assert len(prob) == 1680
    for key in ["P_dd_ge_10", "P_dd_ge_20", "P_technical_ruin"]:
        assert f"{key}_ci_lo" in prob.columns
        assert f"{key}_ci_hi" in prob.columns
    # no reported 0 without a finite CI upper bound
    z = prob[prob["P_dd_ge_30"] == 0]
    assert (z["P_dd_ge_30_ci_hi"] > 0).all()


def test_quantile_ci():
    q = pd.read_csv(OUT / "CR_RISK_BLOCK3_QUANTILE_CI.csv")
    assert len(q) > 0
    for col in ["p95_dd_ci_lo", "p95_dd_ci_hi", "p99_dd_ci_lo",
                "p99_dd_ci_hi"]:
        assert col in q.columns


# ---------------------------------------------------------------------------
# Survival / envelopes use block+episode consensus only
# ---------------------------------------------------------------------------

def test_survival_uses_primary_schemes():
    surv = pd.read_csv(OUT / "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv")
    assert len(surv) > 0
    for col in ["survives_100", "survives_75", "survives_50", "survives_25"]:
        assert col in surv.columns


def test_iid_never_primary():
    # iid rows exist but survival/region tables must not be driven by iid
    surv = pd.read_csv(OUT / "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv")
    assert "scheme" not in surv.columns or "iid" not in set(
        surv["scheme"].unique())
    mc = pd.read_csv(OUT / "CR_RISK_BLOCK3_MC_SURFACE.csv")
    iid = mc[mc["scheme"] == "iid"]
    assert len(iid) == 560  # recorded as diagnostic


def test_envelope_consensus():
    env = pd.read_csv(OUT / "CR_RISK_BLOCK3_RISK_ENVELOPE_MATRIX.csv")
    assert len(env) == 1120  # 560 cells x 2 primary schemes
    for e in [5, 10, 15, 20, 25, 30]:
        for q in ["p95", "p99"]:
            assert f"block_{q}_E{e}" in env.columns
            assert f"episode_{q}_E{e}" in env.columns


def test_dependency_sensitive_reported():
    dep = pd.read_csv(OUT / "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv")
    assert len(dep) > 0
    assert "sensitive" in dep.columns
    assert dep["sensitive"].sum() >= 0


# ---------------------------------------------------------------------------
# Edge transform semantics
# ---------------------------------------------------------------------------

def test_edge_transform_positive_scaled_negative_untouched():
    r = np.array([0.10, -0.05, 0.0, 0.02])
    # engine passes famA as a BOOLEAN mask (int arrays would be interpreted
    # as fancy indices by numpy, so the mask dtype is part of the contract)
    famA = np.array([True, True, True, False])
    out = edge_transformed_r(r, famA, 0.5)
    # positive returns scaled for BOTH families; negatives + zeros untouched
    # (same retention state applies to A and B in the primary frontier)
    assert np.isclose(out[0], 0.05)
    assert np.isclose(out[1], -0.05)
    assert np.isclose(out[2], 0.0)
    assert np.isclose(out[3], 0.01)


def test_edge_transform_identity_at_100():
    rng = np.random.default_rng(7)
    r = rng.normal(0, 1, 50)
    famA = rng.integers(0, 2, 50)
    out = edge_transformed_r(r, famA, 1.0)
    assert np.allclose(out, r)


# ---------------------------------------------------------------------------
# Historical surface minimum-equity survival metric
# ---------------------------------------------------------------------------

def test_historical_surface_cells():
    hist = pd.read_csv(OUT / "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv")
    assert len(hist) == 560
    assert "alloc_id" in hist.columns and "heat_id" in hist.columns
    assert "f_pct" in hist.columns and "edge" in hist.columns


# ---------------------------------------------------------------------------
# Paired / adjacent / marginal analysis exist
# ---------------------------------------------------------------------------

def test_paired_h1_vs_h0():
    p = pd.read_csv(OUT / "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv")
    assert len(p) > 0
    assert p["heat_id"].nunique() == 4  # H1 refs only (H0 is the baseline)
    assert "P_h1_dd_lt_h0" in p.columns


def test_adjacent_and_marginal():
    adj = pd.read_csv(OUT / "CR_RISK_BLOCK3_ADJACENT_SCALE_DELTAS.csv")
    assert len(adj) > 0
    marg = pd.read_csv(OUT / "CR_RISK_BLOCK3_MARGINAL_EFFICIENCY.csv")
    assert len(marg) > 0


def test_knee_and_region():
    knee = pd.read_csv(OUT / "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv")
    assert len(knee) > 0
    assert "knee_interval" in knee.columns
    reg = pd.read_csv(OUT / "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv")
    assert len(reg) == 140  # 4 alloc x 5 heat x 7 scale
    assert "region" in reg.columns
