"""P0-A001-05 — DEFERRED lifecycle semantics consistency (ADR-0004)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeStateTransitionError
from qcae.core.lifecycle.state import (
    EVIDENCE_GATES,
    LEGAL_TRANSITIONS,
    TERMINAL_STATES,
    LifecycleState,
    assert_transition,
    is_legal_transition,
    is_terminal,
    legal_transitions,
)

S = LifecycleState


class TestDeferredConsistency:
    def test_deferred_is_terminal(self) -> None:
        assert S.DEFERRED in TERMINAL_STATES
        assert is_terminal(S.DEFERRED)

    def test_helpers_and_transition_table_agree(self) -> None:
        """is_terminal(), legal_transitions() and assert_transition() must agree
        for every state in the machine."""
        for state in S:
            table_targets = {dst for (src, dst) in LEGAL_TRANSITIONS if src == state}
            helper_targets = legal_transitions(state)
            assert table_targets == helper_targets, (
                f"legal_transitions({state}) disagrees with LEGAL_TRANSITIONS"
            )
            if state in TERMINAL_STATES:
                assert not table_targets, f"terminal {state} has outgoing edges"
            if not table_targets:
                assert is_terminal(state) or state == S.ACQUISITION_CANDIDATE, (
                    f"{state} has no outgoing edges but is not terminal"
                )

    def test_deferred_has_no_outgoing_edges(self) -> None:
        assert legal_transitions(S.DEFERRED) == frozenset()
        for target in S:
            if target is not S.DEFERRED:
                with pytest.raises(QcaeStateTransitionError):
                    assert_transition(S.DEFERRED, target)

    def test_deferred_entry_points_unchanged(self) -> None:
        """DEFERRED remains enterable from evaluation stages (canon 0.5.15)."""
        for stage in EVIDENCE_GATES[3:]:
            assert is_legal_transition(stage, S.DEFERRED)
            assert_transition(stage, S.DEFERRED)
        assert is_legal_transition(S.ACQUISITION_CANDIDATE, S.DEFERRED)

    def test_renewed_investigation_needs_new_object_not_a_transition(self) -> None:
        """ADR-0004: resumption is a superseding object, not a state flip.

        There is no DEFERRED -> anything edge, so a resumed investigation must
        be represented by a new decision carrying supersedes_decision.
        """
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.DEFERRED, S.CANDIDATE)
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.DEFERRED, S.MONITORED)
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.DEFERRED, S.ACQUISITION_CANDIDATE)

    def test_acquisition_candidate_still_branches_three_ways(self) -> None:
        for outcome in (S.APPROVED, S.REJECTED, S.DEFERRED):
            assert is_legal_transition(S.ACQUISITION_CANDIDATE, outcome)

    def test_deferral_adversarial_rejections_preserved(self) -> None:
        """P0 adversarial cases must keep passing with DEFERRED terminal."""
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.REQUESTED, S.DEFERRED)
        with pytest.raises(QcaeStateTransitionError):
            assert_transition(S.APPROVED, S.DEFERRED)
