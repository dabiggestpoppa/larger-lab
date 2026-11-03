"""SENSOR-B5-I11E1 - provider-neutral liquidation observation normalizer.

The I11 realization of bloc_05/04 section 3 (MECHANICAL_LIQUIDATION): a typed
liquidation-specific T1 record over the accepted ``T1BaseEnvelope``, and a pure
``normalize_liquidation`` that preserves native truth while refusing to invent
canonical certainty.

The frozen contract this module implements is four *separate* economic facts
that must never be collapsed into one generic ``side`` (04 section 3):

    position_side_liquidated      LONG / SHORT / UNKNOWN
    execution_side                BUY / SELL / UNKNOWN
    aggressor_side                BUY / SELL / UNKNOWN   (optional)
    maker_taker_role              MAKER / TAKER / BOTH / UNKNOWN   (optional)

A long liquidation "generally requires sell execution" (04 section 3.1), but the
frozen text explicitly forbids encoding that as the ONLY representation, so both
fields survive where the provider supports both -- and neither is derived from
the other, from a price move, or from a provider's aggregate direction.  Where a
provider's own vocabulary is not yet certified, the raw field and the
provisional reading are preserved while the canonical slot stays ``UNKNOWN``:
bloc_05/06 section 9 and the I11 readiness assessment both require Layer-1
behaviour only, with canonical semantic confidence left unresolved.

Three further frozen distinctions are structural here:

* **Event versus aggregate** (04 section 3.3).  ``aggregation_scope`` is one of
  the five frozen tokens.  An ``INTERVAL_AGGREGATE`` or
  ``PROVIDER_MULTI_EVENT_AGGREGATE`` row is not an event: it may not carry a
  liquidation event id, and it must state its ``count``.  ``TRADE_LEVEL`` and
  ``EVENT_LEVEL`` rows may not state a count, because a count on a single event
  is an aggregate claim in disguise.
* **Zero versus missing** (04 section 3.5).  A zero interval is admitted only
  when the provider reports completed intervals including zero activity AND the
  interval coverage is verified.  Otherwise the row is ``UNVERIFIED_MISSING``:
  the provider's own zero is preserved as native evidence, but it is not
  promoted into a verified economic zero, and no absent interval ever becomes
  one.
* **Provider aggregate versus aggressor flow** (04 section 3.4).  A
  ``long_liq_usd``/``short_liq_usd`` figure is a POSITION-SIDE aggregate.  This
  module therefore has no code path that turns it into aggressor volume: the
  position side and the execution side are separate fields, and the aggregate
  keeps its scope label.

Economic honesty follows the accepted I10 discipline exactly (this module reuses
I10's :class:`DerivedAmount` and conversion lift rather than forking them):

* an unavailable derived amount is ``None`` plus a typed missingness cause --
  never an economic zero;
* ``liquidation_usd`` stays BLOCKED while ``B5_I08_UNITS_V1`` has no lawful
  ``sensor_family`` representation, with the citation preserved;
* ``liquidation_quote_notional`` is only ever a genuine quote-asset value, never
  a USD claim, and no stablecoin parity shortcut exists;
* an inverse contract's base quantity needs a PIT reference price, and a missing
  one blocks the derivation instead of substituting the liquidation price.

Out of scope by construction: duplicate collapse and fingerprinting (I17),
replay eligibility (I06), USD methodology registration (I09), and every other
sensor family.  No network, no wall clock, no id generation, no filesystem: a
payload in, a record out, byte-identical for byte-identical input.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from ...contracts.enums import AggressorSide, LiquidationRole, SensorFamily
from ...storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitEvidence,
)
from ..enums import (
    AvailabilityBasis,
    LineageState,
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    QualityDimensionState,
    QuarantineReason,
    TimestampPrecision,
)
from ..models import (
    NativeQuantity,
    NormalizationModelBase,
    ObservationTimeEnvelope,
    OpaqueIdentifier,
    T1BaseEnvelope,
    T1LineageRef,
    T1Quality,
    T1VersionContext,
)
from ..terms.conversion import (
    ReferencePriceEvidence,
    contracts_to_quote_notional,
    inverse_base_from_quote,
    inverse_quote_face,
    linear_base_exposure,
)
from ..terms.snapshot import ContractTermsSnapshot
from .trade import (
    I04B_METHODOLOGY_ID,
    I08_UNITS_METHODOLOGY_ID,
    DerivedAmount,
    _blocked,
    _canonical_flags,
    _from_conversion,
)

__all__ = [
    "I04B_METHODOLOGY_ID",
    "I08_UNITS_METHODOLOGY_ID",
    "LiquidationAggregationScope",
    "LiquidationObservationInput",
    "LiquidationPositionSide",
    "LiquidationZeroIntervalState",
    "T1LiquidationRecord",
    "normalize_liquidation",
]

#: The canonical quantity unit token meaning "this quantity counts contracts".
#: Reused from the frozen ``CanonicalQuantityUnit`` vocabulary rather than
#: re-spelled, exactly as the accepted I10 trade normalizer does.
_CONTRACTS_UNIT = "CONTRACTS"

#: Aggregation scopes that describe more than one underlying event.  A scope in
#: this set must state ``count`` and must not carry an event identity.
_AGGREGATE_SCOPES = frozenset(
    {
        "INTERVAL_AGGREGATE",
        "PROVIDER_MULTI_EVENT_AGGREGATE",
    }
)

#: Scopes that describe exactly one event.  A scope in this set may carry an
#: event identity and must not state ``count``.
_EVENT_SCOPES = frozenset({"TRADE_LEVEL", "EVENT_LEVEL"})

#: Coverage states that can support a verified zero interval (04 section 3.5).
#: ``COMPLETE_SOURCE_BOUNDARY`` is a completed boundary; ``EMPTY_CONFIRMED`` is
#: the upstream vocabulary's own "the provider confirmed emptiness" state.
_ZERO_SUPPORTING_COVERAGE = frozenset(
    {
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    }
)


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class LiquidationPositionSide(_StrEnum):
    """The liquidated POSITION side (bloc_05/04 section 3.1).

    Frozen members: ``LONG``, ``SHORT``, ``UNKNOWN``.  ``UNKNOWN`` is a real
    state -- "the provider did not establish which position was liquidated" --
    and never a placeholder to be filled from the execution side or the tape.
    """

    LONG = "LONG"
    SHORT = "SHORT"
    UNKNOWN = "UNKNOWN"


class LiquidationAggregationScope(_StrEnum):
    """How many underlying events a liquidation row covers (04 section 3.3).

    The five frozen tokens, verbatim.  This is deliberately NOT the Bloc 1
    observation schema's ``LiquidationEventShape`` (TRADE_LEVEL /
    INTERVAL_AGGREGATE / TOTAL_AGGREGATE): that vocabulary belongs to the raw
    observation layer, and bloc_05/04 section 3.3 fixes a different five-member
    set for the normalization envelope.  Re-using the Bloc 1 enum here would
    silently drop ``EVENT_LEVEL`` and ``PROVIDER_MULTI_EVENT_AGGREGATE`` and
    conflate a provider total with a multi-event aggregate.
    """

    TRADE_LEVEL = "TRADE_LEVEL"
    EVENT_LEVEL = "EVENT_LEVEL"
    INTERVAL_AGGREGATE = "INTERVAL_AGGREGATE"
    PROVIDER_MULTI_EVENT_AGGREGATE = "PROVIDER_MULTI_EVENT_AGGREGATE"
    UNKNOWN = "UNKNOWN"


class LiquidationZeroIntervalState(_StrEnum):
    """Whether a zero liquidation quantity is a verified economic zero.

    ``NOT_APPLICABLE`` -- the row's native quantity is non-zero.
    ``VERIFIED_ZERO`` -- zero, with a completed-interval provider claim and
    verified coverage (04 section 3.5, both conditions required).
    ``UNVERIFIED_MISSING`` -- zero was reported, but at least one of the two
    conditions is absent.  The native zero is retained as provider evidence and
    the row is NOT promoted to a verified zero: a missing interval never becomes
    a zero.
    """

    NOT_APPLICABLE = "NOT_APPLICABLE"
    VERIFIED_ZERO = "VERIFIED_ZERO"
    UNVERIFIED_MISSING = "UNVERIFIED_MISSING"


class ContradictoryLiquidationSideError(ValueError):
    """Kept for callers that require a raised refusal instead of a quarantine row.

    ``normalize_liquidation`` itself returns a QUARANTINED record (bloc_05/05
    section 20: quarantine is retention with a reason, not deletion), so this
    type is raised only by :func:`require_consistent_liquidation_sides`, the
    strict form a caller may choose.
    """


class LiquidationObservationInput(NormalizationModelBase):
    """Transport-neutral liquidation observation, before any canonical claim.

    Provider-neutral: the only provider-specific things a caller supplies are
    the raw field names/values it observed (preserved verbatim for the audit
    trail) and a claim about whether those semantics are certified.  Nothing
    here reads a registry, a clock or a network.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    liquidation_event_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    position_side_liquidated: LiquidationPositionSide = LiquidationPositionSide.UNKNOWN
    execution_side: AggressorSide = AggressorSide.UNKNOWN
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    maker_taker_role: LiquidationRole | None = None

    native_position_side_field: OpaqueIdentifier | None = None
    native_position_side_value: OpaqueIdentifier | None = None
    native_execution_side_field: OpaqueIdentifier | None = None
    native_execution_side_value: OpaqueIdentifier | None = None

    #: ``True`` only when provider-grade evidence establishes what the provider's
    #: side fields mean.  While ``False`` the canonical side slots stay UNKNOWN
    #: and the provider's reading is carried as provisional evidence only.
    provider_semantics_verified: bool = False

    quantity_native: Decimal
    quantity_native_unit: OpaqueIdentifier
    native_unit_evidence: SourceUnitEvidence | None = None
    source_unit_contract: SourceUnitContract | None = None

    price_native: Decimal | None = None
    price_reference: ReferencePriceEvidence | None = None

    count: int | None = Field(default=None, ge=0)
    aggregation_scope: LiquidationAggregationScope

    #: 04 section 3.5 condition 1: the provider reports completed intervals,
    #: including intervals with zero activity.
    provider_reports_completed_intervals: bool = False
    interval_closed: bool | None = None

    event_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    market_available_at: datetime | None = None
    availability_basis: AvailabilityBasis | None = None
    source_precision: TimestampPrecision | None = None

    source_revision_id: OpaqueIdentifier
    source_revision_state: RevisionState
    source_coverage_state: CoverageState
    normalization_generation: OpaqueIdentifier

    raw_projection_refs: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    acquisition_refs: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    evidence_blob_hashes: tuple[str, ...] = Field(min_length=1)
    code_version: OpaqueIdentifier
    config_version: OpaqueIdentifier

    @model_validator(mode="after")
    def _scope_count_law(self) -> LiquidationObservationInput:
        """Count is required by an aggregate and forbidden on a single event."""
        scope = self.aggregation_scope.value
        if scope in _AGGREGATE_SCOPES and self.count is None:
            raise ValueError(
                f"aggregation_scope={scope} requires count; an aggregate that "
                "cannot say how many events it covers cannot be compared with an "
                "event (bloc_05/04 sections 3.3-3.4)"
            )
        if scope in _EVENT_SCOPES and self.count is not None:
            raise ValueError(
                f"aggregation_scope={scope} must not carry count; a count on a "
                "single event is an aggregate claim in disguise"
            )
        return self

    @model_validator(mode="after")
    def _no_invented_event_identity(self) -> LiquidationObservationInput:
        """An aggregate may not carry an event identity (04 section 3.3)."""
        if (
            self.aggregation_scope.value in _AGGREGATE_SCOPES
            and self.liquidation_event_id is not None
        ):
            raise ValueError(
                "an aggregate observation must not carry liquidation_event_id; "
                "an event id on an aggregate would invent a single underlying "
                "trade from a summary"
            )
        return self

    @model_validator(mode="after")
    def _native_side_law(self) -> LiquidationObservationInput:
        if (
            self.native_position_side_value is not None
            and self.native_position_side_field is None
        ):
            raise ValueError(
                "a preserved native position-side value requires the provider "
                "field it came from; an unattributed value is not evidence"
            )
        if (
            self.native_execution_side_value is not None
            and self.native_execution_side_field is None
        ):
            raise ValueError(
                "a preserved native execution-side value requires the provider "
                "field it came from"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> LiquidationObservationInput:
        for name in (
            "raw_projection_refs",
            "acquisition_refs",
            "evidence_blob_hashes",
        ):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1LiquidationRecord(T1BaseEnvelope):
    """Liquidation-specific T1 record (bloc_05/04 section 3.3).

    Carries the thirteen canonical liquidation fields under their frozen names,
    plus the provisional and native slots that keep an unresolved provider
    vocabulary auditable.  The inherited base laws still apply unchanged, so
    this subclass can only add restrictions.
    """

    liquidation_event_id: OpaqueIdentifier | None = None

    position_side_liquidated: LiquidationPositionSide = LiquidationPositionSide.UNKNOWN
    execution_side: AggressorSide = AggressorSide.UNKNOWN
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    maker_taker_role: LiquidationRole | None = None

    quantity_native: Decimal
    quantity_native_unit: OpaqueIdentifier
    quantity_base: DerivedAmount | None = None
    liquidation_quote_notional: DerivedAmount | None = None
    liquidation_usd: DerivedAmount | None = None
    price_native: Decimal | None = None
    price_reference: ReferencePriceEvidence | None = None
    count: int | None = Field(default=None, ge=0)
    aggregation_scope: LiquidationAggregationScope

    provisional_position_side: LiquidationPositionSide = LiquidationPositionSide.UNKNOWN
    provisional_execution_side: AggressorSide = AggressorSide.UNKNOWN
    native_position_side_field: OpaqueIdentifier | None = None
    native_position_side_value: OpaqueIdentifier | None = None
    native_execution_side_field: OpaqueIdentifier | None = None
    native_execution_side_value: OpaqueIdentifier | None = None

    zero_interval_state: LiquidationZeroIntervalState = (
        LiquidationZeroIntervalState.NOT_APPLICABLE
    )

    normalization_methodology_id: OpaqueIdentifier | None = None
    normalization_methodology_version: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1LiquidationRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_LIQUIDATION:
            raise ValueError(
                "T1LiquidationRecord requires "
                f"sensor_family=MECHANICAL_LIQUIDATION, got {self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _scope_count_law(self) -> T1LiquidationRecord:
        scope = self.aggregation_scope.value
        if scope in _AGGREGATE_SCOPES and self.count is None:
            raise ValueError(f"aggregation_scope={scope} requires count")
        if scope in _EVENT_SCOPES and self.count is not None:
            raise ValueError(f"aggregation_scope={scope} must not carry count")
        return self

    @model_validator(mode="after")
    def _aggregate_identity_law(self) -> T1LiquidationRecord:
        if (
            self.aggregation_scope.value in _AGGREGATE_SCOPES
            and self.liquidation_event_id is not None
        ):
            raise ValueError(
                "an aggregate liquidation record must not carry an event id"
            )
        return self

    @model_validator(mode="after")
    def _side_separation_law(self) -> T1LiquidationRecord:
        """A collapsed side is unrepresentable, and a contradiction is quarantined.

        The canonical position side and the canonical execution side are
        independent fields; the frozen text only says a long liquidation
        *generally* requires sell execution.  So the one combination the model
        refuses outright is a record that claims the canonical verdict without
        the quarantine that a contradictory provider would require.
        """
        contradiction = _contradicts(
            self.provisional_position_side, self.provisional_execution_side
        )
        if contradiction and self.normalization_status is not (
            NormalizationStatus.QUARANTINED
        ):
            raise ValueError(
                "contradictory liquidation evidence (position "
                f"{self.provisional_position_side.value} with execution "
                f"{self.provisional_execution_side.value}) requires "
                "normalization_status=QUARANTINED, not a guessed reconciliation"
            )
        return self

    @model_validator(mode="after")
    def _zero_interval_law(self) -> T1LiquidationRecord:
        """A zero quantity and its admission state must agree (04 section 3.5)."""
        state = self.zero_interval_state
        if state is LiquidationZeroIntervalState.NOT_APPLICABLE:
            if self.quantity_native == 0:
                raise ValueError(
                    "quantity_native=0 requires an explicit zero_interval_state; "
                    "a zero is a claim about coverage, not a default"
                )
            return self
        if self.quantity_native != 0:
            raise ValueError(
                f"zero_interval_state={state.value} requires quantity_native=0"
            )
        if state is LiquidationZeroIntervalState.UNVERIFIED_MISSING and (
            self._claims_canonical_status
        ):
            raise ValueError(
                "an unverified zero interval must not claim a canonical status "
                "(bloc_05/04 section 3.5: no missing interval becomes zero)"
            )
        return self


def _contradicts(
    position: LiquidationPositionSide, execution: AggressorSide
) -> bool:
    """The one provable contradiction: LONG+BUY or SHORT+SELL.

    A long liquidation requires sell execution and a short liquidation requires
    buy execution (04 section 3.1).  Nothing is inferred when either side is
    UNKNOWN -- an unknown is not a contradiction.
    """
    if position is LiquidationPositionSide.LONG:
        return execution is AggressorSide.BUY
    if position is LiquidationPositionSide.SHORT:
        return execution is AggressorSide.SELL
    return False


def require_consistent_liquidation_sides(
    position: LiquidationPositionSide, execution: AggressorSide
) -> None:
    """Strict form: raise instead of returning a quarantined record."""
    if _contradicts(position, execution):
        raise ContradictoryLiquidationSideError(
            f"position_side_liquidated={position.value} contradicts "
            f"execution_side={execution.value}; a long liquidation requires sell "
            "execution and a short liquidation requires buy execution "
            "(bloc_05/04 section 3.1).  Neither side may be inferred from the "
            "other, from a price move, or from a provider aggregate direction."
        )


def _zero_state(payload: LiquidationObservationInput) -> LiquidationZeroIntervalState:
    """04 section 3.5, both conditions, in the frozen order."""
    if payload.quantity_native != 0:
        return LiquidationZeroIntervalState.NOT_APPLICABLE
    is_aggregate = payload.aggregation_scope.value in _AGGREGATE_SCOPES
    if (
        is_aggregate
        and payload.provider_reports_completed_intervals
        and payload.interval_closed is True
        and payload.source_coverage_state in _ZERO_SUPPORTING_COVERAGE
    ):
        return LiquidationZeroIntervalState.VERIFIED_ZERO
    return LiquidationZeroIntervalState.UNVERIFIED_MISSING


def _derived_amounts(
    payload: LiquidationObservationInput,
    terms: ContractTermsSnapshot | None,
    reference_price: ReferencePriceEvidence | None,
    knowledge_cutoff: datetime | None,
    flags: set[NormalizationQualityFlag],
) -> tuple[DerivedAmount | None, DerivedAmount | None]:
    """I04B quantity base and quote notional, or typed refusals.

    Mirrors the accepted I10 trade arithmetic exactly; no arithmetic of its own.
    """
    quantity_base: DerivedAmount | None = None
    notional_quote: DerivedAmount | None = None
    contract_denominated = payload.quantity_native_unit == _CONTRACTS_UNIT

    if contract_denominated:
        if terms is None:
            return (
                _blocked(
                    I04B_METHODOLOGY_ID,
                    I04B_METHODOLOGY_ID,
                    MissingnessReason.CONVERSION_BLOCKED,
                ),
                None,
            )
        if terms.payoff_type.value == "INVERSE" and terms.inverse_flag:
            face = inverse_quote_face(
                payload.quantity_native, payload.quantity_native_unit, terms
            )
            notional_quote = _from_conversion(face)
            if face.normalized_value is None:
                quantity_base = _blocked(
                    I04B_METHODOLOGY_ID,
                    I04B_METHODOLOGY_ID,
                    MissingnessReason.CONVERSION_BLOCKED,
                )
            elif reference_price is None or knowledge_cutoff is None:
                quantity_base = _blocked(
                    I04B_METHODOLOGY_ID,
                    I04B_METHODOLOGY_ID,
                    MissingnessReason.CONVERSION_BLOCKED,
                )
                flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
            else:
                quantity_base = _from_conversion(
                    inverse_base_from_quote(
                        face.normalized_value,
                        terms.price_unit,
                        terms,
                        reference_price,
                        knowledge_cutoff,
                    )
                )
            return quantity_base, notional_quote

        quantity_base = _from_conversion(
            linear_base_exposure(
                payload.quantity_native, payload.quantity_native_unit, terms
            )
        )
        if reference_price is None or knowledge_cutoff is None:
            notional_quote = _blocked(
                I04B_METHODOLOGY_ID,
                I04B_METHODOLOGY_ID,
                MissingnessReason.CONVERSION_BLOCKED,
            )
            flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
        else:
            notional_quote = _from_conversion(
                contracts_to_quote_notional(
                    payload.quantity_native,
                    payload.quantity_native_unit,
                    terms,
                    reference_price,
                    knowledge_cutoff,
                )
            )
        return quantity_base, notional_quote

    if terms is None or payload.quantity_native_unit == terms.quantity_unit:
        # Nothing to derive: the native quantity is already base-denominated, or
        # there are no PIT terms to convert against.  Re-labelling would be a claim.
        return None, None

    return (
        _blocked(
            I04B_METHODOLOGY_ID,
            I04B_METHODOLOGY_ID,
            MissingnessReason.CONVERSION_BLOCKED,
        ),
        None,
    )


def _usd_refusal() -> DerivedAmount:
    """``liquidation_usd`` is blocked while ``B5_I08_UNITS_V1`` is unresolved."""
    return _blocked(
        I08_UNITS_METHODOLOGY_ID,
        I08_UNITS_METHODOLOGY_ID,
        MissingnessReason.CONVERSION_BLOCKED,
        unresolved_citation=I08_UNITS_METHODOLOGY_ID,
    )


def _quality(
    *, quarantined: bool, identity_resolved: bool, coverage_ok: bool
) -> T1Quality:
    if quarantined:
        return T1Quality(
            identity_quality=QualityDimensionState.PARTIAL,
            time_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
            semantic_quality=QualityDimensionState.QUARANTINED,
            unit_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
            lineage_quality=QualityDimensionState.VERIFIED,
            source_integrity_quality=QualityDimensionState.VERIFIED,
            coverage_quality=QualityDimensionState.QUARANTINED,
            replay_quality=QualityDimensionState.UNKNOWN,
        )
    return T1Quality(
        identity_quality=(
            QualityDimensionState.ACCEPTABLE_WITH_FLAGS
            if identity_resolved
            else QualityDimensionState.PARTIAL
        ),
        time_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        semantic_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        unit_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        lineage_quality=QualityDimensionState.VERIFIED,
        source_integrity_quality=QualityDimensionState.VERIFIED,
        coverage_quality=(
            QualityDimensionState.VERIFIED
            if coverage_ok
            else QualityDimensionState.PARTIAL
        ),
        replay_quality=QualityDimensionState.UNKNOWN,
    )


def normalize_liquidation(
    payload: LiquidationObservationInput,
    *,
    terms: ContractTermsSnapshot | None = None,
    reference_price: ReferencePriceEvidence | None = None,
    knowledge_cutoff: datetime | None = None,
) -> T1LiquidationRecord:
    """Normalize one liquidation observation.  Pure, deterministic, fail-closed.

    Four outcomes, each explicit:

    * **quarantined** -- the provider's own sides contradict each other
      (LONG+BUY / SHORT+SELL).  The row is retained with a typed cause,
      evidence refs and a remediation note; nothing is reconciled by guessing.
    * **provisional** -- side semantics are not certified, so the canonical
      side slots stay ``UNKNOWN`` while the provider's reading is preserved.
    * **verified** -- the caller established the provider's semantics; both
      sides are carried in their own fields.
    * **unverified zero** -- zero reported without a completed-interval claim
      and verified coverage; retained as native evidence, never promoted.
    """
    if (
        terms is not None
        and payload.contract_instance_id is not None
        and terms.contract_instance_id != payload.contract_instance_id
    ):
        raise ValueError(
            "payload contract_instance_id "
            f"{payload.contract_instance_id!r} contradicts the PIT terms' "
            f"{terms.contract_instance_id!r}; an observation is normalized "
            "against its own contract instance or not at all (bloc_05/07 F3)"
        )

    contradiction = _contradicts(
        payload.position_side_liquidated, payload.execution_side
    )
    verified = payload.provider_semantics_verified and not contradiction
    zero_state = _zero_state(payload)

    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }
    if payload.liquidation_event_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)
    if zero_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING:
        flags.add(NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED)

    quantity_base, notional_quote = _derived_amounts(
        payload, terms, reference_price, knowledge_cutoff, flags
    )
    if any(
        amount is not None and amount.blocked
        for amount in (quantity_base, notional_quote)
    ):
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
    flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)

    conversion_refs: list[str] = []
    for amount in (quantity_base, notional_quote):
        if amount is None:
            continue
        for ref in amount.conversion_lineage_refs:
            if ref not in conversion_refs:
                conversion_refs.append(ref)

    lineage = T1LineageRef(
        raw_projection_refs=payload.raw_projection_refs,
        acquisition_refs=payload.acquisition_refs,
        evidence_blob_hashes=payload.evidence_blob_hashes,
        conversion_lineage_refs=tuple(conversion_refs),
        code_version=payload.code_version,
        config_version=payload.config_version,
    )

    native_values = [
        NativeQuantity(
            native_field_name="qty",
            native_value=payload.quantity_native,
            native_unit_evidence=payload.native_unit_evidence,
            source_unit_contract=payload.source_unit_contract,
        )
    ]
    if payload.price_native is not None:
        native_values.append(
            NativeQuantity(
                native_field_name="price", native_value=payload.price_native
            )
        )

    common: dict[str, Any] = dict(
        sensor_family=SensorFamily.MECHANICAL_LIQUIDATION,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.liquidation_event_id,
        native_sequence_id=payload.native_sequence_id,
        contract_instance_id=payload.contract_instance_id,
        normalization_generation=payload.normalization_generation,
        source_revision_id=payload.source_revision_id,
        source_revision_state=payload.source_revision_state,
        source_coverage_state=payload.source_coverage_state,
        time=ObservationTimeEnvelope(
            source_event_at=payload.event_at,
            observed_at=payload.observed_at,
            ingested_at=payload.ingested_at,
            market_available_at=payload.market_available_at,
            availability_basis=payload.availability_basis,
            source_precision=payload.source_precision,
        ),
        native_values=tuple(native_values),
        lineage_state=LineageState.LINEAGE_COMPLETE,
        lineage=lineage,
        quality_flags=_canonical_flags(flags),
        versions=T1VersionContext(),
        liquidation_event_id=payload.liquidation_event_id,
        maker_taker_role=payload.maker_taker_role,
        quantity_native=payload.quantity_native,
        quantity_native_unit=payload.quantity_native_unit,
        quantity_base=quantity_base,
        liquidation_quote_notional=notional_quote,
        liquidation_usd=_usd_refusal(),
        price_native=payload.price_native,
        price_reference=payload.price_reference,
        count=payload.count,
        aggregation_scope=payload.aggregation_scope,
        provisional_position_side=payload.position_side_liquidated,
        provisional_execution_side=payload.execution_side,
        native_position_side_field=payload.native_position_side_field,
        native_position_side_value=payload.native_position_side_value,
        native_execution_side_field=payload.native_execution_side_field,
        native_execution_side_value=payload.native_execution_side_value,
        zero_interval_state=zero_state,
        normalization_methodology_id=None,
        normalization_methodology_version=None,
    )

    if contradiction:
        return T1LiquidationRecord(
            **common,
            normalization_status=NormalizationStatus.QUARANTINED,
            missingness_reason=MissingnessReason.QUARANTINED,
            quality=_quality(
                quarantined=True,
                identity_resolved=payload.contract_instance_id is not None,
                coverage_ok=False,
            ),
            quarantine_reason=QuarantineReason.INVALID_SIDE_MAPPING,
            quarantine_evidence_refs=payload.raw_projection_refs,
            quarantine_remediation=(
                "Re-acquire the provider payload with its own side fields intact "
                "and confirm whether the field denotes the liquidated position or "
                "the execution side; do not derive one from the other, from price "
                "movement, or from a provider aggregate direction "
                "(bloc_05/04 section 3.1)."
            ),
            position_side_liquidated=LiquidationPositionSide.UNKNOWN,
            execution_side=AggressorSide.UNKNOWN,
            aggressor_side=AggressorSide.UNKNOWN,
        )

    position = (
        payload.position_side_liquidated
        if verified
        else LiquidationPositionSide.UNKNOWN
    )
    execution = payload.execution_side if verified else AggressorSide.UNKNOWN
    aggressor = payload.aggressor_side if verified else AggressorSide.UNKNOWN

    missingness = (
        MissingnessReason.SOURCE_GAP
        if zero_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING
        else None
    )

    return T1LiquidationRecord(
        **common,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        missingness_reason=missingness,
        quality=_quality(
            quarantined=False,
            identity_resolved=payload.contract_instance_id is not None,
            coverage_ok=zero_state is not LiquidationZeroIntervalState.UNVERIFIED_MISSING,
        ),
        position_side_liquidated=position,
        execution_side=execution,
        aggressor_side=aggressor,
    )
