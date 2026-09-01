"""G3 cross-scenario audits + independence-dimension swaps + sealing.

* S06 vs S09: both strong consensus — provenance/topology distinguishes
  correlated consensus (needs independent review) from independently-supported
  consensus (counter-attractor closes NO_CHANGE).
* S06 vs S07: raw model quality is not institutional evidence quality.
* S08 vs S09: friction is useful when context correlation hides alternatives,
  and is not mandatory permanent contrarianism.
* §29: change ONE dependency dimension at a time; record which matter under
  the PROVISIONAL contract (without universalizing the weights).
* Sealing: wrong expected verdict / hidden-truth flip / renames never alter
  execution.
* Static guards: the shared policy carries no scenario literals.
"""
import json
from pathlib import Path

import pytest

from engine.cognitive_ecology import ReviewerIndependenceProfile
from engine.ecology_policy import EcologyPolicy
from engine.g3_runner import load_g3_pack, run_g3_scenario

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


def _run(pack):
    return run_g3_scenario(pack.decision_grade(), POLICY)


# --------------------------------------------------------------------------- #
# S06 vs S09 — correlated consensus vs independently-supported consensus
# --------------------------------------------------------------------------- #
def test_s06_and_s09_both_have_strong_consensus():
    s06 = _run(load_g3_pack(ROOT / "s06_correlated_consensus")).artifacts
    s09 = _run(load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")).artifacts
    assert s06["raw_vote_distribution"] == {"ALPHA": 10}
    assert s09["raw_vote_distribution"] == {"REGIME_A": 8}
    assert s06["consensus"]["raw_reviewer_count"] >= 5
    assert s09["consensus"]["raw_reviewer_count"] >= 5


def test_s06_vs_s09_distinguished_by_provenance_not_consensus():
    """Same strong-consensus SHAPE; the difference is provenance/topology."""
    s06 = _run(load_g3_pack(ROOT / "s06_correlated_consensus")).artifacts
    s09 = _run(load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")).artifacts
    # S06: correlated -> needs independent review
    assert s06["independent_confirmation_satisfied"] is False
    assert s06["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert s06["friction_triggered"] is True
    # S09: already independently supported -> counter-attractor closes NO_CHANGE
    assert s09["independent_confirmation_satisfied"] is True
    assert s09["disposition"] == "INDEPENDENTLY_SUPPORTED"
    assert s09["counter_attractor_result"]["terminal_result"] == "NO_CHANGE"
    assert s09["friction_triggered"] is False


def test_s06_vs_s09_behavior_fingerprints_differ():
    s06 = _run(load_g3_pack(ROOT / "s06_correlated_consensus")).artifacts
    s09 = _run(load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")).artifacts
    assert s06["behavior_fingerprint"] != s09["behavior_fingerprint"]


def test_s06_vs_s07_raw_quality_is_not_evidence_quality():
    """S07's HIGH-capability monoculture must not be treated as institutional
    evidence quality; routing to the differentiated topology is the point."""
    s07 = _run(load_g3_pack(ROOT / "s07_independent_weaker_agents")).artifacts
    assert s07["topology_decision"]["chosen_topology_id"] == "TOPO_B_DIFFERENTIATED"
    assert s07["disposition"] == "REQUIRES_INDEPENDENT_REVIEW"
    assert "TOPO_A_MONOCULTURE" not in s07["topology_decision"]["admissible_alternatives"]


def test_s08_vs_s09_friction_is_not_permanent_contrarianism():
    """Friction fires where context correlation hides alternatives (S08) and is
    absent where consensus is independently supported (S09)."""
    s08 = _run(load_g3_pack(ROOT / "s08_reflective_bypass")).artifacts
    s09 = _run(load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")).artifacts
    assert s08["friction_triggered"] is True
    assert s08["friction_result"]["information_gain"] is True
    assert s09["friction_triggered"] is False
    assert s09["friction_result"] is None or s09["friction_result"]["triggered"] is False


# --------------------------------------------------------------------------- #
# §29 independence-dimension swaps (one axis at a time)
# --------------------------------------------------------------------------- #
def _swapped_reviewers(count=4, model=None, runtime=None, sources=None,
                       retrieval=None, exposure=True, fresh=False,
                       visible="EVIDENCE_ONLY", design=None, allocator=None):
    """One-at-a-time axis swapper. Scalar args apply to every reviewer; a list
    arg supplies the per-reviewer value (so a swap can vary exactly one axis)."""
    def per(arg, i, default):
        """A list of length == count is per-index; a 1-element list is a scalar
        shared by every reviewer (unambiguous by length)."""
        if isinstance(arg, list) and len(arg) == count:
            return arg[i]
        if isinstance(arg, list) and len(arg) == 1:
            return arg[0]
        return arg if arg is not None else default(i)
    out = []
    for i in range(count):
        src = per(sources, i, lambda i: ["S_1"])
        if isinstance(src, str):            # scalar source -> single-source list
            src = [src]
        out.append({
            "reviewer_id": f"SW_{i}", "role": "reviewer",
            "model_family": per(model, i, lambda i: f"FAM_M{i % 2}"),
            "provider": "PROV_P",
            "runtime_lineage": per(runtime, i, lambda i: f"RT_A{i % 2}"),
            "sources": src,
            "retrieval_bundle": per(retrieval, i, lambda i: "BUNDLE_1"),
            "prompt_context": "CTX_A",
            "prior_conclusion_exposure": "TRUE" if exposure else "FALSE",
            "implementation_path": "IMP_A",
            "experiment_design_origin": per(design, i, lambda i: "DESIGN_A"),
            "allocator": allocator or "PO", "visible_information": visible,
            "fresh_context": fresh, "conclusion": "CLAIM", "confidence": "HIGH",
            "evidence_refs": [f"E_SW{i}"], "cost_units": 2, "latency_units": 1,
            "capability_tier": "HIGH",
        })
    return out


def _swap_run(**kw):
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = _swapped_reviewers(**kw)
    pack.friction_reviewers = None
    pack.friction_contract = None
    return _run(pack).artifacts


def test_swap_same_model_different_sources_does_not_confirm():
    a = _swap_run(model="FAM_M", runtime="RT_A",
                  sources=[f"S_{i}" for i in range(4)])
    assert a["facts"]["distinct_source_lineages"] == 4
    assert a["facts"]["distinct_model_family_count"] == 1
    assert a["independent_confirmation_satisfied"] is False


def test_swap_different_model_same_source_does_not_confirm():
    a = _swap_run(model=[f"FAM_{i}" for i in range(4)], sources=["S_1"])
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["facts"]["distinct_model_family_count"] == 4
    assert a["independent_confirmation_satisfied"] is False


def test_swap_different_model_and_sources_but_shared_exposure_fails():
    a = _swap_run(model=[f"FAM_{i}" for i in range(4)][:4],
                  sources=[f"S_{i}" for i in range(4)], exposure=True)
    assert a["facts"]["distinct_source_lineages"] == 4
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 1.0
    assert a["independent_confirmation_satisfied"] is False   # exposure blocks


def test_swap_different_everything_fresh_passes():
    a = _swap_run(model=[f"FAM_{i}" for i in range(4)][:4],
                  runtime=[f"RT_{i}" for i in range(4)],
                  sources=[f"S_{i}" for i in range(4)],
                  retrieval=[f"B_{i}" for i in range(4)],
                  exposure=False, fresh=True, visible="BLIND")
    assert a["independent_confirmation_satisfied"] is True
    assert a["disposition"] == "INDEPENDENTLY_SUPPORTED"


def test_swap_same_everything_blind_context_still_fails():
    """Blind context alone does not diversify sources/models: monoculture."""
    a = _swap_run(model="FAM_M", runtime="RT_A", sources=["S_1"], exposure=False,
                  fresh=True, visible="BLIND")
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["facts"]["distinct_model_family_count"] == 1
    assert a["independent_confirmation_satisfied"] is False


def test_swap_same_sources_independent_design_still_fails():
    a = _swap_run(model=[f"FAM_{i}" for i in range(4)],
                  sources=["S_1"], exposure=False,
                  design=[f"DESIGN_{i}" for i in range(4)])
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["facts"]["distinct_experiment_design_count"] == 4
    assert a["independent_confirmation_satisfied"] is False


def test_swap_allocator_alone_does_not_change_sufficiency():
    """Allocator is observable provenance, not a sufficiency axis under this
    PROVISIONAL contract; swapping it alone leaves the disposition unchanged."""
    base = _swap_run(exposure=False, fresh=True)
    other = _swap_run(exposure=False, fresh=True, allocator="GOVERNOR")
    assert base["disposition"] == other["disposition"]
    assert base["independent_confirmation_satisfied"] == other["independent_confirmation_satisfied"]
    assert base["facts"]["distinct_allocator_count"] == 1
    assert other["facts"]["distinct_allocator_count"] == 1


# --------------------------------------------------------------------------- #
# PO / CON-02 observation — allocation visible but never evidentiary
# --------------------------------------------------------------------------- #
def test_allocation_provenance_visible_in_artifacts():
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    a = _run(pack).artifacts
    ap = a["allocation_provenance"]
    assert ap["reviewer_selector"] == "PO"
    assert ap["source_bundle_selector"] == "PO"
    assert ap["fresh_context_decider"] == "GOVERNOR"
    assert "claim_id" in ap


def test_allocator_cannot_convert_allocation_into_evidence_strength():
    """PO selects every reviewer, but PO's allocation does not change the
    independence verdict: monoculture is still SUPPORTED_BUT_CORRELATED."""
    a = _swap_run(exposure=True)
    assert a["allocation_provenance"]["reviewer_selector"] == "PO"  # provenance kept
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert a["independent_confirmation_satisfied"] is False


def test_reviewer_lying_about_lineage_registry_truth_wins():
    """CON-03 observation: a reviewer payload cannot change its provenance to
    look independent; the profile reads the sealed fixture fields only."""
    liar = ReviewerIndependenceProfile.from_reviewer_fixture({
        "reviewer_id": "LIAR", "model_family": "FAM_M", "sources": ["S_A"],
        "prior_conclusion_exposure": "TRUE", "conclusion": "CLAIM",
        # bogus claims that must be ignored
        "claimed_sources": ["S_X", "S_Y"], "claimed_model_family": "INDEPENDENT",
        "claimed_independence": "TOTAL",
    })
    assert liar.source_lineages == ("S_A",)
    assert liar.model_family == "FAM_M"
    assert liar.axis_value("source_lineage") == "S_A"
    assert liar.prior_conclusion_exposure is True


# --------------------------------------------------------------------------- #
# Sealing metamorphics
# --------------------------------------------------------------------------- #
def test_hidden_ground_truth_flip_does_not_alter_actions():
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    flipped = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    flipped.hidden_ground_truth = {"true_regime": "GAMMA",
                                   "no_discriminating_contradiction_exists": False}
    r1 = _run(pack)
    r2 = _run(flipped)
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]
    assert r1.artifacts["counter_attractor_result"] == r2.artifacts["counter_attractor_result"]
    assert r1.artifacts["hidden_ground_truth_accessed"] is False


def test_wrong_expected_disposition_does_not_alter_actions():
    pack = load_g3_pack(ROOT / "s07_independent_weaker_agents")
    wrong = load_g3_pack(ROOT / "s07_independent_weaker_agents")
    wrong.expected_disposition = "INDEPENDENTLY_SUPPORTED"     # deliberately wrong
    r1 = _run(pack)
    r2 = _run(wrong)
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]
    assert r1.artifacts["topology_decision"] == r2.artifacts["topology_decision"]
    assert r2.artifacts["expected_disposition_accessed"] is False


def test_scenario_rename_preserves_behavior_fingerprint_all_scenarios():
    for d in ("s06_correlated_consensus", "s07_independent_weaker_agents",
              "s08_reflective_bypass", "s09_counter_attractor_false_alarm"):
        pack = load_g3_pack(ROOT / d)
        renamed = load_g3_pack(ROOT / d)
        renamed.scenario_id = "RANDOM_NAME_937"
        r1 = _run(pack)
        r2 = _run(renamed)
        assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]
        assert r1.artifacts["fingerprint"] != r2.artifacts["fingerprint"]  # run identity keeps id


# --------------------------------------------------------------------------- #
# Static guards — one shared policy, no scenario literals
# --------------------------------------------------------------------------- #
def test_shared_policy_has_no_scenario_literals():
    text = (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")
    for token in ("S06", "S07", "S08", "S09", "special_reviewer", "expected_conclusion",
                  "R_S06", "TOPO_A", "ALPHA", "REGIME_A", "ELEGANT_A", "R_BLIND"):
        assert token not in text, f"scenario literal {token!r} leaked into the shared policy"


def test_shared_policy_condition_fields_are_generic_only():
    data = json.loads((ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8"))
    for rule in data["rules"]:
        for field in rule["when"]:
            assert field not in ("scenario_id", "reviewer_id", "claim_id"), \
                f"non-generic condition field {field!r} in rule {rule['rule_id']}"


def test_all_four_scenarios_run_under_the_same_policy_object():
    for d in ("s06_correlated_consensus", "s07_independent_weaker_agents",
              "s08_reflective_bypass", "s09_counter_attractor_false_alarm"):
        pack = load_g3_pack(ROOT / d)
        res = _run(pack)
        assert res.artifacts["policy_id"] == "G3_COGNITIVE_ECOLOGY_POLICY"
        assert res.artifacts["policy_version"] == "V1"


def test_health_record_is_a_vector_not_a_scalar():
    a = _run(load_g3_pack(ROOT / "s06_correlated_consensus")).artifacts
    health = a["health_record"]
    assert "HEALTH_SCORE" not in health
    assert "source_concentration" in health
    assert "prior_conclusion_exposure_ratio" in health
    assert "counter_attractor_frequency" in health
    assert "information_gain" in health
