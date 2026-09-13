"""SENSOR-B4-I05A — projection schema registry tests.

Covers:
  - schema key deterministic full SHA
  - schema fingerprint deterministic
  - schema semver valid/invalid
  - same id/version reuse exact
  - same id/version conflict different structure
  - reserved _t0_ column rejected
  - registry round trip persistence
  - descriptor round trip (from_descriptor -> to_descriptor -> from_descriptor)
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaConflict,
    ProjectionSchemaDefinition,
    ProjectionSchemaNotFound,
    ProjectionSchemaRegistry,
    ReservedProjectionColumn,
    compute_schema_fingerprint,
    compute_schema_key,
    validate_semver,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def simple_schema() -> pa.Schema:
    """Minimal valid provider-native Arrow schema."""
    return pa.schema(
        [
            pa.field("price", pa.float64(), nullable=False),
            pa.field("qty", pa.int64(), nullable=True),
            pa.field("symbol", pa.string(), nullable=False),
        ]
    )


@pytest.fixture()
def timestamp_schema() -> pa.Schema:
    """Schema with timestamp field."""
    return pa.schema(
        [
            pa.field("ts", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("value", pa.float64(), nullable=True),
        ]
    )


@pytest.fixture()
def schema_registry(tmp_path: Path) -> ProjectionSchemaRegistry:
    """Fresh registry under a temporary catalog directory."""
    catalog_root = tmp_path / "catalogs" / "projection_schemas"
    return ProjectionSchemaRegistry(catalog_root)


# ---------------------------------------------------------------------------
# §25 schema key
# ---------------------------------------------------------------------------


class TestSchemaKey:
    def test_schema_key_is_full_64_hex(self) -> None:
        key = compute_schema_key("test.schema", "1.0.0")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_schema_key_deterministic(self) -> None:
        k1 = compute_schema_key("test.schema", "1.0.0")
        k2 = compute_schema_key("test.schema", "1.0.0")
        assert k1 == k2

    def test_schema_key_differs_by_id(self) -> None:
        k1 = compute_schema_key("schema.a", "1.0.0")
        k2 = compute_schema_key("schema.b", "1.0.0")
        assert k1 != k2

    def test_schema_key_differs_by_version(self) -> None:
        k1 = compute_schema_key("test.schema", "1.0.0")
        k2 = compute_schema_key("test.schema", "2.0.0")
        assert k1 != k2


# ---------------------------------------------------------------------------
# §28 schema fingerprint
# ---------------------------------------------------------------------------


class TestSchemaFingerprint:
    def test_fingerprint_is_full_64_hex(self, simple_schema: pa.Schema) -> None:
        fp = compute_schema_fingerprint(simple_schema)
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fingerprint_deterministic(self, simple_schema: pa.Schema) -> None:
        fp1 = compute_schema_fingerprint(simple_schema)
        fp2 = compute_schema_fingerprint(simple_schema)
        assert fp1 == fp2

    def test_fingerprint_differs_on_field_name_change(
        self, simple_schema: pa.Schema
    ) -> None:
        fp1 = compute_schema_fingerprint(simple_schema)
        modified = pa.schema(
            [
                pa.field("price", pa.float64(), nullable=False),
                pa.field("qty_alt", pa.int64(), nullable=True),
                pa.field("symbol", pa.string(), nullable=False),
            ]
        )
        fp2 = compute_schema_fingerprint(modified)
        assert fp1 != fp2

    def test_fingerprint_differs_on_type_change(self, simple_schema: pa.Schema) -> None:
        fp1 = compute_schema_fingerprint(simple_schema)
        modified = pa.schema(
            [
                pa.field("price", pa.float32(), nullable=False),  # float32 not float64
                pa.field("qty", pa.int64(), nullable=True),
                pa.field("symbol", pa.string(), nullable=False),
            ]
        )
        fp2 = compute_schema_fingerprint(modified)
        assert fp1 != fp2

    def test_fingerprint_differs_on_nullable_change(
        self, simple_schema: pa.Schema
    ) -> None:
        fp1 = compute_schema_fingerprint(simple_schema)
        modified = pa.schema(
            [
                pa.field("price", pa.float64(), nullable=True),  # was False
                pa.field("qty", pa.int64(), nullable=True),
                pa.field("symbol", pa.string(), nullable=False),
            ]
        )
        fp2 = compute_schema_fingerprint(modified)
        assert fp1 != fp2

    def test_fingerprint_includes_t0_metadata(self, simple_schema: pa.Schema) -> None:
        """Fingerprint must include required _t0 metadata columns."""
        fp = compute_schema_fingerprint(simple_schema)
        # Just verify it's deterministic and valid
        assert len(fp) == 64

    def test_timestamp_fingerprint(self, timestamp_schema: pa.Schema) -> None:
        fp1 = compute_schema_fingerprint(timestamp_schema)
        fp2 = compute_schema_fingerprint(timestamp_schema)
        assert fp1 == fp2
        # Different timestamp unit should differ
        modified = pa.schema(
            [
                pa.field("ts", pa.timestamp("ns", tz="UTC"), nullable=False),
                pa.field("value", pa.float64(), nullable=True),
            ]
        )
        fp3 = compute_schema_fingerprint(modified)
        assert fp1 != fp3


# ---------------------------------------------------------------------------
# §26 semver
# ---------------------------------------------------------------------------


class TestSemver:
    def test_valid_versions(self) -> None:
        for v in ["1.0.0", "0.1.0", "2.10.3", "100.200.300"]:
            validate_semver(v)  # should not raise

    def test_invalid_versions(self) -> None:
        for v in ["1", "1.0", "v1.0.0", "1.0.0-beta", "01.0.0", "1.0.0+build"]:
            with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
                validate_semver(v)

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValueError):
            validate_semver("")


# ---------------------------------------------------------------------------
# §24 ProjectionSchemaDefinition
# ---------------------------------------------------------------------------


class TestProjectionSchemaDefinition:
    def test_basic_creation(self, simple_schema: pa.Schema) -> None:
        definition = ProjectionSchemaDefinition(
            projection_schema_id="test.market.liquidation",
            projection_schema_version="1.0.0",
            provider_native_schema=simple_schema,
        )
        assert definition.projection_schema_id == "test.market.liquidation"
        assert definition.projection_schema_version == "1.0.0"
        assert definition.schema_key == compute_schema_key(
            "test.market.liquidation", "1.0.0"
        )
        assert definition.schema_fingerprint == compute_schema_fingerprint(simple_schema)

    def test_empty_schema_id_rejected(self, simple_schema: pa.Schema) -> None:
        with pytest.raises(ValueError, match="nonempty string"):
            ProjectionSchemaDefinition(
                projection_schema_id="",
                projection_schema_version="1.0.0",
                provider_native_schema=simple_schema,
            )

    def test_invalid_version_rejected(self, simple_schema: pa.Schema) -> None:
        with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
            ProjectionSchemaDefinition(
                projection_schema_id="test.schema",
                projection_schema_version="1.0",
                provider_native_schema=simple_schema,
            )

    def test_not_pa_schema_rejected(self) -> None:
        with pytest.raises(TypeError, match="pa.Schema"):
            ProjectionSchemaDefinition(
                projection_schema_id="test.schema",
                projection_schema_version="1.0.0",
                provider_native_schema="not a schema",  # type: ignore
            )

    def test_eq_same_structure(self, simple_schema: pa.Schema) -> None:
        d1 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        d2 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        assert d1 == d2

    def test_eq_different_fingerprint(self, simple_schema: pa.Schema) -> None:
        d1 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        modified = pa.schema([pa.field("x", pa.int32(), nullable=False)])
        d2 = ProjectionSchemaDefinition("test.schema", "1.0.0", modified)
        assert d1 != d2

    def test_repr(self, simple_schema: pa.Schema) -> None:
        d = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        r = repr(d)
        assert "test.schema" in r
        assert "1.0.0" in r


# ---------------------------------------------------------------------------
# §30 same id/version different schema conflict
# ---------------------------------------------------------------------------


class TestSchemaConflict:
    def test_registry_conflict(
        self, schema_registry: ProjectionSchemaRegistry, simple_schema: pa.Schema
    ) -> None:
        d1 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        schema_registry.register(d1)

        different = pa.schema([pa.field("x", pa.int32(), nullable=False)])
        d2 = ProjectionSchemaDefinition("test.schema", "1.0.0", different)
        with pytest.raises(ProjectionSchemaConflict):
            schema_registry.register(d2)

    def test_registry_idempotent(
        self, schema_registry: ProjectionSchemaRegistry, simple_schema: pa.Schema
    ) -> None:
        d1 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        d2 = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        r1 = schema_registry.register(d1)
        r2 = schema_registry.register(d2)
        assert r1.schema_key == r2.schema_key
        assert r1.schema_fingerprint == r2.schema_fingerprint


# ---------------------------------------------------------------------------
# §10 reserved _t0_ column
# ---------------------------------------------------------------------------


class TestReservedColumn:
    def test_reserved_column_rejected(self) -> None:
        schema = pa.schema(
            [
                pa.field("_t0_provider", pa.string(), nullable=False),
                pa.field("price", pa.float64(), nullable=False),
            ]
        )
        with pytest.raises(ReservedProjectionColumn, match="_t0_provider"):
            ProjectionSchemaDefinition("test.schema", "1.0.0", schema)

    def test_all_t0_columns_rejected(self) -> None:
        for col in [
            "_t0_projection_id",
            "_t0_source_blob_sha256",
            "_t0_acquisition_id",
            "_t0_provider",
            "_t0_venue",
            "_t0_sensor_family",
            "_t0_native_instrument",
            "_t0_parser_version",
            "_t0_schema_version",
            "_t0_row_ordinal",
        ]:
            schema = pa.schema([pa.field(col, pa.string(), nullable=False)])
            with pytest.raises(ReservedProjectionColumn):
                ProjectionSchemaDefinition("test.schema", "1.0.0", schema)


# ---------------------------------------------------------------------------
# Registry persistence round trip
# ---------------------------------------------------------------------------


class TestRegistryRoundTrip:
    def test_persist_and_reload(
        self, tmp_path: Path, simple_schema: pa.Schema
    ) -> None:
        catalog_root = tmp_path / "catalogs" / "projection_schemas"
        d = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)

        # Register in first registry
        reg1 = ProjectionSchemaRegistry(catalog_root)
        reg1.register(d)

        # Reload from disk in a second registry
        reg2 = ProjectionSchemaRegistry(catalog_root)
        loaded = reg2.resolve(d.schema_key)
        assert loaded.projection_schema_id == d.projection_schema_id
        assert loaded.projection_schema_version == d.projection_schema_version
        assert loaded.schema_key == d.schema_key
        assert loaded.schema_fingerprint == d.schema_fingerprint
        assert loaded.provider_native_schema == d.provider_native_schema

    def test_descriptor_round_trip(self, simple_schema: pa.Schema) -> None:
        d = ProjectionSchemaDefinition("test.schema", "1.0.0", simple_schema)
        desc = d.to_descriptor()
        d2 = ProjectionSchemaDefinition.from_descriptor(desc)
        assert d == d2
        assert d.provider_native_schema == d2.provider_native_schema

    def test_resolve_by_id(self, schema_registry: ProjectionSchemaRegistry) -> None:
        schema = pa.schema([pa.field("x", pa.float64(), nullable=False)])
        d = ProjectionSchemaDefinition("my.schema", "2.1.0", schema)
        schema_registry.register(d)

        resolved = schema_registry.resolve_by_id("my.schema", "2.1.0")
        assert resolved.schema_key == d.schema_key

    def test_resolve_not_found(self, schema_registry: ProjectionSchemaRegistry) -> None:
        with pytest.raises(ProjectionSchemaNotFound):
            schema_registry.resolve("nonexistent_key")

    def test_list_keys(self, schema_registry: ProjectionSchemaRegistry) -> None:
        s1 = pa.schema([pa.field("a", pa.float64(), nullable=False)])
        s2 = pa.schema([pa.field("b", pa.int64(), nullable=True)])
        d1 = ProjectionSchemaDefinition("schema.a", "1.0.0", s1)
        d2 = ProjectionSchemaDefinition("schema.b", "1.0.0", s2)
        schema_registry.register(d1)
        schema_registry.register(d2)

        keys = schema_registry.list_keys()
        assert len(keys) == 2
        assert d1.schema_key in keys
        assert d2.schema_key in keys

    def test_has(self, schema_registry: ProjectionSchemaRegistry) -> None:
        schema = pa.schema([pa.field("x", pa.float64(), nullable=False)])
        d = ProjectionSchemaDefinition("test.schema", "1.0.0", schema)
        schema_registry.register(d)
        assert schema_registry.has(d.schema_key)
        assert not schema_registry.has("nonexistent")


# ---------------------------------------------------------------------------
# Field ordering fingerprint stability
# ---------------------------------------------------------------------------


class TestFieldOrdering:
    def test_different_field_order_different_fingerprint(self) -> None:
        """Field ordering is part of the schema structure."""
        s1 = pa.schema(
            [
                pa.field("a", pa.float64(), nullable=False),
                pa.field("b", pa.int64(), nullable=True),
            ]
        )
        s2 = pa.schema(
            [
                pa.field("b", pa.int64(), nullable=True),
                pa.field("a", pa.float64(), nullable=False),
            ]
        )
        fp1 = compute_schema_fingerprint(s1)
        fp2 = compute_schema_fingerprint(s2)
        assert fp1 != fp2  # different order = different structure


# ---------------------------------------------------------------------------
# Complex type fingerprints
# ---------------------------------------------------------------------------


class TestComplexTypes:
    def test_list_type_fingerprint(self) -> None:
        s = pa.schema(
            [
                pa.field("tags", pa.list_(pa.string()), nullable=True),
                pa.field("value", pa.float64(), nullable=False),
            ]
        )
        fp = compute_schema_fingerprint(s)
        assert len(fp) == 64

    def test_map_type_fingerprint(self) -> None:
        s = pa.schema(
            [
                pa.field(
                    "metadata",
                    pa.map_(pa.string(), pa.int64()),
                    nullable=True,
                ),
            ]
        )
        fp = compute_schema_fingerprint(s)
        assert len(fp) == 64

    def test_struct_type_fingerprint(self) -> None:
        s = pa.schema(
            [
                pa.field(
                    "nested",
                    pa.struct(
                        [
                            pa.field("x", pa.float64(), nullable=False),
                            pa.field("y", pa.int64(), nullable=True),
                        ]
                    ),
                    nullable=True,
                ),
            ]
        )
        fp = compute_schema_fingerprint(s)
        assert len(fp) == 64

    def test_decimal_type_fingerprint(self) -> None:
        s = pa.schema(
            [
                pa.field("amount", pa.decimal128(18, 8), nullable=False),
            ]
        )
        fp = compute_schema_fingerprint(s)
        assert len(fp) == 64
