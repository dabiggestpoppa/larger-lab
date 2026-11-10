"""P2-R5R-R2 C01 — zero-mutation refusal ordering (Finding A).

All terminal refusals (UNKNOWN_HYBRID, UNVERSIONED_EXISTING, NOT_LEGACY)
must return/raise BEFORE any persistent write or pragma migration.
Every case is proven against real SQLite files (never a mock).
"""

from __future__ import annotations

import re

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.migrations import _schema_fingerprint
from qcae.infrastructure.persistence.store_factory import (
    open_metadata_db,
    open_raw_connection,
)

_HEX64 = re.compile(r"[0-9a-f]{64}")


def _tables(conn) -> set:
    return {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
            " AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


def _version(conn) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _journal_mode(conn) -> str:
    return conn.execute("PRAGMA journal_mode").fetchone()[0]


def _sidecars_exist(db_path) -> bool:
    return (
        (db_path.parent / (db_path.name + "-wal")).exists()
        or (db_path.parent / (db_path.name + "-shm")).exists()
    )


class TestRefusalOrdering:
    """Finding A: all terminal refusals happen before any persistent write."""

    def test_unknown_hybrid_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "hybrid.sqlite3"
        conn = open_raw_connection(db)
        # v2 stamp with runtime tables: contradictory shape.
        conn.executescript(
            "CREATE TABLE runtime_job (job_id TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version
            assert _schema_fingerprint(conn) == before_fp
            # No -wal/-shm sidecars created by the refused open.
            assert not _sidecars_exist(db)
        finally:
            conn.close()

    def test_unversioned_existing_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "unversioned.sqlite3"
        conn = open_raw_connection(db)
        conn.execute("CREATE TABLE legacy_app_data (id TEXT PRIMARY KEY)")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(QcaeValidationError, match="unversioned"):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version
            assert _schema_fingerprint(conn) == before_fp
            assert not _sidecars_exist(db)
        finally:
            conn.close()

    def test_newer_schema_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "newer.sqlite3"
        conn = open_metadata_db(db)  # bootstraps to v5 (sets WAL)
        conn.execute("PRAGMA user_version = 6")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)  # == 6
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(
            QcaeValidationError, match="not openable by this build"
        ):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version  # refusal did not change it
            assert _schema_fingerprint(conn) == before_fp
        finally:
            conn.close()
