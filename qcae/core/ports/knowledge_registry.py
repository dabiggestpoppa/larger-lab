"""Knowledge/registry persistence ports (Book V 15.9, Book IV 9.3–9.7)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from qcae.core.knowledge import NegativeKnowledge, PositiveKnowledge
from qcae.core.knowledge.memory import NegativeKnowledgeType
from qcae.core.receipts import CapabilityReceipt, ReceiptState

__all__ = [
    "NegativeKnowledgeRepository",
    "PositiveKnowledgeRepository",
    "ReceiptRepository",
    "RegistryQuery",
]


class NegativeKnowledgeRepository(ABC):
    """First-class storage/retrieval for negative knowledge (15.9 invariant 4)."""

    @abstractmethod
    def add(self, record: NegativeKnowledge) -> str:
        """Persist a negative-knowledge record (append-only)."""

    @abstractmethod
    def get(self, record_id: str) -> Optional[NegativeKnowledge]:
        """Fetch by ID with integrity verification."""

    @abstractmethod
    def find_by_subject(self, subject_id: str, source_revision: str = "") -> List[NegativeKnowledge]:
        """Anti-loop check: has this source/revision already failed?"""

    @abstractmethod
    def find_by_failure_type(self, failure_type: NegativeKnowledgeType) -> List[NegativeKnowledge]:
        """All records of one failure category."""

    @abstractmethod
    def active(self) -> List[NegativeKnowledge]:
        """Records not superseded (current rejections)."""


class PositiveKnowledgeRepository(ABC):
    """First-class storage/retrieval for evidence-linked positive knowledge."""

    @abstractmethod
    def add(self, record: PositiveKnowledge) -> str:
        """Persist a positive-knowledge record (append-only)."""

    @abstractmethod
    def get(self, record_id: str) -> Optional[PositiveKnowledge]:
        """Fetch by ID with integrity verification."""

    @abstractmethod
    def find_by_subject(self, subject_id: str) -> List[PositiveKnowledge]:
        """Knowledge about one implementation/revision subject."""

    @abstractmethod
    def find_by_contract(self, contract_id: str, contract_version: str = "") -> List[PositiveKnowledge]:
        """Knowledge under one contract (optionally pinned version)."""

    @abstractmethod
    def material(self) -> List[PositiveKnowledge]:
        """Only evidence-linked material knowledge (notes excluded)."""


class ReceiptRepository(ABC):
    """Durable receipt storage with state-aware retrieval."""

    @abstractmethod
    def add(self, receipt: CapabilityReceipt) -> str:
        """Persist a receipt (append-only; new states mean new records)."""

    @abstractmethod
    def get(self, receipt_id: str) -> Optional[CapabilityReceipt]:
        """Fetch by ID with integrity verification."""

    @abstractmethod
    def find_by_capability(self, capability_id: str) -> List[CapabilityReceipt]:
        """All receipts for a capability (all states)."""

    @abstractmethod
    def find_by_state(self, state: ReceiptState) -> List[CapabilityReceipt]:
        """All receipts in one state (e.g. currently ACTIVE)."""

    @abstractmethod
    def active_for_capability(self, capability_id: str) -> List[CapabilityReceipt]:
        """ACTIVE receipts only — stale/superseded/revoked excluded."""

    @abstractmethod
    def superseded_by(self, receipt_id: str) -> List[CapabilityReceipt]:
        """Receipts whose supersedes_receipt points at ``receipt_id``."""


class RegistryQuery(ABC):
    """Retrieval-order support (Book IV 9.7, P1 spec §18).

    Answers "do we already know enough to avoid external discovery?" with
    structured findings — never an LLM yes/no.
    """

    @abstractmethod
    def decision_reuse_findings(self, capability_id: str, contract_id: str, contract_version: str) -> dict:
        """Assemble 9.7 retrieval-order layers for one request.

        Returns a dict with keys:

        - ``active_receipts``: ACTIVE receipts matching capability+contract;
        - ``positive_knowledge``: material knowledge under the contract;
        - ``negative_blocks``: active negative knowledge whose retry_allowed
          is False for the same source/revision (discovery should not rerun);
        - ``stale_evidence``: evidence needing refresh before reuse;
        - ``sufficient_without_discovery``: bool — active receipt AND
          matching positive knowledge AND no blocking negatives.
        """
