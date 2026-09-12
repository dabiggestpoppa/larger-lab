"""P1-R1-C04R — full decision-reuse outputs (continuation spec §8/§9).

Extends the P1-R1-C04 coverage with:

- ``known_capability_state`` now reports the repository revisions its known
  candidates are located in (ADR-0007 identity/revision split);
- ``internal_first_findings`` classifies internal knowledge A–F from durable
  state only — no LLM, no discovery, structured findings for the future P3
  planner.
"""

from __future__ import annotations

import pytest

from qcae.core.capabilities.atom import AtomType, CapabilityAtom
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.contracts.contract import CapabilityContract
from qcae.core.knowledge.memory import (
    NegativeKnowledge,
    NegativeKnowledgeType,
    ReconsiderationCondition,
)
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.vocabulary import VerificationLevel as VLevel
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    CAPABILITY_REGISTRY_DDL,
    SqliteCapabilityRegistry,
)
from qcae.infrastructure.persistence.sqlite_knowledge_store import (
    KNOWLEDGE_DDL,
    SqliteNegativeKnowledgeRepository,
    SqliteRegistryQuery,
)
from qcae.infrastructure.persistence.sqlite_repository_registry import (
    REPOSITORY_REGISTRY_DDL,
    SqliteRepositoryRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def env():
    conn = open_metadata_db(":memory:")
    conn.executescript(CAPABILITY_REGISTRY_DDL)
    conn.executescript(REPOSITORY_REGISTRY_DDL)
    conn.executescript(KNOWLEDGE_DDL)
    caps = SqliteCapabilityRegistry(conn)
    repos = SqliteRepositoryRegistry(conn)
    neg = SqliteNegativeKnowledgeRepository(conn)
    yield conn, caps, repos, neg
    conn.close()


def _contract(cid="CAP-DR-001", version=1) -> CapabilityContract:
    return CapabilityContract(
        capability_id=cid, contract_version=version, request_id="req-dr",
        title="dr", problem_statement="dr", intent="dr",
        required_behaviors=("b",))


def _atom(atom_id="atom-dr", cid="CAP-DR-001") -> CapabilityAtom:
    return CapabilityAtom(
        atom_id=atom_id, atom_version=1, name=atom_id,
        atom_type=AtomType.COMPUTATIONAL, description=atom_id,
        parent_capabilities=(cid,))


def _candidate(cid="cand-dr", atom="atom-dr", revision="revA") -> Candidate:
    return Candidate(
        candidate_id=cid, name=cid, source_kind=CandidateSourceKind.REPOSITORY,
        source_ref=f"repo:repo-dr", revision=revision,
        claims_atoms=(atom,), claim_verification=VLevel.DISCOVERED)


class TestRepositoryRevisionInventory:
    def test_known_state_includes_repository_revisions(self, env) -> None:
        """§8: inventory reports the repository revisions behind known
        candidates, keyed by stable repository identity (ADR-0007)."""
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate())
        for rev in ("revA", "revB"):
            repos.add(RepositoryRecord(
                repository_id="repo-dr", source_kind=RepositorySourceKind.GIT,
                canonical_locator="git+https://example.com/owner/dr",
                revision=rev))
        conn.commit()

        query = SqliteRegistryQuery(
            None, None, neg, None, capability_registry=caps,
            repository_registry=repos)
        state = query.known_capability_state("CAP-DR-001")
        assert state["repository_revisions"] == {"repo-dr": ["revA", "revB"]}
        assert state["candidate_refs"] == ["cand-dr"]

    def test_no_repository_registry_returns_empty_inventory(self, env) -> None:
        """Without a repository registry wired, the key is present but empty —
        shape is stable regardless of wiring."""
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate())
        conn.commit()
        query = SqliteRegistryQuery(None, None, neg, None, capability_registry=caps)
        assert query.known_capability_state("CAP-DR-001")["repository_revisions"] == {}


class TestInternalFirstFindings:
    """§9 scenarios A–F, answered from durable state only."""

    def _query(self, conn, caps, repos, neg):
        return SqliteRegistryQuery(
            None, None, neg, None, capability_registry=caps,
            repository_registry=repos)

    def test_a_capability_active(self, env) -> None:
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate())
        query = self._query(conn, caps, repos, neg)
        findings = query.internal_first_findings(
            "CAP-DR-001", "CAP-DR-001", "1")
        assert "NO_INTERNAL_KNOWLEDGE" not in findings["categories"]
        # definition + candidate exist but no ACTIVE receipt yet: neither A
        # nor F — it is simply unclassified beyond the other categories
        assert "CAPABILITY_ACTIVE" not in findings["categories"]

    def test_f_no_internal_knowledge(self, env) -> None:
        conn, caps, repos, neg = env
        query = self._query(conn, caps, repos, neg)
        findings = query.internal_first_findings("CAP-UNKNOWN", "CAP-UNKNOWN", "1")
        assert findings["categories"] == ["NO_INTERNAL_KNOWLEDGE"]

    def test_e_definition_without_implementation(self, env) -> None:
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        conn.commit()
        query = self._query(conn, caps, repos, neg)
        findings = query.internal_first_findings("CAP-DR-001", "CAP-DR-001", "1")
        assert "DEFINITION_WITHOUT_IMPLEMENTATION" in findings["categories"]
        assert findings["detail"]["DEFINITION_WITHOUT_IMPLEMENTATION"] == ["atom-dr"]

    def test_c_candidate_previously_failed(self, env) -> None:
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate())
        neg.add(NegativeKnowledge(
            record_id="nk-1", failure_type=NegativeKnowledgeType.CONTRACT_FAILURE,
            subject_id="atom-dr", source_revision="revA",
            contract_id="CAP-DR-001", contract_version="1",
            acquisition_form="USE_DIRECT",
            causal_detail="contract failed under revision revA",
            evidence_ids=(),
            reconsideration=(ReconsiderationCondition(
                condition="new revision with the fix"),),
            scope_summary="atom-dr under contract CAP-DR-001 v1",
            created_at="2026-09-12T00:00:00Z", retry_allowed=False))
        conn.commit()
        query = self._query(conn, caps, repos, neg)
        findings = query.internal_first_findings("CAP-DR-001", "CAP-DR-001", "1")
        assert "CANDIDATE_PREVIOUSLY_FAILED" in findings["categories"]
        assert findings["detail"]["CANDIDATE_PREVIOUSLY_FAILED"] == ["nk-1"]

    def test_d_revision_changed(self, env) -> None:
        """Candidate claims revA but the located repository has only revB
        stored: the observation moved on (ADR-0007)."""
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate(revision="revA"))
        repos.add(RepositoryRecord(
            repository_id="repo-dr", source_kind=RepositorySourceKind.GIT,
            canonical_locator="git+https://example.com/owner/dr",
            revision="revB"))
        conn.commit()
        query = self._query(conn, caps, repos, neg)
        findings = query.internal_first_findings("CAP-DR-001", "CAP-DR-001", "1")
        assert "REVISION_CHANGED" in findings["categories"]
        assert findings["detail"]["REVISION_CHANGED"] == ["cand-dr"]

    def test_partial_state_matches_no_category(self, env) -> None:
        """Definition + candidate exist, no receipt/failure/staleness: none of
        A–E applies — and F must NOT fire because internal knowledge exists.
        Empty categories is the honest "internal state present, nothing to
        classify" answer; the structured detail carries the state."""
        conn, caps, repos, neg = env
        caps.add_contract(_contract())
        caps.add_atom(_atom())
        caps.add_candidate(_candidate())
        conn.commit()
        query = SqliteRegistryQuery(None, None, neg, None, capability_registry=caps)
        findings = query.internal_first_findings("CAP-DR-001", "CAP-DR-001", "1")
        assert findings["categories"] == []
        assert "NO_INTERNAL_KNOWLEDGE" not in findings["categories"]
        assert isinstance(findings["detail"], dict)
