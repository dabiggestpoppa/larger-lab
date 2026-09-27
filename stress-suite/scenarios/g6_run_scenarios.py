"""Generate G6 per-scenario receipts + human-readable results.

Byte-reproducible; run from the stress-suite root:
    python scenarios/g6_run_scenarios.py
Writes run_receipt.json and human_readable_result.md into each S20–S24
scenario directory. Sealed fields are never read by the decision path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.g6_scenario_runner import (  # noqa: E402
    build_receipt,
    evaluate_g6_expectation,
    human_result,
    load_g6_pack,
    run_g6_scenario,
)

SCENARIOS = Path(__file__).resolve().parent

PACKS = {
    "S20": SCENARIOS / "s20_governor_self_change",
    "S21": SCENARIOS / "s21_capability_not_authority",
    "S22": SCENARIOS / "s22_operator_truth_boundary",
    "S23": SCENARIOS / "s23_operator_unavailable",
    "S24": SCENARIOS / "s24_unknown_governance_event",
}


def main() -> dict:
    verdicts = {}
    for sid, d in PACKS.items():
        pack = load_g6_pack(d)
        res = run_g6_scenario(pack.decision_grade())
        verdict = evaluate_g6_expectation(res, pack)
        receipt = build_receipt(pack, res, verdict)
        (d / "run_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (d / "human_readable_result.md").write_text(
            human_result(receipt), encoding="utf-8")
        verdicts[sid] = {"pass": receipt["pass"],
                         "outcome": receipt["actual_outcome"],
                         "behavior_fingerprint": receipt["behavior_fingerprint"],
                         "forbidden_shortcuts_refused":
                             receipt["forbidden_shortcuts_refused"]}
    print(json.dumps(verdicts, indent=2))
    return verdicts


if __name__ == "__main__":
    main()
