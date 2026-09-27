"""G2R-04 / §7-§8 — role-to-action authority + operator-required enforcement.

M5 phase MUTATION is the GOVERNOR path only. A WORKER/PO with a legitimately
seeded enum level cannot drive the phase machine directly. Operator-required
transitions cannot be applied by a GOVERNOR event without an explicit
OPERATOR_AUTHORIZE; authorization grants ACTION permission only and never
changes evidence.
"""
import pytest

from engine.authority import AuthorityState
from engine.base import AuthorityLevel as AL
from engine.governed import GovernedTransitionExecutor
from engine.lifecycle import LifecycleEngine, KnowledgeRecord
from engine.phase import PhaseStateMachine
from engine.replay import DeterministicReplay, ReplayEvent
from engine.base import Provenance


def _auth(**seeds) -> AuthorityState:
    auth = AuthorityState()
    defaults = {"GOVERNOR": "GOVERNOR", "OPERATOR": "OPERATOR", "PO": "PO",
                "WORKER_1": "WORKER", "SENTINEL": "GOVERNOR"}
    defaults.update(seeds)
    for a, l in defaults.items():
        auth.seed_level(a, l)
    auth.freeze_initialization()
    return auth


def _phase_event(seq, actor, to_state, level=None):
    p = {"to_state": to_state, "evidence_vector": {}, "mutation_class": "READ_ONLY", "reason": "r"}
    if level is not None:
        p["authority_level"] = level
    return ReplayEvent(seq, "phase_step", "phase", actor, "@INST", p)


# --------------------------------------------------------------------------- #
# role-to-action (G2R-04)
# --------------------------------------------------------------------------- #
def test_worker_with_real_worker_level_cannot_drive_phase():
    evs = [_phase_event(1, "WORKER_1", "WATCH")]           # WORKER level, no spoof
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert res.trace[0]["kind"] == "AUTHORITY_INVALID"
    assert "ROLE_NOT_AUTHORIZED" in res.trace[0]["rule_ids"]
    assert res.terminal_phase == "STABLE"


def test_po_with_real_po_level_cannot_drive_phase_directly():
    evs = [_phase_event(1, "PO", "WATCH")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "ROLE_NOT_AUTHORIZED" in res.trace[0]["rule_ids"]
    assert res.terminal_phase == "STABLE"


def test_governor_can_drive_permitted_phase():
    evs = [_phase_event(1, "GOVERNOR", "WATCH")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is True
    assert res.terminal_phase == "WATCH"


def test_unknown_actor_still_fails():
    evs = [_phase_event(1, "GHOST", "WATCH")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is False
    assert "AUTHORITY_ACTOR_UNKNOWN" in res.trace[0]["rule_ids"]
    assert res.terminal_phase == "STABLE"


def test_worker_can_produce_evidence_without_phase_authority():
    """The narrow rule blocks M5 MUTATION only; a worker may still produce
    evidence records (evidence machine is not phase authority)."""
    evs = [ReplayEvent(1, "evidence_step", "evidence", "WORKER_1", "@EVID",
                       {"action": "RECORD", "claim": "observation", "kind": "OBSERVATION"})]
    replay = DeterministicReplay(authority=_auth())
    res = replay.run(evs)
    assert res.trace[0]["allowed"] is True
    assert res.trace[0]["kind"] == "OK"


def test_seeded_sentinel_with_governor_level_is_gov_path():
    """An actor seeded at GOVERNOR level (e.g. a sentinel role) is part of the
    GOVERNOR path — the gate is on the authority LEVEL, not the actor name."""
    evs = [_phase_event(1, "SENTINEL", "WATCH")]
    res = DeterministicReplay(authority=_auth()).run(evs)
    assert res.trace[0]["allowed"] is True
    assert res.terminal_phase == "WATCH"


# --------------------------------------------------------------------------- #
# operator-required (G2R §8)
# --------------------------------------------------------------------------- #
def _executor_with_operator():
    phase = PhaseStateMachine()
    lifecycle = LifecycleEngine()
    auth = _auth()   # OPERATOR + GOVERNOR seated
    # seed a knowledge record so evidence-vs-authorization can be checked
    lifecycle.add(KnowledgeRecord(record_id="@K", claim="c",
                                  provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                                  creation_source="t", initial_state="ACTIVE"))
    return GovernedTransitionExecutor(phase, lifecycle, auth)


def test_governor_cannot_apply_operator_required_transition_without_operator_authorization():
    ex = _executor_with_operator()
    entry = ex.execute(ReplayEvent(1, "phase_step", "phase", "GOVERNOR", "@INST",
                                   {"to_state": "TRANSFORMATION_WINDOW", "evidence_vector": {},
                                    "mutation_class": "READ_ONLY", "reason": "r",
                                    "operator_required": True}))
    assert entry.allowed is False
    assert "OPERATOR_REQUIRED" in entry.rule_ids
    assert ex.phase.state == "STABLE"            # phase safe


def test_operator_authorization_allows_only_the_governed_action():
    ex = _executor_with_operator()
    # OPERATOR authorizes ONLY the STABLE -> WATCH step
    ok = ex.execute(ReplayEvent(1, "authority_step", "authority", "OPERATOR", "@AUTH",
                                {"action": "OPERATOR_AUTHORIZE", "authorization_id": "AUTH-1",
                                 "to_state": "WATCH"}))
    assert ok.allowed is True
    # governor may now apply THAT exact authorized transition...
    entry = ex.execute(ReplayEvent(2, "phase_step", "phase", "GOVERNOR", "@INST",
                                   {"to_state": "WATCH", "evidence_vector": {},
                                    "mutation_class": "READ_ONLY", "reason": "r",
                                    "operator_required": True, "operator_authorization_id": "AUTH-1"}))
    assert entry.allowed is True
    assert ex.phase.state == "WATCH"
    # ...but the SAME authorization does NOT cover a different governed action
    ex2 = _executor_with_operator()
    ex2.execute(ReplayEvent(1, "authority_step", "authority", "OPERATOR", "@AUTH",
                            {"action": "OPERATOR_AUTHORIZE", "authorization_id": "AUTH-1",
                             "to_state": "WATCH"}))
    entry2 = ex2.execute(ReplayEvent(2, "phase_step", "phase", "GOVERNOR", "@INST",
                                     {"to_state": "ESCALATION_REVIEW", "evidence_vector": {},
                                      "mutation_class": "READ_ONLY", "reason": "r",
                                      "operator_required": True, "operator_authorization_id": "AUTH-1"}))
    assert entry2.allowed is False
    assert "OPERATOR_REQUIRED" in entry2.rule_ids
    assert ex2.phase.state == "STABLE"          # failed authorization leaves phase safe


def test_operator_authorization_does_not_change_evidence():
    ex = _executor_with_operator()
    before = (len(ex.evidence), ex.authority.registry.grants("GOVERNOR"))
    ex.execute(ReplayEvent(1, "authority_step", "authority", "OPERATOR", "@AUTH",
                           {"action": "OPERATOR_AUTHORIZE", "authorization_id": "A-1",
                            "to_state": "WATCH"}))
    after = (len(ex.evidence), ex.authority.registry.grants("GOVERNOR"))
    assert after == before               # authorization is ACTION permission only
    assert ex.authority.level("GOVERNOR") == "GOVERNOR"  # no authority escalation


def test_operator_required_failure_leaves_phase_safe():
    ex = _executor_with_operator()
    ex.execute(ReplayEvent(1, "phase_step", "phase", "GOVERNOR", "@INST",
                           {"to_state": "WATCH", "evidence_vector": {},
                            "mutation_class": "READ_ONLY", "reason": "r",
                            "operator_required": True}))
    assert ex.phase.state == "STABLE"
    assert len(ex.phase.decisions) == 0    # nothing even entered the ledger


def test_non_operator_cannot_issue_operator_authorization():
    ex = _executor_with_operator()
    entry = ex.execute(ReplayEvent(1, "authority_step", "authority", "GOVERNOR", "@AUTH",
                                   {"action": "OPERATOR_AUTHORIZE", "authorization_id": "A-1",
                                    "to_state": "WATCH"}))
    assert entry.allowed is False
    assert "ROLE_NOT_AUTHORIZED" in entry.rule_ids