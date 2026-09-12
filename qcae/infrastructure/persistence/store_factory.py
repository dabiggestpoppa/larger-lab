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


def open_metadata_db(path: Union[str, Path]) -> sqlite3.Connection:
    """Open (creating if needed) a QCAE metadata database.

    WAL journaling for concurrent readers; explicit schema version recorded
    via ``PRAGMA user_version`` for the migration ledger (P1-C10).
    """
    p = Path(path)
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
        conn.close()
        raise QcaeValidationError(
            f"database schema version {current} is newer than this build "
            f"supports ({SCHEMA_VERSION}); refusing to open (forward-compat guard)"
        )
    conn.commit()
    return conn
