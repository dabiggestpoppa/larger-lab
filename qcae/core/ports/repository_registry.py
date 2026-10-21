"""RepositoryRegistry port (P1-R1 §7).

Persistence substrate for source containers. P3 discovery will write here;
P1 provides storage/retrieval only — no search, cloning, or comprehension.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from qcae.core.registry import RepositoryRecord

__all__ = ["RepositoryRegistryPort"]


class RepositoryRegistryPort(ABC):
    """Durable storage/retrieval for repository records (append-oriented)."""

    @abstractmethod
    def add(self, record: RepositoryRecord) -> str:
        """Persist one observed revision. Same identity+revision is idempotent
        only if identical; different content under the same key is rejected."""

    @abstractmethod
    def get(self, repository_id: str) -> Optional[RepositoryRecord]:
        """Fetch by internal ID (digest-verified)."""

    @abstractmethod
    def get_by_locator(
        self, source_kind, canonical_locator: str, revision: str = ""
    ) -> Optional[RepositoryRecord]:
        """Fetch by container identity, optionally pinned to one revision."""

    @abstractmethod
    def list_by_source_kind(self, source_kind) -> List[RepositoryRecord]:
        """All records of one container class."""

    @abstractmethod
    def list_revisions(self, source_kind, canonical_locator: str) -> List[RepositoryRecord]:
        """All known revisions for one repository identity (no deletion)."""

    @abstractmethod
    def count(self) -> int:
        """Total stored repository records."""
