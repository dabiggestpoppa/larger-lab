"""Schema migration infrastructure (Book V 13.3, P1 spec §16).

- ``PRAGMA user_version`` pins the current schema version;
- every applied migration is appended to ``schema_migration_ledger`` with its
  identity, timestamp, and pre/post digests (transformation provenance);
- the runner refuses to run a migration whose target is not exactly
  ``current + 1`` (no skipping, no backwards, no re-runs);
- migrations record the schema version they produce; a failed migration rolls
  back inside its own transaction and leaves the ledger untouched.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from qcae.core.errors import QcaeValidationError

__all__ = ["Migration", "MigrationLedgerEntry", "MigrationRunner", "MIGRATION_LEDGER_DDL",
           "TEST_V1_TO_V2", "V2_TO_V3", "V3_TO_V4"]

MIGRATION_LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration_ledger (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    from_version   INTEGER NOT NULL,
    to_version     INTEGER NOT NULL,
    migration_id   TEXT NOT NULL,
    applied_at     TEXT NOT NULL,
    pre_digest     TEXT NOT NULL,
    post_digest    TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Migration:
    """One explicit, forward-only schema transformation."""

    from_version: int
    to_version: int
    migration_id: str
    apply: Callable[[sqlite3.Connection], None]
    description: str = ""


@dataclass(frozen=True)
class MigrationLedgerEntry:
    from_version: int
    to_version: int
    migration_id: str
    applied_at: str
    pre_digest: str
    post_digest: str


def _schema_fingerprint(conn: sqlite3.Connection) -> str:
    """Digest of table/DDL shape for provenance (content, not row data)."""
    import hashlib

    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        " ORDER BY name"
    ).fetchall()
    material = repr(rows).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


class MigrationRunner:
    def __init__(self, conn: sqlite3.Connection, clock: Callable[[], str]) -> None:
        self._conn = conn
        self._clock = clock
        conn.executescript(MIGRATION_LEDGER_DDL)

    def current_version(self) -> int:
        return int(self._conn.execute("PRAGMA user_version").fetchone()[0])

    def ledger(self) -> List[MigrationLedgerEntry]:
        rows = self._conn.execute(
            "SELECT from_version, to_version, migration_id, applied_at, pre_digest,"
            " post_digest FROM schema_migration_ledger ORDER BY seq"
        ).fetchall()
        return [MigrationLedgerEntry(*row) for row in rows]

    def migrate_to(self, target: int, migrations: Dict[int, Migration]) -> int:
        """Apply sequential migrations until ``target``. Returns new version.

        ``migrations`` is keyed by TARGET schema version (the version each
        migration produces), so lookup is always "the migration that takes
        the store to ``current + 1``".
        """
        current = self.current_version()
        if target < current:
            raise QcaeValidationError(
                f"refusing to migrate backwards ({current} -> {target})"
            )
        while current < target:
            migration = migrations.get(current + 1)
            if migration is None:
                raise QcaeValidationError(
                    f"no migration registered to take schema {current} -> {target}"
                )
            if migration.from_version != current or migration.to_version != current + 1:
                raise QcaeValidationError(
                    f"migration {migration.migration_id!r} declares "
                    f"{migration.from_version}->{migration.to_version}, "
                    f"but store is at {current}"
                )
            pre = _schema_fingerprint(self._conn)
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                migration.apply(self._conn)
                self._conn.execute(f"PRAGMA user_version = {migration.to_version}")
                self._conn.execute(
                    "INSERT INTO schema_migration_ledger (from_version, to_version,"
                    " migration_id, applied_at, pre_digest, post_digest)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (migration.from_version, migration.to_version, migration.migration_id,
                     self._clock(), pre, _schema_fingerprint(self._conn)),
                )
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise
            current = self.current_version()
        return current


def _apply_test_v2(conn: sqlite3.Connection) -> None:
    """Test migration v1->v2: add an indexed provenance column to evidence.

    Uses a table rebuild (SQLite's ALTER TABLE ADD COLUMN cannot add a
    NOT-NULL-without-default column), preserving all existing rows and
    recording transformation provenance in the ledger via the runner.
    """
    conn.execute("ALTER TABLE evidence_artifact RENAME TO evidence_artifact_v1")
    conn.execute(
        """
        CREATE TABLE evidence_artifact (
            evidence_id      TEXT PRIMARY KEY,
            subject_id       TEXT NOT NULL,
            object_type      TEXT NOT NULL,
            evidence_class   TEXT NOT NULL,
            artifact_digest  TEXT NOT NULL,
            producer         TEXT NOT NULL,
            created_at       TEXT NOT NULL,
            external_owner_domain TEXT NOT NULL DEFAULT '',
            payload_json     TEXT NOT NULL,
            payload_digest   TEXT NOT NULL,
            provenance_note  TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO evidence_artifact (evidence_id, subject_id, object_type,"
        " evidence_class, artifact_digest, producer, created_at,"
        " external_owner_domain, payload_json, payload_digest, provenance_note)"
        " SELECT evidence_id, subject_id, object_type, evidence_class,"
        " artifact_digest, producer, created_at, external_owner_domain,"
        " payload_json, payload_digest, 'migrated-from-v1' FROM evidence_artifact_v1"
    )
    conn.execute("DROP TABLE evidence_artifact_v1")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_evidence_subject ON evidence_artifact(subject_id)"
    )


TEST_V1_TO_V2 = Migration(
    from_version=1,
    to_version=2,
    migration_id="P1-TEST-0001-evidence-provenance-note",
    apply=_apply_test_v2,
    description="adds provenance_note column to evidence_artifact (mechanism proof)",
)


REPOSITORY_REVISION_DDL = """
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


def _apply_v3(conn: sqlite3.Connection) -> None:
    """ADR-0007: add immutable repository_revision records (v2 -> v3).

    Additive only. Existing repository_record rows are unchanged; a revision
    record is created for each existing repository_record observation so
    identity/revision history is preserved through the migration itself.
    """
    conn.executescript(REPOSITORY_REVISION_DDL)
    rows = conn.execute(
        "SELECT payload_json, payload_digest FROM repository_record"
    ).fetchall()
    for payload_json, payload_digest in rows:
        data = json.loads(payload_json)
        revision_id = f"{data['repository_id']}@{data['revision']}"
        conn.execute(
            "INSERT OR IGNORE INTO repository_revision (repository_revision_id,"
            " repository_id, revision, payload_json, payload_digest)"
            " VALUES (?, ?, ?, ?, ?)",
            (revision_id, data["repository_id"], data["revision"],
             payload_json, payload_digest),
        )


V2_TO_V3 = Migration(
    from_version=2,
    to_version=3,
    migration_id="P1R1-0003-repository-revision-records",
    apply=_apply_v3,
    description=(
        "ADR-0007: adds repository_revision table (stable repository identity "
        "plus immutable revision records); back-fills one revision record per "
        "existing repository_record"
    ),
)


RUNTIME_DDL_MIGRATION = """
CREATE TABLE IF NOT EXISTS runtime_job (
    job_id            TEXT PRIMARY KEY,
    deterministic_id  TEXT NOT NULL,
    status            TEXT NOT NULL,
    job_type          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    priority          INTEGER NOT NULL DEFAULT 0,
    queued_at         TEXT NOT NULL DEFAULT '',
    not_before        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_runtime_job_status ON runtime_job(status);
CREATE INDEX IF NOT EXISTS ix_runtime_job_queue ON runtime_job(not_before, priority DESC);

CREATE TABLE IF NOT EXISTS runtime_step (
    step_id           TEXT NOT NULL,
    job_id            TEXT NOT NULL,
    status            TEXT NOT NULL,
    step_type         TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    lease_owner       TEXT NOT NULL DEFAULT '',
    lease_token       TEXT NOT NULL DEFAULT '',
    lease_expires_at  TEXT NOT NULL DEFAULT '',
    not_before        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (step_id)
);
CREATE INDEX IF NOT EXISTS ix_runtime_step_job ON runtime_step(job_id);
CREATE INDEX IF NOT EXISTS ix_runtime_step_status ON runtime_step(status);

CREATE TABLE IF NOT EXISTS runtime_job_event (
    event_seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id          TEXT NOT NULL,
    event_type        TEXT NOT NULL,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL DEFAULT '',
    occurred_at       TEXT NOT NULL,
    actor             TEXT NOT NULL DEFAULT '',
    payload_json      TEXT NOT NULL DEFAULT '',
    event_digest      TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_runtime_event_id ON runtime_job_event(event_id);
CREATE INDEX IF NOT EXISTS ix_runtime_event_job ON runtime_job_event(job_id);

CREATE TABLE IF NOT EXISTS runtime_checkpoint (
    checkpoint_id     TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL DEFAULT '',
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_checkpoint_job ON runtime_checkpoint(job_id);

CREATE TABLE IF NOT EXISTS runtime_idempotency (
    idempotency_key   TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    completed_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_execution (
    idempotency_key   TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    state             TEXT NOT NULL,
    replay_safety     TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_runtime_execution_job ON runtime_execution(job_id);

CREATE TABLE IF NOT EXISTS runtime_queue_claim (
    step_id           TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    lease_owner       TEXT NOT NULL,
    lease_token       TEXT NOT NULL,
    leased_at         TEXT NOT NULL,
    lease_expires_at  TEXT NOT NULL,
    acknowledged      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_queue_claim_expiry
    ON runtime_queue_claim(lease_expires_at);

CREATE TABLE IF NOT EXISTS runtime_budget (
    budget_id         TEXT PRIMARY KEY,
    owner_kind        TEXT NOT NULL,
    owner_id          TEXT NOT NULL,
    parent_budget_id  TEXT NOT NULL DEFAULT '',
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_budget_owner ON runtime_budget(owner_id);

CREATE TABLE IF NOT EXISTS governance_policy_request (
    request_ref       TEXT PRIMARY KEY,
    principal         TEXT NOT NULL,
    action            TEXT NOT NULL,
    resource          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_policy_decision (
    decision_id       TEXT PRIMARY KEY,
    request_ref       TEXT NOT NULL,
    decision          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_gov_decision_request
    ON governance_policy_decision(request_ref);

CREATE TABLE IF NOT EXISTS governance_approval_request (
    request_id        TEXT PRIMARY KEY,
    principal         TEXT NOT NULL,
    action            TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_approval_decision (
    decision_id       TEXT PRIMARY KEY,
    request_ref       TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_approval_decision_request
    ON governance_approval_decision(request_ref);

CREATE TABLE IF NOT EXISTS governance_escalation (
    escalation_id     TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_escalation_decision (
    decision_id       TEXT PRIMARY KEY,
    escalation_ref    TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_escalation_decision_ref
    ON governance_escalation_decision(escalation_ref);
"""


def _apply_v4(conn: sqlite3.Connection) -> None:
    """P2: add runtime + governance tables (v3 -> v4).

    Purely additive: P1 registry/evidence data is untouched. All runtime
    tables start empty; the P2 runtime populates them after migration.
    """
    conn.executescript(RUNTIME_DDL_MIGRATION)


V3_TO_V4 = Migration(
    from_version=3,
    to_version=4,
    migration_id="P2-0004-runtime-governance-tables",
    apply=_apply_v4,
    description=(
        "P2: adds runtime job/step/event/checkpoint/idempotency/claim/budget "
        "and governance policy/approval/escalation tables (additive)"
    ),
)
