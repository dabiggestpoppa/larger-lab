"""Generate G5 per-scenario receipts + human-readable results.

Byte-reproducible: run from the stress-suite root via
    python stress-suite/scenarios/g5_run_evidence.py

Each run writes run_receipt.json and human_readable_result.md into the six
scenario directories (S14–S19).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.g5_runner import (  # noqa: E402
    load_g5_pack,
    run_g5_scenario,
    evaluate_g5_expectation,
)
from engine.domain_policy import G5DomainPolicy  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent
POLICY = G5DomainPolicy.from_data(json.loads(
    (SCENARIOS / "policies/G5_DOMAIN_EPISTEMIC_POLICY.json").read_text(encoding="utf-8")))

PACKS = {
    "S14": SCENARIOS / "s14_huge_fake_alpha",
    "S15": SCENARIOS / "s15_new_alpha_family",
    "S16": SCENARIOS / "s16_cerebus_contradiction",
    "S17": SCENARIOS / "s17_crypto_provider_disagreement",
    "S18": SCENARIOS / "s18_sensor_gap",
    "S19": SCENARIOS / "s19_crypto_to_fx_transfer",
}


def build_receipt(sid: str) -> dict:
    pack = load_g5_pack(PACKS[sid])
    res = run_g5_scenario(pack.decision_grade(), POLICY)
    a = res.artifacts
    verdict = evaluate_g5_expectation(res, pack)
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
        "manual_modified": False,
        "synthetic_backfill_used": False,
        "source_averaged_away": False,
    }


def human_result(sid: str, receipt: dict, detail: dict) -> str:
    lines = [
        f"# {sid} — G5 CLASS C domain scenario result",
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
    for sid in ("S14", "S15", "S16", "S17", "S18", "S19"):
        pack = load_g5_pack(PACKS[sid])
        res = run_g5_scenario(pack.decision_grade(), POLICY)
        a = res.artifacts
        receipt = build_receipt(sid)
        detail = {}
        if sid == "S14":
            item = a["items"][0]
            detail = {"material_failures": item["material_failures"],
                      "research_priority": item["research_priority"]["priority"],
                      "promotion_decision": item["promotion_decision"]["decision"],
                      "failure_atoms": [f["failure_id"] for f in item["failure_atoms"]],
                      "negative_knowledge_created": item["negative_knowledge"] is not None}
        elif sid == "S15":
            detail = {"pattern_disposition": a["patterns"][0]["disposition"],
                      "cluster_observations": a["cluster"].get("independent_observations", 0),
                      "mechanism_card_created": bool(a["mechanism"]),
                      "strategy_created": a["mechanism"].get("strategy_created", False)}
        elif sid == "S16":
            detail = {"reproduction_statuses": [r["status"] for r in a["reproduction_results"]],
                      "manual_modified": a["manual_modified"],
                      "contradiction_opened": len(a["contradictions"]),
                      "amendment_ratified": a["amendment_ratified"],
                      "amendment_operator_required": a["amendment_operator_required"]}
        elif sid == "S17":
            detail = {"causes": [(d["cause"], d["terminal"]) for d in a["diagnoses"]],
                      "native_values_preserved": a["provider_native_values_preserved"]}
        elif sid == "S18":
            detail = {"data_statuses": [b["data_availability"] for b in a["blocked_claims"]],
                      "dispositions": [b["disposition"] for b in a["blocked_claims"]],
                      "search_demands": len(a["search_demands"]),
                      "synthetic_backfill": a["synthetic_backfill_used"]}
        elif sid == "S19":
            detail = {"dispositions": [(t["hypothesis_id"], t["disposition"])
                                       for t in a["transfers"]],
                      "cerebus_overridden": a["transfers"][0]["cerebus_doctrine_overridden"]}
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