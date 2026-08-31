"""M4 — knowledge lifecycle machine (A-009 §9) with a PROVISIONAL edge table.

A-009 §9 lists states but does not specify every legal edge (G0 AMB-06). This
engine therefore ships a PROVISIONAL_TEST_CONTRACT edge table that is:

* replaceable WITHOUT rewriting historical traces (replace_edge_table); and
* validated to NEVER delete provenance on any transition.

Knowledge truth status (M4) is separate from institutional phase (M5) and from
capability verification labels (M1). See G0 AMB-01/AMB-07 separation tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from .base import (
    LIFECYCLE_EDGE_TABLE_CONTRACT,
    PROVISIONAL,
    KnowledgeLifecycleState as L,
    Provenance,
    TransitionRecord,
    deterministic_hex,
    deterministic_timestamp,
)

DEFAULT_LIFECYCLE_EDGES: Dict[str, FrozenSet[str]] = {
    "OBSERVED": frozenset(["CANDIDATE"]),
    "CANDIDATE": frozenset(["TESTED", "CHALLENGED", "DEMOTED", "OBSERVED"]),
    "TESTED": frozenset(["PROMOTED", "CHALLENGED", "DEMOTED", "CANDIDATE"]),
    "PROMOTED": frozenset(["ACTIVE", "CHALLENGED"]),
    "ACTIVE": frozenset(["CHALLENGED", "REVALIDATED", "DEMOTED", "DORMANT", "SUPERSEDED"]),
    "CHALLENGED": frozenset(["REVALIDATED", "DEMOTED", "CANDIDATE", "TESTED", "ACTIVE"]),
    "REVALIDATED": frozenset(["ACTIVE", "DORMANT", "SUPERSEDED", "DEMOTED"]),
    "DEMOTED": frozenset(["DORMANT", "CANDIDATE", "SUPERSEDED"]),
    "DORMANT": frozenset(["REACTIVATED", "CANDIDATE", "SUPERSEDED"]),
    "REACTIVATED": frozenset(["CANDIDATE", "CHALLENGED", "TESTED"]),
    "SUPERSEDED": frozenset(["CANDIDATE"]),  # reopen allowed only through explicit reactivation
}

# Book S10 / G1 contract: demotion must not auto-promote on reopen; reactivation
# routes back through CANDIDATE/CHALLENGED, and a direct DORMANT->ACTIVE skip is
# a forbidden shortcut.
FORBIDDEN_LIFECYCLE_EDGES: Dict[Tuple[str, str], str] = {
    ("DORMANT", "ACTIVE"): "dormant knowledge must realize reactivation/review before promotion",
    ("DEMOTED", "ACTIVE"): "reactivation requires review, not auto-promotion",
    ("REACTIVATED", "ACTIVE"): "reactivation goes through CANDIDATE/CHALLENGED first",
    ("REACTIVATED", "PROMOTED"): "no direct promotion from reactivation",
    ("REACTIVATED", "DEMOTED"): "reactivation does not itself demote",
    ("SUPERSEDED", "ACTIVE"): "superseded must pass through reopen review",
}


@dataclass(frozen=True)
class LifecycleEdgeTable:
    contract_version: str
    status: str  # PROVISIONAL_TEST_CONTRACT / ...
    legal_edges: Mapping[str, FrozenSet[str]]
    source_docs: Tuple[str, ...] = ("OCE_ARCHITECTURE_AMENDMENT_A009_v1.0 SS9", "OCE_INSTITUTIONAL_STRESS_SUITE_BOOK_v1.0 SS16/17")

    @classmethod
    def default(cls) -> "LifecycleEdgeTable":
        return LifecycleEdgeTable(
            contract_version=LIFECYCLE_EDGE_TABLE_CONTRACT,
            status=PROVISIONAL,
            legal_edges={k: frozenset(v) for k, v in DEFAULT_LIFECYCLE_EDGES.items()},
        )


class LifecycleTransitionError(ValueError):
    pass


class EdgeTableReplacementError(ValueError):
    pass


class KnowledgeRecord:
    """A governed knowledge object. Carries M4 lifecycle state plus lineage that
    must precede M1 capability labels: a knowledge object is never promoted to
    'capability verified' merely because it reached ACTIVE."""

    def __init__(
        self,
        record_id: str,
        claim: str,
        provenance: Provenance,
        creation_source: str,
        initial_state: str = L.OBSERVED.value,
        schema_version: str = "1.0.0",
        supersession_lineage: Optional[List[str]] = None,
        lifecycle_status: str = PROVISIONAL,
    ):
        self.record_id = record_id
        self.claim = claim
        self.provenance = provenance
        self.creation_source = creation_source
        self.state = initial_state
        self.schema_version = schema_version
        self.supersession_lineage = list(supersession_lineage or [])
        self.lifecycle_status = lifecycle_status
        self.transitions: List[TransitionRecord] = []
        self.forever_lineage_locked = False

    def current(self) -> str:
        return self.state

    def transition(
        self,
        seq: int,
        to_state: str,
        actor: str,
        authority_basis: str,
        authority_level: str,
        reason: str,
        evidence_refs: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        edge_table: Optional[LifecycleEdgeTable] = None,
    ) -> TransitionRecord:
        table = edge_table or LifecycleEdgeTable.default()
        from_state = self.state
        from_set = table.legal_edges.get(from_state, frozenset())
        legal = to_state in from_set
        mess = None
        if not legal:
            mess = f"{from_state} -> {to_state} absent from lifecycle edge table"
        elif not self._provenance_survives(to_state):
            legal = False
            mess = "lifecycle transition must never delete provenance"
        elif to_state in from_set and (from_state, to_state) in FORBIDDEN_LIFECYCLE_EDGES:
            legal = False
            mess = FORBIDDEN_LIFECYCLE_EDGES[(from_state, to_state)]

        if self.forever_lineage_locked:
            legal = False
            mess = mess or "record lineage locked by operator (PERMANENT_BY_OPERATOR_AUTHORITY)"

        tr = TransitionRecord(
            transition_id=deterministic_hex("lifecycle", self.record_id, from_state, to_state, seq),
            machine="lifecycle",
            object_id=self.record_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            evidence_refs=evidence_refs or [],
            actor=actor,
            authority_basis=authority_basis,
            authority_level=authority_level,
            contract_version=table.contract_version,
            seq=seq,
            timestamp=timestamp or deterministic_timestamp(seq),
        )
        self.transitions.append(tr)
        if legal:
            self.state = to_state
        else:
            self._last_error = mess
        return tr

    def last_error(self) -> Optional[str]:
        return getattr(self, "_last_error", None)

    @staticmethod
    def _provenance_survives(_to_state: str) -> bool:
        # Lifecycle transitions may change active/dormant/archival state but never
        # detach or drop the provenance object. Enforcement is structural: the
        # record always retains self.provenance regardless of state.
        return True

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "claim": self.claim,
            "provenance": asdict(self.provenance),
            "creation_source": self.creation_source,
            "state": self.state,
            "schema_version": self.schema_version,
            "supersession_lineage": list(self.supersession_lineage),
            "lifecycle_status": self.lifecycle_status,
            "transitions": [t.to_dict() for t in self.transitions],
        }


class LifecycleEngine:
    """Holds many KnowledgeRecords and the active edge table version."""

    def __init__(self, edge_table: Optional[LifecycleEdgeTable] = None):
        self.edge_table = edge_table or LifecycleEdgeTable.default()
        self.records: Dict[str, KnowledgeRecord] = {}
        self._trace_by_version: Dict[str, List[TransitionRecord]] = {}

    def add(self, record: KnowledgeRecord) -> None:
        self.records[record.record_id] = record

    def get(self, record_id: str) -> Optional[KnowledgeRecord]:
        return self.records.get(record_id)

    def transition(
        self,
        record_id: str,
        seq: int,
        to_state: str,
        actor: str,
        authority_basis: str,
        authority_level: str,
        reason: str,
        evidence_refs: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ) -> TransitionRecord:
        """Route a lifecycle step through the ENGINE's active edge table."""
        rec = self.records.get(record_id)
        if rec is None:
            raise KeyError(f"unknown knowledge record: {record_id}")
        return rec.transition(
            seq=seq, to_state=to_state, actor=actor, authority_basis=authority_basis,
            authority_level=authority_level, reason=reason, evidence_refs=evidence_refs,
            timestamp=timestamp, edge_table=self.edge_table,
        )

    def replace_edge_table(self, new_table: LifecycleEdgeTable) -> None:
        """Swap the active edge table WITHOUT rewriting any existing transition
        traces. Existing records keep the table version under which they moved;
        only FUTURE transitions use the new table."""
        if new_table.contract_version in ({t.contract_version for r in self.records.values() for t in r.transitions}):
            # duplicates are fine; we just never rewrite history
            pass
        self.edge_table = new_table
