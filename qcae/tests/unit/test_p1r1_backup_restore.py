"""P1-R1-C05 — registry backup/restore evidence (spec §10, §12 items 26–28)."""

from __future__ import annotations

import shutil

import pytest

from qcae.core.capabilities.atom import AtomType, CapabilityAtom
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.capabilities.composite import CompositionMember, CompositionRole
from qcae.core.capabilities.composite import CompositeCapability
from qcae.core.contracts.contract import CapabilityContract
from qcae.core.errors import QcaeValidationError
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.relationships.graph import EntityType
from qcae.core.vocabulary import VerificationLevel
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    CAPABILITY_REGISTRY_DDL,
    SqliteCapabilityRegistry,
)
from qcae.infrastructure.persistence.sqlite_knowledge_store import (
    KNOWLEDGE_DDL,
    SqliteReceiptRepository,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository
from qcae.infrastructure.persistence.sqlite_relationship_registry import (
    RELATIONSHIP_DDL,
    SqliteRelationshipPersistence,
)
from qcae.infrastructure.persistence.sqlite_repository_registry import (
    REPOSITORY_REGISTRY_DDL,
    SqliteRepositoryRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db

from qcae.tests.unit.test_p1_sqlite_store import _artifact
from qcae.tests.unit.test_p1_receipt import _receipt


def _build_full_registry_state(tmp_path):
    """Complete P1-R1 state: evidence + receipt + contracts/atoms/composites/
    candidates + repository records + linking relationships."""
    root = tmp_path / "runtime"
    conn = open_metadata_db(root / "meta.db")
    conn.executescript(KNOWLEDGE_DDL)
    conn.executescript(CAPABILITY_REGISTRY_DDL)
    conn.executescript(REPOSITORY_REGISTRY_DDL)
    conn.executescript(RELATIONSHIP_DDL)

    evidence = SqliteEvidenceRepository(conn)
    receipts = SqliteReceiptRepository(conn)
    caps = SqliteCapabilityRegistry(conn)
    repos = SqliteRepositoryRegistry(conn)
    rel = SqliteRelationshipPersistence(conn)

    evidence.add(_artifact("ev-1"))
    receipts.add(_receipt(receipt_id="r1"))

    caps.add_contract(CapabilityContract(
        capability_id="CAP-REPLAY-001", contract_version=1, request_id="req-1",
        title="replay", problem_statement="replay", intent="replay",
        required_behaviors=("event-sourcing",)))
    caps.add_atom(CapabilityAtom(
        atom_id="atom-replay", atom_version=1, name="replay",
        atom_type=AtomType.COMPUTATIONAL, description="replay events",
        parent_capabilities=("CAP-REPLAY-001",)))
    caps.add_composite(CompositeCapability(
        capability_id="CAP-REPLAY-001", contract_version=1, name="composite",
        members=(CompositionMember(atom_id="atom-replay", role=CompositionRole.REQUIRED),)))
    caps.add_candidate(Candidate(
        candidate_id="cand-1", name="impl-a",
        source_kind=CandidateSourceKind.REPOSITORY, source_ref="repo:owner/impl-a",
        revision="abc123", claims_atoms=("atom-replay",),
        claim_verification=VerificationLevel.DISCOVERED))

    repos.add(RepositoryRecord(
        repository_id="repo-1", source_kind=RepositorySourceKind.GIT,
        canonical_locator="git+https://example.com/owner/impl-a", revision="abc123"))

    rel.add(_edge())
    conn.commit()
    return conn, caps, repos, rel


def _edge():
    from qcae.core.relationships.graph import Relationship, EntityRef, RelationType

    return Relationship(
        source=EntityRef(entity_type=EntityType.COMPONENT, entity_id="cand-1"),
        relation=RelationType.IMPLEMENTS,
        target=EntityRef(entity_type=EntityType.CAPABILITY_ATOM, entity_id="atom-replay"),
        source_revision="abc123",
    )


class TestRegistryBackupRestore:
    def test_complete_registry_state_restores_exactly(self, tmp_path) -> None:
        """§10 flow: create → backup → destroy → restore → verify everything."""
        conn, caps, repos, rel = _build_full_registry_state(tmp_path)

        backup_dir = tmp_path / "backup"
        manifest = BackupService(conn).backup(backup_dir)
        assert manifest["registry_rows"]["capability_contract"] == 1
        assert manifest["registry_rows"]["capability_atom"] == 1
        assert manifest["registry_rows"]["composite_capability"] == 1
        assert manifest["registry_rows"]["candidate"] == 1
        assert manifest["registry_rows"]["repository_record"] == 1
        assert manifest["registry_rows"]["graph_relationship"] == 1
        conn.close()

        shutil.rmtree(tmp_path / "runtime")  # destroy live state

        RestoreService().restore(
            backup_dir, tmp_path / "restored" / "meta.db",
            tmp_path / "restored" / "artifacts")

        c2 = open_metadata_db(tmp_path / "restored" / "meta.db")
        caps2 = SqliteCapabilityRegistry(c2)
        repos2 = SqliteRepositoryRegistry(c2)
        rel2 = SqliteRelationshipPersistence(c2)

        # canonical IDs + revisions
        contract = caps2.get_contract("CAP-REPLAY-001", 1)
        assert contract is not None and contract.title == "replay"
        atom = caps2.get_atom("atom-replay")
        assert atom is not None and atom.parent_capabilities == ("CAP-REPLAY-001",)
        candidate = caps2.get_candidate("cand-1")
        assert candidate is not None and candidate.revision == "abc123"
        # composition survives
        members = caps2.member_atoms("CAP-REPLAY-001", 1)
        assert [a.atom_id for a in members] == ["atom-replay"]
        # repository identity survives
        repo = repos2.get("repo-1")
        assert repo is not None and repo.revision == "abc123"
        assert len(repos2.list_revisions(
            RepositorySourceKind.GIT, "git+https://example.com/owner/impl-a")) == 1
        # linking graph survives
        edges = rel2.edges_implementing(EntityType.CAPABILITY_ATOM, "atom-replay")
        assert len(edges) == 1 and edges[0].source.entity_id == "cand-1"
        # evidence/receipts still resolve
        evidence2 = SqliteEvidenceRepository(c2)
        receipts2 = SqliteReceiptRepository(c2)
        assert evidence2.get("ev-1") is not None
        assert receipts2.get("r1") is not None
        c2.close()

    def test_restore_verifies_declared_registry_counts(self, tmp_path) -> None:
        conn, caps, repos, rel = _build_full_registry_state(tmp_path)
        backup_dir = tmp_path / "backup"
        BackupService(conn).backup(backup_dir)
        conn.close()

        # corrupt a registry table inside the backup db: the metadata-db
        # digest check (outer guard) fires before the per-table count check
        # can. Both layers must reject. (sqlite3 engine access is confined to
        # qcae/infrastructure; open the backup db via the sanctioned factory.)
        from qcae.infrastructure.persistence.store_factory import open_raw_connection

        meta = backup_dir / "metadata.db"
        c = open_raw_connection(meta)
        c.execute("DELETE FROM candidate WHERE candidate_id = 'cand-1'")
        c.commit()
        c.close()

        with pytest.raises(QcaeValidationError, match="metadata database failed digest"):
            RestoreService().restore(
                backup_dir, tmp_path / "restored" / "meta.db",
                tmp_path / "restored" / "artifacts")

        # inner layer: an intact-db copy with doctored manifest counts must
        # also be rejected by the per-table verification
        import json as _json

        manifest = _json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
        conn_ok = open_raw_connection(meta)
        conn_ok.execute("INSERT INTO candidate (candidate_id, source_ref, revision,"
                        " payload_json, payload_digest) SELECT candidate_id, source_ref,"
                        " revision, payload_json, payload_digest FROM candidate")
        conn_ok.commit()
        conn_ok.close()
        # recompute db digest so the outer check passes, then doctor counts
        from qcae.infrastructure.persistence.backup_restore import _file_sha256

        manifest["metadata_db_sha256"] = _file_sha256(meta)
        manifest["registry_rows"]["candidate"] = 999
        (backup_dir / "manifest.json").write_text(
            _json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        with pytest.raises(QcaeValidationError, match="candidate"):
            RestoreService().restore(
                backup_dir, tmp_path / "restored2" / "meta.db",
                tmp_path / "restored2" / "artifacts")
