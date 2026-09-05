"""G1R hardening regressions (defects G1R-01, G1R-05, G1R-06, G1R-07, G1R-08, G1R-09)."""
import pytest

from engine.phase import PhaseStateMachine, PhaseDecisionRecord, PhaseDecisionError, PhaseEdgeTable, DEFAULT_PHASE_EDGES
from engine.lifecycle import KnowledgeRecord, LifecycleEngine
from engine.base import Provenance, AuthorityLevel
from engine.governed import GovernedTransitionExecutor
from engine.authority import AuthorityState, CapabilityGrant, AuthorityViolation
from engine.truth import CapabilityStatus, TruthRegistry
from engine.evidence import EvidenceRecord
from engine.constraint import ConstraintField  # noqa: F401 (kept for sweep symmetry)
from engine.replay import DeterministicReplay, ReplayEvent


# --------------------------------------------------------------------------- #
# G1R-01 — phase decision serialization (must round-trip & be deterministic)
# --------------------------------------------------------------------------- #
def test_phase_decision_to_dict_roundtrip():
    m = PhaseStateMachine()
    d = m.evaluate(seq=1, actor="GOVERNOR", to_state="WATCH",
                   evidence_vector={"independent_contradiction": "HIGH", "reliability_degradation": "MEDIUM"},
                   authority_level="GOVERNOR", mutation_class="READ_ONLY", reason="saw tension")
    js = d.to_dict()
    assert isinstance(js, dict)
    assert js["phase_from"] == "STABLE" and js["phase_to"] == "WATCH"
    assert js["evidence_vector"] == {"independent_contradiction": "HIGH", "reliability_degradation": "MEDIUM"}
    for key in ("decision_id", "seq", "allowed", "authority_level", "operator_required",
                "rationale", "mutation_class", "contract_version"):
        assert key in js
    # deterministic: serializing twice yields identical output
    assert d.to_dict() == d.to_dict()
    # and reconstructable via __dict__ contract
    d2 = PhaseDecisionRecord(**js)
    assert d2.to_dict() == js


# --------------------------------------------------------------------------- #
# G1R-05 — explicit lifecycle admissibility (never inferred from state equality)
# --------------------------------------------------------------------------- #
def _mk(state="ACTIVE"):
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state=state)
    return r


@pytest.fixture
def eng():
    e = LifecycleEngine()
    r = _mk()
    e.add(r)
    return e, r


def test_illegal_same_state_transition_reported_forbidden(eng):
    e, r = eng
    # ACTIVE -> ACTIVE is not an edge; final state == requested state, yet must be FORBIDDEN
    tr = r.transition(seq=1, to_state="ACTIVE", actor="PO", authority_basis="b",
                      authority_level="PO", reason="self-loop attempt")
    assert tr.allowed is False and tr.applied is False
    assert tr.from_state == "ACTIVE" and tr.to_state == "ACTIVE"


def test_legal_transition_reported_allowed(eng):
    r = eng[1]
    tr = r.transition(seq=1, to_state="CHALLENGED", actor="PO", authority_basis="b",
                      authority_level="PO", reason="challenge")
    assert tr.allowed is True and tr.applied is True
    assert r.state == "CHALLENGED"


def test_illegal_transition_does_not_mutate_state(eng):
    e, r = eng
    # OBSERVED is not reachable from ACTIVE in the provisional edge table
    tr = r.transition(seq=1, to_state="OBSERVED", actor="PO", authority_basis="b",
                      authority_level="PO", reason="not a legal ACTIVE jump")
    assert tr.allowed is False and r.state == "ACTIVE"


def test_illegal_transition_trace_preserves_attempt_and_reason():
    r = _mk("ACTIVE")
    tr = r.transition(seq=9, to_state="PROMOTED", actor="PO", authority_basis="b",
                      authority_level="PO", reason="hmm")
    assert tr.allowed is False
    assert tr.violation  # reason for rejection preserved
    assert tr.to_state == "PROMOTED"       # the attempted target is recorded
    assert r.transitions[-1].to_state == "PROMOTED"


# --------------------------------------------------------------------------- #
# G1R-06 — decision.allowed always == application truth; capital never implied
# --------------------------------------------------------------------------- #
def test_capital_disabled_across_all_legal_phase_edges():
    """Every otherwise-legal phase edge must be denied under CAPITAL_MUTATION."""
    table = PhaseEdgeTable.default()
    failed = []
    for from_state, tos in table.legal_edges.items():
        for to_state in tos:
            m = PhaseStateMachine(edge_table=table, initial=from_state)
            d = m.evaluate(seq=1, actor="X", to_state=to_state, evidence_vector={},
                           authority_level="GOVERNOR",
                           mutation_class="CAPITAL_MUTATION")
            if d.allowed:
                failed.append((from_state, to_state))
            # application truth must match decision truth
            m.record(d); m.apply(d)
            if d.allowed is False and m.state != from_state:
                failed.append((from_state, to_state, "state changed though denied"))
            if d.allowed is True and m.state != to_state:
                failed.append((from_state, to_state, "state did not follow allowed"))
    assert not failed, f"capital/truth mismatch on legal edges: {failed}"


def test_invalid_authority_no_ledger_mutation():
    m = PhaseStateMachine()
    before = len(m.decisions)
    with pytest.raises(PhaseDecisionError):
        m.attempt(seq=1, actor="X", to_state="WATCH", evidence_vector={},
                  authority_level="NOT_A_LEVEL", mutation_class="READ_ONLY")
    assert len(m.decisions) == before   # exception before any ledger mutation
    assert m.state == "STABLE"


# --------------------------------------------------------------------------- #
# G1R-07 — governed executor cannot be bypassed by scenario replay
# --------------------------------------------------------------------------- #
def _replay(events, actors=None):
    """Run a governed replay with a registered-actor authority projection
    (G2-P0: governed actions are bound to AuthorityState)."""
    auth = AuthorityState()
    seeds = {"SENTINEL": "GOVERNOR", "GOVERNOR": "GOVERNOR", "PO": "PO"}
    seeds.update(actors or {})
    for a, l in seeds.items():
        auth.seed_level(a, l)
    auth.freeze_initialization()
    return DeterministicReplay(authority=auth).run(events)


def test_replay_cannot_bypass_watch_architecture_mutation_rule():
    evs = [
        ReplayEvent(1, "phase_step", "phase", "SENTINEL", "@INST", {"to_state": "WATCH", "evidence_vector": {}, "authority_level": "GOVERNOR", "mutation_class": "READ_ONLY"}),
        ReplayEvent(2, "phase_step", "phase", "GOVERNOR", "@INST", {"to_state": "ESCALATION_REVIEW", "evidence_vector": {}, "authority_level": "GOVERNOR", "mutation_class": "ONTOLOGY_MUTATION"}),
    ]
    res = _replay(evs)
    assert res.trace[0]["allowed"] is True
    assert res.trace[1]["allowed"] is False
    assert "RULE-02" in res.trace[1]["rule_ids"]
    assert res.terminal_phase == "WATCH"  # second step not applied


def test_replay_cannot_bypass_capability_to_authority_rule():
    evs = [
        ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                    {"action": "REQUEST_AUTHORITY", "capability_gain": True, "authority_gain": True,
                     "actor": "WORKER_1", "target": "WORKER_1", "risk_class": "authority"}),
    ]
    res = _replay(evs, actors={"WORKER_1": "WORKER"})
    assert res.trace[0]["allowed"] is False
    assert "RULE-06" in res.trace[0]["rule_ids"]


def test_replay_cannot_bypass_unresolved_to_ontology_rule():
    evs = [
        ReplayEvent(1, "lifecycle_step", "lifecycle", "PO", "@UP",
                    {"action": "PROMOTE_ONTOLOGY", "record_kind": "UNRESOLVED_PATTERN",
                     "evidence_sufficient": False, "admissible": False}),
    ]
    res = _replay(evs)
    assert res.trace[0]["allowed"] is False
    assert "RULE-04" in res.trace[0]["rule_ids"]


def test_replay_cannot_bypass_agent_confidence_confirmation_rule():
    evs = [
        ReplayEvent(1, "evidence_step", "evidence", "PO", "@E",
                    {"action": "RECORD", "actual_kind": "AGENT_CLAIM", "claimed_kind": "INDEPENDENT_CONFIRMATION"}),
    ]
    res = _replay(evs)
    assert res.trace[0]["allowed"] is False
    assert "RULE-05" in res.trace[0]["rule_ids"]


def test_governed_executor_records_rule_id_on_rejection():
    phase = PhaseStateMachine()
    lifecycle = LifecycleEngine()
    auth = AuthorityState()
    auth.seed_level("X", "GOVERNOR")
    auth.freeze_initialization()
    ex = GovernedTransitionExecutor(phase, lifecycle, auth)
    ev = ReplayEvent(1, "phase_step", "phase", "X", "@INST",
                     {"to_state": "ESCALATION_REVIEW", "evidence_vector": {},
                      "authority_level": "GOVERNOR", "mutation_class": "ARCHITECTURE_MUTATION"})
    phase.attempt(seq=1, actor="SENTINEL", to_state="WATCH", evidence_vector={},
                  authority_level="GOVERNOR", mutation_class="READ_ONLY")
    entry = ex.execute(ev)  # from WATCH with architecture mutation
    assert entry.allowed is False
    assert entry.rule_ids  # a rule id is recorded on rejection


# --------------------------------------------------------------------------- #
# G1R-08 — authority firewall must PROVE state invariance (no placeholders)
# --------------------------------------------------------------------------- #
def test_operator_preference_does_not_change_evidence_or_grants():
    phase = PhaseStateMachine(); lifecycle = LifecycleEngine(); auth = AuthorityState()
    auth.seed_level("OPERATOR", "OPERATOR"); auth.freeze_initialization()
    ex = GovernedTransitionExecutor(phase, lifecycle, auth)
    ex.execute(ReplayEvent(1, "evidence_step", "evidence", "SENSOR", "@E",
                           {"action": "RECORD", "actual_kind": "OBSERVATION", "claim": "temp rises"}))
    assert len(ex.evidence) == 1
    before = {a: [g.grant_id for g in auth.registry.grants(a)] for a in auth.actors}
    ex.execute(ReplayEvent(2, "policy_step", "policy", "OPERATOR", "@policy",
                           {"action": "operator_preference", "detail": "operator prefers new ontology"}))
    assert len(ex.evidence) == 1                       # evidence untouched
    after = {a: [g.grant_id for g in auth.registry.grants(a)] for a in auth.actors}
    assert after == before                             # grants untouched


def test_research_promotion_does_not_grant_execution_authority():
    phase = PhaseStateMachine(); lifecycle = LifecycleEngine(); auth = AuthorityState()
    auth.seed_level("PO", "PO"); auth.freeze_initialization()
    ex = GovernedTransitionExecutor(phase, lifecycle, auth)
    r = KnowledgeRecord(record_id="k", claim="c", provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="OBSERVED")
    lifecycle.add(r)
    for to in ("CANDIDATE", "TESTED", "PROMOTED", "ACTIVE"):
        ex.execute(ReplayEvent(1, "lifecycle_step", "lifecycle", "PO", "k",
                               {"to_state": to, "authority_level": "PO", "reason": "promote"}))
    assert r.state == "ACTIVE"
    assert all(g.action != "capital" for g in auth.registry.grants("PO"))
    assert all(g.risk_class != "execution" for g in auth.registry.grants("PO"))
    # research promotion changes no grants at all
    assert auth.registry.grants("PO") == []


def test_capability_improvement_does_not_change_grants():
    tr = TruthRegistry(); tr.register(CapabilityStatus(capability_id="cap", label="IDEA"))
    tr.promote("cap", "OPERATIONALLY_PROVEN", ["ev1"], "EVALUATOR")
    auth = AuthorityState(); auth.seed_level("WORKER_1", "WORKER"); auth.freeze_initialization()
    before = [g.grant_id for g in auth.registry.grants("WORKER_1")]
    assert before == []   # capability label maxed, but no grant appeared
    # capability != authority
    assert auth.level("WORKER_1") == AuthorityLevel.WORKER.value


def test_profit_raise_does_not_change_validation_authority():
    phase = PhaseStateMachine(); lifecycle = LifecycleEngine(); auth = AuthorityState()
    auth.seed_level("VALIDATOR", "WORKER"); auth.freeze_initialization()
    ex = GovernedTransitionExecutor(phase, lifecycle, auth)
    ex.execute(ReplayEvent(1, "evidence_step", "evidence", "BACKTEST", "@E",
                           {"action": "RECORD", "actual_kind": "DETERMINISTIC", "claim": "huge pnl"}))
    before_grants = {a: [g.grant_id for g in auth.registry.grants(a)] for a in auth.actors}
    before_ev = len(ex.evidence)
    ex.execute(ReplayEvent(2, "policy_step", "policy", "BACKTEST", "@policy",
                           {"action": "profit_report", "detail": "apparent alpha 300%" }))
    assert len(ex.evidence) == before_ev
    # apparent profit must not create new authority grants or change evidence status
    assert {a: [g.grant_id for g in auth.registry.grants(a)] for a in auth.actors} == before_grants


# --------------------------------------------------------------------------- #
# G1R-09 — authority initialization vs mutation
# --------------------------------------------------------------------------- #
def test_authority_initialization_can_seed_roles():
    auth = AuthorityState()
    auth.seed_level("OPERATOR", "OPERATOR")
    auth.seed_level("WORKER_1", "WORKER")
    auth.freeze_initialization()
    assert auth.level("OPERATOR") == "OPERATOR"
    assert auth.level("WORKER_1") == "WORKER"


def test_authority_worker_cannot_bypass_after_freeze():
    auth = AuthorityState()
    auth.seed_level("WORKER_1", "WORKER")
    auth.seed_level("OPERATOR", "OPERATOR")
    auth.freeze_initialization()
    with pytest.raises(AuthorityViolation):
        auth.seed_level("WORKER_1", "OPERATOR")   # escalatory seed is a bypass
    assert auth.level("WORKER_1") == "WORKER"


def test_authority_governed_ratification_remains_legal_after_freeze():
    auth = AuthorityState()
    auth.seed_level("WORKER_1", "WORKER")
    auth.seed_level("OPERATOR", "OPERATOR")
    auth.freeze_initialization()
    g = CapabilityGrant.make(5, "WORKER_1", "archive_write", "documents", issued_by="OPERATOR", risk_class="destructive")
    auth.propose_authority_change("WORKER_1", "WORKER_1", g)
    auth.ratify_authority_change("OPERATOR", "WORKER_1", "WORKER_1", g)
    assert len(auth.registry.grants("WORKER_1")) == 1