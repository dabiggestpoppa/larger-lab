"""P1-C03 — SQLite evidence metadata store evidence (P1 spec §13, tests 29–33)."""

from __future__ import annotations

import json

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.evidence import EvidenceArtifact, EvidenceObjectType, FreshnessState
from qcae.core.ports.evidence_registry import FreshnessChangeEvent
from qcae.core.vocabulary import EvidenceClass
from qcae.infrastructure.persistence.store_factory import open_metadata_db


def _artifact(evidence_id="ev-1", subject_id="atom-x", **over) -> EvidenceArtifact:
    from qcae.core.evidence import ScopeDimensions

    defaults = dict(
        evidence_id=evidence_id,
        subject_id=subject_id,
        evidence_object_type=EvidenceObjectType.TEST_RESULT,
        evidence_class=EvidenceClass.E5_INDEPENDENT_CONTRACT,
        artifact_digest="a" * 64,
        producer="ContractTestWorker",
        created_at="2026-09-12T00:00:00Z",
        scope=ScopeDimensions(implementation_revision="rev-1", contract_version="1.0.0"),
        summary="passed",
    )
    defaults.update(over)
    return EvidenceArtifact(**defaults)


@pytest.fixture()
def conn():  # returns sqlite3.Connection from open_metadata_db
    c = open_metadata_db(":memory:")
    yield c
    c.close()


@pytest.fixture()
def repo(conn):
    from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository

    return SqliteEvidenceRepository(conn)


@pytest.fixture()
def log(conn):
    from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteLifecycleLogRepository

    return SqliteLifecycleLogRepository(conn)


class TestAppendOnly:
    def test_add_and_get_round_trip(self, repo) -> None:
        art = _artifact()
        repo.add(art)
        loaded = repo.get("ev-1")
        assert loaded == art

    def test_duplicate_id_rejected_with_supersede_guidance(self, repo) -> None:
        repo.add(_artifact())
        with pytest.raises(QcaeValidationError, match="superseding record"):
            repo.add(_artifact())

    def test_store_contains_no_update_path(self) -> None:
        """The adapter executes no UPDATE against factual tables (§14).

        AST-based: collects string constants, keeps only SQL-looking ones
        (contain another SQL keyword), and rejects any UPDATE statement.
        Prose in docstrings/comments cannot trip this.
        """
        import ast
        import inspect
        import re

        from qcae.infrastructure.persistence import sqlite_metadata_store

        src = inspect.getsource(sqlite_metadata_store)
        tree = ast.parse(src)
        update_stmt = re.compile(r"\bUPDATE\s+[A-Za-z_][\w.]*\s+SET\b", re.IGNORECASE)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if update_stmt.search(node.value):
                    offenders.append(node.value[:80])
        assert offenders == [], f"UPDATE SQL found in adapter: {offenders}"

    def test_superseded_original_still_retrievable(self, repo) -> None:
        repo.add(_artifact("ev-old"))
        repo.add(_artifact("ev-new", superseded_by="ev-new-2"))
        assert repo.get("ev-old") is not None
        assert repo.list_superseded_by("ev-new-2")[0].evidence_id == "ev-new"


class TestIntegrity:
    def test_row_tampering_detected_on_read(self, repo, conn) -> None:
        repo.add(_artifact())
        conn.execute(
            "UPDATE evidence_artifact SET payload_json = json_set(payload_json,"
            " '$.summary', 'forged conclusion') WHERE evidence_id = 'ev-1'"
        )
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            repo.get("ev-1")

    def test_payload_digest_column_is_canonical(self, repo) -> None:
        art = _artifact()
        repo.add(art)
        row = repo._conn.execute(
            "SELECT payload_digest FROM evidence_artifact WHERE evidence_id='ev-1'"
        ).fetchone()
        assert row[0] == art.digest()


class TestRetrieval:
    @pytest.fixture(autouse=True)
    def _seed(self, repo) -> None:
        from qcae.core.evidence import ScopeDimensions

        repo.add(_artifact("ev-a", subject_id="atom-one", summary="a"))
        repo.add(
            _artifact(
                "ev-b",
                subject_id="atom-two",
                evidence_object_type=EvidenceObjectType.CLAIM,
                evidence_class=EvidenceClass.E0_CLAIM,
                interpretation_status="hypothesis",
                summary="b",
            )
        )
        repo.add(_artifact("ev-c", subject_id="atom-one", summary="c"))
        repo._conn.commit()

    def test_by_subject(self, repo) -> None:
        ids = {a.evidence_id for a in repo.list_by_subject("atom-one")}
        assert ids == {"ev-a", "ev-c"}

    def test_by_object_type(self, repo) -> None:
        assert [a.evidence_id for a in repo.list_by_object_type(EvidenceObjectType.CLAIM)] == ["ev-b"]

    def test_by_class(self, repo) -> None:
        ids = {a.evidence_id for a in repo.list_by_class(EvidenceClass.E5_INDEPENDENT_CONTRACT)}
        assert ids == {"ev-a", "ev-c"}

    def test_by_subject_and_class(self, repo) -> None:
        ids = {
            a.evidence_id
            for a in repo.list_by_subject_and_class("atom-one", EvidenceClass.E5_INDEPENDENT_CONTRACT)
        }
        assert ids == {"ev-a", "ev-c"}

    def test_by_external_owner_domain(self, repo) -> None:
        repo.add(_artifact("ev-ext", external_owner_domain="research-mesh.internal"))
        repo._conn.commit()
        assert [a.evidence_id for a in repo.list_external_refs("research-mesh.internal")] == ["ev-ext"]

    def test_unknown_id_returns_none(self, repo) -> None:
        assert repo.get("nope") is None


class TestFreshnessLog:
    def test_append_and_history(self, repo, log) -> None:
        repo.add(_artifact())
        repo._conn.commit()
        log.append(FreshnessChangeEvent("ev-1", None, FreshnessState.CURRENT, "initial", "t0"))
        log.append(FreshnessChangeEvent("ev-1", FreshnessState.CURRENT, FreshnessState.STALE, "upstream bump", "t1"))
        log.append(FreshnessChangeEvent("ev-1", FreshnessState.STALE, FreshnessState.CURRENT, "revalidated", "t2"))
        repo._conn.commit()
        events = log.history("ev-1")
        assert [e.to_state for e in events] == [
            FreshnessState.CURRENT,
            FreshnessState.STALE,
            FreshnessState.CURRENT,
        ]
        assert log.current_freshness("ev-1") is FreshnessState.CURRENT

    def test_stale_is_not_current_but_not_deleted(self, repo, log) -> None:
        repo.add(_artifact())
        repo._conn.commit()
        log.append(FreshnessChangeEvent("ev-1", None, FreshnessState.STALE, "contract amended", "t1"))
        assert log.current_freshness("ev-1") is FreshnessState.STALE
        assert repo.get("ev-1") is not None  # historical knowledge retained

    def test_default_is_current(self, log) -> None:
        assert log.current_freshness("unknown") is FreshnessState.CURRENT


class TestPersistenceRestart:
    def test_survives_reopen(self, tmp_path) -> None:
        from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository

        db = tmp_path / "meta" / "qcae.db"
        c1 = open_metadata_db(db)
        r1 = SqliteEvidenceRepository(c1)
        art = _artifact()
        r1.add(art)
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        r2 = SqliteEvidenceRepository(c2)
        assert r2.get("ev-1") == art
        assert r2.count() == 1
        c2.close()

    def test_schema_version_recorded(self, tmp_path) -> None:
        c = open_metadata_db(tmp_path / "v.db")
        assert c.execute("PRAGMA user_version").fetchone()[0] >= 1
        c.close()

    def test_forward_compat_guard(self, tmp_path) -> None:
        db = tmp_path / "future.db"
        c = open_metadata_db(db)
        c.execute("PRAGMA user_version = 999")
        c.commit()
        c.close()
        with pytest.raises(QcaeValidationError, match="newer than this build"):
            open_metadata_db(db)


def inspect_source(module) -> str:
    import inspect

    return inspect.getsource(module)
