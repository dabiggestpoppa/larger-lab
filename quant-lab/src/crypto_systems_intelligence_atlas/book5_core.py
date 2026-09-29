"""Book 5 core economic types: sites, locations, attribution, unit-aware
principal components (ratified Book 5 plan v0.3; D5CAP-2 A-REVISED).

Mechanical doctrine encoded here:

- grammar separation: CAPABILITY != CAPACITY != FLOW != STOCK != POSITION !=
  CLAIM != LIABILITY != EXPOSURE != ECONOMIC PRINCIPAL (plan v0.3 §0.1);
- economic sites are Book 5-local identity records anchored to Book 1
  canonical protocol/deployment identities — never re-minting Book 1 truth;
- attribution states carry evidence quality; UNKNOWN never upgrades to EXACT;
- PrincipalComponentSet is unit-aware: no common-value field, no numeraire,
  no price, no cross-unit arithmetic (B5-P32; ALG-14).
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .book5_provenance import (
    ATTRIBUTION_BASIS_QUALIFIERS,
    Book5ProvenanceError,
    require_str_hashable,
)
from .temporal import Timestamp, UnknownBound


class AttributionState(str, Enum):
    """Evidence quality of a principal-contribution edge (plan v0.3 §3)."""

    EXACT = "EXACT"
    PROPORTIONAL = "PROPORTIONAL"
    COMMINGLED = "COMMINGLED"
    DERIVED_ALLOCATION = "DERIVED_ALLOCATION"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN = "UNKNOWN"


#: States under which a component's quantity participates in same-unit
#: arithmetic. COMMINGLED/UNKNOWN/UNRESOLVED never do; DERIVED_ALLOCATION only
#: through its methodology output, labeled — never as an exact total.
ARITHMETIC_STATES: Final[frozenset[AttributionState]] = frozenset(
    {AttributionState.EXACT, AttributionState.PROPORTIONAL}
)


class AttributionStateError(ValueError):
    """An attribution state was used beyond its epistemic basis."""


class AttributionBasisError(Book5ProvenanceError):
    """A component's attribution state exceeds its live Book 2 basis.

    R1-D1 seal: attribution precision is re-verified against the LIVE record
    state at every decision boundary. A state upgraded post-construction
    (e.g. via ``model_copy``) whose underlying claims do not assert the
    matching basis qualifier fails closed — constructor validators alone are
    not authority (plan v0.3 Phase 4; CON-2/CON-10; ALG-11).
    """


def require_canonical_state(component: "PrincipalComponent") -> AttributionState:
    """Fail closed when a component's live state is not the canonical enum.

    ``model_copy(update=...)`` can leave a raw string in ``attribution_state``
    that bypassed validators. The state is normalized ONLY by canonical
    construction — never silently trusted at a decision point.
    """

    if not isinstance(component.attribution_state, AttributionState):
        raise AttributionBasisError(
            f"component carries non-canonical attribution state "
            f"{component.attribution_state!r}; refuse raw attribution payload"
        )
    return component.attribution_state


def require_attributed(state: AttributionState, *, operation: str) -> None:
    """Fail closed when arithmetic is attempted on non-attributed components.

    ALG-7/ALG-11: UNKNOWN (and UNRESOLVED/COMMINGLED) cannot participate as
    zero or as exact in any algebra step; a COMMINGLED edge never supports
    exact unit ancestry (CON-10).
    """

    if state not in ARITHMETIC_STATES:
        raise AttributionStateError(
            f"{operation} refused: attribution state {state.value} does not "
            f"support exact arithmetic"
        )


class SiteType(str, Enum):
    """Candidate site taxonomy (plan v0.3 §1.1; final names ratified in plan)."""

    AMM_POOL = "AMM_POOL"
    CLMM_POOL = "CLMM_POOL"
    LENDING_MARKET = "LENDING_MARKET"
    ISOLATED_MARKET = "ISOLATED_MARKET"
    VAULT = "VAULT"
    STAKING_POOL = "STAKING_POOL"
    RESTAKING_STRATEGY = "RESTAKING_STRATEGY"
    PERP_MARKET = "PERP_MARKET"
    INSURANCE_FUND = "INSURANCE_FUND"
    SETTLEMENT_ACCOUNT = "SETTLEMENT_ACCOUNT"
    RWA_ISSUANCE_VEHICLE = "RWA_ISSUANCE_VEHICLE"
    PAYMENT_ENDPOINT = "PAYMENT_ENDPOINT"


class LocationType(str, Enum):
    """Candidate location ontology (plan v0.3 §1.4; UNKNOWN is first-class)."""

    ONCHAIN_ACCOUNT = "ONCHAIN_ACCOUNT"
    CONTRACT = "CONTRACT"
    POOL = "POOL"
    MARKET = "MARKET"
    VAULT = "VAULT"
    ESCROW = "ESCROW"
    VALIDATOR = "VALIDATOR"
    CEX = "CEX"
    CUSTODIAN = "CUSTODIAN"
    SPV = "SPV"
    OFFCHAIN_SETTLEMENT = "OFFCHAIN_SETTLEMENT"
    PAYMENT_ENDPOINT = "PAYMENT_ENDPOINT"
    OUTSIDE_MODELED_SYSTEM = "OUTSIDE_MODELED_SYSTEM"
    UNKNOWN = "UNKNOWN"


class EconomicLocation(BaseModel):
    """Where capital sits (plan v0.3 §1.4).

    UNKNOWN is a legal, precise state: a location is either genuinely typed or
    explicitly UNKNOWN — never a guessed concrete type with invented precision.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    location_type: LocationType
    ref: str | None = None
    observability: str = "OBSERVED"

    @model_validator(mode="after")
    def _unknown_never_carries_precision(self) -> EconomicLocation:
        if self.location_type is LocationType.UNKNOWN and self.ref is not None:
            raise ValueError(
                "UNKNOWN location must not carry a concrete ref (invented precision)"
            )
        if self.location_type is not LocationType.UNKNOWN and self.ref is None:
            raise ValueError("typed location requires a ref")
        return self


LOCATION_UNKNOWN: Final[EconomicLocation] = EconomicLocation(location_type=LocationType.UNKNOWN)


class EconomicSite(BaseModel):
    """Book 5-local economic-site identity (plan v0.3 §1.1; D7 recon default).

    Anchored to Book 1 canonical identities: a site *occupies* a protocol
    deployment; it never redefines or re-mints Book 1 identity truth.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    site_id: str = Field(min_length=1)
    site_type: SiteType
    protocol_ref: str = Field(min_length=1)
    deployment_ref: str | None = None
    location: EconomicLocation
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None

    @model_validator(mode="after")
    def _temporal_bounds(self) -> EconomicSite:
        if (
            not isinstance(self.valid_from, UnknownBound)
            and not isinstance(self.valid_to, UnknownBound)
            and self.valid_to is not None
            and self.valid_to < self.valid_from
        ):
            raise ValueError("site valid_to precedes valid_from")
        return self


def require_site_ref(value: object) -> str:
    return require_str_hashable(value, role="site_ref")


class PrincipalComponent(BaseModel):
    """One unit-aware principal component of a claim/position.

    Quantities are asset-denominated only. There is deliberately NO value
    field, NO numeraire, NO price — cross-unit scalarization is Book 6
    authority (plan v0.3 §4; ALG-14/15/16).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_ref: str = Field(min_length=1)
    realization_ref: str | None = None
    quantity: str | None  # decimal string; None = MISSING (never fabricated as "0")
    unit: str = Field(min_length=1)
    attribution_state: AttributionState
    book2_claim_refs: tuple[str, ...]
    valid_time: Timestamp | UnknownBound
    share_fraction: str | None = None  # evidenced composition fraction only

    @model_validator(mode="after")
    def _state_laws(self) -> PrincipalComponent:
        if len(self.book2_claim_refs) == 0:
            raise ValueError("principal component requires Book 2 claim refs")
        if self.quantity is not None:
            from decimal import Decimal, InvalidOperation

            try:
                Decimal(self.quantity)
            except InvalidOperation as exc:
                raise ValueError(
                    f"component quantity {self.quantity!r} is not a decimal"
                ) from exc
        if self.attribution_state is AttributionState.DERIVED_ALLOCATION:
            if self.share_fraction is None:
                raise ValueError(
                    "DERIVED_ALLOCATION component requires its methodology-"
                    "derived share_fraction (methodology_id carried on the "
                    "contribution edge)"
                )
        if self.share_fraction is not None and self.attribution_state not in {
            AttributionState.PROPORTIONAL,
            AttributionState.DERIVED_ALLOCATION,
        }:
            raise ValueError(
                "share_fraction is legal only for PROPORTIONAL or "
                "DERIVED_ALLOCATION components (ALG-16: fraction is "
                "composition, never a value basis)"
            )
        return self


class PrincipalComponentSet(BaseModel):
    """Unit-aware vector of principal components (plan v0.3 §4.2).

    The set is the canonical multi-principal representation. Same-unit
    aggregation is exposed only through :meth:`aggregate_same_unit`, which
    enforces attribution and identity laws. No cross-unit operation exists.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    components: tuple[PrincipalComponent, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _nonempty(self) -> PrincipalComponentSet:
        if len(self.components) == 0:
            raise ValueError("PrincipalComponentSet requires at least one component")
        return self

    def units(self) -> tuple[str, ...]:
        """Distinct (unit, realization) denominations — the vector's basis."""

        seen: dict[str, None] = {}
        for component in self.components:
            key = component.realization_ref or component.unit
            seen.setdefault(key, None)
        return tuple(seen)

    def is_heterogeneous(self) -> bool:
        return len(self.units()) > 1

    def aggregate_same_unit(
        self,
        unit: str,
        *,
        realization_ref: str | None = None,
        provenance: object = None,
    ) -> str:
        """Sum quantities of ONE unit under attribution laws (ALG-12).

        Components participate only when their attribution state supports
        arithmetic (EXACT/PROPORTIONAL). Cross-unit aggregation does not exist
        on this type; heterogeneous sets are returned as-is by design.

        R1 live-state seal: when a ``provenance`` is supplied, every
        participating component is re-validated against its LIVE Book 2 basis
        at this decision point — a ``model_copy`` attribution/unit/asset
        mutation cannot convert into an economic conclusion. Without a
        provenance, non-canonical (raw-injected) attribution states still fail
        closed and the attribution arithmetic law still applies.
        """

        from decimal import Decimal, InvalidOperation

        total = Decimal(0)
        matched = 0
        for component in self.components:
            key = component.realization_ref or component.unit
            expected = realization_ref or unit
            if key != expected and component.unit != unit:
                continue
            if provenance is not None:
                provenance.validate_principal_component(component)
            else:
                require_canonical_state(component)
            require_attributed(
                component.attribution_state,
                operation=f"same-unit aggregation of {unit}",
            )
            try:
                total += Decimal(component.quantity)
            except InvalidOperation as exc:
                raise Book5ProvenanceError(
                    f"component quantity {component.quantity!r} is not a decimal"
                ) from exc
            matched += 1
        if matched == 0:
            raise Book5ProvenanceError(f"no attributable components in unit {unit}")
        return str(total)


__all__ = [
    "ARITHMETIC_STATES",
    "AttributionState",
    "AttributionStateError",
    "AttributionBasisError",
    "EconomicLocation",
    "EconomicSite",
    "LOCATION_UNKNOWN",
    "LocationType",
    "PrincipalComponent",
    "PrincipalComponentSet",
    "SiteType",
    "require_attributed",
    "require_canonical_state",
    "require_site_ref",
]
