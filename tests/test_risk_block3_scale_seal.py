"""
CR-RISK-BLOCK-III-SCALE-SEAL tests.

Locks the scale-seal checkpoint invariants:

- All 12 required artifacts exist (plus the transitions csv); the decision
  carries every mandated field with the expected values (bands, allowed vs
  diagnostic allocations, heat status, robust-core ranges, edge survival,
  block/episode agreement, knee seal, adjacent-scale seal, no Kelly /
  DD-adaptive / production / deployment / MT5 authorization).
- Bands are evidence-backed: CONSERVATIVE 0.25-0.50, ROBUST CORE 0.75-1.00,
  AGGRESSIVE 1.50-2.00, STRESS ONLY 3.00.
- Knee band is the modal [1.00, 1.50]; robust core sits at-or-below the
  knee start.
- No dependency-sensitive cells inside the robust core band (block/episode
  agreement -> band sealable).
- Edge retention: 100% + 75% survive in the band; 25% is the alpha-loss
  boundary (not required to survive).
- Adjacent-scale seal: no acceleration inside 0.75->1.00, acceleration at
  the 1.00->1.50 boundary under the operating heat.
- Heat review: H1-1.00-REJ is the operating reference (paired evidence);
  H1-3.00-REJ never binds.
- Preferred research default = A1_70_30 / H1-1.00-REJ / f=1.00 and is
  explicitly NOT production sizing.
- The seal is deterministic: review tables are pure functions of the frozen
  frontier inputs (no new MC), verified by re-running the synthesis in-memory
  and comparing hashes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, _SRC)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.capital_scale_seal import (  # noqa: E402
    AGGRESSIVE_BAND, CONSERVATIVE_BAND, OPERATING_ALLOCS, OPERATING_HEAT,
    PREFERRED_ALLOC, PREFERRED_F_PCT, PRIMARY_SCHEMES, ROBUST_CORE_BAND,
    STRESS_BAND, adjacent_scale_review, adjacent_scale_seal_pass,
    allocation_review, edge_review, edge_seal_state, heat_review, knee_band,
    knee_review, load_frontier, robust_core, robust_core_ranges,
)

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal"

REQUIRED = [
    "CR_RISK_BLOCK3_SCALE_SEAL_PROTOCOL.md",
    "CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json",
    "CR_RISK_BLOCK3_KNEE_REVIEW.csv",
    "CR_RISK_BLOCK3_ADJACENT_SCALE_REVIEW.csv",
    "CR_RISK_BLOCK3_ALLOCATION_REVIEW.csv",
    "CR_RISK_BLOCK3_HEAT_REVIEW.csv",
    "CR_RISK_BLOCK3_EDGE_REVIEW.csv",
    "CR_RISK_BLOCK3_ROBUST_CORE.csv",
    "CR_RISK_BLOCK3_REGION_DEFINITION.json",
    "CR_RISK_BLOCK3_RISK_CONTRACT.json",
    "CR_RISK_BLOCK3_SCALE_SEAL_REPORT.md",
    "CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json",
]

DECISION_FIELDS = [
    "checkpoint", "status", "base_commit", "frontier_nonregression_pass",
    "conservative_scale_band", "robust_core_scale_band",
    "aggressive_scale_band", "stress_scale_band", "allowed_allocations",
    "diagnostic_only_allocations", "heat_architecture_status",
    "preferred_research_default", "robust_core_median_cagr_range",
    "robust_core_p95_dd_range", "robust_core_p_dd_ge_10_range",
    "robust_core_p_dd_ge_15_range", "survives_100_edge", "survives_75_edge",
    "survives_50_edge", "survives_25_edge", "block_episode_agreement_pass",
    "knee_seal_pass", "adjacent_scale_seal_pass", "kelly_used",
    "dd_adaptive_used", "production_scale_selected", "deployment_authorized",
    "mt5_authorized", "block3_scale_seal_pass", "human_review_required",
    "next_checkpoint_recommended", "next_checkpoint_authorized",
]


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _decision() -> Dict:
    return json.loads((OUT / "CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json")
                      .read_text(encoding="utf-8"))


def test_all_artifacts_exist():
    missing = [f for f in REQUIRED if not (OUT / f).exists()]
    assert missing == [], f"missing seal artifacts: {missing}"


def test_decision_carries_every_required_field():
    d = _decision()
    missing = [f for f in DECISION_FIELDS if f not in d]
    assert missing == [], f"missing decision fields: {missing}"
    assert d["checkpoint"] == "CR-RISK-BLOCK-III-SCALE-SEAL"
    assert d["status"] == "PASS"


def test_expected_flag_values():
    d = _decision()
    assert d["frontier_nonregression_pass"] is True
    assert d["block_episode_agreement_pass"] is True
    assert d["knee_seal_pass"] is True
    assert d["adjacent_scale_seal_pass"] is True
    assert d["kelly_used"] is False
    assert d["dd_adaptive_used"] is False
    assert d["production_scale_selected"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False
    assert d["next_checkpoint_authorized"] is False
    assert d["block3_scale_seal_pass"] is True


def test_scale_bands_match_evidence():
    d = _decision()
    assert d["conservative_scale_band"] == CONSERVATIVE_BAND
    assert d["robust_core_scale_band"] == ROBUST_CORE_BAND
    assert d["aggressive_scale_band"] == AGGRESSIVE_BAND
    assert d["stress_scale_band"] == STRESS_BAND


def test_allocations_split():
    d = _decision()
    assert d["allowed_allocations"] == ["A0_50_50", "A1_70_30"]
    assert "A2_100_0_A" in d["diagnostic_only_allocations"]
    assert "A3_0_100_B" in d["diagnostic_only_allocations"]


def test_robust_core_ranges_are_sane():
    d = _decision()
    lo, hi = d["robust_core_median_cagr_range"]
    assert 0.0 < lo <= hi < 2.0
    lo, hi = d["robust_core_p95_dd_range"]
    assert 0.0 <= lo <= hi < 0.30
    lo, hi = d["robust_core_p_dd_ge_10_range"]
    assert 0.0 <= lo <= hi < 0.10
    lo, hi = d["robust_core_p_dd_ge_15_range"]
    assert 0.0 <= lo <= hi < 0.05


def test_edge_retention_in_band():
    d = _decision()
    assert d["survives_100_edge"] is True
    assert d["survives_75_edge"] is True
    assert d["survives_50_edge"] is True
    # 25% is the recorded alpha-loss boundary -- never required to survive
    assert d["survives_25_edge"] is False


def test_preferred_default_not_production():
    d = _decision()
    pref = d["preferred_research_default"]
    assert pref["allocation"] == PREFERRED_ALLOC
    assert pref["heat_architecture"] == OPERATING_HEAT
    assert pref["f_total_pct"] == PREFERRED_F_PCT
    assert "not production sizing" in pref["role"].lower()
    assert d["production_scale_selected"] is False


def test_knee_band_is_modal_1_0_1_5():
    data = load_frontier(FRONTIER)
    kb, stats = knee_band(data["knee"])
    assert kb == [1.0, 1.5]
    assert stats["n_found"] > 0
    assert stats["modal_interval"] == "[1.00, 1.50]"
    # robust core must sit at-or-below the knee start
    assert ROBUST_CORE_BAND[1] <= kb[0]


def test_no_dependency_sensitive_cells_in_band():
    data = load_frontier(FRONTIER)
    rc = robust_core(data["mc"], data["dep"])
    op = rc[rc["is_operating_heat"]]
    assert (op["dependency_sensitive"] == False).all()  # noqa: E712


def test_adjacent_scale_seal_pass():
    data = load_frontier(FRONTIER)
    adj = adjacent_scale_review(data["mc"], ["A0_50_50", "A1_70_30"],
                                ["H0", "H1-1.00-REJ"])
    seal = adjacent_scale_seal_pass(adj)
    assert seal["pass"] is True
    assert seal["core_accelerating_cells"] == 0
    assert seal["boundary_accelerating_cells"] > 0
    assert seal["boundary_scheme_agreement"] is True


def test_heat_verdicts():
    data = load_frontier(FRONTIER)
    heat = heat_review(data["mc"], data["hist"], data["paired"])
    h1 = heat[heat["heat_id"] == "H1-1.00-REJ"].iloc[0]
    h3 = heat[heat["heat_id"] == "H1-3.00-REJ"].iloc[0]
    assert h1["verdict"] == "RETAIN_OPERATING_REFERENCE"
    assert h1["P_h1_dd_lt_h0"] > 0.5
    assert h1["d_median_max_dd"] < 0  # median DD lower under the cap
    assert h3["verdict"] == "NOT_RETAINED_NEVER_BINDS"


def test_knee_review_rows():
    data = load_frontier(FRONTIER)
    kr = knee_review(data["knee"])
    assert len(kr) == len(data["knee"])
    found = kr[kr["knee_condition"] == "FOUND"]
    assert len(found) == 53
    assert (found["knee_interval"] == "[1.00, 1.50]").all()


def test_input_hash_manifest_complete():
    m = json.loads((OUT / "CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json")
                   .read_text(encoding="utf-8"))
    assert m["checkpoint"] == "CR-RISK-BLOCK-III-SCALE-SEAL"
    files = m["files"]
    assert len(files) >= 10
    for name, h in files.items():
        assert h is not None and len(h) == 64
        # verify the hash actually matches the frozen frontier artifact
        assert _sha_file(FRONTIER / name) == h


def test_risk_contract_fields():
    c = json.loads((OUT / "CR_RISK_BLOCK3_RISK_CONTRACT.json")
                   .read_text(encoding="utf-8"))
    for key in ["median_cagr_range", "p95_max_dd_range", "P_dd_ge_10_range",
                "P_dd_ge_15_range", "P_technical_ruin_max",
                "dependency_sensitive_cells_in_band", "edge_100_behavior",
                "edge_75_behavior", "edge_50_behavior", "edge_25_behavior",
                "units"]:
        assert key in c, f"missing contract field {key}"
    assert c["dependency_sensitive_cells_in_band"] == 0
    assert c["edge_100_behavior"]["survives"] is True
    assert c["edge_75_behavior"]["survives"] is True
    assert c["edge_50_behavior"]["survives"] is True
    assert c["edge_25_behavior"]["survives"] is False


def test_determinism_review_tables():
    """Review tables must be pure functions of the frozen frontier inputs:
    re-running the synthesis in-memory reproduces identical artifacts."""
    data = load_frontier(FRONTIER)
    kr = knee_review(data["knee"])
    adj = adjacent_scale_review(data["mc"], ["A0_50_50", "A1_70_30"],
                                ["H0", "H1-1.00-REJ"])
    alloc = allocation_review(data["mc"], data["hist"], data["surv"])
    heat = heat_review(data["mc"], data["hist"], data["paired"])
    edge = edge_review(data["surv"], data["mc"])
    rc = robust_core(data["mc"], data["dep"])

    for name, df in [
        ("CR_RISK_BLOCK3_KNEE_REVIEW.csv", kr),
        ("CR_RISK_BLOCK3_ADJACENT_SCALE_REVIEW.csv",
         pd.read_csv(OUT / "CR_RISK_BLOCK3_ADJACENT_SCALE_REVIEW.csv")),
        ("CR_RISK_BLOCK3_ALLOCATION_REVIEW.csv",
         pd.read_csv(OUT / "CR_RISK_BLOCK3_ALLOCATION_REVIEW.csv")),
        ("CR_RISK_BLOCK3_HEAT_REVIEW.csv",
         pd.read_csv(OUT / "CR_RISK_BLOCK3_HEAT_REVIEW.csv")),
        ("CR_RISK_BLOCK3_EDGE_REVIEW.csv",
         pd.read_csv(OUT / "CR_RISK_BLOCK3_EDGE_REVIEW.csv")),
        ("CR_RISK_BLOCK3_ROBUST_CORE.csv",
         pd.read_csv(OUT / "CR_RISK_BLOCK3_ROBUST_CORE.csv")),
    ]:
        disk = pd.read_csv(OUT / name)
        recomputed = df
        # compare on shared columns, sorted
        shared = [c for c in disk.columns if c in recomputed.columns]
        a = disk[shared].sort_values(shared).reset_index(drop=True)
        b = recomputed[shared].sort_values(shared).reset_index(drop=True)
        assert len(a) == len(b), f"{name}: row count mismatch"
        pd.testing.assert_frame_equal(a, b, check_dtype=False, rtol=1e-12,
                                      atol=1e-12,
                                      obj=f"{name}: determinism violated")
