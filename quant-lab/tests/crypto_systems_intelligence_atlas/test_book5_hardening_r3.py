"""Book 5 HARDENING R3 — derived-reference closure + non-component context.

Defect classes under test, each demonstrated against the R2-hardened kernel:

R3-D1   ``CapitalFieldSynthesis.compose_path`` checks only
        ``len(stage_record_refs) > 0`` — arbitrary strings become a
        ``derived=True`` CapitalFieldPath (A1–A5).
R3-D2   ``topology_view`` checks only that ``node_record_refs`` is non-empty —
        forged node/edge refs become a derived CapitalTopologyView (B1–B5).
R3-D3   ``observed_value_display`` renders fields directly without live
        validation, so a ``model_copy``-mutated fact bypasses the R2 seal
        (C1–C5).
R3-D4   the 5G validators for CapitalFlow / DebtLiability /
        ObservedCommonValueFact call only ``resolve_claim_refs`` — claims
        exist and are evidenced, but the record's asset/unit/site/numeraire
        context is never verified against a binding (D1–D12).

Central R3 invariant (Phases 5–12): NO BINDING != CONTEXT VERIFIED, and
NO ARBITRARY STRING MAY BECOME DERIVED 5G AUTHORITY — every 5G pointer
resolves through a canonical Book 5 record registry at decision time.

Phase 12 adds the model_copy R3 attack matrix (P/T/F/L/O): every
authority-producing path revalidates live state, so a ``model_copy``-
tampered artifact is inert data — its refs cannot re-enter the authority
boundary that produced it.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    EconomicLocation,
    LocationType,
)
from crypto_systems_intelligence_atlas.book5_lineage import DebtLiability
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    CapitalFlow,
    CapitalPosition,
    FlowType,
    ObservedCommonValueFact,
    PositionKind,
)
from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis
from crypto_systems_intelligence_atlas.book5_support import (
    NOW,
    component,
    component_set,
    kernel,
    make_claim,
    make_evidence,
)

T0 = NOW

FAKE_REF = "fake:issuance"
GHOST_NODE = "ghost:node"
GHOST_FLOW = "ghost:flow"


# ---------------------------------------------------------------------------
# shared fixtures — canonical records registered on the R2-sealed kernel
# ---------------------------------------------------------------------------


def _register_economics_claim(
    provenance: Book5Provenance, tag: str, *, qualifier: str | None = None
) -> str:
    """Register one canonical evidenced Book 2 economics claim."""

    evidence_ref = make_evidence(provenance.evidence_store, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    provenance.claim_store.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, qualifier=qualifier)
    )
    return claim_id


def _bound_exact(
    provenance: Book5Provenance,
    tag: str,
    *,
    asset_ref: str,
    unit: str,
    realization_ref: str | None = None,
) -> str:
    """Register a canonical PRINCIPAL_EXACT_FACT claim + R2 context binding
    (the position/component authority machinery from R2, unchanged)."""

    claim_id = _register_economics_claim(
        provenance, tag, qualifier="PRINCIPAL_EXACT_FACT"
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=claim_id,
            asset_ref=asset_ref,
            realization_ref=realization_ref,
            unit=unit,
        )
    )
    return claim_id


def _bind_record_context(provenance: Book5Provenance, **dimensions: Any) -> str:
    """Bind non-component quantitative context via the R3 target API."""

    from crypto_systems_intelligence_atlas.book5_provenance import (
        QuantitativeRecordContextBinding,
    )

    binding = QuantitativeRecordContextBinding(**dimensions)
    provenance.bind_quantitative_record_context(binding)
    return binding.claim_id


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


def _bind_liability_context(
    provenance: Book5Provenance,
    claim_id: str,
    *,
    asset_ref: str,
    unit: str,
    site_ref: str,
) -> None:
    _bind_record_context(
        provenance,
        claim_id=claim_id,
        record_kind="LIABILITY",
        asset_ref=asset_ref,
        unit=unit,
        site_ref=site_ref,
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


def _flow_kernel(
    tag: str,
    *,
    asset_ref: str = "csia:token:eth",
    unit: str = "ETH",
    realization_ref: str | None = None,
) -> tuple[Book5Provenance, str]:
    """Kernel whose stores carry a flow-context-bound economics claim."""

    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, tag)
    _bind_flow_context(
        provenance,
        claim_id,
        asset_ref=asset_ref,
        unit=unit,
        realization_ref=realization_ref,
    )
    return provenance, claim_id


def _liability_kernel(
    tag: str,
    *,
    asset_ref: str = "csia:token:usdc",
    unit: str = "USDC",
    site_ref: str = "csia:site:market-1",
) -> tuple[Book5Provenance, str]:
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, tag)
    _bind_liability_context(
        provenance, claim_id, asset_ref=asset_ref, unit=unit, site_ref=site_ref
    )
    return provenance, claim_id


def _fact_kernel(
    tag: str,
    *,
    subject_ref: str = "csia:stablecoin:fxd",
    numeraire: str = "USD",
    reporter_ref: str | None = None,
) -> tuple[Book5Provenance, str]:
    _, _, provenance = kernel()
    claim_id = _register_economics_claim(provenance, tag)
    _bind_fact_context(
        provenance,
        claim_id,
        subject_ref=subject_ref,
        numeraire=numeraire,
        reporter_ref=reporter_ref,
    )
    return provenance, claim_id


def _make_flow(
    flow_id: str = "flow:r3",
    *,
    claim_ref: str = "book5-claim-eth",
    **overrides: Any,
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


def _make_liability(
    liability_id: str = "liability:r3",
    *,
    claim_ref: str = "book5-claim-usdc",
    **overrides: Any,
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


def _make_fact(
    fact_id: str = "fact:r3",
    *,
    claim_ref: str = "book5-claim-base",
    **overrides: Any,
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
        location=EconomicLocation(location_type=LocationType.POOL, ref="loc:1"),
        quantity="1",
        unit="LP",
        valid_from=T0,
        observed_at=T0,
        book2_claim_refs=(claim_ref,),
    )


def _registry_with(provenance: Book5Provenance, *records: object) -> Any:
    """Build the R3 canonical registry and register validated records."""

    from crypto_systems_intelligence_atlas.book5_registry import (
        Book5CanonicalRecordRegistry,
    )

    registry = Book5CanonicalRecordRegistry()
    for record in records:
        registry.register(record, provenance=provenance)
    return registry


def _refuses_derived_output(
    call: Callable[[], object], *, reason: str
) -> None:
    """Failure-first assertion: the call must raise the typed rejection.

    Today the call still succeeds and the AssertionError escapes the
    ``pytest.raises`` box (the row FAILS, demonstrating the live defect);
    after the R3 seal lands, ``Book5ProvenanceError`` is raised and caught
    (the row PASSES). The defective artifact never escapes the box.
    """

    with pytest.raises(Book5ProvenanceError):
        call()
        raise AssertionError(f"defect still live: {reason}")


# ---------------------------------------------------------------------------
# R3-D1 / Phase 1 — path reference forgeability (A1–A5)
# ---------------------------------------------------------------------------


def test_a1_fake_stage_ref_produces_derived_path_today_reject_required() -> None:
    """A1: compose_path with entirely fake stage refs currently PRODUCES a
    derived=True path; after the R3 seal it must REJECT."""

    _, _, provenance = kernel()
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.compose_path(
            "path:a1",
            stage_record_refs=(FAKE_REF, "fake:credit", "fake:exit"),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance),
        ),
        reason="fake stage refs produced a derived path",
    )


def test_a2_mixed_canonical_and_fake_stage_refs_rejected() -> None:
    """A2: one fake ref smuggled among canonical refs must REJECT — mixing
    cannot launder a forged pointer."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "a2-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:a2", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.compose_path(
            "path:a2",
            stage_record_refs=(position.position_id, "fake:exit"),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance, position),
        ),
        reason="mixed fake ref produced a derived path",
    )


def test_a3_duplicate_stage_ref_rejected() -> None:
    """A3: the same ref repeated to fake a multi-stage path must REJECT —
    no ratified semantics allow duplicate path stages."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "a3-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:a3", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.compose_path(
            "path:a3",
            stage_record_refs=(position.position_id, position.position_id),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance, position),
        ),
        reason="duplicate ref faked a multi-stage path",
    )


def test_a4_empty_path_rejected() -> None:
    """A4: empty stage list REJECT (preserve existing behavior)."""

    _, _, provenance = kernel()
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_path(
            "path:a4",
            stage_record_refs=(),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance),
        )


def test_a5_all_canonical_stage_refs_pass() -> None:
    """A5: every stage ref resolves to a canonical registered Book 5 record
    → PASS with the derived mark intact."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "a5-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:a5", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    path = synthesis.compose_path(
        "path:a5",
        stage_record_refs=(position.position_id,),
        valid_time=T0,
        observed_at=T0,
        registry=_registry_with(provenance, position),
    )
    assert path.derived is True
    assert path.stage_record_refs == (position.position_id,)


# ---------------------------------------------------------------------------
# R3-D2 / Phase 2 — topology reference forgeability (B1–B5)
# ---------------------------------------------------------------------------


def test_b1_unknown_node_ref_rejected() -> None:
    """B1: a node ref that resolves to nothing must REJECT (today: PASS)."""

    _, _, provenance = kernel()
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.topology_view(
            "topo:b1",
            node_record_refs=(GHOST_NODE,),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance),
        ),
        reason="unknown node ref produced a derived topology",
    )


def test_b2_unknown_edge_flow_ref_rejected() -> None:
    """B2: an edge_flow_ref that resolves to nothing must REJECT."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "b2-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:b2", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.topology_view(
            "topo:b2",
            node_record_refs=(position.position_id,),
            edge_flow_refs=(GHOST_FLOW,),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance, position),
        ),
        reason="unknown flow ref produced a derived topology",
    )


def test_b3_mixed_canonical_nodes_and_forged_flow_rejected() -> None:
    """B3: canonical nodes + one forged flow ref → REJECT."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "b3-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:b3", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.topology_view(
            "topo:b3",
            node_record_refs=(position.position_id, GHOST_NODE),
            edge_flow_refs=(GHOST_FLOW,),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance, position),
        ),
        reason="forged flow produced a derived topology",
    )


def test_b4_duplicate_node_ref_rejected() -> None:
    """B4: duplicated node refs (fake fan-out) → REJECT under the explicit
    ratified rule: topology nodes are unique."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(provenance, "b4-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:b4", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    _refuses_derived_output(
        lambda: synthesis.topology_view(
            "topo:b4",
            node_record_refs=(position.position_id, position.position_id),
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(provenance, position),
        ),
        reason="duplicate node faked a two-node topology",
    )


def test_b5_all_canonical_nodes_and_flows_pass() -> None:
    """B5: canonical registered nodes + flows → PASS."""

    _, _, provenance = kernel()
    pos_claim = _bound_exact(provenance, "b5-exact", asset_ref="csia:token:eth", unit="ETH")
    position = _make_position("pos:b5", claim_ref=pos_claim)
    flow_claim = _register_economics_claim(provenance, "b5-flow")
    _bind_flow_context(
        provenance, flow_claim, asset_ref="csia:token:eth", unit="ETH"
    )
    flow = _make_flow("flow:b5", claim_ref=flow_claim)
    synthesis = CapitalFieldSynthesis(provenance)
    view = synthesis.topology_view(
        "topo:b5",
        node_record_refs=(position.position_id,),
        edge_flow_refs=(flow.flow_id,),
        valid_time=T0,
        observed_at=T0,
        registry=_registry_with(provenance, position, flow),
    )
    assert view.derived is True
    assert view.edge_flow_refs == (flow.flow_id,)


# ---------------------------------------------------------------------------
# R3-D3 / Phase 3 — observed_value_display bypass (C1–C5)
# ---------------------------------------------------------------------------


def test_c1_model_copy_stripped_refs_display_rejected() -> None:
    """C1: valid fact → model_copy(book2_claim_refs=()) → display must
    REJECT (today it renders)."""

    _, _, provenance = kernel()
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:c1", claim_ref="book5-claim-base")
    tampered = fact.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(tampered)
        raise AssertionError("defect still live: stripped-refs fact displayed")


def test_c2_swapped_claim_display_rejected() -> None:
    """C2: fact's claim swapped to an unrelated canonical claim → display
    must consult the context binding live and REJECT."""

    provenance, claim_id = _fact_kernel(
        "c2", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:c2", claim_ref=claim_id)
    swapped = fact.model_copy(update={"book2_claim_refs": ("book5-claim-vault",)})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(swapped)
        raise AssertionError("defect still live: swapped-claim fact displayed")


def test_c3_raw_dict_fact_typed_rejection() -> None:
    """C3: raw dict at the display boundary → typed fail-closed error."""

    _, _, provenance = kernel()
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(  # type: ignore[arg-type]
            {"fact_id": "fact:raw", "reported_value": "1"}
        )


def test_c4_valid_fact_display_passes() -> None:
    """C4: canonical fact with a coherent context binding → display PASS."""

    provenance, claim_id = _fact_kernel(
        "c4", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:c4", claim_ref=claim_id)
    payload = synthesis.observed_value_display(fact)
    assert payload["display"] == "OBSERVED_COMMON_VALUE_FACT"
    assert payload["reported_value"] == "40000000000"


def test_c5_display_is_never_valuation() -> None:
    """C5: display must never become valuation authority — the payload kind
    stays OBSERVED_COMMON_VALUE_FACT and valuation stays NOT_AUTHORIZED."""

    provenance, claim_id = _fact_kernel(
        "c5", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:c5", claim_ref=claim_id)
    payload = synthesis.observed_value_display(fact)
    assert payload["display"] == "OBSERVED_COMMON_VALUE_FACT"
    assert payload["display"] != "CSIA_DERIVED_COMMON_VALUE"
    assert synthesis.valuation_request() == "NOT_AUTHORIZED"


# ---------------------------------------------------------------------------
# R3-D4 / Phase 4 — non-component quantitative context (D1–D12)
# ---------------------------------------------------------------------------


def test_d1_flow_unit_mutated_rejected() -> None:
    """D1: valid ETH flow → model_copy unit=USDC, same claim refs → 5G
    validation must REJECT (today it passes)."""

    provenance, claim_id = _flow_kernel("d1", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:d1", claim_ref=claim_id)
    tampered = flow.model_copy(update={"unit": "USDC"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d1", flows=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated flow unit passed 5G validation",
    )


def test_d2_flow_asset_mutated_rejected() -> None:
    """D2: asset_ref ETH → WBTC with same claim refs → REJECT."""

    provenance, claim_id = _flow_kernel("d2", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:d2", claim_ref=claim_id)
    tampered = flow.model_copy(update={"asset_ref": "csia:token:wbtc"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d2", flows=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated flow asset passed 5G validation",
    )


def test_d3_flow_realization_mutated_rejected() -> None:
    """D3: realization_ref chain-a → chain-b while the binding establishes
    the realization context → REJECT."""

    provenance, claim_id = _flow_kernel(
        "d3",
        asset_ref="csia:token:eth",
        unit="ETH",
        realization_ref="realization:chain-a",
    )
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow(
        "flow:d3", claim_ref=claim_id, realization_ref="realization:chain-a"
    )
    tampered = flow.model_copy(update={"realization_ref": "realization:chain-b"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d3", flows=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated flow realization passed 5G validation",
    )


def test_d4_valid_context_bound_flow_passes() -> None:
    """D4: coherent context-bound flow → PASS."""

    provenance, claim_id = _flow_kernel("d4", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:d4", claim_ref=claim_id)
    snapshot = synthesis.compose_snapshot(
        "snap:d4", flows=(flow,), valid_time=T0, observed_at=T0
    )
    assert snapshot.input_record_refs == (flow.flow_id,)
    assert snapshot.principal_components is None  # flow-only: no fabricated vector


def test_d5_liability_unit_mutated_rejected() -> None:
    """D5: USDC liability → model_copy unit=ETH, same claim refs → REJECT."""

    provenance, claim_id = _liability_kernel(
        "d5", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:d5", claim_ref=claim_id)
    tampered = liability.model_copy(update={"unit": "ETH"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d5", liabilities=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated liability unit passed 5G validation",
    )


def test_d6_liability_asset_mutated_rejected() -> None:
    """D6: asset_ref USDC → WBTC with same claim refs → REJECT."""

    provenance, claim_id = _liability_kernel(
        "d6", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:d6", claim_ref=claim_id)
    tampered = liability.model_copy(update={"asset_ref": "csia:token:wbtc"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d6", liabilities=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated liability asset passed 5G validation",
    )


def test_d7_liability_site_mutated_rejected() -> None:
    """D7: market_site_id changed to an unrelated site while the binding
    establishes site context → REJECT."""

    provenance, claim_id = _liability_kernel(
        "d7", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:d7", claim_ref=claim_id)
    tampered = liability.model_copy(update={"market_site_id": "csia:site:market-9"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d7", liabilities=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated liability site passed 5G validation",
    )


def test_d8_valid_context_bound_liability_passes() -> None:
    """D8: coherent context-bound liability → PASS."""

    provenance, claim_id = _liability_kernel(
        "d8", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:d8", claim_ref=claim_id)
    snapshot = synthesis.compose_snapshot(
        "snap:d8", liabilities=(liability,), valid_time=T0, observed_at=T0
    )
    assert snapshot.input_record_refs == (liability.liability_id,)
    assert snapshot.liability_refs == (liability.liability_id,)


def test_d9_fact_numeraire_mutated_rejected() -> None:
    """D9: numeraire USD → BTC with same claim refs → REJECT."""

    provenance, claim_id = _fact_kernel(
        "d9", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:d9", claim_ref=claim_id)
    tampered = fact.model_copy(update={"numeraire": "BTC"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d9", observed_value_facts=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated fact numeraire passed 5G validation",
    )


def test_d10_fact_subject_mutated_rejected() -> None:
    """D10: subject_ref changed with same claim refs → REJECT."""

    provenance, claim_id = _fact_kernel(
        "d10", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:d10", claim_ref=claim_id)
    tampered = fact.model_copy(update={"subject_ref": "csia:stablecoin:other"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d10", observed_value_facts=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated fact subject passed 5G validation",
    )


def test_d11_fact_reporter_mutated_rejected() -> None:
    """D11: reporter_ref changed while the binding establishes reporter
    identity → REJECT."""

    provenance, claim_id = _fact_kernel(
        "d11",
        subject_ref="csia:stablecoin:fxd",
        numeraire="USD",
        reporter_ref="csia:entity:issuer",
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:d11", claim_ref=claim_id)
    tampered = fact.model_copy(update={"reporter_ref": "csia:entity:imposter"})
    _refuses_derived_output(
        lambda: synthesis.compose_snapshot(
            "snap:d11", observed_value_facts=(tampered,), valid_time=T0, observed_at=T0
        ),
        reason="mutated fact reporter passed 5G validation",
    )


def test_d12_valid_context_bound_fact_passes() -> None:
    """D12: coherent context-bound observed fact → compose + display PASS."""

    provenance, claim_id = _fact_kernel(
        "d12", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:d12", claim_ref=claim_id)
    snapshot = synthesis.compose_snapshot(
        "snap:d12", observed_value_facts=(fact,), valid_time=T0, observed_at=T0
    )
    assert snapshot.observed_value_fact_refs == (fact.fact_id,)
    payload = synthesis.observed_value_display(fact)
    assert payload["display"] == "OBSERVED_COMMON_VALUE_FACT"


# ---------------------------------------------------------------------------
# Phase 12 — model_copy R3 attack matrix (P/T/F/L/O): every authority-
# producing path revalidates live state. A model_copy-tampered artifact is
# inert data; the attack demonstrates that its refs cannot re-enter the
# authority boundary that produced it.
# ---------------------------------------------------------------------------


def _path_fixture(tag: str):
    _, _, provenance = kernel()
    claim_id = _bound_exact(
        provenance, f"{tag}-exact", asset_ref="csia:token:eth", unit="ETH"
    )
    position_a = _make_position(f"pos:{tag}-a", claim_ref=claim_id)
    position_b = _make_position(f"pos:{tag}-b", claim_ref=claim_id)
    synthesis = CapitalFieldSynthesis(provenance)
    registry = _registry_with(provenance, position_a, position_b)
    path = synthesis.compose_path(
        f"path:{tag}",
        stage_record_refs=(position_a.position_id, position_b.position_id),
        valid_time=T0,
        observed_at=T0,
        registry=registry,
    )
    return provenance, synthesis, registry, path


def test_p1_path_stage_ref_removed_rejected_on_reentry() -> None:
    """P1: derived path → model_copy(stage_record_refs=()) → the stripped
    artifact cannot re-enter the authority boundary: an empty stage tuple
    still refuses composition."""

    _, synthesis, _, path = _path_fixture("p1")
    tampered = path.model_copy(update={"stage_record_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_path(
            "path:p1-reentry",
            stage_record_refs=tampered.stage_record_refs,
            valid_time=T0,
            observed_at=T0,
            registry=_registry_with(_kernel_provenance()),
        )


def _kernel_provenance() -> Book5Provenance:
    _, _, provenance = kernel()
    return provenance


def test_p2_path_stage_ref_replaced_by_fake_ref_rejected() -> None:
    """P2: stage ref replaced by a fake ref → compose REJECT (UNKNOWN)."""

    _, synthesis, registry, path = _path_fixture("p2")
    tampered_refs = (path.stage_record_refs[0], "fake:exit")
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_path(
            "path:p2-reentry",
            stage_record_refs=tampered_refs,
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def test_p3_path_stage_ref_replaced_by_wrong_kind_ref_rejected() -> None:
    """P3: stage ref replaced by a canonical FLOW record id → compose REJECT
    (path stages must be position records — WRONG-KIND)."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(
        provenance, "p3-exact", asset_ref="csia:token:eth", unit="ETH"
    )
    position = _make_position("pos:p3", claim_ref=claim_id)
    flow_claim = _register_economics_claim(provenance, "p3-flow")
    _bind_flow_context(provenance, flow_claim, asset_ref="csia:token:eth", unit="ETH")
    flow = _make_flow("flow:p3", claim_ref=flow_claim)
    registry = _registry_with(provenance, position, flow)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_path(
            "path:p3",
            stage_record_refs=(flow.flow_id,),
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def _topology_fixture(tag: str):
    _, _, provenance = kernel()
    claim_id = _bound_exact(
        provenance, f"{tag}-exact", asset_ref="csia:token:eth", unit="ETH"
    )
    position = _make_position(f"pos:{tag}", claim_ref=claim_id)
    flow_claim = _register_economics_claim(provenance, f"{tag}-flow")
    _bind_flow_context(provenance, flow_claim, asset_ref="csia:token:eth", unit="ETH")
    flow = _make_flow(f"flow:{tag}", claim_ref=flow_claim)
    synthesis = CapitalFieldSynthesis(provenance)
    registry = _registry_with(provenance, position, flow)
    view = synthesis.topology_view(
        f"topo:{tag}",
        node_record_refs=(position.position_id,),
        edge_flow_refs=(flow.flow_id,),
        valid_time=T0,
        observed_at=T0,
        registry=registry,
    )
    return provenance, synthesis, registry, view


def test_t1_topology_node_ref_fake_rejected() -> None:
    """T1: derived view → node ref replaced by fake ref → re-entry REJECT."""

    _, synthesis, registry, view = _topology_fixture("t1")
    tampered = view.model_copy(update={"node_record_refs": (GHOST_NODE,)})
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:t1-reentry",
            node_record_refs=tampered.node_record_refs,
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def test_t2_topology_flow_ref_fake_rejected() -> None:
    """T2: edge flow ref replaced by fake ref → re-entry REJECT."""

    _, synthesis, registry, view = _topology_fixture("t2")
    tampered = view.model_copy(update={"edge_flow_refs": (GHOST_FLOW,)})
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:t2-reentry",
            node_record_refs=tampered.node_record_refs,
            edge_flow_refs=tampered.edge_flow_refs,
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def test_t3_topology_node_swapped_to_unrelated_record_rejected() -> None:
    """T3: node ref swapped to a canonical non-position record (a registered
    observed fact) → REJECT (a fact is never a capital node — WRONG-KIND)."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(
        provenance, "t3-exact", asset_ref="csia:token:eth", unit="ETH"
    )
    position = _make_position("pos:t3", claim_ref=claim_id)
    fact_claim = _register_economics_claim(provenance, "t3-fact")
    _bind_fact_context(
        provenance,
        fact_claim,
        subject_ref="csia:stablecoin:fxd",
        numeraire="USD",
    )
    fact = _make_fact("fact:t3", claim_ref=fact_claim)
    registry = _registry_with(provenance, position, fact)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:t3",
            node_record_refs=(fact.fact_id,),
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def test_t4_flow_endpoint_refs_mutated_rejected() -> None:
    """T4: a canonical flow whose position endpoint ref does not resolve →
    topology REJECT (endpoint consistency where deterministically possible;
    no invented endpoints)."""

    _, _, provenance = kernel()
    claim_id = _bound_exact(
        provenance, "t4-exact", asset_ref="csia:token:eth", unit="ETH"
    )
    position = _make_position("pos:t4", claim_ref=claim_id)
    flow_claim = _register_economics_claim(provenance, "t4-flow")
    _bind_flow_context(provenance, flow_claim, asset_ref="csia:token:eth", unit="ETH")
    flow = _make_flow(
        "flow:t4", claim_ref=flow_claim, from_position="pos:never-registered"
    )
    registry = _registry_with(provenance, position, flow)
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.topology_view(
            "topo:t4",
            node_record_refs=(position.position_id,),
            edge_flow_refs=(flow.flow_id,),
            valid_time=T0,
            observed_at=T0,
            registry=registry,
        )


def test_f1_flow_unit_mutation_rejected() -> None:
    """F1: canonical flow → model_copy unit → compose REJECT."""

    provenance, claim_id = _flow_kernel("f1", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:f1", claim_ref=claim_id)
    tampered = flow.model_copy(update={"unit": "USDC"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:f1", flows=(tampered,), valid_time=T0, observed_at=T0
        )


def test_f2_flow_asset_mutation_rejected() -> None:
    """F2: canonical flow → model_copy asset_ref → compose REJECT."""

    provenance, claim_id = _flow_kernel("f2", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:f2", claim_ref=claim_id)
    tampered = flow.model_copy(update={"asset_ref": "csia:token:wbtc"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:f2", flows=(tampered,), valid_time=T0, observed_at=T0
        )


def test_f3_flow_realization_mutation_rejected() -> None:
    """F3: flow with bound realization context → model_copy realization →
    compose REJECT."""

    provenance, claim_id = _flow_kernel(
        "f3",
        asset_ref="csia:token:eth",
        unit="ETH",
        realization_ref="realization:chain-a",
    )
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow(
        "flow:f3", claim_ref=claim_id, realization_ref="realization:chain-a"
    )
    tampered = flow.model_copy(update={"realization_ref": "realization:chain-b"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:f3", flows=(tampered,), valid_time=T0, observed_at=T0
        )


def test_f4_flow_claim_refs_stripped_rejected() -> None:
    """F4: canonical flow → model_copy(book2_claim_refs=()) → compose REJECT
    (no basis, no context)."""

    provenance, claim_id = _flow_kernel("f4", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(provenance)
    flow = _make_flow("flow:f4", claim_ref=claim_id)
    tampered = flow.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:f4", flows=(tampered,), valid_time=T0, observed_at=T0
        )


def test_l1_liability_unit_mutation_rejected() -> None:
    """L1: canonical liability → model_copy unit → compose REJECT."""

    provenance, claim_id = _liability_kernel(
        "l1", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:l1", claim_ref=claim_id)
    tampered = liability.model_copy(update={"unit": "ETH"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:l1", liabilities=(tampered,), valid_time=T0, observed_at=T0
        )


def test_l2_liability_asset_mutation_rejected() -> None:
    """L2: canonical liability → model_copy asset_ref → compose REJECT."""

    provenance, claim_id = _liability_kernel(
        "l2", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:l2", claim_ref=claim_id)
    tampered = liability.model_copy(update={"asset_ref": "csia:token:wbtc"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:l2", liabilities=(tampered,), valid_time=T0, observed_at=T0
        )


def test_l3_liability_site_mutation_rejected() -> None:
    """L3: canonical liability → model_copy market_site_id → compose REJECT."""

    provenance, claim_id = _liability_kernel(
        "l3", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:l3", claim_ref=claim_id)
    tampered = liability.model_copy(update={"market_site_id": "csia:site:market-9"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:l3", liabilities=(tampered,), valid_time=T0, observed_at=T0
        )


def test_l4_liability_claim_refs_stripped_rejected() -> None:
    """L4: canonical liability → model_copy(book2_claim_refs=()) → compose
    REJECT (no basis, no context)."""

    provenance, claim_id = _liability_kernel(
        "l4", asset_ref="csia:token:usdc", unit="USDC", site_ref="csia:site:market-1"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    liability = _make_liability("liability:l4", claim_ref=claim_id)
    tampered = liability.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:l4", liabilities=(tampered,), valid_time=T0, observed_at=T0
        )


def test_o1_fact_numeraire_mutation_rejected() -> None:
    """O1: canonical fact → model_copy numeraire → display REJECT."""

    provenance, claim_id = _fact_kernel(
        "o1", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:o1", claim_ref=claim_id)
    tampered = fact.model_copy(update={"numeraire": "BTC"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(tampered)


def test_o2_fact_subject_mutation_rejected() -> None:
    """O2: canonical fact → model_copy subject_ref → display REJECT."""

    provenance, claim_id = _fact_kernel(
        "o2", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:o2", claim_ref=claim_id)
    tampered = fact.model_copy(update={"subject_ref": "csia:stablecoin:other"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(tampered)


def test_o3_fact_reporter_mutation_rejected() -> None:
    """O3: canonical fact with bound reporter identity → model_copy
    reporter_ref → display REJECT."""

    provenance, claim_id = _fact_kernel(
        "o3",
        subject_ref="csia:stablecoin:fxd",
        numeraire="USD",
        reporter_ref="csia:entity:issuer",
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:o3", claim_ref=claim_id)
    tampered = fact.model_copy(update={"reporter_ref": "csia:entity:imposter"})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(tampered)


def test_o4_fact_claim_refs_stripped_rejected() -> None:
    """O4: canonical fact → model_copy(book2_claim_refs=()) → display REJECT
    (no basis, no context)."""

    provenance, claim_id = _fact_kernel(
        "o4", subject_ref="csia:stablecoin:fxd", numeraire="USD"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    fact = _make_fact("fact:o4", claim_ref=claim_id)
    tampered = fact.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.observed_value_display(tampered)
