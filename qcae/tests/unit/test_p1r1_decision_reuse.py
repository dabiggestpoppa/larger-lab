"""P1-R1-C04 — decision-reuse extension evidence (spec §11)."""

from __future__ import annotations

import pytest

from qcae.core.capabilities.atom import AtomStatus, AtomType, CapabilityAtom
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.capabilities.composite import CompositionMember, CompositionRole
from qcae.core.capabilities.composite import CompositeCapability
from qcae.core.contracts.contract import CapabilityContract
from qcae.core.ports.capability_registry import CapabilityRegistryPort
from qcae.core.vocabulary import VerificationLevel
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    CAPABILITY_REGISTRY_DDL,
    SqliteCapabilityRegistry,
)
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


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(KNOWLEDGE_DDL)
    conn.executescript(CAPABILITY_REGISTRY_DDL)
    caps = SqliteCapabilityRegistry(conn)
    query = SqliteRegistryQuery(
        SqliteReceiptRepository(conn),
        SqlitePositiveKnowledgeRepository(conn),
        SqliteNegativeKnowledgeRepository(conn),
        SqliteLifecycleLogRepository(conn),
        capability_registry=caps,
    )
    yield caps, query, conn
    conn.close()


def _contract(cap="CAP-REPLAY-001", version=1, **over) -> CapabilityContract:
    defaults = dict(
        capability_id=cap,
        contract_version=version,
        request_id="req-1",
        title="replay",
        problem_statement="replay",
        intent="replay",
        required_behaviors=("x",),
    )
    defaults.update(over)
    return CapabilityContract(**defaults)


def _atom(aid, cap="CAP-REPLAY-001") -> CapabilityAtom:
    return CapabilityAtom(
        atom_id=aid,
        atom_version=1,
        name=aid,
        atom_type=AtomType.COMPUTATIONAL,
        description=aid,
        parent_capabilities=(cap,),
    )


def _candidate(cid, atom) -> Candidate:
    return Candidate(
        candidate_id=cid,
        name=cid,
        source_kind=CandidateSourceKind.REPOSITORY,
        source_ref=f"repo:owner/{cid}",
        revision="abc123",
        claims_atoms=(atom,),
        claim_verification=VerificationLevel.DISCOVERED,
    )


class TestKnownCapabilityState:
    def test_empty_registry_returns_structured_unknowns(self, env) -> None:
        caps, query, _ = env
        state = query.known_capability_state("CAP-UNKNOWN-001")
        assert state == {
            "contract_versions": [],
            "latest_contract_version": None,
            "atom_ids": [],
            "composite_member_count": None,
            "candidate_refs": [],
            "repository_revisions": {},
        }

    def test_full_inventory_assembled(self, env) -> None:
        caps, query, _ = env
        caps.add_contract(_contract(version=1))
        caps.add_contract(_contract(version=2, supersedes_contract="CAP-REPLAY-001:v1"))
        caps.add_atom(_atom("atom-a"))
        caps.add_atom(_atom("atom-b"))
        caps.add_composite(CompositeCapability(
            capability_id="CAP-REPLAY-001",
            contract_version=2,
            name="replay composite",
            members=(
                CompositionMember(atom_id="atom-a", role=CompositionRole.REQUIRED),
                CompositionMember(atom_id="atom-b", role=CompositionRole.OPTIONAL),
            ),
        ))
        caps.add_candidate(_candidate("cand-1", "atom-a"))
        caps.add_candidate(_candidate("cand-2", "atom-a"))
        caps.add_candidate(_candidate("cand-3", "atom-b"))
        caps._conn.commit()
        state = query.known_capability_state("CAP-REPLAY-001")
        assert state["contract_versions"] == [1, 2]
        assert state["latest_contract_version"] == 2
        assert state["atom_ids"] == ["atom-a", "atom-b"]
        assert state["composite_member_count"] == 2
        assert state["candidate_refs"] == ["cand-1", "cand-2", "cand-3"]

    def test_decision_reuse_still_works_with_registry_wired(self, env) -> None:
        """Regression: the original 9.7 query is unchanged by the extension."""
        caps, query, conn = env
        caps.add_contract(_contract())
        conn.commit()
        findings = query.decision_reuse_findings("CAP-REPLAY-001", "CAP-REPLAY-001", "1.0.0")
        assert findings["active_receipts"] == []
        assert findings["sufficient_without_discovery"] is False

    def test_no_discovery_logic_in_p1(self, env) -> None:
        """The query must not fetch/search: it only reads stored state."""
        caps, query, _ = env
        assert not hasattr(query, "search_github")
        assert not hasattr(query, "discover")
        assert not hasattr(query, "fetch_remote")
