"""
CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE tests.

Locks the fail-closed truth-gate repair:

- DEFECT 1: block3_scale_seal_pass requires EVERY required gate, including
  frontier_nonregression_pass (previously omitted from the pass expression).
- DEFECT 2: status is DERIVED from block3_scale_seal_pass -- never
  hardcoded "PASS".
- Fail-closed authorization invariants: no PASS while any of
  kelly_used / dd_adaptive_used / production_scale_selected /
  deployment_authorized / mt5_authorized is true.
- Gate reasons: seal_gate_failures / seal_gate_passes machine-readable
  lists on every decision.
- Negative tests EXERCISE THE DECISION GATE (fail_closed_gate /
  build_scale_seal_decision with injected inputs), not the artifact.
- Positive nonregression: on the frozen inputs the scientific outputs
  reproduce the ACCEPTED values exactly (bands, knee, allocations, heat,
  preferred default, robust-core risk contract, edge retention).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
for _p in (_SRC, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.capital_scale_seal import (  # noqa: E402
    PROHIBITED_AUTH_FIELDS, REQUIRED_GATE_FIELDS, build_scale_seal_decision,
    fail_closed_gate,
)
import run_risk_block3_scale_seal_r1 as r1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"
SEAL = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal_r1"

R1_ARTIFACTS = [
    "CR_RISK_BLOCK3_SCALE_SEAL_R1_PROTOCOL.md",
    "CR_RISK_BLOCK3_SCALE_SEAL_R1_GATE_TEST.json",
    "CR_RISK_BLOCK3_SCALE_SEAL_R1_NONREGRESSION.json",
    "CR_RISK_BLOCK3_SCALE_SEAL_R1_REPORT.md",
    "CR_RISK_BLOCK3_SCALE_SEAL_R1_DECISION.json",
]

GATE_FIELDS = [name for name, _ in REQUIRED_GATE_FIELDS]
AUTH_FIELDS = [name for name, _ in PROHIBITED_AUTH_FIELDS]

# Frozen scientific expectations (brief "POSITIVE NONREGRESSION").
EXPECTED = {
    "conservative_scale_band": [0.25, 0.5],
    "robust_core_scale_band": [0.75, 1.0],
    "aggressive_scale_band": [1.5, 2.0],
    "stress_scale_band": [3.0, 3.0],
    "knee_band": [1.0, 1.5],
    "allowed_allocations": ["A0_50_50", "A1_70_30"],
    "operating_heat": "H1-1.00-REJ",
    "preferred_allocation": "A1_70_30",
    "preferred_heat": "H1-1.00-REJ",
    "preferred_f_total_pct": 1.0,
    "robust_core_median_cagr_range": [0.4814, 0.7038],
    "robust_core_p95_dd_range": [0.0474, 0.0829],
    "robust_core_p_dd_ge_10_range": [0.0, 0.0072],
    "robust_core_p_dd_ge_15_range": [0.0, 0.0],
    "survives_100_edge": True,
    "survives_75_edge": True,
    "survives_50_edge": True,
    "survives_25_edge": False,
}

# 11 negative injections mandated by the brief.
NEGATIVE_CASES = [
    ("frontier_nonregression_pass", False, "gate"),
    ("block_episode_agreement_pass", False, "gate"),
    ("knee_seal_pass", False, "gate"),
    ("adjacent_scale_seal_pass", False, "gate"),
    ("survives_100_edge", False, "gate"),
    ("survives_75_edge", False, "gate"),
    ("kelly_used", True, "auth"),
    ("dd_adaptive_used", True, "auth"),
    ("production_scale_selected", True, "auth"),
    ("deployment_authorized", True, "auth"),
    ("mt5_authorized", True, "auth"),
]


def _gate_inputs():
    gates = {name: True for name in GATE_FIELDS}
    auths = {name: False for name in AUTH_FIELDS}
    return gates, auths


def _decision_with(**overrides) -> dict:
    """Full decision via the real builder; kwargs override gate/auth inputs."""
    kwargs = {name: True for name in GATE_FIELDS}
    kwargs.update({name: False for name in AUTH_FIELDS})
    kwargs.update({"survives_50_edge": True, "survives_25_edge": False})
    kwargs.update(overrides)
    kwargs["base_commit"] = r1.BASE_COMMIT
    return build_scale_seal_decision(**kwargs)


# --------------------------------------------------------------------------
# Gate mechanics (exercises fail_closed_gate directly)
# --------------------------------------------------------------------------

def test_gate_positive_control():
    gates, auths = _gate_inputs()
    r = fail_closed_gate(gates, auths)
    assert r["block3_scale_seal_pass"] is True
    assert r["status"] == "PASS"
    assert r["seal_gate_failures"] == []
    assert r["seal_gate_passes"] == GATE_FIELDS
    assert r["authorization_invariants_failed"] == []


@pytest.mark.parametrize("field,value,kind", NEGATIVE_CASES)
def test_gate_negative_injections_fail_closed(field, value, kind):
    """Each mandated negative injection must close the seal (pass=false,
    status != PASS) and record the exact failed gate/auth invariant."""
    gates, auths = _gate_inputs()
    if kind == "gate":
        gates[field] = value
        r = fail_closed_gate(gates, auths)
        assert field in r["seal_gate_failures"]
        assert r["authorization_invariants_failed"] == []
    else:
        auths[field] = value
        r = fail_closed_gate(gates, auths)
        assert field in r["authorization_invariants_failed"]
        assert r["seal_gate_failures"] == []
    assert r["block3_scale_seal_pass"] is False
    assert r["status"] != "PASS"
    assert r["status"] == "FAIL"
    assert field in r["status_reason"]


def test_gate_missing_input_fails_closed():
    """A missing required-gate input fails closed (no silent pass)."""
    gates, auths = _gate_inputs()
    del gates["knee_seal_pass"]
    r = fail_closed_gate(gates, auths)
    assert r["block3_scale_seal_pass"] is False
    assert "knee_seal_pass" in r["seal_gate_failures"]


# --------------------------------------------------------------------------
# DEFECT 1 -- nonregression REQUIRED in the final pass expression
# --------------------------------------------------------------------------

@pytest.mark.parametrize("field", GATE_FIELDS)
def test_defect1_each_required_gate_false_closes_seal(field):
    """Every required gate -- including frontier_nonregression_pass -- is
    part of block3_scale_seal_pass.  The OLD code omitted
    frontier_nonregression_pass; this locks the repair."""
    d = _decision_with(**{field: False})
    assert d["block3_scale_seal_pass"] is False
    assert d["status"] != "PASS"
    assert field in d["seal_gate_failures"]


def test_defect1_frontier_nonregression_false_closes_seal():
    d = _decision_with(frontier_nonregression_pass=False)
    assert d["block3_scale_seal_pass"] is False
    assert d["status"] == "FAIL"
    assert d["seal_gate_failures"] == ["frontier_nonregression_pass"]
    # every OTHER gate still passing does not rescue the seal
    assert d["block_episode_agreement_pass"] is True
    assert d["knee_seal_pass"] is True
    assert d["adjacent_scale_seal_pass"] is True
    assert d["survives_100_edge"] is True
    assert d["survives_75_edge"] is True


# --------------------------------------------------------------------------
# DEFECT 2 -- status DERIVED, never hardcoded
# --------------------------------------------------------------------------

def test_defect2_status_derived_from_pass():
    ok = _decision_with()
    assert ok["block3_scale_seal_pass"] is True
    assert ok["status"] == "PASS"
    bad = _decision_with(knee_seal_pass=False)
    assert bad["block3_scale_seal_pass"] is False
    assert bad["status"] == "FAIL"
    assert bad["status_reason"] != ""
    # both came from the SAME code path -- status follows the gate
    assert ok["status"] == ("PASS" if ok["block3_scale_seal_pass"]
                            else "FAIL")
    assert bad["status"] == ("PASS" if bad["block3_scale_seal_pass"]
                             else "FAIL")


def test_defect2_no_unconditional_pass_in_builder_source():
    src = Path(_SRC, "capital_routing", "capital_scale_seal.py").read_text(
        encoding="utf-8")
    gate_src = src[src.index("def fail_closed_gate"):]
    # status is only assigned inside the derived-if -- never an
    # unconditional literal; the decision dict never hardcodes "PASS"
    assert "if block3_scale_seal_pass:" in gate_src
    assert 'status = "PASS"' in gate_src
    assert 'status = "FAIL"' in gate_src
    assert '"status": "PASS"' not in gate_src
    builder_src = src[src.index("def build_scale_seal_decision"):]
    assert '"status": "PASS"' not in builder_src
    # behavioral proof lives in test_defect2_status_derived_from_pass


# --------------------------------------------------------------------------
# Fail-closed authorization invariants
# --------------------------------------------------------------------------

@pytest.mark.parametrize("field", AUTH_FIELDS)
def test_prohibited_auth_true_blocks_pass(field):
    d = _decision_with(**{field: True})
    assert d[field] is True
    assert d["block3_scale_seal_pass"] is False
    assert d["status"] == "FAIL"
    assert field in d["authorization_invariants_failed"]
    # authorized-state flags are locked in the artifact decision
    art = _r1_decision()
    assert art[field] is False


# --------------------------------------------------------------------------
# Gate reasons on the decision
# --------------------------------------------------------------------------

def test_seal_gate_lists_on_decision():
    ok = _decision_with()
    assert ok["seal_gate_failures"] == []
    assert set(ok["seal_gate_passes"]) == set(GATE_FIELDS)
    bad = _decision_with(adjacent_scale_seal_pass=False)
    assert bad["seal_gate_failures"] == ["adjacent_scale_seal_pass"]
    assert "adjacent_scale_seal_pass" not in bad["seal_gate_passes"]


# --------------------------------------------------------------------------
# R1 artifacts
# --------------------------------------------------------------------------

def _r1_decision() -> dict:
    return json.loads((OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_DECISION.json")
                      .read_text(encoding="utf-8"))


def test_r1_artifacts_exist():
    missing = [f for f in R1_ARTIFACTS if not (OUT / f).exists()]
    assert missing == [], f"missing R1 artifacts: {missing}"


def test_r1_decision_science_frozen():
    d = _r1_decision()
    assert d["checkpoint"] == r1.CHECKPOINT
    assert d["base_commit"] == r1.BASE_COMMIT
    assert d["conservative_scale_band"] == EXPECTED["conservative_scale_band"]
    assert d["robust_core_scale_band"] == EXPECTED["robust_core_scale_band"]
    assert d["aggressive_scale_band"] == EXPECTED["aggressive_scale_band"]
    assert d["stress_scale_band"] == EXPECTED["stress_scale_band"]
    assert d["allowed_allocations"] == EXPECTED["allowed_allocations"]
    assert d["robust_core_median_cagr_range"] == \
        EXPECTED["robust_core_median_cagr_range"]
    assert d["robust_core_p95_dd_range"] == EXPECTED["robust_core_p95_dd_range"]
    assert d["robust_core_p_dd_ge_10_range"] == \
        EXPECTED["robust_core_p_dd_ge_10_range"]
    assert d["robust_core_p_dd_ge_15_range"] == \
        EXPECTED["robust_core_p_dd_ge_15_range"]
    pref = d["preferred_research_default"]
    assert pref["allocation"] == EXPECTED["preferred_allocation"]
    assert pref["heat_architecture"] == EXPECTED["preferred_heat"]
    assert pref["f_total_pct"] == EXPECTED["preferred_f_total_pct"]
    assert d["status"] == "PASS"
    assert d["block3_scale_seal_pass"] is True
    assert d["seal_gate_failures"] == []


def test_r1_decision_gate_consistent_with_artifact_fields():
    """Re-run the gate from the artifact's own fields: it must reproduce the
    artifact's pass/status (gate is the single source of truth)."""
    d = _r1_decision()
    gates = {name: bool(d[name]) for name in GATE_FIELDS}
    auths = {name: bool(d[name]) for name in AUTH_FIELDS}
    r = fail_closed_gate(gates, auths)
    assert r["block3_scale_seal_pass"] == d["block3_scale_seal_pass"]
    assert r["status"] == d["status"]
    assert r["seal_gate_failures"] == d["seal_gate_failures"]


def test_r1_nonregression_artifact_pass():
    n = json.loads((OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_NONREGRESSION.json")
                   .read_text(encoding="utf-8"))
    assert n["nonregression_pass"] is True
    assert len(n["fields"]) == len(EXPECTED)
    for f in n["fields"]:
        assert f["matches_expected"] is True, f["field"]
        assert f["matches_sealed"] is True, f["field"]


def test_r1_gate_test_artifact_all_fail_closed():
    g = json.loads((OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_GATE_TEST.json")
                   .read_text(encoding="utf-8"))
    assert g["positive_control"]["block3_scale_seal_pass"] is True
    assert g["positive_control"]["status"] == "PASS"
    assert g["all_negative_tests_fail_closed"] is True
    assert len(g["negative_tests"]) == 11
    for t in g["negative_tests"]:
        assert t["fail_closed"] is True, t["injection"]


# --------------------------------------------------------------------------
# Positive nonregression: recompute from frozen frontier inputs (no new MC)
# --------------------------------------------------------------------------

def test_nonregression_recompute_matches_expected():
    """Recompute the scientific outputs via the pure seal functions and
    compare to the frozen brief expectations -- science is unchanged."""
    from capital_routing.capital_scale_seal import (
        adjacent_scale_review, allocation_review, edge_review, edge_seal_state,
        heat_review, load_frontier, region_definition, risk_contract,
        robust_core)
    data = load_frontier(FRONTIER)
    edge = edge_review(data["surv"], data["mc"])
    edge_state = edge_seal_state(edge)
    rc = robust_core(data["mc"], data["dep"])
    contract = risk_contract(rc, edge_state)
    adj = adjacent_scale_review(data["mc"], ["A0_50_50", "A1_70_30"],
                                ["H0", "H1-1.00-REJ"])
    alloc = allocation_review(data["mc"], data["hist"], data["surv"])
    heat = heat_review(data["mc"], data["hist"], data["paired"])
    region = region_definition(rc, data["knee"], adj, alloc, heat,
                               edge_state, data["decision"], r1.BASE_COMMIT)

    def r4(v):
        return [round(float(x), 4) for x in v]

    assert region["scale_bands"]["CONSERVATIVE"] == \
        EXPECTED["conservative_scale_band"]
    assert region["scale_bands"]["ROBUST_CORE"] == \
        EXPECTED["robust_core_scale_band"]
    assert region["scale_bands"]["AGGRESSIVE"] == \
        EXPECTED["aggressive_scale_band"]
    assert region["scale_bands"]["STRESS_ONLY"] == EXPECTED["stress_scale_band"]
    assert region["knee_band"] == EXPECTED["knee_band"]
    assert region["allowed_allocations"] == EXPECTED["allowed_allocations"]
    assert region["operating_heat_reference"] == EXPECTED["operating_heat"]
    pref = region["preferred_research_default"]
    assert pref["allocation"] == EXPECTED["preferred_allocation"]
    assert pref["heat_architecture"] == EXPECTED["preferred_heat"]
    assert pref["f_total_pct"] == EXPECTED["preferred_f_total_pct"]
    assert r4(contract["median_cagr_range"]) == \
        EXPECTED["robust_core_median_cagr_range"]
    assert r4(contract["p95_max_dd_range"]) == \
        EXPECTED["robust_core_p95_dd_range"]
    assert r4(contract["P_dd_ge_10_range"]) == \
        EXPECTED["robust_core_p_dd_ge_10_range"]
    assert r4(contract["P_dd_ge_15_range"]) == \
        EXPECTED["robust_core_p_dd_ge_15_range"]
    assert edge_state["survives_100"] == EXPECTED["survives_100_edge"]
    assert edge_state["survives_75"] == EXPECTED["survives_75_edge"]
    assert edge_state["survives_50"] == EXPECTED["survives_50_edge"]
    assert edge_state["survives_25"] == EXPECTED["survives_25_edge"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_r1_deterministic_rerun():
    """Re-running the R1 runner reproduces byte-identical artifacts."""
    before = {f: _sha(OUT / f) for f in R1_ARTIFACTS}
    r1.main()
    after = {f: _sha(OUT / f) for f in R1_ARTIFACTS}
    assert before == after
