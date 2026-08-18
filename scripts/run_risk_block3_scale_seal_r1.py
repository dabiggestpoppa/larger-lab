"""CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE -- deterministic runner.

Fail-closed truth-gate repair over the sealed Block-III scale seal (commit
78dca3a7, CR-RISK-BLOCK-III-SCALE-SEAL).  The scientific result is FROZEN
and ACCEPTED -- this checkpoint re-verifies it (positive nonregression) and
repairs ONLY the final decision/governance mechanics:

  DEFECT 1  block3_scale_seal_pass must require EVERY required gate,
            including frontier_nonregression_pass (previously omitted).
  DEFECT 2  status must be DERIVED from block3_scale_seal_pass, never
            hardcoded "PASS".
  FAIL-CLOSED AUTH INVARIANTS -- no PASS while any of
            kelly_used / dd_adaptive_used / production_scale_selected /
            deployment_authorized / mt5_authorized is true.
  GATE REASONS -- explicit machine-readable seal_gate_failures /
            seal_gate_passes lists in every decision.

NO new Monte Carlo.  NO change to the frontier, operating bands,
allocations, H1 heat, f_total, edge-retention logic, preferred research
default, or any alpha science.

Artifacts (research/capital_routing/risk/block3_scale_seal_r1/):
  CR_RISK_BLOCK3_SCALE_SEAL_R1_PROTOCOL.md
  CR_RISK_BLOCK3_SCALE_SEAL_R1_INPUT_HASHES.json
  CR_RISK_BLOCK3_SCALE_SEAL_R1_NONREGRESSION.json
  CR_RISK_BLOCK3_SCALE_SEAL_R1_GATE_TEST.json
  CR_RISK_BLOCK3_SCALE_SEAL_R1_REPORT.md
  CR_RISK_BLOCK3_SCALE_SEAL_R1_DECISION.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from capital_routing.capital_scale_seal import (
    build_scale_seal_decision,
    edge_seal_state,
    fail_closed_gate,
    load_frontier,
    region_definition,
    risk_contract,
    robust_core,
)

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"
SEAL = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal_r1"

# Authoritative base: the ACCEPTED scale-seal commit this repair sits on.
BASE_COMMIT = "78dca3a7453205241bdbe935b985e3e7be7b8144"
CHECKPOINT = "CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE"

FRONTIER_INPUT_FILES: List[str] = [
    "CR_RISK_BLOCK3_MC_SURFACE.csv",
    "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv",
    "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv",
    "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv",
    "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv",
    "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv",
    "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv",
    "CR_RISK_BLOCK3_DECISION.json",
    "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json",
    "CR_RISK_BLOCK3_R6_MC_REGRESSION.json",
]

SEAL_INPUT_FILES: List[str] = [
    "CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json",
    "CR_RISK_BLOCK3_REGION_DEFINITION.json",
    "CR_RISK_BLOCK3_RISK_CONTRACT.json",
]

# Frozen scientific expectations from the ACCEPTED seal (brief section
# "POSITIVE NONREGRESSION").  Used for the recompute-vs-expected check.
EXPECTED: Dict = {
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

# The 11 negative gate-injection tests required by the brief (each mutates
# one input of fail_closed_gate and must produce seal=false / status!=PASS).
NEGATIVE_INJECTIONS: List[Dict] = [
    {"field": "frontier_nonregression_pass", "value": False, "kind": "gate"},
    {"field": "block_episode_agreement_pass", "value": False, "kind": "gate"},
    {"field": "knee_seal_pass", "value": False, "kind": "gate"},
    {"field": "adjacent_scale_seal_pass", "value": False, "kind": "gate"},
    {"field": "survives_100_edge", "value": False, "kind": "gate"},
    {"field": "survives_75_edge", "value": False, "kind": "gate"},
    {"field": "kelly_used", "value": True, "kind": "auth"},
    {"field": "dd_adaptive_used", "value": True, "kind": "auth"},
    {"field": "production_scale_selected", "value": True, "kind": "auth"},
    {"field": "deployment_authorized", "value": True, "kind": "auth"},
    {"field": "mt5_authorized", "value": True, "kind": "auth"},
]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_hashes() -> Dict:
    """SHA-256 manifest of every frozen input (frontier + sealed artifacts)."""
    frontier_entries = {name: _sha256_file(FRONTIER / name)
                        for name in FRONTIER_INPUT_FILES}
    seal_entries = {name: _sha256_file(SEAL / name) for name in SEAL_INPUT_FILES}
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "sources": {
            "block3_frontier": {
                "dir": str(FRONTIER.relative_to(ROOT)),
                "files": frontier_entries,
            },
            "block3_scale_seal": {
                "dir": str(SEAL.relative_to(ROOT)),
                "files": seal_entries,
            },
        },
        "note": "Frontier + sealed artifacts are frozen inputs; the R1 repair "
                "consumes them read-only and recomputes science for "
                "nonregression verification. No new MC / optimization.",
    }


def _round_range(v, nd: int = 4) -> List[float]:
    return [round(float(x), nd) for x in v]


def _same_range(a, b, tol: float = 1e-4) -> bool:
    """Elementwise equality for numeric ranges and string lists alike."""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        try:
            if abs(float(x) - float(y)) > tol:
                return False
        except (TypeError, ValueError):
            if str(x) != str(y):
                return False
    return True


def recompute_science() -> Dict:
    """Recompute the sealed scientific outputs from the frozen frontier
    inputs via the same pure functions (no new MC)."""
    from capital_routing.capital_scale_seal import (
        adjacent_scale_review, allocation_review, edge_review, heat_review)
    data = load_frontier(FRONTIER)
    fdec = data["decision"]
    edge = edge_review(data["surv"], data["mc"])
    edge_state = edge_seal_state(edge)
    rc = robust_core(data["mc"], data["dep"])
    contract = risk_contract(rc, edge_state)
    adj = adjacent_scale_review(data["mc"], ["A0_50_50", "A1_70_30"],
                                ["H0", "H1-1.00-REJ"])
    alloc = allocation_review(data["mc"], data["hist"], data["surv"])
    heat = heat_review(data["mc"], data["hist"], data["paired"])
    region = region_definition(rc, data["knee"], adj, alloc, heat,
                               edge_state, fdec, BASE_COMMIT)
    return {
        "region": region,
        "contract": contract,
        "edge_state": edge_state,
        "knee_band": region["knee_band"],
    }


def nonregression_check(recomputed: Dict) -> Dict:
    """Compare recomputed science against the SEALED artifact and the frozen
    brief expectations.  Scientific outputs must be unchanged by the repair."""
    region, contract, edge_state = (recomputed["region"],
                                    recomputed["contract"],
                                    recomputed["edge_state"])
    sealed_dec = json.loads((SEAL / "CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json")
                            .read_text(encoding="utf-8"))
    values = {
        "conservative_scale_band": region["scale_bands"]["CONSERVATIVE"],
        "robust_core_scale_band": region["scale_bands"]["ROBUST_CORE"],
        "aggressive_scale_band": region["scale_bands"]["AGGRESSIVE"],
        "stress_scale_band": region["scale_bands"]["STRESS_ONLY"],
        "knee_band": region["knee_band"],
        "allowed_allocations": region["allowed_allocations"],
        "operating_heat": region["operating_heat_reference"],
        "preferred_allocation":
            region["preferred_research_default"]["allocation"],
        "preferred_heat":
            region["preferred_research_default"]["heat_architecture"],
        "preferred_f_total_pct":
            region["preferred_research_default"]["f_total_pct"],
        "robust_core_median_cagr_range": _round_range(
            contract["median_cagr_range"]),
        "robust_core_p95_dd_range": _round_range(contract["p95_max_dd_range"]),
        "robust_core_p_dd_ge_10_range": _round_range(
            contract["P_dd_ge_10_range"]),
        "robust_core_p_dd_ge_15_range": _round_range(
            contract["P_dd_ge_15_range"]),
        "survives_100_edge": edge_state["survives_100"],
        "survives_75_edge": edge_state["survives_75"],
        "survives_50_edge": edge_state["survives_50"],
        "survives_25_edge": edge_state["survives_25"],
    }
    sealed_map = {
        "conservative_scale_band": "conservative_scale_band",
        "robust_core_scale_band": "robust_core_scale_band",
        "aggressive_scale_band": "aggressive_scale_band",
        "stress_scale_band": "stress_scale_band",
        "knee_band": None,  # not a sealed decision field; compared to expected
        "allowed_allocations": "allowed_allocations",
        "operating_heat": None,
        "preferred_allocation": None,
        "preferred_heat": None,
        "preferred_f_total_pct": None,
        "robust_core_median_cagr_range": "robust_core_median_cagr_range",
        "robust_core_p95_dd_range": "robust_core_p95_dd_range",
        "robust_core_p_dd_ge_10_range": "robust_core_p_dd_ge_10_range",
        "robust_core_p_dd_ge_15_range": "robust_core_p_dd_ge_15_range",
        "survives_100_edge": "survives_100_edge",
        "survives_75_edge": "survives_75_edge",
        "survives_50_edge": "survives_50_edge",
        "survives_25_edge": "survives_25_edge",
    }
    fields = []
    all_ok = True
    for field, value in values.items():
        expected = EXPECTED[field]
        sealed_field = sealed_map[field]
        sealed_val = sealed_dec.get(sealed_field) if sealed_field else None
        m_exp = (value == expected if not isinstance(value, list)
                 else _same_range(value, expected))
        m_seal = True
        if sealed_field is not None:
            if sealed_val is None:
                m_seal = False
            elif isinstance(value, list):
                m_seal = _same_range(value, sealed_val)
            else:
                m_seal = bool(value) == bool(sealed_val)
        ok = m_exp and m_seal
        all_ok = all_ok and ok
        fields.append({
            "field": field,
            "recomputed": value,
            "sealed": sealed_val,
            "expected": expected,
            "matches_expected": bool(m_exp),
            "matches_sealed": bool(m_seal),
            "pass": bool(ok),
        })
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "nonregression_pass": bool(all_ok),
        "n_fields": len(fields),
        "fields": fields,
        "note": "Scientific outputs recomputed from the frozen frontier "
                "inputs via the same pure functions and compared to the "
                "sealed artifacts and the frozen brief expectations. The R1 "
                "repair changes ONLY decision/governance mechanics.",
    }


def gate_test() -> Dict:
    """Positive + 11 negative injections through fail_closed_gate.  The
    negative tests exercise the decision gate directly (not the artifact)."""
    from capital_routing.capital_scale_seal import (
        PROHIBITED_AUTH_FIELDS, REQUIRED_GATE_FIELDS)
    gates = {name: True for name, _ in REQUIRED_GATE_FIELDS}
    auths = {name: False for name, _ in PROHIBITED_AUTH_FIELDS}
    positive = fail_closed_gate(gates, auths)
    neg_rows = []
    for inj in NEGATIVE_INJECTIONS:
        field, value = inj["field"], inj["value"]
        if inj["kind"] == "gate":
            g = dict(gates)
            g[field] = value
            r = fail_closed_gate(g, auths)
            expect_failure = field in r["seal_gate_failures"]
        else:
            a = dict(auths)
            a[field] = value
            r = fail_closed_gate(gates, a)
            expect_failure = field in r["authorization_invariants_failed"]
        neg_rows.append({
            "injection": f"{field}={value}",
            "kind": inj["kind"],
            "block3_scale_seal_pass": r["block3_scale_seal_pass"],
            "status": r["status"],
            "seal_gate_failures": r["seal_gate_failures"],
            "authorization_invariants_failed": r[
                "authorization_invariants_failed"],
            "fail_closed": (not r["block3_scale_seal_pass"])
                           and r["status"] != "PASS",
            "expected_failure_recorded": bool(expect_failure),
        })
    all_fail_closed = all(row["fail_closed"] for row in neg_rows) \
        and positive["block3_scale_seal_pass"] is True \
        and positive["status"] == "PASS"
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "positive_control": {
            "block3_scale_seal_pass": positive["block3_scale_seal_pass"],
            "status": positive["status"],
            "seal_gate_failures": positive["seal_gate_failures"],
        },
        "negative_tests": neg_rows,
        "all_negative_tests_fail_closed": bool(all_fail_closed),
    }


def build_r1_decision(recomputed: Dict) -> Dict:
    """The repaired decision: identical scientific content, fail-closed
    governance (status derived, nonregression required, gate reasons)."""
    region, contract, edge_state = (recomputed["region"],
                                    recomputed["contract"],
                                    recomputed["edge_state"])
    return build_scale_seal_decision(
        base_commit=BASE_COMMIT,
        checkpoint=CHECKPOINT,
        frontier_nonregression_pass=region["frontier_nonregression_pass"],
        block_episode_agreement_pass=region["block_episode_agreement_pass"],
        knee_seal_pass=region["knee_seal_pass"],
        adjacent_scale_seal_pass=region["adjacent_scale_seal"]["pass"],
        survives_100_edge=edge_state["survives_100"],
        survives_75_edge=edge_state["survives_75"],
        survives_50_edge=edge_state["survives_50"],
        survives_25_edge=edge_state["survives_25"],
        kelly_used=False,
        dd_adaptive_used=False,
        production_scale_selected=False,
        deployment_authorized=False,
        mt5_authorized=False,
        scale_bands=region["scale_bands"],
        allowed_allocations=region["allowed_allocations"],
        diagnostic_only_allocations=region["diagnostic_only_allocations"],
        heat_architecture_status="H1_OPTIONAL_SAFETY_LAYER_RETAINED",
        preferred_research_default=region["preferred_research_default"],
        robust_core_median_cagr_range=_round_range(
            contract["median_cagr_range"]),
        robust_core_p95_dd_range=_round_range(contract["p95_max_dd_range"]),
        robust_core_p_dd_ge_10_range=_round_range(
            contract["P_dd_ge_10_range"]),
        robust_core_p_dd_ge_15_range=_round_range(
            contract["P_dd_ge_15_range"]),
        next_checkpoint_recommended=region["next_checkpoint_recommended"],
    )


def _protocol_md() -> str:
    return f"""# CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE -- Protocol

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Authoritative base:** {BASE_COMMIT} (CR-RISK-BLOCK-III-SCALE-SEAL -- ACCEPTED)
**Type:** GOVERNANCE REPAIR -- NO new MC, NO frontier change, NO science change.

## Mission
Perform ONLY a fail-closed truth-gate repair of the final decision/governance
mechanics.  The scientific result is FROZEN and ACCEPTED:

- CONSERVATIVE 0.25-0.50 / ROBUST CORE 0.75-1.00 / AGGRESSIVE 1.50-2.00 /
  STRESS ONLY 3.00
- KNEE 1.00-1.50
- ALLOWED A0_50_50, A1_70_30; DIAGNOSTIC ONLY A2_100_0_A, A3_0_100_B
- OPERATING HEAT H1-1.00-REJ
- PREFERRED RESEARCH DEFAULT A1_70_30 / H1-1.00-REJ / f=1.00 (NOT production)
- ROBUST CORE RISK CONTRACT: median CAGR 0.4814-0.7038; p95 DD 0.0474-0.0829;
  P(DD>=10) 0.0-0.0072; P(DD>=15) 0.0
- Edge: 100/75/50 SURVIVE; 25 DOES NOT SURVIVE (alpha-loss boundary)

## Defect 1 -- nonregression not in the final pass expression
block3_scale_seal_pass = true ONLY IF ALL required gates pass:
frontier_nonregression_pass AND block_episode_agreement_pass AND
knee_seal_pass AND adjacent_scale_seal_pass AND survives_100_edge AND
survives_75_edge AND no prohibited authorization state.

## Defect 2 -- status hardcoded
status is DERIVED: PASS iff block3_scale_seal_pass == true; otherwise FAIL
with explicit reasons in status_reason / seal_gate_failures.

## Fail-closed authorization invariants
No PASS while any of kelly_used, dd_adaptive_used, production_scale_selected,
deployment_authorized, mt5_authorized is true.  All remain FALSE.

## Gate reasons
Every decision carries machine-readable seal_gate_failures and
seal_gate_passes lists (failures = [] on PASS).

## Negative tests (exercise the gate, not the artifact)
1 frontier_nonregression=false -> seal=false -> status != PASS
2 block_episode_agreement=false -> seal=false
3 knee_seal=false -> seal=false
4 adjacent_scale_seal=false -> seal=false
5 survives_100=false -> seal=false
6 survives_75=false -> seal=false
7 kelly_used=true -> seal=false
8 dd_adaptive_used=true -> seal=false
9 production_scale_selected=true -> seal=false
10 deployment_authorized=true -> seal=false
11 mt5_authorized=true -> seal=false

## Positive nonregression
On the frozen inputs the scientific outputs must reproduce EXACTLY the
ACCEPTED values listed above (recomputed from the frozen frontier artifacts
via the same pure functions, compared to the sealed artifacts AND the frozen
brief expectations).

## Not done here
No re-run of MC, no band/allocation/heat/f_total/edge-logic changes, no
preferred-default change, no Kelly, no DD adaptation, no deployment, no MT5,
no execution translation.
"""


def _report_md(nonreg: Dict, gate: Dict, decision: Dict) -> str:
    L: List[str] = []
    A = L.append
    A(f"# CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE -- Report")
    A("")
    A(f"- **Status:** {decision['status']}  ")
    A(f"- **block3_scale_seal_pass:** {decision['block3_scale_seal_pass']}  ")
    A(f"- **Base commit:** {BASE_COMMIT}  ")
    A("")
    A("## Defects repaired")
    A("")
    A("- **Defect 1:** `block3_scale_seal_pass` now requires "
      "`frontier_nonregression_pass` AND every other required gate "
      "(block/episode agreement, knee seal, adjacent-scale seal, 100% edge, "
      "75% edge) plus no prohibited authorization state.  ")
    A("- **Defect 2:** `status` is DERIVED from the pass -- never hardcoded.  ")
    A("- **Fail-closed auth invariants:** kelly / DD-adaptive / production / "
      "deployment / MT5 all remain FALSE and any TRUE blocks PASS.  ")
    A("- **Gate reasons:** `seal_gate_failures` / `seal_gate_passes` are "
      "explicit machine-readable fields.  ")
    A("")
    A("## Positive nonregression (science frozen)")
    A("")
    A(f"- nonregression_pass = {nonreg['nonregression_pass']} "
      f"({nonreg['n_fields']} fields recomputed from the frozen frontier "
      f"inputs and compared to the sealed artifacts AND the frozen brief "
      f"expectations)  ")
    A("")
    for f in nonreg["fields"]:
        A(f"- {f['field']}: recomputed {f['recomputed']} "
          f"| expected {f['expected']} | matches_expected "
          f"{f['matches_expected']} | matches_sealed {f['matches_sealed']}  ")
    A("")
    A("## Gate test (11 negative injections)")
    A("")
    A(f"- positive control: pass={gate['positive_control']['block3_scale_seal_pass']} "
      f"status={gate['positive_control']['status']}  ")
    A(f"- all negative tests fail closed = "
      f"{gate['all_negative_tests_fail_closed']}  ")
    A("")
    A("| injection | seal pass | status | recorded failure |")
    A("|---|---|---|---|")
    for t in gate["negative_tests"]:
        failures = (t["seal_gate_failures"] or t["authorization_invariants_failed"])
        A(f"| {t['injection']} | {t['block3_scale_seal_pass']} | "
          f"{t['status']} | {failures} |")
    A("")
    A("## Decision")
    A("")
    A(f"- status: {decision['status']}  ")
    A(f"- seal_gate_failures: {decision['seal_gate_failures']}  ")
    A(f"- seal_gate_passes: {decision['seal_gate_passes']}  ")
    A(f"- bands: CONSERVATIVE {decision['conservative_scale_band']} / "
      f"ROBUST CORE {decision['robust_core_scale_band']} / AGGRESSIVE "
      f"{decision['aggressive_scale_band']} / STRESS "
      f"{decision['stress_scale_band']}  ")
    A(f"- allowed allocations: {decision['allowed_allocations']}  ")
    A(f"- operating heat: {decision['heat_architecture_status']}  ")
    A(f"- preferred research default: "
      f"{decision['preferred_research_default']}  ")
    A(f"- robust core contract: CAGR {decision['robust_core_median_cagr_range']} "
      f"| p95 DD {decision['robust_core_p95_dd_range']} | "
      f"P(DD>=10) {decision['robust_core_p_dd_ge_10_range']} | "
      f"P(DD>=15) {decision['robust_core_p_dd_ge_15_range']}  ")
    A("")
    A("## Authorizations (all locked)  ")
    A("")
    A(f"- kelly_used={decision['kelly_used']} / "
      f"dd_adaptive_used={decision['dd_adaptive_used']} / "
      f"production_scale_selected={decision['production_scale_selected']} / "
      f"deployment_authorized={decision['deployment_authorized']} / "
      f"mt5_authorized={decision['mt5_authorized']}  ")
    A(f"- next_checkpoint_recommended: "
      f"{decision['next_checkpoint_recommended']} "
      f"(authorized: {decision['next_checkpoint_authorized']})  ")
    return "\n".join(L)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Protocol + input hashes (frozen before results are written)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_PROTOCOL.md").write_text(
        _protocol_md(), encoding="utf-8")
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_INPUT_HASHES.json").write_text(
        json.dumps(input_hashes(), indent=2), encoding="utf-8")

    # 2. Positive nonregression: recompute science from frozen frontier
    recomputed = recompute_science()
    nonreg = nonregression_check(recomputed)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_NONREGRESSION.json").write_text(
        json.dumps(nonreg, indent=2), encoding="utf-8")

    # 3. Gate test: positive control + 11 negative injections
    gate = gate_test()
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_GATE_TEST.json").write_text(
        json.dumps(gate, indent=2), encoding="utf-8")

    # 4. Repaired decision (identical science, fail-closed governance)
    decision = build_r1_decision(recomputed)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    # 5. Report
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_R1_REPORT.md").write_text(
        _report_md(nonreg, gate, decision), encoding="utf-8")

    print(f"[seal-r1] base {BASE_COMMIT}")
    print(f"[seal-r1] nonregression_pass={nonreg['nonregression_pass']}")
    print(f"[seal-r1] all_negative_tests_fail_closed="
          f"{gate['all_negative_tests_fail_closed']}")
    print(f"[seal-r1] status={decision['status']} "
          f"pass={decision['block3_scale_seal_pass']}")
    print(f"[seal-r1] seal_gate_failures={decision['seal_gate_failures']}")
    print("[seal-r1] DONE")


if __name__ == "__main__":
    main()
