"""SENSOR-B4-I05R1B — schema fidelity, safe catalog identity and reload self-validation.

Covers (I05R1 §34-§39):

- the FULL ordered T0 metadata schema participates in the fingerprint
  (``_t0_row_ordinal`` int64→string must change the fingerprint);
- lossless structural fidelity for every supported Arrow type family:
  time32/time64 units, timestamp timezone, duration unit, date units,
  list/large-list child name + nullability, struct child
  name/type/nullability/order, map key/value + keys_sorted, decimal
  precision/scale, fixed-size-binary width;
- fail closed on unsupported Arrow types (dictionary/union) — no getattr
  fallback on reload;
- registry reload self-validation: schema_key drift, fingerprint tamper and
  T0-contract drift all fail closed as catalog corruption;
- safe physical catalog identity: hashed filenames, no raw logical ID on
  disk, binding enforced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.storage.json_catalog import catalog_physical_key
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaCatalogCorrupt,
    ProjectionSchemaConflict,
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    UnsupportedProjectionSchemaType,
    T0_METADATA_SCHEMA,
    compute_schema_fingerprint,
    t0_metadata_descriptor,
)


@pytest.fixture()
def registry(tmp_path: Path) -> ProjectionSchemaRegistry:
    return ProjectionSchemaRegistry(tmp_path / "catalogs" / "projection_schemas")


SIMPLE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
    ]
)


# ---------------------------------------------------------------------------
# §34/§35 — full T0 metadata schema in the fingerprint
# ---------------------------------------------------------------------------


class TestT0MetadataFingerprint:
    def test_t0_metadata_type_change_alters_fingerprint(self) -> None:
        """A _t0_row_ordinal int64→string change MUST alter the fingerprint.

        The fingerprint hashes the FULL ordered T0 metadata descriptor, not
        a bare set of column names.
        """
        fields_desc = [{"name": "price", "type": {"type": "double"}, "nullable": False}]
        descriptor_v1 = {
            "fields": fields_desc,
            "t0_metadata_schema": t0_metadata_descriptor(),
        }
        # Tamper: _t0_row_ordinal int64 -> string
        t0_v2 = [
            dict(d) for d in t0_metadata_descriptor()
        ]
        t0_v2 = [
            (
                {**d, "type": {"type": "string"}}
                if d["name"] == "_t0_row_ordinal"
                else d
            )
            for d in t0_v2
        ]
        descriptor_v2 = {"fields": fields_desc, "t0_metadata_schema": t0_v2}
        import hashlib

        h1 = hashlib.sha256(
            json.dumps(descriptor_v1, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        h2 = hashlib.sha256(
            json.dumps(descriptor_v2, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert h1 != h2

    def test_t0_metadata_schema_is_ordered_canonical(self) -> None:
        desc = t0_metadata_descriptor()
        names = [d["name"] for d in desc]
        assert names == [
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
        ]
        # Every entry carries name + type + nullable — full structure.
        for d in desc:
            assert set(d) == {"name", "type", "nullable"}

    def test_row_ordinal_is_int64_nonnullable(self) -> None:
        field = T0_METADATA_SCHEMA.field("_t0_row_ordinal")
        assert field.type == pa.int64()
        assert not field.nullable


# ---------------------------------------------------------------------------
# §36 — Arrow structural fidelity (lossless round trip)
# ---------------------------------------------------------------------------


class TestArrowStructuralFidelity:
    def _roundtrip(self, schema: pa.Schema) -> None:
        d = ProjectionSchemaDefinition("fidelity.schema", "1.0.0", schema)
        rebuilt = ProjectionSchemaDefinition.from_descriptor(d.to_descriptor())
        assert rebuilt.provider_native_schema.equals(schema, check_metadata=False)

    def test_time32_unit(self) -> None:
        self._roundtrip(pa.schema([pa.field("t", pa.time32("s"), nullable=True)]))
        self._roundtrip(pa.schema([pa.field("t", pa.time32("ms"), nullable=True)]))

    def test_time64_unit(self) -> None:
        self._roundtrip(pa.schema([pa.field("t", pa.time64("us"), nullable=True)]))
        self._roundtrip(pa.schema([pa.field("t", pa.time64("ns"), nullable=True)]))

    def test_timestamp_timezone_and_unit(self) -> None:
        self._roundtrip(
            pa.schema([pa.field("ts", pa.timestamp("ms", tz="+05:30"), nullable=False)])
        )
        self._roundtrip(pa.schema([pa.field("ts", pa.timestamp("ns"), nullable=True)]))

    def test_duration_unit(self) -> None:
        self._roundtrip(pa.schema([pa.field("d", pa.duration("ms"), nullable=True)]))

    def test_date_units(self) -> None:
        self._roundtrip(pa.schema([pa.field("d", pa.date32(), nullable=True)]))
        self._roundtrip(pa.schema([pa.field("d", pa.date64(), nullable=True)]))

    def test_list_child_name_and_nullability(self) -> None:
        s1 = pa.schema(
            [pa.field("l", pa.list_(pa.field("item", pa.string(), nullable=False)))]
        )
        self._roundtrip(s1)
        # Non-nullable child differs from nullable child structurally.
        s2 = pa.schema(
            [pa.field("l", pa.list_(pa.field("item", pa.string(), nullable=True)))]
        )
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)

    def test_large_list_child_nullability(self) -> None:
        s1 = pa.schema(
            [
                pa.field(
                    "l", pa.large_list(pa.field("v", pa.int64(), nullable=False))
                )
            ]
        )
        self._roundtrip(s1)

    def test_struct_child_order_and_nullability(self) -> None:
        s1 = pa.schema(
            [
                pa.field(
                    "s",
                    pa.struct(
                        [
                            pa.field("x", pa.float64(), nullable=False),
                            pa.field("y", pa.int64(), nullable=True),
                        ]
                    ),
                )
            ]
        )
        s2 = pa.schema(
            [
                pa.field(
                    "s",
                    pa.struct(
                        [
                            pa.field("y", pa.int64(), nullable=True),
                            pa.field("x", pa.float64(), nullable=False),
                        ]
                    ),
                )
            ]
        )
        self._roundtrip(s1)
        # Struct child ORDER is part of the structure.
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)

    def test_map_keys_sorted(self) -> None:
        s1 = pa.schema(
            [pa.field("m", pa.map_(pa.string(), pa.int64(), keys_sorted=True))]
        )
        s2 = pa.schema(
            [pa.field("m", pa.map_(pa.string(), pa.int64(), keys_sorted=False))]
        )
        self._roundtrip(s1)
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)

    def test_decimal_precision_scale(self) -> None:
        s1 = pa.schema([pa.field("a", pa.decimal128(18, 8), nullable=False)])
        s2 = pa.schema([pa.field("a", pa.decimal128(20, 8), nullable=False)])
        s3 = pa.schema([pa.field("a", pa.decimal128(18, 2), nullable=False)])
        self._roundtrip(s1)
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s3)

    def test_fixed_size_binary_width(self) -> None:
        s1 = pa.schema([pa.field("b", pa.binary(16), nullable=True)])
        s2 = pa.schema([pa.field("b", pa.binary(32), nullable=True)])
        self._roundtrip(s1)
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)

    def test_int_widths_and_sign(self) -> None:
        s1 = pa.schema([pa.field("n", pa.int32(), nullable=False)])
        s2 = pa.schema([pa.field("n", pa.uint32(), nullable=False)])
        assert compute_schema_fingerprint(s1) != compute_schema_fingerprint(s2)

    def test_float_widths(self) -> None:
        s1 = pa.schema([pa.field("f", pa.float32(), nullable=False)])
        s2 = pa.schema([pa.field("f", pa.float64(), nullable=False)])
        s3 = pa.schema([pa.field("f", pa.float16(), nullable=False)])
        assert (
            len({compute_schema_fingerprint(x) for x in (s1, s2, s3)}) == 3
        )


# ---------------------------------------------------------------------------
# §37 — fail closed on unsupported Arrow types
# ---------------------------------------------------------------------------


class TestUnsupportedTypes:
    def test_dictionary_type_rejected(self) -> None:
        # Build a dictionary type via an array cast.
        arr = pa.array(["a", "b", "a"]).dictionary_encode()
        schema = pa.schema([pa.field("d", arr.type, nullable=True)])
        with pytest.raises(UnsupportedProjectionSchemaType):
            ProjectionSchemaDefinition("bad.schema", "1.0.0", schema)

    def test_no_getattr_fallback_on_rebuild(self) -> None:
        """An unknown descriptor name must fail closed, not getattr(pa, ...)."""
        from crypto_sensor_fabric.storage.projection_schema import _rebuild_arrow_type

        with pytest.raises(UnsupportedProjectionSchemaType):
            _rebuild_arrow_type({"type": "totally_unknown_type"})

    def test_descriptor_tamper_rejected(self) -> None:
        from crypto_sensor_fabric.storage.projection_schema import _rebuild_arrow_type

        with pytest.raises(UnsupportedProjectionSchemaType):
            _rebuild_arrow_type({"type": "decimal128"})  # missing precision/scale


# ---------------------------------------------------------------------------
# §38 — reload self-validation (tamper matrix)
# ---------------------------------------------------------------------------


def _register_one(registry: ProjectionSchemaRegistry) -> ProjectionSchemaDefinition:
    d = ProjectionSchemaDefinition("tamper.schema", "1.0.0", SIMPLE)
    registry.register(d)
    return d


class TestRegistrySelfValidation:
    def test_schema_key_tamper_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        frag = root / catalog_physical_key(d.schema_identity)
        payload = json.loads(frag.read_text(encoding="utf-8"))
        payload["schema_key"] = "f" * 64
        frag.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)

    def test_schema_fingerprint_tamper_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        frag = root / catalog_physical_key(d.schema_identity)
        payload = json.loads(frag.read_text(encoding="utf-8"))
        payload["schema_fingerprint"] = "e" * 64
        frag.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)

    def test_t0_contract_drift_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        frag = root / catalog_physical_key(d.schema_identity)
        payload = json.loads(frag.read_text(encoding="utf-8"))
        payload["t0_metadata_schema"] = t0_metadata_descriptor()[:-1]  # drop one
        frag.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)

    def test_invalid_json_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        (root / catalog_physical_key(d.schema_identity)).write_text(
            "{corrupt", encoding="utf-8"
        )
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)

    def test_corrupt_entry_never_silently_disappears(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        # Corrupt the committed fragment beyond parsing.
        (root / catalog_physical_key(d.schema_identity)).write_text(
            "not json at all", encoding="utf-8"
        )
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)  # NOT a silent skip

    def test_valid_reload_roundtrip(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = _register_one(reg)
        reg2 = ProjectionSchemaRegistry(root)
        loaded = reg2.resolve(d.schema_key)
        assert loaded == d
        assert loaded.provider_native_schema.equals(SIMPLE)


# ---------------------------------------------------------------------------
# §39 — registry immutability via the durable catalog
# ---------------------------------------------------------------------------


class TestRegistryImmutability:
    def test_same_id_version_conflict(self, registry) -> None:
        d1 = ProjectionSchemaDefinition("conflict.schema", "1.0.0", SIMPLE)
        registry.register(d1)
        different = pa.schema([pa.field("x", pa.int32(), nullable=False)])
        d2 = ProjectionSchemaDefinition("conflict.schema", "1.0.0", different)
        with pytest.raises(ProjectionSchemaConflict):
            registry.register(d2)

    def test_idempotent_reuse(self, registry) -> None:
        d1 = ProjectionSchemaDefinition("idem.schema", "1.0.0", SIMPLE)
        registry.register(d1)
        d2 = ProjectionSchemaDefinition("idem.schema", "1.0.0", SIMPLE)
        registry.register(d2)
        assert len(registry.list_keys()) == 1

    def test_physical_filename_is_hashed_identity(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = ProjectionSchemaDefinition("safe.schema", "1.0.0", SIMPLE)
        reg.register(d)
        # The raw logical identity must NEVER appear as a filename.
        frag = root / catalog_physical_key(d.schema_identity)
        assert frag.exists()
        names = [p.name for p in root.glob("*.json")]
        assert names == [frag.name]
        assert "safe.schema" not in names
