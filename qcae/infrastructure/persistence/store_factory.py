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
from qcae.infrastructure.persistence.sqlite_metadata_store import (
    SCHEMA_VERSION,
    SqliteEvidenceRepository,
    SqliteLifecycleLogRepository,
    _SCHEMA_DDL,
)

#: Runtime engine version, exposed here so build tools need no engine import.
SQLITE_VERSION = sqlite3.sqlite_version

__all__ = [
    "SqliteEvidenceRepository",
    "SqliteLifecycleLogRepository",
    "SCHEMA_VERSION",
    "SQLITE_VERSION",
    "open_metadata_db",
]


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
    p = Path(path)
    if path != ":memory:":
        if p.is_dir():
            raise QcaeValidationError(
                f"metadata database path {p} is a directory, not a database file"
            )
    conn: Optional[sqlite3.Connection] = None
    try:
        if path != ":memory:":
            p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(p) if path != ":memory:" else ":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA_DDL)
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        if current == 0:
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        elif current > SCHEMA_VERSION:
            raise QcaeValidationError(
                f"database schema version {current} is newer than this build "
                f"supports ({SCHEMA_VERSION}); refusing to open (forward-compat guard)"
            )
        conn.commit()
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
            f"metadata database at {p} could not be opened: {exc}"
        ) from exc
    return conn
