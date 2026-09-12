"""SQLite RepositoryRegistry — ADR-0007 two-level identity model (P1-R1 §1–§5).

- ``repository_record``: the *identity* table. One row per stable
  ``repository_id`` (immutable first registration; identity attributes
  source_kind/canonical_locator are unique and immutable — locator migration
  happens via explicit supersession, never by editing).
- ``repository_revision``: the *revision* table. One immutable, digest-verified
  row per observed revision, keyed by
  ``repository_revision_id = repository_id + "@" + revision``.

ONE repository identity -> MANY immutable revision records. A new commit SHA
is a new revision of a known repository, never a new repository.

"Latest" is resolved ONLY by explicit observation metadata (last_observed_at,
then first_seen_at, then repository_revision_id as deterministic tie-break) —
never by revision-string lexical order (§5). If no observation ordering was
recorded, latest_observation() refuses rather than guessing.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.ports.repository_registry import RepositoryRegistryPort

__all__ = ["SqliteRepositoryRegistry", "REPOSITORY_REGISTRY_DDL"]

REPOSITORY_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS repository_record (
    repository_id   TEXT PRIMARY KEY,
    source_kind     TEXT NOT NULL,
    canonical_locator TEXT NOT NULL,
    revision        TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    UNIQUE (source_kind, canonical_locator)
);
CREATE INDEX IF NOT EXISTS ix_repo_locator ON repository_record(canonical_locator);
CREATE INDEX IF NOT EXISTS ix_repo_kind ON repository_record(source_kind);

CREATE TABLE IF NOT EXISTS repository_revision (
    repository_revision_id TEXT PRIMARY KEY,
    repository_id          TEXT NOT NULL,
    revision               TEXT NOT NULL,
    payload_json           TEXT NOT NULL,
    payload_digest         TEXT NOT NULL,
    UNIQUE (repository_id, revision)
);
CREATE INDEX IF NOT EXISTS ix_repo_revision_identity
    ON repository_revision(repository_id);
"""


def _revision_id(repository_id: str, revision: str) -> str:
    return f"{repository_id}@{revision}"


def _decode(payload_json: str, payload_digest: str, key: str) -> RepositoryRecord:
    record = RepositoryRecord.from_dict(json.loads(payload_json))
    if record.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored repository record {key!r} failed integrity check (digest mismatch)"
        )
    return record


class SqliteRepositoryRegistry(RepositoryRegistryPort):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- write path -----------------------------------------------------------

    def add(self, record: RepositoryRecord) -> str:
        """Record one observation of one revision (ADR-0007).

        1. The immutable revision row is inserted (idempotent for identical
           content; conflicting content under the same identity+revision is a
           rewrite attempt and is rejected).
        2. The identity row is inserted on first sight of the repository_id.
           Its identity attributes (source_kind, canonical_locator) are
           immutable afterwards; a later observation carrying different
           identity attributes is rejected — locator migration requires an
           explicit superseding identity.
        """
        record.validate()
        payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
        digest = record.digest()
        rid = _revision_id(record.repository_id, record.revision)
        try:
            self._conn.execute(
                "INSERT INTO repository_revision (repository_revision_id,"
                " repository_id, revision, payload_json, payload_digest)"
                " VALUES (?, ?, ?, ?, ?)",
                (rid, record.repository_id, record.revision, payload, digest),
            )
        except sqlite3.IntegrityError:
            existing = self._conn.execute(
                "SELECT payload_digest FROM repository_revision"
                " WHERE repository_revision_id = ?",
                (rid,),
            ).fetchone()
            if existing and existing[0] == digest:
                pass  # idempotent identical re-observation
            else:
                raise QcaeValidationError(
                    f"repository revision {rid!r} already stored with different "
                    "content; observations are immutable"
                )
        identity = self._conn.execute(
            "SELECT source_kind, canonical_locator FROM repository_record"
            " WHERE repository_id = ?",
            (record.repository_id,),
        ).fetchone()
        if identity is None:
            try:
                self._conn.execute(
                    "INSERT INTO repository_record (repository_id, source_kind,"
                    " canonical_locator, revision, payload_json, payload_digest)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (record.repository_id, record.source_kind.value,
                     record.canonical_locator, record.revision, payload, digest),
                )
            except sqlite3.IntegrityError as exc:
                # locator claimed by a different identity
                raise QcaeValidationError(
                    f"canonical locator {record.canonical_locator!r} already "
                    "registered to a different repository identity"
                ) from exc
        elif (identity[0] != record.source_kind.value
              or identity[1] != record.canonical_locator):
            raise QcaeValidationError(
                f"repository identity {record.repository_id!r} is registered as "
                f"({identity[0]}, {identity[1]}); identity attributes are "
                "immutable — supersede the identity instead of editing it"
            )
        return rid

    # -- identity-level reads ---------------------------------------------------

    def get(self, repository_id: str) -> Optional[RepositoryRecord]:
        """The identity record (first registration)."""
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM repository_record"
            " WHERE repository_id = ?",
            (repository_id,),
        ).fetchone()
        return _decode(row[0], row[1], repository_id) if row else None

    def get_by_locator(self, source_kind, canonical_locator: str, revision: str = "") -> Optional[RepositoryRecord]:
        identity = self._conn.execute(
            "SELECT repository_id, payload_json, payload_digest FROM repository_record"
            " WHERE source_kind = ? AND canonical_locator = ?",
            (source_kind.value, canonical_locator),
        ).fetchone()
        if identity is None:
            return None
        if not revision:
            return _decode(identity[1], identity[2], canonical_locator)
        return self.get_revision_of(identity[0], revision)

    def list_by_source_kind(self, source_kind) -> List[RepositoryRecord]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM repository_record"
            " WHERE source_kind = ? ORDER BY canonical_locator",
            (source_kind.value,),
        ).fetchall()
        return [_decode(r[0], r[1], source_kind.value) for r in rows]

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM repository_record").fetchone()
        return int(row[0])

    # -- revision-level reads -----------------------------------------------------

    def get_revision(self, repository_revision_id: str) -> Optional[RepositoryRecord]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM repository_revision"
            " WHERE repository_revision_id = ?",
            (repository_revision_id,),
        ).fetchone()
        return _decode(row[0], row[1], repository_revision_id) if row else None

    def get_revision_of(self, repository_id: str, revision: str) -> Optional[RepositoryRecord]:
        return self.get_revision(_revision_id(repository_id, revision))

    def list_revisions(self, repository_id: str) -> List[RepositoryRecord]:
        """Full revision history for one identity, oldest observation first.

        Ordered by explicit observation metadata (then revision_id as
        deterministic tie-break) — never by revision string.
        """
        rows = self._conn.execute(
            "SELECT r.payload_json, r.payload_digest FROM repository_revision r"
            " JOIN repository_record i ON i.repository_id = r.repository_id"
            " WHERE r.repository_id = ?"
            " ORDER BY json_extract(r.payload_json, '$.last_observed_at'),"
            "          json_extract(r.payload_json, '$.first_seen_at'),"
            "          r.repository_revision_id",
            (repository_id,),
        ).fetchall()
        return [_decode(r[0], r[1], repository_id) for r in rows]

    def latest_observation(self, repository_id: str) -> Optional[RepositoryRecord]:
        """Most recently observed revision by explicit observation metadata.

        Refuses to guess (§5): if multiple revisions exist and none carries
        observation timestamps, the caller must request an exact revision.
        A single-revision history is unambiguous and is returned.
        """
        history = self.list_revisions(repository_id)
        if not history:
            return None
        if len(history) == 1:
            return history[0]
        observed = [
            r for r in history
            if r.last_observed_at or r.first_seen_at
        ]
        if not observed:
            raise QcaeValidationError(
                f"repository {repository_id!r} has {len(history)} revisions but "
                "no observation timestamps; specify an exact revision (latest "
                "cannot be guessed from revision strings)"
            )
        # list_revisions already orders by observation metadata
        return history[-1]
