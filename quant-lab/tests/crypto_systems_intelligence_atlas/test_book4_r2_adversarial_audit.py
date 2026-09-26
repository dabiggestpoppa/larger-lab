"""Adversarial audit of the Book 4 R2 seals.

Each test is an explicit bypass attempt against one seal.  Attacks that
exploit constructor-only validation (pydantic ``model_copy`` skips every
model validator) must be refused at the decision points: the classification
gates and the book ``add`` methods.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book4_r1_support import NOW
from crypto_systems_intelligence_atlas.book4_r2_support import (
    GENERIC_PLACEHOLDER,
    R2_FACT_CONSUMER,
    R2_FACT_FUNCTION,
    R2_FACT_PROVIDER,
    R2_FACT_SCOPE,
    context_bindings,
    fact_claim_for,
    kernel,
    mechanism_claim,
    provider_refs_for,
    r2_failure_domain,
    r2_redundancy,
    redundancy_independence_binding,
    redundancy_independence_claim,
    snapshot_ref,
)
from crypto_systems_intelligence_atlas.dependency import (
    FallbackState,
    HardRuntimeEvidence,
    HardRuntimeFact,
    HardRuntimeFactBinding,
    HardRuntimeGate,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_provenance import Book4ProvenanceError
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    FailureDomainClassification,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState

CONTEXT = {
    "consumer": R2_FACT_CONSUMER,
    "provider": R2_FACT_PROVIDER,
    "function": R2_FACT_FUNCTION,
    "scope": R2_FACT_SCOPE,
}


def clean_evidence() -> HardRuntimeEvidence:
    bindings = context_bindings(**CONTEXT)
    claim_refs = tuple(
        sorted({ref for binding in bindings for ref in binding.claim_refs})
    )
    return HardRuntimeEvidence(
        consumer_ref=CONTEXT["consumer"],
        provider_ref=CONTEXT["provider"],
        function=CONTEXT["function"],
        scope=CONTEXT["scope"],
        deployed_configuration_evidenced=True,
        runtime_necessity_evidenced=True,
        removal_makes_function_unavailable=True,
        fallback_state=FallbackState.NONE,
        valid_time=NOW,
        book2_claim_refs=claim_refs,
        source_snapshot_refs=tuple(
            sorted(snapshot_ref(ref) for ref in claim_refs)
        ),
        fact_bindings=bindings,
    )


def redundancy_book():
    _, _, provenance = kernel()
    return RedundancyBook(provenance, FailureDomainBook(provenance))


def domain_book():
    _, _, provenance = kernel()
    return FailureDomainBook(provenance)


def scoped_redundancy(assessment_id: str):
    claim = redundancy_independence_claim()
    return r2_redundancy(
        assessment_id,
        provider_refs=provider_refs_for("A/B"),
        state=RedundancyState.INDEPENDENT_REDUNDANCY,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(
            redundancy_independence_binding(
                claim, providers=provider_refs_for("A/B")
            ),
        ),
        book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
    )


# ------------------------------------------------------- context binding seal


def test_a1_consumer_drift_via_model_copy_is_refused_at_the_gate() -> None:
    """model_copy skips every model validator; the gate must re-verify that
    each binding's declared context still equals the record context."""

    drifted = clean_evidence().model_copy(update={"consumer_ref": "consumer-other"})
    result = HardRuntimeGate(provenance=kernel()[2]).classify(drifted)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a2_binding_swap_to_plain_untyped_binding_is_refused_at_the_gate() -> None:
    """A binding stripped of its context fields (plain HardRuntimeFactBinding)
    carries no context at all; the gate must refuse it even though the claim
    itself is canonical and correctly qualified."""

    plain = HardRuntimeFactBinding(
        fact=HardRuntimeFact.RUNTIME_NECESSITY,
        claim_refs=(
            fact_claim_for(HardRuntimeFact.RUNTIME_NECESSITY, **CONTEXT),
        ),
    )
    swapped = clean_evidence().model_copy(
        update={
            "fact_bindings": tuple(
                plain if binding.fact is HardRuntimeFact.RUNTIME_NECESSITY else binding
                for binding in clean_evidence().fact_bindings
            )
        }
    )
    result = HardRuntimeGate(provenance=kernel()[2]).classify(swapped)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a3_function_drift_via_model_copy_is_refused_at_the_gate() -> None:
    drifted = clean_evidence().model_copy(update={"function": "other function"})
    result = HardRuntimeGate(provenance=kernel()[2]).classify(drifted)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a4_scope_drift_via_model_copy_is_refused_at_the_gate() -> None:
    drifted = clean_evidence().model_copy(update={"scope": "other scope"})
    result = HardRuntimeGate(provenance=kernel()[2]).classify(drifted)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a5_raw_dict_binding_is_refused_at_the_gate() -> None:
    """model_copy performs no coercion or validation, so a raw dict binding
    lands in the record untouched; the gate must refuse to classify it."""

    raw = clean_evidence().model_copy(
        update={
            "fact_bindings": (
                {"fact": "RUNTIME_NECESSITY", "claim_refs": ("whatever",)},
            )
        }
    )
    result = HardRuntimeGate(provenance=kernel()[2]).classify(raw)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("context-bound" in reason for reason in result.reasons)


# ------------------------------------------------- provenance closure seal


def test_a6_outside_claim_added_via_model_copy_is_refused_at_the_gate() -> None:
    _, _, provenance = kernel()
    outside = fact_claim_for(
        HardRuntimeFact.IDENTITY,
        consumer="consumer-b",
        provider="provider-b",
        function="function-b",
        scope="scope-b",
    )
    contaminated = clean_evidence().model_copy(
        update={
            "book2_claim_refs": tuple(
                sorted((*clean_evidence().book2_claim_refs, outside))
            )
        }
    )
    result = HardRuntimeGate(provenance).classify(contaminated)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a7_claim_refs_swapped_via_model_copy_are_re_resolved_by_the_gate() -> None:
    _, _, provenance = kernel()
    unrelated = fact_claim_for(
        HardRuntimeFact.RUNTIME_NECESSITY,
        consumer="consumer-b",
        provider="provider-b",
        function="function-b",
        scope="scope-b",
    )
    swapped = clean_evidence().model_copy(
        update={
            "fact_bindings": context_bindings(**CONTEXT)[:-1]
            + (
                context_bindings(**CONTEXT)[-1].model_copy(
                    update={"claim_refs": (unrelated,)}
                ),
            )
        }
    )
    result = HardRuntimeGate(provenance).classify(swapped)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


# ------------------------------------------- exact snapshot lineage seal


def test_a8_extra_snapshot_via_model_copy_is_refused_at_the_gate() -> None:
    _, _, provenance = kernel()
    contaminated = clean_evidence().model_copy(
        update={
            "source_snapshot_refs": (
                *clean_evidence().source_snapshot_refs,
                "snapshot://unrelated/extra",
            )
        }
    )
    result = HardRuntimeGate(provenance).classify(contaminated)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a9_duplicate_and_reordered_snapshots_deduplicate() -> None:
    _, _, provenance = kernel()
    duplicated_first = (clean_evidence().source_snapshot_refs[0],)
    scrambled = clean_evidence().model_copy(
        update={
            "source_snapshot_refs": tuple(
                reversed(duplicated_first + clean_evidence().source_snapshot_refs[1:])
            )
        }
    )
    result = HardRuntimeGate(provenance).classify(scrambled)
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME


def test_a10_missing_snapshot_via_model_copy_is_refused_at_the_gate() -> None:
    _, _, provenance = kernel()
    trimmed = clean_evidence().model_copy(
        update={"source_snapshot_refs": clean_evidence().source_snapshot_refs[1:]}
    )
    result = HardRuntimeGate(provenance).classify(trimmed)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


# ---------------------------------------------- redundancy context seal


def test_a11_partial_pair_evidence_cannot_claim_full_set_independence() -> None:
    """A three-provider assessment with an independence binding for only the
    first two providers must not reach INDEPENDENT_REDUNDANCY."""

    claim = redundancy_independence_claim()
    book = redundancy_book()
    assessment = r2_redundancy(
        "a11",
        provider_refs=(
            "provider-a",
            "provider-b",
            "provider-c",
        ),
        state=RedundancyState.INDEPENDENT_REDUNDANCY,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(
            redundancy_independence_binding(
                claim, providers=provider_refs_for("A/B")
            ),
        ),
        book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
    )
    with pytest.raises(Book4ProvenanceError):
        book.add(assessment)


def test_a12_independence_bindings_stripped_via_model_copy_are_refused() -> None:
    """model_copy can strip the pair-scope bindings while keeping the
    independence claims; add must re-verify exact binding coverage."""

    book = redundancy_book()
    stripped = scoped_redundancy("a12").model_copy(
        update={"independence_bindings": ()}
    )
    with pytest.raises(Book4ProvenanceError):
        book.add(stripped)


def test_a13_undeclared_independence_claim_added_via_model_copy_is_refused() -> None:
    """model_copy can append a second independence claim that no binding
    covers; add must refuse because bindings must cover exactly the declared
    claims."""

    book = redundancy_book()
    extra = "r2-independence-x-y-independent"
    inflated = scoped_redundancy("a13").model_copy(
        update={
            "positive_independence_claim_refs": (
                redundancy_independence_claim(),
                extra,
            )
        }
    )
    with pytest.raises(Book4ProvenanceError):
        book.add(inflated)


def test_a14_binding_for_wrong_pair_added_via_model_copy_is_refused() -> None:
    book = redundancy_book()
    hostile = scoped_redundancy("a14").model_copy(
        update={
            "independence_bindings": (
                redundancy_independence_binding(
                    redundancy_independence_claim(),
                    providers=provider_refs_for("X/Y"),
                ),
            )
        }
    )
    with pytest.raises(
        Book4ProvenanceError, match="outside the assessed provider set"
    ):
        book.add(hostile)


# ------------------------------------------- failure-domain pair scope seal


def test_a15_unbound_extra_system_cannot_ride_on_pair_scoped_independence() -> None:
    """A domain claiming two affected systems gets pair-scope evidence for the
    first system only; classify must refuse INDEPENDENT because the second
    system has no bound independence claim."""

    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = r2_failure_domain(
        "a15-left",
        system="system-a",
        mechanism_claim_refs=(mechanism_claim("A", "B"),),
        right_system="system-z",
    )
    right = r2_failure_domain(
        "a15-right",
        system="system-b",
        mechanism_claim_refs=(mechanism_claim("X", "Y"),),
    )
    left = book.add(left)
    right = book.add(right)
    claim = "r2-independence-a-b-independent"
    binding = IndependenceClaimBinding(
        claim_ref=claim,
        left_domain_ref=left.domain_id,
        right_domain_ref=right.domain_id,
        left_system_ref="system-a",
        right_system_ref="system-b",
        correlation_scope=left.correlation_scope,
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is not FailureDomainClassification.INDEPENDENT


def test_a16_shared_mechanism_still_dominates_after_audit_fixes() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    shared = mechanism_claim("A", "B", variant="shared")
    left = book.add(
        r2_failure_domain(
            "a16-left", system="system-a", mechanism_claim_refs=(shared,)
        )
    )
    right = book.add(
        r2_failure_domain(
            "a16-right", system="system-b", mechanism_claim_refs=(shared,)
        )
    )
    result = book.classify(left, right)
    assert result.classification is FailureDomainClassification.SHARED_FAILURE_DOMAIN
