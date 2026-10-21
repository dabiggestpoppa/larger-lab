"""SQLite adapter for the evidence metadata store (ADR-0006).

Implements ``EvidenceRepository`` and ``LifecycleLogRepository`` from
``qcae.core.ports``. Design laws:

- **No UPDATE statements exist for factual payloads.** Records are inserted
  once and immutable; corrections create new records + lineage. Only the
  append-only ``freshness_log`` grows over time (§14 append/supersede law).

- **Row-integrity:** each row stores the record's canonical sha256 (computed
  from ``SerializableRecord.digest()`` at write time). Every read re-serializes
  the payload and re-verifies, so out-of-band database edits fail loudly
  (Book V 13.3 auditability).

- **Parameterized SQL everywhere**; the only caller-supplied values reach the
  engine as bound parameters.

- **One connection per store instance** with WAL journaling; transaction
  boundaries are owned by the unit-of-work layer (P1-C09), so repository
  methods run in autocommit unless an ambient transaction is open.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from qcae.core.evidence import EvidenceArtifact, EvidenceObjectType, FreshnessState
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.evidence_registry import (
    EvidenceRepository,
    FreshnessChangeEvent,
    LifecycleLogRepository,
)
from qcae.core.serialization import QcaeSerializationError
from qcae.core.vocabulary import EvidenceClass

__all__ = ["SqliteEvidenceRepository", "SqliteLifecycleLogRepository", "SCHEMA_VERSION"]

#: Metadata schema version (see PRAGMA user_version; migration ledger P1-C10).
SCHEMA_VERSION = 1

_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS evidence_artifact (
    evidence_id      TEXT PRIMARY KEY,
    subject_id       TEXT NOT NULL,
    object_type      TEXT NOT NULL,
    evidence_class   TEXT NOT NULL,
    artifact_digest  TEXT NOT NULL,
    producer         TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    external_owner_domain TEXT NOT NULL DEFAULT '',
    payload_json     TEXT NOT NULL,
    payload_digest   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_evidence_subject ON evidence_artifact(subject_id);
CREATE INDEX IF NOT EXISTS ix_evidence_otype   ON evidence_artifact(object_type);
CREATE INDEX IF NOT EXISTS ix_evidence_class   ON evidence_artifact(evidence_class);
CREATE INDEX IF NOT EXISTS ix_evidence_owner   ON evidence_artifact(external_owner_domain);

CREATE TABLE IF NOT EXISTS freshness_log (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id  TEXT NOT NULL,
    from_state   TEXT,
    to_state     TEXT NOT NULL,
    reason       TEXT NOT NULL,
    changed_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_freshness_eid ON freshness_log(evidence_id);
"""

_DOCUMENTED_NO_UPDATE = (
    "append-only store: factual rows are never updated (P1 spec §14); "
    "freshness changes append to freshness_log"
)


def _row_to_artifact(payload_json: str, payload_digest: str, evidence_id: str) -> EvidenceArtifact:
    data = json.loads(payload_json)
    try:
        artifact = EvidenceArtifact.from_dict(data)
    except (QcaeSerializationError, QcaeValidationError, KeyError, TypeError) as exc:
        raise QcaeValidationError(
            f"stored evidence {evidence_id!r} payload unreadable: {exc}"
        ) from exc
    if artifact.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored evidence {evidence_id!r} failed integrity check: "
            "payload digest mismatch (row tampered or schema drifted)"
        )
    return artifact


class SqliteEvidenceRepository(EvidenceRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, artifact: EvidenceArtifact) -> str:
        payload = json.dumps(artifact.to_dict(), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO evidence_artifact ("
                " evidence_id, subject_id, object_type, evidence_class,"
                " artifact_digest, producer, created_at, external_owner_domain,"
                " payload_json, payload_digest)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    artifact.evidence_id,
                    artifact.subject_id,
                    artifact.evidence_object_type.value,
                    artifact.evidence_class.value,
                    artifact.artifact_digest,
                    artifact.producer,
                    artifact.created_at,
                    artifact.external_owner_domain,
                    payload,
                    artifact.digest(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"evidence id {artifact.evidence_id!r} already stored "
                "(append-only store: create a superseding record instead)"
            ) from exc
        return artifact.evidence_id

    def get(self, evidence_id: str) -> Optional[EvidenceArtifact]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM evidence_artifact WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_artifact(row[0], row[1], evidence_id)

    def _select(self, where: str, params: tuple) -> List[EvidenceArtifact]:
        rows = self._conn.execute(
            "SELECT evidence_id, payload_json, payload_digest FROM evidence_artifact "
            f"WHERE {where} ORDER BY created_at, evidence_id",
            params,
        ).fetchall()
        return [_row_to_artifact(pj, pd, eid) for eid, pj, pd in rows]

    def list_by_subject(self, subject_id: str) -> List[EvidenceArtifact]:
        return self._select("subject_id = ?", (subject_id,))

    def list_by_object_type(self, object_type: EvidenceObjectType) -> List[EvidenceArtifact]:
        return self._select("object_type = ?", (object_type.value,))

    def list_by_class(self, evidence_class: EvidenceClass) -> List[EvidenceArtifact]:
        return self._select("evidence_class = ?", (evidence_class.value,))

    def list_by_subject_and_class(
        self, subject_id: str, evidence_class: EvidenceClass
    ) -> List[EvidenceArtifact]:
        return self._select(
            "subject_id = ? AND evidence_class = ?", (subject_id, evidence_class.value)
        )

    def list_superseded_by(self, superseding_id: str) -> List[EvidenceArtifact]:
        return self._select(
            "json_extract(payload_json, '$.superseded_by') = ?", (superseding_id,)
        )

    def list_external_refs(self, owner_domain: str) -> List[EvidenceArtifact]:
        return self._select("external_owner_domain = ? AND external_owner_domain != ''", (owner_domain,))

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM evidence_artifact").fetchone()
        return int(row[0])


class SqliteLifecycleLogRepository(LifecycleLogRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, event: FreshnessChangeEvent) -> None:
        self._conn.execute(
            "INSERT INTO freshness_log (evidence_id, from_state, to_state, reason, changed_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                event.evidence_id,
                event.from_state.value if event.from_state else None,
                event.to_state.value,
                event.reason,
                event.changed_at,
            ),
        )

    def history(self, evidence_id: str) -> List[FreshnessChangeEvent]:
        rows = self._conn.execute(
            "SELECT from_state, to_state, reason, changed_at FROM freshness_log"
            " WHERE evidence_id = ? ORDER BY seq",
            (evidence_id,),
        ).fetchall()
        return [
            FreshnessChangeEvent(
                evidence_id=evidence_id,
                from_state=FreshnessState(f) if f else None,
                to_state=FreshnessState(t),
                reason=reason,
                changed_at=changed_at,
            )
            for f, t, reason, changed_at in rows
        ]

    def current_freshness(self, evidence_id: str) -> FreshnessState:
        row = self._conn.execute(
            "SELECT to_state FROM freshness_log WHERE evidence_id = ?"
            " ORDER BY seq DESC LIMIT 1",
            (evidence_id,),
        ).fetchone()
        return FreshnessState(row[0]) if row else FreshnessState.CURRENT
