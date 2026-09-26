"""Book 4 Hardening R3 — multi-provider independence completeness.

Demonstrated defects under repair:

1. ``RedundancyBook.add`` enforced independence coverage over *consecutive*
   provider pairs only, so a 3-provider A/B/C assessment needed only A-B and
   B-C; an unverified A-C pair could still ride to INDEPENDENT_REDUNDANCY
   (PAIRWISE_TRANSITIVITY_FALSE).
2. ``RedundancyAssessment._binding_matches`` bound every binding against
   ``provider_refs[0]``/``provider_refs[1]`` only, so a legitimate B-C pair
   binding in a 3-provider assessment could not be represented at all
   (FIRST_PAIR_BINDING_ASSUMPTION).

Set-level independence requires complete unordered pairwise evidence. No
transitivity: A⊥B and B⊥C does NOT imply A⊥C.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book4_test_support import (
    add_pair_independence_claim,
    kernel,
    redundancy,
)
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState

FUNCTION = "liquidation execution"
SUBJECT = "fixture:liquidation-contract"


def _book() -> tuple[RedundancyBook, object, object]:
    claims, evidence, provenance = kernel()
    return RedundancyBook(provenance, FailureDomainBook(provenance)), claims, evidence


def _pair_claim(
    claims: object,
    evidence: object,
    left: str,
    right: str,
) -> str:
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


def _provider_assessment(
    redundancy_id: str,
    providers: tuple[str, ...],
    *,
    state: RedundancyState = RedundancyState.INDEPENDENT_REDUNDANCY,
    claims: object | None = None,
    evidence: object | None = None,
    pair_coverage: tuple[tuple[str, str], ...] | None = None,
    claim_ids: tuple[str, ...] | None = None,
    bindings: tuple[IndependenceClaimBinding, ...] | None = None,
) -> object:
    """Build a multi-provider assessment over the given providers.

    ``pair_coverage`` selects which unordered pairs get evidence; ``None``
    means the complete coverage. ``claim_ids``/``bindings`` allow fully manual
    claim/binding control for negative cases (duplicates, external pairs).
    """
    complete = [
        (left, right)
        for i, left in enumerate(providers)
        for right in providers[i + 1 :]
    ]
    if pair_coverage is None:
        pair_coverage = tuple(complete)
    if claims is not None and evidence is not None and bindings is None:
        claim_ids = tuple(
            _pair_claim(claims, evidence, left, right) for left, right in pair_coverage
        )
        bindings = tuple(
            _binding(claim_id, left, right)
            for claim_id, (left, right) in zip(claim_ids, pair_coverage)
        )
    claim_refs = claim_ids if claim_ids is not None else ()
    return redundancy(
        redundancy_id,
        state=state,
        positive=claim_refs,
    ).model_copy(
        update={
            "provider_refs": providers,
            "independence_bindings": bindings if bindings is not None else (),
        }
    )


# --------------------------------------------------------------------------
# R3-A: pair-completeness matrix (decision point: RedundancyBook.add)
# --------------------------------------------------------------------------


def test_r3_a1_three_providers_missing_non_adjacent_pair_is_rejected() -> None:
    """A-B + B-C present but A-C missing must NOT reach INDEPENDENT_REDUNDANCY."""
    book, claims, evidence = _book()
    assessment = _provider_assessment(
        "red-r3-a1",
        ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c"),
        claims=claims,
        evidence=evidence,
        pair_coverage=(("fixture:provider-a", "fixture:provider-b"), ("fixture:provider-b", "fixture:provider-c")),
    )
    with pytest.raises(ValueError, match="A-C|incomplete|missing"):
        book.add(assessment)


def test_r3_a2_three_providers_complete_pairwise_evidence_passes() -> None:
    book, claims, evidence = _book()
    assessment = _provider_assessment(
        "red-r3-a2",
        ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c"),
        claims=claims,
        evidence=evidence,
    )
    stored = book.add(assessment)
    assert stored.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_r3_a3_provider_order_invariance() -> None:
    """Reordering providers must not change independence truth."""
    book, claims, evidence = _book()
    reordered = _provider_assessment(
        "red-r3-a3",
        ("fixture:provider-c", "fixture:provider-a", "fixture:provider-b"),
        claims=claims,
        evidence=evidence,
    )
    stored = book.add(reordered)
    assert stored.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_r3_a4_duplicate_pair_evidence_cannot_substitute_for_missing_pair() -> None:
    """Two A-B claims plus A-C, with B-C missing, must be rejected."""
    book, claims, evidence = _book()
    providers = ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c")
    # Two DISTINCT canonical claims scoped to the same A-B pair.
    ab_1 = add_pair_independence_claim(
        claims,
        evidence,
        left_system=providers[0],
        right_system=providers[1],
        claim_id="book4-independence-a-b-first",
    )
    ab_2 = add_pair_independence_claim(
        claims,
        evidence,
        left_system=providers[0],
        right_system=providers[1],
        claim_id="book4-independence-a-b-duplicate",
    )
    ac = _pair_claim(claims, evidence, providers[0], providers[2])
    bindings = (
        _binding(ab_1, providers[0], providers[1]),
        _binding(ab_2, providers[0], providers[1]),
        _binding(ac, providers[0], providers[2]),
    )
    assessment = _provider_assessment(
        "red-r3-a4",
        providers,
        claim_ids=(ab_1, ab_2, ac),
        bindings=bindings,
    )
    with pytest.raises(ValueError, match="duplicate|more than once|incomplete|missing|B-C"):
        book.add(assessment)


def test_r3_a5_external_provider_binding_is_rejected() -> None:
    """A binding naming provider D outside the assessed set must be rejected."""
    book, claims, evidence = _book()
    providers = ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c")
    # Complete in-set coverage plus an out-of-set A-D binding.
    in_set = [
        (providers[0], providers[1]),
        (providers[0], providers[2]),
        (providers[1], providers[2]),
    ]
    claim_ids = tuple(_pair_claim(claims, evidence, left, right) for left, right in in_set)
    bindings = tuple(
        _binding(claim_id, left, right) for claim_id, (left, right) in zip(claim_ids, in_set)
    )
    external = _pair_claim(claims, evidence, providers[0], "fixture:provider-d")
    assessment = _provider_assessment(
        "red-r3-a5",
        providers,
        claim_ids=(*claim_ids, external),
        bindings=(*bindings, _binding(external, providers[0], "fixture:provider-d")),
    )
    with pytest.raises(ValueError, match="outside|not scoped|provider-d"):
        book.add(assessment)


def test_r3_a6_self_pair_binding_is_rejected() -> None:
    book, claims, evidence = _book()
    providers = ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c")
    complete = [
        (providers[0], providers[1]),
        (providers[0], providers[2]),
        (providers[1], providers[2]),
    ]
    claim_ids = tuple(_pair_claim(claims, evidence, left, right) for left, right in complete)
    bindings = tuple(
        _binding(claim_id, left, right) for claim_id, (left, right) in zip(claim_ids, complete)
    )
    self_claim = _pair_claim(claims, evidence, providers[0], providers[0])
    assessment = _provider_assessment(
        "red-r3-a6",
        providers,
        claim_ids=(*claim_ids, self_claim),
        bindings=(*bindings, _binding(self_claim, providers[0], providers[0])),
    )
    with pytest.raises(ValueError, match="self|same provider|distinct|provider-a"):
        book.add(assessment)


def test_r3_a7_two_provider_behavior_is_preserved() -> None:
    book, claims, evidence = _book()
    assessment = _provider_assessment(
        "red-r3-a7",
        ("fixture:provider-a", "fixture:provider-b"),
        claims=claims,
        evidence=evidence,
    )
    stored = book.add(assessment)
    assert stored.state is RedundancyState.INDEPENDENT_REDUNDANCY


@pytest.mark.parametrize("missing", [0, 1, 2, 3, 4, 5])
def test_r3_a8_four_providers_with_any_missing_pair_is_rejected(missing: int) -> None:
    """All six unordered pairs required; dropping any one must reject."""
    book, claims, evidence = _book()
    providers = (
        "fixture:provider-a",
        "fixture:provider-b",
        "fixture:provider-c",
        "fixture:provider-d",
    )
    complete = [
        (providers[i], providers[j])
        for i in range(len(providers))
        for j in range(i + 1, len(providers))
    ]
    kept = [pair for index, pair in enumerate(complete) if index != missing]
    claim_ids = tuple(_pair_claim(claims, evidence, left, right) for left, right in kept)
    bindings = tuple(
        _binding(claim_id, left, right) for claim_id, (left, right) in zip(claim_ids, kept)
    )
    assessment = _provider_assessment(
        f"red-r3-a8-{missing}",
        providers,
        claim_ids=claim_ids,
        bindings=bindings,
    )
    with pytest.raises(ValueError, match="incomplete|missing|no pair-scoped"):
        book.add(assessment)


def test_r3_a9_four_providers_complete_six_pair_coverage_passes() -> None:
    book, claims, evidence = _book()
    providers = (
        "fixture:provider-a",
        "fixture:provider-b",
        "fixture:provider-c",
        "fixture:provider-d",
    )
    assessment = _provider_assessment("red-r3-a9", providers, claims=claims, evidence=evidence)
    stored = book.add(assessment)
    assert stored.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_r3_no_transitivity_between_pair_claims() -> None:
    """A⊥B and B⊥C must not imply A⊥C even when every present pair is canonical."""
    book, claims, evidence = _book()
    assessment = _provider_assessment(
        "red-r3-transitivity",
        ("fixture:provider-a", "fixture:provider-b", "fixture:provider-c"),
        claims=claims,
        evidence=evidence,
        pair_coverage=(("fixture:provider-a", "fixture:provider-b"), ("fixture:provider-b", "fixture:provider-c")),
    )
    with pytest.raises(ValueError):
        book.add(assessment)


def test_r3_claims_without_bindings_do_not_silently_upgrade_state() -> None:
    """UNKNOWN/CORRELATED records keep existing doctrine: no silent upgrade."""
    book, _, _ = _book()
    unknown = redundancy("red-r3-unknown", state=RedundancyState.UNKNOWN)
    stored = book.add(unknown)
    assert stored.state is RedundancyState.UNKNOWN


def test_r3_correlated_with_positive_refs_retains_doctrine() -> None:
    """CORRELATED + declared positive refs keeps doctrine (no silent upgrade)."""
    book, _, _ = _book()
    correlated = redundancy(
        "red-r3-correlated",
        state=RedundancyState.CORRELATED_REDUNDANCY,
        shared_upstreams=("common-api",),
        positive=("book4-independence-review",),
    )
    stored = book.add(correlated)
    assert stored.state is RedundancyState.CORRELATED_REDUNDANCY
