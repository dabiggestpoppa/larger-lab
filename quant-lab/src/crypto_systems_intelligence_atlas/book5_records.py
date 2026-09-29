"""Book 5 position family, flow events, transformations, encumbrance, claims,
exposure, and observed common-value facts (ratified plan v0.3 §2–§5, §7).

Mechanical doctrine:

- positions are state records (CLAIM_SIDE / LIABILITY_SIDE /
  CUSTODY_OBSERVATION) with UNKNOWN-legal holders; ownership != custody !=
  location != liability (B5-P17);
- flows are append-only events; they never mutate stocks (B5-P19);
- transformations are distinct from flows and carry typed
  input/output claims plus liability/encumbrance/custody deltas;
- exposures live in the exposure domain and never enter principal sums
  (ALG-5/9);
- observed common-value facts are stored observations, never derivations.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .book5_core import (
    AttributionState,
    EconomicLocation,
    EconomicSite,
    PrincipalComponent,
    PrincipalComponentSet,
)
from .book5_lineage import DebtLiability, RedemptionClaim, ReserveLiability
from .book5_provenance import Book5ProvenanceError, require_str_hashable
from .temporal import Timestamp, UnknownBound


class PositionKind(str, Enum):
    CLAIM_SIDE = "CLAIM_SIDE"
    LIABILITY_SIDE = "LIABILITY_SIDE"
    CUSTODY_OBSERVATION = "CUSTODY_OBSERVATION"


class EncumbranceState(str, Enum):
    UNENCUMBERED = "UNENCUMBERED"
    PLEDGED = "PLEDGED"
    REHYPOTHECATED = "REHYPOTHECATED"
    UNKNOWN = "UNKNOWN"


class CapitalPosition(BaseModel):
    """Base position record (plan v0.3 §2.1).

    ``principal_components`` is the unit-aware vector (may be single-root for
    genuinely EXACT chains — never forced). Holder/custody are independent
    UNKNOWN-legal fields. ``liability_refs`` point at canonical liability
    records; positions never restate canonical obligation quantities.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    position_id: str = Field(min_length=1)
    position_kind: PositionKind
    asset_ref: str = Field(min_length=1)
    principal_components: PrincipalComponentSet
    holder_ref: str | None = None
    protocol_ref: str = Field(min_length=1)
    deployment_ref: str | None = None
    site_ref: str = Field(min_length=1)
    location: EconomicLocation
    custody_ref: str | None = None
    liability_refs: tuple[str, ...] = ()
    quantity: str
    unit: str = Field(min_length=1)
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    encumbrance_state: EncumbranceState = EncumbranceState.UNENCUMBERED

    @model_validator(mode="after")
    def _laws(self) -> CapitalPosition:
        if (
            not isinstance(self.valid_from, UnknownBound)
            and not isinstance(self.valid_to, UnknownBound)
            and self.valid_to is not None
            and self.valid_to < self.valid_from
        ):
            raise ValueError("position valid_to precedes valid_from")
        if (
            self.position_kind is PositionKind.CUSTODY_OBSERVATION
            and self.holder_ref is not None
        ):
            raise ValueError(
                "custody observation must not silently assert a holder "
                "(location truth is not ownership)"
            )
        return self

    def reference_liability(self, liability: DebtLiability, *, observed_at: Timestamp) -> str:
        """D5CAP-1 projection rule: a position may restate a canonical
        quantity only as a reconciling projection at equal parameters."""

        if liability.liability_id not in self.liability_refs:
            raise Book5ProvenanceError(
                f"position {self.position_id} does not reference liability "
                f"{liability.liability_id}"
            )
        if observed_at != self.observed_at:
            raise Book5ProvenanceError(
                "projection observation parameters differ from the position "
                "observation; refusing comparison"
            )
        from decimal import Decimal, InvalidOperation

        try:
            if Decimal(self.quantity) != Decimal(liability.quantity):
                raise Book5ProvenanceError(
                    "position liability projection diverges from canonical "
                    "DebtLiability quantity; fail closed"
                )
        except InvalidOperation as exc:
            raise Book5ProvenanceError("non-decimal liability quantity") from exc
        return liability.quantity


class Encumbrance(BaseModel):
    """Typed pledge/rehypothecation chain state — never an additive balance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    encumbrance_id: str = Field(min_length=1)
    encumbered_ref: str = Field(min_length=1)
    pledge_holder_ref: str | None = None
    state: EncumbranceState
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class EconomicClaim(BaseModel):
    """Holder-side claim wrapper (deposit claim, share claim, redemption
    claim context). Claims reference canonical obligations; they never
    restate them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_record_id: str = Field(min_length=1)
    holder_ref: str | None = None
    asset_ref: str = Field(min_length=1)
    quantity: str
    unit: str = Field(min_length=1)
    liability_refs: tuple[str, ...] = ()
    site_ref: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class FlowType(str, Enum):
    """Ratified candidate flow vocabulary (plan v0.3 §3; stress-reviewed)."""

    MINT = "MINT"
    BURN = "BURN"
    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BORROW = "BORROW"
    REPAY = "REPAY"
    LIQUIDATION = "LIQUIDATION"
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    RESTAKE = "RESTAKE"
    UNRESTAKE = "UNRESTAKE"
    SWAP = "SWAP"
    BRIDGE_IN = "BRIDGE_IN"
    BRIDGE_OUT = "BRIDGE_OUT"
    REDEEM = "REDEEM"
    YIELD_CREDIT = "YIELD_CREDIT"
    FEE = "FEE"
    SETTLEMENT = "SETTLEMENT"
    PAYMENT = "PAYMENT"
    OFF_RAMP = "OFF_RAMP"


class CapitalFlow(BaseModel):
    """Append-only economic event (plan v0.3 §3; B5-P19).

    ``capability_route_ref`` is an optional Book 1 capability-edge anchor —
    referencing it never turns availability into use (B5-P3/P4).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    flow_id: str = Field(min_length=1)
    flow_type: FlowType
    asset_ref: str = Field(min_length=1)
    realization_ref: str | None = None
    quantity: str
    unit: str = Field(min_length=1)
    from_location: EconomicLocation
    to_location: EconomicLocation
    from_position: str | None = None
    to_position: str | None = None
    from_site: str | None = None
    to_site: str | None = None
    capability_route_ref: str | None = None
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class TransformationKind(str, Enum):
    ASSET_TO_REALIZATION = "ASSET_TO_REALIZATION"
    ASSET_TO_LP_CLAIM = "ASSET_TO_LP_CLAIM"
    ASSET_TO_VAULT_SHARE = "ASSET_TO_VAULT_SHARE"
    ASSET_TO_LST = "ASSET_TO_LST"
    LST_TO_RESTAKED_CLAIM = "LST_TO_RESTAKED_CLAIM"
    COLLATERAL_TO_DEBT_RELATION = "COLLATERAL_TO_DEBT_RELATION"
    SPOT_COLLATERAL_TO_DERIVATIVE_MARGIN = "SPOT_COLLATERAL_TO_DERIVATIVE_MARGIN"
    RWA_UNDERLYING_TO_TOKENIZED_CLAIM = "RWA_UNDERLYING_TO_TOKENIZED_CLAIM"


class CapitalTransformation(BaseModel):
    """Typed form-change with conservation semantics (plan v0.3 §4).

    Distinct record class from CapitalFlow: a transformation records that one
    form became another with principal continuity; a flow records movement.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    transformation_id: str = Field(min_length=1)
    transformation_kind: TransformationKind
    input_claim_id: str = Field(min_length=1)
    output_claim_id: str = Field(min_length=1)
    principal_component_refs: tuple[str, ...] = Field(min_length=1)
    liability_created: tuple[str, ...] = ()
    liability_retired: tuple[str, ...] = ()
    encumbrance_created: tuple[str, ...] = ()
    encumbrance_released: tuple[str, ...] = ()
    custody_from: str | None = None
    custody_to: str | None = None
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _distinct_claims(self) -> CapitalTransformation:
        if self.input_claim_id == self.output_claim_id:
            raise ValueError(
                "transformation input and output claims must be distinct "
                "identities (form change, not identity erasure)"
            )
        return self


class DerivativeExposure(BaseModel):
    """Exposure-domain record (plan v0.3 §2.2/§20). Never a principal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    exposure_id: str = Field(min_length=1)
    instrument_ref: str = Field(min_length=1)
    site_ref: str = Field(min_length=1)
    notional_quantity: str
    notional_unit: str = Field(min_length=1)
    open_interest_quantity: str | None = None
    direction: str = Field(min_length=1)
    collateral_position_refs: tuple[str, ...] = ()
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class SettlementBalance(BaseModel):
    """Venue/contract settlement stock with segregability semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    balance_id: str = Field(min_length=1)
    venue_site_id: str = Field(min_length=1)
    principal_components: PrincipalComponentSet
    segregability: str = "UNKNOWN"
    valid_time: Timestamp | UnknownBound
    observed_at: Timestamp
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class ObservedCommonValueFact(BaseModel):
    """An externally reported scalar with provenance (plan v0.3 §4).

    Stored observation only: never a Book 5 valuation output, never mixed
    into component vectors, never an implicit numeraire (ALG-17).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_id: str = Field(min_length=1)
    reported_value: str
    numeraire: str = Field(min_length=1)
    reporter_ref: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    observed_at: Timestamp
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class AppendOnlyFlowLedger:
    """B5-P19/B5-P20 executor: flows append; supersession replaces records,
    never events; historical entries remain queryable forever."""

    def __init__(self) -> None:
        self._flows: tuple[CapitalFlow, ...] = ()
        self._superseded: set[str] = set()

    def append(self, flow: CapitalFlow) -> None:
        if any(existing.flow_id == flow.flow_id for existing in self._flows):
            raise Book5ProvenanceError(
                f"flow {flow.flow_id} already exists; flows are append-only and "
                "immutable (B5-P19)"
            )
        self._flows += (flow,)

    def supersede(self, flow_id: str, *, replacement: CapitalFlow) -> CapitalFlow:
        """Record replacement, not world-change: the original stays queryable."""

        if not any(existing.flow_id == flow_id for existing in self._flows):
            raise Book5ProvenanceError(f"unknown flow {flow_id}")
        if replacement.flow_id == flow_id:
            raise Book5ProvenanceError(
                "replacement flow must carry a new identity"
            )
        self._superseded.add(flow_id)
        self._flows += (replacement,)
        return replacement

    def flows(self) -> tuple[CapitalFlow, ...]:
        return self._flows

    def active_flow_ids(self) -> tuple[str, ...]:
        return tuple(f.flow_id for f in self._flows if f.flow_id not in self._superseded)


__all__ = [
    "AppendOnlyFlowLedger",
    "CapitalFlow",
    "CapitalPosition",
    "CapitalTransformation",
    "DerivativeExposure",
    "EconomicClaim",
    "Encumbrance",
    "EncumbranceState",
    "FlowType",
    "ObservedCommonValueFact",
    "PositionKind",
    "SettlementBalance",
    "TransformationKind",
]
