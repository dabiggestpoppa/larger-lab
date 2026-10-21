"""Evidence-layer ports and services (Book V 15.9).

Repository interfaces here are engine-agnostic; concrete adapters live under
``qcae/infrastructure/persistence/`` (15.9: engine implementations live under
infrastructure). Domain and service code depends only on these ports.

Two immutable-store laws every repository documents contractually:

- **Append/supersede (§14):** factual historical records are never updated.
  New information creates new records plus explicit SUPERSEDES lineage.
  Corrections of *operational standing* (stale/revalidate/reinstate) are
  append-only lifecycle-log entries, never payload rewrites.

- **Row-integrity (13.3):** every stored record carries a canonical digest;
  retrieval re-verifies it so out-of-band tampering is detected on read.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from qcae.core.evidence import EvidenceArtifact, EvidenceObjectType, FreshnessState
from qcae.core.vocabulary import EvidenceClass

__all__ = [
    "EvidenceRepository",
    "LifecycleLogRepository",
    "FreshnessChangeEvent",
]


class EvidenceRepository(ABC):
    """Durable storage for EvidenceArtifact records (append-oriented)."""

    @abstractmethod
    def add(self, artifact: EvidenceArtifact) -> str:
        """Persist a new record. Rejects duplicate evidence_id. Returns id."""

    @abstractmethod
    def get(self, evidence_id: str) -> Optional[EvidenceArtifact]:
        """Fetch by canonical ID, verifying row digest. None if absent."""

    @abstractmethod
    def list_by_subject(self, subject_id: str) -> List[EvidenceArtifact]:
        """All evidence for a subject (atom/candidate/decision/...)."""

    @abstractmethod
    def list_by_object_type(self, object_type: EvidenceObjectType) -> List[EvidenceArtifact]:
        """All evidence of one object type."""

    @abstractmethod
    def list_by_class(self, evidence_class: EvidenceClass) -> List[EvidenceArtifact]:
        """All evidence of one strength class."""

    @abstractmethod
    def list_by_subject_and_class(
        self, subject_id: str, evidence_class: EvidenceClass
    ) -> List[EvidenceArtifact]:
        """Strength-filtered subject retrieval."""

    @abstractmethod
    def list_superseded_by(self, superseding_id: str) -> List[EvidenceArtifact]:
        """Records whose superseded_by pointer names ``superseding_id``."""

    @abstractmethod
    def list_external_refs(self, owner_domain: str) -> List[EvidenceArtifact]:
        """Evidence records referencing an external owner domain (A-001)."""

    @abstractmethod
    def count(self) -> int:
        """Total stored evidence records."""


class FreshnessChangeEvent:
    """One append-only entry in a subject's freshness lifecycle log.

    The EvidenceArtifact payload is immutable; freshness transitions land
    here with reason and timestamp so history is preserved and the *current*
    standing is the latest entry (§11, §14).
    """

    __slots__ = ("evidence_id", "from_state", "to_state", "reason", "changed_at")

    def __init__(
        self,
        evidence_id: str,
        from_state: Optional[FreshnessState],
        to_state: FreshnessState,
        reason: str,
        changed_at: str,
    ) -> None:
        self.evidence_id = evidence_id
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.changed_at = changed_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FreshnessChangeEvent):
            return NotImplemented
        return (
            self.evidence_id == other.evidence_id
            and self.from_state == other.from_state
            and self.to_state == other.to_state
            and self.reason == other.reason
            and self.changed_at == other.changed_at
        )

    def __repr__(self) -> str:
        return (
            f"FreshnessChangeEvent(evidence_id={self.evidence_id!r}, "
            f"from_state={self.from_state}, to_state={self.to_state}, "
            f"reason={self.reason!r}, changed_at={self.changed_at!r})"
        )


class LifecycleLogRepository(ABC):
    """Append-only freshness/lifecycle log over evidence records."""

    @abstractmethod
    def append(self, event: FreshnessChangeEvent) -> None:
        """Record a freshness transition (append-only)."""

    @abstractmethod
    def history(self, evidence_id: str) -> List[FreshnessChangeEvent]:
        """Full transition history for one record, oldest first."""

    @abstractmethod
    def current_freshness(self, evidence_id: str) -> FreshnessState:
        """Latest logged state; CURRENT when never transitioned."""
