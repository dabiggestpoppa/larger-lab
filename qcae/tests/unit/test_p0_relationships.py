"""P0-C06 — Relationship, EntityRef, EvidenceRef evidence (canon 1.3 + 0.4)."""

from __future__ import annotations

import pytest

from qcae.core.evidence_ref import EvidenceRef
from qcae.core.errors import QcaeValidationError
from qcae.core.relationships.graph import (
    EntityRef,
    EntityType,
    RelationType,
    Relationship,
    make_relationship,
)
from qcae.core.vocabulary import EvidenceClass, VerificationLevel

ET = EntityType
RT = RelationType
VL = VerificationLevel
EC = EvidenceClass

DIGEST_A = "a1b2c3d4e5f6a7b8"


def component_ref(entity_id: str = "comp:orderbook-engine") -> EntityRef:
    return EntityRef(entity_type=ET.COMPONENT, entity_id=entity_id)


def atom_ref(entity_id: str = "CAP-ATOM-OB-STATE") -> EntityRef:
    return EntityRef(entity_type=ET.CAPABILITY_ATOM, entity_id=entity_id)


class TestEntityRef:
    def test_valid_ref(self) -> None:
        component_ref().validate()

    def test_bad_entity_type_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="entity_type"):
            EntityRef(entity_type="COMPONENT", entity_id="comp:x").validate()

    def test_bad_entity_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="entity_id"):
            EntityRef(entity_type=ET.COMPONENT, entity_id="has spaces").validate()

    def test_round_trip(self) -> None:
        ref = atom_ref()
        rebuilt = EntityRef.from_dict(ref.to_dict())
        assert rebuilt == ref
        assert rebuilt.entity_type is ET.CAPABILITY_ATOM


class TestRelationship:
    def test_valid_implements_edge(self) -> None:
        make_relationship(
            source=component_ref(),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            verification=VL.CODE_VERIFIED,
            source_revision="9cf13ab",
            asserted_by="worker:repository-intelligence",
            asserted_at="2026-09-12T00:00:00Z",
        )

    def test_entity_separate_from_relationship(self) -> None:
        """Canon 1.3.2: entities stored separately; edge references them by ID."""
        edge = make_relationship(
            source=component_ref("comp:external-tool"),
            relation=RT.IMPLEMENTS,
            target=atom_ref("CAP-ATOM-PARSER"),
        )
        assert edge.source.entity_id == "comp:external-tool"
        assert edge.target.entity_id == "CAP-ATOM-PARSER"
        # The edge record carries no entity payload.
        assert not hasattr(edge.source, "name")
        assert not hasattr(edge.target, "description")

    def test_relationship_typing_vocabulary_frozen(self) -> None:
        required = {
            "requested_by", "normalized_as", "composed_of", "implements",
            "partially_implements", "contained_in", "exposed_through", "depends_on",
            "optional_dependency_on", "conflicts_with", "substitutes_for", "extends",
            "supersedes", "wraps", "vendors", "forked_from", "extracted_from",
            "derived_from", "specified_by", "described_by", "validated_by",
            "tested_by", "benchmarked_by", "observed_in", "requires_data",
            "produces_data", "compatible_with", "incompatible_with", "integrated_as",
            "approved_by", "rejected_by", "triggered_revalidation_of",
        }
        assert {r.value for r in RT} == required

    def test_arbitrary_prose_type_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="RelationType"):
            make_relationship(
                source=component_ref(),
                relation="is kind of like",
                target=atom_ref(),
            )

    def test_reversed_implements_edge_rejected(self) -> None:
        """Direction matters (canon 1.3.5): an atom does not implement a component."""
        with pytest.raises(QcaeValidationError, match="source must be"):
            make_relationship(
                source=atom_ref(),
                relation=RT.IMPLEMENTS,
                target=component_ref(),
            )

    def test_implements_target_must_be_capability(self) -> None:
        with pytest.raises(QcaeValidationError, match="target must be"):
            make_relationship(
                source=component_ref(),
                relation=RT.IMPLEMENTS,
                target=EntityRef(entity_type=ET.REPOSITORY, entity_id="repo:a/b"),
            )

    def test_composed_of_direction_enforced(self) -> None:
        with pytest.raises(QcaeValidationError, match="source must be"):
            make_relationship(
                source=atom_ref(),
                relation=RT.COMPOSED_OF,
                target=atom_ref("CAP-ATOM-OTHER"),
            )

    def test_contained_in_requires_repository_target(self) -> None:
        with pytest.raises(QcaeValidationError, match="target must be"):
            make_relationship(
                source=component_ref(),
                relation=RT.CONTAINED_IN,
                target=atom_ref(),
            )

    def test_supersedes_requires_same_entity_type(self) -> None:
        with pytest.raises(QcaeValidationError, match="same entity type"):
            make_relationship(
                source=EntityRef(entity_type=ET.CAPABILITY_ATOM, entity_id="CAP-ATOM-A"),
                relation=RT.SUPERSEDES,
                target=EntityRef(entity_type=ET.PACKAGE, entity_id="pkg:x/y@1.0"),
            )

    def test_normalizes_as_direction_enforced(self) -> None:
        with pytest.raises(QcaeValidationError, match="source must be a NEED"):
            make_relationship(
                source=atom_ref(),
                relation=RT.NORMALIZED_AS,
                target=EntityRef(
                    entity_type=ET.CAPABILITY_CONTRACT, entity_id="CAP-REPLAY-001"
                ),
            )

    def test_claimed_vs_verified_distinct(self) -> None:
        """Canon 1.3.6: CLAIMED_IMPLEMENTATION != CODE_VERIFIED_IMPLEMENTATION."""
        claimed = make_relationship(
            source=component_ref("comp:x"),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            verification=VL.DISCOVERED,
        )
        verified = make_relationship(
            source=component_ref("comp:x"),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            verification=VL.CODE_VERIFIED,
        )
        assert claimed.verification is not verified.verification
        assert claimed.digest() != verified.digest()

    def test_revision_scoped_edge(self) -> None:
        """Canon 1.3.12: same entities, different revisions, opposite facts."""
        edge_a = make_relationship(
            source=component_ref(),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            source_revision="commit-A",
        )
        edge_b = make_relationship(
            source=component_ref(),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            source_revision="commit-B",
            verification=VL.SOURCE_LOCATED,
        )
        assert edge_a.source_revision != edge_b.source_revision
        assert edge_a.digest() != edge_b.digest()

    def test_evidence_digest_linkage(self) -> None:
        edge = make_relationship(
            source=component_ref(),
            relation=RT.IMPLEMENTS,
            target=atom_ref(),
            evidence_digests=(DIGEST_A, "b2c3d4e5f6a7b8c9"),
        )
        assert len(edge.evidence_digests) == 2

    def test_bad_evidence_digest_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence_digests"):
            make_relationship(
                source=component_ref(),
                relation=RT.IMPLEMENTS,
                target=atom_ref(),
                evidence_digests=("short",),
            )

    def test_relationship_round_trip(self) -> None:
        edge = make_relationship(
            source=component_ref("comp:full-edge"),
            relation=RT.PARTIALLY_IMPLEMENTS,
            target=atom_ref("CAP-ATOM-PARTIAL"),
            verification=VL.CONTRACT_VERIFIED,
            source_revision="3fa8c2d",
            evidence_digests=(DIGEST_A,),
            asserted_by="worker:contract-test",
            asserted_at="2026-09-12T12:00:00Z",
        )
        rebuilt = Relationship.from_dict(edge.to_dict())
        assert rebuilt == edge
        assert rebuilt.relation is RT.PARTIALLY_IMPLEMENTS
        assert rebuilt.verification is VL.CONTRACT_VERIFIED
        assert isinstance(rebuilt.source, EntityRef)


class TestEvidenceRef:
    def test_valid_source_evidence_ref(self) -> None:
        EvidenceRef(
            artifact_digest=DIGEST_A * 4,
            evidence_class=EC.E2_SOURCE,
            subject_id="CAP-ATOM-OB-STATE",
            revision="9cf13ab",
            locator="file://sandbox/candidate/src/book.py",
            collected_at="2026-09-12T00:00:00Z",
            collected_by="worker:sandbox-build",
        ).validate()

    def test_malformed_digest_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="artifact_digest"):
            EvidenceRef(
                artifact_digest="NOT-A-HASH",
                evidence_class=EC.E2_SOURCE,
                subject_id="CAP-ATOM-OB-STATE",
            ).validate()

    def test_short_digest_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="artifact_digest"):
            EvidenceRef(
                artifact_digest="abc123",
                evidence_class=EC.E2_SOURCE,
                subject_id="CAP-ATOM-OB-STATE",
            ).validate()

    def test_evidence_ref_revision_provenance_shape(self) -> None:
        """Canon 0.4.7: evidence stores reviewed revision + collector provenance."""
        ref = EvidenceRef(
            artifact_digest="f" * 64,
            evidence_class=EC.E5_INDEPENDENT_CONTRACT,
            subject_id="cand:acme/obtool",
            revision="v2.1.0",
            collected_at="2026-09-12T00:00:00Z",
            collected_by="worker:contract-test",
        )
        ref.validate()
        assert ref.revision == "v2.1.0"
        assert ref.collected_by == "worker:contract-test"

    def test_bad_evidence_class_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence_class"):
            EvidenceRef(
                artifact_digest=DIGEST_A,
                evidence_class="E2_SOURCE",
                subject_id="CAP-ATOM-OB-STATE",
            ).validate()

    def test_bad_subject_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="subject_id"):
            EvidenceRef(
                artifact_digest=DIGEST_A,
                evidence_class=EC.E2_SOURCE,
                subject_id="",
            ).validate()

    def test_round_trip(self) -> None:
        ref = EvidenceRef(
            artifact_digest="e" * 64,
            evidence_class=EC.E7_DOMAIN_VALIDATION,
            subject_id="CAP-STRAT-001",
            revision="paper-v3",
        )
        rebuilt = EvidenceRef.from_dict(ref.to_dict())
        assert rebuilt == ref
        assert rebuilt.evidence_class is EC.E7_DOMAIN_VALIDATION
