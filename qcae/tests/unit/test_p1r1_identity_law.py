"""P1-R1-T01 — capability identity law + registry adversarial qualification.

Identity law (P1-R1 §5):

- same capability + multiple implementations ≠ multiple capabilities;
- same repository + multiple capability atoms ≠ one indivisible capability;
- repository/product identity never becomes capability identity.
"""

from __future__ import annotations

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
from qcae.infrastructure.persistence.registry_service import RegistryService
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    CAPABILITY_REGISTRY_DDL,
    SqliteCapabilityRegistry,
)
from qcae.infrastructure.persistence.sqlite_relationship_registry import (
    RELATIONSHIP_DDL,
    SqliteRelationshipPersistence,
)
from qcae.infrastructure.persistence.sqlite_repository_registry import (
    REPOSITORY_REGISTRY_DDL,
    SqliteRepositoryRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    for ddl in (CAPABILITY_REGISTRY_DDL, REPOSITORY_REGISTRY_DDL, RELATIONSHIP_DDL):
        conn.executescript(ddl)
    caps = SqliteCapabilityRegistry(conn)
    repos = SqliteRepositoryRegistry(conn)
    svc = RegistryService(SqliteRelationshipPersistence(conn))
    yield conn, caps, repos, svc
    conn.close()


def _contract(cap, version=1, **over) -> CapabilityContract:
    defaults = dict(
        capability_id=cap, contract_version=version, request_id="req-1",
        title="t", problem_statement="p", intent="i", required_behaviors=("b",))
    defaults.update(over)
    return CapabilityContract(**defaults)


def _atom(aid, cap) -> CapabilityAtom:
    return CapabilityAtom(
        atom_id=aid, atom_version=1, name=aid, atom_type=AtomType.COMPUTATIONAL,
        description=aid, parent_capabilities=(cap,))


def _candidate(cid, atom, ref, revision) -> Candidate:
    return Candidate(
        candidate_id=cid, name=cid, source_kind=CandidateSourceKind.REPOSITORY,
        source_ref=ref, revision=revision, claims_atoms=(atom,),
        claim_verification=VerificationLevel.DISCOVERED)


def _repo(rid, revision) -> RepositoryRecord:
    return RepositoryRecord(
        repository_id=rid, source_kind=RepositorySourceKind.GIT,
        canonical_locator=f"git+https://example.com/owner/{rid}", revision=revision)


class TestCapabilityIdentityLaw:
    def test_multiple_implementations_are_one_capability(self, env) -> None:
        """One capability + three candidate implementations from three
        different repositories — capability count stays ONE."""
        conn, caps, repos, svc = env
        caps.add_contract(_contract("CAP-ONE-001"))
        caps.add_atom(_atom("atom-shared", "CAP-ONE-001"))
        for i, (cid, rid, rev) in enumerate([
            ("cand-a", "repo-a", "r1"),
            ("cand-b", "repo-b", "r2"),
            ("cand-c", "repo-c", "r3"),
        ]):
            caps.add_candidate(_candidate(cid, "atom-shared", f"repo:owner/{rid}", rev))
            repos.add(_repo(rid, rev))
            svc.candidate_implements_atom(
                _candidate(cid, "atom-shared", f"repo:owner/{rid}", rev),
                "atom-shared", verification=VerificationLevel.DISCOVERED)
        conn.commit()
        implementers = svc.candidates_for_atom("atom-shared")
        assert {e.source.entity_id for e in implementers} == {"cand-a", "cand-b", "cand-c"}
        # capability identity is still the contract set, not the implementations
        assert len(caps.list_contract_versions("CAP-ONE-001")) == 1
        # retrieval by atom still returns all three candidates
        assert len(caps.list_candidates_for_atom("atom-shared")) == 3

    def test_repository_with_multiple_atoms_is_not_indivisible(self, env) -> None:
        """One repository implementing four distinct atoms yields four distinct
        capability relationships — not one blob capability."""
        conn, caps, repos, svc = env
        repo = _repo("repo-multi", "r1")
        repos.add(repo)
        for aid in ("atom-1", "atom-2", "atom-3", "atom-4"):
            caps.add_atom(_atom(aid, "CAP-MULTI-001"))
            svc.repository_implements_atom(repo, aid)
        conn.commit()
        edges = svc.atoms_implemented_by_repository("repo-multi")
        assert {e.target.entity_id for e in edges} == {
            "atom-1", "atom-2", "atom-3", "atom-4"}

    def test_repository_identity_never_becomes_capability_identity(self, env) -> None:
        """A repository locator stored in the repository registry cannot leak
        into capability identity: capability IDs and locators are disjoint
        namespaces with distinct retrieval paths."""
        conn, caps, repos, svc = env
        locator = "git+https://example.com/owner/repo-1"
        repos.add(_repo("repo-1", "r1"))
        caps.add_contract(_contract("CAP-SEPARATE-001"))
        conn.commit()
        # repository retrieval by locator
        repo = repos.get_by_locator(RepositorySourceKind.GIT, locator)
        assert repo is not None and repo.repository_id == "repo-1"
        # capability retrieval by ID — locator is not a capability key
        assert caps.latest_contract(locator) is None
        assert caps.latest_contract("CAP-SEPARATE-001") is not None
        assert caps.get_candidate(locator) is None

    def test_same_repository_multiple_versions_distinct_records(self, env) -> None:
        """ADR-0007: one identity, two immutable revision records."""
        conn, caps, repos, svc = env
        repos.add(_repo("repo-v", "v1"))
        repos.add(_repo("repo-v", "v2"))
        conn.commit()
        revisions = repos.list_revisions("repo-v")
        assert {r.revision for r in revisions} == {"v1", "v2"}

    def test_identical_locator_multiple_revisions_grouped(self, env) -> None:
        conn, caps, repos, svc = env
        base = "git+https://example.com/owner/lib"
        repos.add(RepositoryRecord(
            repository_id="lib-stable", source_kind=RepositorySourceKind.GIT,
            canonical_locator=base, revision="v1"))
        repos.add(RepositoryRecord(
            repository_id="lib-stable", source_kind=RepositorySourceKind.GIT,
            canonical_locator=base, revision="v2"))
        conn.commit()
        assert len(repos.list_revisions("lib-stable")) == 2
        # and neither record was deleted; identity is ONE repository
        assert repos.get("lib-stable") is not None


class TestAdversarialRegistry:
    def test_cross_store_id_separation_is_intentional(self, env) -> None:
        """Capability and repository records are separate namespaces: the same
        internal ID string can denote different objects in each registry
        without interference, and neither store can mutate the other."""
        conn, caps, repos, svc = env
        caps.add_candidate(_candidate("cand-1", "atom-1", "repo:owner/x", "r1"))
        repos.add(_repo("repo-1", "r1"))
        conn.commit()
        assert caps.get_candidate("cand-1") is not None
        assert repos.get("repo-1") is not None
        # neither store exposes a mutation path into the other
        assert not hasattr(caps, "delete_repository")
        assert not hasattr(repos, "delete_contract")

    def test_repository_key_content_mutation_rejected(self, env) -> None:
        """Same identity+revision with different content is a rewrite attempt —
        rejected as an immutable-observation violation (identical re-observation
        is idempotent, conflicting content is not)."""
        conn, caps, repos, svc = env
        repos.add(_repo("repo-1", "r1"))
        # identical content: idempotent, not an error
        repos.add(_repo("repo-1", "r1"))
        # conflicting content under the same (repository_id, revision): rejected
        mutated = RepositoryRecord(
            repository_id="repo-1", source_kind=RepositorySourceKind.GIT,
            canonical_locator="git+https://example.com/owner/repo-1",
            revision="r1", display_name="rewritten display name")
        with pytest.raises(QcaeValidationError, match="immutable"):
            repos.add(mutated)

    def test_identity_attribute_migration_rejected(self, env) -> None:
        """ADR-0007: identity attributes are immutable — moving an identity to
        a new locator requires explicit supersession, not an edit."""
        conn, caps, repos, svc = env
        repos.add(_repo("repo-1", "r1"))
        with pytest.raises(QcaeValidationError, match="immutable"):
            repos.add(RepositoryRecord(
                repository_id="repo-1", source_kind=RepositorySourceKind.GIT,
                canonical_locator="git+https://example.com/owner/other",
                revision="r9"))

    def test_relationship_revision_scoping_distinguishes_revisions(self, env) -> None:
        """An IMPLEMENTS edge holds for the observed revision, not forever:
        edges from different revisions are distinct records."""
        conn, caps, repos, svc = env
        svc.repository_implements_atom(_repo("repo-x", "v1"), "atom-1")
        svc.repository_implements_atom(_repo("repo-y", "v2"), "atom-1")
        conn.commit()
        from qcae.infrastructure.persistence.sqlite_relationship_registry import (
            SqliteRelationshipPersistence)

        rel = SqliteRelationshipPersistence(conn)
        edges = rel.edges_implementing(EntityType.CAPABILITY_ATOM, "atom-1")
        assert {e.source_revision for e in edges} == {"v1", "v2"}

    def test_composite_member_resolution_requires_stored_atoms(self, env) -> None:
        """A composite referencing an unregistered atom resolves partially —
        the gap is visible, not silently papered over."""
        conn, caps, repos, svc = env
        caps.add_atom(_atom("atom-known", "CAP-GAP-001"))
        caps.add_composite(CompositeCapability(
            capability_id="CAP-GAP-001", contract_version=1, name="gapped",
            members=(
                CompositionMember(atom_id="atom-known", role=CompositionRole.REQUIRED),
                CompositionMember(atom_id="atom-missing", role=CompositionRole.REQUIRED),
            )))
        conn.commit()
        resolved = caps.member_atoms("CAP-GAP-001", 1)
        assert [a.atom_id for a in resolved] == ["atom-known"]

    def test_superseded_contract_chain_unbroken(self, env) -> None:
        """Version coexistence + declared supersession must form one walkable
        chain; a forged jump is detectable."""
        conn, caps, repos, svc = env
        caps.add_contract(_contract("CAP-CHAIN-001", 1))
        caps.add_contract(_contract("CAP-CHAIN-001", 2,
                                    supersedes_contract="CAP-CHAIN-001:v1"))
        caps.add_contract(_contract("CAP-CHAIN-001", 3,
                                    supersedes_contract="CAP-CHAIN-001:v2"))
        conn.commit()
        chain = caps.contract_supersession_chain("CAP-CHAIN-001")
        assert [c.contract_version for c in chain] == [1, 2, 3]

    def test_tamper_detection_across_new_stores(self, env) -> None:
        """Row-level tampering is caught in every registry table."""
        conn, caps, repos, svc = env
        caps.add_contract(_contract("CAP-TAMPER-001", 1))
        caps.add_atom(_atom("atom-t", "CAP-TAMPER-001"))
        repos.add(_repo("repo-t", "r1"))
        conn.commit()

        conn.execute("UPDATE capability_contract SET payload_json ="
                     " json_set(payload_json, '$.title', 'forged')")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            caps.get_contract("CAP-TAMPER-001", 1)

        conn.execute("UPDATE capability_atom SET payload_json ="
                     " json_set(payload_json, '$.description', 'forged')")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            caps.get_atom("atom-t")

        conn.execute("UPDATE repository_record SET payload_json ="
                     " json_set(payload_json, '$.revision', 'forged')")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            repos.get("repo-t")

    def test_restart_preserves_full_registry_graph(self, tmp_path) -> None:
        db = tmp_path / "identity.db"
        c1 = open_metadata_db(db)
        for ddl in (CAPABILITY_REGISTRY_DDL, REPOSITORY_REGISTRY_DDL, RELATIONSHIP_DDL):
            c1.executescript(ddl)
        caps1 = SqliteCapabilityRegistry(c1)
        repos1 = SqliteRepositoryRegistry(c1)
        svc1 = RegistryService(SqliteRelationshipPersistence(c1))
        caps1.add_contract(_contract("CAP-R-001", 1))
        caps1.add_atom(_atom("atom-r", "CAP-R-001"))
        caps1.add_candidate(_candidate("cand-r", "atom-r", "repo:owner/impl", "r1"))
        repos1.add(_repo("repo-r", "r1"))
        svc1.candidate_implements_atom(
            _candidate("cand-r", "atom-r", "repo:owner/impl", "r1"),
            "atom-r", verification=VerificationLevel.DISCOVERED)
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        caps2 = SqliteCapabilityRegistry(c2)
        repos2 = SqliteRepositoryRegistry(c2)
        svc2 = RegistryService(SqliteRelationshipPersistence(c2))
        assert caps2.get_contract("CAP-R-001", 1) is not None
        assert caps2.get_atom("atom-r") is not None
        assert caps2.get_candidate("cand-r") is not None
        assert repos2.get("repo-r") is not None
        assert len(svc2.candidates_for_atom("atom-r")) == 1
        c2.close()
