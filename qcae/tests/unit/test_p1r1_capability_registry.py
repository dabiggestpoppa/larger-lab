"""P1-R1-C01 — CapabilityRegistry persistence evidence (spec §12 items 6–15)."""

from __future__ import annotations

import pytest

from qcae.core.capabilities.atom import (
    AtomStatus,
    AtomType,
    CapabilityAtom,
)
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.capabilities.composite import CompositionMember, CompositionRole
from qcae.core.capabilities.composite import CompositeCapability
from qcae.core.contracts.contract import CapabilityContract
from qcae.core.errors import QcaeValidationError
from qcae.core.vocabulary import VerificationLevel
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    CAPABILITY_REGISTRY_DDL,
    SqliteCapabilityRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def reg():
    conn = open_metadata_db(":memory:")
    conn.executescript(CAPABILITY_REGISTRY_DDL)
    yield SqliteCapabilityRegistry(conn), conn
    conn.close()


def _contract(cap="CAP-REPLAY-001", version=1, **over) -> CapabilityContract:
    defaults = dict(
        capability_id=cap,
        contract_version=version,
        request_id="req-001",
        title="replay engine",
        problem_statement="deterministic replay for backtests",
        intent="provide replay semantics",
        required_behaviors=("event sourcing",),
    )
    defaults.update(over)
    return CapabilityContract(**defaults)


def _atom(aid="atom-replay-engine", version=1, **over) -> CapabilityAtom:
    defaults = dict(
        atom_id=aid,
        atom_version=version,
        name="replay engine",
        atom_type=AtomType.COMPUTATIONAL,
        description="replay event streams deterministically",
    )
    defaults.update(over)
    return CapabilityAtom(**defaults)


def _candidate(cid="cand-impl-a", atom="atom-replay-engine", **over) -> Candidate:
    defaults = dict(
        candidate_id=cid,
        name="impl A",
        source_kind=CandidateSourceKind.REPOSITORY,
        source_ref="repo:owner/impl-a",
        revision="abc123",
        claims_atoms=(atom,),
        claim_verification=VerificationLevel.DISCOVERED,
    )
    defaults.update(over)
    return Candidate(**defaults)


def _composite(cap="CAP-REPLAY-001", version=1, members=None) -> CompositeCapability:
    return CompositeCapability(
        capability_id=cap,
        contract_version=version,
        name="replay composite",
        members=members
        or (
            CompositionMember(atom_id="atom-replay-engine", role=CompositionRole.REQUIRED),
            CompositionMember(atom_id="atom-ordering", role=CompositionRole.OPTIONAL),
        ),
    )


class TestContractPersistence:
    def test_persist_and_restart(self, tmp_path) -> None:
        db = tmp_path / "cap.db"
        c1 = open_metadata_db(db)
        c1.executescript(CAPABILITY_REGISTRY_DDL)
        SqliteCapabilityRegistry(c1).add_contract(_contract())
        c1.commit()
        c1.close()
        c2 = open_metadata_db(db)
        r2 = SqliteCapabilityRegistry(c2)
        loaded = r2.get_contract("CAP-REPLAY-001", 1)
        assert loaded is not None and loaded.title == "replay engine"
        c2.close()

    def test_multiple_versions_coexist(self, reg) -> None:
        registry, _ = reg
        registry.add_contract(_contract(version=1))
        registry.add_contract(
            _contract(version=2, supersedes_contract="CAP-REPLAY-001:v1")
        )
        assert len(registry.list_contract_versions("CAP-REPLAY-001")) == 2
        assert registry.get_contract("CAP-REPLAY-001", 1) is not None
        assert registry.get_contract("CAP-REPLAY-001", 2) is not None

    def test_latest_version_retrieval(self, reg) -> None:
        registry, _ = reg
        registry.add_contract(_contract(version=1))
        registry.add_contract(_contract(version=2, supersedes_contract="CAP-REPLAY-001:v1"))
        registry.add_contract(_contract(version=10, supersedes_contract="CAP-REPLAY-001:v2"))
        assert registry.latest_contract("CAP-REPLAY-001").contract_version == 10

    def test_supersession_chain_ordered(self, reg) -> None:
        registry, _ = reg
        registry.add_contract(_contract(version=1))
        registry.add_contract(_contract(version=2, supersedes_contract="CAP-REPLAY-001:v1"))
        chain = registry.contract_supersession_chain("CAP-REPLAY-001")
        assert [c.contract_version for c in chain] == [1, 2]

    def test_duplicate_version_rejected_no_mutable_overwrite(self, reg) -> None:
        registry, _ = reg
        registry.add_contract(_contract(version=1))
        with pytest.raises(QcaeValidationError, match="new version is a new record"):
            registry.add_contract(_contract(version=1, title="rewritten history"))

    def test_tampered_contract_row_detected(self, reg) -> None:
        registry, conn = reg
        registry.add_contract(_contract(version=1))
        conn.commit()
        conn.execute(
            "UPDATE capability_contract SET payload_json = json_set(payload_json,"
            " '$.required_behaviors', '[\"forged behavior\"]')"
            " WHERE capability_id='CAP-REPLAY-001'")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            registry.get_contract("CAP-REPLAY-001", 1)


class TestAtomPersistence:
    def test_persist_and_restart(self, tmp_path) -> None:
        db = tmp_path / "atom.db"
        c1 = open_metadata_db(db)
        c1.executescript(CAPABILITY_REGISTRY_DDL)
        SqliteCapabilityRegistry(c1).add_atom(_atom(parent_capabilities=("CAP-REPLAY-001",)))
        c1.commit()
        c1.close()
        c2 = open_metadata_db(db)
        assert SqliteCapabilityRegistry(c2).get_atom("atom-replay-engine") is not None
        c2.close()

    def test_by_parent_capability(self, reg) -> None:
        registry, _ = reg
        registry.add_atom(_atom("atom-a", parent_capabilities=("CAP-1",)))
        registry.add_atom(_atom("atom-b", parent_capabilities=("CAP-1",)))
        registry.add_atom(_atom("atom-c", parent_capabilities=("CAP-2",)))
        ids = {a.atom_id for a in registry.list_atoms_for_capability("CAP-1")}
        assert ids == {"atom-a", "atom-b"}

    def test_by_status_and_domain(self, reg) -> None:
        registry, _ = reg
        registry.add_atom(_atom("atom-a", status=AtomStatus.ACTIVE, domain="quant"))
        registry.add_atom(_atom("atom-b", status=AtomStatus.PROPOSED, domain="quant"))
        active = {a.atom_id for a in registry.list_atoms_by_status(AtomStatus.ACTIVE)}
        assert active == {"atom-a"}
        assert len(registry.list_atoms_by_domain("quant")) == 2


class TestCompositePersistence:
    def test_membership_survives_restart(self, tmp_path) -> None:
        db = tmp_path / "comp.db"
        c1 = open_metadata_db(db)
        c1.executescript(CAPABILITY_REGISTRY_DDL)
        registry1 = SqliteCapabilityRegistry(c1)
        registry1.add_atom(_atom("atom-replay-engine"))
        registry1.add_atom(_atom("atom-ordering"))
        registry1.add_composite(_composite())
        c1.commit()
        c1.close()

        c2 = open_metadata_db(db)
        registry2 = SqliteCapabilityRegistry(c2)
        members = registry2.member_atoms("CAP-REPLAY-001", 1)
        assert {a.atom_id for a in members} == {"atom-replay-engine", "atom-ordering"}
        c2.close()


class TestCandidatePersistence:
    def test_multiple_implementations_of_same_atom(self, reg) -> None:
        """Identity law: same atom + multiple implementations is ONE capability
        with several candidates, never several capabilities."""
        registry, _ = reg
        registry.add_atom(_atom())
        registry.add_candidate(_candidate("cand-a", source_ref="repo:owner/impl-a"))
        registry.add_candidate(_candidate("cand-b", source_ref="repo:owner/impl-b",
                                          revision="def456"))
        hits = registry.list_candidates_for_atom("atom-replay-engine")
        assert {c.candidate_id for c in hits} == {"cand-a", "cand-b"}

    def test_candidate_retrieval_by_source_revision(self, reg) -> None:
        registry, _ = reg
        registry.add_candidate(_candidate("cand-a", revision="v1"))
        registry.add_candidate(_candidate("cand-b", source_ref="repo:owner/impl-a",
                                          revision="v2"))
        assert [c.candidate_id for c in registry.list_candidates_by_source(
            "repo:owner/impl-a", "v2")] == ["cand-b"]
        assert len(registry.list_candidates_by_source("repo:owner/impl-a")) == 2

    def test_duplicate_candidate_rejected(self, reg) -> None:
        registry, _ = reg
        registry.add_candidate(_candidate("cand-a"))
        with pytest.raises(QcaeValidationError, match="new candidate record"):
            registry.add_candidate(_candidate("cand-a", revision="v2"))
