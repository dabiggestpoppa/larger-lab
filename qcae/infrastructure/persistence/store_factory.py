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
    LegacyDatabaseClass,
    MigrationRunner,
    V2_TO_V3,
    V3_TO_V4,
    V4_TO_V5,
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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA_DDL)
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        if current == 0:
            # Fresh database: create at the canonical version; no migration
            # history to replay (the DDL above already matches this version).
            conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
            conn.commit()
        elif current > CURRENT_SCHEMA_VERSION:
            raise QcaeValidationError(
                f"database schema version {current} is newer than this build "
                f"supports ({CURRENT_SCHEMA_VERSION}); refusing to open "
                f"(forward-compat guard)"
            )
        else:
            # 0 < current <= CURRENT_SCHEMA_VERSION: classify and, for known
            # legacy P2-misversioned databases, migrate via the production
            # chain; unknown hybrid shapes fail closed (P2-R5R policy).
            classification = classify_legacy_database(conn, current)
            if classification == LegacyDatabaseClass.UNKNOWN_HYBRID and current < CURRENT_SCHEMA_VERSION:
                # Only refuse pre-chain unknown shapes; if on the production
                # chain, still attempt migration below.
                if current not in _PRODUCTION_MIGRATIONS and (current + 1) not in _PRODUCTION_MIGRATIONS and current not in (2, 3, 4):
                    raise QcaeValidationError(
                        f"unknown hybrid / legacy misversioned database at schema "
                        f"{current} cannot be migrated to {CURRENT_SCHEMA_VERSION} "
                        f"(failing closed)"
                    )
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
