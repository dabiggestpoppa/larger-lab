"""M5 — Governor phase machine (A-010 §3 plus Book §5 holding/terminal states).

Owns INSTITUTIONAL PHASE ONLY. It does NOT own knowledge truth status (M4) and
must not merge capability verification (M1) into it. See G0-pack AMB-01/AMB-07.

The default edge table is a PROVISIONAL_TEST_CONTRACT (like the M4 lifecycle
edge map) because A-010 leaves some edges unspecified. Scenarios may override it
via a scenario spec, but the historical trace is never rewritten.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import AbstractSet, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from .base import (
    PHASE_EDGE_TABLE_CONTRACT,
    PROVISIONAL,
    AuthorityLevel,
    MutationClass,
    PhaseState,
    TransitionRecord,
    deterministic_hex,
)

# Key instruments
#: legal source -> targets
DEFAULT_PHASE_EDGES: Dict[str, FrozenSet[str]] = {
    # Ordinary escalation chain (A-010 §3)
    "STABLE": frozenset(["WATCH", "DATA_BLOCKED"]),
    "WATCH": frozenset(["ESCALATION_REVIEW", "STABLE", "DATA_BLOCKED"]),
    "ESCALATION_REVIEW": frozenset([
        "HOMEOSTATIC_REPAIR",
        "TRANSFORMATION_CANDIDATE",
        "NO_CHANGE",
        "OPERATOR_HOLD",
        "AUTHORITY_BLOCKED",
    ]),
    "HOMEOSTATIC_REPAIR": frozenset(["STABLE", "WATCH"]),
    "TRANSFORMATION_CANDIDATE": frozenset([
        "TRANSFORMATION_WINDOW",
        "NO_CHANGE",
        "OPERATOR_HOLD",
        "AUTHORITY_BLOCKED",
    ]),
    "TRANSFORMATION_WINDOW": frozenset([
        "RECONSOLIDATION",
        "NO_CHANGE",
        "UNRESOLVED",
        "OPERATOR_HOLD",
        "AUTHORITY_BLOCKED",
    ]),
    "RECONSOLIDATION": frozenset([
        "NEW_STABLE",
        "ROLLBACK",
        "NO_CHANGE",
        "PLURAL_MODEL_STATE",
        "UNRESOLVED",
    ]),
    # Outcome / holding states with optional return into stable operation
    "NEW_STABLE": frozenset(["STABLE"]),
    "ROLLBACK": frozenset(["STABLE"]),
    "NO_CHANGE": frozenset(["STABLE"]),
    "PLURAL_MODEL_STATE": frozenset(["STABLE"]),
    "UNRESOLVED": frozenset(["STABLE"]),
    "OPERATOR_HOLD": frozenset([
        "ESCALATION_REVIEW",
        "TRANSFORMATION_CANDIDATE",
        "WATCH",
        "STABLE",
    ]),
    "DATA_BLOCKED": frozenset(["STABLE", "WATCH"]),
    "AUTHORITY_BLOCKED": frozenset(["ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE", "STABLE"]),
}

PROVISIONAL_PHASE_UNREACHABLE_SOURCES = {"STABLE", "WATCH", "ESCALATION_REVIEW"}

#: boundaries where an attempted jump is a forbidden shortcut
FORBIDDEN_PHASE_EDGES: Dict[Tuple[str, str], str] = {
    ("STABLE", "NEW_STABLE"): "must pass review/evidence path before a new stable epoch",
    ("WATCH", "HOMEOSTATIC_REPAIR"): "repair requires escalation review",
    ("WATCH", "ARCHITECTURE_MUTATION"): "watch cannot mutate architecture",
    ("ESCALATION_REVIEW", "TRANSFORMATION_WINDOW"): "must pass through TRANSFORMATION_CANDIDATE",
    ("TRANSFORMATION_CANDIDATE", "NEW_STABLE"): "window + reconsolidation required",
    ("TRANSFORMATION_WINDOW", "CAPITAL_MUTATION"): "window grants no capital authority",
    ("WATCH", "NEW_STABLE"): "no direct watch -> new-stable",
    ("STABLE", "PLURAL_MODEL_STATE"): "pluralism emerges from reconsolidation, not STABLE",
}


@dataclass(frozen=True)
class PhaseEdgeTable:
    contract_version: str
    status_on_edge_table: str  # PROVISIONAL / v2 ...
    legal_edges: Mapping[str, FrozenSet[str]]
    source_docs: Tuple[str, ...] = ("OCE_ARCHITECTURE_AMENDMENT_A010_v1.0 SS3", "OCE_INSTITUTIONAL_STRESS_SUITE_BOOK_v1.0 SS5")

    @classmethod
    def default(cls) -> "PhaseEdgeTable":
        return PhaseEdgeTable(
            contract_version=PHASE_EDGE_TABLE_CONTRACT,
            status_on_edge_table=PROVISIONAL,
            legal_edges={k: frozenset(v) for k, v in DEFAULT_PHASE_EDGES.items()},
        )


class PhaseDecisionError(ValueError):
    pass


class PhaseDecisionRecord:
    """A-010 decision for one attempted phase step. Preserves the evidence-channel
    vector; NO scalar may possess transition authority (G1 requirement §7)."""

    def __init__(
        self,
        decision_id: str,
        seq: int,
        phase_from: str,
        phase_to: str,
        allowed: bool,
        evidence_vector: Mapping[str, str],
        evidence_refs: List[str],
        authority_level: str,
        operator_required: bool,
        rationale: str,
        mutation_class: str,
        contract_version: str,
    ):
        self.decision_id = decision_id
        self.seq = seq
        self.phase_from = phase_from
        self.phase_to = phase_to
        self.allowed = allowed
        self.evidence_vector = dict(evidence_vector)
        self.evidence_refs = list(evidence_refs)
        self.authority_level = authority_level
        self.operator_required = operator_required
        self.rationale = rationale
        self.mutation_class = mutation_class
        self.contract_version = contract_version

    def to_dict(self) -> dict:
        return asdict(self)

    # a scalar is never authoritative in G1; this is an operator-view summary only
    def operator_scalar_summary(self) -> float:
        """EXPERIMENTAL / NON-AUTHORITATIVE. Never used for phase transitions."""
        raise PhaseDecisionError("no scalar may possess transition authority in G1")


class PhaseStateMachine:
    """Owns current phase state and validates transitions against an edge table.

    The machine is a pure state holder + legality checker. It does not decide
    WHY a transition is warranted — callees supply the evidence vector — and it
    never writes authority or knowledge states.
    """

    def __init__(self, edge_table: Optional[PhaseEdgeTable] = None, initial: str = "STABLE"):
        self.edge_table = edge_table or PhaseEdgeTable.default()
        self.state: str = initial
        self.decisions: List[PhaseDecisionRecord] = []

    def legal_transitions(self) -> FrozenSet[str]:
        return self.edge_table.legal_edges.get(self.state, frozenset())

    def can_transition(self, to_state: str) -> bool:
        return to_state in self.legal_transitions()

    def attempt(
        self,
        seq: int,
        actor: str,
        to_state: str,
        evidence_vector: Mapping[str, str],
        authority_level: str,
        mutation_class: str,
        operator_required: bool = False,
        evidence_refs: Optional[List[str]] = None,
        reason: str = "",
        timestamp: Optional[str] = None,
        allowed_edges_override: Optional[Mapping[str, FrozenSet[str]]] = None,
    ) -> PhaseDecisionRecord:
        """Validate + record one phase step. Returns the decision; applies only
        if allowed. `allowed_edges_override` is scoped to the caller's evaluation
        contract (G1 eval-contract freeze)."""
        edge_set = allowed_edges_override or self.edge_table.legal_edges
        from_state = self.state
        from_set = edge_set.get(from_state, frozenset())
        legal = to_state in from_set

        forbidden_reason = None
        if not legal:
            forbidden_reason = FORBIDDEN_PHASE_EDGES.get((from_state, to_state)) or "edge absent from phase graph"
        elif self._is_capital_shortcut(from_state, to_state, mutation_class):
            legal = False
            forbidden_reason = "TRANSFORMATION_WINDOW -> capital authority is forbidden"

        decision = PhaseDecisionRecord(
            decision_id=deterministic_hex("phase", from_state, to_state, seq),
            seq=seq,
            phase_from=from_state,
            phase_to=to_state,
            allowed=legal,
            evidence_vector=evidence_vector,
            evidence_refs=evidence_refs or [],
            authority_level=authority_level,
            operator_required=operator_required,
            rationale=reason or ("" if legal else (forbidden_reason or "forbidden")),
            mutation_class=mutation_class,
            contract_version=self.edge_table.contract_version,
        )
        self.decisions.append(decision)
        if legal:
            if authority_level not in AuthorityLevel.__members__:
                raise PhaseDecisionError(f"unknown authority level: {authority_level}")
            if mutation_class == MutationClass.CAPITAL_MUTATION.value:
                # even in a legal phase target, capital is a separate authority gate
                legal = False
                decision.rationale = "capital mutation requires separate authority gate (never implied by phase)"
        if legal:
            self.state = to_state
        return decision

    @staticmethod
    def _is_capital_shortcut(from_state: str, to_state: str, mutation_class: str) -> bool:
        if mutation_class == MutationClass.CAPITAL_MUTATION.value:
            if from_state in ("STABLE", "WATCH", "TRANSFORMATION_WINDOW", "TRANSFORMATION_CANDIDATE"):
                return True
        return False


# Falsification note: M5 is intentionally agnostic to "architecture mutation"
# legality; that is the job of the ForbiddenTransitionValidator (engine.forbidden)
# and the authority firewall, not the phase graph. This keeps phase legality a
# pure topology property while mutation/authority semantics stay separated.