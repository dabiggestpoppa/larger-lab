"""P1-C07 — registry retrieval + decision-reuse evidence (P1 spec §13, §18, tests 24, 33)."""

from __future__ import annotations

import pytest

from qcae.core.evidence import FreshnessState
from qcae.core.errors import QcaeValidationError
from qcae.core.knowledge import NegativeKnowledgeType
from qcae.core.ports.evidence_registry import FreshnessChangeEvent
from qcae.core.ports.knowledge_registry import RegistryQuery
from qcae.core.receipts import ReceiptState
from qcae.infrastructure.persistence.sqlite_knowledge_store import (
    KNOWLEDGE_DDL,
    SqliteNegativeKnowledgeRepository,
    SqlitePositiveKnowledgeRepository,
    SqliteReceiptRepository,
    SqliteRegistryQuery,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteLifecycleLogRepository
from qcae.infrastructure.persistence.store_factory import open_metadata_db

from qcae.tests.unit.test_p1_knowledge import _negative
from qcae.tests.unit.test_p1_receipt import _receipt


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(KNOWLEDGE_DDL)
    repos = {
        "conn": conn,
        "neg": SqliteNegativeKnowledgeRepository(conn),
        "pos": SqlitePositiveKnowledgeRepository(conn),
        "rcpt": SqliteReceiptRepository(conn),
        "fresh": SqliteLifecycleLogRepository(conn),
    }
    repos["query"] = SqliteRegistryQuery(
        repos["rcpt"], repos["pos"], repos["neg"], repos["fresh"]
    )
    yield repos
    conn.close()


def _positive(repo, **over):
    from qcae.core.knowledge import make_positive_knowledge

    defaults = dict(
        record_id="pos-001",
        statement="v3.1 passed contract CAP-ORDER-001 v1.0.0",
        subject_id="repo:owner/libx@v3.1",
        evidence_ids=("ev-pass-1",),
        created_at="2026-09-12T00:00:00Z",
        source_revision="v3.1",
        contract_id="CAP-ORDER-001",
        contract_version="1.0.0",
    )
    defaults.update(over)
    record = make_positive_knowledge(**defaults)
    repo.add(record)
    return record


class TestNegativeRetrieval:
    def test_find_by_subject_and_revision(self, env) -> None:
        env["neg"].add(_negative())
        env["conn"].commit()
        hits = env["neg"].find_by_subject("repo:owner/libx@v2.4", "v2.4")
        assert len(hits) == 1
        assert hits[0].failure_type is NegativeKnowledgeType.CONTRACT_FAILURE
        assert env["neg"].find_by_subject("repo:owner/libx@v9.9") == []

    def test_active_excludes_superseded(self, env) -> None:
        env["neg"].add(_negative(record_id="neg-old", superseded_by="neg-new"))
        env["neg"].add(_negative(record_id="neg-new"))
        env["conn"].commit()
        assert {n.record_id for n in env["neg"].active()} == {"neg-new"}

    def test_append_only_duplicate_rejected(self, env) -> None:
        env["neg"].add(_negative())
        with pytest.raises(QcaeValidationError, match="append-only"):
            env["neg"].add(_negative())


class TestReceiptRetrieval:
    def test_state_and_capability_filters(self, env) -> None:
        env["rcpt"].add(_receipt(receipt_id="r1"))
        env["rcpt"].add(_receipt(receipt_id="r2", state=ReceiptState.STALE))
        env["rcpt"].add(_receipt(receipt_id="r3", capability_id="CAP-OTHER-001"))
        env["conn"].commit()
        active = {r.receipt_id for r in env["rcpt"].find_by_state(ReceiptState.ACTIVE)}
        assert active == {"r1", "r3"}
        assert {r.receipt_id for r in env["rcpt"].active_for_capability("CAP-REPLAY-001")} == {"r1"}
        stale = env["rcpt"].find_by_state(ReceiptState.STALE)
        assert [r.receipt_id for r in stale] == ["r2"]

    def test_supersession_lookup(self, env) -> None:
        env["rcpt"].add(_receipt(receipt_id="r-old", state=ReceiptState.SUPERSEDED))
        env["rcpt"].add(_receipt(receipt_id="r-new", supersedes_receipt="r-old"))
        env["conn"].commit()
        assert [r.receipt_id for r in env["rcpt"].superseded_by("r-old")] == ["r-new"]


class TestDecisionReuse:
    def test_sufficient_knowledge_avoids_discovery(self, env) -> None:
        """9.7 order: active receipt + matching positive knowledge + no
        negative blocks => QCAE can skip external discovery."""
        env["rcpt"].add(_receipt(receipt_id="r1"))
        env["pos"].add(_positive(env["pos"]))
        env["conn"].commit()
        findings = env["query"].decision_reuse_findings(
            "CAP-REPLAY-001", "CAP-REPLAY-001", "1.0.0"
        )
        assert isinstance(findings, dict)
        assert findings["active_receipts"] == ["r1"]
        assert findings["positive_knowledge"] == ["pos-001"]
        assert findings["negative_blocks"] == []
        assert findings["sufficient_without_discovery"] is True

    def test_negative_block_prevents_rediscovery_loop(self, env) -> None:
        """9.7 anti-loop: a prior unrecoverable failure blocks rerunning."""
        env["rcpt"].add(_receipt(receipt_id="r1"))
        env["pos"].add(_positive(env["pos"]))
        env["neg"].add(_negative())  # retry_allowed=False for same source/revision
        env["conn"].commit()
        findings = env["query"].decision_reuse_findings(
            "CAP-REPLAY-001", "CAP-ORDER-001", "1.0.0"
        )
        assert findings["negative_blocks"] == ["neg-001"]
        assert findings["sufficient_without_discovery"] is False

    def test_missing_evidence_returns_structured_gap(self, env) -> None:
        findings = env["query"].decision_reuse_findings("CAP-NONE-001", "c", "1")
        assert findings["active_receipts"] == []
        assert findings["positive_knowledge"] == []
        assert findings["sufficient_without_discovery"] is False

    def test_stale_evidence_listed_for_refresh(self, env) -> None:
        env["fresh"].append(FreshnessChangeEvent(
            "ev-9", FreshnessState.CURRENT, FreshnessState.STALE, "upstream bump", "t1"))
        env["conn"].commit()
        findings = env["query"].decision_reuse_findings("CAP-NONE-001", "c", "1")
        assert findings["stale_evidence"] == ["ev-9"]
