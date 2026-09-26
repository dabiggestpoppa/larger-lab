"""G2-P0 — identity / authority binding preflight (G2 §1).

P0-A: governed phase/lifecycle/authority actions are attributed to event.actor;
      a payload authority_level claim must EXACTLY match AuthorityState level or
      be omitted (then derived). Unknown actors fail closed.
P0-B: RATIFY binds ratifier == event.actor; a worker cannot impersonate OPERATOR.
P0-C: seed_level() rejects unknown authority levels (enum-bounded setup).
P0-D: unknown risk classes fail closed (canonical capability-grant vocabulary).
"""
import pytest

from engine.authority import AuthorityState, CapabilityGrant, AuthorityViolation, RISK_CLASSES
from engine.authority import AuthorityLevel
from engine.base import Provenance
from engine.governed import GovernedTransitionExecutor
from engine.lifecycle import LifecycleEngine, KnowledgeRecord
from engine.phase import PhaseStateMachine
from engine.replay import DeterministicReplay, ReplayEvent


def _auth(**seeds) -> AuthorityState:
    auth = AuthorityState()
    defaults = {"GOVERNOR": "GOVERNOR", "OPERATOR": "OPERATOR", "PO": "PO", "WORKER_1": "WORKER"}
    defaults.update(seeds)
    for a, l in defaults.items():
        auth.seed_level(a, l)
    auth.freeze_initialization()
    return auth


def _phase_event(seq, actor, to_state, level, mutation_class="READ_ONLY"):
    return ReplayEvent(seq, "phase_step", "phase", actor, "@INST",
                       {"to_state": to_state, "evidence_vector": {},
                        "authority_level": level, "mutation_class": mutation_class,
                        "reason": "r"})


# --------------------------------------------------------------------------- #
# P0-A — actor authority binding
# --------------------------------------------------------------------------- #
def test_worker_phase_spoof_rejected():
    """WORKER_1 seeded WORKER claims GOVERNOR => rejected, no phase change,
    identity rule recorded."""
    evs = [_phase_event(1, "WORKER_1", "WATCH", "GOVERNOR")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert res.trace[0]["kind"] == "AUTHORITY_INVALID"
    assert "AUTHORITY_LEVEL_MISMATCH" in res.trace[0]["rule_ids"]
    assert res.terminal_phase == "STABLE"


def test_unknown_actor_phase_rejected():
    """An actor not registered in AuthorityState cannot drive a phase action."""
    evs = [_phase_event(1, "GHOST", "WATCH", "GOVERNOR")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_ACTOR_UNKNOWN" in res.trace[0]["rule_ids"]
    assert res.terminal_phase == "STABLE"


def test_phase_claim_omitted_derives_registered_level():
    """Omitted payload authority_level is derived from AuthorityState, never
    defaulted to OBSERVER."""
    evs = [ReplayEvent(1, "phase_step", "phase", "GOVERNOR", "@INST",
                       {"to_state": "WATCH", "evidence_vector": {},
                        "mutation_class": "READ_ONLY", "reason": "r"})]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is True
    assert res.terminal_phase == "WATCH"


def test_worker_lifecycle_spoof_rejected():
    """Lifecycle state changes are equally identity-bound."""
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="TESTED")
    evs = [ReplayEvent(1, "lifecycle_step", "lifecycle", "WORKER_1", "k",
                       {"to_state": "PROMOTED", "authority_level": "PO", "reason": "spoof"})]
    res = DeterministicReplay(seed_records=[r], authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_LEVEL_MISMATCH" in res.trace[0]["rule_ids"]
    assert res.terminal_lifecycle["k"] == "TESTED"


def test_unknown_actor_lifecycle_rejected():
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="TESTED")
    evs = [ReplayEvent(1, "lifecycle_step", "lifecycle", "GHOST", "k",
                       {"to_state": "PROMOTED", "authority_level": "PO", "reason": "x"})]
    res = DeterministicReplay(seed_records=[r], authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_ACTOR_UNKNOWN" in res.trace[0]["rule_ids"]
    assert res.terminal_lifecycle["k"] == "TESTED"


# --------------------------------------------------------------------------- #
# P0-B — ratifier identity
# --------------------------------------------------------------------------- #
def test_worker_cannot_spoof_operator_ratifier():
    """event.actor=WORKER_1 with payload.ratifier=OPERATOR must fail closed."""
    evs = [ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                       {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                        "ratifier": "OPERATOR", "risk_class": "read"})]
    replay = DeterministicReplay(authority=_auth())
    res = replay.run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_RATIFIER_MISMATCH" in res.trace[0]["rule_ids"]
    # no grant was issued to WORKER_1 by the spoofed ratification
    assert replay.authority.registry.grants("WORKER_1") == []


def test_operator_actor_can_ratify_with_valid_grant():
    """G2R-05 correction: a ratification must reference a PRIOR proposal. The
    operator first receives a REQUEST_AUTHORITY (real proposal), then ratifies.

    Old assertion: an OPERATOR could RATIFY a grant fabricated directly at
    ratification time (proposal-less).
    Why invalid: that allowed a grant that was never proposed (G2R-05:
    ratify_without_prior_proposal_fails_closed).
    Replacement: proposal -> ratification, then the grant exists."""
    evs = [
        ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                    {"action": "REQUEST_AUTHORITY", "capability_gain": False,
                     "authority_gain": False, "target": "WORKER_1",
                     "risk_class": "read", "grant_action": "read", "target_scope": "dataset"}),
        ReplayEvent(2, "authority_step", "authority", "OPERATOR", "@AUTH",
                    {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                     "risk_class": "read"}),
    ]
    replay = DeterministicReplay(authority=_auth())
    res = replay.run(evs)
    assert res.trace[-1]["allowed"] is True
    assert res.trace[-1]["to"] == "ratified"
    assert len(replay.authority.registry.grants("WORKER_1")) == 1


def test_ratify_without_prior_proposal_fails_closed():
    """G2R-05: an OPERATOR cannot fabricate a grant that was never proposed."""
    evs = [ReplayEvent(1, "authority_step", "authority", "OPERATOR", "@AUTH",
                       {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                        "risk_class": "read"})]
    replay = DeterministicReplay(authority=_auth())
    res = replay.run(evs)
    assert res.trace[0]["allowed"] is False
    assert "NO_PRIOR_PROPOSAL" in res.trace[0]["rule_ids"]
    assert replay.authority.registry.grants("WORKER_1") == []


def test_non_operator_cannot_ratify_broker_grant():
    """G2R-05: broker is authority-bearing and requires OPERATOR ratification,
    exactly like deployment / destructive / capital. A governed GOVERNOR-level
    actor cannot ratify a broker grant."""
    from engine.base import AuthorityLevel as AL
    evs = [
        ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                    {"action": "REQUEST_AUTHORITY", "capability_gain": False,
                     "authority_gain": False, "target": "WORKER_1",
                     "risk_class": "broker", "grant_action": "broker_route", "target_scope": "exchange"}),
        ReplayEvent(2, "authority_step", "authority", "GOVERNOR", "@AUTH",
                    {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                     "risk_class": "broker"}),
    ]
    replay = DeterministicReplay(authority=_auth())
    res = replay.run(evs)
    assert res.trace[1]["allowed"] is False
    assert "AUTHORITY_FIREWALL" in res.trace[1]["rule_ids"]
    assert replay.authority.registry.grants("WORKER_1") == []
    # and the SAME proposal ratified by OPERATOR succeeds
    evs2 = [
        ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                    {"action": "REQUEST_AUTHORITY", "capability_gain": False,
                     "authority_gain": False, "target": "WORKER_1",
                     "risk_class": "broker", "grant_action": "broker_route", "target_scope": "exchange"}),
        ReplayEvent(2, "authority_step", "authority", "OPERATOR", "@AUTH",
                    {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                     "risk_class": "broker"}),
    ]
    replay2 = DeterministicReplay(authority=_auth())
    res2 = replay2.run(evs2)
    assert res2.trace[1]["allowed"] is True
    assert len(replay2.authority.registry.grants("WORKER_1")) == 1


def test_mismatched_actor_ratifier_fails_closed():
    evs = [ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                       {"action": "RATIFY", "proposer": "WORKER_1", "target": "WORKER_1",
                        "ratifier": "WORKER_2", "risk_class": "read"})]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_RATIFIER_MISMATCH" in res.trace[0]["rule_ids"]


# --------------------------------------------------------------------------- #
# P0-C — authority level enum validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", ["SUPREME_OVERLORD", "GOD", "admin", ""])
def test_seed_level_rejects_unknown_levels(bad):
    auth = AuthorityState()
    with pytest.raises(AuthorityViolation):
        auth.seed_level("X", bad)
    with pytest.raises(AuthorityViolation):
        auth.set_level("Y", bad)   # alias shares the guard


def test_seed_level_accepts_canonical_levels():
    auth = AuthorityState()
    for lvl in AuthorityLevel:
        auth.seed_level(f"A_{lvl.value}", lvl.value)
    assert auth.level("A_OPERATOR") == AuthorityLevel.OPERATOR.value


# --------------------------------------------------------------------------- #
# P0-D — risk class fail-closed
# --------------------------------------------------------------------------- #
def test_unknown_risk_class_rejected_at_construction():
    with pytest.raises(AuthorityViolation):
        CapabilityGrant.make(1, "WORKER_1", "act", "tgt", issued_by="OPERATOR",
                             risk_class="SUPREME_OVERLORD")


def test_unknown_risk_class_fails_closed_in_governed_request():
    """A governed REQUEST_AUTHORITY whose payload claims an unknown risk class is
    rejected — the unknown label cannot sneak past the RULE-06 veto."""
    evs = [ReplayEvent(1, "authority_step", "authority", "WORKER_1", "@AUTH",
                       {"action": "REQUEST_AUTHORITY", "capability_gain": False,
                        "authority_gain": False, "target": "WORKER_1",
                        "risk_class": "SUPREME"})]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_FIREWALL" in res.trace[0]["rule_ids"]


def test_canonical_risk_classes_are_accepted():
    assert "read" in RISK_CLASSES and "capital" in RISK_CLASSES
    g = CapabilityGrant.make(2, "WORKER_1", "archive_write", "docs",
                             issued_by="OPERATOR", risk_class="destructive")
    auth = AuthorityState()
    auth.seed_level("OPERATOR", "OPERATOR")
    auth.registry.issue(g, ratified_by="OPERATOR")
    assert len(auth.registry.grants("WORKER_1")) == 1


def test_governed_executor_rejects_unregistered_actor_before_mutation():
    """Fail-closed ordering: an unregistered actor's phase event must not mutate
    anything, even via the low-level executor."""
    phase = PhaseStateMachine()
    lifecycle = LifecycleEngine()
    auth = AuthorityState()
    auth.seed_level("OPERATOR", "OPERATOR")
    auth.freeze_initialization()
    ex = GovernedTransitionExecutor(phase, lifecycle, auth)
    entry = ex.execute(_phase_event(1, "GHOST", "WATCH", "GOVERNOR"))
    assert entry.allowed is False
    assert entry.kind == "AUTHORITY_INVALID"
    assert phase.state == "STABLE"
    assert phase.decisions == []   # no ledger mutation either