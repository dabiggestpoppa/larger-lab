"""SENSOR-B5-I10E1 - provider-neutral trade observation normalizer.

The I10 realization of ``BLOC_05_I10D1_DECISION_PACKAGE.md`` sections 3, 5, 6 and
9.2: a typed trade-specific T1 record over the accepted ``T1BaseEnvelope``, and a
pure ``normalize_trade`` that preserves native truth while refusing to invent
canonical certainty.

What the record adds to the base envelope is exactly the trade-specific surface
bloc_05/03 section 2 and section 18 contemplate (``normalization/sensors/``), so
no sealed I01/I02/I06 interface is modified and the unfinished
``T1ObservationEnvelope`` stays unexported:

* ``price_canonical`` / ``quantity_base`` / ``notional_quote`` / ``notional_usd``
  as :class:`DerivedAmount` carriers, each citing its own methodology identity;
* the canonical ``aggressor_side`` plus the four side roles, all typed with the
  frozen ``contracts.enums.AggressorSide`` vocabulary (re-used, never re-declared);
* ``provisional_side``: the computed-but-unadmitted side, in a different type;
* ``native_side_field`` / ``native_side_boolean``: the raw provider boolean,
  preserved verbatim per operator ruling R2;
* ``aggregation_type`` / ``source_trade_count`` / ``trade_flags``;
* the record-level ``normalization_methodology_id`` / ``_version`` slots under
  bloc_05/03 section 2's own field names, so a later composite release is a move
  rather than a rename.  They stay ``None`` at I10 because no methodology id may
  be minted for the row shape itself (rulings R2/R6).

Economic honesty, enforced rather than documented:

* native values live in the inherited ``native_values`` and no canonical field
  can overwrite them (bloc_05/07 F12);
* an unavailable derived amount is ``None`` with a typed
  :class:`~crypto_sensor_fabric.normalization.enums.MissingnessReason` -- never
  an economic zero (bloc_05/03 section 14, F13) and never a placeholder;
* every derived amount names the accepted conversion primitive, its version, its
  consumed inputs and its lineage (bloc_05/03 section 22 inv.7);
* the USD step is BLOCKED while ``B5_I08_UNITS_V1`` has no lawful
  ``sensor_family`` representation (ruling R6).  No 1 USDT = 1 USD shortcut
  exists here, and a blocked amount keeps the unresolved citation visible
  instead of dropping it;
* duplicate collapse, fingerprinting and replay verdicts do NOT appear: they are
  I17's and I06's (ruling R5, bloc_05/04 section 2.3, bloc_05/06 section 1 G7).

No network, no wall clock, no id generation, no filesystem: a payload in, a
record out, byte-identical for byte-identical input.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from ...contracts.enums import AggregationType, AggressorSide, SensorFamily
from ...storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitEvidence,
)
from ..enums import (
    _FLAG_ORDER,
    AvailabilityBasis,
    LineageState,
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    QualityDimensionState,
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
    ConversionResult,
    ReferencePriceEvidence,
    contracts_to_quote_notional,
    inverse_base_from_quote,
    inverse_quote_face,
    linear_base_exposure,
)
from ..authority import (
    MappingProvenance,
    SemanticAuthority,
    resolve_authority_inputs,
)
from ..common.semantic_registry import ProviderSemanticRegistry
from ..terms.snapshot import ContractTermsSnapshot
from .side_maps import (
    ProvisionalSideMapping,
    SideEvidence,
    SideEvidenceKind,
    apply_side_map,
    resolve_side_mapping,
)

__all__ = [
    "I04B_METHODOLOGY_ID",
    "I08_UNITS_METHODOLOGY_ID",
    "DerivedAmount",
    "T1TradeRecord",
    "TradeObservationInput",
    "normalize_trade",
]

#: The accepted I04B conversion primitive's methodology identity, cited verbatim
#: (``normalization/terms/conversion.py::METHODOLOGY_VERSION``).  A constant, so
#: that a call site cannot paraphrase it; a test asserts the two stay equal.
I04B_METHODOLOGY_ID = "B5_I04B_CONVERSION_V1"

#: The unresolved cross-family unit methodology, cited verbatim
#: (``normalization/common/conversion.py::METHODOLOGY_VERSION``).  Recorded as a
#: *reference* and never resolved: ruling R6 keeps the derived USD output blocked
#: until an operator rules a lawful ``sensor_family`` representation for it.
I08_UNITS_METHODOLOGY_ID = "B5_I08_UNITS_V1"

#: The canonical quantity unit token meaning "this quantity counts contracts".
#: Taken from the frozen ``CanonicalQuantityUnit`` vocabulary rather than
#: re-spelled, so contract denomination is recognized by vocabulary and not by
#: pattern-matching a provider payload.
_CONTRACTS_UNIT = "CONTRACTS"

#: Quote assets whose USD equivalent needs the unresolved ``B5_I08_UNITS_V1``
#: methodology.  Named explicitly so the stablecoin-specific quality flag is
#: raised only where it is true, instead of on every row.
_STABLECOIN_QUOTES = frozenset({"USDT", "USDC"})


class DerivedAmount(NormalizationModelBase):
    """One derived canonical amount, or a typed refusal to compute one.

    The shape mirrors the accepted :class:`ConversionResult` discipline
    (bloc_05/03 section 22): a value is never present without its unit,
    methodology, version and consumed-input lineage, and an absent value is
    always ``None`` plus a typed missingness cause -- never ``0``.

    ``unresolved_citation`` is what keeps ruling R6 auditable: a blocked amount
    whose cause is an unresolved methodology records that methodology's id, so
    the block is attributable rather than merely absent.
    """

    value: Decimal | None
    blocked: bool
    missingness_reason: MissingnessReason | None = None
    methodology_id: OpaqueIdentifier
    methodology_version: OpaqueIdentifier
    output_unit: OpaqueIdentifier | None = None
    conversion_lineage_refs: tuple[OpaqueIdentifier, ...] = ()
    unresolved_citation: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _amount_laws(self) -> DerivedAmount:
        if self.blocked != (self.value is None):
            raise ValueError(
                "blocked must be exactly 'value is None': a blocked amount is "
                "absent (never zero) and a present amount is never blocked "
                "(bloc_05/03 section 14, bloc_05/07 F13)"
            )
        if self.blocked:
            if self.missingness_reason is None:
                raise ValueError(
                    "a blocked derived amount requires a typed missingness_reason "
                    "(bloc_05/05 section 12): absence is never a bare None"
                )
            if self.conversion_lineage_refs:
                raise ValueError(
                    "a blocked derived amount must not claim consumed conversion "
                    "inputs (bloc_05/03 section 22 inv.7)"
                )
            return self
        if self.missingness_reason is not None:
            raise ValueError(
                "a present derived amount must not carry a missingness_reason"
            )
        if self.output_unit is None:
            raise ValueError("a present derived amount requires an explicit output unit")
        if not self.conversion_lineage_refs:
            raise ValueError(
                "a present derived amount requires conversion input lineage "
                "(bloc_05/03 section 22 inv.7)"
            )
        return self


class TradeObservationInput(NormalizationModelBase):
    """Transport-neutral trade observation, before any canonical claim.

    Deliberately provider-neutral (ruling R1): the only provider-specific thing a
    caller supplies is a :class:`SideEvidence`, and the normalizer resolves it
    through the I09 registry.  Native price, quantity, unit and the raw side
    boolean are carried verbatim; identity, time and lineage references are
    caller-supplied durable values, never derived here.

    ``native_event_id`` is Optional because a provider may genuinely supply no
    trade id (OP-T10-A04); the normalizer flags that absence rather than
    synthesizing a key, which is what keeps I17's eligibility input honest.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_event_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    price_native: Decimal
    quantity_native: Decimal
    quantity_native_unit: OpaqueIdentifier
    native_unit_evidence: SourceUnitEvidence | None = None
    source_unit_contract: SourceUnitContract | None = None

    side_evidence: SideEvidence
    aggregation_type: AggregationType = AggregationType.INDIVIDUAL
    source_trade_count: int | None = Field(default=None, ge=1)
    trade_flags: tuple[OpaqueIdentifier, ...] = ()

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
    def _aggregation_law(self) -> TradeObservationInput:
        if self.aggregation_type is AggregationType.AGGREGATED:
            if self.source_trade_count is None:
                raise ValueError(
                    "aggregation_type=AGGREGATED requires source_trade_count; an "
                    "aggregate that cannot say how many trades it covers cannot be "
                    "compared with an individual trade (bloc_05/04 section 2.1)"
                )
        elif self.source_trade_count is not None:
            raise ValueError(
                "aggregation_type=INDIVIDUAL must not carry source_trade_count"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> TradeObservationInput:
        for name in (
            "raw_projection_refs",
            "acquisition_refs",
            "evidence_blob_hashes",
            "trade_flags",
        ):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1TradeRecord(T1BaseEnvelope):
    """Trade-specific T1 record (bloc_05/03 section 2/18; decision package 9.2).

    Extends the accepted base envelope and adds only trade-owned fields.  The
    inherited laws still apply unchanged -- typed missingness, canonical flag
    ordering, the lineage/flag agreement, the blocking-flag refusal -- so this
    subclass cannot relax the ratified base contract; it can only add.

    Two trade-specific laws are enforced beyond the base:

    * an ``INDIVIDUAL`` record carries no ``source_trade_count``, and an
      ``AGGREGATED`` one carries it (an aggregate is not expanded into fake
      individual events -- OP-T10-D05);
    * the canonical ``aggressor_side`` may equal ``provisional_side.mapped_side``
      ONLY when that provisional mapping was admitted.  This is the structural
      form of ruling R2: the provisional value cannot reach the canonical field
      by being copied, only by the evidence ladder clearing it.
    """

    price_canonical: DerivedAmount | None = None
    quantity_base: DerivedAmount | None = None
    notional_quote: DerivedAmount | None = None
    notional_usd: DerivedAmount | None = None

    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    maker_side: AggressorSide = AggressorSide.UNKNOWN
    buyer_side: AggressorSide = AggressorSide.UNKNOWN
    seller_side: AggressorSide = AggressorSide.UNKNOWN
    provisional_side: ProvisionalSideMapping | None = None

    native_side_field: OpaqueIdentifier | None = None
    native_side_boolean: bool | None = None

    trade_flags: tuple[OpaqueIdentifier, ...] = ()
    aggregation_type: AggregationType = AggregationType.INDIVIDUAL
    source_trade_count: int | None = Field(default=None, ge=1)

    normalization_methodology_id: OpaqueIdentifier | None = None
    normalization_methodology_version: OpaqueIdentifier | None = None

    #: SENSOR-B5-I09P2b: what the canonical side claims about its
    #: authorization.  Present only when the side was actually admitted;
    #: a consumer re-derives it with ``verify_mapping_provenance``.
    authority_provenance: MappingProvenance | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1TradeRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_TRADE:
            raise ValueError(
                "T1TradeRecord requires sensor_family=MECHANICAL_TRADE, got "
                f"{self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _aggregation_law(self) -> T1TradeRecord:
        if self.aggregation_type is AggregationType.AGGREGATED:
            if self.source_trade_count is None:
                raise ValueError(
                    "aggregation_type=AGGREGATED requires source_trade_count"
                )
        elif self.source_trade_count is not None:
            raise ValueError(
                "aggregation_type=INDIVIDUAL must not carry source_trade_count"
            )
        return self

    @model_validator(mode="after")
    def _provisional_admission_law(self) -> T1TradeRecord:
        provisional = self.provisional_side
        if provisional is None:
            return self
        if (
            self.aggressor_side is provisional.mapped_side
            and not provisional.canonical_admitted
        ):
            raise ValueError(
                "the canonical aggressor_side equals a provisional mapping that "
                "was not admitted; ruling R2 requires canonical UNKNOWN until "
                "provider semantics are verified (schema rule B1-T10)"
            )
        return self

    @model_validator(mode="after")
    def _native_side_law(self) -> T1TradeRecord:
        if self.native_side_boolean is not None and self.native_side_field is None:
            raise ValueError(
                "a preserved native side boolean requires the provider field it "
                "came from; an unattributed boolean is not evidence"
            )
        return self


def _blocked(
    methodology_id: str,
    methodology_version: str,
    reason: MissingnessReason,
    *,
    unresolved_citation: str | None = None,
    output_unit: str | None = None,
) -> DerivedAmount:
    return DerivedAmount(
        value=None,
        blocked=True,
        missingness_reason=reason,
        methodology_id=methodology_id,
        methodology_version=methodology_version,
        output_unit=output_unit,
        conversion_lineage_refs=(),
        unresolved_citation=unresolved_citation,
    )


def _from_conversion(result: ConversionResult) -> DerivedAmount:
    """Lift an accepted I04B result into a :class:`DerivedAmount`.

    Both branches are carried verbatim: a successful primitive contributes its
    value, output unit and consumed-input lineage; a refused one contributes its
    typed absence and NO consumed inputs, exactly as I04B itself decided.  This
    function adds no arithmetic of its own.
    """
    if result.normalized_value is None:
        return _blocked(
            methodology_id=I04B_METHODOLOGY_ID,
            methodology_version=result.methodology_version,
            reason=MissingnessReason.CONVERSION_BLOCKED,
        )
    return DerivedAmount(
        value=result.normalized_value,
        blocked=False,
        missingness_reason=None,
        methodology_id=I04B_METHODOLOGY_ID,
        methodology_version=result.methodology_version,
        output_unit=result.output_unit,
        conversion_lineage_refs=tuple(result.conversion_inputs),
        unresolved_citation=None,
    )


def _canonical_flags(
    flags: set[NormalizationQualityFlag],
) -> tuple[NormalizationQualityFlag, ...]:
    """Canonical, duplicate-free flag ordering the base envelope requires."""
    return tuple(sorted(flags, key=_FLAG_ORDER.__getitem__))


def normalize_trade(
    payload: TradeObservationInput,
    *,
    registry: ProviderSemanticRegistry | SemanticAuthority | None = None,
    terms: ContractTermsSnapshot | None = None,
    reference_price: ReferencePriceEvidence | None = None,
    knowledge_cutoff: datetime | None = None,
) -> T1TradeRecord:
    """Normalize one trade observation.  Pure, deterministic, fail-closed.

    ``registry`` carries EITHER a loader-issued
    :class:`~crypto_sensor_fabric.normalization.common.authority.SemanticAuthority`
    (the only thing that may promote a canonical aggressor side) OR a bare I09
    ``ProviderSemanticRegistry``, which stays a DIAGNOSTIC value: its rows are
    resolved so a provisional reading can still be computed, but no canonical
    field is admitted from it (SENSOR-B5-I09P2A).

    Raises ``ValueError`` for the one contradiction the record cannot represent:
    a payload whose ``contract_instance_id`` disagrees with the supplied PIT
    terms (bloc_05/07 F3 -- the observation must belong to the contract the terms
    describe).  Every other unease is expressed as a typed flag or a blocked
    derived amount, never as an exception and never as a guess.
    """
    if (
        terms is not None
        and payload.contract_instance_id is not None
        and terms.contract_instance_id != payload.contract_instance_id
    ):
        raise ValueError(
            "payload contract_instance_id "
            f"{payload.contract_instance_id!r} contradicts the PIT terms' "
            f"{terms.contract_instance_id!r}; an observation is normalized against "
            "its own contract instance or not at all (bloc_05/07 F3)"
        )

    authority, registry = resolve_authority_inputs(registry, None)

    # -- side: provisional only; canonical stays UNKNOWN unless approved -----
    evidence = payload.side_evidence
    mapping = None
    if (
        evidence.kind is SideEvidenceKind.PROVIDER_BOOLEAN_FIELD
        and evidence.provider_field
        and registry is not None
    ):
        mapping = resolve_side_mapping(
            registry,
            payload.provider,
            evidence.provider_field,
            SensorFamily.MECHANICAL_TRADE,
        )
    provisional = apply_side_map(evidence, mapping)
    # Three conjuncts, all required: the ladder must admit, an approval must
    # exist, and that approval must cover THIS row.  A caller-minted registry
    # satisfies the first and neither of the others.
    canonical_side = (
        provisional.mapped_side
        if provisional is not None
        and provisional.canonical_admitted
        and mapping is not None
        and authority is not None
        and authority.attests(mapping) is None
        else AggressorSide.UNKNOWN
    )

    provenance = (
        MappingProvenance(
            artifact_id=authority.artifact_id,
            approval_id=authority.approval_id,
            registry_digest=authority.registry_digest,
            provider=mapping.provider,
            provider_field=mapping.provider_field,
            canonical_field=mapping.canonical_field,
            canonical_sensor=mapping.canonical_sensor.value,
            methodology_id=mapping.methodology_id,
            methodology_version=mapping.version,
            evidence_reference=mapping.evidence_reference,
            semantic_confidence=mapping.semantic_confidence.value,
            approved_at=authority.approved_at,
            available_at=authority.available_at,
        )
        if (
            canonical_side is not AggressorSide.UNKNOWN
            and mapping is not None
            and authority is not None
            and mapping.methodology_id is not None
        )
        else None
    )

    # -- native values: preserved verbatim, never overwritten --------------
    native_values = (
        NativeQuantity(native_field_name="price", native_value=payload.price_native),
        NativeQuantity(
            native_field_name="qty",
            native_value=payload.quantity_native,
            native_unit_evidence=payload.native_unit_evidence,
            source_unit_contract=payload.source_unit_contract,
        ),
    )

    # -- derived amounts: I04B where honestly available, else typed refusal -
    quantity_base: DerivedAmount | None = None
    notional_quote: DerivedAmount | None = None
    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }

    contract_denominated = payload.quantity_native_unit == _CONTRACTS_UNIT

    if contract_denominated:
        if terms is None:
            quantity_base = _blocked(
                I04B_METHODOLOGY_ID,
                I04B_METHODOLOGY_ID,
                MissingnessReason.CONVERSION_BLOCKED,
            )
        elif terms.payoff_type.value == "INVERSE" and terms.inverse_flag:
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
        else:
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
    elif terms is None:
        # No PIT terms supplied and the native quantity is not contract-counted:
        # nothing is convertible here, so nothing is claimed and nothing blocked.
        quantity_base = None
        notional_quote = None
    elif payload.quantity_native_unit == terms.quantity_unit:
        # Already base-denominated: the native value IS the base quantity, so
        # there is nothing to derive, and re-labelling it would be a claim.
        quantity_base = None
        notional_quote = None
    else:
        quantity_base = _blocked(
            I04B_METHODOLOGY_ID,
            I04B_METHODOLOGY_ID,
            MissingnessReason.CONVERSION_BLOCKED,
        )

    # -- the unresolved cross-family step stays blocked (ruling R6) --------
    notional_usd = _blocked(
        I08_UNITS_METHODOLOGY_ID,
        I08_UNITS_METHODOLOGY_ID,
        MissingnessReason.CONVERSION_BLOCKED,
        unresolved_citation=I08_UNITS_METHODOLOGY_ID,
    )

    # -- flags reflect exactly what was refused ----------------------------
    if any(
        amount is not None and amount.blocked
        for amount in (quantity_base, notional_quote)
    ):
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
    if notional_usd.blocked:
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
        quote_asset = terms.quote_asset_id if terms is not None else None
        if (
            quote_asset in _STABLECOIN_QUOTES
            or payload.quantity_native_unit in _STABLECOIN_QUOTES
        ):
            flags.add(NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE)
    if payload.native_event_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)

    # -- lineage: aggregate the conversion refs, duplicate-free -------------
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

    quality = T1Quality(
        identity_quality=(
            QualityDimensionState.ACCEPTABLE_WITH_FLAGS
            if payload.contract_instance_id is not None
            else QualityDimensionState.PARTIAL
        ),
        time_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        semantic_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        unit_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        lineage_quality=QualityDimensionState.VERIFIED,
        source_integrity_quality=QualityDimensionState.VERIFIED,
        coverage_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        replay_quality=QualityDimensionState.UNKNOWN,
    )

    return T1TradeRecord(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.native_event_id,
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
        native_values=native_values,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        missingness_reason=None,
        lineage_state=LineageState.LINEAGE_COMPLETE,
        lineage=lineage,
        quality=quality,
        quality_flags=_canonical_flags(flags),
        versions=T1VersionContext(),
        price_canonical=None,
        quantity_base=quantity_base,
        notional_quote=notional_quote,
        notional_usd=notional_usd,
        aggressor_side=canonical_side,
        provisional_side=provisional,
        native_side_field=evidence.provider_field,
        native_side_boolean=evidence.boolean_value,
        trade_flags=payload.trade_flags,
        aggregation_type=payload.aggregation_type,
        source_trade_count=payload.source_trade_count,
        normalization_methodology_id=None,
        normalization_methodology_version=None,
        authority_provenance=provenance,
    )
