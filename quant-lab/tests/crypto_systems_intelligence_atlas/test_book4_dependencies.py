"""Book 4 direct dependency, path, and provenance tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_test_support import NOW, descriptor, kernel, path, record
from crypto_systems_intelligence_atlas.claims import ClaimState
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.dependency import (
    DependencyBook,
    DependencyStrengthState,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_paths import DependencyPathBook
from crypto_systems_intelligence_atlas.dependency_provenance import Book4Provenance, Book4ProvenanceError
from crypto_systems_intelligence_atlas.relationships import EdgeType


def test_dependency_book_validates_book2_provenance() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    assert book.add(record("dependency-1")) is not None
    with pytest.raises(ValueError, match="unique"):
        book.add(record("dependency-1"))


def test_dependency_book_rejects_missing_claim_ref() -> None:
    claims, evidence, _ = kernel()
    item = record("dependency-1")
    detached = item.model_copy(update={"book2_claim_refs": ("missing-claim",)})
    with pytest.raises(Book4ProvenanceError, match="unknown claim"):
        DependencyBook(Book4Provenance(claims, evidence)).add(detached)


def test_strength_and_runtime_are_independent_axes() -> None:
    primary = record("dependency-primary", runtime_scope=RuntimeScope.SOFT_RUNTIME)
    required_build = record(
        "dependency-build",
        relation=EdgeType.BUILT_WITH,
        runtime_scope=RuntimeScope.BUILD_TIME,
        strength=DependencyStrengthState.REQUIRED,
    )
    assert primary.strength_descriptor.state is DependencyStrengthState.PRIMARY
    assert primary.runtime_scope is RuntimeScope.SOFT_RUNTIME
    assert required_build.runtime_scope is RuntimeScope.BUILD_TIME


def test_direct_dependency_never_silently_becomes_transitive() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    book.add(record("a-b"))
    book.add(record("b-c"))
    assert {item.dependency_id for item in book.all_records()} == {"a-b", "b-c"}
    assert all(item.dependency_id != "a-c" for item in book.all_records())


def test_dependency_path_preserves_a_b_c() -> None:
    _, _, provenance = kernel()
    book = DependencyPathBook(provenance)
    item = book.add(path())
    assert item.ordered_nodes == ("A", "B", "C")
    assert [(rel.subject_ref, rel.object_ref) for rel in item.ordered_relations] == [
        ("A", "B"),
        ("B", "C"),
    ]
    derived = book.derive_transitive("path-abc")
    assert derived.ordered_path == ("A", "B", "C")
    assert derived.authoritative is False


def test_dependency_path_rejects_discontinuity() -> None:
    item = path()
    with pytest.raises(ValidationError, match="relation does not"):
        item.model_copy(
            update={
                "ordered_relations": (
                    item.ordered_relations[0],
                    item.ordered_relations[0],
                )
            }
        ).model_validate(
            {
                **item.model_dump(),
                "ordered_relations": (
                    item.ordered_relations[0],
                    item.ordered_relations[0],
                ),
            }
        )


@pytest.mark.parametrize(
    "target",
    [
        ClaimState.REJECTED,
        ClaimState.STALE,
        ClaimState.CONTESTED,
        ClaimState.UNRESOLVED,
    ],
)
def test_provenance_rejects_non_promotable_book2_states(target: ClaimState) -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import service_kernel

    service = service_kernel()
    evidence_ref = service.require("book4-transition").evidence_refs[0]
    engine = ClaimStateEngine(service)
    if target is ClaimState.UNRESOLVED:
        service.claim_store.add_initial(
            service.require("book4-transition").model_copy(
                update={"claim_id": "book4-declared", "claim_state": ClaimState.DECLARED}
            )
        )
        engine.transition(
            "book4-declared",
            target,
            triggering_evidence_refs=(evidence_ref,),
            transitioned_at=NOW,
        )
        claim_id = "book4-declared"
    else:
        engine.transition(
            "book4-transition",
            target,
            triggering_evidence_refs=(evidence_ref,),
            transitioned_at=NOW,
        )
        claim_id = "book4-transition"
    provenance = Book4Provenance(service.claim_store, service.evidence_store)
    with pytest.raises(Book4ProvenanceError, match="graph-promotable"):
        provenance.resolve_claim(claim_id)


def test_provenance_rejects_superseded_claim() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import make_claim, service_kernel

    service = service_kernel()
    evidence_store = service.evidence_store
    replacement_evidence = evidence_store.capture(
        source_id="csia:source:book4-offline",
        retrieved_at=NOW,
        content=b"replacement",
        content_locator="fixture://book4/replacement",
        raw_snapshot_ref="snapshot://book4/replacement",
        extractor_version="test",
        parser_version="test",
        evidence_tier="FIRST_PARTY_DOC",
    ).evidence_id
    service.add_observed(make_claim("book4-replacement", replacement_evidence))
    engine = ClaimStateEngine(service)
    engine.transition(
        "book4-replacement",
        ClaimState.SUPERSEDED,
        triggering_evidence_refs=(replacement_evidence,),
        transitioned_at=NOW,
        replacement_claim_id="book4-transition",
        supersession_reason="fixture supersession",
    )
    provenance = Book4Provenance(service.claim_store, evidence_store)
    with pytest.raises(Book4ProvenanceError, match="graph-promotable"):
        provenance.resolve_claim("book4-replacement")


def test_provenance_rejects_detached_evidence() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import make_claim
    from crypto_systems_intelligence_atlas.claims import ClaimStore
    from crypto_systems_intelligence_atlas.evidence import EvidenceStore
    from crypto_systems_intelligence_atlas.sources import SourceRegistry

    claims = ClaimStore()
    claims.add_initial(make_claim("detached", "missing-evidence"))
    provenance = Book4Provenance(claims, EvidenceStore(SourceRegistry()))
    with pytest.raises(Book4ProvenanceError, match="detached evidence"):
        provenance.resolve_claim("detached")


def test_provenance_rejects_invented_book2_state() -> None:
    with pytest.raises(ValidationError):
        descriptor().model_copy(update={"state": "VERIFIED"}).model_validate(
            {
                **descriptor().model_dump(),
                "state": "VERIFIED",
            }
        )
