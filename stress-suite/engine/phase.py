"""M5 — Governor phase machine (A-010 §3 plus Book §5 holding/terminal states).

Owns INSTITUTIONAL PHASE ONLY. It does NOT own knowledge truth status (M4) and
must not merge capability verification (M1) into it. See G0 AMB-01/AMB-07.

HARDENING (G1R-01 / G1R-06):
  * PhaseDecisionRecord is a real dataclass with deterministic serialization.
  * The machine computes a decision *then* applies it. `decision.allowed` always
    equals whether the transition was actually authorized for application, and if
    `allowed is False` the state never changes.
  * No local flag is flipped after the decision object is produced. Invalid
    authority raises BEFORE any decision/ledger mutation (documented policy).
  * The phase machine can never grant capital: any CAPITAL_MUTATION attempt is
    denied here regardless of the (otherwise legal) edge. Cross-cutting forbidden
    policy (e.g. WATCH -> architecture mutation) lives in engine.governed and is
    composed at the governed-execution layer, keeping this machine pure topology.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
from typing import AbstractSet, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple, Any

from .base import (
    PHASE_EDGE_TABLE_CONTRACT,
    PROVISIONAL,
    AuthorityLevel,
    MutationClass,
    PhaseState,
    deterministic_hex,
)

#: legal source -> targets (PROVISIONAL_TEST_CONTRACT; see module docstring)
DEFAULT_PHASE_EDGES: Dict[str, FrozenSet[str]] = {
    "STABLE": frozenset(["WATCH", "DATA_BLOCKED"]),
    "WATCH": frozenset(["ESCALATION_REVIEW", "STABLE", "DATA_BLOCKED"]),
    "ESCALATION_REVIEW": frozenset([
        "HOMEOSTATIC_REPAIR", "TRANSFORMATION_CANDIDATE", "NO_CHANGE",
        "OPERATOR_HOLD", "AUTHORITY_BLOCKED",
    ]),
    "HOMEOSTATIC_REPAIR": frozenset(["STABLE", "WATCH"]),
    "TRANSFORMATION_CANDIDATE": frozenset([
        "TRANSFORMATION_WINDOW", "NO_CHANGE", "OPERATOR_HOLD", "AUTHORITY_BLOCKED",
    ]),
    "TRANSFORMATION_WINDOW": frozenset([
        "RECONSOLIDATION", "NO_CHANGE", "UNRESOLVED", "OPERATOR_HOLD", "AUTHORITY_BLOCKED",
    ]),
    "RECONSOLIDATION": frozenset([
        "NEW_STABLE", "ROLLBACK", "NO_CHANGE", "PLURAL_MODEL_STATE", "UNRESOLVED",
    ]),
    "NEW_STABLE": frozenset(["STABLE"]),
    "ROLLBACK": frozenset(["STABLE"]),
    "NO_CHANGE": frozenset(["STABLE"]),
    "PLURAL_MODEL_STATE": frozenset(["STABLE"]),
    "UNRESOLVED": frozenset(["STABLE"]),
    "OPERATOR_HOLD": frozenset(["ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE", "WATCH", "STABLE"]),
    "DATA_BLOCKED": frozenset(["STABLE", "WATCH"]),
    "AUTHORITY_BLOCKED": frozenset(["ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE", "STABLE"]),
}

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


@dataclass(frozen=True)
class PhaseDecisionRecord:
    """A-010 decision for one attempted phase step. A dataclass (G1R-01) with
    deterministic serialization. Preserves the evidence-channel vector; NO scalar
    may possess transition authority. `allowed` ALWAYS equals application truth."""

    decision_id: str
    seq: int
    phase_from: str
    phase_to: str
    allowed: bool
    evidence_vector: Mapping[str, str]
    evidence_refs: List[str]
    authority_level: str
    operator_required: bool
    rationale: str
    mutation_class: str
    contract_version: str
    rule_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # a scalar is never authoritative in G1; this is an operator-view summary only
    def operator_scalar_summary(self) -> float:
        raise PhaseDecisionError("no scalar may possess transition authority in G1")


class PhaseStateMachine:
    """Pure topology phase machine. evaluate() computes, record() logs,
    apply() mutates. attempt() = evaluate + record + apply for low-level tests.

    The machine never decides WHY a transition is warranted and never grants
    capital or authority; those are composed by the governed executor."""

    def __init__(self, edge_table: Optional[PhaseEdgeTable] = None, initial: str = "STABLE"):
        self.edge_table = edge_table or PhaseEdgeTable.default()
        self.state: str = initial
        self.decisions: List[PhaseDecisionRecord] = []

    def legal_transitions(self) -> FrozenSet[str]:
        return self.edge_table.legal_edges.get(self.state, frozenset())

    def can_transition(self, to_state: str) -> bool:
        return to_state in self.legal_transitions()

    # ------------------------------------------------------------------ #
    # pure evaluation: no ledger, no state change
    # ------------------------------------------------------------------ #
    def evaluate(
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
        decision_id: Optional[str] = None,
    ) -> PhaseDecisionRecord:
        from_state = self.state

        # Policy G1R-06: invalid authority raises BEFORE any ledger mutation so an
        # ambiguous partially-committed decision can never exist.
        if authority_level not in AuthorityLevel.__members__:
            raise PhaseDecisionError(f"unknown authority level: {authority_level}")

        from_set = allowed_edges_override or self.edge_table.legal_edges
        legal_edge = to_state in from_set.get(from_state, frozenset())
        capital_bad = mutation_class == MutationClass.CAPITAL_MUTATION.value
        allowed = legal_edge and not capital_bad

        if not legal_edge:
            why = FORBIDDEN_PHASE_EDGES.get((from_state, to_state)) or "edge absent from phase graph"
        elif capital_bad:
            why = "capital mutation is never implied by a phase transition"
        else:
            why = reason

        return PhaseDecisionRecord(
            decision_id=decision_id or deterministic_hex("phase", from_state, to_state, seq),
            seq=seq,
            phase_from=from_state,
            phase_to=to_state,
            allowed=allowed,
            evidence_vector=dict(evidence_vector),
            evidence_refs=list(evidence_refs or []),
            authority_level=authority_level,
            operator_required=operator_required,
            rationale=why,
            mutation_class=mutation_class,
            contract_version=self.edge_table.contract_version,
        )

    def record(self, decision: PhaseDecisionRecord) -> None:
        self.decisions.append(decision)

    def apply(self, decision: PhaseDecisionRecord) -> None:
        if decision.allowed:
            self.state = decision.phase_to

    def attempt(self, **kw) -> PhaseDecisionRecord:
        """Low-level convenience: evaluate + record + apply. Kept for unit tests
        of the pure machine; the governed replay path uses evaluate/record/apply."""
        decision = self.evaluate(**kw)
        self.record(decision)
        self.apply(decision)
        return decision

    def apply_authoritative(self, decision: PhaseDecisionRecord) -> None:
        """Governed-executor path: record the FINAL decision (which may carry
        rule_ids and a flipped allowed flag decided above this machine) then apply
        exactly according to decision.allowed."""
        self.record(decision)
        self.apply(decision)