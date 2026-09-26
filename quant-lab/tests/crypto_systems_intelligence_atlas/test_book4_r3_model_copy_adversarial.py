"""Book 4 Hardening R3 — decision-point (model_copy) adversarial probes.

The R2 audit proved pydantic ``model_copy(update=...)`` skips every model
validator. Decision-point re-verification in ``RedundancyBook.add`` is
therefore authoritative; these probes attack the complete-pair seal through
that exact bypass. Constructor validation remains defense in depth.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book4_test_support import (
    add_pair_independence_claim,
    kernel,
    redundancy,
)
from crypto_systems_intelligence_atlas.dependency_provenance import Book4ProvenanceError
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState

FUNCTION = "liquidation execution"
SUBJECT = "fixture:liquidation-contract"
PROVIDERS = (
    "fixture:provider-a",
    "fixture:provider-b",
    "fixture:provider-c",
)


def _fixture() -> tuple[RedundancyBook, object, object]:
    claims, evidence, provenance = kernel()
    return RedundancyBook(provenance, FailureDomainBook(provenance)), claims, evidence


def _pair_claim(claims: object, evidence: object, left: str, right: str) -> str:
    return add_pair_independence_claim(
        claims, evidence, left_system=left, right_system=right
    )


def _binding(claim_ref: str, left: str, right: str) -> IndependenceClaimBinding:
    return IndependenceClaimBinding(
        claim_ref=claim_ref,
        left_domain_ref=left,
        right_domain_ref=right,
        left_system_ref=SUBJECT,
        right_system_ref=SUBJECT,
        correlation_scope=FUNCTION,
    )


def _complete_record(
    redundancy_id: str,
    providers: tuple[str, ...],
    claims: object,
    evidence: object,
) -> object:
    """A record with complete unordered pair coverage over ``providers``."""
    pairs = [
        (providers[i], providers[j])
        for i in range(len(providers))
        for j in range(i + 1, len(providers))
    ]
    claim_ids = tuple(_pair_claim(claims, evidence, l, r) for l, r in pairs)
    bindings = tuple(
        _binding(claim_id, left, right)
        for claim_id, (left, right) in zip(claim_ids, pairs)
    )
    return redundancy(redundancy_id, state=RedundancyState.INDEPENDENT_REDUNDANCY, positive=claim_ids).model_copy(
        update={"provider_refs": providers, "independence_bindings": bindings}
    )


def test_r3_b1_model_copy_stripping_pairs_is_refused_at_add() -> None:
    """Complete A/B/C record, then strip to consecutive pairs only."""
    book, claims, evidence = _fixture()
    assessment = _complete_record("r3-b1", PROVIDERS, claims, evidence)
    book.add(assessment)  # complete record is accepted

    stripped = assessment.model_copy(
        update={
            "independence_bindings": (
                _binding(
                    "book4-independence-fixture:provider-a-fixture:provider-b",
                    PROVIDERS[0],
                    PROVIDERS[1],
                ),
                _binding(
                    "book4-independence-fixture:provider-a-fixture:provider-c",
                    PROVIDERS[0],
                    PROVIDERS[2],
                ),
            ),
            "positive_independence_claim_refs": (
                "book4-independence-fixture:provider-a-fixture:provider-b",
                "book4-independence-fixture:provider-a-fixture:provider-c",
            ),
            "book2_claim_refs": (
                "book4-claim-current",
                "book4-independence-fixture:provider-a-fixture:provider-b",
                "book4-independence-fixture:provider-a-fixture:provider-c",
            ),
        }
    ).model_copy(update={"redundancy_id": "r3-b1-stripped"})
    with pytest.raises(Book4ProvenanceError, match="incomplete"):
        book.add(stripped)


def test_r3_b2_model_copy_provider_expansion_without_bindings_is_refused() -> None:
    """Expand (A, B) to (A, B, C) via model_copy; the new pairs are unbound."""
    book, claims, evidence = _fixture()
    pairs = [(PROVIDERS[0], PROVIDERS[1])]
    claim_ids = tuple(_pair_claim(claims, evidence, l, r) for l, r in pairs)
    bindings = tuple(
        _binding(claim_id, left, right) for claim_id, (left, right) in zip(claim_ids, pairs)
    )
    two_provider = redundancy(
        "r3-b2",
        state=RedundancyState.INDEPENDENT_REDUNDANCY,
        positive=claim_ids,
    ).model_copy(
        update={"provider_refs": (PROVIDERS[0], PROVIDERS[1]), "independence_bindings": bindings}
    )
    book.add(two_provider)

    expanded = two_provider.model_copy(
        update={"provider_refs": PROVIDERS, "redundancy_id": "r3-b2-expanded"}
    )
    with pytest.raises(Book4ProvenanceError, match="incomplete"):
        book.add(expanded)


def test_r3_b3_model_copy_reorder_with_complete_coverage_passes() -> None:
    """Reordering provider_refs with still-complete normalized coverage passes."""
    book, claims, evidence = _fixture()
    assessment = _complete_record("r3-b3", PROVIDERS, claims, evidence)
    book.add(assessment)

    reordered = assessment.model_copy(
        update={
            "provider_refs": (PROVIDERS[2], PROVIDERS[0], PROVIDERS[1]),
            "redundancy_id": "r3-b3-reordered",
        }
    )
    stored = book.add(reordered)
    assert stored.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_r3_b4_raw_dict_binding_injected_via_model_copy_fails_closed() -> None:
    """A raw dict binding smuggled through model_copy must fail closed (no
    AttributeError, no acceptance)."""
    book, claims, evidence = _fixture()
    assessment = _complete_record("r3-b4", PROVIDERS, claims, evidence)
    book.add(assessment)

    hostile = assessment.model_copy(
        update={
            "independence_bindings": (
                {
                    "claim_ref": "book4-independence-fixture:provider-a-fixture:provider-b",
                    "left_domain_ref": PROVIDERS[0],
                    "right_domain_ref": PROVIDERS[1],
                    "left_system_ref": SUBJECT,
                    "right_system_ref": SUBJECT,
                    "correlation_scope": FUNCTION,
                },
            ),
            "redundancy_id": "r3-b4-hostile",
        }
    )
    with pytest.raises(Book4ProvenanceError):
        book.add(hostile)
