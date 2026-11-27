"""SENSOR-B5-I16 (preliminary) - deterministic T1 identity and lineage laws.

Each test maps to a frozen clause of bloc_05/05 sections 2, 3 and 4, plus the two
Wave 1 instructions: identity derivation independent of wall clock, incidental
order and machine-local state, and the LINEAGE gate NOT closed.

Offline, deterministic, provider-import free.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import LineageState
from crypto_sensor_fabric.normalization.lineage import (
    LINEAGE_GATE_CLOSED,
    LINEAGE_GATE_STATE,
    REQUIRED_SENSOR_FAMILIES,
    GenerationDescriptor,
    GenerationImmutableViolation,
    IncompleteLineageError,
    T1IdentityKey,
    assert_generation_immutable,
    assert_lineage_complete,
    canonical_identity_bytes,
    compute_t1_record_id,
    generation_fingerprint,
    lineage_completeness,
    missing_sensor_families,
)
from crypto_sensor_fabric.normalization.sensors import (
    PositioningMetricType,
    PositioningObservationInput,
    normalize_positioning,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "e" * 64
_AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


def _key(**overrides: object) -> T1IdentityKey:
    base: dict[str, object] = dict(
        sensor_family=SensorFamily.MECHANICAL_POSITIONING,
        provider="BINANCE_USDM",
        venue="BINANCE",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_identity_id="POS-1",
        native_sequence_id="7",
        source_revision_id="rev-1",
        normalization_generation="gen-1",
    )
    base.update(overrides)
    return T1IdentityKey(**base)  # type: ignore[arg-type]


def _record(**overrides: object):
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_positioning_id="POS-1",
        metric_type=PositioningMetricType.ACCOUNT_LONG_SHORT_RATIO,
        numerator_definition="LONG_ACCOUNTS",
        denominator_definition="SHORT_ACCOUNTS",
        population_scope="ALL_ACCOUNTS",
        value_native=Decimal("1.1"),
        value_unit="RATIO",
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
        event_at=_AT,
    )
    base.update(overrides)
    return normalize_positioning(PositioningObservationInput(**base))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 05 4 -- deterministic record identity
# ---------------------------------------------------------------------------


def test_identity_is_reproducible() -> None:
    assert compute_t1_record_id(_key()) == compute_t1_record_id(_key())


def test_identity_is_a_prefixed_sha256() -> None:
    record_id = compute_t1_record_id(_key())
    assert record_id.startswith("t1:")
    assert len(record_id) == len("t1:") + 64


def test_a_revision_yields_a_different_identity() -> None:
    assert compute_t1_record_id(_key()) != compute_t1_record_id(
        _key(source_revision_id="rev-2")
    )


def test_a_new_generation_yields_a_different_identity() -> None:
    assert compute_t1_record_id(_key()) != compute_t1_record_id(
        _key(normalization_generation="gen-2")
    )


def test_the_identity_key_carries_no_normalized_number() -> None:
    """05 section 4: never derive the id from the normalized value."""
    payload = _key().model_dump()
    for forbidden in ("value_native", "basis_value_native", "oi_native_value", "price"):
        assert forbidden not in payload


def test_the_identity_bytes_are_canonical() -> None:
    assert canonical_identity_bytes(_key()) == canonical_identity_bytes(_key())
    assert b" " not in canonical_identity_bytes(_key())


def test_the_identity_key_is_immutable() -> None:
    key = _key()
    with pytest.raises(ValidationError):
        key.provider = "OTHER"  # type: ignore[misc]


def test_a_caller_cannot_choose_the_identity_schema() -> None:
    with pytest.raises(ValueError, match="identity_schema_version"):
        _key(identity_schema_version="b5-i16-caller-choice")


# ---------------------------------------------------------------------------
# 05 13 -- generation immutability
# ---------------------------------------------------------------------------


def _generation(**overrides: object) -> GenerationDescriptor:
    base: dict[str, object] = dict(
        generation_id="gen-1",
        code_commit="62200f3cb18ee5cea1483d986e64502f388eeb77",
        identity_registry_version="id-v1",
        semantic_registry_version="sem-v1",
        methodology_registry_version="meth-v1",
        time_semantics_version="time-v1",
        source_revision_mode="ERROR_ON_AMBIGUITY",
        input_manifest_refs=("manifest-1",),
        created_at="2026-11-27T00:00:00Z",
    )
    base.update(overrides)
    return GenerationDescriptor(**base)  # type: ignore[arg-type]


def test_build_time_is_not_part_of_a_generation_fingerprint() -> None:
    assert generation_fingerprint(_generation()) == generation_fingerprint(
        _generation(created_at="2027-01-01T00:00:00Z")
    )


def test_a_changed_methodology_changes_the_fingerprint() -> None:
    assert generation_fingerprint(_generation()) != generation_fingerprint(
        _generation(methodology_registry_version="meth-v2")
    )


def test_an_unchanged_generation_passes_the_immutability_assertion() -> None:
    assert_generation_immutable(_generation(), _generation(created_at=None))


def test_a_drifted_generation_is_refused() -> None:
    with pytest.raises(GenerationImmutableViolation, match="no longer byte-equivalent"):
        assert_generation_immutable(_generation(), _generation(code_commit="deadbeef"))


def test_a_renamed_generation_is_refused() -> None:
    with pytest.raises(GenerationImmutableViolation, match="generation id changed"):
        assert_generation_immutable(_generation(), _generation(generation_id="gen-2"))


# ---------------------------------------------------------------------------
# 05 2 -- completeness assertions
# ---------------------------------------------------------------------------


def test_a_complete_record_passes() -> None:
    record = _record()
    assert_lineage_complete(record)
    assert lineage_completeness(record) is LineageState.LINEAGE_COMPLETE


def test_a_record_without_a_generation_is_refused() -> None:
    record = _record()
    broken = record.model_copy(update={"normalization_generation": ""})
    with pytest.raises(IncompleteLineageError, match="no normalization generation"):
        assert_lineage_complete(broken)
    assert lineage_completeness(broken) is LineageState.LINEAGE_BROKEN


def test_a_record_without_an_acquisition_reference_is_refused() -> None:
    record = _record()
    lineage = record.lineage.model_copy(update={"acquisition_refs": ()})
    broken = record.model_copy(update={"lineage": lineage})
    with pytest.raises(IncompleteLineageError, match="no acquisition reference"):
        assert_lineage_complete(broken)


# ---------------------------------------------------------------------------
# The gate stays open
# ---------------------------------------------------------------------------


def test_the_lineage_gate_is_not_closed() -> None:
    assert LINEAGE_GATE_CLOSED is False
    assert LINEAGE_GATE_STATE == "NOT_CLOSED"


def test_the_required_family_set_is_the_frozen_eight() -> None:
    assert len(REQUIRED_SENSOR_FAMILIES) == 8
    assert "MECHANICAL_TRADE" in REQUIRED_SENSOR_FAMILIES
    assert "MECHANICAL_BASIS" in REQUIRED_SENSOR_FAMILIES


def test_wave1_leaves_the_required_set_uncovered() -> None:
    """I17-I19 own the rest of the chain, so coverage cannot close here."""
    missing = missing_sensor_families([SensorFamily.MECHANICAL_POSITIONING])
    assert missing
    assert "MECHANICAL_POSITIONING" not in missing
