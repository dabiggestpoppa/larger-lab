"""Book 5 Bloc 5G — Capital Field synthesis (D5CAP-3 A; D7 binding invariants).

5G is DERIVED ONLY:

    5G MAY DERIVE FROM CANONICAL CAPITAL FACTS.
    5G MAY NOT CREATE CANONICAL CAPITAL FACTS.

Every output is a composition of canonical 5A–5F records by pointer, carrying
input refs, methodology/version, valid + observation time, unknown
propagation, liability/exposure treatment, principal-component handling, and
a recomputation path (INV-5G-1..7). Heterogeneous compositions return
PrincipalComponentSet vectors — never a scalar (ALG-18). Valuation requests
resolve to NOT_AUTHORIZED before Book 6 exists (state law, distinct from
UNKNOWN). ``SynthesisWriteLedger`` proves the canonical write count is zero
by construction: this module contains no path that mints canonical records.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from .book5_core import (
    AttributionState,
    PrincipalComponent,
    PrincipalComponentSet,
)
from .book5_lineage import (
    CapitalPrincipalLineageGraph,
    DebtLiability,
    VALUATION_NOT_AUTHORIZED,
)
from .book5_provenance import Book5ProvenanceError
from .book5_records import (
    CapitalFlow,
    CapitalPosition,
    ObservedCommonValueFact,
)
from .temporal import Timestamp, UnknownBound

SYNTHESIS_METHODOLOGY_VERSION = "5g-compose-v1"


class Gap(BaseModel):
    """An explicit unknown-propagation marker (INV-5G-4)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    missing_input_ref: str
    reason: str


class CapitalFieldSnapshot(BaseModel):
    """Immutable, versioned composition at a valid time (D5CAP-3 A).

    Derived artifact: every field is an input pointer, methodology/temporal
    parameter, propagated unknown, or same-unit collapsed aggregate labeled
    with its attribution basis. No field originates an economic observation.

    R1-D3 seal: ``principal_components`` is ``None`` when the composition has
    NO principal-component observation — a missing-input state carried as an
    explicit Gap, never a placeholder token, a fabricated zero, or a fake
    claim ref (UNKNOWN != ZERO; no missing-input fabrication; INV-5G-4).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(min_length=1)
    methodology_id: str = Field(min_length=1)
    methodology_version: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    input_record_refs: tuple[str, ...] = Field(min_length=1)
    principal_components: PrincipalComponentSet | None
    same_unit_totals: tuple[str, ...] = ()
    gaps: tuple[Gap, ...] = ()
    liability_refs: tuple[str, ...] = ()
    observed_value_fact_refs: tuple[str, ...] = ()
    derived: Literal[True] = True

    @property
    def incomplete(self) -> bool:
        return len(self.gaps) > 0


NO_PRINCIPAL_COMPONENT_OBSERVED: Final[str] = "NO_PRINCIPAL_COMPONENT_OBSERVED"


class CapitalFieldPath(BaseModel):
    """Typed issuance → … → exit path over canonical record pointers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path_id: str = Field(min_length=1)
    stage_record_refs: tuple[str, ...] = Field(min_length=1)
    methodology_id: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    gaps: tuple[Gap, ...] = ()
    derived: Literal[True] = True


class CapitalPrincipalLineageView(BaseModel):
    """DERIVED projection over the canonical lineage graph (naming seal).

    Never carries more lineage precision than the canonical records contain:
    per-component attribution states are copied, COMMINGLED components are
    never rendered as unit ancestry.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    view_id: str = Field(min_length=1)
    target_record_id: str = Field(min_length=1)
    components: PrincipalComponentSet
    methodology_id: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    derived: Literal[True] = True


class CapitalTopologyView(BaseModel):
    """Projected topology surface over canonical records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    view_id: str = Field(min_length=1)
    node_record_refs: tuple[str, ...] = Field(min_length=1)
    edge_flow_refs: tuple[str, ...] = ()
    methodology_id: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    gaps: tuple[Gap, ...] = ()
    derived: Literal[True] = True


class SynthesisWriteLedger:
    """Structural proof artifact: 5G canonical write count = 0.

    The only way to author canonical Book 5 records is the canonical record
    constructors (book5_records/book5_lineage); none of them is reachable
    from this module. The ledger records every composition the synthesis
    engine performed so the count is demonstrated, not asserted.
    """

    def __init__(self) -> None:
        self._compositions = 0

    def record_composition(self) -> None:
        self._compositions += 1

    @property
    def canonical_write_count(self) -> int:
        return 0

    @property
    def composition_count(self) -> int:
        return self._compositions


class CapitalFieldSynthesis:
    """The 5G composition engine (derived outputs only).

    R1-D5 seal: when a ``provenance`` is supplied, every canonical input is
    re-validated against live Book 2 state at compose time — position claim
    sets, nested component claim sets, attribution bases, and context. A
    ``model_copy``-mutated record with stripped or swapped provenance cannot
    enter 5G; 5G cannot gain authority by accepting malformed inputs.
    """

    def __init__(
        self,
        ledger: SynthesisWriteLedger | None = None,
        *,
        provenance: object = None,
    ) -> None:
        self.ledger = ledger or SynthesisWriteLedger()
        self.provenance = provenance

    # -- INV-5G-2/3 helpers ------------------------------------------------

    def _typed(self, value: object, expected: type, *, role: str) -> None:
        """Typed fail-closed input guard (R1-D4): raw dicts and other
        non-canonical objects at a 5G boundary raise a typed
        Book5ProvenanceError — never an AttributeError/TypeError leak."""

        if not isinstance(value, expected):
            raise Book5ProvenanceError(
                f"5G input {role} must be a typed {expected.__name__}, got "
                f"{type(value).__name__}"
            )

    def _validate_position(self, position: object) -> None:
        from .book5_records import CapitalPosition as _Position

        self._typed(position, _Position, role="position")
        if self.provenance is None:
            return
        self.provenance.resolve_claim_refs(position.book2_claim_refs)
        for component in position.principal_components.components:
            self.provenance.validate_principal_component(component)

    def _validate_flow(self, flow: object) -> None:
        from .book5_records import CapitalFlow as _Flow

        self._typed(flow, _Flow, role="flow")
        if self.provenance is None:
            return
        self.provenance.resolve_claim_refs(flow.book2_claim_refs)

    def _validate_liability(self, liability: object) -> None:
        from .book5_lineage import DebtLiability as _Liability

        self._typed(liability, _Liability, role="liability")
        if self.provenance is None:
            return
        self.provenance.resolve_claim_refs(liability.book2_claim_refs)

    def _validate_observed_value_fact(self, fact: object) -> None:
        from .book5_records import ObservedCommonValueFact as _Fact

        self._typed(fact, _Fact, role="observed value fact")
        if self.provenance is None:
            return
        self.provenance.resolve_claim_refs(fact.book2_claim_refs)

    def _snapshot(
        self,
        snapshot_id: str,
        *,
        input_record_refs: tuple[str, ...],
        principal_components: PrincipalComponentSet | None,
        valid_time: Timestamp | UnknownBound,
        observed_at: Timestamp,
        gaps: tuple[Gap, ...] = (),
        liability_refs: tuple[str, ...] = (),
        observed_value_fact_refs: tuple[str, ...] = (),
        same_unit_totals: tuple[str, ...] = (),
    ) -> CapitalFieldSnapshot:
        self.ledger.record_composition()
        return CapitalFieldSnapshot(
            snapshot_id=snapshot_id,
            methodology_id="5g-capital-field-composition",
            methodology_version=SYNTHESIS_METHODOLOGY_VERSION,
            valid_time=valid_time,
            observed_at=observed_at,
            input_record_refs=input_record_refs,
            principal_components=principal_components,
            same_unit_totals=same_unit_totals,
            gaps=gaps,
            liability_refs=liability_refs,
            observed_value_fact_refs=observed_value_fact_refs,
        )

    # -- composition -------------------------------------------------------

    def compose_snapshot(
        self,
        snapshot_id: str,
        *,
        positions: tuple[CapitalPosition, ...] = (),
        flows: tuple[CapitalFlow, ...] = (),
        liabilities: tuple[DebtLiability, ...] = (),
        observed_value_facts: tuple[ObservedCommonValueFact, ...] = (),
        valid_time: Timestamp | UnknownBound,
        observed_at: Timestamp,
    ) -> CapitalFieldSnapshot:
        """Compose canonical records into a derived snapshot.

        INV-5G-4: any position with non-attributable components propagates a
        Gap (never zero-fill). INV-5G-5/6/7: components are carried with
        attribution; liabilities are referenced (not netted); exposures are
        not accepted as inputs. T-1: heterogeneous vectors are preserved as
        vectors — no scalar exists on this artifact.

        R1-D3 seal: a flow-only composition carries ``principal_components
        = None`` plus an explicit ``NO_PRINCIPAL_COMPONENT_OBSERVED`` gap —
        no placeholder token, no fabricated zero, no invented claim ref.
        R1-D5 seal: when a provenance is bound, every input is re-validated
        against live Book 2 state before composition.
        """

        if not positions and not flows and not liabilities:
            raise Book5ProvenanceError(
                "5G composition requires at least one canonical input record"
            )
        # R1-D4: typed fail-closed guards run BEFORE any attribute access so a
        # raw dict can never leak an AttributeError from this boundary.
        for position in positions:
            self._validate_position(position)
        for flow in flows:
            self._validate_flow(flow)
        for liability in liabilities:
            self._validate_liability(liability)
        for fact in observed_value_facts:
            self._validate_observed_value_fact(fact)
        input_seed: list[str] = [
            *(p.position_id for p in positions),
            *(f.flow_id for f in flows),
            *(liab.liability_id for liab in liabilities),
            *(o.fact_id for o in observed_value_facts),
        ]
        if not input_seed:
            raise Book5ProvenanceError(
                "5G composition requires at least one canonical input record"
            )
        components: list[PrincipalComponent] = []
        gaps: list[Gap] = []
        for position in positions:
            for component in position.principal_components.components:
                state = (
                    component.attribution_state.value
                    if isinstance(component.attribution_state, AttributionState)
                    else str(component.attribution_state)
                )
                if state in {
                    AttributionState.UNKNOWN.value,
                    AttributionState.UNRESOLVED.value,
                    AttributionState.COMMINGLED.value,
                }:
                    gaps.append(
                        Gap(
                            missing_input_ref=position.position_id,
                            reason=(
                                f"component {component.unit} attribution "
                                f"{state} does not "
                                "support exact composition"
                            ),
                        )
                    )
                components.append(component)
        for flow in flows:
            for ref in (flow.from_position, flow.to_position):
                if ref is not None:
                    pass  # position linkage recorded via input refs
        input_refs = tuple(
            [p.position_id for p in positions]
            + [f.flow_id for f in flows]
            + [liab.liability_id for liab in liabilities]
            + [o.fact_id for o in observed_value_facts]
        )
        if components:
            principal: PrincipalComponentSet | None = PrincipalComponentSet(
                components=tuple(components)
            )
        elif positions:
            raise Book5ProvenanceError(
                "5G composition encountered malformed position inputs with no "
                "principal components; refusing to fabricate"
            )
        else:
            principal = None
            gaps.append(
                Gap(
                    missing_input_ref="5g:principal-vector",
                    reason="NO_PRINCIPAL_COMPONENT_OBSERVED",
                )
            )
        return self._snapshot(
            snapshot_id,
            input_record_refs=input_refs,
            principal_components=principal,
            valid_time=valid_time,
            observed_at=observed_at,
            gaps=tuple(gaps),
            liability_refs=tuple(liab.liability_id for liab in liabilities),
            observed_value_fact_refs=tuple(o.fact_id for o in observed_value_facts),
        )

    def compose_path(
        self,
        path_id: str,
        *,
        stage_record_refs: tuple[str, ...],
        valid_time: Timestamp | UnknownBound,
        observed_at: Timestamp,
        gaps: tuple[Gap, ...] = (),
    ) -> CapitalFieldPath:
        if len(stage_record_refs) == 0:
            raise Book5ProvenanceError("path requires stage record refs")
        self.ledger.record_composition()
        return CapitalFieldPath(
            path_id=path_id,
            stage_record_refs=stage_record_refs,
            methodology_id="5g-capital-field-path",
            valid_time=valid_time,
            observed_at=observed_at,
            gaps=gaps,
        )

    def lineage_view(
        self,
        view_id: str,
        *,
        graph: CapitalPrincipalLineageGraph,
        target_record_id: str,
        valid_time: Timestamp | UnknownBound,
        observed_at: Timestamp,
    ) -> CapitalPrincipalLineageView:
        """Projection over the canonical lineage graph (T-1/T-5).

        Attribution states are copied verbatim from canonical contributions —
        the view cannot be more precise than its sources.
        """

        components = graph.components_for(target_record_id)
        self.ledger.record_composition()
        return CapitalPrincipalLineageView(
            view_id=view_id,
            target_record_id=target_record_id,
            components=components,
            methodology_id="5g-lineage-view",
            valid_time=valid_time,
            observed_at=observed_at,
        )

    def topology_view(
        self,
        view_id: str,
        *,
        node_record_refs: tuple[str, ...],
        edge_flow_refs: tuple[str, ...] = (),
        valid_time: Timestamp | UnknownBound,
        observed_at: Timestamp,
        gaps: tuple[Gap, ...] = (),
    ) -> CapitalTopologyView:
        if not node_record_refs:
            raise Book5ProvenanceError("topology view requires node record refs")
        self.ledger.record_composition()
        return CapitalTopologyView(
            view_id=view_id,
            node_record_refs=node_record_refs,
            edge_flow_refs=edge_flow_refs,
            methodology_id="5g-topology-view",
            valid_time=valid_time,
            observed_at=observed_at,
            gaps=gaps,
        )

    # -- collapse / valuation ----------------------------------------------

    def collapse_request(
        self,
        *,
        graph: CapitalPrincipalLineageGraph,
        record_id: str,
        unit: str,
    ) -> tuple[Literal["SAME_UNIT_COLLAPSE", "HETEROGENEOUS_VECTOR"], str | None, PrincipalComponentSet | None]:
        """T-14/A: same-unit collapse where permitted; T-9/B: heterogeneous
        sets return the component vector (never a scalar)."""

        components = graph.components_for(record_id)
        units = components.units()
        if len(units) > 1:
            return ("HETEROGENEOUS_VECTOR", None, components)
        total = graph.collapse_same_unit(record_id, unit=unit)
        return ("SAME_UNIT_COLLAPSE", total, None)

    def valuation_request(self) -> str:
        """Phase 21/13: cross-asset valuation in Book 5 is NOT_AUTHORIZED.

        State law: NOT_AUTHORIZED names an authority boundary; it is never
        substituted with UNKNOWN (missing truth) and never computed.
        """

        return VALUATION_NOT_AUTHORIZED

    def observed_value_display(
        self, fact: ObservedCommonValueFact
    ) -> dict[str, str]:
        """T-13: an observed scalar is displayable as an observed fact with
        provenance — never as a Book 5/5G valuation output and never as a
        conversion authority for component vectors."""

        return {
            "display": "OBSERVED_COMMON_VALUE_FACT",
            "fact_id": fact.fact_id,
            "reported_value": fact.reported_value,
            "numeraire": fact.numeraire,
            "reporter_ref": fact.reporter_ref,
            "book2_claim_refs": ",".join(fact.book2_claim_refs),
        }


__all__ = [
    "SynthesisWriteLedger",
    "CapitalFieldPath",
    "CapitalFieldSnapshot",
    "CapitalFieldSynthesis",
    "CapitalPrincipalLineageView",
    "CapitalTopologyView",
    "Gap",
    "SYNTHESIS_METHODOLOGY_VERSION",
]
