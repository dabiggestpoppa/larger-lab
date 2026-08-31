"""Evidence objects (Stress Suite Book §4; A-004 §2 / A-010 §4).

An EvidenceRecord is attributable observation, distinct from a ConfidenceClaim
(agent confidence) and from IndependentConfirmation. The three must not be
conflated — the authority firewall and the phase machine both rely on this.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .base import EvidenceChannel, Provenance, deterministic_hex


class EvidenceStatus(str):
    pass


EVIDENCE_KINDS = ("OBSERVATION", "AGENT_CLAIM", "INDEPENDENT_CONFIRMATION", "DETERMINISTIC")


@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    schema_version: str = "1.0.0"
    kind: str = "OBSERVATION"            # see EVIDENCE_KINDS
    claim: str = ""
    provenance: Optional[Provenance] = None
    evidence_refs: List[str] = field(default_factory=list)
    status: str = "ACTIVE"               # ACTIVE / DEMOTED / DORMANT / SUPERSEDED
    seq: int = 0
    source_label: str = ""

    @classmethod
    def make(
        cls,
        seq: int,
        claim: str,
        kind: str = "OBSERVATION",
        provenance: Optional[Provenance] = None,
        source_label: str = "",
        evidence_refs: Optional[List[str]] = None,
    ) -> "EvidenceRecord":
        if kind not in EVIDENCE_KINDS:
            raise ValueError(f"unknown evidence kind: {kind}")
        return cls(
            record_id=deterministic_hex("evidence", seq, claim),
            kind=kind,
            claim=claim,
            provenance=provenance,
            evidence_refs=list(evidence_refs or []),
            seq=seq,
            source_label=source_label,
        )

    # --- conflation guards (used by authority firewall) ---------------------- #
    @property
    def is_independent_confirmation(self) -> bool:
        return self.kind == "INDEPENDENT_CONFIRMATION"


@dataclass(frozen=True)
class ContradictionRecord:
    contradiction_id: str
    schema_version: str = "1.0.0"
    claim_a: str = ""
    claim_b: str = ""
    evidence_a: List[str] = field(default_factory=list)
    evidence_b: List[str] = field(default_factory=list)
    conflict_level: str = ""       # LOCAL / DATA_QUALITY / EXPLANATORY / ONTOLOGY / AUTHORITY
    provenance: Optional[Provenance] = None
    seq: int = 0

    @classmethod
    def make(cls, seq, claim_a, claim_b, conflict_level="EXPLANATORY", provenance=None):
        return cls(
            contradiction_id=deterministic_hex("contradiction", seq, claim_a, claim_b),
            claim_a=claim_a,
            claim_b=claim_b,
            conflict_level=conflict_level,
            provenance=provenance,
            seq=seq,
        )


@dataclass(frozen=True)
class EvidenceGap:
    gap_id: str
    schema_version: str = "1.0.0"
    question: str = ""
    missing: str = ""
    target_state: str = ""         # e.g. lifecycle state or truth label it would unlock
    required_evidence_kind: str = "OBSERVATION"
    source_demand: str = ""        # SEARCH_DEMAND / RESEARCH_DEMAND (A-006)
    reopen_if: str = ""            # machine-readable reopen condition
    seq: int = 0

    @classmethod
    def make(cls, seq, question, missing, target_state="", source_demand="SEARCH_DEMAND"):
        return cls(
            gap_id=deterministic_hex("evidencegap", seq, question),
            question=question,
            missing=missing,
            target_state=target_state,
            source_demand=source_demand,
            seq=seq,
        )


class EvidenceChannelVector:
    """A-010 §4 evidence vector. Represents the 8 channels independently and
    never collapses them to an authoritative scalar. Derived operator summaries
    are explicitly NON-AUTHORITATIVE (G1 requirement §7)."""

    DEFAULT_CHANNELS = tuple(c.value for c in EvidenceChannel)

    def __init__(self, values: Optional[Mapping[str, str]] = None):
        base = {c: "LOW" for c in self.DEFAULT_CHANNELS}
        base.update(values or {})
        unknown = set(base) - set(self.DEFAULT_CHANNELS)
        if unknown:
            raise ValueError(f"unknown evidence channels: {sorted(unknown)}")
        self._vector: Dict[str, str] = base

    def channel(self, name: str) -> str:
        return self._vector[name]

    @property
    def vector(self) -> Mapping[str, str]:
        return dict(self._vector)

    def operator_summary(self) -> float:
        """EXPERIMENTAL / NON-AUTHORITATIVE. Charts the shape but is never a
        transition authority. Raising here is defensive: G1 forbids a scalar
        holding phase authority, so the machine never calls this."""
        alter = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return sum(alter[self._vector[c]] for c in self.DEFAULT_CHANNELS) / len(self.DEFAULT_CHANNELS)

    def display(self) -> Dict[str, str]:
        return self.vector