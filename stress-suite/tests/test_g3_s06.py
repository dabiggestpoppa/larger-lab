"""S06 — Ten Correlated Agents Agree (CONSENSUS CAPTURE).

10 synthetic reviewers, same model family / provider / retrieval bundle /
source lineage / prior-conclusion exposure, different reviewer IDs, 10/10 raw
agreement. The institution must keep raw consensus as an observation while
recognizing ONE correlated topology — never ten independent confirmations.
"""
import json
from pathlib import Path

import pytest

from engine.cognitive_ecology import DependencyGraph
from engine.ecology_policy import EcologyPolicy
from engine.g3_runner import load_g3_pack, run_g3_scenario

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACK_DIR = ROOT / "s06_correlated_consensus"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


def _run(pack=None):
    pack = pack or load_g3_pack(PACK_DIR)
    return run_g3_scenario(pack.decision_grade(), POLICY)


def _dupe_pack(count):
    """A pack with `count` duplicates of the same correlated reviewer."""
    base = load_g3_pack(PACK_DIR)
    one = base.reviewers[0]
    base.reviewers = [dict(one, reviewer_id=f"R_{i}", evidence_refs=[f"E_{i}"])
                      for i in range(count)]
    return base


# --------------------------------------------------------------------------- #
def test_ten_same_lineage_votes_are_ten_raw_votes_one_correlated_topology():
    res = _run()
    a = res.artifacts
    assert a["raw_reviewer_count"] == 10
    assert a["raw_vote_distribution"] == {"ALPHA": 10}          # raw consensus kept
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["facts"]["distinct_model_family_count"] == 1
    assert a["facts"]["distinct_runtime_lineage_count"] == 1
    assert a["facts"]["source_concentration"] == 1.0
    # every reviewer pair is fully correlated -> one tight basin
    assert a["fully_correlated_pairs"] == 45
    assert a["consensus"]["disposition"] == "" or a["disposition"] != ""


def test_high_consequence_refuses_promotion_under_monoculture():
    res = _run()
    a = res.artifacts
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert a["independent_confirmation_satisfied"] is False
    assert a["disposition"] != "INDEPENDENTLY_SUPPORTED"


def test_independent_path_is_requested_but_not_fabricated():
    """The system requests a meaningfully independent path (friction triggered,
    fresh reviewer allocated) without pretending confirmation already exists."""
    res = _run()
    a = res.artifacts
    assert a["friction_triggered"] is True
    fr = a["friction_result"]
    assert fr["triggered"] is True
    assert fr["budget_used"] >= 1
    assert fr["fresh_context_reviewers"]                       # a fresh path was allocated
    assert fr["information_gain"] is False                     # pending, not completed
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"      # still not confirmed


def test_prior_conclusion_exposure_remains_visible():
    res = _run()
    a = res.artifacts
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 1.0
    assert a["consensus"]["prior_conclusion_exposure_count"] == 10


def test_100_duplicates_do_not_become_100_independent_confirmations():
    res = _run(_dupe_pack(100))
    a = res.artifacts
    assert a["raw_reviewer_count"] == 100
    assert a["raw_vote_distribution"] == {"ALPHA": 100}
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["independent_confirmation_satisfied"] is False
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"      # no 10x scaling
    assert a["fully_correlated_pairs"] == 100 * 99 // 2


def test_reviewer_renaming_changes_no_behavior():
    pack = load_g3_pack(PACK_DIR)
    renamed = load_g3_pack(PACK_DIR)
    renamed.reviewers = [dict(r, reviewer_id=f"NEW_{i}")
                         for i, r in enumerate(renamed.reviewers)]
    r1 = _run(pack)
    r2 = _run(renamed)
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]
    assert r1.artifacts["disposition"] == r2.artifacts["disposition"]
    assert r1.artifacts["raw_vote_distribution"] == r2.artifacts["raw_vote_distribution"]


def test_same_conclusion_diversified_paths_changes_independence_profile():
    """Identical votes, but diversified source/model/retrieval paths with fresh
    context and no shared exposure -> the independence profile must change."""
    pack = load_g3_pack(PACK_DIR)
    pack.reviewers = []
    for i in range(8):
        pack.reviewers.append(dict(
            reviewer_id=f"RV_{i}", role="reviewer",
            model_family=f"FAM_{i % 4}", provider=f"PROV_{i % 4}",
            runtime_lineage=f"RT_{i % 3}", sources=[f"S_{i % 3}"],
            retrieval_bundle=f"BUNDLE_{i % 3}", prompt_context=f"CTX_{i % 4}",
            prior_conclusion_exposure="FALSE", implementation_path=f"IMP_{i % 4}",
            experiment_design_origin=f"DESIGN_{i % 4}", allocator="GOVERNOR",
            visible_information="BLIND" if i % 2 else "EVIDENCE_ONLY",
            fresh_context=(i % 2 == 0), conclusion="ALPHA", confidence="MEDIUM",
            evidence_refs=[f"E_D{i}"], cost_units=3, latency_units=1,
            capability_tier="ADEQUATE"))
    pack.independent_replication_count = 2
    res = _run(pack)
    a = res.artifacts
    assert a["raw_vote_distribution"] == {"ALPHA": 8}          # same votes
    assert a["facts"]["distinct_source_lineages"] == 3
    assert a["facts"]["distinct_model_family_count"] == 4
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 0.0
    assert a["independent_confirmation_satisfied"] is True
    assert a["disposition"] == "INDEPENDENTLY_SUPPORTED"       # profile changed


def test_model_name_change_with_shared_runtime_lineage_gives_no_false_independence():
    """Metamorphic D: change model NAMES while preserving the actual shared
    runtime lineage -> distinct model-family count rises but the shared runtime
    and single source still fail the sufficiency guard."""
    pack = load_g3_pack(PACK_DIR)
    pack.reviewers = [dict(r, model_family=f"RENAMED_{i}", provider=f"PROV_{i}")
                      for i, r in enumerate(pack.reviewers)]
    res = _run(pack)
    a = res.artifacts
    assert a["facts"]["distinct_model_family_count"] == 10     # renamed
    assert a["facts"]["distinct_runtime_lineage_count"] == 1   # actual shared lineage
    assert a["facts"]["distinct_source_lineages"] == 1
    assert a["independent_confirmation_satisfied"] is False    # no false independence
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"


def test_raw_consensus_retained_not_discarded():
    res = _run()
    a = res.artifacts
    assert a["consensus"]["raw_vote_distribution"] == {"ALPHA": 10}
    assert a["consensus"]["raw_reviewer_count"] == 10
    assert a["consensus"]["disagreement_retained"] == ["ALPHA"]
    assert a["consensus"]["supporting_evidence_refs"]  # evidence refs preserved
