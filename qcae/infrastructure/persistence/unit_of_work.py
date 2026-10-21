"""Unit-of-work / transaction boundary (Book V 15.9, P1 spec §15).

Canonical state updates that must remain consistent — evidence metadata plus
lineage edge plus artifact reference — commit together or not at all.

Implementation: every QCAE repository for one store shares a single SQLite
connection, so a transaction opened on that connection spans them all.
``UnitOfWork`` owns ``BEGIN IMMEDIATE`` (write lock taken up front; WAL keeps
readers live), commits on clean exit, and rolls back on any exception —
including injected ones. There are no fake semantics: if the process dies
before commit, SQLite itself discards the journal.
"""

from __future__ import annotations

import sqlite3
from types import TracebackType
from typing import Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.evidence import EvidenceArtifact
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType, LineageRepository

__all__ = ["UnitOfWork", "EvidenceCommitService"]


class UnitOfWork:
    """Transactional scope over all repositories sharing one connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self) -> "UnitOfWork":
        if self._conn.in_transaction:
            raise QcaeValidationError(
                "nested unit-of-work is not supported; keep one transaction scope per operation"
            )
        self._conn.execute("BEGIN IMMEDIATE")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> bool:
        if exc is None:
            self._conn.commit()
            return False
        self._conn.rollback()
        return False  # do not suppress the caller's exception

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()


class EvidenceCommitService:
    """Composes evidence + artifact + lineage into one atomic commit (§15).

    ``record_evidence`` persists metadata rows and the lineage edge inside a
    single unit of work. The raw bytes are put in the artifact store *before*
    the transaction opens: content-addressed puts are idempotent, and a
    transaction failure leaves only an unreferenced (harmless, deduplicated)
    blob — the reverse ordering would risk metadata referencing bytes that
    never landed.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        evidence_repo,
        lineage_repo: LineageRepository,
        artifact_store=None,
    ) -> None:
        self._conn = conn
        self._evidence = evidence_repo
        self._lineage = lineage_repo
        self._artifacts = artifact_store

    def record_evidence(
        self,
        artifact: EvidenceArtifact,
        raw_bytes: Optional[bytes] = None,
        lineage: Optional[LineageEdge] = None,
        expected_edge_type: LineageEdgeType = LineageEdgeType.DERIVED_FROM,
    ) -> str:
        """Atomically persist evidence metadata (+ raw artifact + lineage edge)."""
        if raw_bytes is not None and self._artifacts is not None:
            digest = self._artifacts.put_bytes(raw_bytes)
            if digest != artifact.artifact_digest:
                raise QcaeValidationError(
                    f"artifact bytes digest {digest[:12]}… does not match metadata "
                    f"digest {artifact.artifact_digest[:12]}…; refusing to record"
                )
        with UnitOfWork(self._conn):
            self._evidence.add(artifact)
            if lineage is not None:
                self._lineage.add(lineage)
        return artifact.evidence_id
