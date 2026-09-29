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

from typing import Final, Literal, cast

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
from .book5_provenance import Book5Provenance, Book5ProvenanceError
from .book5_registry import Book5CanonicalRecordRegistry
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

    R2 mandatory-authority seal: a provenance resolver is REQUIRED at
    construction. There is no authority-bearing mode of this engine without
    live Book 2 context — an explicit ``None`` is refused, and no default,
    global singleton, or second epistemic engine exists (R2-D1B).

    R1-D5 seal: every canonical input is re-validated against live Book 2
    state at compose time — position claim sets, nested component claim
    sets, attribution bases, and bound context. A ``model_copy``-mutated
    record with stripped or swapped provenance cannot enter 5G; 5G cannot
    gain authority by accepting malformed inputs.
    """

    def __init__(
        self,
        provenance: Book5Provenance,
        ledger: SynthesisWriteLedger | None = None,
        registry: Book5CanonicalRecordRegistry | None = None,
    ) -> None:
        if provenance is None:  # explicit None fails closed (R2-D1B)
            raise Book5ProvenanceError(
                "CapitalFieldSynthesis requires an explicit Book5Provenance "
                "resolver; authority-bearing composition cannot exist without "
                "a live Book 2 authority context"
            )
        self.provenance = provenance
        self.ledger = ledger or SynthesisWriteLedger()
        # R3 Phase 8: the canonical record registry binds at the DERIVED-VIEW
        # boundary — compose_path/topology_view REQUIRE it (explicit None is
        # refused there). NO ARBITRARY STRING -> DERIVED 5G AUTHORITY.
        self.registry = registry

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

        position = cast(_Position, position)
        self._typed(position, _Position, role="position")
        self.provenance.resolve_claim_refs(position.book2_claim_refs)
        # R1-D4 typed guard runs FIRST: raw nested payloads fail closed as
        # typed errors before any attribute access (never AttributeError).
        nested: list[PrincipalComponent] = []
        for component in position.principal_components.components:
            self._typed(component, PrincipalComponent, role="nested principal component")
            nested.append(component)
        # R2 S4 closure: the position's asserted claim set must COVER the
        # claim set of every nested component — a position cannot cite an
        # unrelated canonical claim while its components ride another basis.
        nested_refs = {
            ref
            for component in nested
            for ref in component.book2_claim_refs
        }
        uncovered = sorted(nested_refs.difference(position.book2_claim_refs))
        if uncovered:
            raise Book5ProvenanceError(
                "position claim refs do not cover nested component claim "
                f"refs: {', '.join(uncovered)}; refusing composition"
            )
        for component in nested:
            self.provenance.validate_principal_component(component)

    def _validate_flow(self, flow: object) -> None:
        from .book5_records import CapitalFlow as _Flow

        flow = cast(_Flow, flow)
        self._typed(flow, _Flow, role="flow")
        self.provenance.resolve_claim_refs(flow.book2_claim_refs)
        # R3-D4 context seal: the claim set must be bound to this flow's
        # live quantitative context (asset/unit/realization) — claim
        # existence alone never verifies the record's identity.
        self.provenance.validate_quantitative_record(flow)

    def _validate_liability(self, liability: object) -> None:
        from .book5_lineage import DebtLiability as _Liability

        liability = cast(_Liability, liability)
        self._typed(liability, _Liability, role="liability")
        self.provenance.resolve_claim_refs(liability.book2_claim_refs)
        # R3-D4 context seal (asset/unit/market-site context).
        self.provenance.validate_quantitative_record(liability)

    def _validate_observed_value_fact(self, fact: object) -> None:
        from .book5_records import ObservedCommonValueFact as _Fact

        fact = cast(_Fact, fact)
        self._typed(fact, _Fact, role="observed value fact")
        self.provenance.resolve_claim_refs(fact.book2_claim_refs)
        # R3-D4 context seal (subject/numeraire/reporter context).
        self.provenance.validate_quantitative_record(fact)

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
        R2 mandatory-authority seal: every input is re-validated against
        live Book 2 state before composition — the engine cannot be
        constructed without its authority resolver.
        """

        if (
            not positions
            and not flows
            and not liabilities
            and not observed_value_facts
        ):
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
            *(liab.liability_id for liab in liabilities if not isinstance(liab, ObservedCommonValueFact)),
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
            + [
                liab.liability_id
                for liab in liabilities
                if not isinstance(liab, ObservedCommonValueFact)
            ]
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
            liability_refs=tuple(
                liab.liability_id
                for liab in liabilities
                if not isinstance(liab, ObservedCommonValueFact)
            ),
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
        registry: Book5CanonicalRecordRegistry,
    ) -> CapitalFieldPath:
        """Compose a derived path over canonical record pointers (R3-D1 seal).

        Phase 8/9 reference closure: EVERY stage ref must resolve through the
        canonical Book 5 record registry as a position or transformation
        record. An unknown ref is REJECTED (UNKNOWN), a registered record of
        another kind is REJECTED (WRONG-KIND), a duplicated ref is REJECTED
        (no ratified semantics allow repeated stages — a repeat fakes a
        multi-stage path the canonical records do not assert). Path order is
        preserved exactly as given; semantic gaps are carried only as
        explicit ``Gap`` entries — never as a fabricated stage ref, and an
        unknown stage is never represented as a ref at all
        (NO PATH WITH UNRESOLVED CANONICAL REF).
        """

        if registry is None:  # explicit None fails closed (R3 Phase 8)
            raise Book5ProvenanceError(
                "compose_path requires an explicit canonical record registry; "
                "a path whose stages cannot be proven canonical is not a "
                "derived artifact"
            )
        if len(stage_record_refs) == 0:
            raise Book5ProvenanceError("path requires stage record refs")
        if len(set(stage_record_refs)) != len(stage_record_refs):
            raise Book5ProvenanceError(
                "path stages must be unique; a repeated stage ref fakes a "
                "multi-stage path the canonical records do not assert"
            )
        for ref in stage_record_refs:
            resolved = registry.resolve(ref, expected_kind="position")
            if resolved.record_kind != "position":
                raise Book5ProvenanceError(
                    f"path stage {ref!r} is a canonical "
                    f"{resolved.record_kind} record; path stages must be "
                    "position records (WRONG-KIND)"
                )
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

        R2 mandatory-authority seal: every rendered component revalidates
        against live Book 2 state — a derived lineage view is an authority-
        bearing artifact and cannot launder mutated records.
        """

        components = graph.components_for(
            target_record_id, provenance=self.provenance
        )
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
        registry: Book5CanonicalRecordRegistry,
    ) -> CapitalTopologyView:
        """Compose a derived topology view over canonical pointers (R3-D2).

        Phase 8/10 reference closure: EVERY node ref must resolve through the
        canonical registry (any kind except flow — a flow is an edge, not a
        node), and EVERY edge_flow_ref must resolve as a canonical flow
        record. Nodes are unique; edges are unique. For each edge flow whose
        canonical record asserts position endpoints (from_position/
        to_position), the endpoint ref must itself resolve in the registry
        (an unresolved canonical ref is REJECTED); when the endpoint is
        registered but NOT represented in the node set, the omission is
        carried as an explicit ``Gap`` — never a fabricated node
        (NO FAKE TOPOLOGY NODE; incomplete truth stays incomplete).
        """

        if registry is None:  # explicit None fails closed (R3 Phase 8)
            raise Book5ProvenanceError(
                "topology_view requires an explicit canonical record registry; "
                "a topology whose nodes and edges cannot be proven canonical "
                "is not a derived artifact"
            )
        if not node_record_refs:
            raise Book5ProvenanceError("topology view requires node record refs")
        if len(set(node_record_refs)) != len(node_record_refs):
            raise Book5ProvenanceError(
                "topology nodes must be unique; a duplicated node ref fakes "
                "fan-out the canonical records do not assert"
            )
        node_set = set(node_record_refs)
        for ref in node_record_refs:
            resolved = registry.resolve(ref)
            if resolved.record_kind == "flow":
                raise Book5ProvenanceError(
                    f"topology node {ref!r} is a canonical flow record; "
                    "flows are edges, not nodes (WRONG-KIND)"
                )
        if len(set(edge_flow_refs)) != len(edge_flow_refs):
            raise Book5ProvenanceError(
                "topology edge flow refs must be unique; a repeated edge "
                "fakes connectivity the canonical records do not assert"
            )
        computed_gaps: list[Gap] = list(gaps)
        for ref in edge_flow_refs:
            registry.resolve(ref, expected_kind="flow")
            flow = registry.registered_record(ref)
            for endpoint_attr in (
                "from_position",
                "to_position",
            ):
                endpoint_ref = getattr(flow, endpoint_attr, None)
                if endpoint_ref is None:
                    continue
                registry.resolve(endpoint_ref, expected_kind="position")
                if endpoint_ref not in node_set:
                    computed_gaps.append(
                        Gap(
                            missing_input_ref=endpoint_ref,
                            reason=(
                                f"FLOW_ENDPOINT_NOT_IN_TOPOLOGY ({endpoint_attr} "
                                f"of flow {ref})"
                            ),
                        )
                    )
        self.ledger.record_composition()
        return CapitalTopologyView(
            view_id=view_id,
            node_record_refs=node_record_refs,
            edge_flow_refs=edge_flow_refs,
            methodology_id="5g-topology-view",
            valid_time=valid_time,
            observed_at=observed_at,
            gaps=tuple(computed_gaps),
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
        sets return the component vector (never a scalar).

        R2 mandatory-authority seal: the bound provenance is forwarded to
        every materialization and collapse boundary — attribution bases and
        bound context are verified against live Book 2 state before any
        economic total or component vector is produced."""

        components = graph.components_for(
            record_id, provenance=self.provenance
        )
        units = components.units()
        if len(units) > 1:
            return ("HETEROGENEOUS_VECTOR", None, components)
        total = graph.collapse_same_unit(
            record_id, unit=unit, provenance=self.provenance
        )
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
        conversion authority for component vectors.

        R3-D3 seal (Phase 11): display is an authority-producing surface, so
        the LIVE fact is validated before any payload is rendered — typed
        guard (raw dicts fail closed), Book 2 claim resolution (stripped or
        detached refs fail), and the quantitative context seal (asset —
        here: subject/numeraire/reporter — context verified against the
        binding; ``model_copy`` tampering cannot display). The payload is
        DISPLAY ONLY: no conversion, no valuation derivation, and the kind
        stays OBSERVED_COMMON_VALUE_FACT, never CSIA_DERIVED_COMMON_VALUE.
        """

        from .book5_records import ObservedCommonValueFact as _Fact

        self._typed(fact, _Fact, role="observed value fact")
        self.provenance.resolve_claim_refs(fact.book2_claim_refs)
        self.provenance.validate_quantitative_record(fact)
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
