"""S09 — Counter-Attractor False Alarm (CONTRARIAN ATTRACTOR / NOVELTY THEATER).

A strong, independently-supported consensus triggers a BOUNDED counter-attractor
challenge. No discriminating contradiction exists -> the review terminates
NO_CHANGE. Nobody is rewarded for manufacturing dissent; exhausting the budget
never reduces evidence status arbitrarily; identical evidence never loops.
"""
import json
from pathlib import Path

from engine.ecology_policy import EcologyPolicy
from engine.g3_runner import load_g3_pack, run_g3_scenario

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACK_DIR = ROOT / "s09_counter_attractor_false_alarm"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


def _run(pack=None):
    pack = pack or load_g3_pack(PACK_DIR)
    return run_g3_scenario(pack.decision_grade(), POLICY)


# --------------------------------------------------------------------------- #
def test_strong_independent_consensus_triggers_bounded_counter_attractor():
    res = _run()
    a = res.artifacts
    assert a["independent_confirmation_satisfied"] is True
    assert a["counter_attractor_rule"] == "eco.counter_attractor.strong_consensus"
    ca = a["counter_attractor_result"]
    assert ca["trigger_reason"]
    assert ca["review_budget"] > 0


def test_counter_attractor_returns_no_change():
    res = _run()
    ca = res.artifacts["counter_attractor_result"]
    assert ca["terminal_result"] == "NO_CHANGE"
    assert ca["discriminating_contradiction_found"] is False


def test_challenge_budget_terminates():
    res = _run()
    ca = res.artifacts["counter_attractor_result"]
    assert ca["budget_used"] == ca["review_budget"]
    assert ca["budget_used"] > 0
    assert res.artifacts["cost_units"] == ca["cost_units"] > 0


def test_no_synthetic_dissent_manufactured():
    """All challenge methods find no discriminating contradiction; nothing
    invents a CHALLENGE_SUPPORTED outcome."""
    res = _run()
    ca = res.artifacts["counter_attractor_result"]
    assert ca["terminal_result"] != "CHALLENGE_SUPPORTED"
    assert ca["discriminating_contradiction_found"] is False
    findings = json.loads((PACK_DIR / "counter_attractor.json").read_text(encoding="utf-8"))
    assert all(not f["discriminating_contradiction"] for f in findings["findings"])


def test_no_confidence_penalty_for_honest_no_change():
    """Exhausting the challenge budget without a contradiction does not reduce
    the claim's evidence status: disposition stays INDEPENDENTLY_SUPPORTED."""
    res = _run()
    a = res.artifacts
    assert a["counter_attractor_result"]["terminal_result"] == "NO_CHANGE"
    assert a["disposition"] == "INDEPENDENTLY_SUPPORTED"
    assert a["independent_confirmation_satisfied"] is True


def test_repeated_invocation_is_deterministic_and_does_not_loop():
    r1 = _run()
    r2 = _run()
    assert r1.artifacts["counter_attractor_result"] == r2.artifacts["counter_attractor_result"]
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]
    # a single counter-attractor invocation, not an endless contrarian loop
    assert r1.artifacts["health_record"]["counter_attractor_frequency"] == 1


def test_no_transformation_without_discriminating_contradiction():
    res = _run()
    a = res.artifacts
    assert a["disposition"] == "INDEPENDENTLY_SUPPORTED"
    assert "TRANSFORMATION" not in a["disposition"]
    assert a["authority_before"] == "NONE" and a["authority_after"] == "NONE"


def test_friction_not_triggered_for_well_supported_consensus():
    """No shared-context exposure -> no epistemic friction; the counter-attractor
    alone is invoked and closes NO_CHANGE."""
    res = _run()
    a = res.artifacts
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 0.0
    assert a["friction_triggered"] is False
    assert a["friction_result"] is None or a["friction_result"]["triggered"] is False


def test_challenge_with_discriminating_contradiction_supports_change():
    """If a challenge DID find discriminating evidence, the terminal changes to
    CHALLENGE_SUPPORTED — the machinery is honest, not hardcoded to NO_CHANGE."""
    pack = load_g3_pack(PACK_DIR)
    pack.counter_attractor_findings = [
        {"method": "fresh_context", "evidence_id": "CA_1", "discriminating_contradiction": True},
    ]
    res = _run(pack)
    ca = res.artifacts["counter_attractor_result"]
    assert ca["terminal_result"] == "CHALLENGE_SUPPORTED"
    assert ca["discriminating_contradiction_found"] is True
