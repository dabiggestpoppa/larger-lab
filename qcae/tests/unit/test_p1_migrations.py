"""P1-C10 — schema migration evidence (P1 spec §16, tests 33–34)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.migrations import Migration, MigrationRunner, TEST_V1_TO_V2
from qcae.infrastructure.persistence.store_factory import open_metadata_db

from qcae.tests.unit.test_p1_sqlite_store import _artifact


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "mig.db"
    conn = open_metadata_db(path)
    yield conn
    conn.close()


class TestMigrationMechanism:
    def test_v1_store_migrates_to_v2_with_data_preserved(self, db) -> None:
        repo = None
        from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository

        repo = SqliteEvidenceRepository(db)
        art = _artifact("ev-keep")
        repo.add(art)
        db.commit()

        runner = MigrationRunner(db, clock=lambda: "2026-09-12T00:00:00Z")
        assert runner.current_version() == 1
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        assert runner.current_version() == 2

        # row data preserved through the rebuild
        assert repo.get("ev-keep") == art

    def test_ledger_records_transformation_provenance(self, db) -> None:
        runner = MigrationRunner(db, clock=lambda: "2026-09-12T00:00:00Z")
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        entries = runner.ledger()
        assert len(entries) == 1
        e = entries[0]
        assert (e.from_version, e.to_version) == (1, 2)
        assert e.migration_id == "P1-TEST-0001-evidence-provenance-note"
        assert e.applied_at == "2026-09-12T00:00:00Z"
        assert e.pre_digest != e.post_digest  # schema shape changed

    def test_no_backward_migration(self, db) -> None:
        runner = MigrationRunner(db, clock=lambda: "t")
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        with pytest.raises(QcaeValidationError, match="backwards"):
            runner.migrate_to(1, {2: TEST_V1_TO_V2})

    def test_no_skipping_versions(self, db) -> None:
        runner = MigrationRunner(db, clock=lambda: "t")
        with pytest.raises(QcaeValidationError, match="no migration registered"):
            runner.migrate_to(5, {2: TEST_V1_TO_V2})

    def test_failed_migration_rolls_back(self, db) -> None:
        def broken(conn):
            conn.execute("CREATE TABLE half_written (x TEXT)")
            raise RuntimeError("injected migration crash")

        bad = Migration(from_version=1, to_version=2,
                        migration_id="P1-TEST-BROKEN", apply=broken)
        runner = MigrationRunner(db, clock=lambda: "t")
        with pytest.raises(RuntimeError, match="injected migration crash"):
            runner.migrate_to(2, {2: bad})
        assert runner.current_version() == 1
        assert runner.ledger() == []
        assert db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='half_written'"
        ).fetchone()[0] == 0

    def test_migration_is_not_reapplied(self, db) -> None:
        runner = MigrationRunner(db, clock=lambda: "t")
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        # current == target: the while loop runs zero times; version unchanged
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        assert len(runner.ledger()) == 1

    def test_version_mismatched_migration_rejected(self, db) -> None:
        wrong = Migration(from_version=9, to_version=10,
                          migration_id="P1-TEST-WRONG", apply=lambda conn: None)
        runner = MigrationRunner(db, clock=lambda: "t")
        with pytest.raises(QcaeValidationError, match="declares"):
            runner.migrate_to(2, {2: wrong})
