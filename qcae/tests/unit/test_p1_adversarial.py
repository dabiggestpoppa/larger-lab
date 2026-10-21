"""P1-T01 — adversarial/integrity qualification (P1 spec §20, cross-cutting).

These tests attack the spine as a whole: tampering, laundering, append-only
pressure, restart persistence, and firewall integration — beyond the
happy-path coverage each slice carries.
"""

from __future__ import annotations

import json

import pytest

from qcae.core.amendments.a001.external_registry import (
    ExternalRegistry,
    ExternalRegistryRef,
)
from qcae.core.evidence import EvidenceObjectType, FreshnessState, ScopeDimensions
from qcae.core.errors import QcaeValidationError
from qcae.core.knowledge import NegativeKnowledgeType
from qcae.core.ports.evidence_registry import FreshnessChangeEvent
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType
from qcae.core.receipts import ReceiptEvidenceRef, ReceiptState
from qcae.core.vocabulary import EvidenceClass
from qcae.infrastructure.artifact_store import ArtifactCorruptionError
from qcae.infrastructure.persistence.sqlite_external_registry_store import (
    SqliteExternalRegistryRefRepository,
    EXTERNAL_REGISTRY_DDL,
)
from qcae.infrastructure.persistence.sqlite_knowledge_store import (
    SqliteNegativeKnowledgeRepository,
    SqliteReceiptRepository,
    KNOWLEDGE_DDL,
)
from qcae.infrastructure.persistence.sqlite_lineage_store import (
    SqliteLineageRepository,
    LINEAGE_DDL,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository
from qcae.infrastructure.persistence.store_factory import open_metadata_db

from qcae.tests.unit.test_p1_knowledge import _negative
from qcae.tests.unit.test_p1_receipt import _receipt
from qcae.tests.unit.test_p1_sqlite_store import _artifact


@pytest.fixture()
def full_env(tmp_path):
    conn = open_metadata_db(tmp_path / "adv.db")
    conn.executescript(LINEAGE_DDL)
    conn.executescript(KNOWLEDGE_DDL)
    conn.executescript(EXTERNAL_REGISTRY_DDL)
    repos = {
        "conn": conn,
        "evidence": SqliteEvidenceRepository(conn),
        "lineage": SqliteLineageRepository(conn),
        "neg": SqliteNegativeKnowledgeRepository(conn),
        "rcpt": SqliteReceiptRepository(conn),
        "extref": SqliteExternalRegistryRefRepository(conn),
    }
    yield repos
    conn.close()


class TestTamperResistance:
    def test_row_and_digest_tamper_both_detected(self, full_env) -> None:
        conn = full_env["conn"]
        full_env["evidence"].add(_artifact("ev-t"))
        conn.commit()
        # tamper payload without updating stored digest -> caught
        conn.execute(
            "UPDATE evidence_artifact SET payload_json = json_set(payload_json,"
            " '$.summary','forged') WHERE evidence_id='ev-t'")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            full_env["evidence"].get("ev-t")

    def test_forged_digest_row_detected(self, full_env) -> None:
        """Recomputing nothing: swapping the payload_digest column itself still
        fails because the forged digest won't match the payload's canonical form."""
        conn = full_env["conn"]
        full_env["evidence"].add(_artifact("ev-t2"))
        conn.commit()
        conn.execute(
            "UPDATE evidence_artifact SET payload_json = json_set(payload_json,"
            " '$.summary','forged'), payload_digest = '0' WHERE evidence_id='ev-t2'")
        conn.commit()
        with pytest.raises(QcaeValidationError):
            full_env["evidence"].get("ev-t2")

    def test_artifact_bytes_and_metadata_digest_binding(self, tmp_path, full_env) -> None:
        """Metadata's artifact_digest binds the record to exact raw bytes;
        divergent bytes corrupt the chain and must be detectable end to end."""
        from qcae.infrastructure.artifact_store import ContentAddressedArtifactStore

        store = ContentAddressedArtifactStore(tmp_path / "art")
        raw = b"definitive benchmark log"
        digest = store.put_bytes(raw)
        full_env["evidence"].add(_artifact("ev-bound", artifact_digest=digest))
        full_env["conn"].commit()
        assert full_env["evidence"].get("ev-bound").artifact_digest == digest
        assert store.get_bytes(digest) == raw
        store._path_for(digest).write_bytes(b"replaced log")
        with pytest.raises(ArtifactCorruptionError):
            store.get_bytes(digest)


class TestAppendOnlyPressure:
    def test_every_factual_store_rejects_id_reuse(self, full_env) -> None:
        full_env["evidence"].add(_artifact("ev-dup"))
        full_env["neg"].add(_negative())
        full_env["rcpt"].add(_receipt())
        full_env["extref"].add(ExternalRegistryRef(
            registry=ExternalRegistry.RESEARCH_MESH, external_id="rm-1",
            owner_domain="research-mesh:synthesis"))
        full_env["conn"].commit()
        with pytest.raises(QcaeValidationError):
            full_env["evidence"].add(_artifact("ev-dup"))
        with pytest.raises(QcaeValidationError):
            full_env["neg"].add(_negative())
        with pytest.raises(QcaeValidationError):
            full_env["rcpt"].add(_receipt())
        with pytest.raises(QcaeValidationError):
            full_env["extref"].add(ExternalRegistryRef(
                registry=ExternalRegistry.RESEARCH_MESH, external_id="rm-1",
                owner_domain="research-mesh:synthesis", external_digest="d" * 64))

    def test_supersession_never_deletes_history_anywhere(self, full_env) -> None:
        """Evidence, negative knowledge, receipts: superseding coexists."""
        full_env["evidence"].add(_artifact("ev-old", superseded_by="ev-new"))
        full_env["evidence"].add(_artifact("ev-new"))
        full_env["neg"].add(_negative(record_id="neg-old", superseded_by="neg-new"))
        full_env["neg"].add(_negative(record_id="neg-new"))
        full_env["rcpt"].add(_receipt(receipt_id="r-old", state=ReceiptState.SUPERSEDED))
        full_env["rcpt"].add(_receipt(receipt_id="r-new", supersedes_receipt="r-old"))
        full_env["conn"].commit()
        assert full_env["evidence"].get("ev-old") is not None
        assert full_env["neg"].get("neg-old") is not None
        assert full_env["rcpt"].get("r-old").state is ReceiptState.SUPERSEDED


class TestRestartIntegrity:
    def test_complete_spine_survives_restart(self, tmp_path) -> None:
        """The P1 north star: durable structured state across process death."""
        db = tmp_path / "spine.db"
        c1 = open_metadata_db(db)
        c1.executescript(LINEAGE_DDL)
        c1.executescript(KNOWLEDGE_DDL)
        c1.executescript(EXTERNAL_REGISTRY_DDL)
        ev = SqliteEvidenceRepository(c1)
        lin = SqliteLineageRepository(c1)
        rcpt = SqliteReceiptRepository(c1)
        ext = SqliteExternalRegistryRefRepository(c1)

        ev.add(_artifact("ev-1"))
        ev.add(_artifact("ev-2", superseded_by="ev-1"))
        lin.add(LineageEdge(src_id="ev-1", src_kind="evidence",
                            edge_type=LineageEdgeType.SUPERSEDES,
                            dst_id="ev-2", dst_kind="evidence", created_at="t0"))
        rcpt.add(_receipt(receipt_id="r1"))
        ext.add(ExternalRegistryRef(
            registry=ExternalRegistry.RESEARCH_MESH, external_id="rm-1",
            owner_domain="research-mesh:synthesis"))
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        ev2 = SqliteEvidenceRepository(c2)
        lin2 = SqliteLineageRepository(c2)
        rcpt2 = SqliteReceiptRepository(c2)
        ext2 = SqliteExternalRegistryRefRepository(c2)
        assert ev2.get("ev-1") is not None
        assert ev2.get("ev-2").superseded_by == "ev-1"
        assert len(lin2.supersession_chain("ev-1")) == 1
        assert rcpt2.get("r1").receipt_id == "r1"
        assert ext2.get("rm-1", registry_value="RESEARCH_MESH").owner_domain == "research-mesh:synthesis"
        c2.close()


class TestFirewallIntegration:
    def test_evidence_to_receipt_chain_with_mesh_support(self, full_env) -> None:
        """Full chain: raw evidence -> interpretation -> receipt; Mesh refs
        may support but the executable proof stays QCAE-owned."""
        conn = full_env["conn"]
        full_env["evidence"].add(_artifact(
            "ev-raw", evidence_object_type=EvidenceObjectType.OBSERVATION,
            evidence_class=EvidenceClass.E2_SOURCE))
        full_env["evidence"].add(_artifact(
            "ev-exec", evidence_class=EvidenceClass.E5_INDEPENDENT_CONTRACT))
        conn.commit()
        # receipt: one internal executable ref + one external supporting ref
        r = _receipt(
            receipt_id="r-chain",
            proof_refs=(
                ReceiptEvidenceRef(evidence_id="ev-exec",
                                   evidence_class="E5_INDEPENDENT_CONTRACT",
                                   artifact_digest="a" * 64),
                ReceiptEvidenceRef(evidence_id="rm-evidence-0001",
                                   evidence_class="E2_SOURCE",
                                   artifact_digest="c" * 64,
                                   external_owner_domain="research-mesh:synthesis"),
            ),
        )
        full_env["rcpt"].add(r)
        conn.commit()
        assert full_env["rcpt"].get("r-chain") is not None

    def test_client_confidential_classification_flows_through(self, full_env) -> None:
        """Data classification survives persistence on evidence records."""
        conn = full_env["conn"]
        full_env["evidence"].add(_artifact(
            "ev-confidential",
            data_classification="CLIENT_CONFIDENTIAL",
            rights_status="client-specific, promotion requires governed review"))
        conn.commit()
        loaded = full_env["evidence"].get("ev-confidential")
        assert loaded.data_classification == "CLIENT_CONFIDENTIAL"
        assert "promotion requires governed review" in loaded.rights_status

    def test_negative_and_positive_knowledge_coexist_for_one_source(self, full_env) -> None:
        """Book IV 9.4 invariant 4: failed alpha can coexist with useful
        software capability — same source, different subjects."""
        conn = full_env["conn"]
        full_env["neg"].add(_negative(record_id="neg-alpha",
                                      failure_type=NegativeKnowledgeType.QUANT_INVALIDATION,
                                      subject_id="repo:owner/libx@v3.1"))
        full_env["evidence"].add(_artifact(
            "ev-sw", subject_id="repo:owner/libx@v3.1",
            evidence_class=EvidenceClass.E5_INDEPENDENT_CONTRACT))
        conn.commit()
        assert full_env["neg"].find_by_subject("repo:owner/libx@v3.1")
        assert full_env["evidence"].list_by_subject("repo:owner/libx@v3.1")


class TestArchitectureRegression:
    def test_no_engine_or_provider_fragments_in_core_tree(self) -> None:
        """Standalone re-check independent of the P0 guard module."""
        import ast
        from pathlib import Path

        core = Path("qcae/core")
        forbidden = ("sqlite3", "duckdb", "sqlalchemy", "requests", "httpx",
                     "github", "deepwiki", "docker", "kubernetes")
        offenders = []
        for py in core.rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        if root in forbidden:
                            offenders.append(f"{py}: {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    root = node.module.split(".")[0]
                    if root in forbidden:
                        offenders.append(f"{py}: {node.module}")
        assert offenders == []
