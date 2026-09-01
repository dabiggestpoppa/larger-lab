"""S08 — Reflective Bypass (RAPID RECURSIVE CONSENSUS).

A shared-context review converges rapidly on an elegant interpretation. For a
high-consequence claim the policy triggers bounded epistemic friction; a
fresh-context (blind) reviewer surfaces an alternative that vanishes when the
prior conclusion leaks. Friction creates information value; disagreement never
triggers transformation by itself.
"""
import json
from pathlib import Path

from engine.ecology_policy import EcologyPolicy
from engine.g3_runner import load_g3_pack, run_g3_scenario

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACK_DIR = ROOT / "s08_reflective_bypass"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


def _run(pack=None):
    pack = pack or load_g3_pack(PACK_DIR)
    return run_g3_scenario(pack.decision_grade(), POLICY)


def _leaked_pack():
    """Control: the fresh-context reviewer receives the original conclusion
    prematurely (PRIOR_CONCLUSION_VISIBLE instead of BLIND)."""
    pack = load_g3_pack(PACK_DIR)
    pack.friction_reviewers = [
        dict(r, visible_information="PRIOR_CONCLUSION_VISIBLE")
        for r in pack.friction_reviewers
    ]
    return pack


# --------------------------------------------------------------------------- #
def test_shared_context_creates_high_exposure_topology():
    res = _run()
    a = res.artifacts
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 1.0
    assert a["consensus"]["raw_vote_distribution"] == {"ELEGANT_A": 5}
    assert a["facts"]["source_concentration"] == 1.0
    assert a["facts"]["model_family_concentration"] == 1.0


def test_high_consequence_review_triggers_friction():
    res = _run()
    a = res.artifacts
    assert a["friction_triggered"] is True
    assert a["friction_rule"] == "eco.friction.context_correlation"
    assert a["friction_result"]["budget_used"] >= 1


def test_fresh_context_reviewer_is_genuinely_blind():
    res = _run()
    fr = res.artifacts["friction_result"]
    assert fr["triggered"] is True
    assert "R_BLIND_S08" in fr["fresh_context_reviewers"]
    # the fixture's fresh reviewer is BLIND with fresh context and no shared
    # source bundle with the panel (exposure recorded as provenance)
    friction_data = json.loads((PACK_DIR / "friction.json").read_text(encoding="utf-8"))
    blind = friction_data["reviewers"][0]
    assert blind["visible_information"] == "BLIND"
    assert blind["fresh_context"] is True
    assert blind["prior_conclusion_exposure"] == "FALSE"
    # the shared-context panel reviewers are all FULL_SHARED_CONTEXT
    assert all(r["visible_information"] == "FULL_SHARED_CONTEXT"
               for r in load_g3_pack(PACK_DIR).reviewers)


def test_blind_path_surfaces_alternative_explanation():
    res = _run()
    fr = res.artifacts["friction_result"]
    assert fr["information_gain"] is True
    assert "ALT_B" in fr["surfaced_alternatives"]
    assert fr["evidence_gap"] is not None


def test_leaked_prior_conclusion_suppresses_alternative_in_control():
    """The membrane matters: when the fresh reviewer sees the original
    conclusion, the alternative disappears in the synthetic fixture."""
    res = _run(_leaked_pack())
    fr = res.artifacts["friction_result"]
    assert fr["information_gain"] is False
    assert fr["surfaced_alternatives"] == ()
    assert fr["evidence_gap"] is None


def test_system_preserves_both_hypotheses_and_gap():
    res = _run()
    a = res.artifacts
    # original consensus retained (5/5 ELEGANT_A)
    assert a["consensus"]["raw_vote_distribution"] == {"ELEGANT_A": 5}
    # alternative preserved in the friction record
    assert "ALT_B" in a["friction_result"]["surfaced_alternatives"]
    # discriminating evidence gap generated
    assert a["friction_result"]["evidence_gap"]["question"]
    assert a["friction_result"]["evidence_gap"]["reopen_if"]


def test_friction_budget_is_bounded():
    res = _run()
    fr = res.artifacts["friction_result"]
    contract = json.loads((PACK_DIR / "friction.json").read_text(encoding="utf-8"))
    budget = contract["contract"]["consequence_classes"]["HIGH"]["budget"]
    assert fr["budget_used"] <= budget
    assert fr["cost_units"] <= budget * 5


def test_no_automatic_transformation_from_disagreement():
    """The alternative does NOT trigger a phase transformation: disposition
    stays a correlated-support epistemic state; nothing moves to a
    transformation outcome."""
    res = _run()
    a = res.artifacts
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert "TRANSFORMATION" not in a["disposition"]
    assert a["authority_before"] == "NONE" and a["authority_after"] == "NONE"


def test_scenario_rename_preserves_behavior():
    pack = load_g3_pack(PACK_DIR)
    renamed = load_g3_pack(PACK_DIR)
    renamed.scenario_id = "RANDOM_NAME_937"
    r1 = _run(pack)
    r2 = _run(renamed)
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]


def test_wrong_expected_disposition_does_not_alter_execution():
    pack = load_g3_pack(PACK_DIR)
    pack.expected_disposition = "INDEPENDENTLY_SUPPORTED"    # deliberately wrong
    res = _run(pack)
    # execution is sealed: the wrong expectation changes nothing about behavior
    assert res.artifacts["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert res.artifacts["friction_result"]["information_gain"] is True
