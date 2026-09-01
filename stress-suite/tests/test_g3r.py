"""G3R — cognitive-ecology adversarial hardening regressions.

Each G3R defect gets adversarial tests that FAIL on the pre-G3R behavior:

G3R-01  counter-attractor budget must be real (only consumed findings count)
G3R-02  counter-attractor method contract enforced
G3R-03  strong consensus = actual vote concentration, not reviewer count
G3R-04  correlation risk must not require prior-conclusion exposure
G3R-05  friction methods/budget actually govern execution
G3R-06  fresh-context vs independent-design are distinct, provenance-based
G3R-07  reviewer provenance is registry-bound (CLAIMED vs VERIFIED)
G3R-08  dependency graph UNKNOWN semantics are tri-state
G3R-09  capability contract semantics are explicit (no max-capability bypass)
G3R-10  recommended topology is not confused with executed evidence

Plus the required cross-case matrix (CASE A–E). All local, deterministic,
model-free. All existing G3 tests remain valid.
"""
import json
from pathlib import Path

import pytest

from engine.cognitive_ecology import (
    DIFFERENT,
    SAME,
    UNKNOWN,
    ConsensusRecord,
    DependencyGraph,
    EcologyFacts,
    ReviewerIndependenceProfile,
    ReviewerProvenanceRegistry,
    independent_confirmation_satisfied,
)
from engine.ecology_policy import EcologyPolicy
from engine.friction import (
    COUNTER_ATTRACTOR_METHODS,
    CounterAttractorSpec,
    FrictionContract,
    FrictionTrigger,
    counter_attractor_trigger,
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


def _run_pack(pack):
    return run_g3_scenario(pack.decision_grade(), POLICY)


def _ca_spec(**kw):
    return CounterAttractorSpec(**{"spec_id": "T-CA", **kw})


def _topology(profiles, capability_tiers, cost=10, fresh=0, design=0,
              latency=5, topology_id="T"):
    return ReviewTopology(
        topology_id=topology_id, purpose="p", consequence_class="HIGH",
        profiles=tuple(profiles), capability_tiers=tuple(capability_tiers),
        cost_units=cost, latency_units=latency,
        fresh_context_count=fresh, independently_originated_design_count=design,
        counter_attractor_budget=0, stop_conditions=())


# --------------------------------------------------------------------------- #
# G3R-01 — counter-attractor budget must be real
# --------------------------------------------------------------------------- #
def test_contradiction_after_budget_is_ignored():
    """budget=3; findings 1-3 clean; finding 4 contradicts -> 4 MUST NOT count."""
    spec = _ca_spec(budget=3, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "reverse_premise", "evidence_id": "E2", "discriminating_contradiction": False},
        {"method": "alternate_source_search", "evidence_id": "E3", "discriminating_contradiction": False},
        {"method": "fresh_context", "evidence_id": "E4", "discriminating_contradiction": True},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.terminal_result == "NO_CHANGE"
    assert ca.discriminating_contradiction_found is False
    assert ca.budget_used == 3
    assert "E4" not in ca.evidence_produced


def test_contradiction_within_budget_is_honored():
    spec = _ca_spec(budget=3, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "reverse_premise", "evidence_id": "E2", "discriminating_contradiction": True},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.terminal_result == "CHALLENGE_SUPPORTED"
    assert ca.discriminating_contradiction_found is True
    assert ca.budget_used == 2


def test_evidence_produced_contains_only_consumed_findings():
    spec = _ca_spec(budget=2, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "reverse_premise", "evidence_id": "E2", "discriminating_contradiction": False},
        {"method": "alternate_source_search", "evidence_id": "E3", "discriminating_contradiction": False},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert sorted(ca.evidence_produced) == ["E1", "E2"]
    assert "E3" not in ca.evidence_produced


def test_cost_equals_consumed_authorized_methods():
    spec = _ca_spec(budget=4, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "reverse_premise", "evidence_id": "E2", "discriminating_contradiction": False},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.budget_used == 2
    assert ca.cost_units == 2 * 3


def test_zero_findings_does_not_fake_budget_consumption():
    spec = _ca_spec(budget=3, cost_per_method=3)
    ca = run_counter_attractor(spec, "INCUMBENT", [])
    assert ca.budget_used == 0
    assert ca.cost_units == 0
    assert ca.evidence_produced == ()
    assert ca.terminal_result == "UNRESOLVED"   # no authorized action completed


# --------------------------------------------------------------------------- #
# G3R-02 — counter-attractor method contract
# --------------------------------------------------------------------------- #
def test_unauthorized_method_cannot_support_challenge():
    spec = _ca_spec(budget=3, allowed_methods=("fresh_context",))
    findings = [
        {"method": "reverse_premise", "evidence_id": "E1", "discriminating_contradiction": True},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.discriminating_contradiction_found is False
    assert ca.terminal_result == "UNRESOLVED"
    assert len(ca.non_admissible_findings) == 1


def test_authorized_method_can_support_challenge():
    spec = _ca_spec(budget=3, allowed_methods=("fresh_context",))
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": True},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.discriminating_contradiction_found is True
    assert ca.terminal_result == "CHALLENGE_SUPPORTED"


def test_unknown_method_recorded_but_not_counted():
    spec = _ca_spec(budget=3, cost_per_method=3)
    findings = [
        {"method": "psychic_reading", "evidence_id": "E1", "discriminating_contradiction": True},
        {"method": "fresh_context", "evidence_id": "E2", "discriminating_contradiction": False},
        {"method": "fresh_context", "evidence_id": "E3", "discriminating_contradiction": False},
        {"method": "fresh_context", "evidence_id": "E4", "discriminating_contradiction": False},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    # unknown method preserved but never affects verdict and consumes no budget
    assert any(f.get("evidence_id") == "E1" for f in ca.non_admissible_findings)
    assert ca.budget_used == 3
    assert ca.terminal_result == "NO_CHANGE"
    assert "E1" not in ca.evidence_produced


def test_method_budget_and_finding_count_are_consistent():
    spec = _ca_spec(budget=2, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "alternate_source_search", "evidence_id": "E2", "discriminating_contradiction": False},
        {"method": "fresh_context", "evidence_id": "E3", "discriminating_contradiction": False},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.budget_used == 2                       # capped at budget
    assert len(ca.evidence_produced) == 2            # only consumed evidence
    assert ca.cost_units == ca.budget_used * 3


# --------------------------------------------------------------------------- #
# G3R-03 — strong consensus means consensus
# --------------------------------------------------------------------------- #
def test_eight_of_eight_independent_consensus_may_trigger():
    profiles = [_profile(f"R{i}", sources=[f"S_{i % 3}"], model_family=f"FAM_{i % 3}",
                         runtime_lineage=f"RT_{i % 3}", fresh_context=True)
                for i in range(8)]
    facts = _facts(profiles, consequence="HIGH", replication=1)
    assert facts.dominant_vote_ratio == 1.0
    assert facts.distinct_conclusion_count == 1
    assert counter_attractor_trigger(facts, _ca_spec()) is True


def test_three_two_split_does_not_trigger_strong_consensus():
    """3/2 split is exactly the provisional 0.6 boundary — NOT strong consensus."""
    profiles = (
        [_profile(f"R{i}", conclusion="A", sources=[f"S_{i % 3}"],
                  model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}", fresh_context=True)
         for i in range(3)]
        + [_profile(f"R{i}", conclusion="B", sources=[f"S_{i % 3}"],
                    model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}", fresh_context=True)
           for i in range(3, 5)]
    )
    facts = _facts(profiles, consequence="HIGH", replication=1)
    assert facts.raw_reviewer_count == 5
    assert facts.dominant_vote_ratio == pytest.approx(0.6)
    assert facts.distinct_conclusion_count == 2
    assert counter_attractor_trigger(facts, _ca_spec()) is False


def test_reviewer_count_alone_cannot_trigger_counter_attractor():
    """8 reviewers with a 4/4 split: count >= 5 but ratio 0.5 -> no trigger."""
    profiles = (
        [_profile(f"R{i}", conclusion="A", sources=[f"S_{i % 3}"],
                  model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}", fresh_context=True)
         for i in range(4)]
        + [_profile(f"R{i}", conclusion="B", sources=[f"S_{i % 3}"],
                    model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}", fresh_context=True)
           for i in range(4, 8)]
    )
    facts = _facts(profiles, consequence="HIGH", replication=1)
    assert facts.raw_reviewer_count == 8
    assert facts.dominant_vote_ratio == 0.5
    assert counter_attractor_trigger(facts, _ca_spec()) is False


def test_duplicate_correlated_votes_do_not_create_independent_support():
    """10 identical reviewers (S06 monoculture): ratio 1.0 but no independence."""
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = [dict(pack.reviewers[0], reviewer_id=f"R_{i}") for i in range(10)]
    a = _run_pack(pack).artifacts
    assert a["facts"]["dominant_vote_ratio"] == 1.0
    assert a["independent_confirmation_satisfied"] is False
    assert a["counter_attractor_result"] is None        # never triggered
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"


def test_three_two_split_at_runner_level_no_counter_attractor():
    """Runner-level: a split consensus under an otherwise independent topology
    must NOT fire the strong-consensus counter-attractor route."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    reviewers = (
        [dict(r, reviewer_id=f"SPLIT_A{i}", conclusion="REGIME_A",
              sources=[f"S_{i % 3}"], model_family=f"FAM_{i % 3}",
              runtime_lineage=f"RT_{i % 3}", retrieval_bundle=f"B_{i % 3}",
              fresh_context=True, prior_conclusion_exposure="FALSE")
         for i, r in enumerate(pack.reviewers[:3])]
        + [dict(r, reviewer_id=f"SPLIT_B{i}", conclusion="REGIME_B",
                sources=[f"S_{i % 3}"], model_family=f"FAM_{i % 3}",
                runtime_lineage=f"RT_{i % 3}", retrieval_bundle=f"B_{i % 3}",
                fresh_context=True, prior_conclusion_exposure="FALSE")
           for i, r in enumerate(pack.reviewers[3:6])]
    )
    pack.reviewers = reviewers
    pack.counter_attractor_findings = []
    a = _run_pack(pack).artifacts
    assert a["facts"]["dominant_vote_ratio"] == pytest.approx(0.5)
    assert a["counter_attractor_result"] is None
    assert a["counter_attractor_rule"] != "eco.counter_attractor.strong_consensus"


# --------------------------------------------------------------------------- #
# G3R-04 — correlation risk without prior-conclusion exposure
# --------------------------------------------------------------------------- #
def _monoculture_reviewers(exposure, count=10):
    """Fixture DICTS (the runner builds profiles via the provenance registry)."""
    return [
        dict(reviewer_id=f"M{i}", model_family="FAM_A", provider="PROV_A",
             runtime_lineage="RT_A", sources=["S_A"], retrieval_bundle="BUNDLE_A",
             prompt_context="CTX_A", prior_conclusion_exposure="TRUE" if exposure else "FALSE",
             implementation_path="IMP_A", experiment_design_origin="DESIGN_A",
             allocator="PO", visible_information="FULL_SHARED_CONTEXT",
             conclusion="ALPHA", confidence="HIGH", evidence_refs=[f"E_M{i}"])
        for i in range(count)
    ]


def test_case_a_monoculture_no_exposure_still_triggers_friction():
    """CASE A: 10 reviewers, same source/model/retrieval, exposure=0, 10/10,
    HIGH. The correlation-risk requirement cannot be bypassed by exposure=0."""
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = _monoculture_reviewers(exposure=False)
    a = _run_pack(pack).artifacts
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 0.0
    assert a["facts"]["source_concentration"] == 1.0
    assert a["friction_triggered"] is True                 # blind monoculture is a monoculture
    assert a["friction_rule"] == "eco.friction.correlation_risk"
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"  # correlated support stays visible


def test_case_a_friction_trigger_fires_without_exposure():
    profiles = [
        _profile(f"M{i}", sources=["S_A"], model_family="FAM_A", runtime_lineage="RT_A",
                 retrieval_bundle="BUNDLE_A", prior_conclusion_exposure=False)
        for i in range(10)
    ]
    facts = _facts(profiles, consequence="HIGH")
    contract = FrictionContract(
        contract_id="T-FRICTION",
        consequence_classes={"HIGH": {"trigger_on": ["correlation_risk"],
                                      "max_prior_exposure_ratio": 1.0,
                                      "budget": 2}})
    trigger = friction_trigger(facts, contract)
    assert trigger.triggered is True


def test_case_b_3_3_split_is_not_strong_consensus_and_no_unneeded_friction():
    """CASE B: 6 independent reviewers, 3/3 split, HIGH. Diversified on every
    axis the provisional contract inspects (sources, models, runtimes,
    retrieval) so no shared-axis concentration remains."""
    profiles = (
        [_profile(f"R{i}", conclusion="A", sources=[f"S_{i % 3}"],
                  model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}",
                  retrieval_bundle=f"B_{i % 3}", fresh_context=True)
         for i in range(3)]
        + [_profile(f"R{i}", conclusion="B", sources=[f"S_{i % 3}"],
                    model_family=f"FAM_{i % 3}", runtime_lineage=f"RT_{i % 3}",
                    retrieval_bundle=f"B_{i % 3}", fresh_context=True)
           for i in range(3, 6)]
    )
    facts = _facts(profiles, consequence="HIGH", replication=1)
    assert facts.retrieval_concentration == pytest.approx(1 / 3)
    assert counter_attractor_trigger(facts, _ca_spec()) is False
    contract = FrictionContract(contract_id="T-FRICTION", consequence_classes={
        "HIGH": {"trigger_on": ["correlation_risk"], "max_prior_exposure_ratio": 1.0}})
    assert friction_trigger(facts, contract).triggered is False


def test_case_c_diversified_topology_no_exposure_no_friction():
    """CASE C: diversified topology, exposure=0 -> no unnecessary friction."""
    profiles = [_profile(f"R{i}", sources=[f"S_{i % 4}"], model_family=f"FAM_{i % 4}",
                         runtime_lineage=f"RT_{i % 4}", retrieval_bundle=f"B_{i % 4}",
                         fresh_context=True, conclusion="A")
                for i in range(8)]
    facts = _facts(profiles, consequence="HIGH", replication=1)
    contract = FrictionContract(contract_id="T-FRICTION", consequence_classes={
        "HIGH": {"trigger_on": ["correlation_risk"], "max_prior_exposure_ratio": 1.0}})
    assert facts.source_concentration == pytest.approx(0.25)   # 8 reviewers / 4 sources
    assert friction_trigger(facts, contract).triggered is False


def test_case_d_disagreement_alone_no_friction():
    """CASE D: disagreement alone must never create friction actions."""
    facts = _facts([_profile("R1", conclusion="A"), _profile("R2", conclusion="B")],
                   consequence="LOW")
    contract = FrictionContract(contract_id="T-FRICTION", consequence_classes={
        "HIGH": {"trigger_on": ["correlation_risk"]}})
    trigger = friction_trigger(facts, contract)
    assert trigger.triggered is False


# --------------------------------------------------------------------------- #
# G3R-05 — friction methods must actually govern execution
# --------------------------------------------------------------------------- #
def _blind(reviewer_id, conclusion=""):
    return _profile(reviewer_id, visible_information="BLIND", fresh_context=True,
                    conclusion=conclusion)


def test_unauthorized_friction_method_ignored_or_rejected():
    trigger = FrictionTrigger(True, "test", budget=4,
                              methods=("fresh_context_reconstruction",))
    reviewers = [_blind("R1"), _blind("R2")]
    # the authorized fresh path returns the incumbent (no alternative); the
    # alternate-source results are supplied but NOT authorized -> ignored
    fr = run_friction(trigger, reviewers, {"R1": {"BLIND": "INCUMBENT"},
                                           "R2": {"BLIND": "INCUMBENT"}},
                      "INCUMBENT", 4, method_results={
                          "alternate_source_bundle": {"RX": "ALT_X"}})
    assert fr.triggered is True
    assert fr.surfaced_alternatives == ()
    assert all(a.method == "fresh_context_reconstruction" for a in fr.actions)
    assert fr.information_gain is False


def test_friction_budget_bounds_actions():
    trigger = FrictionTrigger(True, "test", budget=1,
                              methods=("fresh_context_reconstruction",))
    reviewers = [_blind("R1"), _blind("R2"), _blind("R3")]
    fr = run_friction(trigger, reviewers, {}, "INCUMBENT", 1)
    assert fr.action_count() == 1
    assert fr.budget_used == 1
    assert fr.cost_units == 5


def test_fresh_context_action_consumes_budget():
    trigger = FrictionTrigger(True, "test", budget=2,
                              methods=("fresh_context_reconstruction",))
    reviewers = [_blind("R1"), _blind("R2")]
    fr = run_friction(trigger, reviewers, {"R1": {"BLIND": "ALT_1"}, "R2": {"BLIND": "ALT_2"}},
                      "INCUMBENT", 2)
    assert fr.budget_used == 2
    assert fr.action_count() == 2
    assert fr.cost_units == 10
    assert tuple(sorted(fr.surfaced_alternatives)) == ("ALT_1", "ALT_2")


def test_no_trigger_means_zero_actions():
    trigger = FrictionTrigger(False, "no contract", budget=0, methods=())
    fr = run_friction(trigger, [_blind("R1")], {"R1": {"BLIND": "ALT_1"}}, "INCUMBENT", 2)
    assert fr.triggered is False
    assert fr.action_count() == 0
    assert fr.budget_used == 0
    assert fr.information_gain is False


def test_disagreement_does_not_create_actions_without_trigger():
    """Disagreement alone (no trigger) -> zero actions, no information gain."""
    facts = _facts([_profile("R1", conclusion="A"), _profile("R2", conclusion="B")],
                   consequence="LOW")
    contract = FrictionContract(contract_id="T-FRICTION", consequence_classes={})
    trigger = friction_trigger(facts, contract)
    assert trigger.triggered is False
    fr = run_friction(trigger, [_blind("R1")], {"R1": {"BLIND": "B"}}, "A", 2)
    assert fr.action_count() == 0


# --------------------------------------------------------------------------- #
# G3R-06 — fresh vs independent design semantics
# --------------------------------------------------------------------------- #
def _contract(**constraints):
    return TopologyConstraintContract(
        contract_id="T-ROUTE", constraints={"HIGH": constraints})


def test_fresh_context_satisfies_fresh_or_design_requirement():
    topo = _topology([_profile("R1", fresh_context=True)], ("ADEQUATE",),
                     fresh=1, design=0)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_fresh_or_independent_design=1,
                                               min_capability="BASIC"))
    assert decision.constraints_satisfied is True


def test_independent_design_satisfies_requirement_without_fresh_context():
    p = ReviewerIndependenceProfile(
        reviewer_id="R1", model_family="FAM_A", runtime_lineage="RT_A",
        source_lineages=("S_A",), retrieval_bundle="BUNDLE_A", prompt_context="CTX_A",
        prior_conclusion_exposure=False, implementation_path="IMP_A",
        experiment_design_origin="DESIGN_1", allocator="PO",
        independently_originated_design=True)
    topo = _topology([p], ("ADEQUATE",), fresh=0, design=1)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_fresh_or_independent_design=1,
                                               min_capability="BASIC"))
    assert decision.constraints_satisfied is True


def test_duplicated_design_does_not_satisfy():
    """Two reviewers sharing ONE design origin, no fresh context -> fail."""
    profiles = [
        ReviewerIndependenceProfile(
            reviewer_id=f"R{i}", model_family="FAM_A", runtime_lineage="RT_A",
            source_lineages=("S_A",), retrieval_bundle="BUNDLE_A", prompt_context="CTX_A",
            prior_conclusion_exposure=False, implementation_path="IMP_A",
            experiment_design_origin="DESIGN_SAME", allocator="PO",
            independently_originated_design=False)
        for i in range(2)
    ]
    topo = _topology(profiles, ("ADEQUATE", "ADEQUATE"), fresh=0, design=0)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_fresh_or_independent_design=1,
                                               min_capability="BASIC"))
    assert decision.constraints_satisfied is False
    assert any("fresh-context / independent-design" in g for g in decision.remaining_gaps)


def test_unknown_design_does_not_count_favorably():
    p = ReviewerIndependenceProfile(
        reviewer_id="R1", model_family="FAM_A", runtime_lineage="RT_A",
        source_lineages=("S_A",), prior_conclusion_exposure=False,
        experiment_design_origin=UNKNOWN, allocator="PO")
    topo = _topology([p], ("ADEQUATE",), fresh=0, design=0)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_fresh_or_independent_design=1,
                                               min_capability="BASIC"))
    assert decision.constraints_satisfied is False


# --------------------------------------------------------------------------- #
# G3R-07 — reviewer provenance registry
# --------------------------------------------------------------------------- #
def _claim(reviewer_id, **kw):
    base = dict(reviewer_id=reviewer_id, model_family="FAM_CLAIM",
                sources=["S_CLAIM"], retrieval_bundle="BUNDLE_CLAIM",
                runtime_lineage="RT_CLAIM", prior_conclusion_exposure=False,
                visible_information="BLIND", fresh_context=True, conclusion="X")
    base.update(kw)
    return ReviewerIndependenceProfile.from_reviewer_fixture(base)


def test_worker_claims_fake_model_lineage():
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": "W1", "model_family": "FAM_TRUE"}])
    bound, conflicts = registry.bind(_claim("W1", model_family="FAM_FAKE"))
    assert bound.model_family == "FAM_TRUE"                 # registered wins
    assert any(c.axis == "model_family" for c in conflicts)


def test_worker_claims_fake_source_lineage():
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": "W1", "sources": ["S_TRUE"]}])
    bound, conflicts = registry.bind(_claim("W1", sources=["S_FAKE_1", "S_FAKE_2"]))
    assert bound.source_lineages == ("S_TRUE",)
    assert any(c.axis == "source_lineage" for c in conflicts)


def test_worker_claims_fake_retrieval_bundle():
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": "W1", "retrieval_bundle": "BUNDLE_TRUE"}])
    bound, conflicts = registry.bind(_claim("W1", retrieval_bundle="BUNDLE_FAKE"))
    assert bound.retrieval_bundle == "BUNDLE_TRUE"
    assert any(c.axis == "retrieval_bundle" for c in conflicts)


def test_worker_claims_blind_but_registry_records_prior_exposure():
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": "W1", "prior_conclusion_exposure": "TRUE",
         "visible_information": "FULL_SHARED_CONTEXT"}])
    bound, conflicts = registry.bind(_claim("W1", prior_conclusion_exposure=False,
                                            visible_information="BLIND"))
    assert bound.prior_conclusion_exposure is True          # system-observable wins
    assert bound.exposure_mode == "FULL_SHARED_CONTEXT"
    assert any(c.axis == "prior_conclusion_exposure" for c in conflicts)


def test_unknown_registry_provenance_remains_unknown():
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": "W1", "model_family": UNKNOWN}])
    bound, conflicts = registry.bind(_claim("W1", model_family="FAM_CLAIM"))
    assert bound.model_family == UNKNOWN                     # claim NOT promoted
    assert any(c.disposition == "UNVERIFIED_CLAIM" for c in conflicts)


def test_registered_truth_changes_independence_profile():
    """CASE E: reviewer claims three model lineages; registry says one."""
    claims = [_claim(f"W{i}", model_family=f"FAM_CLAIM_{i}") for i in range(3)]
    registry = ReviewerProvenanceRegistry.from_fixtures([
        {"reviewer_id": f"W{i}", "model_family": "FAM_TRUE"} for i in range(3)])
    bound, conflicts = registry.bind_all(claims)
    assert {p.model_family for p in bound} == {"FAM_TRUE"}
    # every claimant's model-family lie is recorded as REGISTERED_WINS
    assert sum(1 for c in conflicts if c.axis == "model_family"
               and c.disposition == "REGISTERED_WINS") == 3
    facts = _facts(bound, consequence="HIGH")
    assert facts.distinct_model_family_count == 1           # one verified lineage wins


def test_missing_registry_entry_does_not_promote_claims():
    registry = ReviewerProvenanceRegistry.from_fixtures([])
    bound, conflicts = registry.bind(_claim("GHOST", model_family="FAM_CLAIM"))
    assert bound.model_family == "FAM_CLAIM" or bound.model_family == UNKNOWN
    # every claimed axis is at least marked unverified
    assert all(c.disposition == "UNVERIFIED_CLAIM" for c in conflicts)


# --------------------------------------------------------------------------- #
# G3R-08 — tri-state dependency UNKNOWN semantics
# --------------------------------------------------------------------------- #
def test_unknown_unknown_dependency_is_unknown():
    profiles = [
        ReviewerIndependenceProfile(reviewer_id="U1", conclusion="A"),
        ReviewerIndependenceProfile(reviewer_id="U2", conclusion="A"),
    ]
    graph = DependencyGraph.build(profiles)
    pair = graph.pairs[0]
    for axis in ("model_family", "runtime_lineage", "retrieval_bundle",
                 "experiment_design", "allocator", "source_lineage"):
        assert pair.overlaps[axis] == UNKNOWN, axis
    assert graph.fully_correlated_pairs() == 0       # UNKNOWN is not SAME


def test_known_same_is_shared():
    profiles = [_profile("K1", model_family="FAM_M"), _profile("K2", model_family="FAM_M")]
    graph = DependencyGraph.build(profiles)
    assert graph.pairs[0].overlaps["model_family"] == SAME


def test_known_different_is_distinct():
    profiles = [_profile("K1", model_family="FAM_M"), _profile("K2", model_family="FAM_N")]
    graph = DependencyGraph.build(profiles)
    assert graph.pairs[0].overlaps["model_family"] == DIFFERENT


def test_unknown_axis_cannot_satisfy_independence_requirement():
    """Two reviewers, both UNKNOWN on model/runtime but different sources:
    source diversity exists yet independence still fails (unknown is never
    favorable)."""
    profiles = [
        ReviewerIndependenceProfile(reviewer_id="U1", source_lineages=("S_A",), conclusion="A"),
        ReviewerIndependenceProfile(reviewer_id="U2", source_lineages=("S_B",), conclusion="A"),
    ]
    facts = _facts(profiles, consequence="HIGH")
    assert facts.distinct_source_lineages == 2
    assert facts.distinct_model_family_count == 0
    assert independent_confirmation_satisfied(facts) is False


# --------------------------------------------------------------------------- #
# G3R-09 — capability semantics
# --------------------------------------------------------------------------- #
def test_one_high_plus_basic_fails_all_required_capability():
    """One HIGH + several BASIC must NOT pass a contract that requires ADEQUATE
    review paths (fail-closed; max-capability bypass eliminated)."""
    profiles = [_profile(f"R{i}") for i in range(3)]
    topo = _topology(profiles, ("HIGH", "BASIC", "BASIC"), cost=6)
    decision = route_review_topology(
        "p", "HIGH", [topo],
        _contract(min_capability="ADEQUATE"))
    assert decision.constraints_satisfied is False
    assert any("capability" in g for g in decision.remaining_gaps)


def test_all_required_roles_capability_explicit_key():
    profiles = [_profile("R1"), _profile("R2")]
    topo = _topology(profiles, ("ADEQUATE", "ADEQUATE"), cost=6)
    decision = route_review_topology(
        "p", "HIGH", [topo],
        _contract(minimum_all_required_roles_capability="ADEQUATE"))
    assert decision.constraints_satisfied is True


def test_any_reviewer_capability_semantics():
    """minimum_any_reviewer_capability admits the HIGH+BASIC mix; the all-
    required key does not. The contract states what it means."""
    profiles = [_profile(f"R{i}") for i in range(3)]
    topo = _topology(profiles, ("HIGH", "BASIC", "BASIC"), cost=6)
    any_ok = route_review_topology(
        "p", "HIGH", [topo],
        _contract(minimum_any_reviewer_capability="ADEQUATE"))
    assert any_ok.constraints_satisfied is True
    all_req = route_review_topology(
        "p", "HIGH", [topo],
        _contract(minimum_all_required_roles_capability="ADEQUATE"))
    assert all_req.constraints_satisfied is False


# --------------------------------------------------------------------------- #
# G3R-10 — recommended vs executed topology
# --------------------------------------------------------------------------- #
def test_recommended_topology_not_confused_with_executed_evidence():
    """S07 router RECOMMENDS a better topology; that is not evidence obtained."""
    res = _run_pack(load_g3_pack(ROOT / "s07_independent_weaker_agents"))
    a = res.artifacts
    td = a["topology_decision"]
    assert td["execution_status"] == "REVIEW_TOPOLOGY_RECOMMENDED"
    assert td["evidence_obtained"] is False
    assert a["topology_execution_status"] == "REVIEW_TOPOLOGY_RECOMMENDED"
    assert a["evidence_obtained_from_executed_topology"] is False
    # disposition stays REQUIRES_INDEPENDENT_REVIEW — the recommendation is not
    # converted into institutional evidence
    assert a["disposition"] == "REQUIRES_INDEPENDENT_REVIEW"


def test_receipt_artifact_records_recommended_vs_executed():
    from pathlib import Path as _P
    receipt = json.loads((_P(__file__).resolve().parent.parent / "scenarios"
                          / "s07_independent_weaker_agents" / "run_receipt.json")
                         .read_text(encoding="utf-8"))
    assert receipt["topology_status"] == "REVIEW_TOPOLOGY_RECOMMENDED"
    assert receipt["evidence_obtained_from_executed_topology"] is False


# --------------------------------------------------------------------------- #
# cross-case matrix (prompt §14)
# --------------------------------------------------------------------------- #
def test_case_c_budget_3_contradiction_after_clean_findings():
    """CASE C: budget 3, first 3 counter-attractor findings clean, 4th
    contradicts -> the 4th cannot alter terminal state."""
    spec = _ca_spec(budget=3, cost_per_method=3)
    findings = [
        {"method": "fresh_context", "evidence_id": "E1", "discriminating_contradiction": False},
        {"method": "reverse_premise", "evidence_id": "E2", "discriminating_contradiction": False},
        {"method": "alternate_source_search", "evidence_id": "E3", "discriminating_contradiction": False},
        {"method": "raw_evidence_reconstruction", "evidence_id": "E4",
         "discriminating_contradiction": True},
    ]
    ca = run_counter_attractor(spec, "INCUMBENT", findings)
    assert ca.terminal_result == "NO_CHANGE"
    assert "E4" not in ca.evidence_produced


def test_case_d_two_independent_designs_no_fresh_context():
    """CASE D: two independent experiment designs, no fresh-context path -> the
    fresh-or-independent-design constraint can be satisfied if the contract
    permits it."""
    profiles = [
        ReviewerIndependenceProfile(
            reviewer_id=f"R{i}", model_family="FAM_A", runtime_lineage="RT_A",
            source_lineages=(f"S_{i}",), retrieval_bundle="BUNDLE_A", prompt_context="CTX_A",
            prior_conclusion_exposure=False, implementation_path="IMP_A",
            experiment_design_origin=f"DESIGN_{i}", allocator="GOVERNOR",
            independently_originated_design=True)
        for i in range(2)
    ]
    topo = _topology(profiles, ("ADEQUATE", "ADEQUATE"), fresh=0, design=2)
    decision = route_review_topology("p", "HIGH", [topo],
                                     _contract(min_fresh_or_independent_design=1,
                                               min_capability="BASIC"))
    assert decision.constraints_satisfied is True


def test_case_a_runner_level_friction_and_disposition():
    """CASE A (runner): correlated support stays visible and the independent
    review requirement cannot be bypassed merely because exposure=0."""
    pack = load_g3_pack(ROOT / "s06_correlated_consensus")
    pack.reviewers = _monoculture_reviewers(exposure=False)
    a = _run_pack(pack).artifacts
    assert a["facts"]["prior_conclusion_exposure_ratio"] == 0.0
    assert a["friction_triggered"] is True
    assert a["disposition"] == "SUPPORTED_BUT_CORRELATED"
    assert a["independent_confirmation_satisfied"] is False


def test_case_b_runner_level_3_3_split_high_consequence():
    """CASE B (runner): a 3/3 split among genuinely independent reviewers is not
    strong consensus; no counter-attractor strong-consensus route fires."""
    pack = load_g3_pack(ROOT / "s09_counter_attractor_false_alarm")
    pack.reviewers = [
        dict(r, reviewer_id=f"SPLIT_{i}", conclusion="REGIME_A" if i % 2 else "REGIME_B",
             sources=[f"S_{i % 3}"], model_family=f"FAM_{i % 3}",
             runtime_lineage=f"RT_{i % 3}", fresh_context=True,
             prior_conclusion_exposure="FALSE")
        for i, r in enumerate(pack.reviewers[:6])
    ]
    pack.counter_attractor_findings = []
    a = _run_pack(pack).artifacts
    assert a["facts"]["dominant_vote_ratio"] == 0.5
    assert a["counter_attractor_result"] is None
