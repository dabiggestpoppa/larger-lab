"""G3R2 — provenance-closure / unknown-semantics adversarial hardening.

Governing principle: UNKNOWN IS NOT INDEPENDENT. UNVERIFIED IS NOT VERIFIED.
A PLANNED REVIEWER IS NOT EVIDENCE. A SELF-CLAIM IS NOT ITS OWN PROVENANCE
AUTHORITY.

Each G3R2 defect gets adversarial tests that FAIL on the pre-G3R2 behavior:

G3R2-01  missing registry entry fails closed (all independence axes UNKNOWN)
G3R2-02  no silent self-registration; explicit provenance modes
G3R2-03  topology/friction secondary surfaces use the same provenance authority
G3R2-04  max single-source prevalence detects partial-bundle shared dependency
G3R2-05  UNKNOWN prior exposure is not FALSE (true/false/unknown counts)
G3R2-06  tri-state UNKNOWN survives into decision-grade facts (coverage)
G3R2-07  counter-attractor/friction method vocabularies fail closed
G3R2-08  counter-attractor stops at the FIRST consumed discriminating contradiction
G3R2-09  unique epistemic paths, not summed labels
G3R2-10  topology capability provenance (UNVERIFIED fails closed)

Plus the mandatory cross-case matrix (CASE F–K). All local, deterministic,
model-free. All prior G3/G3R tests remain valid.
"""
import json
from pathlib import Path

import pytest

from engine.cognitive_ecology import (
    UNKNOWN,
    ConsensusRecord,
    DependencyGraph,
    EcologyFacts,
    ReviewerIndependenceProfile,
    ReviewerProvenanceRegistry,
    SyntheticFixtureAuthority,
    collect_epistemic_paths,
    independent_confirmation_satisfied,
)
from engine.ecology_policy import EcologyPolicy
from engine.friction import (
    COUNTER_ATTRACTOR_METHODS,
    FRICTION_METHODS,
    CounterAttractorSpec,
    FrictionContract,
    FrictionTrigger,
    friction_trigger,
    run_counter_attractor,
    run_friction,
)
from engine.g3_runner import load_g3_pack, run_g3_scenario
from engine.review_topology import (
    ReviewTopology,
    TopologyConstraintContract,
    route_review_topology,
)

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _profile(reviewer_id, conclusion="CLAIM", **kw):
    base = dict(
        reviewer_id=reviewer_id, model_family="FAM_A", provider="PROV_A",
        runtime_lineage="RT_A", sources=["S_A"], retrieval_bundle="BUNDLE_A",
        prompt_context="CTX_A", prior_conclusion_exposure=False,
        implementation_path="IMP_A", experiment_design_origin="DESIGN_A",
        allocator="PO", visible_information="EVIDENCE_ONLY",
        conclusion=conclusion,
    )
    base.update(kw)
    return ReviewerIndependenceProfile.from_reviewer_fixture(base)


def _facts(profiles, consequence="HIGH", replication=0):
    graph = DependencyGraph.build(profiles)
    consensus = ConsensusRecord.build("C", profiles, graph)
    return EcologyFacts.from_consensus(
        consensus, consequence_class=consequence,
        independent_replication_count=replication)


def _run(pack):
    return run_g3_scenario(pack.decision_grade(), POLICY)


def _contract(**kw):
    constraints = {"HIGH": {"min_capability": "ADEQUATE", **kw}}
    return TopologyConstraintContract(contract_id="T-C", constraints=constraints)


# --------------------------------------------------------------------------- #
# G3R2-01 — missing registry entry must fail closed
# --------------------------------------------------------------------------- #
def test_missing_registry_model_claim_becomes_unknown():
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", model_family="FAM_CLAIM"))
    assert bound.model_family == UNKNOWN


def test_missing_registry_source_claim_becomes_unknown():
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", sources=["S_CLAIM_A", "S_CLAIM_B"]))
    assert bound.source_lineages == ()


def test_missing_registry_runtime_claim_becomes_unknown():
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", runtime_lineage="RT_CLAIM"))
    assert bound.runtime_lineage == UNKNOWN


def test_missing_registry_retrieval_claim_becomes_unknown():
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", retrieval_bundle="BUNDLE_CLAIM"))
    assert bound.retrieval_bundle == UNKNOWN


def test_missing_registry_blind_claim_not_verified():
    bound, conflicts = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", visible_information="BLIND", fresh_context=True))
    assert bound.exposure_mode == UNKNOWN          # cannot self-declare BLIND
    assert bound.fresh_context is False
    assert any(c.axis == "exposure_mode" for c in conflicts)


def test_missing_registry_independent_design_not_verified():
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(
        _profile("GHOST", independent_design=True))
    assert bound.independently_originated_design is False


def test_unverified_claims_cannot_satisfy_independence():
    """Rich claims against an empty registry produce an all-UNKNOWN profile
    whose facts can never satisfy independent confirmation."""
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind_all([
        _profile(f"R{i}", model_family=f"FAM_{i}", sources=[f"S_{i}"],
                 runtime_lineage=f"RT_{i}") for i in range(4)])
    facts = _facts(list(bound), consequence="HIGH")
    assert facts.distinct_source_lineages == 0
    assert facts.distinct_model_family_count == 0
    assert independent_confirmation_satisfied(facts) is False


# --------------------------------------------------------------------------- #
# G3R2-02 — no silent self-registration; explicit provenance modes
# --------------------------------------------------------------------------- #
def test_default_missing_registry_fails_closed():
    """Default mode is GOVERNED_REGISTRY: without a registry file, S09's rich
    fixture claims must NOT self-register into verified truth."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    pack.provenance_mode = "GOVERNED_REGISTRY"     # explicit default semantics
    pack.registered_provenance = None              # NO registry file
    a = _run(pack).artifacts
    assert a["provenance_mode"] == "GOVERNED_REGISTRY"
    assert a["independent_confirmation_satisfied"] is False
    assert a["disposition"] != "INDEPENDENTLY_SUPPORTED"


def test_explicit_synthetic_fixture_mode_allows_fixture_truth():
    """AUTHORITATIVE_SYNTHETIC_FIXTURE is EXPLICIT in the scenario contract:
    the harness owns the synthetic ground truth, so fixture fields are truth."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    assert pack.provenance_mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE"  # in scenario.json
    a = _run(pack).artifacts
    assert a["independent_confirmation_satisfied"] is True
    assert a["disposition"] == "INDEPENDENTLY_SUPPORTED"


def test_synthetic_fixture_mode_recorded_in_receipt():
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    a = _run(pack).artifacts
    assert a["provenance_mode"] == "AUTHORITATIVE_SYNTHETIC_FIXTURE"
    assert a["synthetic_fixture_authority_used"] is True
    assert a["synthetic_fixture_authority"]["agent_claims_trusted"] is False
    assert a["synthetic_fixture_authority"]["model_calls"] == 0


def test_governed_registry_mode_never_self_registers_claims():
    """Even with registered_provenance=[] the runner must NOT fall back to the
    reviewers as the registry."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    pack.provenance_mode = "GOVERNED_REGISTRY"
    pack.registered_provenance = []
    a = _run(pack).artifacts
    assert a["provenance_mode"] == "GOVERNED_REGISTRY"
    assert a["facts"]["distinct_model_family_count"] == 0
    assert a["provenance_conflicts"] != []          # claims recorded as UNVERIFIED


def test_unknown_provenance_mode_rejected():
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.provenance_mode = "IMAGINED_MODE"
    with pytest.raises(ValueError):
        _run(pack)


# --------------------------------------------------------------------------- #
# G3R2-03 — bind all cognitive surfaces (topology / friction)
# --------------------------------------------------------------------------- #
def test_topology_candidate_fake_model_diversity_fails():
    """Candidates self-declaring different model families with NO registered
    provenance: binding collapses the claims to UNKNOWN — a proposed topology
    cannot become admissible on self-declared diversity."""
    candidates = [_profile(f"FAKE_{i}", model_family=f"FAM_{i}", sources=[f"S_{i}"])
                  for i in range(3)]
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind_all(candidates)
    assert all(p.model_family == UNKNOWN for p in bound)
    topo = ReviewTopology(topology_id="FAKE", purpose="p", consequence_class="HIGH",
                          profiles=tuple(bound), capability_tiers=("HIGH",) * 3,
                          capability_source="UNVERIFIED_CAPABILITY", cost_units=1)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_source_lineages=2,
                                               min_model_or_runtime_lineages=2,
                                               min_fresh_or_independent_design=1))
    assert decision.constraints_satisfied is False


def test_topology_candidate_fake_source_diversity_fails():
    candidates = [_profile(f"FAKE_{i}", sources=[f"S_{i}"]) for i in range(3)]
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind_all(candidates)
    assert all(p.source_lineages == () for p in bound)


def test_topology_candidate_fake_independent_design_fails():
    candidates = [_profile(f"FAKE_{i}", independent_design=True, fresh_context=True)
                  for i in range(3)]
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind_all(candidates)
    assert all(p.independently_originated_design is False for p in bound)
    assert all(p.fresh_context is False for p in bound)
    assert len(collect_epistemic_paths(bound)) == 0     # no qualifying paths


def test_friction_reviewer_fake_blind_status_fails():
    """A fresh-context reviewer cannot self-declare BLIND without provenance."""
    liar = _profile("R_BLIND", visible_information="BLIND", fresh_context=True)
    bound, _ = ReviewerProvenanceRegistry.from_fixtures([]).bind(liar)
    assert bound.exposure_mode == UNKNOWN
    assert bound.fresh_context is False


def test_friction_reviewer_registry_blind_status_succeeds():
    """With registered provenance the BLIND status survives and the fresh path
    executes."""
    truth = ReviewerProvenanceRegistry.from_fixtures([{
        "reviewer_id": "R_BLIND", "model_family": "FAM_A", "sources": ["S_A"],
        "runtime_lineage": "RT_A", "retrieval_bundle": "BUNDLE_A",
        "prior_conclusion_exposure": "FALSE", "visible_information": "BLIND",
        "fresh_context": True}])
    bound, _ = truth.bind(_profile("R_BLIND", visible_information="BLIND",
                                   fresh_context=True))
    assert bound.exposure_mode == "BLIND"
    assert bound.fresh_context is True
    trigger = FrictionTrigger(True, "test", 1, ("fresh_context_reconstruction",))
    result = run_friction(
        trigger, [bound], {"R_BLIND": {"BLIND": "ALT"}}, incumbent_conclusion="INC",
        budget=1)
    assert "R_BLIND" in result.fresh_context_reviewers
    assert result.information_gain is True


def test_secondary_surfaces_share_same_provenance_semantics():
    """Friction reviewers bound through the governed runner: primary reviewers
    are registered (facts match S08 and friction triggers), but R_BLIND_S08 is
    NOT registered — its self-declared BLIND status is not verified, so the
    fresh path produces no action and no information gain."""
    pack = load_g3_pack(ROOT / "s08_reflective_bypass")
    pack.provenance_mode = "GOVERNED_REGISTRY"
    pack.registered_provenance = [dict(r) for r in pack.reviewers]  # primary verified
    # NOTE: friction reviewer R_BLIND_S08 is deliberately NOT in the registry
    a = _run(pack).artifacts
    assert a["friction_triggered"] is True           # facts still correlate (registered)
    fr = a["friction_result"] or {}
    assert fr.get("fresh_context_reviewers") in ((), [])   # R_BLIND_S08 not BLIND
    assert fr.get("information_gain", False) is False


# --------------------------------------------------------------------------- #
# G3R2-04 — source-overlap prevalence
# --------------------------------------------------------------------------- #
def test_partial_bundle_overlap_detects_shared_source():
    """Different bundles, one shared source: bundle concentration is low but
    single-source prevalence is 1.0."""
    profiles = [
        _profile("R1", sources=["SOURCE_A", "SOURCE_B"]),
        _profile("R2", sources=["SOURCE_A", "SOURCE_C"]),
        _profile("R3", sources=["SOURCE_A", "SOURCE_D"]),
    ]
    facts = _facts(profiles)
    assert facts.source_concentration == pytest.approx(1 / 3)   # bundle-level modal
    assert facts.max_single_source_lineage_prevalence == 1.0    # SOURCE_A everywhere


def test_all_reviewers_share_one_source_prevalence_is_one():
    facts = _facts([_profile(f"R{i}", sources=["SOURCE_A"]) for i in range(3)])
    assert facts.max_single_source_lineage_prevalence == 1.0


def test_disjoint_source_bundles_remain_low_overlap():
    facts = _facts([_profile(f"R{i}", sources=[f"S_{i}"]) for i in range(3)])
    assert facts.max_single_source_lineage_prevalence == pytest.approx(1 / 3)


def test_unknown_source_metadata_not_treated_as_diverse():
    """Reviewers with NO source metadata: prevalence is None, not a low number
    that could be mistaken for diversity."""
    facts = _facts([_profile(f"R{i}", sources=[]) for i in range(3)])
    assert facts.max_single_source_lineage_prevalence is None
    assert facts.distinct_source_lineages == 0


def test_common_source_plus_unique_sources_keeps_correlation_visible():
    """CASE G metamorphic: 10 reviewers each [SOURCE_COMMON + unique_i]. The
    shared dependency must remain visible and friction must trigger at HIGH."""
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = []
    for i in range(10):
        pack.reviewers.append(dict(
            reviewer_id=f"R_{i}", role="reviewer", model_family="FAM_A",
            provider="PROV_A", runtime_lineage="RT_A",
            sources=["SOURCE_COMMON", f"UNIQUE_{i}"],
            retrieval_bundle="BUNDLE_A", prompt_context="CTX_A",
            prior_conclusion_exposure="FALSE", implementation_path="IMP_A",
            experiment_design_origin="DESIGN_A", allocator="PO",
            visible_information="EVIDENCE_ONLY", conclusion="CLAIM",
            evidence_refs=[f"E_{i}"], cost_units=1, latency_units=1,
            capability_tier="ADEQUATE"))
    pack.friction_contract = {
        "contract_id": "T-FRICTION",
        "consequence_classes": {"HIGH": {
            "trigger_on": ["correlation_risk"], "max_prior_exposure_ratio": 1.0,
            "budget": 2, "cost_per_reconstruction": 5,
            "methods": ["fresh_context_reconstruction"]}}}
    pack.friction_reviewers = []
    a = _run(pack).artifacts
    assert a["facts"]["distinct_source_lineages"] == 11       # common + 10 unique
    assert a["facts"]["max_single_source_lineage_prevalence"] == 1.0
    assert a["friction_triggered"] is True                     # correlation visible


# --------------------------------------------------------------------------- #
# G3R2-05 — UNKNOWN prior exposure is not FALSE
# --------------------------------------------------------------------------- #
def test_all_unknown_exposure_does_not_count_as_zero_exposure():
    facts = _facts([_profile(f"R{i}", prior_conclusion_exposure=None) for i in range(4)])
    assert facts.prior_exposure_true_count == 0
    assert facts.prior_exposure_false_count == 0
    assert facts.prior_exposure_unknown_count == 4
    assert facts.prior_exposure_known_ratio == 0.0
    # the old-style ratio (true/total) would read 0.0 — that must NOT be read
    # as evidence of zero exposure
    assert facts.prior_conclusion_exposure_ratio == 0.0
    assert facts.prior_exposure_known_ratio < 1.0


def test_unknown_exposure_cannot_satisfy_strict_independence_contract():
    facts = _facts([
        _profile(f"R{i}", sources=[f"S_{i}"], model_family=f"FAM_{i}",
                 prior_conclusion_exposure=None) for i in range(4)])
    assert independent_confirmation_satisfied(facts) is False


def test_known_false_exposure_can_satisfy():
    facts = _facts([
        _profile(f"R{i}", sources=[f"S_{i}"], model_family=f"FAM_{i}",
                 runtime_lineage=f"RT_{i}", prior_conclusion_exposure=False,
                 fresh_context=True) for i in range(4)])
    assert facts.prior_exposure_known_ratio == 1.0
    assert facts.prior_exposure_true_ratio_among_known == 0.0
    assert independent_confirmation_satisfied(facts) is True


def test_mixed_known_unknown_preserves_coverage_uncertainty():
    facts = _facts([
        _profile(f"R{i}", prior_conclusion_exposure=False if i < 2 else None)
        for i in range(4)])
    assert facts.prior_exposure_false_count == 2
    assert facts.prior_exposure_unknown_count == 2
    assert facts.prior_exposure_known_ratio == 0.5
    assert facts.prior_exposure_true_ratio_among_known == 0.0
    # mixed coverage: UNKNOWN reviewers keep the strict contract unsatisfied
    assert independent_confirmation_satisfied(facts) is False


def test_case_h_unknown_exposure_blocks_strict_independence():
    """Diverse sources/models, exposure UNKNOWN -> strict 'unexposed
    independent review' requirement NOT satisfied (UNKNOWN is not FALSE)."""
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = []
    for i in range(4):
        pack.reviewers.append(dict(
            reviewer_id=f"R_{i}", role="reviewer", model_family=f"FAM_{i}",
            provider="PROV_A", runtime_lineage=f"RT_{i}", sources=[f"S_{i}"],
            retrieval_bundle=f"B_{i}", prompt_context="CTX_A",
            implementation_path="IMP_A", experiment_design_origin=f"DESIGN_{i}",
            allocator="PO", visible_information="EVIDENCE_ONLY",
            conclusion="CLAIM", evidence_refs=[f"E_{i}"], cost_units=1,
            latency_units=1, capability_tier="ADEQUATE"))
        # NOTE: no prior_conclusion_exposure key -> UNKNOWN
    pack.friction_contract = None
    pack.friction_reviewers = None
    a = _run(pack).artifacts
    assert a["facts"]["distinct_source_lineages"] == 4
    assert a["facts"]["distinct_model_family_count"] == 4
    assert a["facts"]["prior_exposure_known_ratio"] == 0.0
    assert a["independent_confirmation_satisfied"] is False
    assert a["disposition"] != "INDEPENDENTLY_SUPPORTED"


# --------------------------------------------------------------------------- #
# G3R2-06 — tri-state UNKNOWN survives into decision-grade facts
# --------------------------------------------------------------------------- #
def test_unknown_heavy_set_is_not_equivalent_to_known_diversity():
    """2 known different + 8 unknown must NOT look like 10 known diversified
    reviewers: coverage facts preserve the difference."""
    sparse = ([_profile(f"S{i}", sources=[f"S_{i}"], model_family=f"FAM_{i}",
                        runtime_lineage=f"RT_{i}", fresh_context=True)
               for i in range(2)] +
              [_profile(f"U{i}", sources=[]) for i in range(8)])
    full = [_profile(f"F{i}", sources=[f"S_{i}"], model_family=f"FAM_{i}",
                     runtime_lineage=f"RT_{i}", fresh_context=True)
            for i in range(10)]
    fs, ff = _facts(sparse), _facts(full)
    assert fs.distinct_source_lineages == 2
    assert ff.distinct_source_lineages == 10
    assert fs.known_coverage_by_axis["source_lineage"] == pytest.approx(0.2)
    assert ff.known_coverage_by_axis["source_lineage"] == 1.0
    assert fs.unknown_count_by_axis["source_lineage"] == 8
    assert ff.unknown_count_by_axis["source_lineage"] == 0
    # a strict contract requiring source coverage fails the sparse set
    assert independent_confirmation_satisfied(
        fs, min_source_known_coverage=0.9) is False
    assert independent_confirmation_satisfied(
        ff, min_source_known_coverage=0.9) is True


def test_unknown_axis_coverage_survives_into_facts_dict():
    facts = _facts([_profile("R1"), _profile("R2", model_family=UNKNOWN)])
    d = facts.to_dict()
    assert d["known_coverage_by_axis"]["model_family"] == pytest.approx(0.5)
    assert d["unknown_count_by_axis"]["model_family"] == 1


# --------------------------------------------------------------------------- #
# G3R2-07 — method vocabulary fail-closed
# --------------------------------------------------------------------------- #
def test_unknown_counter_method_contract_rejected():
    with pytest.raises(ValueError):
        CounterAttractorSpec(spec_id="T", allowed_methods=("MAGIC_METHOD",))


def test_unknown_friction_method_contract_rejected():
    with pytest.raises(ValueError):
        FrictionContract(contract_id="T", consequence_classes={
            "HIGH": {"methods": ["MAGIC_METHOD"]}})


def test_canonical_subset_accepted():
    spec = CounterAttractorSpec(spec_id="T", allowed_methods=("fresh_context",))
    assert set(spec.allowed_methods) <= set(COUNTER_ATTRACTOR_METHODS)
    fcontract = FrictionContract(contract_id="T", consequence_classes={
        "HIGH": {"methods": ["fresh_context_reconstruction"]}})
    assert fcontract.for_consequence("HIGH")["methods"] == ["fresh_context_reconstruction"]


def test_empty_allowed_methods_uses_documented_default():
    spec = CounterAttractorSpec(spec_id="T")
    assert spec.allowed_methods == ()
    ca = run_counter_attractor(spec, "INC", [
        {"method": "fresh_context", "evidence_id": "E1",
         "discriminating_contradiction": False}])
    assert ca.budget_used == 1                       # canonical method accepted


# --------------------------------------------------------------------------- #
# G3R2-08 — stop on the first discriminating contradiction
# --------------------------------------------------------------------------- #
def _findings(n, contradiction_at=None):
    out = []
    for i in range(1, n + 1):
        out.append({"method": "fresh_context" if i % 2 else "reverse_premise",
                    "evidence_id": f"E{i}",
                    "discriminating_contradiction": (i == contradiction_at)})
    return out


def test_early_contradiction_stops_review():
    """budget=5; contradiction at #3 -> budget_used 3, not 5."""
    ca = run_counter_attractor(
        CounterAttractorSpec(spec_id="T", budget=5, cost_per_method=3),
        "INC", _findings(5, contradiction_at=3))
    assert ca.terminal_result == "CHALLENGE_SUPPORTED"
    assert ca.discriminating_contradiction_found is True
    assert ca.budget_used == 3


def test_post_contradiction_findings_not_consumed():
    ca = run_counter_attractor(
        CounterAttractorSpec(spec_id="T", budget=5), "INC",
        _findings(5, contradiction_at=3))
    assert {"E4", "E5"}.isdisjoint(ca.evidence_produced)   # never consumed


def test_post_contradiction_evidence_not_recorded():
    ca = run_counter_attractor(
        CounterAttractorSpec(spec_id="T", budget=5), "INC",
        _findings(5, contradiction_at=3))
    assert sorted(ca.evidence_produced) == ["E1", "E2", "E3"]


def test_cost_stops_with_review():
    ca = run_counter_attractor(
        CounterAttractorSpec(spec_id="T", budget=5, cost_per_method=3), "INC",
        _findings(5, contradiction_at=3))
    assert ca.cost_units == 3 * 3                    # budget_used * cost_per_method
    assert ca.cost_units == ca.budget_used * 3


def test_case_i_early_challenge_stops_at_two():
    """CASE I: budget 5, contradiction on action 2 -> stop at 2."""
    ca = run_counter_attractor(
        CounterAttractorSpec(spec_id="T", budget=5), "INC",
        _findings(5, contradiction_at=2))
    assert ca.budget_used == 2
    assert ca.terminal_result == "CHALLENGE_SUPPORTED"
    assert sorted(ca.evidence_produced) == ["E1", "E2"]


# --------------------------------------------------------------------------- #
# G3R2-09 — unique epistemic paths, not summed labels
# --------------------------------------------------------------------------- #
def test_one_path_fresh_plus_design_counts_as_one():
    p = _profile("R1", fresh_context=True, independent_design=True)
    paths = collect_epistemic_paths([p])
    assert len(paths) == 1
    assert paths[0].fresh_context is True and paths[0].independent_design is True


def test_two_distinct_qualifying_paths_count_as_two():
    paths = collect_epistemic_paths([
        _profile("R1", fresh_context=True), _profile("R2", independent_design=True)])
    assert len(paths) == 2


def test_duplicated_path_id_counts_once():
    """The same reviewer appearing twice (duplicated id) counts as one path."""
    dup = _profile("R1", fresh_context=True)
    paths = collect_epistemic_paths([dup, dup])
    assert len(paths) == 1


def test_unknown_path_provenance_does_not_qualify():
    """A reviewer whose provenance is entirely UNKNOWN cannot qualify as an
    independent epistemic path even if flags claim otherwise."""
    blank = ReviewerIndependenceProfile(
        reviewer_id="BLANK", fresh_context=True,
        independently_originated_design=True)
    assert collect_epistemic_paths([blank]) == ()


def test_case_j_one_path_two_labels_is_one():
    """One reviewer that is BOTH fresh AND independently-designed is ONE
    epistemic path; independence (threshold=1) is satisfied with that one path
    while other gates (2 sources / 2 model-runtimes) pass."""
    p1 = _profile("R1", sources=["S_1"], model_family="FAM_1",
                  runtime_lineage="RT_1", fresh_context=True,
                  independent_design=True)
    p2 = _profile("R2", sources=["S_2"], model_family="FAM_2",
                  runtime_lineage="RT_2")
    facts = _facts([p1, p2])
    assert facts.fresh_context_count == 1
    assert facts.independently_originated_design_count == 1
    assert facts.unique_epistemic_path_count == 1    # ONE path, not two
    assert independent_confirmation_satisfied(facts) is True  # threshold=1 satisfied


def test_replication_paths_are_distinct_identities():
    p = _profile("R1", fresh_context=True)
    facts = _facts([p], replication=3)
    assert facts.unique_epistemic_path_count == 4    # 1 fresh + 3 replications


# --------------------------------------------------------------------------- #
# G3R2-10 — topology capability provenance
# --------------------------------------------------------------------------- #
def test_unverified_high_capability_does_not_pass():
    topo = ReviewTopology(
        topology_id="T", purpose="p", consequence_class="HIGH",
        profiles=tuple(_profile(f"R{i}") for i in range(2)),
        capability_tiers=("HIGH", "HIGH"), capability_source="UNVERIFIED_CAPABILITY",
        cost_units=5)
    decision = route_review_topology("p", "HIGH", [topo], _contract())
    assert decision.constraints_satisfied is False
    assert any("capability" in g for g in decision.remaining_gaps)


def test_registered_adequate_capability_passes():
    topo = ReviewTopology(
        topology_id="T", purpose="p", consequence_class="HIGH",
        profiles=tuple(_profile(f"R{i}") for i in range(2)),
        capability_tiers=("ADEQUATE", "ADEQUATE"), capability_source="REGISTERED_CAPABILITY",
        cost_units=5)
    decision = route_review_topology("p", "HIGH", [topo], _contract())
    assert decision.constraints_satisfied is True
    assert decision.capability_source == "REGISTERED_CAPABILITY"


def test_synthetic_authoritative_capability_mode_explicit():
    topo = ReviewTopology(
        topology_id="T", purpose="p", consequence_class="HIGH",
        profiles=tuple(_profile(f"R{i}") for i in range(2)),
        capability_tiers=("ADEQUATE", "ADEQUATE"),
        capability_source="AUTHORITATIVE_SYNTHETIC_CAPABILITY", cost_units=5)
    decision = route_review_topology("p", "HIGH", [topo], _contract())
    assert decision.constraints_satisfied is True
    assert decision.capability_source == "AUTHORITATIVE_SYNTHETIC_CAPABILITY"


def test_case_k_fake_topology_cannot_satisfy_verified_routing():
    """CASE K: candidates self-claim HIGH capability + independent axes, but
    the registry holds UNKNOWN capability -> the HIGH-consequence routing
    constraint cannot be satisfied."""
    pack = load_g3_pack(ROOT / "s07_independent_weaker_agents")
    # registered entries carry the candidates' axes but NO capability fact
    registered = []
    for opt in pack.topology_options:
        for r in opt.get("reviewers", []):
            registered.append({k: v for k, v in r.items()
                               if k != "capability_tier"})
    pack.provenance_mode = "GOVERNED_REGISTRY"
    pack.registered_provenance = registered
    a = _run(pack).artifacts
    td = a["topology_decision"]
    assert td["constraints_satisfied"] is False
    assert td["capability_source"] == "UNVERIFIED_CAPABILITY"
    assert any("capability" in g for g in td["remaining_gaps"])


def test_capability_change_does_not_change_authority():
    """Capability provenance is a routing fact, never an authority fact:
    authority stays NONE regardless of the capability source."""
    pack = load_g3_pack(ROOT / "s07_independent_weaker_agents")
    a = _run(pack).artifacts
    assert a["authority_before"] == "NONE"
    assert a["authority_after"] == "NONE"
    assert a["authority_before"] == a["authority_after"]


# --------------------------------------------------------------------------- #
# Cross-cases F–K runner level
# --------------------------------------------------------------------------- #
def test_case_f_self_registered_swarm_fails_closed():
    """CASE F: 10 reviewers CLAIM 10 independent lineages, no registry,
    GOVERNED_REGISTRY -> independence NOT established."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    pack.provenance_mode = "GOVERNED_REGISTRY"
    pack.registered_provenance = None
    a = _run(pack).artifacts
    assert a["facts"]["distinct_source_lineages"] == 0
    assert a["independent_confirmation_satisfied"] is False
    assert a["disposition"] != "INDEPENDENTLY_SUPPORTED"


def test_case_g_partial_source_monoculture_detected():
    """CASE G: 10 reviewers each COMMON_SOURCE + unique_i -> the common-source
    dependency is detected even though bundles differ."""
    facts = _facts([
        _profile(f"R{i}", sources=["COMMON_SOURCE", f"UNIQUE_{i}"])
        for i in range(10)])
    assert facts.distinct_source_lineages == 11
    assert facts.max_single_source_lineage_prevalence == 1.0


def test_recommended_topology_remains_distinct_from_executed_evidence():
    """G3R-10 preserved: an admissible plan is not executed observation."""
    pack = load_g3_pack(ROOT / "s07_independent_weaker_agents")
    a = _run(pack).artifacts
    assert a["topology_execution_status"] == "REVIEW_TOPOLOGY_RECOMMENDED"
    assert a["evidence_obtained_from_executed_topology"] is False


def test_no_effective_independence_scalar_minted():
    facts = _facts([_profile(f"R{i}", sources=[f"S_{i}"], model_family=f"FAM_{i}")
                    for i in range(4)])
    for key in ("effective_independent_agents", "independence_score",
                "effective_sample_size", "HEALTH_SCORE"):
        assert key not in facts.to_dict()
