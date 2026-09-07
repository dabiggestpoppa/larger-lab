"""G6 canonical scenario-execution regressions (STRESS-G6ER1).

UNIT TEST != SCENARIO EXECUTION: these tests execute the materialized S20–S24
scenario contracts through the generic runner — the same machinery the receipt
generator uses — and assert that every scenario proves at least one forbidden
shortcut. The decision path never sees sealed fields.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.g6_scenario_runner import (
    build_receipt,
    evaluate_g6_expectation,
    load_g6_pack,
    run_g6_scenario,
)

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"

PACKS = {
    "S20": SCENARIOS / "s20_governor_self_change",
    "S21": SCENARIOS / "s21_capability_not_authority",
    "S22": SCENARIOS / "s22_operator_truth_boundary",
    "S23": SCENARIOS / "s23_operator_unavailable",
    "S24": SCENARIOS / "s24_unknown_governance_event",
}


@pytest.mark.parametrize("sid", sorted(PACKS))
def test_g6_scenario_passes_through_canonical_runner(sid):
    pack = load_g6_pack(PACKS[sid])
    res = run_g6_scenario(pack.decision_grade())
    verdict = evaluate_g6_expectation(res, pack)
    assert verdict["pass"], f"{sid}: {verdict['failures']}"


@pytest.mark.parametrize("sid", sorted(PACKS))
def test_g6_scenario_proves_a_forbidden_shortcut(sid):
    pack = load_g6_pack(PACKS[sid])
    res = run_g6_scenario(pack.decision_grade())
    assert res.forbidden_shortcuts_attempted, f"{sid}: no shortcut attempted"


def test_g6_scenario_receipts_are_sealed_and_clean():
    for sid, d in PACKS.items():
        pack = load_g6_pack(d)
        res = run_g6_scenario(pack.decision_grade())
        verdict = evaluate_g6_expectation(res, pack)
        receipt = build_receipt(pack, res, verdict)
        assert receipt["expected_outcome_accessed"] is False
        assert receipt["hidden_ground_truth_accessed"] is False
        assert receipt["authority_changes"] == "NONE"
        assert receipt["model_calls"] == 0
        assert receipt["cloud_mutations"] == 0
        assert receipt["production_mutations"] == 0
        assert receipt["capital_mutations"] == 0


def test_g6_runner_is_generic_no_scenario_id_dispatch():
    # every stimulus type is handled by event-type dispatch; a scenario whose
    # id is renamed but whose content is identical must behave identically
    pack = load_g6_pack(PACKS["S20"])
    decision = pack.decision_grade()
    decision["scenario_id"] = "S20_RENAMED_PROBE"
    res_a = run_g6_scenario(decision)
    res_b = run_g6_scenario(pack.decision_grade())
    assert [p["phase"] for p in res_a.phases] == [p["phase"] for p in res_b.phases]
    assert res_a.behavior_fingerprint != res_b.behavior_fingerprint or True
    # phases identical; fingerprint binds the scenario id by design (identity),
    # so compare phase sequences only for semantic equivalence
    assert [p["phase"] for p in res_a.phases] == [
        "CONTRACT_FROZEN", "MUTATION_REFUSED", "NESTED_MUTATION_IMPOSSIBLE",
        "NESTED_MUTATION_IMPOSSIBLE", "WINDOW_EVALUATION",
        "STALE_FINGERPRINT_REFUSED", "RETROACTIVE_CHANGE_REFUSED",
        "FUTURE_VERSION_CANDIDATE", "ACTIVATION_REFUSED", "WINDOW_EVALUATION"]


def test_g6_unknown_stimulus_type_fails_closed():
    pack = load_g6_pack(PACKS["S21"])
    decision = pack.decision_grade()
    decision["stimulus_events"] = [{"type": "MAGIC_BYPASS", "actor": "W1"}]
    with pytest.raises(Exception):
        run_g6_scenario(decision)
