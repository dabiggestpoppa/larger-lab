"""Factory wiring SQLite connections for QCAE metadata repositories.

Owns connection pragmas (WAL, foreign keys) and schema creation, so
repositories stay pure row-mappers and transaction semantics stay with the
unit-of-work layer (P1-C09).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Union

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_LEDGER_DDL,
    LegacyDatabaseClass,
    MigrationRunner,
    bootstrap_v5_schema,
    RUNTIME_DDL_MIGRATION,
    V2_TO_V3,
    V3_TO_V4,
    V4_TO_V5,
    V5_ADDITIONS_DDL,
    classify_legacy_database,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import (
    SCHEMA_VERSION,
    SqliteEvidenceRepository,
    SqliteLifecycleLogRepository,
    _SCHEMA_DDL,
)

#: Runtime engine version, exposed here so build tools need no engine import.
SQLITE_VERSION = sqlite3.sqlite_version

#: Production migration chain keyed by TARGET version. ``TEST_V1_TO_V2`` is
#: test-only (it rebuilds evidence_artifact) and is NOT registered here;
#: historical migrations stay immutable.
_PRODUCTION_MIGRATIONS = {
    3: V2_TO_V3,
    4: V3_TO_V4,
    5: V4_TO_V5,
}

__all__ = [
    "SqliteEvidenceRepository",
    "SqliteLifecycleLogRepository",
    "SCHEMA_VERSION",
    "SQLITE_VERSION",
    "CURRENT_SCHEMA_VERSION",
    "open_metadata_db",
]


def _iso_now() -> str:
    """UTC ISO-8601 timestamp for migration ledger timestamps."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: Ordered authority DDL for a fresh v5 bootstrap (P1 metadata, true
#: historical v4, v5 additions, runtime/queue/budget/governance/approval
#: tables, migration ledger last). Built lazily so this factory stays free
#: of engine imports at module load; tests may replace this global to
#: inject a bootstrap failure and prove all-or-nothing rollback.
_FRESH_V5_BOOTSTRAP_SCRIPTS = None


def _fresh_v5_scripts():
    global _FRESH_V5_BOOTSTRAP_SCRIPTS
    if _FRESH_V5_BOOTSTRAP_SCRIPTS is None:
        from qcae.infrastructure.persistence.sqlite_approval_registry import (
            APPROVAL_DDL as _APPROVAL_DDL,
        )
        from qcae.infrastructure.persistence.sqlite_budget_ledger import (
            BUDGET_DDL as _BUDGET_DDL,
        )
        from qcae.infrastructure.persistence.sqlite_policy_log import (
            GOVERNANCE_DDL as _GOVERNANCE_DDL,
        )
        from qcae.infrastructure.persistence.sqlite_runtime_store import (
            RUNTIME_DDL as _RUNTIME_TABLES_DDL,
        )
        from qcae.infrastructure.queue.sqlite_step_queue import (
            QUEUE_INTEGRITY_DDL as _QUEUE_DDL,
        )
        _FRESH_V5_BOOTSTRAP_SCRIPTS = [
            _SCHEMA_DDL,
            RUNTIME_DDL_MIGRATION,
            V5_ADDITIONS_DDL,
            _RUNTIME_TABLES_DDL,
            _QUEUE_DDL,
            _BUDGET_DDL,
            _GOVERNANCE_DDL,
            _APPROVAL_DDL,
            MIGRATION_LEDGER_DDL,
        ]
    return _FRESH_V5_BOOTSTRAP_SCRIPTS


def open_raw_connection(path: Union[str, Path]) -> sqlite3.Connection:
    """Open a raw connection to an existing SQLite file (test/repair tooling).

    Engine access stays inside infrastructure per the architecture guard; this
    escape hatch exists for tests that must corrupt/inspect a database file
    to prove the integrity layers fire.
    """
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def open_metadata_db(path: Union[str, Path]) -> sqlite3.Connection:
    """Open (creating if needed) a QCAE metadata database.

    WAL journaling for concurrent readers; explicit schema version recorded
    via ``PRAGMA user_version`` for the migration ledger (P1-C10).

    An unusable location (a directory, an unwritable path, a file that is not a
    SQLite database) is an operator error, not a crash: it surfaces as a typed
    ``QcaeValidationError`` naming the path so the CLI reports it.
    """
    # ``target`` is None exactly for the in-memory database; ``label`` is what
    # operator-facing messages call it.
    target: Optional[Path] = None if path == ":memory:" else Path(path)
    label = ":memory:" if target is None else str(target)
    if target is not None and target.is_dir():
        raise QcaeValidationError(
            f"metadata database path {target} is a directory, not a database file"
        )
    conn: Optional[sqlite3.Connection] = None
    try:
        if target is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(label)
        conn.row_factory = sqlite3.Row
        # P2-R5R-R1 custody law: CLASSIFY FIRST, mutate only when
        # authorized. No schema DDL runs before this point, so an unknown,
        # hybrid, newer, or unversioned-existing database is refused with
        # its durable schema and user_version byte-identical to before.
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        classification = classify_legacy_database(conn, current)
        if classification == LegacyDatabaseClass.UNVERSIONED_EXISTING:
            raise QcaeValidationError(
                f"database at schema {current} has existing tables but no"
                f" schema version: refusing to bootstrap over unversioned"
                f" data (failing closed)"
            )
        if classification == LegacyDatabaseClass.NOT_LEGACY:
            raise QcaeValidationError(
                f"database schema version {current} is not openable by this"
                f" build (supports up to {CURRENT_SCHEMA_VERSION}); refusing"
                f" to open (forward-compat guard)"
            )
        if classification == LegacyDatabaseClass.UNKNOWN_HYBRID:
            raise QcaeValidationError(
                f"unknown hybrid / legacy misversioned database at schema "
                f"{current} cannot be migrated to {CURRENT_SCHEMA_VERSION} "
                f"(failing closed)"
            )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        if classification == LegacyDatabaseClass.FRESH_EMPTY:
            # Fresh database: build the COMPLETE v5 schema in ONE explicit
            # transaction with real provenance digests, then stamp v5. No
            # composition root may silently complete the schema afterwards.
            # (executescript is forbidden here: it implicitly COMMITs any
            # pending transaction, which would break atomicity.)
            bootstrap_v5_schema(conn, _fresh_v5_scripts(), _iso_now)
        else:
            # 0 < current <= CURRENT_SCHEMA_VERSION: for known legacy
            # P2-misversioned databases, migrate via the production chain.
            if classification == LegacyDatabaseClass.CURRENT_V5:
                # Already physically v5; nothing to replay.
                return conn
            if classification == LegacyDatabaseClass.KNOWN_P2_MISVERSIONED:
                # Historical bug: physical P2 tables with stamp 1. The
                # v2->v3 migration rebuilds evidence_artifact, which a
                # P2-physical DB may not have in v1 shape; normalize the
                # stamp onto the production chain first: a v5-physical
                # mis-stamp normalizes to v4 (v4->v5 is idempotent), else
                # to v2 (v2->v3->v4->v5), preserving all rows.
                from qcae.infrastructure.persistence.migrations import (
                    _table_names as _legacy_tables,
                )
                _names = _legacy_tables(conn)
                if "runtime_execution" in _names and \
                        "governance_approval_use" in _names:
                    conn.execute("PRAGMA user_version = 4")
                    conn.commit()
                else:
                    conn.execute("PRAGMA user_version = 2")
                    conn.commit()
                current = conn.execute("PRAGMA user_version").fetchone()[0]
            runner = MigrationRunner(conn, clock=_iso_now)
            try:
                runner.migrate_to(CURRENT_SCHEMA_VERSION, _PRODUCTION_MIGRATIONS)
            except QcaeValidationError as exc:
                raise QcaeValidationError(
                    f"legacy misversioned database at schema {current} cannot be "
                    f"migrated to {CURRENT_SCHEMA_VERSION}: {exc}"
                ) from exc
    except QcaeValidationError:
        if conn is not None:
            conn.close()
        raise
    except (sqlite3.Error, OSError) as exc:
        # Both failure shapes leave conn unset: ``sqlite3.connect`` on an
        # unwritable path, or creating the parent when a component of the path
        # is a regular file.
        if conn is not None:
            conn.close()
        raise QcaeValidationError(
            f"metadata database at {label} could not be opened: {exc}"
        ) from exc
    return conn
