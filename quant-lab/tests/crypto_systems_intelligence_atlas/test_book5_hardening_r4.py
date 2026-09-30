"""Book 5 HARDENING R4 — registry/derived-ref authority decay seal.

Defect class under test (operator-reported, demonstrated failure-first):

R4-D1   ``Book5CanonicalRecordRegistry.resolve`` checks only dict membership
        and record kind. Registration validates the underlying Book 2 claims
        ONCE, at registration time. If a registered record's Book 2 claim is
        later transitioned out of the current graph-promotable states
        (OBSERVED/CORROBORATED/INFERRED basis) into CONTESTED, STALE,
        REJECTED, or SUPERSEDED, the registry keeps accepting the stale
        entry: ``compose_path`` and ``topology_view`` still resolve it and
        5G mints a new ``derived=True`` artifact whose input pointers name
        data whose Book 2 authority is no longer current (E1–E16).

Central R4 invariant (Phases 1–3): NO STALE AUTHORITY THROUGH THE REGISTRY —
registry resolution is a LIVE Book 2 authority boundary, not a remembered
construction. The record itself is immutable, so its entry is never "fixed":
the only faithful resolution is to REJECT the ref the moment its Book 2
authority decays. ``compose_snapshot`` and ``observed_value_display``
already live-revalidate (R1/R2/R3); the path/topology/registry boundary is
closed here with the same single-epistemic-engine machinery.

Attack matrix (Phases 2–3): E1–E9 + E9b decay through the registry at every
surface; E16 isolates endpoint revalidation; E12 WRONG-KIND precedence; E13
resurrection (STALE → OBSERVED restores authority); E14/E15/E18 recovery
controls (CONTESTED → CORROBORATED via an independent-source transition,
fresh claims rebind and resolve, decay is per-claim not per-registry);
E10/E11 are single-engine controls (compose_snapshot and register() already
refuse decayed claims live); E17 pins registered_record as a
non-authoritative structural accessor; E19 fails closed on explicit-None
provenance; E20 pins registered_refs as structural, not authority.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from crypto_systems_intelligence_atlas.book5_lineage import DebtLiability
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
    QuantitativeRecordContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    CapitalFlow,
    CapitalPosition,
    FlowType,
    ObservedCommonValueFact,
    PositionKind,
    TransformationKind,
)
from crypto_systems_intelligence_atlas.book5_registry import (
    Book5CanonicalRecordRegistry,
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
from crypto_systems_intelligence_atlas.book5_core import EconomicLocation, LocationType
from crypto_systems_intelligence_atlas.claims import ClaimState, same_proposition
from crypto_systems_intelligence_atlas.evidence import EvidenceTier
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


# ---------------------------------------------------------------------------
# shared fixtures — canonical records registered while their claims are
# OBSERVED, exactly as in R3
# ---------------------------------------------------------------------------


def _register_economics_claim(
    provenance: Book5Provenance, tag: str, *, qualifier: str | None = None
) -> str:
    """Register one canonical evidenced Book 2 economics claim (OBSERVED)."""

    evidence_ref = make_evidence(provenance.evidence_store, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    provenance.claim_store.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, qualifier=qualifier)
    )
    return claim_id


def _bind_record_context(provenance: Book5Provenance, **dimensions: Any) -> None:
    provenance.bind_quantitative_record_context(
        QuantitativeRecordContextBinding(**dimensions)
    )


def _bind_flow_context(
    provenance: Book5Provenance,
    claim_id: str,
    *,
    asset_ref: str,
    unit: str,
    realization_ref: str | None = None,
) -> None:
    _bind_record_context(
        provenance,
        claim_id=claim_id,
        record_kind="FLOW",
        asset_ref=asset_ref,
        realization_ref=realization_ref,
        unit=unit,
    )


def _bind_fact_context(
    provenance: Book5Provenance,
    claim_id: str,
    *,
    subject_ref: str,
    numeraire: str,
    reporter_ref: str | None = None,
) -> None:
    _bind_record_context(
        provenance,
        claim_id=claim_id,
        record_kind="OBSERVED_FACT",
        subject_ref=subject_ref,
        numeraire=numeraire,
        reporter_ref=reporter_ref,
    )


def _make_position(position_id: str, *, claim_ref: str) -> CapitalPosition:
    """Canonical position whose refs DERIVE from its bound exact component."""

    return CapitalPosition(
        position_id=position_id,
        position_kind=PositionKind.CLAIM_SIDE,
        asset_ref="csia:token:lp",
        principal_components=component_set(component(claim_ref=claim_ref)),
        holder_ref=None,
        protocol_ref="csia:protocol:amm",
        site_ref="csia:site:pool-1",
        location=EconomicLocation(
            location_type=LocationType.POOL,
            ref="loc:1",
        ),
        quantity="1",
        unit="LP",
        valid_from=T0,
        observed_at=T0,
        book2_claim_refs=(claim_ref,),
    )


def _make_flow(
    flow_id: str, *, claim_ref: str, **overrides: Any
) -> CapitalFlow:
    base: dict[str, Any] = dict(
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
    base.update(overrides)
    return CapitalFlow(**base)


def _make_fact(
    fact_id: str, *, claim_ref: str, **overrides: Any
) -> ObservedCommonValueFact:
    base: dict[str, Any] = dict(
        fact_id=fact_id,
        reported_value="40000000000",
        numeraire="USD",
        reporter_ref="csia:entity:issuer",
        subject_ref="csia:stablecoin:fxd",
        observed_at=T0,
        valid_time=T0,
        book2_claim_refs=(claim_ref,),
    )
    base.update(overrides)
    return ObservedCommonValueFact(**base)


def _make_liability(
    liability_id: str, *, claim_ref: str, **overrides: Any
) -> DebtLiability:
    base: dict[str, Any] = dict(
        liability_id=liability_id,
        market_site_id="csia:site:market-1",
        asset_ref="csia:token:usdc",
        quantity="800",
        unit="USDC",
        book2_claim_refs=(claim_ref,),
        valid_time=T0,
    )
    base.update(overrides)
    return DebtLiability(**base)


def _make_transformation(
    transformation_id: str, *, claim_ref: str
) -> Any:
    from crypto_systems_intelligence_atlas.book5_records import (
        CapitalTransformation,
    )

    return CapitalTransformation(
        transformation_id=transformation_id,
        transformation_kind=TransformationKind.ASSET_TO_LP_CLAIM,
        input_claim_id="csia:claim:input",
        output_claim_id="csia:claim:output",
        principal_component_refs=("component:1",),
        valid_time=T0,
        observed_at=T0,
        book2_claim_refs=(claim_ref,),
    )


def _registry(*records: object) -> Book5CanonicalRecordRegistry:
    return Book5CanonicalRecordRegistry()


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
    """Transition the canonical claim through the accepted Book 2 engine."""

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


# ---------------------------------------------------------------------------
# decay fixtures — one per record kind
# ---------------------------------------------------------------------------


def _decay_position_fixture(new_state: ClaimState):
    """Register a canonical position while its claim is OBSERVED, then
    transition the claim to ``new_state`` through the accepted engine."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(
        provenance, "pos-exact", qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=claim_id,
            asset_ref="csia:token:eth",
            unit="ETH",
        )
    )
    position = _make_position("pos:decay", claim_ref=claim_id)
    registry = _registry()
    registry.register(position, provenance=provenance)
    assert registry.registered_count == 1
    _decay(provenance, claim_id, new_state)
    return provenance, registry, position, claim_id


def _decay_position_multi_claim_fixture(new_state: ClaimState):
    """Position whose entry carries TWO claim refs: the SECOND decays."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(
        provenance, "pos-exact", qualifier="PRINCIPAL_EXACT_FACT"
    )
    other_id = _register_economics_claim(
        provenance, "pos-exact-2", qualifier="PRINCIPAL_EXACT_FACT"
    )
    for ref in (claim_id, other_id):
        provenance.bind_claim_context(
            ClaimContextBinding(claim_id=ref, asset_ref="csia:token:eth", unit="ETH")
        )
    position = _make_position("pos:decay-multi", claim_ref=claim_id)
    tampered = position.model_copy(
        update={"book2_claim_refs": (claim_id, other_id)}
    )
    registry = _registry()
    registry.register(tampered, provenance=provenance)
    _decay(provenance, other_id, new_state)
    return provenance, registry, tampered, other_id


def _decay_flow_fixture(new_state: ClaimState):
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, "flow-decay")
    _bind_flow_context(
        provenance, claim_id, asset_ref="csia:token:eth", unit="ETH"
    )
    flow = _make_flow("flow:decay", claim_ref=claim_id)
    registry = _registry()
    registry.register(flow, provenance=provenance)
    _decay(provenance, claim_id, new_state)
    return provenance, registry, flow, claim_id


def _decay_fact_fixture(new_state: ClaimState):
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, "fact-decay")
    _bind_fact_context(
        provenance,
        claim_id,
        subject_ref="csia:stablecoin:fxd",
        numeraire="USD",
    )
    fact = _make_fact("fact:decay", claim_ref=claim_id)
    registry = _registry()
    registry.register(fact, provenance=provenance)
    _decay(provenance, claim_id, new_state)
    return provenance, registry, fact, claim_id


def _decay_liability_fixture(new_state: ClaimState):
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, "liab-decay")
    _bind_record_context(
        provenance,
        claim_id=claim_id,
        record_kind="LIABILITY",
        asset_ref="csia:token:usdc",
        unit="USDC",
        site_ref="csia:site:market-1",
    )
    liability = _make_liability("liability:decay", claim_ref=claim_id)
    registry = _registry()
    registry.register(liability, provenance=provenance)
    _decay(provenance, claim_id, new_state)
    return provenance, registry, liability, claim_id


def _decay_transformation_fixture(new_state: ClaimState):
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, "trans-decay")
    transformation = _make_transformation("transform:decay", claim_ref=claim_id)
    registry = _registry()
    registry.register(transformation, provenance=provenance)
    _decay(provenance, claim_id, new_state)
    return provenance, registry, transformation, claim_id


# ---------------------------------------------------------------------------
# R4-D1 / Phase 1 — the decay defect demonstrated on registry.resolve
# ---------------------------------------------------------------------------

DECAY_STATES = (
    ClaimState.CONTESTED,
    ClaimState.STALE,
    ClaimState.REJECTED,
    ClaimState.SUPERSEDED,
)


def _supersede(
    provenance: Book5Provenance, claim_id: str
) -> None:
    replacement_id = f"{claim_id}-replacement"
    provenance.claim_store.add_initial(
        make_claim(
            replacement_id,
            evidence_ref=make_evidence(
                provenance.evidence_store, f"{claim_id}-replacement-ev"
            ),
        )
    )
    _transition_claim(
        provenance,
        claim_id,
        ClaimState.SUPERSEDED,
        replacement_claim_id=replacement_id,
        supersession_reason="R4 decay fixture",
    )


def _decay(
    provenance: Book5Provenance, claim_id: str, new_state: ClaimState
) -> None:
    """Decay a claim to ``new_state`` through the accepted Book 2 engine,
    routing SUPERSEDED through its mandatory replacement-claim path."""

    if new_state is ClaimState.SUPERSEDED:
        _supersede(provenance, claim_id)
    else:
        _transition_claim(provenance, claim_id, new_state)


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e1_stale_position_registry_resolve_rejects(new_state: ClaimState) -> None:
    """E1: valid position registered while OBSERVED → claim decays →
    ``registry.resolve`` must REJECT (today it accepts)."""

    provenance, registry, position, claim_id = _decay_position_fixture(new_state)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            position.position_id, expected_kind="position", provenance=provenance
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e2_stale_position_compose_path_rejects(new_state: ClaimState) -> None:
    """E2: the stale position must not become a derived path stage —
    ``compose_path`` must REJECT (today it emits ``derived=True``)."""

    provenance, registry, position, claim_id = _decay_position_fixture(new_state)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_path(
            "path:e2",
            stage_record_refs=(position.position_id,),
            valid_time=T0,
            observed_at=T1,
            registry=registry,
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e3_stale_position_topology_node_rejects(new_state: ClaimState) -> None:
    """E3: the stale position must not become a topology node —
    ``topology_view`` must REJECT (today it emits ``derived=True``)."""

    provenance, registry, position, claim_id = _decay_position_fixture(new_state)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:e3",
            node_record_refs=(position.position_id,),
            valid_time=T0,
            observed_at=T1,
            registry=registry,
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e4_one_decayed_claim_poisons_the_whole_entry(new_state: ClaimState) -> None:
    """E4: an entry with TWO claim refs decays only through its second ref —
    resolution must still REJECT (today it accepts)."""

    provenance, registry, position, claim_id = _decay_position_multi_claim_fixture(
        new_state
    )
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            position.position_id, expected_kind="position", provenance=provenance
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e5_stale_flow_registry_resolve_rejects(new_state: ClaimState) -> None:
    """E5: registered canonical flow → claim decays → resolve REJECT."""

    provenance, registry, flow, claim_id = _decay_flow_fixture(new_state)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            flow.flow_id, expected_kind="flow", provenance=provenance
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e6_stale_flow_topology_edge_rejects(new_state: ClaimState) -> None:
    """E6: the stale flow must not become a topology edge —
    ``topology_view`` must REJECT (today it emits ``derived=True``)."""

    provenance, registry, flow, claim_id = _decay_flow_fixture(new_state)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:e6",
            node_record_refs=("pos:unrelated",),
            edge_flow_refs=(flow.flow_id,),
            valid_time=T0,
            observed_at=T1,
            registry=registry,
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e7_stale_fact_registry_resolve_rejects(new_state: ClaimState) -> None:
    """E7: registered canonical observed fact → claim decays → resolve
    REJECT (today it accepts)."""

    provenance, registry, fact, claim_id = _decay_fact_fixture(new_state)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            fact.fact_id, expected_kind="observed_fact", provenance=provenance
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e8_stale_fact_display_rejects(new_state: ClaimState) -> None:
    """E8: a stale fact must not display — ``observed_value_display``
    already live-revalidates claim currency (R3 seal); pinned here against
    the decay engine for every non-promotable target state."""

    provenance, registry, fact, claim_id = _decay_fact_fixture(new_state)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(fact)


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e9_stale_liability_registry_resolve_rejects(new_state: ClaimState) -> None:
    """E9: registered canonical liability → claim decays → resolve REJECT."""

    provenance, registry, liability, claim_id = _decay_liability_fixture(new_state)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            liability.liability_id, expected_kind="liability", provenance=provenance
        )


@pytest.mark.parametrize(
    "new_state", DECAY_STATES, ids=lambda s: s.value
)
def test_e9b_stale_transformation_registry_resolve_rejects(
    new_state: ClaimState,
) -> None:
    """E9b: registered canonical transformation → claim decays → resolve
    REJECT (today it accepts)."""

    provenance, registry, transformation, claim_id = _decay_transformation_fixture(
        new_state
    )
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            transformation.transformation_id,
            expected_kind="transformation",
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# R4-D1 / Phase 2 — decay attack matrix
# ---------------------------------------------------------------------------


def test_e10_decayed_claim_refused_at_registration() -> None:
    """E10 (single-engine control): a decayed claim cannot ENTER the
    registry at all — ``register`` live-validates through Book 2 and
    REJECTS (already sealed; pinned so the resolve seal never regresses
    into a registration-only check)."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(
        provenance, "e10-exact", qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:eth", unit="ETH")
    )
    position = _make_position("pos:e10", claim_ref=claim_id)
    _transition_claim(provenance, claim_id, ClaimState.REJECTED)
    registry = _registry()
    with pytest.raises(Book5ProvenanceError):
        registry.register(position, provenance=provenance)
    assert registry.registered_count == 0


def test_e11_decayed_flow_refused_at_compose_snapshot() -> None:
    """E11 (single-engine control): the decayed flow cannot enter 5G through
    ``compose_snapshot`` either — that boundary already live-revalidates
    claim currency (R3); pinned here against the same decay engine."""

    provenance, registry, flow, claim_id = _decay_flow_fixture(
        ClaimState.REJECTED
    )
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:e11", flows=(flow,), valid_time=T0, observed_at=T1
        )


def test_e12_wrong_kind_error_precedes_stale_authority_check() -> None:
    """E12: WRONG-KIND stays a WRONG-KIND rejection even when the entry is
    also stale — kind identity never leaks authority across namespaces."""

    provenance, registry, flow, claim_id = _decay_flow_fixture(
        ClaimState.REJECTED
    )
    with pytest.raises(Book5ProvenanceError) as excinfo:
        registry.resolve(
            flow.flow_id, expected_kind="position", provenance=provenance
        )
    assert "WRONG-KIND" in str(excinfo.value)


def test_e13_stale_then_resharpened_claim_restores_resolution() -> None:
    """E13 (R4 PASS row): decay is LIVE, not a one-way tombstone — STALE →
    OBSERVED (a ratified transition) restores resolution of the same
    immutable record, because the seal mirrors Book 2 state exactly rather
    than remembering a rejection."""

    provenance, registry, position, claim_id = _decay_position_fixture(
        ClaimState.STALE
    )
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            position.position_id, expected_kind="position", provenance=provenance
        )
    _transition_claim(provenance, claim_id, ClaimState.OBSERVED, at=T1)
    resolved = registry.resolve(
        position.position_id, expected_kind="position", provenance=provenance
    )
    assert resolved.record_kind == "position"


def test_e14_contested_then_recorroborated_claim_restores_resolution() -> None:
    """E14 (R4 PASS row): CONTESTED → CORROBORATED through the accepted
    Book 2 engine (P-4: independent source, owner, and mechanism; matching
    proposition) restores resolution — graph-promotable again, same record,
    no rebind."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(
        provenance, "e14-exact", qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:eth", unit="ETH")
    )
    position = _make_position("pos:e14", claim_ref=claim_id)
    registry = _registry()
    registry.register(position, provenance=provenance)
    _transition_claim(provenance, claim_id, ClaimState.CONTESTED)

    # P-4 corroboration: distinct source, distinct owner, distinct mechanism.
    corroboration_source_id = "csia:source:e14-independent"
    provenance.evidence_store._source_registry.register(
        Source(
            source_id=corroboration_source_id,
            source_class=SourceClass.NATIVE_TECHNICAL,
            canonical_name="e14 independent corroborating fixture",
            owner_entity_ref="csia:entity:e14-owner",
            object_scope=(),
            locator=LocatorMetadata(
                base_locator="fixture://book5/e14",
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
            verification_evidence_refs=("e14-source-verification",),
            last_verified_at=NOW,
        )
    )
    # The corroborating claim's evidence is captured THROUGH the distinct
    # source (a separate registry entry with its own owner and RPC mechanism),
    # so P-4 sees a genuinely independent corroboration path.
    corroboration_evidence_ref = provenance.evidence_store.capture(
        source_id=corroboration_source_id,
        retrieved_at=NOW,
        content=b"book5 evidence e14-corroboration",
        content_locator="fixture://book5/e14-corroboration",
        raw_snapshot_ref="snapshot://book5/e14-corroboration",
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id
    corroborating_id = f"{claim_id}-corroborating"
    # proposition equivalence (same_proposition) requires the SAME structured
    # proposition — corroborating claim = original claim re-sourced.
    corroborating = provenance.claim_store.require(claim_id).model_copy(
        update={
            "claim_id": corroborating_id,
            "evidence_refs": (corroboration_evidence_ref,),
            "source_refs": (corroboration_source_id,),
            "claim_state": ClaimState.OBSERVED,
        }
    )
    provenance.claim_store.add_initial(corroborating)
    _transition_claim(
        provenance,
        claim_id,
        ClaimState.CORROBORATED,
        corroborating_claim_id=corroborating_id,
        triggering_evidence_refs=(corroboration_evidence_ref,),
    )
    assert (
        provenance.claim_store.require(claim_id).claim_state
        is ClaimState.CORROBORATED
    )
    assert same_proposition(
        provenance.claim_store.require(claim_id).proposition,
        provenance.claim_store.require(corroborating_id).proposition,
    )
    resolved = registry.resolve(
        position.position_id, expected_kind="position", provenance=provenance
    )
    assert resolved.record_kind == "position"


def test_e15_rebinding_with_fresh_claim_restores_resolution() -> None:
    """E15 (recovery control): after REJECTED, a NEW evidenced claim can be
    context-bound and minted into a new canonical record that resolves —
    the decay seal never blocks fresh canonical authority."""

    provenance, registry, liability, claim_id = _decay_liability_fixture(
        ClaimState.REJECTED
    )
    fresh_claim_id = _register_economics_claim(provenance, "e15-fresh")
    _bind_record_context(
        provenance,
        claim_id=fresh_claim_id,
        record_kind="LIABILITY",
        asset_ref="csia:token:usdc",
        unit="USDC",
        site_ref="csia:site:market-1",
    )
    fresh_liability = _make_liability("liability:e15", claim_ref=fresh_claim_id)
    registry.register(fresh_liability, provenance=provenance)
    resolved = registry.resolve(
        fresh_liability.liability_id,
        expected_kind="liability",
        provenance=provenance,
    )
    assert resolved.record_kind == "liability"


def test_e16_edge_to_position_whose_claim_decayed_rejects() -> None:
    """E16: the edge flow's own claim is healthy, but its canonical position
    endpoint is a registry entry whose Book 2 claim decayed — endpoint
    resolution revalidates live and REJECTS (today it accepts)."""

    _, _, provenance = kernel()
    pos_claim_id = _register_economics_claim(
        provenance, "e16-pos", qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=pos_claim_id, asset_ref="csia:token:eth", unit="ETH"
        )
    )
    position = _make_position("pos:e16", claim_ref=pos_claim_id)
    flow_claim_id = _register_economics_claim(provenance, "e16-flow")
    _bind_flow_context(
        provenance, flow_claim_id, asset_ref="csia:token:eth", unit="ETH"
    )
    flow = _make_flow(
        "flow:e16", claim_ref=flow_claim_id, from_position=position.position_id
    )
    registry = _registry()
    registry.register(position, provenance=provenance)
    registry.register(flow, provenance=provenance)
    _decay(provenance, pos_claim_id, ClaimState.REJECTED)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:e16",
            node_record_refs=(position.position_id,),
            edge_flow_refs=(flow.flow_id,),
            valid_time=T0,
            observed_at=T1,
            registry=registry,
        )


# ---------------------------------------------------------------------------
# R4-D1 / Phase 3 — recovery controls and the structural-accessor contract
# ---------------------------------------------------------------------------


def test_e17_registered_record_stays_structural_only() -> None:
    """E17: ``registered_record`` must stay a NON-authoritative structural
    accessor: it returns the registered object even after the claim decays,
    and its docstring contract (inspection only, never revalidated state)
    stays intact. Authority flows only through resolve/compose boundaries."""

    provenance, registry, position, claim_id = _decay_position_fixture(
        ClaimState.REJECTED
    )
    structural = registry.registered_record(position.position_id)
    assert structural is position
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            position.position_id, expected_kind="position", provenance=provenance
        )


def test_e18_healthy_entry_still_resolves_after_unrelated_decay() -> None:
    """E18 (recovery control): decay is per-claim, not per-registry — an
    unrelated entry whose claims remain current keeps resolving after a
    sibling entry's claim decays."""

    _, _, provenance = kernel()
    claim_a = _register_economics_claim(
        provenance, "e18-a", qualifier="PRINCIPAL_EXACT_FACT"
    )
    claim_b = _register_economics_claim(
        provenance, "e18-b", qualifier="PRINCIPAL_EXACT_FACT"
    )
    for ref in (claim_a, claim_b):
        provenance.bind_claim_context(
            ClaimContextBinding(claim_id=ref, asset_ref="csia:token:eth", unit="ETH")
        )
    position_a = _make_position("pos:e18-a", claim_ref=claim_a)
    position_b = _make_position("pos:e18-b", claim_ref=claim_b)
    registry = _registry()
    registry.register(position_a, provenance=provenance)
    registry.register(position_b, provenance=provenance)
    _transition_claim(provenance, claim_a, ClaimState.REJECTED)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(
            position_a.position_id, expected_kind="position", provenance=provenance
        )
    resolved = registry.resolve(
        position_b.position_id, expected_kind="position", provenance=provenance
    )
    assert resolved.record_kind == "position"


def test_e19_resolve_requires_explicit_provenance() -> None:
    """E19: the R2/R3 mandatory-authority pattern — resolution without an
    explicit Book 2 authority context is refused outright (fail closed,
    no remembered-construction fallback, no default resolver)."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(
        provenance, "e19-exact", qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:eth", unit="ETH")
    )
    position = _make_position("pos:e19", claim_ref=claim_id)
    registry = _registry()
    registry.register(position, provenance=provenance)
    with pytest.raises(Book5ProvenanceError):
        registry.resolve(  # type: ignore[arg-type]
            position.position_id,
            expected_kind="position",
            provenance=None,
        )


def test_e20_registered_refs_reports_resolution_health_not_acceptance() -> None:
    """E20: ``registered_refs`` stays a deterministic structural snapshot —
    the decay seal lives at the authority boundary (resolve), so the
    snapshot is unchanged by a decayed claim (structural ≠ authority)."""

    provenance, registry, position, claim_id = _decay_position_fixture(
        ClaimState.REJECTED
    )
    assert registry.registered_refs("position") == (position.position_id,)
