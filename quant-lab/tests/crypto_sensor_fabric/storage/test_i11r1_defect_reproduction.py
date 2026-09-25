"""Focused I11R1 defect reproduction.

These tests intentionally describe the operator-reported contract and are
expected to fail against the I11 implementation until the R1 repair lands.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from crypto_sensor_fabric.storage import postgres_metadata as pg

psycopg = pytest.importorskip("psycopg")


class _Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []


class _Connection:
    def __init__(self):
        self.statements: list[str] = []
        self.last_parameters = None
        self.insert_parameters = None

    def execute(self, statement, parameters=None):
        self.statements.append(statement)
        self.last_parameters = parameters
        if statement.lstrip().upper().startswith("INSERT"):
            self.insert_parameters = parameters
        row = self.insert_parameters if statement.lstrip().upper().startswith("SELECT") and "integrity_checks" in statement else None
        return _Result(row)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _repo():
    connection = _Connection()
    return pg.PostgresMetadataRepository(
        pg.PostgresMetadataConfig("postgresql://fixture.invalid/db"),
        connection_factory=lambda: connection,
    ), connection


def _acquisition_values(*, include_tokens: bool = False) -> dict[str, object]:
    values = {column: None for column in pg._TABLE_COLUMNS["acquisitions"]}
    values.update(
        acquisition_id="acq-1",
        provider_id="PROVIDER",
        venue="VENUE",
        sensor_family="MECHANICAL_TRADE",
        request_fingerprint="request-1",
        adapter_version="1.0.0",
        requested_start=datetime(2026, 1, 1, tzinfo=UTC),
        requested_end=datetime(2026, 1, 2, tzinfo=UTC),
        request_started_at=datetime(2026, 1, 1, tzinfo=UTC),
        response_observed_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
        ingested_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
        native_instrument="NATIVE",
        source_locator="locator",
        quality_flags=[],
        provider_checksum_verified=True,
    )
    if include_tokens:
        values["resume_token_before"] = "PRIVATE_RESUME_TOKEN"
        values["resume_token_after"] = "PRIVATE_RESUME_TOKEN"
    return values


def test_defect_a_valid_acquisition_metadata_is_not_self_refused() -> None:
    row = pg.validate_row("acquisitions", _acquisition_values())
    assert row["acquisition_id"] == "acq-1"


def test_defect_a_resume_tokens_are_not_projected() -> None:
    model = SimpleNamespace(model_dump=lambda mode: _acquisition_values(include_tokens=True))
    row = pg._acquisition_row(model)
    assert "resume_token_before" not in row
    assert "resume_token_after" not in row


def test_defect_b_canonical_order_is_not_character_joined() -> None:
    repo, connection = _repo()
    repo.canonical_rows()
    provider_query = next(s for s in connection.statements if "provider_registry" in s)
    assert 'ORDER BY "provider_id"' in provider_query


def test_defect_c_integrity_write_uses_check_id_conflict_policy() -> None:
    repo, connection = _repo()
    row = {column: None for column in pg._TABLE_COLUMNS["integrity_checks"]}
    row.update(check_id="check-1", object_type="BLOB", object_id="blob-1")
    repo.upsert_operational_state("integrity_checks", row)
    statement = next(s for s in connection.statements if "INSERT INTO" in s and "integrity_checks" in s)
    assert "ON CONFLICT (check_id)" in statement


def test_defect_d_acquisition_ddl_is_explicitly_typed_and_token_free() -> None:
    repo, _ = _repo()
    ddl = repo._create_table_sql("acquisitions")
    assert "BOOLEAN" in ddl
    assert "TIMESTAMPTZ" in ddl
    assert "resume_token" not in ddl


def test_defect_e_install_exposes_exact_schema_validator() -> None:
    assert hasattr(pg.PostgresMetadataRepository, "validate_installed_schema")


def test_defect_f_column_and_value_firewalls_are_separate() -> None:
    row = {column: None for column in pg._TABLE_COLUMNS["provider_registry"]}
    row.update(provider_id="P", status="CANDIDATE", evidence_class="B1", capability_count=0, fallback_count=0, notes="secretary notes")
    assert pg.validate_row("provider_registry", row)["notes"] == "secretary notes"
