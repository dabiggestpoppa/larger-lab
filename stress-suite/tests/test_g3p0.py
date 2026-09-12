"""G3-P0 — independence semantics + receipt lineage preflight (before S06).

P0-A: model/runtime independence is NEVER inferred from source independence.
P0-B: no ambiguous shared_* booleans — explicit distinct counts + concentrations.
P0-C: receipts distinguish artifacts head from externally verified branch head;
      no self-referential terminal-commit pinning.
"""
import pytest

from engine.cognitive_ecology import (
    ConsensusRecord,
    DependencyGraph,
    EcologyFacts,
    PROFILE_SCHEMA_VERSION,
    ReviewerIndependenceProfile,
    UNKNOWN,
    independent_confirmation_satisfied,
    receipt_lineage,
    RECEIPT_LINEAGE_SEMANTICS,
)


def _profile(reviewer_id, **kw):
    base = dict(
        reviewer_id=reviewer_id, model_family="FAM_A", provider="PROV_A",
        runtime_lineage="RT_A", sources=["S_A"], retrieval_bundle="BUNDLE_A",
        prompt_context="CTX_A", prior_conclusion_exposure=False,
        implementation_path="IMP_A", experiment_design_origin="DESIGN_A",
        allocator="PO", visible_information="EVIDENCE_ONLY",
        conclusion="CLAIM",
    )
    base.update(kw)
    return ReviewerIndependenceProfile.from_reviewer_fixture(base)


def _facts(profiles, consequence="HIGH"):
    graph = DependencyGraph.build(profiles)
    consensus = ConsensusRecord.build("C", profiles, graph)
    return EcologyFacts.from_consensus(consensus, consequence_class=consequence)


# --------------------------------------------------------------------------- #
# P0-A — axes never inferred from one another
# --------------------------------------------------------------------------- #
def test_source_diversity_does_not_imply_model_diversity():
    """Different sources, SAME model family / runtime: model independence must
    NOT be inferred from source diversity."""
    profiles = [
        _profile("A1", sources=["S_1"]),
        _profile("A2", sources=["S_2"]),
        _profile("A3", sources=["S_3"]),
    ]
    facts = _facts(profiles)
    assert facts.distinct_source_lineages == 3
    assert facts.distinct_model_family_count == 1          # NOT inferred from sources
    assert facts.distinct_runtime_lineage_count == 1
    assert independent_confirmation_satisfied(facts) is False


def test_model_diversity_does_not_imply_source_diversity():
    """Different model families, SAME source: source independence must NOT be
    inferred from model diversity."""
    profiles = [
        _profile("B1", model_family="FAM_X", runtime_lineage="RT_X"),
        _profile("B2", model_family="FAM_Y", runtime_lineage="RT_Y"),
        _profile("B3", model_family="FAM_Z", runtime_lineage="RT_Z"),
    ]
    facts = _facts(profiles)
    assert facts.distinct_source_lineages == 1             # shared source
    assert facts.distinct_model_family_count == 3
    assert facts.distinct_runtime_lineage_count == 3
    assert independent_confirmation_satisfied(facts) is False


def test_model_family_and_runtime_are_separate_axes():
    """Same model family, different runtimes: runtime diversity exists, model
    diversity does not — and the sufficiency guard requires BOTH source and
    model/runtime diversity."""
    profiles = [
        _profile("C1", model_family="FAM_M", runtime_lineage="RT_1", sources=["S_1"]),
        _profile("C2", model_family="FAM_M", runtime_lineage="RT_2", sources=["S_2"]),
    ]
    facts = _facts(profiles)
    assert facts.distinct_model_family_count == 1
    assert facts.distinct_runtime_lineage_count == 2
    assert facts.distinct_source_lineages == 2


def test_both_axes_needed_for_independent_confirmation():
    """Sufficiency requires >=2 source lineages AND >=2 model-or-runtime
    lineages: either axis alone is insufficient."""
    only_sources = _facts([
        _profile("D1", sources=["S_1"]), _profile("D2", sources=["S_2"]),
    ])
    only_models = _facts([
        _profile("E1", model_family="FAM_X", runtime_lineage="RT_X", sources=["S_A"]),
        _profile("E2", model_family="FAM_Y", runtime_lineage="RT_Y", sources=["S_A"]),
    ])
    assert independent_confirmation_satisfied(only_sources) is False
    assert independent_confirmation_satisfied(only_models) is False
    both = _facts([
        _profile("F1", model_family="FAM_X", runtime_lineage="RT_X", sources=["S_1"],
                 fresh_context=True),
        _profile("F2", model_family="FAM_Y", runtime_lineage="RT_Y", sources=["S_2"],
                 fresh_context=True),
    ])
    assert independent_confirmation_satisfied(both) is True


# --------------------------------------------------------------------------- #
# P0-B — unambiguous allocator/retrieval quantities and concentrations
# --------------------------------------------------------------------------- #
def test_allocator_semantics_unambiguous():
    profiles = [
        _profile("G1", allocator="PO"),
        _profile("G2", allocator="PO"),
        _profile("G3", allocator="GOVERNOR"),
    ]
    facts = _facts(profiles)
    assert facts.distinct_allocator_count == 2
    # single allocator is one value, not an ambiguous boolean


def test_retrieval_semantics_unambiguous():
    profiles = [
        _profile("H1", retrieval_bundle="BUNDLE_1"),
        _profile("H2", retrieval_bundle="BUNDLE_2"),
        _profile("H3", retrieval_bundle="BUNDLE_3"),
    ]
    facts = _facts(profiles)
    assert facts.distinct_retrieval_bundle_count == 3
    consensus = ConsensusRecord.build("C", profiles, DependencyGraph.build(profiles))
    assert consensus.retrieval_bundle_concentration == pytest.approx(1 / 3)


def test_unknown_axis_stays_unknown_and_never_independent():
    """A reviewer with NO model_family declared is UNKNOWN on that axis; the
    profile must not infer a model family, and unknown contributes nothing."""
    p = ReviewerIndependenceProfile.from_reviewer_fixture({
        "reviewer_id": "U1", "sources": ["S_A", "S_B"], "conclusion": "X",
    })
    assert p.model_family == UNKNOWN
    assert p.known_axis("model_family") is False
    assert p.known_axis("source_lineage") is True
    # source diversity present but model/runtime unknown -> still insufficient
    profiles = [p, _profile("U2", sources=["S_C"], model_family="FAM_Z",
                            runtime_lineage="RT_Z")]
    facts = _facts(profiles)
    assert facts.distinct_source_lineages == 3
    assert facts.distinct_model_family_count == 1          # only U2's known family
    assert facts.unknown_dimension_count >= 1
    assert independent_confirmation_satisfied(facts) is False


def test_profile_is_versioned_separately_from_g2r_lineage():
    """The G3 profile is versioned (2.0.0) and distinct from the frozen G2R
    LineageSummary surface; P0-B semantics live here, not by mutating G2R."""
    assert PROFILE_SCHEMA_VERSION == "2.0.0"
    # no ambiguous shared_allocator / shared_retrieval booleans in the profile
    assert "shared_allocator" not in ReviewerIndependenceProfile.__dataclass_fields__
    assert "shared_retrieval" not in ReviewerIndependenceProfile.__dataclass_fields__


# --------------------------------------------------------------------------- #
# P0-C — receipt SHA lineage semantics
# --------------------------------------------------------------------------- #
def test_receipt_distinguishes_artifacts_head_from_verified_branch_head():
    lineage = receipt_lineage("abc123", "def456")
    assert lineage["artifacts_head_sha"] == "abc123"
    assert lineage["receipt_content_parent_sha"] == "def456"
    # externally verified branch head is NOT self-contained in the receipt
    assert lineage["externally_verified_branch_head"] is None
    assert lineage["self_pin_attempted"] is False
    assert "artifacts_head_sha" in RECEIPT_LINEAGE_SEMANTICS
    assert "externally_verified_branch_head" in RECEIPT_LINEAGE_SEMANTICS


def test_no_self_referential_terminal_pin_in_g3_receipt_semantics():
    assert "receipt_terminal_commit" not in RECEIPT_LINEAGE_SEMANTICS


def test_p0_axes_distinct_in_pairwise_graph():
    """Pairwise overlap distinguishes source vs model axes explicitly.

    G3R-08 legacy upgrade: overlaps were booleans (True/False). A boolean False
    could be misread as either "distinct" OR "unknown". Replaced with the
    tri-state SAME / DIFFERENT / UNKNOWN — P1 and P2 use disjoint known sources
    (DIFFERENT) while sharing model family and runtime (SAME).
    Old assertion: overlaps["source_lineage"] is False.
    Why invalid: unknown-vs-known could not be represented; missing metadata
    must never mint favorable independence.
    Replacement: tri-state relation asserted below.
    """
    profiles = [
        _profile("P1", sources=["S_1"], model_family="FAM_M", runtime_lineage="RT_1"),
        _profile("P2", sources=["S_2"], model_family="FAM_M", runtime_lineage="RT_1"),
    ]
    graph = DependencyGraph.build(profiles)
    pair = graph.pairs[0]
    assert pair.overlaps["source_lineage"] == "DIFFERENT"
    assert pair.overlaps["model_family"] == "SAME"
    assert pair.overlaps["runtime_lineage"] == "SAME"
