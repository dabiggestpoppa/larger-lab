"""P1-C09 — unit-of-work transaction evidence (P1 spec §15, tests 30–32)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.evidence import EvidenceArtifact, EvidenceObjectType
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType
from qcae.core.vocabulary import EvidenceClass
from qcae.infrastructure.persistence.sqlite_lineage_store import (
    SqliteLineageRepository,
    LINEAGE_DDL,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.persistence.unit_of_work import EvidenceCommitService, UnitOfWork

from qcae.tests.unit.test_p1_sqlite_store import _artifact


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(LINEAGE_DDL)
    repos = {
        "conn": conn,
        "evidence": SqliteEvidenceRepository(conn),
        "lineage": SqliteLineageRepository(conn),
    }
    yield repos
    conn.close()


class TestUnitOfWork:
    def test_commit_persists_both_repos(self, env) -> None:
        conn = env["conn"]
        with UnitOfWork(conn):
            env["evidence"].add(_artifact("ev-1"))
            env["lineage"].add(LineageEdge(
                src_id="ev-1", src_kind="evidence",
                edge_type=LineageEdgeType.DERIVED_FROM,
                dst_id="ev-0", dst_kind="evidence",
                created_at="t0"))
        conn.commit()
        assert env["evidence"].get("ev-1") is not None
        assert len(env["lineage"].edges_from("ev-1")) == 1

    def test_rollback_on_injected_failure_leaves_nothing(self, env) -> None:
        """§15: metadata + edge must either commit together or not commit."""
        conn = env["conn"]

        class InjectedFailure(Exception):
            pass

        with pytest.raises(InjectedFailure):
            with UnitOfWork(conn):
                env["evidence"].add(_artifact("ev-partial"))
                env["lineage"].add(LineageEdge(
                    src_id="ev-partial", src_kind="evidence",
                    edge_type=LineageEdgeType.SUPPORTS,
                    dst_id="atom-x", dst_kind="candidate",
                    created_at="t0"))
                raise InjectedFailure
        conn.commit()  # any stray open txn is closed; nothing should exist
        assert env["evidence"].get("ev-partial") is None
        assert env["lineage"].edges_from("ev-partial") == []

    def test_repository_error_triggers_rollback(self, env) -> None:
        conn = env["conn"]
        env["evidence"].add(_artifact("ev-exists"))
        conn.commit()
        with pytest.raises(QcaeValidationError):
            with UnitOfWork(conn):
                env["evidence"].add(_artifact("ev-doomed"))
                env["evidence"].add(_artifact("ev-exists"))  # duplicate -> error
        conn.commit()
        assert env["evidence"].get("ev-doomed") is None

    def test_nested_unit_of_work_rejected(self, env) -> None:
        conn = env["conn"]
        with UnitOfWork(conn):
            with pytest.raises(QcaeValidationError, match="nested"):
                with UnitOfWork(conn):
                    pass

    def test_rollback_does_not_suppress_exception(self, env) -> None:
        conn = env["conn"]

        class Boom(Exception):
            pass

        with pytest.raises(Boom):
            with UnitOfWork(conn):
                raise Boom
        assert not conn.in_transaction

    def test_isolation_uncommitted_invisible_to_second_connection(self, tmp_path) -> None:
        db = tmp_path / "uow.db"
        c1 = open_metadata_db(db)
        c2 = open_metadata_db(db)
        r1 = SqliteEvidenceRepository(c1)
        r2 = SqliteEvidenceRepository(c2)
        uow = UnitOfWork(c1)
        uow.__enter__()  # open transaction, held across the assertions below
        r1.add(_artifact("ev-hidden"))
        # second connection cannot see uncommitted metadata (WAL isolation)
        assert r2.get("ev-hidden") is None
        uow.commit()
        assert r2.get("ev-hidden") is not None
        c1.close()
        c2.close()


class TestComposedService:
    def test_record_evidence_atomic(self, env) -> None:
        conn = env["conn"]
        svc = EvidenceCommitService(conn, env["evidence"], env["lineage"])
        art = _artifact("ev-composed")
        edge = LineageEdge(
            src_id="ev-composed", src_kind="evidence",
            edge_type=LineageEdgeType.DERIVED_FROM,
            dst_id="ev-raw", dst_kind="evidence", created_at="t0")
        svc.record_evidence(art, lineage=edge)
        assert env["evidence"].get("ev-composed") is not None
        assert len(env["lineage"].edges_from("ev-composed")) == 1

    def test_lineage_failure_aborts_evidence_write(self, env) -> None:
        conn = env["conn"]
        svc = EvidenceCommitService(conn, env["evidence"], env["lineage"])
        art = _artifact("ev-aborted")
        bad_edge = LineageEdge(
            src_id="ev-aborted", src_kind="bogus-kind",
            edge_type=LineageEdgeType.SUPPORTS,
            dst_id="atom-x", dst_kind="candidate", created_at="t0")
        with pytest.raises(QcaeValidationError, match="kinds"):
            svc.record_evidence(art, lineage=bad_edge)
        assert env["evidence"].get("ev-aborted") is None  # rolled back together

    def test_bytes_digest_must_match_metadata(self, env, tmp_path) -> None:
        from qcae.infrastructure.artifact_store import ContentAddressedArtifactStore

        store = ContentAddressedArtifactStore(tmp_path / "art")
        svc = EvidenceCommitService(
            env["conn"], env["evidence"], env["lineage"], artifact_store=store)
        art = _artifact("ev-bytes", artifact_digest="a" * 64)
        with pytest.raises(QcaeValidationError, match="does not match metadata"):
            svc.record_evidence(art, raw_bytes=b"mismatching bytes")
