"""Canonical QCAE capability lifecycle (canon Book I 0.5).

The state machine is the single authority for lifecycle legality. Adapters and
services may not invent transitions (Book V 15.2 invariant 4).

Structure of the canonical machine:

- An ordered chain of evidence gates::

      REQUESTED -> DECOMPOSED -> DISCOVERING -> CANDIDATE -> TRIAGED ->
      CODE_VERIFIED -> SANDBOX_VERIFIED -> DEMO_VERIFIED -> DOMAIN_VERIFIED ->
      INTEGRATION_VERIFIED -> ACQUISITION_CANDIDATE

- Terminal acquisition outcomes from ACQUISITION_CANDIDATE::

      APPROVED | REJECTED | DEFERRED

- Post-approval monitoring::

      APPROVED -> MONITORED -> REVIEW_REQUIRED | SUPERSEDED | RETIRED
      REVIEW_REQUIRED -> MONITORED            (after revalidation)

- Candidates may be culled (REJECTED) or parked (DEFERRED) at any evaluation
  stage from CANDIDATE through ACQUISITION_CANDIDATE (canon 0.5.14, 0.5.15).

- REJECTED, SUPERSEDED and RETIRED are terminal. Historical evidence is never
  silently rewritten (canon 0.2.8, 0.5.18, 0.5.19).

Waivers: the DOMAIN_VERIFIED gate may be waived with a recorded policy
justification (canon 0.5.10 "NOT_APPLICABLE with policy justification"). This
is the only waivable gate and the only way to move DEMO_VERIFIED ->
INTEGRATION_VERIFIED. All other jumps are illegal.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Dict, FrozenSet, Mapping, Optional, Tuple

from qcae.core.errors import QcaeStateTransitionError, QcaeTransitionWaiverError


class LifecycleState(StrEnum):
    """Canonical lifecycle states (canon 0.5.1)."""

    REQUESTED = "REQUESTED"
    DECOMPOSED = "DECOMPOSED"
    DISCOVERING = "DISCOVERING"
    CANDIDATE = "CANDIDATE"
    TRIAGED = "TRIAGED"
    CODE_VERIFIED = "CODE_VERIFIED"
    SANDBOX_VERIFIED = "SANDBOX_VERIFIED"
    DEMO_VERIFIED = "DEMO_VERIFIED"
    DOMAIN_VERIFIED = "DOMAIN_VERIFIED"
    INTEGRATION_VERIFIED = "INTEGRATION_VERIFIED"
    ACQUISITION_CANDIDATE = "ACQUISITION_CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    MONITORED = "MONITORED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


#: Ordered evidence-gate chain (canon 0.5.1). Index = gate depth.
EVIDENCE_GATES: Tuple[LifecycleState, ...] = (
    LifecycleState.REQUESTED,
    LifecycleState.DECOMPOSED,
    LifecycleState.DISCOVERING,
    LifecycleState.CANDIDATE,
    LifecycleState.TRIAGED,
    LifecycleState.CODE_VERIFIED,
    LifecycleState.SANDBOX_VERIFIED,
    LifecycleState.DEMO_VERIFIED,
    LifecycleState.DOMAIN_VERIFIED,
    LifecycleState.INTEGRATION_VERIFIED,
    LifecycleState.ACQUISITION_CANDIDATE,
)

#: Gates whose skip requires a policy waiver (canon 0.5.10 — only DOMAIN_VERIFIED).
WAIVABLE_GATES: FrozenSet[LifecycleState] = frozenset({LifecycleState.DOMAIN_VERIFIED})

#: Edge unlocked only by a valid waiver for the named gate.
WAIVER_EDGES: Mapping[Tuple[LifecycleState, LifecycleState], LifecycleState] = {
    (LifecycleState.DEMO_VERIFIED, LifecycleState.INTEGRATION_VERIFIED): LifecycleState.DOMAIN_VERIFIED,
}

#: Terminal states: no outgoing transitions (canon 0.2.8, 0.5.18, 0.5.19).
#: DEFERRED is terminal for that decision/version per ADR-0004: renewed
#: investigation creates a new/superseding object (canon 0.5.15 scope + Book IV
#: 11.6 anti-reopening doctrine).
TERMINAL_STATES: FrozenSet[LifecycleState] = frozenset(
    {
        LifecycleState.REJECTED,
        LifecycleState.DEFERRED,
        LifecycleState.SUPERSEDED,
        LifecycleState.RETIRED,
    }
)


def _build_transitions() -> Dict[Tuple[LifecycleState, LifecycleState], None]:
    edges: Dict[Tuple[LifecycleState, LifecycleState], None] = {}

    # Linear evidence-gate progression.
    for current, nxt in zip(EVIDENCE_GATES, EVIDENCE_GATES[1:]):
        edges[(current, nxt)] = None

    # Acquisition outcomes from ACQUISITION_CANDIDATE.
    for outcome in (
        LifecycleState.APPROVED,
        LifecycleState.REJECTED,
        LifecycleState.DEFERRED,
    ):
        edges[(LifecycleState.ACQUISITION_CANDIDATE, outcome)] = None

    # Candidate culling / deferral at any evaluation stage (canon 0.5.14/0.5.15).
    for stage in EVIDENCE_GATES[3:]:  # CANDIDATE .. ACQUISITION_CANDIDATE
        edges[(stage, LifecycleState.REJECTED)] = None
        edges[(stage, LifecycleState.DEFERRED)] = None

    # Post-approval monitoring cycle.
    edges[(LifecycleState.APPROVED, LifecycleState.MONITORED)] = None
    edges[(LifecycleState.MONITORED, LifecycleState.REVIEW_REQUIRED)] = None
    edges[(LifecycleState.MONITORED, LifecycleState.SUPERSEDED)] = None
    edges[(LifecycleState.MONITORED, LifecycleState.RETIRED)] = None
    edges[(LifecycleState.REVIEW_REQUIRED, LifecycleState.MONITORED)] = None

    return edges


#: Exhaustive map of legal transitions. Waiver-unlocked edges are intentionally
#: absent here; they are legal only through ``assert_transition`` with a waiver.
LEGAL_TRANSITIONS: Mapping[Tuple[LifecycleState, LifecycleState], None] = _build_transitions()


def is_legal_transition(current: LifecycleState, target: LifecycleState) -> bool:
    """True when the edge exists without any waiver."""
    return (LifecycleState(current), LifecycleState(target)) in LEGAL_TRANSITIONS


def legal_transitions(current: LifecycleState) -> FrozenSet[LifecycleState]:
    """All states reachable from ``current`` in one legal, unwaived step."""
    return frozenset(
        target for (src, target) in LEGAL_TRANSITIONS if src == LifecycleState(current)
    )


def is_terminal(state: LifecycleState) -> bool:
    return LifecycleState(state) in TERMINAL_STATES


def is_evidence_gate(state: LifecycleState) -> bool:
    return LifecycleState(state) in EVIDENCE_GATES


def assert_transition(
    current: LifecycleState,
    target: LifecycleState,
    waiver: Optional["object"] = None,
) -> None:
    """Raise unless ``current -> target`` is legal.

    ``waiver`` is a :class:`qcae.core.lifecycle.waiver.TransitionWaiver`. It is
    required exactly when the edge is waiver-unlocked (canon 0.5.10) and is
    rejected on edges that do not need one (strictness prevents waivers from
    becoming decorative).
    """
    current = LifecycleState(current)
    target = LifecycleState(target)

    if is_legal_transition(current, target):
        if waiver is not None:
            raise QcaeTransitionWaiverError(
                f"transition {current} -> {target} is legal without a waiver; "
                "waivers are only valid for: "
                + ", ".join(f"{src} -> {dst} (skips {gate})" for (src, dst), gate in WAIVER_EDGES.items())
            )
        return

    required_gate = WAIVER_EDGES.get((current, target))
    if required_gate is not None:
        if waiver is None:
            raise QcaeTransitionWaiverError(
                f"transition {current} -> {target} skips the {required_gate} gate "
                "and requires a recorded policy waiver (canon 0.5.10)"
            )
        # Waiver self-consistency is validated by TransitionWaiver.validate();
        # here we only enforce that it targets this edge's skipped gate.
        if getattr(waiver, "waived_gate", None) != required_gate:
            raise QcaeTransitionWaiverError(
                f"waiver names gate {getattr(waiver, 'waived_gate', None)!r} but "
                f"edge {current} -> {target} skips {required_gate}"
            )
        return

    raise QcaeStateTransitionError(f"illegal lifecycle transition: {current} -> {target}")
