"""P0-C03 — lifecycle states, transition guards, waiver evidence (canon 0.5)."""

from __future__ import annotations

from typing import List, Set, Tuple

import pytest

from qcae.core.errors import (
    QcaeStateTransitionError,
    QcaeTransitionWaiverError,
    QcaeValidationError,
)
from qcae.core.lifecycle.state import (
    EVIDENCE_GATES,
    LEGAL_TRANSITIONS,
    TERMINAL_STATES,
    WAIVABLE_GATES,
    LifecycleState,
    assert_transition,
    is_evidence_gate,
    is_legal_transition,
    is_terminal,
    legal_transitions,
)
from qcae.core.lifecycle.waiver import TransitionWaiver

S = LifecycleState


@pytest.fixture()
def domain_waiver() -> TransitionWaiver:
    return TransitionWaiver(
        waived_gate=S.DOMAIN_VERIFIED,
        justification="generic parser utility: no financial claim to validate",
        policy_ref="policy:evidence-domain-notapplicable",
        authority_id="human:quant-lab-operator",
        decided_at="2026-09-12T00:00:00Z",
    )


class TestCanonicalStructure:
    def test_all_states_from_canon_present(self) -> None:
        expected = {
            "REQUESTED", "DECOMPOSED", "DISCOVERING", "CANDIDATE", "TRIAGED",
            "CODE_VERIFIED", "SANDBOX_VERIFIED", "DEMO_VERIFIED", "DOMAIN_VERIFIED",
            "INTEGRATION_VERIFIED", "ACQUISITION_CANDIDATE", "APPROVED", "REJECTED",
            "DEFERRED", "MONITORED", "REVIEW_REQUIRED", "SUPERSEDED", "RETIRED",
        }
        assert {s.value for s in S} == expected

    def test_evidence_gate_order_matches_canon_051(self) -> None:
        assert EVIDENCE_GATES == (
            S.REQUESTED, S.DECOMPOSED, S.DISCOVERING, S.CANDIDATE, S.TRIAGED,
            S.CODE_VERIFIED, S.SANDBOX_VERIFIED, S.DEMO_VERIFIED, S.DOMAIN_VERIFIED,
            S.INTEGRATION_VERIFIED, S.ACQUISITION_CANDIDATE,
        )

    def test_only_domain_gate_is_waivable(self) -> None:
        assert WAIVABLE_GATES == {S.DOMAIN_VERIFIED}

    def test_terminal_states(self) -> None:
        # DEFERRED is terminal per ADR-0004 (P0-A001-05): renewed investigation
        # creates a superseding object; no direct resume transition exists.
        assert TERMINAL_STATES == {S.REJECTED, S.DEFERRED, S.SUPERSEDED, S.RETIRED}

    def test_no_outgoing_edges_from_terminal_states(self) -> None:
        for terminal in TERMINAL_STATES:
            assert legal_transitions(terminal) == frozenset()

    def test_single_predecessor_on_gate_chain(self) -> None:
        for i, gate in enumerate(EVIDENCE_GATES[1:]):
            predecessors = [
                src for (src, dst) in LEGAL_TRANSITIONS
                if dst == gate and src in EVIDENCE_GATES
            ]
            assert predecessors == [EVIDENCE_GATES[i]]


class TestLegalTransitions:
    def test_full_gate_progression(self) -> None:
        for current, nxt in zip(EVIDENCE_GATES, EVIDENCE_GATES[1:]):
            assert is_legal_transition(current, nxt)
            assert_transition(current, nxt)

    def test_acquisition_outcomes_from_acquisition_candidate(self) -> None:
        for outcome in (S.APPROVED, S.REJECTED, S.DEFERRED):
            assert is_legal_transition(S.ACQUISITION_CANDIDATE, outcome)

    def test_candidate_culling_at_evaluation_stages(self) -> None:
        for stage in EVIDENCE_GATES[3:]:
            assert is_legal_transition(stage, S.REJECTED)
            assert is_legal_transition(stage, S.DEFERRED)

    def test_no_culling_before_candidate(self) -> None:
        for stage in EVIDENCE_GATES[:3]:
            assert not is_legal_transition(stage, S.REJECTED)
            assert not is_legal_transition(stage, S.DEFERRED)

    def test_monitoring_cycle(self) -> None:
        assert is_legal_transition(S.APPROVED, S.MONITORED)
        assert is_legal_transition(S.MONITORED, S.REVIEW_REQUIRED)
        assert is_legal_transition(S.MONITORED, S.SUPERSEDED)
        assert is_legal_transition(S.MONITORED, S.RETIRED)
        assert is_legal_transition(S.REVIEW_REQUIRED, S.MONITORED)

    def test_state_helpers(self) -> None:
        assert is_terminal(S.RETIRED)
        assert not is_terminal(S.MONITORED)
        assert is_evidence_gate(S.CODE_VERIFIED)
        assert not is_evidence_gate(S.MONITORED)


class TestIllegalTransitions:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (S.REQUESTED, S.CANDIDATE),
            (S.REQUESTED, S.CODE_VERIFIED),
            (S.REQUESTED, S.APPROVED),
            (S.DECOMPOSED, S.SANDBOX_VERIFIED),
            (S.DISCOVERING, S.INTEGRATION_VERIFIED),
            (S.CANDIDATE, S.APPROVED),
            (S.CODE_VERIFIED, S.ACQUISITION_CANDIDATE),
            (S.SANDBOX_VERIFIED, S.DOMAIN_VERIFIED),
            (S.DEMO_VERIFIED, S.ACQUISITION_CANDIDATE),
            (S.MONITORED, S.APPROVED),
            (S.MONITORED, S.CANDIDATE),
            (S.REVIEW_REQUIRED, S.SUPERSEDED),
            (S.REVIEW_REQUIRED, S.RETIRED),
            (S.APPROVED, S.REJECTED),
            (S.REJECTED, S.CANDIDATE),
            (S.RETIRED, S.MONITORED),
            (S.SUPERSEDED, S.MONITORED),
            (S.DEFERRED, S.APPROVED),
            (S.DEFERRED, S.CANDIDATE),
            (S.ACQUISITION_CANDIDATE, S.MONITORED),
        ],
    )
    def test_illegal_jump_rejected(self, current: S, target: S) -> None:
        assert not is_legal_transition(current, target)
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(current, target)

    def test_self_transition_rejected(self) -> None:
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.CANDIDATE, S.CANDIDATE)

    def test_backward_transition_rejected(self) -> None:
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.INTEGRATION_VERIFIED, S.CODE_VERIFIED)

    def test_gate_skip_without_waiver_rejected(self) -> None:
        with pytest.raises(QcaeTransitionWaiverError):
            assert_transition(S.DEMO_VERIFIED, S.INTEGRATION_VERIFIED)


class TestWaivers:
    def test_waiver_unlocks_domain_skip(self, domain_waiver: TransitionWaiver) -> None:
        assert_transition(S.DEMO_VERIFIED, S.INTEGRATION_VERIFIED, waiver=domain_waiver)

    def test_waiver_names_wrong_gate_rejected(self, domain_waiver: TransitionWaiver) -> None:
        class _OtherGateWaiver:
            waived_gate = S.CODE_VERIFIED

        with pytest.raises(QcaeTransitionWaiverError):
            assert_transition(
                S.DEMO_VERIFIED, S.INTEGRATION_VERIFIED, waiver=_OtherGateWaiver()
            )

    def test_waiver_on_unneeded_edge_rejected(self, domain_waiver: TransitionWaiver) -> None:
        with pytest.raises(QcaeTransitionWaiverError):
            assert_transition(S.CANDIDATE, S.TRIAGED, waiver=domain_waiver)

    def test_waiver_does_not_unlock_other_skips(self, domain_waiver: TransitionWaiver) -> None:
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.TRIAGED, S.SANDBOX_VERIFIED, waiver=domain_waiver)


class TestWaiverRecord:
    def test_valid_waiver_validates(self, domain_waiver: TransitionWaiver) -> None:
        domain_waiver.validate()

    def test_non_waivable_gate_rejected(self) -> None:
        waiver = TransitionWaiver(
            waived_gate=S.CODE_VERIFIED,
            justification="trying it on",
            policy_ref="policy:x",
            authority_id="human:op",
            decided_at="2026-09-12T00:00:00Z",
        )
        with pytest.raises(QcaeValidationError):
            waiver.validate()

    def test_empty_justification_rejected(self) -> None:
        waiver = TransitionWaiver(
            waived_gate=S.DOMAIN_VERIFIED,
            justification="   ",
            policy_ref="policy:x",
            authority_id="human:op",
            decided_at="2026-09-12T00:00:00Z",
        )
        with pytest.raises(QcaeValidationError):
            waiver.validate()

    def test_reserved_policy_ref_rejected(self) -> None:
        waiver = TransitionWaiver(
            waived_gate=S.DOMAIN_VERIFIED,
            justification="legit reason",
            policy_ref="unspecified",
            authority_id="human:op",
            decided_at="2026-09-12T00:00:00Z",
        )
        with pytest.raises(QcaeValidationError):
            waiver.validate()

    def test_waiver_round_trip(self, domain_waiver: TransitionWaiver) -> None:
        rebuilt = TransitionWaiver.from_dict(domain_waiver.to_dict())
        assert rebuilt == domain_waiver
