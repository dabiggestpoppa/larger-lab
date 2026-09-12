"""P1-R1-C03 — registry relationship evidence (spec §12 items 22–25, §5 identity law)."""

from __future__ import annotations

import pytest

from qcae.core.capabilities.atom import AtomType, CapabilityAtom
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.errors import QcaeValidationError
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.relationships.graph import (
    EntityType,
    Relationship,
    RelationType,
)
from qcae.core.vocabulary import VerificationLevel as VLevel
from qcae.infrastructure.persistence.registry_service import RegistryService
from qcae.infrastructure.persistence.sqlite_relationship_registry import (
    RELATIONSHIP_DDL,
    SqliteRelationshipPersistence,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(RELATIONSHIP_DDL)
    rel = SqliteRelationshipPersistence(conn)
    svc = RegistryService(rel)
    yield conn, rel, svc
    conn.close()


def _repo(rid="repo-001", revision="abc123", kind=RepositorySourceKind.GIT) -> RepositoryRecord:
    return RepositoryRecord(
        repository_id=rid,
        source_kind=kind,
        canonical_locator=f"git+https://example.com/owner/{rid}",
        revision=revision,
    )


def _candidate(cid="cand-001", atom="atom-1", kind=CandidateSourceKind.REPOSITORY) -> Candidate:
    return Candidate(
        candidate_id=cid,
        name=f"candidate {cid}",
        source_kind=kind,
        source_ref=f"repo:owner/{cid}",
        revision="abc123",
        claims_atoms=(atom,),
        claim_verification=VLevel.DISCOVERED,
    )


class TestRepositoryAtomLinks:
    def test_repository_implements_atom(self, env) -> None:
        conn, rel, svc = env
        edge = svc.repository_implements_atom(
            _repo(), "atom-1", verification=VLevel.CODE_VERIFIED)
        assert edge.relation is RelationType.IMPLEMENTS
        assert edge.source.entity_id == "repo-001"
        assert edge.source_revision == "abc123"  # revision-scoped (canon 1.3.12)

    def test_repository_links_to_multiple_atoms(self, env) -> None:
        """Identity law: one repository + multiple atoms ≠ one indivisible capability."""
        conn, rel, svc = env
        repo = _repo()
        for atom in ("atom-1", "atom-2", "atom-3"):
            svc.repository_implements_atom(repo, atom)
        hits = svc.atoms_implemented_by_repository("repo-001")
        assert {e.target.entity_id for e in hits} == {"atom-1", "atom-2", "atom-3"}

    def test_one_capability_candidates_across_repositories(self, env) -> None:
        """Same atom implemented from two different repositories."""
        conn, rel, svc = env
        svc.repository_implements_atom(_repo("repo-a"), "atom-shared")
        svc.repository_implements_atom(_repo("repo-b"), "atom-shared")
        implementers = svc.candidates_for_atom("atom-shared")
        assert {e.source.entity_id for e in implementers} == {"repo-a", "repo-b"}

    def test_non_code_container_cannot_implement(self, env) -> None:
        conn, rel, svc = env
        paper_repo = _repo("repo-paper", kind=RepositorySourceKind.PAPER_IMPL)
        with pytest.raises(QcaeValidationError, match="code container"):
            svc.repository_implements_atom(paper_repo, "atom-1")

    def test_illegal_endpoint_rejected_by_canon_rules(self, env) -> None:
        """The frozen 1.3.4 endpoint enforcement still guards persistence."""
        conn, rel, svc = env
        bad = {
            "source": {"entity_type": "CAPABILITY_ATOM", "entity_id": "atom-1"},
            "relation": "implements",
            "target": {"entity_type": "CAPABILITY_ATOM", "entity_id": "atom-2"},
        }
        with pytest.raises(QcaeValidationError, match="IMPLEMENTS source"):
            rel.add(Relationship.from_dict(
                {**bad, "schema_version": 1, "object_type": "Relationship"}))


class TestCandidateLinks:
    def test_candidate_implements_and_located_in(self, env) -> None:
        conn, rel, svc = env
        cand = _candidate()
        repo = _repo()
        svc.candidate_implements_atom(cand, "atom-1", verification=VLevel.DISCOVERED)
        svc.candidate_located_in_repository(cand, repo)
        impl = svc.candidates_for_atom("atom-1")
        located = svc.candidates_in_repository("repo-001")
        assert {e.source.entity_id for e in impl} == {"cand-001"}
        assert {e.source.entity_id for e in located} == {"cand-001"}

    def test_candidate_can_claim_multiple_atoms(self, env) -> None:
        conn, rel, svc = env
        cand = _candidate()
        svc.candidate_implements_atom(cand, "atom-1", verification=VLevel.DISCOVERED)
        svc.candidate_implements_atom(cand, "atom-2", verification=VLevel.DISCOVERED)
        atoms = {e.target.entity_id
                 for e in rel.edges_from(EntityType.COMPONENT, "cand-001")}
        assert atoms == {"atom-1", "atom-2"}


class TestPersistenceIntegrity:
    def test_relationship_survives_restart(self, tmp_path) -> None:
        db = tmp_path / "rel.db"
        c1 = open_metadata_db(db)
        c1.executescript(RELATIONSHIP_DDL)
        svc1 = RegistryService(SqliteRelationshipPersistence(c1))
        svc1.repository_implements_atom(
            _repo(), "atom-1", verification=VLevel.CODE_VERIFIED)
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        svc2 = RegistryService(SqliteRelationshipPersistence(c2))
        hits = svc2.atoms_implemented_by_repository("repo-001")
        assert len(hits) == 1
        assert hits[0].verification is VLevel.CODE_VERIFIED
        c2.close()

    def test_tampered_edge_detected(self, env) -> None:
        conn, rel, svc = env
        svc.repository_implements_atom(_repo(), "atom-1")
        conn.commit()
        conn.execute(
            "UPDATE graph_relationship SET payload_json = json_set(payload_json,"
            " '$.verification', 'DOMAIN_VERIFIED')")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            rel.all_edges()

    def test_duplicate_edge_idempotent(self, env) -> None:
        conn, rel, svc = env
        svc.repository_implements_atom(_repo(), "atom-1")
        svc.repository_implements_atom(_repo(), "atom-1")
        assert len(rel.all_edges()) == 1
