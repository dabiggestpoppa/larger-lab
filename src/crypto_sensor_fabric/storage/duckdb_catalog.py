"""SENSOR-B4-I10A — DuckDB discovery bootstrap, typed errors, and views."""

from __future__ import annotations

import duckdb

VIEW_NAMES = (
    "v_t0_blobs", "v_t0_acquisitions", "v_t0_projections", "v_t0_partitions",
    "v_t0_gaps", "v_t0_revisions", "v_t0_quarantine", "v_t0_storage_usage",
)
CATALOG_SCHEMA_VERSION = "1.0"


class DuckDBCatalogError(RuntimeError):
    """Base typed rebuild/discovery failure."""


class DuckDBCatalogCorrupt(DuckDBCatalogError):
    """Durable evidence is corrupt, dangling, or internally inconsistent."""


class DuckDBCatalogPublishError(DuckDBCatalogError):
    """A validated rebuild could not be durably published."""


_VIEW_COLUMNS = {
    "v_t0_blobs": "blob_sha256 VARCHAR, byte_length BIGINT, stored_byte_length BIGINT, storage_object_key VARCHAR, backend_id VARCHAR, resolved_local_path VARCHAR, source_media_type VARCHAR, storage_encoding VARCHAR, integrity_state VARCHAR, created_at VARCHAR",
    "v_t0_acquisitions": "acquisition_id VARCHAR, provider_id VARCHAR, venue VARCHAR, sensor_family VARCHAR, request_fingerprint VARCHAR, native_instrument VARCHAR, requested_start VARCHAR, requested_end VARCHAR, actual_start VARCHAR, actual_end VARCHAR, response_observed_at VARCHAR, ingested_at VARCHAR, blob_sha256 VARCHAR, failure_ref VARCHAR, schema_state VARCHAR",
    "v_t0_projections": "projection_id VARCHAR, provider VARCHAR, venue VARCHAR, sensor_family VARCHAR, native_instrument VARCHAR, partition_key VARCHAR, projection_schema_id VARCHAR, projection_schema_version VARCHAR, parser_version VARCHAR, projection_object_key VARCHAR, backend_id VARCHAR, resolved_local_path VARCHAR, projection_sha256 VARCHAR, row_count BIGINT, stored_bytes BIGINT, state VARCHAR, lineage_manifest_id VARCHAR, source_count BIGINT",
    "v_t0_partitions": "partition_manifest_id VARCHAR, partition_key VARCHAR, manifest_version BIGINT, is_current BOOLEAN, provider VARCHAR, venue VARCHAR, sensor_family VARCHAR, native_instrument VARCHAR, blob_refs VARCHAR[], projection_refs VARCHAR[], coverage_state VARCHAR, integrity_state VARCHAR, gap_count BIGINT, revision_count BIGINT, supersedes_manifest_id VARCHAR",
    "v_t0_gaps": "gap_id VARCHAR, scope VARCHAR, scope_id VARCHAR, missingness VARCHAR, detail VARCHAR",
    "v_t0_revisions": "source_revision_key VARCHAR, revision_number BIGINT, segment_id VARCHAR, blob_sha256 VARCHAR, first_acquisition_id VARCHAR, first_seen_at VARCHAR, revision_state VARCHAR, revision_reason VARCHAR",
    "v_t0_quarantine": "recovery_action_id VARCHAR, recovery_run_id VARCHAR, object_type VARCHAR, object_id VARCHAR, problem VARCHAR, resolution VARCHAR, action_kind VARCHAR",
    "v_t0_storage_usage": "evidence_class VARCHAR, integrity_state VARCHAR, provider VARCHAR, sensor_family VARCHAR, storage_priority VARCHAR, universe_tier VARCHAR, stored_bytes BIGINT, raw_bytes BIGINT, projection_bytes BIGINT, object_count BIGINT",
}


def _create_table(con: duckdb.DuckDBPyConnection, name: str, rows: list[dict[str, object]]) -> None:
    table = f"t0_{name.removeprefix('v_t0_')}"
    if not rows:
        con.execute(f"CREATE TABLE {table} ({_VIEW_COLUMNS[name]})")
    else:
        declarations = []
        for column, value in rows[0].items():
            kind = "BOOLEAN" if isinstance(value, bool) else "BIGINT" if isinstance(value, int) else "VARCHAR[]" if isinstance(value, list) else "VARCHAR"
            declarations.append(f"{column} {kind}")
        con.execute(f"CREATE TABLE {table} ({', '.join(declarations)})")
        keys = list(rows[0])
        con.executemany(
            f"INSERT INTO {table} VALUES ({', '.join('?' for _ in keys)})",
            [[row.get(key) for key in keys] for row in rows],
        )
    con.execute(f"CREATE VIEW {name} AS SELECT * FROM {table}")


__all__ = ["CATALOG_SCHEMA_VERSION", "DuckDBCatalogCorrupt", "DuckDBCatalogError", "DuckDBCatalogPublishError", "VIEW_NAMES"]
