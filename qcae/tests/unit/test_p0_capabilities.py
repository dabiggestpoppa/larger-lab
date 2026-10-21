"""P0-C05 — CapabilityAtom, CompositeCapability, Candidate evidence (canon 1.2/1.3)."""

from __future__ import annotations

import pytest

from qcae.core.capabilities.atom import (
    AtomCoupling,
    AtomProvenance,
    AtomStatus,
    AtomType,
    CapabilityAtom,
)
from qcae.core.capabilities.candidate import Candidate, CandidateSourceKind
from qcae.core.capabilities.composite import (
    CompositionMember,
    CompositionRole,
    CompositeCapability,
    make_composite,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.vocabulary import VerificationLevel


def make_atom(**overrides) -> CapabilityAtom:
    fields = {
        "atom_id": "CAP-ATOM-OB-STATE",
        "atom_version": 1,
        "name": "book-state-transition",
        "atom_type": AtomType.COMPUTATIONAL,
        "description": "Reconstruct L2 order-book state from an ordered event stream.",
        "acceptance_conditions": (
            "reconstructed state matches reference fixture at every checkpoint",
        ),
        "inputs": ("timestamped normalized market events",),
        "outputs": ("book snapshots",),
    }
    fields.update(overrides)
    return CapabilityAtom(**fields)


class TestAtom:
    def test_valid_atom(self) -> None:
        atom = make_atom()
        atom.validate()

    def test_atom_requires_acceptance_conditions(self) -> None:
        with pytest.raises(QcaeValidationError, match="acceptance_conditions"):
            make_atom(acceptance_conditions=()).validate()

    def test_atom_versioning_behavior_evolution(self) -> None:
        v1 = make_atom()
        v2 = make_atom(
            atom_version=2,
            description="Adds per-event deterministic replay.",
            acceptance_conditions=v1.acceptance_conditions
            + ("per-event replay is deterministic",),
        )
        v1.validate()
        v2.validate()
        assert v1.atom_id == v2.atom_id
        assert v2.atom_version > v1.atom_version
        assert v1.digest() != v2.digest()

    def test_atom_identity_independent_of_implementation(self) -> None:
        """Same atom, different candidate sets: identity is behavioral."""
        internal_atom = make_atom(
            implementation_candidates=("internal:orderbook-engine",),
            provenance=AtomProvenance.INTERNALLY_DEVELOPED,
        )
        external_atom = make_atom(
            implementation_candidates=("repo:acme/obtool@abc123", "pkg:pypi/obkit@2.1.0"),
            provenance=AtomProvenance.EXTRACTED,
        )
        internal_atom.validate()
        external_atom.validate()
        # Same behavioral identity survives implementation replacement.
        assert internal_atom.atom_id == external_atom.atom_id
        assert internal_atom.name == external_atom.name
        assert internal_atom.atom_type == external_atom.atom_type
        # But the records differ in provenance/implementation fields.
        assert internal_atom.digest() != external_atom.digest()

    def test_atom_types_cover_canon_129(self) -> None:
        assert {t.value for t in AtomType} == {
            "COMPUTATIONAL", "DATA", "PROTOCOL", "STORAGE", "EXECUTION",
            "VALIDATION", "OBSERVABILITY", "INTERFACE", "RESEARCH", "ARCHITECTURE",
        }

    def test_coupling_classes_cover_canon_1214(self) -> None:
        assert {c.value for c in AtomCoupling} == {
            "NONE", "WEAK", "SHARED_LIBRARY", "SHARED_STATE", "SHARED_RUNTIME",
            "SHARED_SERVICE", "INSEPARABLE_IN_CURRENT_IMPLEMENTATION",
        }

    def test_atom_round_trip_with_enums(self) -> None:
        atom = make_atom(
            coupling=AtomCoupling.SHARED_RUNTIME,
            status=AtomStatus.ACTIVE,
            provenance=AtomProvenance.VENDORED,
            atom_type=AtomType.DATA,
        )
        rebuilt = CapabilityAtom.from_dict(atom.to_dict())
        assert rebuilt == atom
        assert rebuilt.coupling is AtomCoupling.SHARED_RUNTIME
        assert rebuilt.status is AtomStatus.ACTIVE
        assert rebuilt.provenance is AtomProvenance.VENDORED

    def test_atom_bad_type_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="atom_type"):
            make_atom(atom_type="COMPUTATIONAL").validate()

    def test_atom_bad_dependency_ref_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="dependencies entry"):
            make_atom(dependencies=("has spaces in it",)).validate()

    def test_atom_bad_version_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="atom_version"):
            make_atom(atom_version=0).validate()


def member(atom_id: str, role: CompositionRole) -> CompositionMember:
    return CompositionMember(atom_id=atom_id, role=role)


class TestComposite:
    def test_valid_composition_with_alternatives(self) -> None:
        composite = make_composite(
            capability_id="CAP-MD-HIST-001",
            contract_version=1,
            name="historical-market-data",
            members=(
                member("CAP-ATOM-INGEST", CompositionRole.REQUIRED),
                member("CAP-ATOM-NORMALIZE", CompositionRole.REQUIRED),
                member("CAP-ATOM-COMPRESS", CompositionRole.OPTIONAL),
                member("CAP-ATOM-PARQUET", CompositionRole.ALTERNATIVE),
                member("CAP-ATOM-TSDB", CompositionRole.ALTERNATIVE),
            ),
        )
        assert len(composite.members) == 5

    def test_single_member_alternative_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="single-member ALTERNATIVE"):
            make_composite(
                capability_id="CAP-X-001",
                contract_version=1,
                name="broken-composite",
                members=(
                    member("CAP-ATOM-A", CompositionRole.REQUIRED),
                    member("CAP-ATOM-B", CompositionRole.ALTERNATIVE),
                ),
            )

    def test_required_atom_in_alternative_group_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="REQUIRED and ALTERNATIVE"):
            make_composite(
                capability_id="CAP-X-002",
                contract_version=1,
                name="contradictory-composite",
                members=(
                    member("CAP-ATOM-A", CompositionRole.REQUIRED),
                    member("CAP-ATOM-A", CompositionRole.ALTERNATIVE),
                    member("CAP-ATOM-B", CompositionRole.ALTERNATIVE),
                ),
            )

    def test_only_optional_members_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="only OPTIONAL"):
            make_composite(
                capability_id="CAP-X-003",
                contract_version=1,
                name="vacuous-composite",
                members=(
                    member("CAP-ATOM-A", CompositionRole.OPTIONAL),
                    member("CAP-ATOM-B", CompositionRole.OPTIONAL),
                ),
            )

    def test_empty_members_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least one member"):
            make_composite(
                capability_id="CAP-X-004",
                contract_version=1,
                name="empty-composite",
                members=(),
            )

    def test_duplicate_members_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_composite(
                capability_id="CAP-X-005",
                contract_version=1,
                name="dupe-composite",
                members=(
                    member("CAP-ATOM-A", CompositionRole.REQUIRED),
                    member("CAP-ATOM-A", CompositionRole.REQUIRED),
                ),
            )

    def test_composite_round_trip(self) -> None:
        composite = make_composite(
            capability_id="CAP-MD-HIST-002",
            contract_version=2,
            name="historical-market-data-v2",
            members=(
                member("CAP-ATOM-INGEST", CompositionRole.REQUIRED),
                member("CAP-ATOM-PARQUET", CompositionRole.ALTERNATIVE),
                member("CAP-ATOM-TSDB", CompositionRole.ALTERNATIVE),
            ),
        )
        rebuilt = CompositeCapability.from_dict(composite.to_dict())
        assert rebuilt == composite
        assert all(isinstance(m, CompositionMember) for m in rebuilt.members)
        assert rebuilt.members[0].role is CompositionRole.REQUIRED

    def test_member_bad_role_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="role"):
            CompositionMember(atom_id="CAP-ATOM-A", role="REQUIRED").validate()


class TestCandidate:
    def test_valid_repository_candidate(self) -> None:
        candidate = Candidate(
            candidate_id="cand:acme/obtool",
            name="obtool",
            source_kind=CandidateSourceKind.REPOSITORY,
            source_ref="repo:acme/obtool",
            revision="9cf13ab",
            claims_atoms=("CAP-ATOM-OB-STATE", "CAP-ATOM-CHECKPOINT"),
            claim_verification=VerificationLevel.DISCOVERED,
            discovered_via="github-search:order book replay",
        )
        candidate.validate()

    def test_candidate_without_claim_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="claim"):
            Candidate(
                candidate_id="cand:orphan",
                name="orphan-repo",
                source_kind=CandidateSourceKind.REPOSITORY,
                source_ref="repo:acme/orphan",
                claims_atoms=(),
            ).validate()

    def test_internal_candidate_requires_source_path(self) -> None:
        with pytest.raises(QcaeValidationError, match="internal"):
            Candidate(
                candidate_id="cand:internal-mystery",
                name="mystery",
                source_kind=CandidateSourceKind.INTERNAL_CODE,
                source_ref="",
                claims_atoms=("CAP-ATOM-OB-STATE",),
            ).validate()

    def test_contract_verified_requires_revision(self) -> None:
        with pytest.raises(QcaeValidationError, match="revision"):
            Candidate(
                candidate_id="cand:moving-branch",
                name="moving-branch-candidate",
                source_kind=CandidateSourceKind.REPOSITORY,
                source_ref="repo:acme/obtool",
                revision="",
                claims_atoms=("CAP-ATOM-OB-STATE",),
                claim_verification=VerificationLevel.CONTRACT_VERIFIED,
            ).validate()

    def test_claim_not_silently_upgraded(self) -> None:
        """Verification level is caller-owned evidence, never auto-computed."""
        candidate = Candidate(
            candidate_id="cand:a",
            name="a",
            source_kind=CandidateSourceKind.REPOSITORY,
            source_ref="repo:a/b",
            revision="deadbeef",
            claims_atoms=("CAP-ATOM-X",),
            claim_verification=VerificationLevel.SOURCE_LOCATED,
        )
        candidate.validate()
        assert candidate.claim_verification is VerificationLevel.SOURCE_LOCATED

    def test_multiple_candidates_implement_same_atom(self) -> None:
        """Canon 1.2.12: the atom is the stable comparison object."""
        atom_a = Candidate(
            candidate_id="cand:repo-a",
            name="Repo A component",
            source_kind=CandidateSourceKind.REPOSITORY,
            source_ref="repo:a/comp",
            revision="1111111",
            claims_atoms=("CAP-ATOM-CHANGEPOINT",),
        )
        repo_b = Candidate(
            candidate_id="cand:repo-b",
            name="Repo B library",
            source_kind=CandidateSourceKind.PACKAGE,
            source_ref="pkg:pypi/compb@1.4.0",
            revision="1.4.0",
            claims_atoms=("CAP-ATOM-CHANGEPOINT",),
        )
        paper_c = Candidate(
            candidate_id="cand:paper-c",
            name="Reference implementation",
            source_kind=CandidateSourceKind.PAPER,
            source_ref="paper:arxiv:2401.12345",
            claims_atoms=("CAP-ATOM-CHANGEPOINT",),
        )
        internal_d = Candidate(
            candidate_id="cand:internal-z",
            name="Internal implementation Z",
            source_kind=CandidateSourceKind.INTERNAL_CODE,
            source_ref="quant-lab/src/estimators/changepoint.py",
            claims_atoms=("CAP-ATOM-CHANGEPOINT",),
        )
        for candidate in (atom_a, repo_b, paper_c, internal_d):
            candidate.validate()
        claims = {c.claims_atoms for c in (atom_a, repo_b, paper_c, internal_d)}
        assert claims == {("CAP-ATOM-CHANGEPOINT",)}

    def test_candidate_round_trip(self) -> None:
        candidate = Candidate(
            candidate_id="cand:round-trip",
            name="rt",
            source_kind=CandidateSourceKind.SERVICE,
            source_ref="service:internal/kafka@broker-3",
            claims_atoms=("CAP-ATOM-INGEST",),
            claim_verification=VerificationLevel.RUNTIME_VERIFIED,
            revision="broker-3",
        )
        rebuilt = Candidate.from_dict(candidate.to_dict())
        assert rebuilt == candidate
        assert rebuilt.source_kind is CandidateSourceKind.SERVICE
        assert rebuilt.claim_verification is VerificationLevel.RUNTIME_VERIFIED
