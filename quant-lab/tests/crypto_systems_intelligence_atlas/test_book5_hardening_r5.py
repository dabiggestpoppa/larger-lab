"""Book 5 HARDENING R5 — binding-basis live currentness seal.

Defect class under test (R4 reconciliation, demonstrated failure-first):

R4 correctly established REGISTRY MEMBERSHIP != CURRENT AUTHORITY. R5
completes the separately authorized clause R4 did not implement:
BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY.

R5-D1   ``ClaimContextBinding`` (the R2 component context family) resolves
        its ``basis_claim_refs`` only at REGISTRATION time
        (``bind_claim_context``). ``validate_principal_component`` checks
        the SUBJECT claim's live currentness and the binding FIELD
        agreement, but never re-resolves the binding's BASIS claims. A
        basis claim that decays to STALE/CONTESTED/REJECTED/SUPERSEDED
        (while the subject stays OBSERVED) leaves every component
        authority boundary OPEN: aggregate_same_unit, components_for,
        collapse_same_unit, lineage_view, compose_snapshot all PASS.

R5-D2   ``QuantitativeRecordContextBinding`` (the R3 flow/liability/fact
        family) has the same registration-only basis validation:
        ``validate_quantitative_record`` live-revalidates the record's own
        claim refs but not the binding's basis refs.

Central R5 invariant (mirrors R4 registry doctrine):
    BINDING EXISTS != BINDING CURRENTLY AUTHORITATIVE
    registration proves VALID THEN; decision-time resolution proves VALID NOW.
    SUBJECT CLAIM CURRENT != BINDING BASIS CURRENT — authority requires BOTH.
    No decayed basis claim through authority; no auto-follow of superseded
    basis; the frozen binding object is never mutated — its contextual
    interpretation is immutable, its epistemic authority is not.

Row families: A (component basis decay, aggregate boundary), B (quantitative
basis decay), C/Q (subject vs basis distinction), F/L/O (per-kind matrix),
P (component matrix), M (multi-basis weakest link), D (superseded basis no
auto-follow), S (registry propagation, Phase 10), E (empty basis semantics).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from crypto_systems_intelligence_atlas.book5_core import EconomicLocation, LocationType
from crypto_systems_intelligence_atlas.book5_lineage import DebtLiability
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
    QuantitativeRecordContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    CapitalFlow,
    FlowType,
    ObservedCommonValueFact,
)
from crypto_systems_intelligence_atlas.book5_support import (
    NOW,
    component,
    component_set,
    kernel,
    make_claim,
    make_evidence,
)
from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis
from crypto_systems_intelligence_atlas.claims import ClaimState, same_proposition
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import (
    AuthoritySeed,
    AuthorityTier,
    ClaimFamily,
    SourceClass,
)

T0 = NOW
T1 = datetime(2026, 9, 29, 18, tzinfo=UTC)

DECAY_STATES = (
    ClaimState.STALE,
    ClaimState.CONTESTED,
    ClaimState.REJECTED,
    ClaimState.SUPERSEDED,
)


# ---------------------------------------------------------------------------
# transition machinery (accepted Book 2 engine only)
# ---------------------------------------------------------------------------


def _register_economics_claim(
    provenance: Book5Provenance, tag: str, *, qualifier: str | None = None
) -> str:
    evidence_ref = make_evidence(provenance.evidence_store, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    provenance.claim_store.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, qualifier=qualifier)
    )
    return claim_id


def _transition_claim(
    provenance: Book5Provenance,
    claim_id: str,
    new_state: ClaimState,
    *,
    at: datetime = T1,
    replacement_claim_id: str | None = None,
    supersession_reason: str | None = None,
    corroborating_claim_id: str | None = None,
    triggering_evidence_refs: tuple[str, ...] | None = None,
) -> None:
    from crypto_systems_intelligence_atlas.claims import ClaimService

    service = ClaimService(provenance.evidence_store, provenance.claim_store)
    engine = ClaimStateEngine(service)
    current = provenance.claim_store.require(claim_id)
    engine.transition(
        claim_id,
        new_state,
        triggering_evidence_refs=(
            triggering_evidence_refs
            if triggering_evidence_refs is not None
            else current.evidence_refs
        ),
        transitioned_at=at,
        replacement_claim_id=replacement_claim_id,
        supersession_reason=supersession_reason,
        corroborating_claim_id=corroborating_claim_id,
    )


def _supersede(provenance: Book5Provenance, claim_id: str) -> str:
    """SUPERSede ``claim_id`` through the canonical engine; return the
    replacement claim id (which stays current in the store)."""

    replacement_id = f"{claim_id}-replacement"
    provenance.claim_store.add_initial(
        make_claim(
            replacement_id,
            evidence_ref=make_evidence(
                provenance.evidence_store, f"{replacement_id}-ev"
            ),
        )
    )
    _transition_claim(
        provenance,
        claim_id,
        ClaimState.SUPERSEDED,
        replacement_claim_id=replacement_id,
        supersession_reason="R5 binding-basis decay fixture",
    )
    return replacement_id


def _decay(
    provenance: Book5Provenance, claim_id: str, new_state: ClaimState
) -> None:
    if new_state is ClaimState.SUPERSEDED:
        _supersede(provenance, claim_id)
    else:
        _transition_claim(provenance, claim_id, new_state)


def _restore_corroborated(provenance: Book5Provenance, claim_id: str) -> None:
    """CONTESTED -> CORROBORATED through the accepted P-4 route: distinct
    source, owner, and mechanism; proposition equivalence."""

    corroboration_source_id = f"csia:source:{claim_id}-independent"
    provenance.evidence_store._source_registry.register(
        Source(
            source_id=corroboration_source_id,
            source_class=SourceClass.NATIVE_TECHNICAL,
            canonical_name="R5 independent corroborating fixture",
            owner_entity_ref=f"csia:entity:{claim_id}-owner",
            object_scope=(),
            locator=LocatorMetadata(
                base_locator=f"fixture://book5/{claim_id}",
                access_method=AccessMethod.RPC,
                authentication="none",
            ),
            authority_metadata=(
                AuthoritySeed(
                    claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                    tier=AuthorityTier.PRIMARY,
                    valid_from=NOW,
                    policy_version="book5-fixture-v1",
                ),
            ),
            verification_status=VerificationStatus.VERIFIED,
            verification_evidence_refs=(f"{claim_id}-source-verification",),
            last_verified_at=NOW,
        )
    )
    corroboration_evidence_ref = provenance.evidence_store.capture(
        source_id=corroboration_source_id,
        retrieved_at=NOW,
        content=f"book5 evidence {claim_id}-corroboration".encode(),
        content_locator=f"fixture://book5/{claim_id}-corroboration",
        raw_snapshot_ref=f"snapshot://book5/{claim_id}-corroboration",
        extractor_version="test",
        parser_version="test",
    ).evidence_id
    corroborating_id = f"{claim_id}-corroborating"
    corroborating = provenance.claim_store.require(claim_id).model_copy(
        update={
            "claim_id": corroborating_id,
            "evidence_refs": (corroboration_evidence_ref,),
            "source_refs": (corroboration_source_id,),
            "claim_state": ClaimState.OBSERVED,
        }
    )
    provenance.claim_store.add_initial(corroborating)
    assert same_proposition(
        provenance.claim_store.require(claim_id).proposition,
        corroborating.proposition,
    )
    _transition_claim(
        provenance,
        claim_id,
        ClaimState.CORROBORATED,
        corroborating_claim_id=corroborating_id,
        triggering_evidence_refs=(corroboration_evidence_ref,),
    )


# ---------------------------------------------------------------------------
# kernels — subject claim A current, basis claim B decays
# ---------------------------------------------------------------------------


def _component_kernel(tag: str, *, basis_claims: int = 1):
    """Subject PRINCIPAL_EXACT_FACT claim + ClaimContextBinding whose basis
    refs are ``basis_claims`` separate current OBSERVED claims."""

    _, _, provenance = kernel()
    subject = _register_economics_claim(
        provenance, f"{tag}-subject", qualifier="PRINCIPAL_EXACT_FACT"
    )
    basis = tuple(
        _register_economics_claim(provenance, f"{tag}-basis-{index}")
        for index in range(basis_claims)
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=subject,
            basis_claim_refs=basis,
            asset_ref="csia:token:eth",
            unit="ETH",
        )
    )
    return provenance, subject, basis


def _flow_kernel_with_basis(tag: str, *, basis_claims: int = 1):
    _, _, provenance = kernel()
    subject = _register_economics_claim(provenance, f"{tag}-subject")
    basis = tuple(
        _register_economics_claim(provenance, f"{tag}-basis-{index}")
        for index in range(basis_claims)
    )
    provenance.bind_quantitative_record_context(
        QuantitativeRecordContextBinding(
            claim_id=subject,
            record_kind="FLOW",
            basis_claim_refs=basis,
            asset_ref="csia:token:eth",
            unit="ETH",
        )
    )
    return provenance, subject, basis


def _liability_kernel_with_basis(tag: str, *, basis_claims: int = 1):
    _, _, provenance = kernel()
    subject = _register_economics_claim(provenance, f"{tag}-subject")
    basis = tuple(
        _register_economics_claim(provenance, f"{tag}-basis-{index}")
        for index in range(basis_claims)
    )
    provenance.bind_quantitative_record_context(
        QuantitativeRecordContextBinding(
            claim_id=subject,
            record_kind="LIABILITY",
            basis_claim_refs=basis,
            asset_ref="csia:token:usdc",
            unit="USDC",
            site_ref="csia:site:market-1",
        )
    )
    return provenance, subject, basis


def _fact_kernel_with_basis(tag: str, *, basis_claims: int = 1):
    _, _, provenance = kernel()
    subject = _register_economics_claim(provenance, f"{tag}-subject")
    basis = tuple(
        _register_economics_claim(provenance, f"{tag}-basis-{index}")
        for index in range(basis_claims)
    )
    provenance.bind_quantitative_record_context(
        QuantitativeRecordContextBinding(
            claim_id=subject,
            record_kind="OBSERVED_FACT",
            basis_claim_refs=basis,
            subject_ref="csia:stablecoin:fxd",
            numeraire="USD",
        )
    )
    return provenance, subject, basis


def _make_flow(flow_id: str, *, claim_ref: str) -> CapitalFlow:
    return CapitalFlow(
        flow_id=flow_id,
        flow_type=FlowType.TRANSFER,
        asset_ref="csia:token:eth",
        realization_ref=None,
        quantity="1",
        unit="ETH",
        from_location=EconomicLocation(
            location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"
        ),
        to_location=EconomicLocation(
            location_type=LocationType.ONCHAIN_ACCOUNT, ref="b"
        ),
        valid_time=T0,
        observed_at=T0,
        book2_claim_refs=(claim_ref,),
    )


def _make_liability(liability_id: str, *, claim_ref: str) -> DebtLiability:
    return DebtLiability(
        liability_id=liability_id,
        market_site_id="csia:site:market-1",
        asset_ref="csia:token:usdc",
        quantity="800",
        unit="USDC",
        book2_claim_refs=(claim_ref,),
        valid_time=T0,
    )


def _make_fact(fact_id: str, *, claim_ref: str) -> ObservedCommonValueFact:
    return ObservedCommonValueFact(
        fact_id=fact_id,
        reported_value="40000000000",
        numeraire="USD",
        reporter_ref="csia:entity:issuer",
        subject_ref="csia:stablecoin:fxd",
        observed_at=T0,
        valid_time=T0,
        book2_claim_refs=(claim_ref,),
    )


# ---------------------------------------------------------------------------
# R5-D1 / Phase 1 — component binding-basis decay (A1–A4, A5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", DECAY_STATES, ids=lambda s: s.value)
def test_a1_component_basis_decay_aggregate_rejects(state: ClaimState) -> None:
    """A1-A4: subject claim A stays OBSERVED; binding basis claim B decays —
    ``aggregate_same_unit`` must REJECT (today it PASSES: the R5-D1 defect)."""

    provenance, subject, (basis,) = _component_kernel("a")
    _decay(provenance, basis, state)
    assert (
        provenance.claim_store.require(subject).claim_state is ClaimState.OBSERVED
    )
    vectors = component_set(component(claim_ref=subject))
    with pytest.raises(Book5ProvenanceError):
        vectors.aggregate_same_unit("ETH", provenance=provenance)


def test_a5_component_basis_current_passes() -> None:
    """A5: subject current + basis current → the aggregate PASSES (the seal
    never blocks live authority)."""

    provenance, subject, (basis,) = _component_kernel("a5")
    vectors = component_set(component(claim_ref=subject))
    assert vectors.aggregate_same_unit("ETH", provenance=provenance) == "3"


# ---------------------------------------------------------------------------
# R5-D2 / Phase 2 — quantitative binding-basis decay (B1–B4)
# ---------------------------------------------------------------------------


def test_b1_flow_basis_stale_compose_rejects() -> None:
    """B1: FLOW binding basis STALE → ``compose_snapshot`` REJECT (today it
    PASSES: the R5-D2 defect)."""

    provenance, subject, (basis,) = _flow_kernel_with_basis("b1")
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:b1",
            flows=(_make_flow("flow:b1", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_b2_liability_basis_stale_compose_rejects() -> None:
    """B2: LIABILITY binding basis STALE → ``compose_snapshot`` REJECT."""

    provenance, subject, (basis,) = _liability_kernel_with_basis("b2")
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:b2",
            liabilities=(_make_liability("liability:b2", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_b3_fact_basis_stale_compose_rejects() -> None:
    """B3: OBSERVED_FACT binding basis STALE → ``compose_snapshot`` REJECT."""

    provenance, subject, (basis,) = _fact_kernel_with_basis("b3")
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:b3",
            observed_value_facts=(_make_fact("fact:b3", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_b4_fact_basis_stale_display_rejects() -> None:
    """B4: OBSERVED_FACT binding basis STALE → ``observed_value_display``
    REJECT (today it PASSES: the R5-D2 defect)."""

    provenance, subject, (basis,) = _fact_kernel_with_basis("b4")
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(_make_fact("fact:b4", claim_ref=subject))


# ---------------------------------------------------------------------------
# Phase 3 — subject vs basis currentness are independently required
# ---------------------------------------------------------------------------


def test_c1_component_subject_stale_basis_current_rejects() -> None:
    """C1: subject STALE, basis current → REJECT (existing subject seal;
    pinned so basis sealing never replaces subject sealing)."""

    provenance, subject, (basis,) = _component_kernel("c1")
    _transition_claim(provenance, subject, ClaimState.STALE)
    vectors = component_set(component(claim_ref=subject))
    with pytest.raises(Book5ProvenanceError):
        vectors.aggregate_same_unit("ETH", provenance=provenance)


def test_c2_component_subject_current_basis_stale_rejects() -> None:
    """C2: subject OBSERVED, basis STALE → REJECT (today it PASSES — the
    R5-D1 defect: SUBJECT CURRENT != BASIS CURRENT)."""

    provenance, subject, (basis,) = _component_kernel("c2")
    _decay(provenance, basis, ClaimState.STALE)
    vectors = component_set(component(claim_ref=subject))
    with pytest.raises(Book5ProvenanceError):
        vectors.aggregate_same_unit("ETH", provenance=provenance)


def test_c3_component_subject_stale_basis_stale_rejects() -> None:
    """C3: both decayed → REJECT."""

    provenance, subject, (basis,) = _component_kernel("c3")
    _transition_claim(provenance, subject, ClaimState.STALE)
    _decay(provenance, basis, ClaimState.STALE)
    vectors = component_set(component(claim_ref=subject))
    with pytest.raises(Book5ProvenanceError):
        vectors.aggregate_same_unit("ETH", provenance=provenance)


def test_c4_component_subject_current_basis_current_passes() -> None:
    """C4: both current → PASS."""

    provenance, subject, (basis,) = _component_kernel("c4")
    vectors = component_set(component(claim_ref=subject))
    assert vectors.aggregate_same_unit("ETH", provenance=provenance) == "3"


def test_q1_flow_subject_stale_basis_current_rejects() -> None:
    """Q1: quantitative family — subject STALE, basis current → REJECT."""

    provenance, subject, (basis,) = _flow_kernel_with_basis("q1")
    _transition_claim(provenance, subject, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:q1",
            flows=(_make_flow("flow:q1", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_q2_flow_subject_current_basis_stale_rejects() -> None:
    """Q2: quantitative family — subject OBSERVED, basis STALE → REJECT
    (today it PASSES — the R5-D2 defect)."""

    provenance, subject, (basis,) = _flow_kernel_with_basis("q2")
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:q2",
            flows=(_make_flow("flow:q2", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_q3_flow_subject_stale_basis_stale_rejects() -> None:
    """Q3: both decayed → REJECT."""

    provenance, subject, (basis,) = _flow_kernel_with_basis("q3")
    _transition_claim(provenance, subject, ClaimState.STALE)
    _decay(provenance, basis, ClaimState.STALE)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:q3",
            flows=(_make_flow("flow:q3", claim_ref=subject),),
            valid_time=T0,
            observed_at=T1,
        )


def test_q4_flow_subject_current_basis_current_passes() -> None:
    """Q4: both current → PASS."""

    provenance, subject, (basis,) = _flow_kernel_with_basis("q4")
    synthesis = CapitalFieldSynthesis(provenance)
    snapshot = synthesis.compose_snapshot(
        "snap:q4",
        flows=(_make_flow("flow:q4", claim_ref=subject),),
        valid_time=T0,
        observed_at=T1,
    )
    assert snapshot.input_record_refs == ("flow:q4",)
