"""SENSOR-B5-I12 - open-interest normalizer semantics (frozen clauses + adversarial).

Each test maps to a frozen clause of bloc_05/04 section 4 (plus bloc_05/02
section 4 for time) and asserts against observable record fields only, never a
private helper.  The suite is offline, deterministic and provider-import free.

Fixtures are synthetic and labelled; no test certifies a venue.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import (
    MissingnessReason,
    NormalizationQualityFlag,
)
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.sensors import (
    OpenInterestAggregationScope,
    OpenInterestNativeUnit,
    OpenInterestObservationInput,
    OpenInterestSnapshotScope,
    SensorAdmissionRefusal,
    T1OpenInterestRecord,
    normalize_open_interest,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "a" * 64
_FAMILY = SensorFamily.MECHANICAL_OPEN_INTEREST


def _payload(wave1, **overrides: object) -> OpenInterestObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_snapshot_id="OI-1",
        oi_native_value=Decimal("125000"),
        native_unit_token="CONTRACTS",
        native_unit_field="openInterest",
        unit_reading=OpenInterestNativeUnit.CONTRACTS,
        snapshot_scope=OpenInterestSnapshotScope.POINT_SNAPSHOT,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
        event_at=wave1.AT,
    )
    base.update(overrides)
    return OpenInterestObservationInput(**base)  # type: ignore[arg-type]


def _flags(record: T1OpenInterestRecord) -> set[str]:
    return {flag.value for flag in record.quality_flags}


def _admitted(wave1):
    """A synthetic approval root that certifies the unit field for THIS fixture.

    The unit claim is a semantic claim like any other, so every conversion test
    needs an admitted row: without one the derived fields stay blocked, which is
    exactly the fail-closed behaviour other tests assert.
    """
    registry = wave1.registry(
        (wave1.row("openInterest", "oi_native_unit", family=_FAMILY),)
    )
    return wave1.authority(registry)


# ---------------------------------------------------------------------------
# 04 4.2 -- unit honesty
# ---------------------------------------------------------------------------


def test_contract_oi_with_terms_derives_base(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1),
        registry=_admitted(wave1),
        terms=wave1.terms(multiplier="0.001"),
    )
    assert record.oi_contracts is None
    assert record.oi_base is not None
    assert record.oi_base.blocked is False
    assert record.oi_base.value == Decimal("125.000")
    assert record.oi_base.output_unit == "BTC"
    assert record.oi_base.conversion_lineage_refs


def test_contract_oi_without_terms_blocks_base(wave1) -> None:
    record = normalize_open_interest(_payload(wave1), registry=_admitted(wave1))
    assert record.oi_base is not None
    assert record.oi_base.blocked is True
    assert record.oi_base.value is None
    assert record.oi_base.missingness_reason is MissingnessReason.CONVERSION_BLOCKED
    # The native value survives untouched.
    assert record.oi_native_value == Decimal("125000")
    assert record.native_values[0].native_value == Decimal("125000")


def test_quote_needs_a_reference_price(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1),
        registry=_admitted(wave1),
        terms=wave1.terms(multiplier="0.001"),
    )
    assert record.oi_quote is not None and record.oi_quote.blocked is True
    assert NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE.value in _flags(record)


def test_quote_derived_with_pit_price(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1),
        registry=_admitted(wave1),
        terms=wave1.terms(multiplier="0.001"),
        reference_price=wave1.price(value="60000"),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.oi_quote is not None and record.oi_quote.blocked is False
    assert record.oi_quote.value == Decimal("7500000.000")
    assert record.oi_quote.output_unit == "USDT"
    assert record.reference_price_ref is not None


def test_inverse_contract_quote_face_then_base(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1),
        registry=_admitted(wave1),
        terms=wave1.terms(payoff=wave1.PayoffType.INVERSE, multiplier="1", inverse=True),
        reference_price=wave1.price(value="60000"),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.oi_quote is not None and record.oi_quote.blocked is False
    assert record.oi_quote.value == Decimal("125000")
    assert record.oi_base is not None and record.oi_base.blocked is False


def test_base_native_is_carried_not_copied(wave1) -> None:
    """A native unit that is already base must not appear as a derived value."""
    record = normalize_open_interest(
        _payload(
            wave1,
            native_unit_token="BTC",
            unit_reading=OpenInterestNativeUnit.BASE_ASSET,
            oi_native_value=Decimal("1250"),
        ),
        registry=_admitted(wave1),
        terms=wave1.terms(multiplier="0.001"),
    )
    assert record.oi_base is None
    assert record.oi_quote is None
    assert record.oi_native_value == Decimal("1250")


def test_provider_specific_unit_never_converts(wave1) -> None:
    record = normalize_open_interest(
        _payload(
            wave1,
            native_unit_token="LOTS",
            unit_reading=OpenInterestNativeUnit.PROVIDER_SPECIFIC,
            oi_native_value=Decimal("9999"),
        ),
        terms=wave1.terms(),
    )
    assert record.oi_native_value == Decimal("9999")
    assert record.oi_base is not None and record.oi_base.blocked is True
    assert record.unit_admission is not None
    assert record.unit_admission.admitted is False


# ---------------------------------------------------------------------------
# The I08 dependency: no dollar is ever emitted
# ---------------------------------------------------------------------------


def test_usd_is_always_blocked_and_cites_i08(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1), terms=wave1.terms(), reference_price=wave1.price(),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.oi_usd is not None
    assert record.oi_usd.blocked is True
    assert record.oi_usd.value is None
    assert record.oi_usd.unresolved_citation == "B5_I08_UNITS_V1"


def test_a_record_cannot_carry_an_unblocked_usd_value(wave1) -> None:
    from crypto_sensor_fabric.normalization.sensors import DerivedAmount

    good = normalize_open_interest(_payload(wave1))
    with pytest.raises(ValueError, match="B5_I08_UNITS_V1 is unresolved"):
        T1OpenInterestRecord(
            **{
                **good.model_dump(),
                "oi_usd": DerivedAmount(
                    value=Decimal("1"),
                    blocked=False,
                    methodology_id="OI_USD_NATIVE_PASSTHROUGH_V1",
                    methodology_version="1",
                    output_unit="USD",
                    conversion_lineage_refs=("x",),
                ),
            }
        )


def test_usd_native_reading_is_preserved_with_the_passthrough_pending(wave1) -> None:
    record = normalize_open_interest(
        _payload(
            wave1,
            native_unit_token="USD",
            unit_reading=OpenInterestNativeUnit.USD,
            oi_native_value=Decimal("82000000"),
        )
    )
    assert record.oi_native_value == Decimal("82000000")
    assert record.oi_usd.blocked is True
    # Not admitted by any authority, so the passthrough is not even pending.
    assert record.usd_native_passthrough_pending is False


# ---------------------------------------------------------------------------
# 02 4 / readiness 7 -- zeros, intervals, aggregates
# ---------------------------------------------------------------------------


def test_measured_zero_is_not_missing(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1, oi_native_value=Decimal("0")), terms=wave1.terms()
    )
    assert record.measured_zero is True
    assert record.oi_native_value == Decimal("0")
    assert record.missingness_reason is None


def test_zero_without_verified_coverage_converts_to_nothing(wave1) -> None:
    record = normalize_open_interest(
        _payload(
            wave1,
            oi_native_value=Decimal("0"),
            source_coverage_state=CoverageState.PARTIAL,
        ),
        terms=wave1.terms(),
    )
    assert record.measured_zero is True
    assert record.zero_coverage_verified is False
    assert record.oi_base is not None
    assert record.oi_base.blocked is True
    assert record.oi_base.missingness_reason is MissingnessReason.SOURCE_GAP


def test_interval_scope_requires_a_window_end(wave1) -> None:
    with pytest.raises(ValueError, match="requires interval_end_at"):
        _payload(wave1, snapshot_scope=OpenInterestSnapshotScope.INTERVAL_LAST)


def test_multi_venue_aggregate_refuses_venue_attribution(wave1) -> None:
    record = normalize_open_interest(
        _payload(
            wave1,
            snapshot_scope=OpenInterestSnapshotScope.PROVIDER_AGGREGATE,
            aggregation_scope=OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE,
            aggregate_venue_count=4,
        )
    )
    assert record.venue_assignment_refused is True
    assert record.aggregation_scope is OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE


def test_aggregate_cannot_be_scoped_as_a_point_snapshot(wave1) -> None:
    with pytest.raises(ValueError, match="must be scoped PROVIDER_AGGREGATE"):
        normalize_open_interest(
            _payload(
                wave1,
                snapshot_scope=OpenInterestSnapshotScope.POINT_SNAPSHOT,
                aggregation_scope=OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE,
                aggregate_venue_count=2,
            )
        )


def test_single_venue_observation_cannot_refuse_its_venue(wave1) -> None:
    record = normalize_open_interest(_payload(wave1))
    assert record.venue_assignment_refused is False


# ---------------------------------------------------------------------------
# 03 11-13 -- semantic admission, not caller assertion
# ---------------------------------------------------------------------------


def test_a_caller_minted_registry_confers_no_admission(wave1) -> None:
    registry = wave1.registry(
        (wave1.row("openInterest", "oi_native_unit", family=_FAMILY),)
    )
    record = normalize_open_interest(
        _payload(wave1), registry=registry, terms=wave1.terms()
    )
    assert record.unit_admission is not None
    assert record.unit_admission.admitted is False
    assert record.unit_admission.refusal is SensorAdmissionRefusal.UNTRUSTED_AUTHORITY
    assert record.oi_base is not None and record.oi_base.blocked is True
    assert record.oi_native_value == Decimal("125000")


def test_an_untyped_unit_field_cannot_be_admitted(wave1) -> None:
    record = normalize_open_interest(
        _payload(wave1, native_unit_field=None), terms=wave1.terms()
    )
    assert record.unit_admission is not None
    assert record.unit_admission.refusal is SensorAdmissionRefusal.NO_NATIVE_FIELD


def test_a_row_about_another_field_does_not_admit_the_unit(wave1) -> None:
    registry = wave1.registry(
        (wave1.row("openInterest", "oi_base", family=_FAMILY),)
    )
    record = normalize_open_interest(
        _payload(wave1),
        registry=wave1.authority(registry),
        terms=wave1.terms(),
    )
    assert record.unit_admission is not None
    assert record.unit_admission.refusal is SensorAdmissionRefusal.FIELD_MISMATCH


def test_an_approved_row_admits_the_unit_and_then_converts(wave1) -> None:
    registry = wave1.registry(
        (wave1.row("openInterest", "oi_native_unit", family=_FAMILY),)
    )
    record = normalize_open_interest(
        _payload(wave1),
        registry=wave1.authority(registry),
        terms=wave1.terms(multiplier="0.001"),
    )
    assert record.unit_admission is not None and record.unit_admission.admitted is True
    assert record.unit_admission.admission_approval_id is not None
    assert record.oi_base is not None and record.oi_base.blocked is False


def test_a_pending_row_leaves_derived_fields_blocked(wave1) -> None:
    registry = wave1.registry(
        (
            wave1.row(
                "openInterest",
                "oi_native_unit",
                family=_FAMILY,
                evidence="BLOC2_PROBE_PENDING",
                confidence=wave1.SemanticConfidence.AMBIGUOUS,
            ),
        )
    )
    record = normalize_open_interest(
        _payload(wave1), registry=registry, terms=wave1.terms()
    )
    assert record.unit_admission is not None
    assert record.unit_admission.refusal is SensorAdmissionRefusal.PENDING_EVIDENCE
    assert record.oi_base.blocked is True
    assert NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED.value in _flags(record)


def test_corroboration_only_rows_never_admit(wave1) -> None:
    registry = wave1.registry(
        (
            wave1.row(
                "openInterest",
                "oi_native_unit",
                family=_FAMILY,
                equivalence=wave1.SemanticEquivalence.CORROBORATION_ONLY,
            ),
        )
    )
    record = normalize_open_interest(
        _payload(wave1), registry=registry, terms=wave1.terms()
    )
    assert record.unit_admission is not None
    assert (
        record.unit_admission.refusal
        is SensorAdmissionRefusal.CORROBORATION_ONLY_MAPPING
    )


def test_a_contradicting_contract_instance_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="contradicts the PIT terms"):
        normalize_open_interest(
            _payload(wave1, contract_instance_id="CANON:OTHER"),
            terms=wave1.terms(),
        )


# ---------------------------------------------------------------------------
# Determinism and the family law
# ---------------------------------------------------------------------------


def test_normalization_is_byte_deterministic(wave1) -> None:
    kwargs = dict(terms=wave1.terms(), reference_price=wave1.price())
    first = normalize_open_interest(_payload(wave1), **kwargs)
    second = normalize_open_interest(_payload(wave1), **kwargs)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)


def test_the_record_cannot_claim_another_sensor_family(wave1) -> None:
    good = normalize_open_interest(_payload(wave1))
    with pytest.raises(ValueError, match="MECHANICAL_OPEN_INTEREST"):
        T1OpenInterestRecord(
            **{
                **good.model_dump(),
                "sensor_family": SensorFamily.MECHANICAL_FUNDING,
            }
        )
