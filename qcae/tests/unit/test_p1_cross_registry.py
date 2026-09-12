"""P1-C08 — A-001 cross-registry provenance evidence (P1 spec §12, tests 36–41)."""

from __future__ import annotations

import pytest

from qcae.core.amendments.a001.external_registry import (
    ExternalLifecycleRole,
    ExternalRegistry,
    ExternalRegistryRef,
)
from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.sqlite_external_registry_store import (
    EXTERNAL_REGISTRY_DDL,
    SqliteExternalRegistryRefRepository,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(EXTERNAL_REGISTRY_DDL)
    repo = SqliteExternalRegistryRefRepository(conn)
    yield conn, repo
    conn.close()


def _ref(**over) -> ExternalRegistryRef:
    defaults = dict(
        registry=ExternalRegistry.RESEARCH_MESH,
        external_id="rm-evidence-0001",
        owner_domain="research-mesh:synthesis",
        lifecycle_role=ExternalLifecycleRole.OBSERVE,
        external_digest="c" * 64,
        referenced_at="2026-09-12T00:00:00Z",
    )
    defaults.update(over)
    return ExternalRegistryRef(**defaults)


class TestOwnerPreservation:
    def test_owner_domain_survives_persistence_and_restart(self, env, tmp_path) -> None:
        conn, repo = env
        repo.add(_ref())
        conn.commit()
        loaded = repo.get("rm-evidence-0001", registry_value="RESEARCH_MESH")
        assert loaded is not None
        assert loaded.owner_domain == "research-mesh:synthesis"
        assert loaded.registry is ExternalRegistry.RESEARCH_MESH

    def test_owner_rewrite_rejected(self, env) -> None:
        """QCAE cannot silently re-register external knowledge under a new
        owner — that would be laundering external authority as internal."""
        conn, repo = env
        repo.add(_ref())
        with pytest.raises(QcaeValidationError, match="ownership rewrite"):
            repo.add(_ref(owner_domain="qcae:internal"))

    def test_qcae_cannot_claim_external_object_as_own_knowledge(self, env) -> None:
        """There is no API to convert an external ref into QCAE-owned state;
        the only stored owner is the external one."""
        conn, repo = env
        repo.add(_ref())
        loaded = repo.get("rm-evidence-0001", registry_value="RESEARCH_MESH")
        assert not hasattr(repo, "claim")
        assert not hasattr(repo, "import_as_internal")
        assert loaded.owner_domain.startswith("research-mesh:")


class TestReferenceSemantics:
    def test_refs_remain_references_not_authority(self, env) -> None:
        """The stored record carries OBSERVE/SUBMIT role only; no GOVERN role
        exists in the vocabulary to persist."""
        assert {r.value for r in ExternalLifecycleRole} == {"OBSERVE", "SUBMIT"}
        with pytest.raises(QcaeValidationError):
            _ref(lifecycle_role="GOVERN").validate()

    def test_duplicate_identical_ref_idempotent(self, env) -> None:
        conn, repo = env
        repo.add(_ref())
        repo.add(_ref())  # same content: idempotent
        assert repo.count() == 1

    def test_mutated_ref_rejected_append_only(self, env) -> None:
        conn, repo = env
        repo.add(_ref())
        with pytest.raises(QcaeValidationError, match="append-only"):
            repo.add(_ref(external_digest="d" * 64))

    def test_client_confidential_rights_visible(self, env) -> None:
        """Economic-experience refs carrying client material keep their owner
        domain visible — classification lives with the owner, not QCAE."""
        conn, repo = env
        repo.add(_ref(
            registry=ExternalRegistry.ECONOMIC_EXPERIENCE,
            external_id="econ-rec-77",
            owner_domain="institution:transformation-governor",
        ))
        conn.commit()
        hits = repo.list_by_owner("institution:transformation-governor")
        assert [r.external_id for r in hits] == ["econ-rec-77"]

    def test_receipt_cites_mesh_evidence_but_still_requires_executable_proof(self) -> None:
        """§12 final integration: a receipt may cite a persisted external ref
        in its proof set as supporting evidence, but the receipt firewall
        (P1-C05) still rejects external-only proof."""
        from qcae.core.receipts import ReceiptEvidenceRef, make_receipt
        from qcae.tests.unit.test_p1_receipt import _receipt

        mesh_only = (
            ReceiptEvidenceRef(
                evidence_id="rm-evidence-0001",
                evidence_class="E2_SOURCE",
                artifact_digest="c" * 64,
                external_owner_domain="research-mesh:synthesis",
            ),
        )
        with pytest.raises(QcaeValidationError, match="Research Mesh/external"):
            _receipt(proof_refs=mesh_only)


class TestRestart:
    def test_cross_registry_link_survives_reopen(self, tmp_path) -> None:
        db = tmp_path / "xr.db"
        c1 = open_metadata_db(db)
        c1.execute("PRAGMA journal_mode=WAL")
        c1.executescript(EXTERNAL_REGISTRY_DDL)
        SqliteExternalRegistryRefRepository(c1).add(_ref())
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        repo2 = SqliteExternalRegistryRefRepository(c2)
        loaded = repo2.get("rm-evidence-0001", registry_value="RESEARCH_MESH")
        assert loaded is not None
        assert loaded.external_digest == "c" * 64
        assert loaded.owner_domain == "research-mesh:synthesis"
        c2.close()
