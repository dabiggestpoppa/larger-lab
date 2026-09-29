"""Book 5 principal lineage graph (D5CAP-2 A-REVISED) and liability family
(D5CAP-1 B).

The lineage graph is a typed many-to-many graph of lineage nodes plus
PrincipalContribution edges. It supports 1:1, 1:N, N:1, and N:N principal
relationships; it is NOT a tree and never assumes one principal root per
claim. Conservation rules CON-1..CON-10 from the ratified plan v0.3 §4 are
mechanical here. The liability family implements the D5CAP-1 single-source-
of-truth: canonical obligation quantities exist in exactly one record and
positions reference them via reconciling projections.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .book5_core import (
    AttributionState,
    PrincipalComponent,
    PrincipalComponentSet,
    require_attributed,
)
from .book5_provenance import Book5Provenance, Book5ProvenanceError, require_str_hashable
from .temporal import Timestamp, UnknownBound


class LineageError(ValueError):
    """A lineage operation violates the ratified conservation doctrine."""


class PrincipalLineageNode(BaseModel):
    """One economic principal in the lineage graph (a conservation root)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lineage_id: str = Field(min_length=1)
    asset_ref: str = Field(min_length=1)
    realization_ref: str | None = None
    unit: str = Field(min_length=1)
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound


class PrincipalContribution(BaseModel):
    """Typed contribution edge: source principal -> target record.

    Quantity and share_fraction are optional per edge — never fabricated.
    DERIVED_ALLOCATION edges carry the methodology that produced them
    (plan v0.3 §4.2). COMMINGLED edges preserve the source set without unit
    identity (CON-3/CON-10).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_lineage_id: str = Field(min_length=1)
    target_record_id: str = Field(min_length=1)
    attribution_state: AttributionState
    quantity: str | None = None
    unit: str | None = None
    share_fraction: str | None = None
    methodology_id: str | None = None
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _state_laws(self) -> PrincipalContribution:
        if len(self.book2_claim_refs) == 0:
            raise ValueError("contribution edge requires Book 2 claim refs")
        if self.attribution_state is AttributionState.DERIVED_ALLOCATION and (
            self.methodology_id is None or self.share_fraction is None
        ):
            raise ValueError(
                "DERIVED_ALLOCATION contribution requires methodology_id and "
                "derived share_fraction"
            )
        if self.share_fraction is not None and self.attribution_state not in {
            AttributionState.PROPORTIONAL,
            AttributionState.DERIVED_ALLOCATION,
        }:
            raise ValueError(
                "share_fraction legal only for PROPORTIONAL/DERIVED_ALLOCATION "
                "(ALG-16)"
            )
        if (self.quantity is None) != (self.unit is None):
            raise ValueError("quantity and unit must be carried together or not at all")
        return self


def require_decimal(value: str, *, role: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise LineageError(f"{role} {value!r} is not a decimal") from exc


class AttributionBasisError(LineageError):
    """An attribution state claims more precision than its Book 2 basis.

    Ratified doctrine (Phase 4): no attribution state may increase epistemic
    precision beyond its Book 2 basis. EXACT contributions require claims
    asserting PRINCIPAL_EXACT_FACT; PROPORTIONAL contributions require
    PRINCIPAL_PROPORTIONAL_FACT. A state flipped post-construction (e.g., via
    ``model_copy``) fails closed at the collapse boundary when a provenance
    is supplied.
    """


ATTRIBUTION_BASIS_QUALIFIERS: Final[dict[str, str]] = {
    AttributionState.EXACT.value: "PRINCIPAL_EXACT_FACT",
    AttributionState.PROPORTIONAL.value: "PRINCIPAL_PROPORTIONAL_FACT",
}


class CapitalPrincipalLineageGraph:
    """Executable many-to-many lineage graph enforcing CON-1..CON-10.

    ``compose`` builds the graph; ``collapse_same_unit`` performs the only
    aggregation the doctrine allows (same-unit, attribution-honest,
    cycle-safe). There is no cross-unit collapse and no single-root
    assumption anywhere in this class.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, PrincipalLineageNode] = {}
        self._edges: tuple[PrincipalContribution, ...] = ()

    def add_node(self, node: PrincipalLineageNode) -> None:
        """R1-D4 seal: a raw dict or other non-canonical object at this
        boundary raises a typed LineageError — never an AttributeError from
        attribute access on malformed post-construction input."""

        if not isinstance(node, PrincipalLineageNode):
            raise LineageError(
                f"lineage node must be a typed PrincipalLineageNode, got "
                f"{type(node).__name__}"
            )
        require_str_hashable(node.lineage_id, role="lineage_id")
        if node.lineage_id in self._nodes:
            raise LineageError(f"lineage node {node.lineage_id} already exists")
        self._nodes[node.lineage_id] = node

    def add_edge(self, edge: PrincipalContribution) -> None:
        """R1-D4 seal: typed fail-closed input guard before attribute access."""

        if not isinstance(edge, PrincipalContribution):
            raise LineageError(
                f"contribution edge must be a typed PrincipalContribution, "
                f"got {type(edge).__name__}"
            )
        require_str_hashable(edge.source_lineage_id, role="source_lineage_id")
        require_str_hashable(edge.target_record_id, role="target_record_id")
        if edge.source_lineage_id not in self._nodes:
            raise LineageError(
                f"contribution references unknown lineage {edge.source_lineage_id}"
            )
        self._edges += (edge,)

    # -- structure ---------------------------------------------------------

    def roots_for(self, record_id: str) -> tuple[PrincipalLineageNode, ...]:
        """All principal roots feeding a record — MAY be many (N:1, N:N)."""

        seen: dict[str, PrincipalLineageNode] = {}
        self._walk(record_id, seen, set())
        return tuple(seen.values())

    def _walk(
        self,
        record_id: str,
        seen: dict[str, PrincipalLineageNode],
        visiting: set[str],
    ) -> None:
        for edge in self._edges:
            if edge.target_record_id != record_id:
                continue
            source = edge.source_lineage_id
            if source in seen:
                continue
            if source in visiting:
                raise LineageError(f"principal lineage cycle detected at {source}")
            visiting.add(source)
            # contributions may chain: lineage -> record -> lineage via
            # targets that are themselves lineage nodes.
            if source in self._nodes:
                seen[source] = self._nodes[source]
            self._walk(source, seen, visiting)
            visiting.discard(source)

    def detect_cycles(self) -> tuple[str, ...]:
        """Return lineage ids participating in cycles (CON-9; structural).

        A cycle is any lineage node reachable from itself through
        contribution edges. Detected by walking each node's downstream
        edges until the walk either terminates or returns to its origin.
        """

        cycles: set[str] = set()
        for origin in self._nodes:
            # downstream walk: origin -> targets -> further targets
            stack = [origin]
            visited: set[str] = set()
            while stack:
                current = stack.pop()
                for edge in self._edges:
                    if edge.source_lineage_id != current:
                        continue
                    target = edge.target_record_id
                    if target == origin:
                        cycles.add(origin)
                        break
                    if target in visited or target not in self._nodes:
                        continue
                    visited.add(target)
                    stack.append(target)
        return tuple(sorted(cycles))

    # -- aggregation -------------------------------------------------------

    def verify_edge_basis(self, provenance: Book5Provenance) -> None:
        """Verify every attributable edge's attribution basis in Book 2.

        Required at authority boundaries: an EXACT/PROPORTIONAL edge whose
        underlying claims do not assert the matching basis qualifier is
        refused (detects post-construction state upgrades that bypassed
        validators). R2: the resolver is mandatory at collapse time.
        """

        if provenance is None:  # defensive: explicit None fails closed
            raise Book5ProvenanceError(
                "verify_edge_basis requires an explicit Book5Provenance resolver"
            )

        for edge in self._edges:
            state_value = (
                edge.attribution_state.value
                if isinstance(edge.attribution_state, AttributionState)
                else str(edge.attribution_state)
            )
            # a post-construction tamper may leave a raw string in place of
            # the enum; both spellings are checked (fail-closed, never trusted)
            if state_value not in {s.value for s in AttributionState}:
                raise AttributionBasisError(
                    f"edge {edge.source_lineage_id}->{edge.target_record_id} "
                    f"carries non-canonical attribution state {state_value!r}"
                )
            if state_value not in ATTRIBUTION_BASIS_QUALIFIERS:
                continue
            required = ATTRIBUTION_BASIS_QUALIFIERS[state_value]
            for ref in edge.book2_claim_refs:
                claim = provenance.resolve_claim(ref)
                if claim.proposition.qualifier != required:
                    raise AttributionBasisError(
                        f"edge {edge.source_lineage_id}->{edge.target_record_id} "
                        f"claims {state_value} but claim {ref} asserts qualifier "
                        f"{claim.proposition.qualifier}; attribution basis "
                        f"exceeds its Book 2 evidence"
                    )

    def _materialize_components(self, record_id: str) -> tuple[PrincipalComponent, ...]:
        """Materialize the record's components from its contribution edges.

        Shared structural materialization: missing edge quantity stays
        ``None`` — never fabricated as "0" (R1-D3).
        """

        components: list[PrincipalComponent] = []
        for edge in self._edges:
            if edge.target_record_id != record_id:
                continue
            node = self._nodes[edge.source_lineage_id]
            components.append(
                PrincipalComponent(
                    asset_ref=node.asset_ref,
                    realization_ref=node.realization_ref,
                    quantity=edge.quantity,  # None = missing, NEVER fabricated "0"
                    unit=edge.unit or node.unit,
                    attribution_state=edge.attribution_state,
                    book2_claim_refs=edge.book2_claim_refs,
                    valid_time=edge.valid_time,
                    share_fraction=edge.share_fraction,
                )
            )
        if not components:
            raise LineageError(f"record {record_id} has no principal components")
        return tuple(components)

    def inspect_components_for(self, record_id: str) -> PrincipalComponentSet:
        """STRUCTURAL ONLY: raw component vector without Book 2 validation.

        R2 Phase 8 seal: this method exists so structural inspection never
        overloads the authoritative API. It performs NO live-state, basis,
        or context validation and its output MUST NOT back any economic
        conclusion, snapshot, aggregate, or 5G derived artifact — use
        :meth:`components_for` (authority context required) for that.
        """

        return PrincipalComponentSet(components=self._materialize_components(record_id))

    def components_for(
        self, record_id: str, *, provenance: Book5Provenance
    ) -> PrincipalComponentSet:
        """The record's principal components as a unit-aware vector (ALG-18).

        R1-D3 seal: a contribution edge lacking an evidenced quantity is NOT a
        zero. Missing quantity is carried as ``quantity=None`` — an explicit
        unknown — and remains distinguishable from an explicitly evidenced
        ``"0"`` (UNKNOWN != ZERO; no quantity may be fabricated).

        R2 mandatory-authority seal: ``provenance`` is REQUIRED — every
        materialized component revalidates against live Book 2 state
        (canonical type, attribution basis, bound context). ``model_copy``
        mutations cannot flow through lineage into conclusions, and the
        resolver cannot be forgotten: an absent context never degrades this
        boundary into an unverified vector.
        """

        if provenance is None:  # explicit None fails closed (R2-D1)
            raise Book5ProvenanceError(
                "components_for requires an explicit Book5Provenance resolver; "
                "use inspect_components_for for structural-only access"
            )
        components = self._materialize_components(record_id)
        for component in components:
            provenance.validate_principal_component(component)
        return PrincipalComponentSet(components=components)

    def collapse_same_unit(
        self,
        record_id: str,
        *,
        unit: str,
        realization_ref: str | None = None,
        provenance: Book5Provenance,
    ) -> str:
        """Collapse one record's principal components to a SAME-UNIT total.

        CON-2: exact conservation asserted only over EXACT/PROPORTIONAL
        edges. CON-3: COMMINGLED sources contribute only when the pool-level
        composition is itself evidenced (their own components carry
        attributable states). CON-9: cycle participation refuses collapse.
        There is deliberately no cross-unit variant (ALG-14/15).

        R2 mandatory-authority seal: ``provenance`` is REQUIRED. Edge bases
        are verified against live Book 2 state and every participating
        component's bound context is revalidated before any total is
        produced — a missing resolver can never produce an unverified
        economic total.
        """

        if provenance is None:  # explicit None fails closed (R2-D1)
            raise Book5ProvenanceError(
                "collapse_same_unit requires an explicit Book5Provenance "
                "resolver; a missing authority context never degrades into "
                "an unverified economic total"
            )
        if self.detect_cycles():
            raise LineageError(
                "refusing collapse over cyclic lineage; de-duplicate or report "
                "UNKNOWN (CON-9)"
            )
        self.verify_edge_basis(provenance)
        total = Decimal(0)
        matched = 0
        for edge in self._edges:
            if edge.target_record_id != record_id:
                continue
            node = self._nodes[edge.source_lineage_id]
            edge_unit = edge.unit or node.unit
            expected_unit = realization_ref or unit
            if edge_unit != unit and (node.realization_ref or node.unit) != expected_unit:
                continue
            component = PrincipalComponent(
                asset_ref=node.asset_ref,
                realization_ref=node.realization_ref,
                quantity=edge.quantity,
                unit=edge_unit,
                attribution_state=edge.attribution_state,
                book2_claim_refs=edge.book2_claim_refs,
                valid_time=edge.valid_time,
                share_fraction=edge.share_fraction,
            )
            require_attributed(
                edge.attribution_state,
                operation=f"collapse of lineage {edge.source_lineage_id}",
            )
            if edge.quantity is None:
                raise LineageError(
                    f"attributable edge {edge.source_lineage_id}->{record_id} "
                    "carries no quantity; refusing to fabricate one"
                )
            provenance.validate_principal_component(component)
            if (edge.quantity is None) != (edge.unit is None):
                raise LineageError(
                    f"attributable edge {edge.source_lineage_id}->{record_id} "
                    "carries quantity/unit inconsistently; refusing"
                )
            total += require_decimal(edge.quantity, role="edge quantity")
            matched += 1
        if matched == 0:
            raise LineageError(f"no attributable contributions for {record_id} in {unit}")
        return str(total)


#: Explicit valuation-request state (plan v0.3 §6 state law). Distinct from
#: UNKNOWN: NOT_AUTHORIZED names an authority boundary, not missing truth.
VALUATION_NOT_AUTHORIZED: Final[str] = "NOT_AUTHORIZED"


class DebtLiability(BaseModel):
    """Canonical borrowed-obligation record (D5CAP-1 single source of truth)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    liability_id: str = Field(min_length=1)
    market_site_id: str = Field(min_length=1)
    asset_ref: str = Field(min_length=1)
    quantity: str
    unit: str = Field(min_length=1)
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound


class ReserveLiability(BaseModel):
    """Canonical issuer/protocol backing obligation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    liability_id: str = Field(min_length=1)
    issuer_ref: str = Field(min_length=1)
    claim_token_ref: str = Field(min_length=1)
    backing: PrincipalComponentSet
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound


class RedemptionClaim(BaseModel):
    """Canonical redemption entitlement of a holder against an issuer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str = Field(min_length=1)
    liability_id: str = Field(min_length=1)
    holder_ref: str | None = None
    quantity: str
    unit: str = Field(min_length=1)
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound


def reconcile_projection(
    *,
    canonical_quantity: str,
    projected_quantity: str,
    same_observation_parameters: bool,
) -> str:
    """D5CAP-1 mechanical consistency rule (ALG-13).

    A projection may restate a canonical quantity only at equal observation
    parameters and only at the canonical value; divergence fails closed.
    """

    if not same_observation_parameters:
        raise Book5ProvenanceError(
            "liability projection observation parameters differ from canonical "
            "record; refusing to compare"
        )
    if (
        require_decimal(canonical_quantity, role="canonical quantity")
        != require_decimal(projected_quantity, role="projected quantity")
    ):
        raise Book5ProvenanceError(
            "liability projection diverges from canonical record; fail closed"
        )
    return canonical_quantity


__all__ = [
    "CapitalPrincipalLineageGraph",
    "DebtLiability",
    "LineageError",
    "PrincipalContribution",
    "PrincipalLineageNode",
    "RedemptionClaim",
    "ReserveLiability",
    "VALUATION_NOT_AUTHORIZED",
    "reconcile_projection",
    "require_decimal",
]
