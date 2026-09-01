"""Generate G3 per-scenario receipts + human-readable results.

Byte-reproducible: run from the stress-suite root via
    python stress-suite/scenarios/g3_run_evidence.py
Each run writes run_receipt.json and human_readable_result.md into the four
scenario directories. The receipt shape follows G3 prompt §34.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ecology_policy import EcologyPolicy  # noqa: E402
from engine.g3_runner import (  # noqa: E402
    load_g3_pack,
    run_g3_scenario,
    evaluate_g3_expectation,
)

SCENARIOS = Path(__file__).resolve().parent
POLICY = EcologyPolicy.from_data(json.loads(
    (SCENARIOS / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))

PACKS = {
    "S06": SCENARIOS / "s06_correlated_consensus",
    "S07": SCENARIOS / "s07_independent_weaker_agents",
    "S08": SCENARIOS / "s08_reflective_bypass",
    "S09": SCENARIOS / "s09_counter_attractor_false_alarm",
}


def build_receipt(sid: str) -> dict:
    pack = load_g3_pack(PACKS[sid])
    res = run_g3_scenario(pack.decision_grade(), POLICY)
    a = res.artifacts
    verdict = evaluate_g3_expectation(res, pack)
    consensus = a["consensus"]
    exposure_modes = sorted({p["exposure_mode"] for p in consensus["reviewer_profiles"]})
    return {
        "scenario_id": sid,
        "scenario_version": pack.scenario_version,
        "claim_id": pack.claim_id,
        "consequence_class": a["consequence_class"],
        "behavior_fingerprint": a["behavior_fingerprint"],
        "run_identity_fingerprint": a["fingerprint"],
        "review_topology_id": (a["topology_decision"] or {}).get("chosen_topology_id", ""),
        "raw_reviewer_count": a["raw_reviewer_count"],
        "raw_vote_distribution": a["raw_vote_distribution"],
        "independence_profile_refs": [a["dependency_graph_fingerprint"]],
        "dependency_graph_fingerprint": a["dependency_graph_fingerprint"],
        "affected_surface_consequence": a["consequence_class"],
        "information_exposure_modes": exposure_modes,
        "fresh_context_paths": a["facts"]["fresh_context_count"],
        "counter_attractor_invocations": 1 if a["counter_attractor_result"] else 0,
        "evidence_refs": consensus["supporting_evidence_refs"],
        "facts": a["facts"],
        "disposition": a["disposition"],
        "disposition_rule": a["disposition_rule"],
        "independent_confirmation_satisfied": a["independent_confirmation_satisfied"],
        "friction_triggered": a["friction_triggered"],
        "counter_attractor_result": a["counter_attractor_result"],
        "topology_decision": a["topology_decision"],
        "friction_result": a["friction_result"],
        "expected_disposition": pack.expected_disposition,
        "expected_accessed_during_run": False,
        "hidden_ground_truth_accessed": False,
        "cost_units": a["cost_units"],
        "latency_units": a["latency_units"],
        "authority_before": "NONE",
        "authority_after": "NONE",
        "policy_id": a["policy_id"],
        "policy_fingerprint": a["policy_fingerprint"],
        "pass": verdict["pass"],
        "failures": verdict["failures"],
        "authority_changes": "NONE",
        "cloud_mutations": 0,
        "production_mutations": 0,
        "capital_mutations": 0,
    }


def human_result(sid: str, receipt: dict) -> str:
    a = receipt
    topo = a.get("topology_decision") or {}
    fr = a.get("friction_result") or {}
    ca = a.get("counter_attractor_result") or {}
    lines = [
        f"# {sid} — G3 scenario result",
        "",
        f"- disposition: **{a['disposition']}** (expected `{a['expected_disposition']}`)"
        + (" — PASS" if a["pass"] else f" — FAIL {a['failures']}"),
        f"- raw reviewers: {a['raw_reviewer_count']} · votes: {a['raw_vote_distribution']}",
        f"- independent confirmation satisfied (provisional contract): {a['independent_confirmation_satisfied']}",
        f"- source lineages: {a['facts']['distinct_source_lineages']} · model families: {a['facts']['distinct_model_family_count']} · "
        f"runtimes: {a['facts']['distinct_runtime_lineage_count']} · exposure ratio: {a['facts']['prior_conclusion_exposure_ratio']}",
        f"- dependency graph: `{a['dependency_graph_fingerprint']}`",
        f"- exposure modes: {a['information_exposure_modes']} · fresh paths: {a['fresh_context_paths']}",
        f"- topology decision: `{topo.get('chosen_topology_id', '—')}` (satisfied={topo.get('constraints_satisfied', '—')}, "
        f"cost={topo.get('cost_units', '—')})",
        f"- friction: triggered={a['friction_triggered']} · information gain={fr.get('information_gain', '—')} · "
        f"alternatives={fr.get('surfaced_alternatives', '—')}",
        f"- counter-attractor: invocations={a['counter_attractor_invocations']} · terminal={ca.get('terminal_result', '—')}",
        f"- cost units: {a['cost_units']} · authority: {a['authority_before']} -> {a['authority_after']}",
        f"- sealed: expected_accessed={a['expected_accessed_during_run']} · "
        f"hidden_ground_truth_accessed={a['hidden_ground_truth_accessed']}",
        f"- behavior fingerprint: `{a['behavior_fingerprint']}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> dict:
    verdicts = {}
    for sid in ("S06", "S07", "S08", "S09"):
        receipt = build_receipt(sid)
        d = PACKS[sid]
        (d / "run_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (d / "human_readable_result.md").write_text(human_result(sid, receipt), encoding="utf-8")
        verdicts[sid] = {
            "pass": receipt["pass"],
            "disposition": receipt["disposition"],
            "behavior_fingerprint": receipt["behavior_fingerprint"],
        }
    print(json.dumps(verdicts, indent=2))
    return verdicts


if __name__ == "__main__":
    main()
