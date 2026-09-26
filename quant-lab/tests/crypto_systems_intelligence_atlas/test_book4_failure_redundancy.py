"""Book 4 failure-domain and redundancy stress tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_test_support import (
    add_pair_independence_claim,
    failure_domain,
    kernel,
    redundancy,
)
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    FailureDomainClassification,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState


@pytest.mark.parametrize(
    ("case", "left_kwargs", "right_kwargs", "positive", "expected"),
    [
        ("same oracle network/different feeds", {"provider": "oracle-a", "evidence_ref": "oracle-domain"}, {"provider": "oracle-a", "evidence_ref": "oracle-domain"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("same feed/different deployments", {"provider": "feed-a", "evidence_ref": "deployment-a"}, {"provider": "feed-a", "evidence_ref": "deployment-b"}, (), FailureDomainClassification.PARTIAL_SHARED_DOMAIN),
        ("same verifier set/multiple bridges", {"provider": "verifier-a", "evidence_ref": "set-a"}, {"provider": "verifier-a", "evidence_ref": "set-a"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("same RPC brand/separate backend", {"provider": "rpc-brand", "evidence_ref": "backend-a"}, {"provider": "rpc-brand", "evidence_ref": "backend-b"}, (), FailureDomainClassification.PARTIAL_SHARED_DOMAIN),
        ("different brands/same cloud", {"provider": "rpc-a", "evidence_ref": "cloud-a"}, {"provider": "rpc-b", "evidence_ref": "cloud-a"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared sequencer operator", {"operator": "sequencer-op", "evidence_ref": "sequencer-op"}, {"operator": "sequencer-op", "evidence_ref": "sequencer-op"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared DA", {"provider": "da-a", "evidence_ref": "da-layer"}, {"provider": "da-b", "evidence_ref": "da-layer"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared validator set", {"provider": "validator-a", "evidence_ref": "validator-set"}, {"provider": "validator-b", "evidence_ref": "validator-set"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared governance multisig", {"provider": "system-a", "evidence_ref": "multisig"}, {"provider": "system-b", "evidence_ref": "multisig"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared custody", {"provider": "system-a", "evidence_ref": "custodian"}, {"provider": "system-b", "evidence_ref": "custodian"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared relayer", {"provider": "system-a", "evidence_ref": "relayer"}, {"provider": "system-b", "evidence_ref": "relayer"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("shared indexer", {"provider": "app-a", "evidence_ref": "indexer"}, {"provider": "app-b", "evidence_ref": "indexer"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("common upstream API", {"provider": "service-a", "evidence_ref": "upstream-api"}, {"provider": "service-b", "evidence_ref": "upstream-api"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("fallbacks sharing upstream", {"provider": "fallback-a", "evidence_ref": "fallback-upstream"}, {"provider": "fallback-b", "evidence_ref": "fallback-upstream"}, (), FailureDomainClassification.SHARED_FAILURE_DOMAIN),
        ("positive independent backends", {"provider": "a", "evidence_ref": "a"}, {"provider": "b", "evidence_ref": "b"}, ("book4-independence-review",), FailureDomainClassification.INDEPENDENT),
        ("no inference from different brands", {"provider": "a", "evidence_ref": "a"}, {"provider": "b", "evidence_ref": "b"}, (), FailureDomainClassification.UNKNOWN),
    ],
)
def test_failure_domain_scenarios(
    case: str,
    left_kwargs: dict[str, object],
    right_kwargs: dict[str, object],
    positive: tuple[str, ...],
    expected: FailureDomainClassification,
) -> None:
    claims, evidence, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain(f"{case}:left", **left_kwargs))
    right = book.add(failure_domain(f"{case}:right", **right_kwargs))
    if positive:
        positive = (
            add_pair_independence_claim(
                claims,
                evidence,
                left_system=left.affected_system_refs[0],
                right_system=right.affected_system_refs[0],
            ),
        )
    bindings: tuple[IndependenceClaimBinding, ...] = ()
    if positive:
        bindings = (
            IndependenceClaimBinding(
                claim_ref=positive[0],
                left_domain_ref=left.domain_id,
                right_domain_ref=right.domain_id,
                left_system_ref=left.affected_system_refs[0],
                right_system_ref=right.affected_system_refs[0],
                correlation_scope=left.correlation_scope,
            ),
        )
    assert (
        book.classify(
            left,
            right,
            positive_independence_claim_refs=positive,
            independence_bindings=bindings,
        ).classification
        is expected
    )


def test_two_providers_without_shared_evidence_remain_unknown() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain("left", provider="a", evidence_ref="a"))
    right = book.add(failure_domain("right", provider="b", evidence_ref="b"))
    assert book.classify(left, right).classification is FailureDomainClassification.UNKNOWN


def test_redundancy_book_validates_canonical_claims() -> None:
    from crypto_systems_intelligence_atlas.failure_domains import FailureDomainBook

    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    assert book.add(redundancy("red-1")) is not None
    with pytest.raises(ValueError, match="unique"):
        book.add(redundancy("red-1"))


def test_independent_redundancy_requires_positive_evidence() -> None:
    with pytest.raises(ValidationError, match="positive evidence"):
        redundancy("red-independent", state=RedundancyState.INDEPENDENT_REDUNDANCY)


def test_correlated_redundancy_names_shared_upstream() -> None:
    item = redundancy(
        "red-correlated",
        state=RedundancyState.CORRELATED_REDUNDANCY,
        shared_upstreams=("common-api",),
    )
    assert item.state is RedundancyState.CORRELATED_REDUNDANCY


def test_independent_redundancy_rejects_shared_upstream() -> None:
    with pytest.raises(ValidationError, match="correlated"):
        redundancy(
            "red-invalid",
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            shared_upstreams=("common-api",),
            positive=("positive-review",),
        )
