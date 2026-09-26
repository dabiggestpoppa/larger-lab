"""Book 4 Hardening R2 — contextual claim binding + provenance-set closure.

Findings A-F: decision-driving claims must live inside the declared record
provenance set, must be bound to the exact assessed context, must be
pair-scoped for independence, and snapshot lineage must be exact.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_r1_support import NOW
from crypto_systems_intelligence_atlas.book4_r2_support import (
    GENERIC_PLACEHOLDER,
    R2_FACT_CONSUMER,
    R2_FACT_FUNCTION,
    R2_FACT_PROVIDER,
    R2_FACT_SCOPE,
    add_derived_evidence_claim,
    context_bindings,
    domain_independence_binding,
    fact_claim_for,
    kernel,
    mechanism_claim,
    provider_refs_for,
    r2_failure_domain,
    r2_redundancy,
    redundancy_independence_binding,
    redundancy_independence_claim,
    snapshot_ref,
    with_fact_claim,
)
from crypto_systems_intelligence_atlas.dependency import (
    FallbackState,
    HardRuntimeEvidence,
    HardRuntimeFact,
    HardRuntimeGate,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_provenance import (
    Book4ProvenanceError,
)
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    FailureDomainClassification,
)
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState

CONTEXT = {
    "consumer": R2_FACT_CONSUMER,
    "provider": R2_FACT_PROVIDER,
    "function": R2_FACT_FUNCTION,
    "scope": R2_FACT_SCOPE,
}
OTHER_CONTEXT = {
    "consumer": "consumer-b",
    "provider": "provider-b",
    "function": "function-b",
    "scope": "scope-b",
}


def hard_evidence_r2(
    *,
    bindings=None,
    book2_claim_refs=None,
    source_snapshot_refs=None,
) -> HardRuntimeEvidence:
    bindings = context_bindings(**CONTEXT) if bindings is None else bindings
    if book2_claim_refs is None:
        book2_claim_refs = tuple(
            sorted({ref for binding in bindings for ref in binding.claim_refs})
        )
    if source_snapshot_refs is None:
        source_snapshot_refs = tuple(
            sorted(snapshot_ref(ref) for ref in book2_claim_refs)
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
        book2_claim_refs=book2_claim_refs,
        source_snapshot_refs=source_snapshot_refs,
        fact_bindings=bindings,
    )


def rebound_evidence(fact: HardRuntimeFact, other_claim: str) -> HardRuntimeEvidence:
    """Evidence whose ``fact`` support is swapped to a context-mismatched claim."""

    bindings = with_fact_claim(context_bindings(**CONTEXT), fact, other_claim)
    return hard_evidence_r2(bindings=bindings)


# ---------------------------------------------------------------- Finding A
# Decision-driving HARD_RUNTIME fact claims must be inside the declared
# record provenance set (HardRuntimeEvidence.book2_claim_refs).


def test_a1_necessity_claim_omitted_from_record_provenance_rejected() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = context_bindings(**CONTEXT)
    necessity_ref = fact_claim_for(HardRuntimeFact.RUNTIME_NECESSITY, **CONTEXT)
    trimmed = tuple(
        ref
        for ref in hard_evidence_r2(bindings=bindings).book2_claim_refs
        if ref != necessity_ref
    )
    result = gate.classify(
        hard_evidence_r2(bindings=bindings, book2_claim_refs=trimmed)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("outside the declared book2_claim_refs" in reason for reason in result.reasons)


def test_a2_missing_fact_claim_from_record_provenance_rejected() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = tuple(
        binding
        for binding in context_bindings(**CONTEXT)
        if binding.fact is not HardRuntimeFact.DEPLOYED_CONFIGURATION
    )
    result = gate.classify(hard_evidence_r2(bindings=bindings))
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("DEPLOYED_CONFIGURATION" in reason for reason in result.reasons)


def test_a3_all_required_fact_claims_in_provenance_passes() -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence_r2())
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME


def test_a4_binding_claims_not_reachable_from_provenance_rejected() -> None:
    """Bindings reference six claims but provenance declares only one."""

    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = context_bindings(**CONTEXT)
    identity_ref = fact_claim_for(HardRuntimeFact.IDENTITY, **CONTEXT)
    result = gate.classify(
        hard_evidence_r2(bindings=bindings, book2_claim_refs=(identity_ref,))
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("outside the declared book2_claim_refs" in reason for reason in result.reasons)


# ---------------------------------------------------------------- Finding B
# Fact qualifier != fact context: a canonical claim must match the exact
# consumer/provider being assessed, not just the fact class.


def test_b1_runtime_necessity_claim_for_other_consumer_rejected() -> None:
    _, _, provenance = kernel()
    other = fact_claim_for(HardRuntimeFact.RUNTIME_NECESSITY, **OTHER_CONTEXT)
    result = HardRuntimeGate(provenance).classify(
        rebound_evidence(HardRuntimeFact.RUNTIME_NECESSITY, other)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("does not bind the assessed consumer" in reason for reason in result.reasons)


def test_b2_deployed_configuration_claim_for_other_provider_rejected() -> None:
    _, _, provenance = kernel()
    other = fact_claim_for(HardRuntimeFact.DEPLOYED_CONFIGURATION, **OTHER_CONTEXT)
    result = HardRuntimeGate(provenance).classify(
        rebound_evidence(HardRuntimeFact.DEPLOYED_CONFIGURATION, other)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("does not bind the assessed provider" in reason for reason in result.reasons)


def test_b3_failure_consequence_claim_for_other_function_rejected() -> None:
    """Function/scope have no Proposition dimension, so the claim rebinds only
    through consumer/provider; the mismatched context binding is rejected
    structurally, and here the unrelated claim fails the provider check."""

    _, _, provenance = kernel()
    other = fact_claim_for(HardRuntimeFact.FAILURE_CONSEQUENCE, **OTHER_CONTEXT)
    result = HardRuntimeGate(provenance).classify(
        rebound_evidence(HardRuntimeFact.FAILURE_CONSEQUENCE, other)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert result.reasons


def test_b4_no_fallback_claim_for_other_scope_rejected() -> None:
    _, _, provenance = kernel()
    other = fact_claim_for(
        HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK, **OTHER_CONTEXT
    )
    result = HardRuntimeGate(provenance).classify(
        rebound_evidence(HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK, other)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert result.reasons


def test_b5_valid_time_claim_for_other_deployment_rejected() -> None:
    _, _, provenance = kernel()
    other = fact_claim_for(HardRuntimeFact.VALID_TIME, **OTHER_CONTEXT)
    result = HardRuntimeGate(provenance).classify(
        rebound_evidence(HardRuntimeFact.VALID_TIME, other)
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert result.reasons


def test_b6_exact_context_fact_claims_produce_hard_runtime() -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence_r2())
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME


def test_b7_binding_context_must_equal_assessment_context() -> None:
    """A binding whose declared context differs from the record is invalid."""

    bindings = context_bindings(consumer="consumer-b", **{
        key: value for key, value in CONTEXT.items() if key != "consumer"
    })
    with pytest.raises(ValidationError, match="binding context must equal"):
        hard_evidence_r2(bindings=bindings)


# ---------------------------------------------------------------- Finding C
# Failure-domain independence is pair-scoped.


def test_c1_independence_claim_for_other_pair_is_rejected() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(r2_failure_domain("c1-left", system="system-a", mechanism_claim_refs=(mechanism_claim("A", "B"),)))
    right = book.add(r2_failure_domain("c1-right", system="system-b", mechanism_claim_refs=(mechanism_claim("X", "Y"),)))
    claim = "r2-independence-x-y-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is not FailureDomainClassification.INDEPENDENT
    assert "does not bind" in result.reason or "not scoped" in result.reason


def test_c2_claim_for_same_systems_other_scope_is_not_independent() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(
        r2_failure_domain(
            "c2-left",
            system="system-a",
            mechanism_claim_refs=(mechanism_claim("A", "B"),),
            correlation_scope="scope one",
        )
    )
    right = book.add(
        r2_failure_domain(
            "c2-right",
            system="system-b",
            mechanism_claim_refs=(mechanism_claim("X", "Y"),),
            correlation_scope="scope one",
        )
    )
    claim = "r2-independence-a-b-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
        scope="other scope",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is not FailureDomainClassification.INDEPENDENT


def test_c3_pair_scoped_claim_can_produce_independent() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(r2_failure_domain("c3-left", system="system-a", mechanism_claim_refs=(mechanism_claim("A", "B"),)))
    right = book.add(r2_failure_domain("c3-right", system="system-b", mechanism_claim_refs=(mechanism_claim("X", "Y"),)))
    claim = "r2-independence-a-b-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is FailureDomainClassification.INDEPENDENT


def test_c4_shared_mechanism_beats_unrelated_independence_claim() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    shared = mechanism_claim("A", "B", variant="shared")
    left = book.add(r2_failure_domain("c4-left", system="system-a", mechanism_claim_refs=(shared,)))
    right = book.add(r2_failure_domain("c4-right", system="system-b", mechanism_claim_refs=(shared,)))
    claim = "r2-independence-x-y-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is FailureDomainClassification.SHARED_FAILURE_DOMAIN


def test_c5_pair_scoped_independence_without_shared_mechanism_is_independent() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(r2_failure_domain("c5-left", system="system-a", mechanism_claim_refs=(mechanism_claim("A", "B"),)))
    right = book.add(r2_failure_domain("c5-right", system="system-b", mechanism_claim_refs=(mechanism_claim("X", "Y"),)))
    claim = "r2-independence-a-b-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim,),
        independence_bindings=(binding,),
    )
    assert result.classification is FailureDomainClassification.INDEPENDENT


def test_c6_binding_set_must_cover_exactly_the_declared_claims() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(r2_failure_domain("c6-left", system="system-a", mechanism_claim_refs=(mechanism_claim("A", "B"),)))
    right = book.add(r2_failure_domain("c6-right", system="system-b", mechanism_claim_refs=(mechanism_claim("X", "Y"),)))
    claim = "r2-independence-a-b-independent"
    binding = domain_independence_binding(
        claim,
        left_domain_id=left.domain_id,
        right_domain_id=right.domain_id,
        left_system="system-a",
        right_system="system-b",
    )
    result = book.classify(
        left,
        right,
        positive_independence_claim_refs=(claim, "r2-independence-x-y-independent"),
        independence_bindings=(binding,),
    )
    assert result.classification is not FailureDomainClassification.INDEPENDENT


# ---------------------------------------------------------------- Finding D
# Redundancy independence must be provider/function-scoped.


def test_d1_independence_claim_for_other_providers_rejected() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    other_binding = redundancy_independence_binding(
        claim, providers=provider_refs_for("X/Y")
    )
    with pytest.raises(Book4ProvenanceError, match="not scoped"):
        book.add(
            r2_redundancy(
                "d1",
                provider_refs=provider_refs_for("A/B"),
                state=RedundancyState.INDEPENDENT_REDUNDANCY,
                positive_independence_claim_refs=(claim,),
                independence_bindings=(other_binding,),
                book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
            )
        )


def test_d2_independence_claim_for_other_function_rejected() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    other_binding = redundancy_independence_binding(
        claim,
        providers=provider_refs_for("A/B"),
        function="settlement finality",
    )
    with pytest.raises(Book4ProvenanceError, match="not scoped"):
        book.add(
            r2_redundancy(
                "d2",
                provider_refs=provider_refs_for("A/B"),
                state=RedundancyState.INDEPENDENT_REDUNDANCY,
                positive_independence_claim_refs=(claim,),
                independence_bindings=(other_binding,),
                book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
            )
        )


def test_d3_claim_with_wrong_subject_rejected() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    other_binding = redundancy_independence_binding(
        claim,
        providers=provider_refs_for("A/B"),
        subject="fixture:other-subject",
    )
    with pytest.raises(Book4ProvenanceError, match="not scoped"):
        book.add(
            r2_redundancy(
                "d3",
                provider_refs=provider_refs_for("A/B"),
                state=RedundancyState.INDEPENDENT_REDUNDANCY,
                positive_independence_claim_refs=(claim,),
                independence_bindings=(other_binding,),
                book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
            )
        )


def test_d4_correctly_scoped_claim_allows_independent_redundancy() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    binding = redundancy_independence_binding(
        claim, providers=provider_refs_for("A/B")
    )
    item = book.add(
        r2_redundancy(
            "d4",
            provider_refs=provider_refs_for("A/B"),
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            positive_independence_claim_refs=(claim,),
            independence_bindings=(binding,),
            book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
        )
    )
    assert item.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_d5_independent_redundancy_with_resolved_shared_domain_rejected() -> None:
    with pytest.raises(ValidationError, match="correlated"):
        r2_redundancy(
            "d5",
            provider_refs=provider_refs_for("A/B"),
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            positive_independence_claim_refs=(redundancy_independence_claim(),),
            independence_bindings=(
                redundancy_independence_binding(
                    redundancy_independence_claim(),
                    providers=provider_refs_for("A/B"),
                ),
            ),
            failure_domain_refs=("domain-shared",),
        )


# ---------------------------------------------------------------- Finding E
# Nested claim-set coherence.


def test_e1_mechanism_claim_outside_domain_provenance_rejected() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    domain = r2_failure_domain(
        "e1",
        system="system-a",
        mechanism_claim_refs=(mechanism_claim("A", "B"),),
        book2_claim_refs=(GENERIC_PLACEHOLDER,),
    )
    with pytest.raises(Book4ProvenanceError, match="outside"):
        book.add(domain)


def test_e2_mechanism_claim_inside_domain_provenance_passes() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    domain = book.add(
        r2_failure_domain(
            "e2",
            system="system-a",
            mechanism_claim_refs=(mechanism_claim("A", "B"),),
            book2_claim_refs=(GENERIC_PLACEHOLDER, mechanism_claim("A", "B")),
        )
    )
    assert domain.domain_id == "e2"


def test_e3_independence_claim_outside_redundancy_provenance_rejected() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    binding = redundancy_independence_binding(
        claim, providers=provider_refs_for("A/B")
    )
    with pytest.raises(Book4ProvenanceError, match="outside"):
        book.add(
            r2_redundancy(
                "e3",
                provider_refs=provider_refs_for("A/B"),
                state=RedundancyState.INDEPENDENT_REDUNDANCY,
                positive_independence_claim_refs=(claim,),
                independence_bindings=(binding,),
                book2_claim_refs=(GENERIC_PLACEHOLDER,),
            )
        )


def test_e4_independence_claim_inside_redundancy_provenance_passes() -> None:
    _, _, provenance = kernel()
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    claim = redundancy_independence_claim()
    binding = redundancy_independence_binding(
        claim, providers=provider_refs_for("A/B")
    )
    item = book.add(
        r2_redundancy(
            "e4",
            provider_refs=provider_refs_for("A/B"),
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            positive_independence_claim_refs=(claim,),
            independence_bindings=(binding,),
            book2_claim_refs=(GENERIC_PLACEHOLDER, claim),
        )
    )
    assert item.redundancy_id == "e4"


def test_e5_hard_runtime_fact_claim_outside_provenance_rejected() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = context_bindings(**CONTEXT)
    identity_ref = fact_claim_for(HardRuntimeFact.IDENTITY, **CONTEXT)
    result = gate.classify(
        hard_evidence_r2(bindings=bindings, book2_claim_refs=(identity_ref,))
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


# ---------------------------------------------------------------- Finding F
# Exact snapshot lineage.


def test_f1_missing_required_snapshot_rejected() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    evidence_record = hard_evidence_r2()
    trimmed = tuple(evidence_record.source_snapshot_refs[1:])
    result = gate.classify(hard_evidence_r2(source_snapshot_refs=trimmed))
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("missing required snapshots" in reason for reason in result.reasons)


def test_f2_extra_unrelated_snapshot_rejected() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    evidence_record = hard_evidence_r2()
    contaminated = tuple(
        sorted((*evidence_record.source_snapshot_refs, "snapshot://unrelated/extra"))
    )
    result = gate.classify(hard_evidence_r2(source_snapshot_refs=contaminated))
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("unrelated extra snapshots" in reason for reason in result.reasons)


def test_f3_exact_snapshot_set_passes() -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence_r2())
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME


def test_f4_deduplicated_shared_snapshot_set_passes() -> None:
    claims, evidence, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = context_bindings(**CONTEXT)
    extra_claim = add_derived_evidence_claim(
        claims,
        evidence,
        claim_id="r2-shared-snapshot-claim",
        parent_claim_ref=fact_claim_for(HardRuntimeFact.IDENTITY, **CONTEXT),
    )
    base = hard_evidence_r2(bindings=bindings)
    same_snapshot = tuple(sorted({*base.book2_claim_refs, extra_claim}))
    result = gate.classify(
        hard_evidence_r2(
            bindings=bindings,
            book2_claim_refs=same_snapshot,
            source_snapshot_refs=base.source_snapshot_refs,
        )
    )
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME


def test_f5_all_and_only_reachable_snapshots_pass() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    bindings = context_bindings(**CONTEXT)
    base = hard_evidence_r2(bindings=bindings)
    result = gate.classify(
        hard_evidence_r2(
            bindings=bindings, source_snapshot_refs=base.source_snapshot_refs
        )
    )
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME
    partial = base.source_snapshot_refs[:-1]
    rejected = gate.classify(
        hard_evidence_r2(bindings=bindings, source_snapshot_refs=partial)
    )
    assert rejected.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_f6_exact_lineage_applies_to_dependency_records() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import (
        descriptor,
        kernel as support_kernel,
    )
    from crypto_systems_intelligence_atlas.dependency import (
        DependencyBook,
        DependencyClass,
        DependencyRecord,
        RuntimeScope,
    )
    from crypto_systems_intelligence_atlas.relationships import EdgeType

    _, _, provenance = support_kernel()
    book = DependencyBook(provenance)
    payload = {
        "dependency_id": "r2-exact-lineage",
        "subject_ref": "fixture:subject",
        "object_ref": "fixture:object",
        "function": "execute liquidation",
        "scope": "liquidation execution",
        "relation_basis": EdgeType.DEPENDS_ON,
        "dependency_class": DependencyClass.DIRECT_RUNTIME,
        "runtime_scope": RuntimeScope.SOFT_RUNTIME,
        "strength_descriptor": descriptor(),
        "mechanism": "configured service call",
        "valid_time": NOW,
        "book2_claim_refs": ("book4-claim-current",),
        "source_snapshot_refs": (
            "snapshot://book4/evidence",
            "snapshot://unrelated/extra",
        ),
    }
    record = DependencyRecord.model_validate(payload)
    with pytest.raises(Book4ProvenanceError, match="unrelated"):
        book.add(record)
    exact = record.model_copy(
        update={"source_snapshot_refs": ("snapshot://book4/evidence",)}
    )
    assert book.add(exact) is not None


# ---------------------------------------------------------------- R1 preservation

def test_r1_legacy_unbound_independence_is_now_rejected() -> None:
    """R1 accepted qualifier-only independence; R2 requires pair binding."""

    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(r2_failure_domain("r1p-left", system="system-a", mechanism_claim_refs=(mechanism_claim("A", "B"),)))
    right = book.add(r2_failure_domain("r1p-right", system="system-b", mechanism_claim_refs=(mechanism_claim("X", "Y"),)))
    with pytest.raises(Book4ProvenanceError, match="pair-scoped"):
        book.classify(
            left,
            right,
            positive_independence_claim_refs=("r2-independence-a-b-independent",),
        )


def test_r1_hard_runtime_provenance_helpers_still_resolve() -> None:
    """The R1 fixture kernel keeps resolving through the same gates."""

    from crypto_systems_intelligence_atlas.book4_r1_support import (
        all_snapshot_refs,
        fact_bindings,
        hard_evidence_r1,
        kernel as r1_kernel,
    )

    _, _, provenance = r1_kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence_r1())
    assert result.runtime_scope is RuntimeScope.HARD_RUNTIME
    assert len(fact_bindings()) == len(HardRuntimeFact)
    assert all_snapshot_refs()
