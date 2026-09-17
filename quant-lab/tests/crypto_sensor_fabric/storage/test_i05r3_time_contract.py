"""SENSOR-B4-I05R3C — projection-context time-truth contract tests.

Covers (I05R3 §14-§19 + §21.9-§21.16):

- naive ``logical_date_start``/``logical_date_end``/``min_provider_time``/
  ``max_provider_time``/``created_at`` inputs are rejected — never silently
  reinterpreted as UTC;
- offset-aware non-UTC timestamps are accepted and serialize normalized to
  UTC;
- a persisted NAIVE timestamp fragment fails closed on reload
  (``from_dict`` = catalog corruption);
- provider-time ordering is enforced only when both bounds exist; missing
  bounds are never manufactured;
- ``created_at`` stays operational metadata (never part of content identity
  doctrine) while still being timezone-aware.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactCatalogCorrupt,
    ProjectionCatalogRecord,
    ProjectionPreconditionError,
)

UTC_M5 = timezone(timedelta(hours=-5))


def _record(**overrides: object) -> ProjectionCatalogRecord:
    base: dict[str, object] = {
        "projection_id": "proj-time",
        "provider": "kraken",
        "venue": "futures",
        "sensor_family": "MECHANICAL_TRADE",
        "native_instrument": "BTC-USDT",
        "source_granularity": "1m",
        "partition_key": "kraken/futures/BTC-USDT/2026-01-15",
        "logical_date_start": datetime(2026, 1, 15, tzinfo=UTC),
        "logical_date_end": datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
        "projection_schema_id": "schema.x",
        "projection_schema_version": "1.0.0",
        "schema_key": "k" * 64,
        "schema_fingerprint": "f" * 64,
        "parser_version": "1.0.0",
        "projection_uri": "projections/part-0.parquet",
        "projection_sha256": "a" * 64,
        "row_count": 1,
        "min_provider_time": None,
        "max_provider_time": None,
        "lineage_manifest_id": "lm-time",
        "quality_flags": [],
        "created_at": datetime(2026, 1, 16, tzinfo=UTC),
    }
    base.update(overrides)
    return ProjectionCatalogRecord(**base)  # type: ignore[arg-type]


class TestNaiveTimestampsRejected:
    def test_naive_logical_date_start_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="logical_date_start"):
            _record(logical_date_start=datetime(2026, 1, 15))

    def test_naive_logical_date_end_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="logical_date_end"):
            _record(logical_date_end=datetime(2026, 1, 15, 23, 59, 59))

    def test_naive_min_provider_time_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="min_provider_time"):
            _record(
                min_provider_time=datetime(2026, 1, 15),
                max_provider_time=datetime(2026, 1, 15, 23, tzinfo=UTC),
            )

    def test_naive_max_provider_time_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="max_provider_time"):
            _record(
                min_provider_time=datetime(2026, 1, 15, tzinfo=UTC),
                max_provider_time=datetime(2026, 1, 15, 23),
            )

    def test_naive_created_at_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="created_at"):
            _record(created_at=datetime(2026, 1, 16))


class TestAwareTimestampsAccepted:
    def test_offset_aware_non_utc_normalized_to_utc(self) -> None:
        """§16: 2026-01-01T12:00:00-05:00 serializes as 17:00+00:00."""
        record = _record(
            logical_date_start=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC_M5),
        )
        payload = record.to_dict()
        assert payload["logical_date_start"] == "2026-01-01T17:00:00+00:00"

    def test_min_provider_time_offset_aware_normalized(self) -> None:
        record = _record(
            min_provider_time=datetime(2026, 1, 15, 7, tzinfo=UTC_M5),
            max_provider_time=datetime(2026, 1, 15, 12, 1, tzinfo=UTC_M5),
        )
        payload = record.to_dict()
        assert payload["min_provider_time"] == "2026-01-15T12:00:00+00:00"
        assert payload["max_provider_time"] == "2026-01-15T17:01:00+00:00"

    def test_missing_provider_times_stay_none(self) -> None:
        """§17: absent bounds are never manufactured."""
        payload = _record().to_dict()
        assert payload["min_provider_time"] is None
        assert payload["max_provider_time"] is None


class TestProviderTimeOrdering:
    def test_inverted_provider_range_rejected(self) -> None:
        with pytest.raises(ProjectionPreconditionError, match="max_provider_time"):
            _record(
                min_provider_time=datetime(2026, 1, 15, 12, tzinfo=UTC),
                max_provider_time=datetime(2026, 1, 15, 11, tzinfo=UTC),
            )

    def test_mixed_awareness_comparison_safe(self) -> None:
        """An inverted range across offsets is still caught after awareness."""
        with pytest.raises(ProjectionPreconditionError, match="max_provider_time"):
            _record(
                min_provider_time=datetime(2026, 1, 15, 12, tzinfo=UTC),
                max_provider_time=datetime(
                    2026, 1, 15, 6, tzinfo=UTC_M5
                ),  # == 11:00 UTC
            )

    def test_equal_bounds_accepted(self) -> None:
        record = _record(
            min_provider_time=datetime(2026, 1, 15, tzinfo=UTC),
            max_provider_time=datetime(2026, 1, 15, tzinfo=UTC),
        )
        assert record.min_provider_time is not None


class TestReloadValidation:
    def test_round_trip_preserves_instant(self) -> None:
        record = _record(
            logical_date_start=datetime(2026, 1, 1, 12, tzinfo=UTC_M5),
        )
        restored = ProjectionCatalogRecord.from_dict(record.to_dict())
        assert restored == record

    def test_persisted_naive_logical_start_fails_reload(self) -> None:
        payload = _record().to_dict()
        payload["logical_date_start"] = "2026-01-15T00:00:00"
        with pytest.raises(ProjectionArtifactCatalogCorrupt, match="naive"):
            ProjectionCatalogRecord.from_dict(payload)

    def test_persisted_naive_created_at_fails_reload(self) -> None:
        payload = _record().to_dict()
        payload["created_at"] = "2026-01-16T00:00:00"
        with pytest.raises(ProjectionArtifactCatalogCorrupt, match="naive"):
            ProjectionCatalogRecord.from_dict(payload)

    def test_persisted_naive_min_provider_time_fails_reload(self) -> None:
        payload = _record().to_dict()
        payload["min_provider_time"] = "2026-01-15T00:00:00"
        with pytest.raises(ProjectionArtifactCatalogCorrupt, match="naive"):
            ProjectionCatalogRecord.from_dict(payload)

    def test_offset_aware_reload_accepted(self) -> None:
        payload = _record().to_dict()
        payload["logical_date_start"] = "2026-01-01T12:00:00-05:00"
        restored = ProjectionCatalogRecord.from_dict(payload)
        assert restored.logical_date_start == datetime(2026, 1, 1, 17, tzinfo=UTC)
