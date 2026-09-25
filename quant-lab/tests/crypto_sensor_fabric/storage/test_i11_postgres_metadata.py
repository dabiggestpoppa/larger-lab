"""SENSOR-B4-I11 PostgreSQL metadata boundary tests.

Offline tests never open a database.  The integration test is explicit and
only runs when SENSOR_POSTGRES_TEST_DSN names a real local PostgreSQL engine.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.storage.postgres_metadata import (
    MetadataSnapshot,
    PostgresImportError,
    PostgresMetadataError,
    PostgresMetadataConfig,
    PostgresMetadataRepository,
    RECONSTRUCTIBLE_TABLES,
    SCHEMA_NAME,
    TABLE_AUTHORITY,
    TABLE_NAMES,
    redact_dsn,
    validate_row,
)


def _provider(**overrides: object) -> dict[str, object]:
    row = {
        "provider_id": "KRAKEN_FUTURES",
        "status": "CANDIDATE",
        "evidence_class": "B1",
        "access_class": "FREE_REFERENCE_ONLY",
        "capability_count": 1,
        "fallback_count": 0,
        "notes": "safe metadata",
    }
    row.update(overrides)
    return row


def test_closed_authority_map_and_fixed_namespace() -> None:
    assert SCHEMA_NAME == "crypto_sensor_fabric_ops"
    assert len(TABLE_NAMES) == 12
    assert set(TABLE_AUTHORITY) == set(TABLE_NAMES)
    assert set(RECONSTRUCTIBLE_TABLES) <= set(TABLE_NAMES)
    assert TABLE_AUTHORITY["quota_state"] == "OPERATIONAL_ONLY"
    assert TABLE_AUTHORITY["storage_jobs"] == "RECONSTRUCTIBLE"


def test_dsn_redaction_never_exposes_password_or_token() -> None:
    rendered = redact_dsn("postgresql://operator:super-secret@localhost/db?password=also-secret&token=tok")
    assert "super-secret" not in rendered
    assert "also-secret" not in rendered
    assert "<redacted>" in rendered


def test_raw_bytes_and_generic_raw_keys_are_refused() -> None:
    with pytest.raises(PostgresImportError):
        validate_row("provider_registry", _provider(notes=b"raw source bytes"))
    bad = _provider()
    bad["payload"] = "{}"
    with pytest.raises(PostgresImportError):
        validate_row("provider_registry", bad)


def test_secret_shaped_metadata_is_not_a_usable_value() -> None:
    with pytest.raises(PostgresImportError):
        validate_row("provider_registry", _provider(notes="api_key=should-not-persist"))


def test_snapshot_rejects_unknown_table_and_requires_exact_columns() -> None:
    with pytest.raises(PostgresImportError):
        MetadataSnapshot({"raw_events": []})
    with pytest.raises(PostgresImportError):
        MetadataSnapshot({"provider_registry": [{"provider_id": "P"}]})


def test_real_postgres_integration_is_explicitly_opt_in() -> None:
    dsn = os.getenv("SENSOR_POSTGRES_TEST_DSN")
    if not dsn:
        pytest.skip("real PostgreSQL runtime unavailable; set SENSOR_POSTGRES_TEST_DSN")
    repo = PostgresMetadataRepository(PostgresMetadataConfig(dsn))
    repo.install_schema()
    try:
        assert repo.introspect_schema()["raw_table_absent"] is True
        assert repo.introspect_schema()["generic_raw_column_absent"] is True
        assert repo.introspect_schema()["bytea_absent"] is True
        empty = MetadataSnapshot({table: [] for table in RECONSTRUCTIBLE_TABLES})
        repo.refresh_reconstructible_metadata(snapshot=empty)
        assert repo.canonical_rows() == {table: [] for table in RECONSTRUCTIBLE_TABLES}
    finally:
        repo.drop_schema()


def test_real_postgres_failed_refresh_rolls_back_previous_snapshot() -> None:
    dsn = os.getenv("SENSOR_POSTGRES_TEST_DSN")
    if not dsn:
        pytest.skip("real PostgreSQL runtime unavailable; set SENSOR_POSTGRES_TEST_DSN")
    repo = PostgresMetadataRepository(PostgresMetadataConfig(dsn))
    repo.install_schema()
    try:
        empty = MetadataSnapshot({table: [] for table in RECONSTRUCTIBLE_TABLES})
        repo.refresh_reconstructible_metadata(snapshot=empty)
        before = repo.canonical_rows()
        failing = PostgresMetadataRepository(
            PostgresMetadataConfig(dsn),
            refresh_hook=lambda table, connection: (_ for _ in ()).throw(RuntimeError("injected refresh failure")) if table == "recovery_runs" else None,
        )
        with pytest.raises(PostgresMetadataError):
            failing.refresh_reconstructible_metadata(snapshot=empty)
        assert repo.canonical_rows() == before
    finally:
        repo.drop_schema()


# Keep a concrete UTC value in this module so static analyzers do not infer
# that timestamp normalization is accidentally optional.
_UTC_TEST_CLOCK = datetime.now(UTC)
