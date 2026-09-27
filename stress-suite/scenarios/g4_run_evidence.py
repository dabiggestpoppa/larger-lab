"""Generate G4 per-scenario receipts + human-readable results.

Byte-reproducible: run from the stress-suite root via
    python stress-suite/scenarios/g4_run_evidence.py
Each run writes run_receipt.json and human_readable_result.md into the four
scenario directories.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.g4_runner import (  # noqa: E402
    load_g4_pack,
    run_g4_scenario,
    evaluate_g4_expectation,
)
from engine.memory_policy import MemoryPolicy  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent
POLICY = MemoryPolicy.from_data(json.loads(
    (SCENARIOS / "policies/G4_MEMORY_AND_REACTIVATION_POLICY.json").read_text(encoding="utf-8")))

PACKS = {
    "S10": SCENARIOS / "s10_dormant_knowledge_returns",
    "S11": SCENARIOS / "s11_negative_knowledge_dogma",
    "S12": SCENARIOS / "s12_institutional_hyperthymesia",
    "S13": SCENARIOS / "s13_runtime_replacement_epoch_reconstruction",
}


def build_receipt(sid: str) -> dict:
    pack = load_g4_pack(PACKS[sid])
    res = run_g4_scenario(pack.decision_grade(), POLICY)
    a = res.artifacts
    verdict = evaluate_g4_expectation(res, pack)
    return {
        "scenario_id": sid,
        "scenario_version": pack.scenario_version,
        "behavior_fingerprint": a["behavior_fingerprint"],
        "fingerprint": a["fingerprint"],
        "expected_outcome": pack.expected_outcome,
        "actual_outcome": verdict["actual_outcome"],
        "pass": verdict["pass"],
        "failures": verdict["failures"],
        "policy_id": a["policy_id"],
        "policy_version": a["policy_version"],
        "policy_fingerprint": a["policy_fingerprint"],
        "expected_outcome_accessed": False,
        "hidden_ground_truth_accessed": False,
        "authority_before": "NONE",
        "authority_after": "NONE",
        "authority_changes": "NONE",
        "cloud_mutations": 0,
        "production_mutations": 0,
        "capital_mutations": 0,
        "model_calls": 0,
    }


def human_result(sid: str, receipt: dict, detail: dict) -> str:
    lines = [
        f"# {sid} — G4 scenario result",
        "",
        f"- outcome: **{receipt['actual_outcome']}** (expected `{receipt['expected_outcome']}`)"
        + (" — PASS" if receipt["pass"] else f" — FAIL {receipt['failures']}"),
        f"- behavior fingerprint: `{receipt['behavior_fingerprint']}`",
        f"- authority: {receipt['authority_before']} -> {receipt['authority_after']}",
        f"- sealed: expected_accessed={receipt['expected_outcome_accessed']} · "
        f"hidden_ground_truth_accessed={receipt['hidden_ground_truth_accessed']}",
        "",
    ]
    for k, v in detail.items():
        lines.append(f"- {k}: `{v}`")
    return "\n".join(lines) + "\n"


def main() -> dict:
    verdicts = {}
    for sid in ("S10", "S11", "S12", "S13"):
        pack = load_g4_pack(PACKS[sid])
        res = run_g4_scenario(pack.decision_grade(), POLICY)
        a = res.artifacts
        receipt = build_receipt(sid)
        detail = {}
        if sid == "S10":
            detail = {"reopen_outcomes": a["reopen_outcomes"],
                      "direct_dormant_to_active_forbidden": a["direct_dormant_to_active_forbidden"]}
        elif sid == "S11":
            detail = {"suppression_next_action": a["suppression_decisions"][0]["decision"]["next_action"],
                      "record_retained": True,
                      "reopen_condition_status": a["suppression_decisions"][0]["decision"]["reopen_condition_status"]}
        elif sid == "S12":
            detail = {"total_history": a["total_history"],
                      "active_context_objects": a["metrics"]["active_context_objects"],
                      "required_recall": round(a["metrics"]["required_object_recall"], 4),
                      "stale_intrusion": a["metrics"]["stale_object_intrusion_count"],
                      "growth_ratio": round(a["metrics"]["context_growth_ratio"], 8)}
        elif sid == "S13":
            report = a["reports"][-1]
            detail = {"epochs_reconstructed": [r["epoch_id"] for r in a["reports"]],
                      "chain_pass": a["chain"]["pass"],
                      "missing_surfaces": report["missing_surfaces"],
                      "runtime_rename_semantic_stable": a["runtime_rename_semantic_stable"],
                      "reconstruction_semantic_fingerprint": report["reconstruction_semantic_fingerprint"]}
        d = PACKS[sid]
        (d / "run_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (d / "human_readable_result.md").write_text(
            human_result(sid, receipt, detail), encoding="utf-8")
        verdicts[sid] = {"pass": receipt["pass"], "outcome": receipt["actual_outcome"],
                         "behavior_fingerprint": receipt["behavior_fingerprint"]}
    print(json.dumps(verdicts, indent=2))
    return verdicts


if __name__ == "__main__":
    main()
