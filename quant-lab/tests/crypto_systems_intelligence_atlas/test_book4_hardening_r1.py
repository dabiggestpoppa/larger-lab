"""Book 4 Hardening R1 — failing provenance, integrity, and boundary tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_r1_support import (
    ACTIVE_FALLBACK_CLAIM,
    DEPLOYMENT_CLAIM,
    GENERIC_CLAIM,
    INDEPENDENCE_CLAIM,
    INDEPENDENCE_CONTESTED_CLAIM,
    MECHANISM_LEFT_CLAIM,
    MECHANISM_RIGHT_CLAIM,
    MECHANISM_SHARED_CLAIM,
    NOW,
    all_snapshot_refs,
    contested_kernel,
    fact_bindings,
    failure_domain_r1,
    hard_evidence_r1,
    kernel,
    redundancy_r1,
    snapshot_ref,
)
from crypto_systems_intelligence_atlas.claims import ClaimState
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.dependency import (
    BOOK4_DEPENDENCY_RELATION_ALLOWLIST,
    BOOK5_ECONOMIC_RELATIONS,
    DependencyBook,
    DependencyClass,
    DependencyRecord,
    DependencyStrengthDescriptor,
    DependencyStrengthState,
    FallbackState,
    HardRuntimeFact,
    HardRuntimeFactBinding,
    HardRuntimeGate,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_provenance import (
    Book4Provenance,
    Book4ProvenanceError,
)
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    FailureDomainClassification,
)
from crypto_systems_intelligence_atlas.relationships import EdgeType
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook, RedundancyState

ALL_FACTS = frozenset(HardRuntimeFact)
SUPPORT_NOW = NOW


def gate() -> HardRuntimeGate:
    _, _, provenance = kernel()
    return HardRuntimeGate(provenance)


# ---------------------------------------------------------------- Finding A


def test_a1_unrelated_canonical_claim_cannot_drive_hard_runtime() -> None:
    evidence = hard_evidence_r1(
        bindings=fact_bindings(omit=ALL_FACTS),
        book2_claim_refs=(GENERIC_CLAIM,),
    )
    result = gate().classify(evidence)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert result.reasons


def test_a2_deployment_only_cannot_drive_hard_runtime() -> None:
    evidence = hard_evidence_r1(
        bindings=fact_bindings(omit={HardRuntimeFact.RUNTIME_NECESSITY})
    )
    assert gate().classify(evidence).runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a3_necessity_only_cannot_drive_hard_runtime() -> None:
    evidence = hard_evidence_r1(
        bindings=fact_bindings(omit={HardRuntimeFact.FAILURE_CONSEQUENCE})
    )
    assert gate().classify(evidence).runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a4_no_fallback_assertion_without_proof_is_not_hard_runtime() -> None:
    evidence = hard_evidence_r1(
        bindings=fact_bindings(omit={HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK}),
        fallback_state=FallbackState.NONE,
    )
    assert gate().classify(evidence).runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a5_all_fact_specific_claims_support_hard_runtime() -> None:
    assert gate().classify(hard_evidence_r1()).runtime_scope is RuntimeScope.HARD_RUNTIME


def _provenance_with_claim_in_state(target: ClaimState) -> Book4Provenance:
    service, _ = contested_kernel()
    engine = ClaimStateEngine(service)
    evidence_ref = service.require(INDEPENDENCE_CONTESTED_CLAIM).evidence_refs[0]
    if target is ClaimState.UNRESOLVED:
        declared_id = f"{INDEPENDENCE_CONTESTED_CLAIM}-declared"
        service.claim_store.add_initial(
            service.require(INDEPENDENCE_CONTESTED_CLAIM).model_copy(
                update={"claim_id": declared_id, "claim_state": ClaimState.DECLARED}
            )
        )
        engine.transition(
            declared_id,
            target,
            triggering_evidence_refs=(evidence_ref,),
            transitioned_at=NOW,
        )
    elif target is ClaimState.SUPERSEDED:
        replacement_id = f"{INDEPENDENCE_CONTESTED_CLAIM}-replacement"
        service.add_observed(
            service.require(INDEPENDENCE_CONTESTED_CLAIM).model_copy(
                update={"claim_id": replacement_id}
            )
        )
        engine.transition(
            INDEPENDENCE_CONTESTED_CLAIM,
            target,
            triggering_evidence_refs=(evidence_ref,),
            transitioned_at=NOW,
            replacement_claim_id=replacement_id,
            supersession_reason="R1 superseded fixture",
        )
    else:
        engine.transition(
            INDEPENDENCE_CONTESTED_CLAIM,
            target,
            triggering_evidence_refs=(evidence_ref,),
            transitioned_at=NOW,
        )
    return Book4Provenance(service.claim_store, service.evidence_store)


@pytest.mark.parametrize(
    "target",
    [
        ClaimState.CONTESTED,
        ClaimState.UNRESOLVED,
        ClaimState.STALE,
        ClaimState.REJECTED,
        ClaimState.SUPERSEDED,
    ],
)
def test_a6_non_promotable_fact_claims_cannot_support_hard_runtime(
    target: ClaimState,
) -> None:
    provenance = _provenance_with_claim_in_state(target)
    bindings = tuple(
        HardRuntimeFactBinding(fact=binding.fact, claim_refs=(INDEPENDENCE_CONTESTED_CLAIM,))
        for binding in fact_bindings()
    )
    result = HardRuntimeGate(provenance).classify(hard_evidence_r1(bindings=bindings))
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


def test_a7_fallback_proof_claim_cannot_prove_no_active_fallback() -> None:
    bindings = tuple(
        HardRuntimeFactBinding(
            fact=HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK,
            claim_refs=(ACTIVE_FALLBACK_CLAIM,),
        )
        if binding.fact is HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK
        else binding
        for binding in fact_bindings()
    )
    assert gate().classify(hard_evidence_r1(bindings=bindings)).runtime_scope is not RuntimeScope.HARD_RUNTIME


# ---------------------------------------------------------------- Finding B


def test_b1_arbitrary_mechanism_string_cannot_establish_shared_domain() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = failure_domain_r1(
        "b1-left", mechanism_claim_refs=(GENERIC_CLAIM,), mechanism_evidence_refs=("fake-cloud",)
    )
    with pytest.raises(Book4ProvenanceError, match="qualifier"):
        book.add(left)


def test_b2_same_provider_only_is_never_shared_domain() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(
        failure_domain_r1("b2-left", mechanism_claim_refs=(MECHANISM_LEFT_CLAIM,), provider="same-brand")
    )
    right = book.add(
        failure_domain_r1("b2-right", mechanism_claim_refs=(MECHANISM_RIGHT_CLAIM,), provider="same-brand")
    )
    result = book.classify(left, right)
    assert result.classification is not FailureDomainClassification.SHARED_FAILURE_DOMAIN


def test_b3_canonical_shared_mechanism_establishes_shared_domain() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain_r1("b3-left", mechanism_claim_refs=(MECHANISM_SHARED_CLAIM,), provider="a"))
    right = book.add(failure_domain_r1("b3-right", mechanism_claim_refs=(MECHANISM_SHARED_CLAIM,), provider="b"))
    assert book.classify(left, right).classification is FailureDomainClassification.SHARED_FAILURE_DOMAIN


def test_b4_different_mechanisms_without_independence_are_unknown() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain_r1("b4-left", mechanism_claim_refs=(MECHANISM_LEFT_CLAIM,)))
    right = book.add(failure_domain_r1("b4-right", mechanism_claim_refs=(MECHANISM_RIGHT_CLAIM,)))
    assert book.classify(left, right).classification is FailureDomainClassification.UNKNOWN


def test_b5_noncanonical_independence_claim_cannot_establish_independence() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain_r1("b5-left", mechanism_claim_refs=(MECHANISM_LEFT_CLAIM,)))
    right = book.add(failure_domain_r1("b5-right", mechanism_claim_refs=(MECHANISM_RIGHT_CLAIM,)))
    result = book.classify(left, right, positive_independence_claim_refs=("arbitrary-string",))
    assert result.classification is not FailureDomainClassification.INDEPENDENT


def test_b6_canonical_independence_claim_establishes_independence() -> None:
    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain_r1("b6-left", mechanism_claim_refs=(MECHANISM_LEFT_CLAIM,)))
    right = book.add(failure_domain_r1("b6-right", mechanism_claim_refs=(MECHANISM_RIGHT_CLAIM,)))
    result = book.classify(left, right, positive_independence_claim_refs=(INDEPENDENCE_CLAIM,))
    assert result.classification is FailureDomainClassification.INDEPENDENT


def test_b7_contested_independence_claim_is_not_independence() -> None:
    provenance = _provenance_with_claim_in_state(ClaimState.CONTESTED)
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain_r1("b7-left", mechanism_claim_refs=(MECHANISM_SHARED_CLAIM,)))
    right = book.add(failure_domain_r1("b7-right", mechanism_claim_refs=(MECHANISM_LEFT_CLAIM,)))
    result = book.classify(
        left, right, positive_independence_claim_refs=(INDEPENDENCE_CONTESTED_CLAIM,)
    )
    assert result.classification is not FailureDomainClassification.INDEPENDENT


# ---------------------------------------------------------------- Finding C


def _books():
    _, _, provenance = kernel()
    return provenance, FailureDomainBook(provenance)


def test_c1_correlated_redundancy_rejects_unknown_failure_domain() -> None:
    provenance, domains = _books()
    book = RedundancyBook(provenance, domains)
    with pytest.raises(Book4ProvenanceError, match="unknown failure domain"):
        book.add(
            redundancy_r1(
                "c1",
                state=RedundancyState.CORRELATED_REDUNDANCY,
                failure_domain_refs=("domain-does-not-exist",),
            )
        )


def test_c2_independent_redundancy_rejects_arbitrary_independence_string() -> None:
    provenance, domains = _books()
    book = RedundancyBook(provenance, domains)
    with pytest.raises(Book4ProvenanceError):
        book.add(
            redundancy_r1(
                "c2",
                state=RedundancyState.INDEPENDENT_REDUNDANCY,
                positive_independence_claim_refs=("made-up",),
            )
        )


def test_c3_independent_redundancy_with_canonical_evidence_passes() -> None:
    provenance, domains = _books()
    book = RedundancyBook(provenance, domains)
    item = book.add(
        redundancy_r1(
            "c3",
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            positive_independence_claim_refs=(INDEPENDENCE_CLAIM,),
        )
    )
    assert item.state is RedundancyState.INDEPENDENT_REDUNDANCY


def test_c4_independent_redundancy_rejects_shared_failure_domain() -> None:
    with pytest.raises(ValidationError, match="correlated"):
        redundancy_r1(
            "c4",
            state=RedundancyState.INDEPENDENT_REDUNDANCY,
            failure_domain_refs=("domain-shared",),
            positive_independence_claim_refs=(INDEPENDENCE_CLAIM,),
        )


def test_c5_correlated_redundancy_with_real_failure_domain_passes() -> None:
    provenance, domains = _books()
    domains.add(failure_domain_r1("domain-real", mechanism_claim_refs=(MECHANISM_SHARED_CLAIM,)))
    book = RedundancyBook(provenance, domains)
    item = book.add(
        redundancy_r1(
            "c5",
            state=RedundancyState.CORRELATED_REDUNDANCY,
            failure_domain_refs=("domain-real",),
        )
    )
    assert item.state is RedundancyState.CORRELATED_REDUNDANCY


def test_c6_two_providers_only_remain_unknown() -> None:
    provenance, domains = _books()
    book = RedundancyBook(provenance, domains)
    item = book.add(redundancy_r1("c6"))
    assert item.state is RedundancyState.UNKNOWN
    assert item.positive_independence_claim_refs == ()


# ---------------------------------------------------------------- Finding D


def _dependency_payload(
    snapshot_refs: tuple[str, ...],
    *,
    relation: EdgeType = EdgeType.DEPENDS_ON,
    dependency_id: str = "r1-dependency",
    function: str = "read chain state",
    scope: str = "rpc read path",
) -> dict[str, object]:
    return {
        "dependency_id": dependency_id,
        "subject_ref": "fixture:r1-consumer",
        "object_ref": "fixture:r1-provider",
        "function": function,
        "scope": scope,
        "relation_basis": relation,
        "dependency_class": DependencyClass.DIRECT_RUNTIME,
        "runtime_scope": RuntimeScope.SOFT_RUNTIME,
        "strength_descriptor": DependencyStrengthDescriptor(
            state=DependencyStrengthState.PRIMARY,
            function=function,
            scope=scope,
            mechanism="configured endpoint call",
            valid_time=SUPPORT_NOW,
            book2_claim_refs=(DEPLOYMENT_CLAIM,),
        ),
        "mechanism": "configured endpoint call",
        "valid_time": SUPPORT_NOW,
        "book2_claim_refs": (DEPLOYMENT_CLAIM,),
        "source_snapshot_refs": snapshot_refs,
    }


def test_d1_fake_snapshot_ref_is_rejected() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    record = DependencyRecord.model_validate(_dependency_payload(("snapshot://invented",)))
    with pytest.raises(Book4ProvenanceError, match="snapshot"):
        book.add(record)


def test_d2_snapshot_unrelated_to_supporting_claim_is_rejected() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    record = DependencyRecord.model_validate(
        _dependency_payload((snapshot_ref(GENERIC_CLAIM),))
    )
    with pytest.raises(Book4ProvenanceError, match="snapshot"):
        book.add(record)


def test_d3_snapshot_from_supporting_claim_is_accepted() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    record = DependencyRecord.model_validate(
        _dependency_payload((snapshot_ref(DEPLOYMENT_CLAIM),))
    )
    assert book.add(record) is not None


# ---------------------------------------------------------------- Finding E


@pytest.mark.parametrize(
    "relation",
    [
        EdgeType.COLLATERAL_IN,
        EdgeType.LIQUIDITY_ON,
        EdgeType.STAKED_IN,
        EdgeType.RESTAKED_IN,
    ],
)
def test_e1_e4_book5_economic_relations_are_rejected(relation: EdgeType) -> None:
    payload = _dependency_payload(
        all_snapshot_refs(), relation=relation, dependency_id=f"r1-{relation.value.lower()}"
    )
    with pytest.raises(ValidationError, match="Book 4"):
        DependencyRecord.model_validate(payload)


def test_e5_capital_flow_semantics_fail_structurally_without_forbidden_phrases() -> None:
    payload = _dependency_payload(
        all_snapshot_refs(),
        relation=EdgeType.COLLATERAL_IN,
        dependency_id="r1-capital-flow",
        function="post units for execution",
        scope="protocol margin account",
    )
    with pytest.raises(ValidationError, match="Book 4"):
        DependencyRecord.model_validate(payload)


@pytest.mark.parametrize(
    "relation",
    [EdgeType.ROUTED_THROUGH, EdgeType.BRIDGES_TO, EdgeType.DEPENDS_ON],
)
def test_e6_e8_technical_relations_remain_supported(relation: EdgeType) -> None:
    assert relation in BOOK4_DEPENDENCY_RELATION_ALLOWLIST
    payload = _dependency_payload(
        all_snapshot_refs(), relation=relation, dependency_id=f"r1-{relation.value.lower()}"
    )
    assert DependencyRecord.model_validate(payload) is not None


def test_e_book5_relations_are_never_in_the_book4_allowlist() -> None:
    assert not (BOOK5_ECONOMIC_RELATIONS & BOOK4_DEPENDENCY_RELATION_ALLOWLIST)
