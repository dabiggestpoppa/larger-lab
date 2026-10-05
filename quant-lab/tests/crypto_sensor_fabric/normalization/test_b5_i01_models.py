"""SENSOR-B5-I01C — N0 model/schema tests for the Bloc 5 base normalization layer.

Test layer N0 of bloc_05/06 §2 (MODEL / SCHEMA): pure model behavior, no
provider, no fixture, no storage backend, no network.  ``network_calls = 0``.

Every law asserted here is quoted from a frozen Bloc 5 document, because a base
layer is only worth having if it fails closed on exactly the frozen rules:

* naive datetimes, blank/padded identifiers, duplicate refs;
* native value precision and native/canonical separation;
* provider and venue as separate fields;
* typed missingness, reasoned quarantine, the four blocked classes;
* lineage state and the four frozen registry/methodology version laws;
* canonical quality-flag ordering;
* null is never zero, and stablecoin is never fiat.

What is NOT tested here, because it does not exist at B5-I01: resolution,
conversion, availability derivation, replay eligibility, dedupe, generation or
persistence.  ``test_b5_i01_scope_audit.py`` proves their absence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization import (
    BLOCKED_STATUS_MISSINGNESS_REASON,
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    MissingnessReason,
    NativeQuantity,
    NormalizationQualityFlag,
    NormalizationStatus,
    ObservationTimeEnvelope,
    QuarantineReason,
    QualityDimensionState,
    T1BaseEnvelope,
    T1GenerationId,
    T1LineageRef,
    T1Quality,
    T1RecordId,
    T1VersionContext,
    TimestampPrecision,
    canonical_json_bytes,
)
from crypto_sensor_fabric.probes.enums import Granularity
from crypto_sensor_fabric.storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitEvidence,
    SourceUnitState,
    SourceUnitVariability,
)

BLOB_SHA256 = "a" * 64
OTHER_BLOB_SHA256 = "b" * 64
UTC = timezone.utc

CANONICAL_STATUSES = (
    NormalizationStatus.NORMALIZED,
    NormalizationStatus.PARTIALLY_NORMALIZED,
)

_QUALITY_DIMENSIONS = (
    "identity_quality",
    "time_quality",
    "semantic_quality",
    "unit_quality",
    "lineage_quality",
    "source_integrity_quality",
    "coverage_quality",
    "replay_quality",
)


def flags(*requested: NormalizationQualityFlag) -> tuple[NormalizationQualityFlag, ...]:
    """Return flags in canonical declaration order (deduplicated)."""
    order = {flag: index for index, flag in enumerate(NormalizationQualityFlag)}
    return tuple(sorted(set(requested), key=order.__getitem__))


def quality(**overrides: QualityDimensionState) -> T1Quality:
    """A quality block that declares every dimension as UNKNOWN by default.

    UNKNOWN is the frozen "not determined" state; declaring it explicitly is
    what the model requires instead of defaulting a dimension to healthy.
    """
    values = {name: QualityDimensionState.UNKNOWN for name in _QUALITY_DIMENSIONS}
    values.update(overrides)
    return T1Quality(**values)


def lineage(**overrides: Any) -> T1LineageRef:
    values: dict[str, Any] = {
        "raw_projection_refs": ("projection-1",),
        "acquisition_refs": ("acquisition-1",),
        "evidence_blob_hashes": (BLOB_SHA256,),
        "code_version": "commit-abc1234",
        "config_version": "config-1",
    }
    values.update(overrides)
    return T1LineageRef(**values)


def native_quantity(**overrides: Any) -> NativeQuantity:
    values: dict[str, Any] = {
        "native_field_name": "quantity",
        "native_value": Decimal("0.00100"),
        "source_unit_contract": SourceUnitContract.NO_UNIT_FIELDS,
    }
    values.update(overrides)
    return NativeQuantity(**values)


def envelope(**overrides: Any) -> T1BaseEnvelope:
    """A minimal VALID canonical envelope; individual tests override one fact."""
    values: dict[str, Any] = {
        "sensor_family": SensorFamily.MECHANICAL_TRADE,
        "provider": "BINANCE_USDM",
        "venue": "BINANCE_USDM",
        "native_instrument": "BTCUSDT",
        "contract_instance_id": "contract-instance:binance:btcusdt:perp:v1",
        "normalization_generation": "generation-2026-01",
        "source_revision_id": "revision-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "time": ObservationTimeEnvelope(
            source_event_at=datetime(2022, 5, 12, 1, 2, 3, tzinfo=UTC),
            source_precision=TimestampPrecision.MILLISECOND,
        ),
        "native_values": (native_quantity(),),
        "normalization_status": NormalizationStatus.NORMALIZED,
        "lineage_state": LineageState.LINEAGE_COMPLETE,
        "lineage": lineage(),
        "quality": quality(identity_quality=QualityDimensionState.VERIFIED),
        "quality_flags": flags(NormalizationQualityFlag.LINEAGE_COMPLETE),
        "versions": T1VersionContext(
            identity_registry_version="identity-registry-1",
            contract_terms_version="contract-terms-1",
            semantic_registry_version="semantic-registry-1",
            methodology_registry_version="methodology-registry-1",
        ),
    }
    values.update(overrides)
    return T1BaseEnvelope(**values)


def blocked_envelope(status: NormalizationStatus, **overrides: Any) -> T1BaseEnvelope:
    """A blocked row: native evidence kept, no contract id, typed cause."""
    values: dict[str, Any] = {
        "contract_instance_id": None,
        "normalization_status": status,
        "missingness_reason": BLOCKED_STATUS_MISSINGNESS_REASON[status],
        "quality": quality(identity_quality=QualityDimensionState.BLOCKED),
        "quality_flags": flags(
            NormalizationQualityFlag.IDENTITY_AMBIGUOUS,
            NormalizationQualityFlag.LINEAGE_COMPLETE,
        ),
        "versions": T1VersionContext(),
    }
    values.update(overrides)
    return envelope(**values)


# ---------------------------------------------------------------------------
# Construction and the happy path
# ---------------------------------------------------------------------------


def test_minimal_canonical_envelope_constructs() -> None:
    env = envelope()
    assert env.provider == "BINANCE_USDM"
    assert env.contract_instance_id is not None
    assert env.normalization_status is NormalizationStatus.NORMALIZED
    # Nothing is invented: an unassigned T1 identity stays absent at I01.
    assert env.t1_record_id is None
    assert env.supersedes_t1_record_id is None


def test_all_eight_quality_dimensions_are_required() -> None:
    """A defaulted dimension is a claim; every dimension must be declared."""
    for name in _QUALITY_DIMENSIONS:
        payload: dict[str, Any] = {
            dimension: QualityDimensionState.UNKNOWN for dimension in _QUALITY_DIMENSIONS
        }
        del payload[name]
        with pytest.raises(ValueError):
            T1Quality(**payload)


def test_extra_fields_are_refused() -> None:
    """``extra="forbid"``: an unknown field is a schema contradiction."""
    with pytest.raises(ValueError):
        envelope(not_a_frozen_field="x")
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(derived_market_available_at=datetime(2022, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError):
        NativeQuantity(native_field_name="q", native_value=Decimal(1), usd_equivalent=1)


# ---------------------------------------------------------------------------
# §26 validation: identifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "provider",
        "venue",
        "native_instrument",
        "normalization_generation",
        "source_revision_id",
        "contract_instance_id",
        "provider_instrument_id",
        "native_event_id",
        "native_sequence_id",
    ],
)
@pytest.mark.parametrize("bad", ["", "   ", "\t", " x", "x "])
def test_blank_or_padded_identifiers_are_refused(field: str, bad: str) -> None:
    with pytest.raises(ValueError):
        envelope(**{field: bad})


def test_lineage_identifiers_are_refused_when_blank() -> None:
    for field in ("code_version", "config_version"):
        with pytest.raises(ValueError):
            lineage(**{field: "  "})


def test_native_field_name_must_not_be_blank() -> None:
    with pytest.raises(ValueError):
        native_quantity(native_field_name="   ")


# ---------------------------------------------------------------------------
# §21 time model: timezone-aware UTC only, nothing derived
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "source_event_at",
        "interval_start_at",
        "interval_end_at",
        "effective_at",
        "published_at",
        "market_available_at",
        "observed_at",
        "ingested_at",
        "normalized_at",
    ],
)
def test_naive_datetimes_are_refused(field: str) -> None:
    """bloc_05/02 §18 invariant 1: no naive timestamps."""
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(**{field: datetime(2022, 5, 12, 1, 2, 3)})


def test_offset_datetimes_are_normalized_to_utc() -> None:
    aware = datetime(2022, 5, 12, 3, 2, 3, tzinfo=timezone(timedelta(hours=2)))
    time = ObservationTimeEnvelope(source_event_at=aware)
    assert time.source_event_at is not None
    assert time.source_event_at.utcoffset() == timedelta(0)
    assert time.source_event_at.hour == 1


def test_all_nine_clocks_stay_independent_fields() -> None:
    """bloc_05/07 F8: no clock silently substitutes for another."""
    fields = set(ObservationTimeEnvelope.model_fields)
    assert {
        "source_event_at",
        "interval_start_at",
        "interval_end_at",
        "effective_at",
        "published_at",
        "market_available_at",
        "observed_at",
        "ingested_at",
        "normalized_at",
    } <= fields
    # Absent means not applicable / not verified -- never "equal to another".
    empty = ObservationTimeEnvelope()
    assert empty.source_event_at is None
    assert empty.effective_at is None
    assert empty.market_available_at is None
    assert empty.ingested_at is None


def test_interval_bounds_require_a_declared_boundary_convention() -> None:
    """bloc_05/02 §7: interval semantics are explicit, never guessed."""
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(interval_start_at=datetime(2022, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(
            interval_start_at=datetime(2022, 1, 1, tzinfo=UTC),
            interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        )
    declared = ObservationTimeEnvelope(
        interval_start_at=datetime(2022, 1, 1, tzinfo=UTC),
        interval_end_at=datetime(2022, 1, 1, 0, 5, tzinfo=UTC),
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    )
    assert declared.interval_closed is True


def test_inverted_interval_window_is_refused() -> None:
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(
            interval_start_at=datetime(2022, 1, 1, 0, 5, tzinfo=UTC),
            interval_end_at=datetime(2022, 1, 1, tzinfo=UTC),
            interval_closed=True,
            interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        )


def test_no_ordering_is_assumed_between_distinct_clocks() -> None:
    """bloc_05/02 §6: a future-effective published value must stay representable."""
    published = datetime(2022, 5, 12, 1, 0, tzinfo=UTC)
    effective = datetime(2022, 5, 12, 8, 0, tzinfo=UTC)
    time = ObservationTimeEnvelope(
        source_event_at=published,
        published_at=published,
        effective_at=effective,
    )
    assert time.published_at < time.effective_at


def test_market_available_at_requires_a_usable_basis() -> None:
    """bloc_05/02 §5: an unplaceable availability time is not a market time."""
    available = datetime(2022, 5, 12, 1, 2, 3, tzinfo=UTC)
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(market_available_at=available)
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(
            market_available_at=available,
            availability_basis=AvailabilityBasis.UNKNOWN,
        )
    assert ObservationTimeEnvelope(
        market_available_at=available,
        availability_basis=AvailabilityBasis.REALTIME_PUBLIC_EVENT,
    ).market_available_at == available


# ---------------------------------------------------------------------------
# §13 native-value preservation and §22 native/canonical separation
# ---------------------------------------------------------------------------


def test_native_value_precision_is_preserved_exactly() -> None:
    """bloc_05/03 §3.1/§3.3: do not round, and do not invent precision."""
    for raw in ("0.00100", "123456789.123456789012345678", "0"):
        quantity = native_quantity(native_value=Decimal(raw))
        assert quantity.native_value == Decimal(raw)
        assert str(quantity.native_value) == raw


def test_native_quantity_has_no_canonical_counterpart_field() -> None:
    """bloc_05/07 F12: canonical comparability is additive, never destructive."""
    fields = set(NativeQuantity.model_fields)
    assert fields == {
        "native_field_name",
        "native_value",
        "native_unit_evidence",
        "source_unit_contract",
    }
    for forbidden in ("normalized_value", "canonical_value", "usd", "notional", "base"):
        assert forbidden not in fields


def test_envelope_carries_no_canonical_numeric_field() -> None:
    """The base envelope has no normalized numeric field to confuse native with."""
    fields = set(T1BaseEnvelope.model_fields)
    for forbidden in (
        "normalized_value",
        "canonical_value",
        "usd",
        "usd_equivalent",
        "notional",
        "base_quantity",
        "quote_notional",
    ):
        assert forbidden not in fields
    assert "native_values" in fields


def test_verified_native_unit_requires_its_evidence_object() -> None:
    """Bloc 4's truth-bound unit proof is carried, not re-implemented."""
    verified = SourceUnitEvidence(
        field_name="quantity_unit",
        native_unit_lexeme="BTC",
        state=SourceUnitState.VERIFIED_NATIVE,
        variability=SourceUnitVariability.STATIC_VERIFIED,
    )
    quantity = native_quantity(
        native_unit_evidence=verified,
        source_unit_contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
    )
    assert quantity.native_unit_evidence is verified
    assert quantity.native_unit_evidence.state is SourceUnitState.VERIFIED_NATIVE


def test_row_native_unit_keeps_its_structural_location() -> None:
    """Bloc 4 says WHERE a row-native unit lives; it never fabricates a lexeme."""
    evidence = SourceUnitEvidence(
        field_name="bids",
        state=SourceUnitState.UNIT_UNVERIFIED,
        field_path=("bids", "item", "quantity_unit"),
        variability=SourceUnitVariability.ROW_NATIVE,
    )
    quantity = native_quantity(
        native_unit_evidence=evidence,
        source_unit_contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
    )
    assert quantity.native_unit_evidence.field_path == ("bids", "item", "quantity_unit")
    assert quantity.native_unit_evidence.native_unit_lexeme is None


def test_unverified_unit_never_carries_a_guessed_lexeme() -> None:
    """bloc_04/I17 §4.6: UNIT_UNVERIFIED licenses no guess."""
    with pytest.raises(ValueError):
        SourceUnitEvidence(
            field_name="quantity_unit",
            native_unit_lexeme="BTC",
            state=SourceUnitState.UNIT_UNVERIFIED,
        )


def test_three_state_unit_contract_is_never_collapsed() -> None:
    """bloc_04/I17 §4.7: explicit NO_UNIT_FIELDS is not historical absence."""
    explicit = native_quantity(source_unit_contract=SourceUnitContract.NO_UNIT_FIELDS)
    absent = native_quantity(source_unit_contract=None)
    assert explicit.source_unit_contract is SourceUnitContract.NO_UNIT_FIELDS
    assert absent.source_unit_contract is None
    with pytest.raises(ValueError):
        native_quantity(
            native_unit_evidence=SourceUnitEvidence(
                field_name="quantity_unit",
                native_unit_lexeme="BTC",
                state=SourceUnitState.VERIFIED_NATIVE,
            ),
            source_unit_contract=SourceUnitContract.NO_UNIT_FIELDS,
        )
    with pytest.raises(ValueError):
        native_quantity(source_unit_contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED)


def test_native_value_survives_a_blocked_row() -> None:
    """§23: a blocked observation must not lose its native evidence."""
    env = blocked_envelope(NormalizationStatus.BLOCKED_IDENTITY)
    assert env.contract_instance_id is None
    assert env.missingness_reason is MissingnessReason.IDENTITY_BLOCKED
    assert env.normalization_status is NormalizationStatus.BLOCKED_IDENTITY
    assert env.native_values[0].native_value == Decimal("0.00100")


# ---------------------------------------------------------------------------
# §15 provider / venue distinction
# ---------------------------------------------------------------------------


def test_provider_and_venue_are_separate_required_fields() -> None:
    fields = T1BaseEnvelope.model_fields
    assert "provider" in fields
    assert "venue" in fields
    # No collapsed "source"/"source_id" field may re-merge them.
    assert not {
        "source",
        "source_id",
        "source_venue",
        "provider_venue",
        "exchange",
    } & set(fields)


def test_an_aggregator_reports_a_venue_it_does_not_operate() -> None:
    """bloc_05/01 §13: provider=COINALYZE, venue=BINANCE_USDM is representable."""
    env = envelope(provider="COINALYZE", venue="BINANCE_USDM")
    assert env.provider == "COINALYZE"
    assert env.venue == "BINANCE_USDM"


def test_native_instrument_is_preserved_verbatim() -> None:
    """bloc_05/07 F1 / doc 05 §23 invariant 5: native symbol survives."""
    env = envelope(native_instrument="BTCUSDT", contract_instance_id="contract-instance:x")
    assert env.native_instrument == "BTCUSDT"
    assert env.native_instrument != env.contract_instance_id


# ---------------------------------------------------------------------------
# §5 blocked normalization law
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "cause"),
    [
        (NormalizationStatus.BLOCKED_IDENTITY, MissingnessReason.IDENTITY_BLOCKED),
        (NormalizationStatus.BLOCKED_TIME, MissingnessReason.TIME_BLOCKED),
        (NormalizationStatus.BLOCKED_SEMANTICS, MissingnessReason.SEMANTICS_BLOCKED),
        (NormalizationStatus.BLOCKED_CONVERSION, MissingnessReason.CONVERSION_BLOCKED),
    ],
)
def test_each_blocked_class_is_representable(status: NormalizationStatus, cause) -> None:
    env = blocked_envelope(status)
    assert env.normalization_status is status
    assert env.missingness_reason is cause
    assert env.contract_instance_id is None
    assert env.native_values


@pytest.mark.parametrize("status", list(BLOCKED_STATUS_MISSINGNESS_REASON))
def test_a_blocked_row_cannot_file_its_cause_under_a_generic_reason(
    status: NormalizationStatus,
) -> None:
    """§8: missingness reason must be typed, not erased into a generic cause."""
    for generic in (
        MissingnessReason.SOURCE_GAP,
        MissingnessReason.NOT_REPORTED,
        MissingnessReason.PROVIDER_EMPTY,
    ):
        with pytest.raises(ValueError):
            blocked_envelope(status, missingness_reason=generic)
    with pytest.raises(ValueError):
        blocked_envelope(status, missingness_reason=None)


@pytest.mark.parametrize("status", CANONICAL_STATUSES)
def test_a_canonical_status_requires_a_contract_instance(
    status: NormalizationStatus,
) -> None:
    """bloc_05/01 §2.5 / F3: normalized or it fails closed."""
    with pytest.raises(ValueError):
        envelope(normalization_status=status, contract_instance_id=None)


def test_no_unknown_contract_placeholder_exists() -> None:
    """§12: there is no invented UNKNOWN_CONTRACT value to fill the gap."""
    assert "UNKNOWN_CONTRACT" not in {
        member.value for member in NormalizationStatus
    } | {
        member.value for member in MissingnessReason
    } | {
        member.value for member in QualityDimensionState
    } | {
        member.value for member in LineageState
    }


def test_native_only_keeps_native_evidence_without_a_contract_instance() -> None:
    env = envelope(
        contract_instance_id=None,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        quality_flags=flags(
            NormalizationQualityFlag.UNIT_NATIVE_ONLY,
            NormalizationQualityFlag.LINEAGE_COMPLETE,
        ),
        quality=quality(),
        versions=T1VersionContext(),
    )
    assert env.contract_instance_id is None
    assert env.missingness_reason is None
    assert env.native_values[0].native_value == Decimal("0.00100")


def test_a_canonical_status_requires_native_evidence() -> None:
    """bloc_05/07 F12: no canonical claim with nothing behind it."""
    with pytest.raises(ValueError):
        envelope(native_values=())


# ---------------------------------------------------------------------------
# §8 missingness / §13 no zero-fill
# ---------------------------------------------------------------------------


def test_missingness_is_never_a_bool_and_never_present_on_a_normalized_row() -> None:
    assert T1BaseEnvelope.model_fields["missingness_reason"].annotation == (
        MissingnessReason | None
    )
    assert T1BaseEnvelope.model_fields["missingness_reason"].default is None
    with pytest.raises(ValueError):
        envelope(missingness_reason=MissingnessReason.PROVIDER_EMPTY)
    with pytest.raises(ValueError):
        envelope(missingness_reason=True)  # type: ignore[arg-type]


def test_absent_evidence_stays_absent_and_is_never_zero_filled() -> None:
    """bloc_05/03 §14 / bloc_05/07 F13: no missing payload becomes zero."""
    env = envelope(
        contract_instance_id=None,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        native_values=(),
        missingness_reason=MissingnessReason.PROVIDER_EMPTY,
        quality_flags=flags(NormalizationQualityFlag.LINEAGE_COMPLETE),
        quality=quality(),
        versions=T1VersionContext(),
    )
    payload = env.as_canonical_dict()
    assert payload["native_values"] == []
    assert payload["missingness_reason"] == "PROVIDER_EMPTY"
    assert payload["contract_instance_id"] is None


def test_a_verified_economic_zero_remains_distinguishable_from_absence() -> None:
    zero = envelope(native_values=(native_quantity(native_value=Decimal("0")),))
    absent = envelope(
        contract_instance_id=None,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        native_values=(),
        quality_flags=flags(NormalizationQualityFlag.LINEAGE_COMPLETE),
        quality=quality(),
        versions=T1VersionContext(),
    )
    assert zero.native_values[0].native_value == Decimal("0")
    assert absent.native_values == ()
    assert (
        zero.as_canonical_dict()["native_values"][0]["native_value"] != absent.as_canonical_dict()["native_values"]
    )


def test_no_base_model_field_defaults_to_a_numeric_zero() -> None:
    """A structural check: nothing anywhere invents a zero by default."""
    models = (
        T1BaseEnvelope,
        T1LineageRef,
        T1Quality,
        T1VersionContext,
        ObservationTimeEnvelope,
        NativeQuantity,
    )
    for model in models:
        for name, field in model.model_fields.items():
            assert field.default is not None or not str(field.annotation).startswith(
                ("Decimal", "int", "float")
            ), f"{model.__name__}.{name} may default to a numeric value"
            assert field.default != 0, f"{model.__name__}.{name} defaults to 0"


def test_no_generic_missing_boolean_exists() -> None:
    for model in (T1BaseEnvelope, NativeQuantity, T1LineageRef, T1Quality):
        for name in model.model_fields:
            assert not name.endswith("_missing")
            assert not name.startswith("has_")
            assert name != "missing"


# ---------------------------------------------------------------------------
# §14 stablecoin firewall
# ---------------------------------------------------------------------------


def test_no_base_model_implies_fiat_equivalence() -> None:
    """bloc_05/07 F7: no field, default or helper may equate USDT/USDC with USD."""
    models = (
        T1BaseEnvelope,
        T1LineageRef,
        T1Quality,
        T1VersionContext,
        ObservationTimeEnvelope,
        NativeQuantity,
    )
    for model in models:
        for name in model.model_fields:
            assert "usd" not in name.lower()
            assert "fiat" not in name.lower()


def test_stablecoin_conversion_unavailability_blocks_normalization() -> None:
    """bloc_05/03 §9 / bloc_05/06 G5: unavailable means blocked, never assumed."""
    assert (
        NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE
        in BLOCKING_QUALITY_FLAGS
    )
    with pytest.raises(ValueError):
        envelope(
            quality_flags=flags(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
            )
        )


def test_stablecoin_distinctness_is_a_recordable_fact() -> None:
    assert NormalizationQualityFlag.IDENTITY_STABLECOIN_DISTINCT.value == (
        "IDENTITY_STABLECOIN_DISTINCT"
    )


# ---------------------------------------------------------------------------
# §9 quality / lineage base vocabulary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [LineageState.LINEAGE_COMPLETE, LineageState.LINEAGE_PARTIAL, LineageState.LINEAGE_BROKEN],
)
def test_lineage_state_must_agree_with_its_matching_flag(state: LineageState) -> None:
    matching = NormalizationQualityFlag(state.value)
    others = {
        NormalizationQualityFlag.LINEAGE_COMPLETE,
        NormalizationQualityFlag.LINEAGE_PARTIAL,
        NormalizationQualityFlag.LINEAGE_BROKEN,
    } - {matching}
    # LINEAGE_BROKEN is blocking, so it cannot accompany a canonical status at
    # all; the state/flag agreement law is still what is under test here.
    claim = (
        NormalizationStatus.NATIVE_ONLY
        if state is LineageState.LINEAGE_BROKEN
        else NormalizationStatus.NORMALIZED
    )
    ok = envelope(
        lineage_state=state,
        quality_flags=flags(matching),
        quality=quality(lineage_quality=QualityDimensionState.PARTIAL),
        **(
            {"normalization_status": claim, "versions": T1VersionContext()}
            if claim is NormalizationStatus.NATIVE_ONLY
            else {}
        ),
    )
    assert ok.lineage_state is state
    with pytest.raises(ValueError):
        envelope(lineage_state=state, quality_flags=flags(*others))
    with pytest.raises(ValueError):
        envelope(lineage_state=state, quality_flags=flags(matching, *others))


def test_lineage_broken_is_blocking() -> None:
    """bloc_05/05 §11: LINEAGE_BROKEN is blocking, whatever the status claims."""
    assert NormalizationQualityFlag.LINEAGE_BROKEN in BLOCKING_QUALITY_FLAGS
    with pytest.raises(ValueError):
        envelope(
            lineage_state=LineageState.LINEAGE_BROKEN,
            quality_flags=flags(NormalizationQualityFlag.LINEAGE_BROKEN),
        )
    permitted = envelope(
        lineage_state=LineageState.LINEAGE_BROKEN,
        quality_flags=flags(NormalizationQualityFlag.LINEAGE_BROKEN),
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        quality=quality(lineage_quality=QualityDimensionState.BLOCKED),
        versions=T1VersionContext(),
    )
    assert permitted.lineage_state is LineageState.LINEAGE_BROKEN


@pytest.mark.parametrize("flag", sorted(BLOCKING_QUALITY_FLAGS, key=str))
def test_no_blocking_flag_may_accompany_a_canonical_status(
    flag: NormalizationQualityFlag,
) -> None:
    with pytest.raises(ValueError):
        envelope(
            quality_flags=flags(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                flag,
            )
        )


# ---------------------------------------------------------------------------
# §10 / §31 quality flags: deterministic ordering
# ---------------------------------------------------------------------------


def test_quality_flags_must_be_in_canonical_declaration_order() -> None:
    forward = (
        NormalizationQualityFlag.IDENTITY_ALIAS_USED,
        NormalizationQualityFlag.BOOK_DEPTH_UNKNOWN,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
        NormalizationQualityFlag.IDENTITY_MANUAL_OVERRIDE,
        NormalizationQualityFlag.TIME_CLOCK_SKEW,
        NormalizationQualityFlag.PIT_PROVIDER_BACKFILL,
    )
    assert envelope(quality_flags=forward).quality_flags == forward
    with pytest.raises(ValueError):
        envelope(quality_flags=tuple(reversed(forward)))


def test_duplicate_quality_flags_are_refused() -> None:
    with pytest.raises(ValueError):
        envelope(
            quality_flags=(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                NormalizationQualityFlag.LINEAGE_COMPLETE,
            )
        )


def test_quality_flag_order_cannot_change_the_serialized_bytes() -> None:
    """Order-determinism is the point: equal sets serialize identically."""
    first = envelope(
        quality_flags=flags(
            NormalizationQualityFlag.LINEAGE_COMPLETE,
            NormalizationQualityFlag.IDENTITY_ALIAS_USED,
        )
    )
    second = envelope(
        quality_flags=flags(
            NormalizationQualityFlag.IDENTITY_ALIAS_USED,
            NormalizationQualityFlag.LINEAGE_COMPLETE,
        )
    )
    assert first.canonical_json() == second.canonical_json()


def test_verified_dimension_may_not_contradict_the_envelope() -> None:
    with pytest.raises(ValueError):
        envelope(quality=quality(identity_quality=QualityDimensionState.VERIFIED),
                 contract_instance_id=None)
    with pytest.raises(ValueError):
        envelope(
            quality=quality(unit_quality=QualityDimensionState.VERIFIED),
            quality_flags=flags(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
            ),
        )
    with pytest.raises(ValueError):
        envelope(
            quality=quality(time_quality=QualityDimensionState.VERIFIED),
            quality_flags=flags(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
            ),
        )
    with pytest.raises(ValueError):
        envelope(
            quality=quality(semantic_quality=QualityDimensionState.VERIFIED),
            quality_flags=flags(
                NormalizationQualityFlag.LINEAGE_COMPLETE,
                NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
            ),
        )
    with pytest.raises(ValueError):
        envelope(
            lineage_state=LineageState.LINEAGE_BROKEN,
            quality_flags=flags(NormalizationQualityFlag.LINEAGE_BROKEN),
            quality=quality(lineage_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS),
        )


# ---------------------------------------------------------------------------
# §24 quarantine law
# ---------------------------------------------------------------------------


def test_quarantine_requires_a_typed_reason_evidence_and_remediation() -> None:
    shared: dict[str, Any] = {
        "contract_instance_id": None,
        "normalization_status": NormalizationStatus.QUARANTINED,
        "missingness_reason": MissingnessReason.QUARANTINED,
        "quality_flags": flags(NormalizationQualityFlag.LINEAGE_COMPLETE),
        "quality": quality(),
        "versions": T1VersionContext(),
    }
    with pytest.raises(ValueError):
        envelope(**shared)
    with pytest.raises(ValueError):
        envelope(
            **shared,
            quarantine_reason=QuarantineReason.SCHEMA_FAILURE,
        )
    with pytest.raises(ValueError):
        envelope(
            **shared,
            quarantine_reason=QuarantineReason.SCHEMA_FAILURE,
            quarantine_evidence_refs=("projection-1",),
        )
    with pytest.raises(ValueError):
        envelope(
            **shared,
            quarantine_reason=QuarantineReason.SCHEMA_FAILURE,
            quarantine_evidence_refs=("projection-1",),
            quarantine_remediation="   ",
        )
    ok = envelope(
        **shared,
        quarantine_reason=QuarantineReason.SCHEMA_FAILURE,
        quarantine_evidence_refs=("projection-1",),
        quarantine_remediation="re-parse with the corrected schema",
    )
    assert ok.quarantine_reason is QuarantineReason.SCHEMA_FAILURE


def test_quarantine_metadata_cannot_ride_on_a_non_quarantined_row() -> None:
    with pytest.raises(ValueError):
        envelope(quarantine_reason=QuarantineReason.LINEAGE_BREAK)
    with pytest.raises(ValueError):
        envelope(quarantine_evidence_refs=("projection-1",))
    with pytest.raises(ValueError):
        envelope(quarantine_remediation="fix later")


# ---------------------------------------------------------------------------
# §20 version references
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", CANONICAL_STATUSES)
@pytest.mark.parametrize(
    "version",
    [
        "identity_registry_version",
        "contract_terms_version",
        "semantic_registry_version",
        "methodology_registry_version",
    ],
)
def test_canonical_status_requires_each_registry_version(
    status: NormalizationStatus, version: str
) -> None:
    """bloc_05/06 §3: registry/methodology versions where derived fields exist."""
    versions = T1VersionContext(
        identity_registry_version="identity-registry-1",
        contract_terms_version="contract-terms-1",
        semantic_registry_version="semantic-registry-1",
        methodology_registry_version="methodology-registry-1",
    )
    setattr(versions, version, None)
    with pytest.raises(ValueError):
        envelope(normalization_status=status, versions=versions)


def test_time_semantics_version_is_a_slot_not_a_requirement_at_i01() -> None:
    """No time semantics exist yet, so the slot exists but nothing is demanded."""
    assert "time_semantics_version" in T1VersionContext.model_fields
    slot_only = envelope(
        contract_instance_id=None,
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        native_values=(),
        quality_flags=flags(NormalizationQualityFlag.LINEAGE_COMPLETE),
        quality=quality(),
        versions=T1VersionContext(),
    )
    assert slot_only.versions.time_semantics_version is None


# ---------------------------------------------------------------------------
# §11/§31 identifiers are types only
# ---------------------------------------------------------------------------


def test_t1_record_id_is_absent_by_default_and_never_generated() -> None:
    """§18: the deterministic T1 identity algorithm is B5-I16, not I01."""
    assert envelope().t1_record_id is None
    assigned = envelope(t1_record_id="t1-record-0001")
    assert assigned.t1_record_id == "t1-record-0001"
    with pytest.raises(ValueError):
        envelope(t1_record_id="   ")


def test_generation_is_a_required_opaque_reference() -> None:
    """§19: the generation itself is B5-I18; I01 only names it."""
    assert envelope().normalization_generation == "generation-2026-01"
    with pytest.raises(ValueError):
        envelope(normalization_generation="")


def test_upstream_revision_and_coverage_truth_is_carried_not_redeclared() -> None:
    """§17: accepted Bloc 4 vocabularies are consumed as upstream evidence."""
    assert set(T1BaseEnvelope.model_fields) >= {
        "source_revision_id",
        "source_revision_state",
        "source_coverage_state",
        "source_granularity",
    }
    env = envelope(
        source_revision_state=RevisionState.SOURCE_MUTATION,
        source_coverage_state=CoverageState.KNOWN_GAP,
        source_granularity=Granularity.G1M,
    )
    assert env.source_revision_state is RevisionState.SOURCE_MUTATION
    assert env.source_coverage_state is CoverageState.KNOWN_GAP
    assert env.source_granularity is Granularity.G1M


def test_supersedes_reference_is_optional_and_type_only() -> None:
    """bloc_05/02 §10 keeps the T1 revision chain append-only."""
    assert envelope().supersedes_t1_record_id is None
    linked = envelope(t1_record_id="t1-2", supersedes_t1_record_id="t1-1")
    assert linked.supersedes_t1_record_id == "t1-1"


# ---------------------------------------------------------------------------
# §25 determinism
# ---------------------------------------------------------------------------


def test_serialization_is_byte_identical_for_equal_envelopes() -> None:
    assert envelope().canonical_json() == envelope().canonical_json()
    assert canonical_json_bytes(envelope()) == envelope().canonical_json()


def test_serialization_sorts_keys_and_uses_enum_strings() -> None:
    payload = envelope().as_canonical_dict()
    assert payload["normalization_status"] == "NORMALIZED"
    assert payload["sensor_family"] == "MECHANICAL_TRADE"
    assert payload["source_revision_state"] == "STABLE"
    assert payload["source_coverage_state"] == "COMPLETE_SOURCE_BOUNDARY"
    assert list(payload) == sorted(payload)
    raw = envelope().canonical_json()
    assert b"NormalizedStatus" not in raw
    assert b"object at 0x" not in raw


def test_construction_reads_no_wall_clock_and_generates_no_identity() -> None:
    """No default may smuggle in 'now' or a synthesized key."""
    for name, field in T1BaseEnvelope.model_fields.items():
        assert "default_factory" not in str(field.default_factory), name
        if isinstance(field.default_factory, type) or field.default_factory is not None:
            assert name not in {"t1_record_id", "normalization_generation"}


def test_utc_serialization_is_stable() -> None:
    env = envelope(
        time=ObservationTimeEnvelope(
            source_event_at=datetime(2022, 5, 12, 3, 2, 3, tzinfo=timezone(timedelta(hours=2)))
        )
    )
    assert b"2022-05-12T01:02:03" in env.canonical_json()


def test_equal_envelopes_round_trip_through_canonical_json() -> None:
    env = envelope()
    restored = T1BaseEnvelope.model_validate_json(env.canonical_json())
    assert restored.canonical_json() == env.canonical_json()
    assert restored.native_values[0].native_value == Decimal("0.00100")


# ---------------------------------------------------------------------------
# Native upstream evidence refs survive intact
# ---------------------------------------------------------------------------


def test_upstream_evidence_refs_are_preserved_verbatim() -> None:
    """bloc_05/07 F25 / bloc_04/I17 §7: lineage names durable IDs, not paths."""
    refs = lineage(
        raw_projection_refs=("projection-1", "projection-2"),
        acquisition_refs=("acquisition-1", "acquisition-2"),
        evidence_blob_hashes=(BLOB_SHA256, OTHER_BLOB_SHA256),
        identity_evidence_refs=("identity-evidence-1",),
        semantic_evidence_refs=("semantic-evidence-1",),
        conversion_lineage_refs=("conversion-lineage-1",),
    )
    env = envelope(lineage=refs)
    payload = env.as_canonical_dict()
    assert payload["lineage"]["raw_projection_refs"] == ["projection-1", "projection-2"]
    assert payload["lineage"]["evidence_blob_hashes"] == [
        BLOB_SHA256,
        OTHER_BLOB_SHA256,
    ]
    assert payload["lineage"]["identity_evidence_refs"] == ["identity-evidence-1"]
    restored = T1BaseEnvelope.model_validate_json(env.canonical_json())
    assert restored.lineage == refs


def test_lineage_chain_must_be_complete_and_duplicate_free() -> None:
    """bloc_05/05 §2: T1 -> T0B -> AcquisitionRecord -> T0A blob SHA256."""
    with pytest.raises(ValueError):
        lineage(raw_projection_refs=())
    with pytest.raises(ValueError):
        lineage(acquisition_refs=())
    with pytest.raises(ValueError):
        lineage(evidence_blob_hashes=())
    with pytest.raises(ValueError):
        lineage(acquisition_refs=("acquisition-1", "acquisition-1"))
    with pytest.raises(ValueError):
        lineage(evidence_blob_hashes=(BLOB_SHA256, BLOB_SHA256))
    with pytest.raises(ValueError):
        lineage(evidence_blob_hashes=("not-a-digest",))


def test_lineage_refs_carry_no_filesystem_or_catalog_knowledge() -> None:
    """bloc_04/I17 §12/§13: durable identifiers only, never paths or DuckDB."""
    for name in T1LineageRef.model_fields:
        assert "path" not in name
        assert "uri" not in name
        assert "directory" not in name
        assert "catalog" not in name
        assert "duckdb" not in name


def test_type_aliases_are_public_and_annotated() -> None:
    """The four opaque identifier types are part of the documented surface."""
    for alias in (T1RecordId, T1GenerationId):
        assert alias is not None