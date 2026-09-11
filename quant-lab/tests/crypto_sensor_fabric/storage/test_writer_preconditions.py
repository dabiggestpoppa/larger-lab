"""SENSOR-B4-I05R1D — row-lineage ownership and publication preconditions.

Covers (I05R1 §24-§33):

- provider-native rows may NEVER supply ``_t0_*`` keys — typed rejection
  before any physical work, including the I04R1 quality-flag repair which
  now happens BEFORE publication (§24/§29);
- quality flags validated pre-publication: enum values accepted, unknown
  strings rejected before any T0B bytes exist (§29);
- source hashes validated pre-publication: malformed SHA and duplicate
  sources fail before staging (§28);
- the registered-schema gate: an unregistered schema refuses physical
  publication (§30);
- exact native row-field contract: unknown keys and missing non-nullable
  fields fail closed; nullable-missing becomes null (§31);
- RowProjectionLineage ownership: pairs outside the committed file-level
  lineage set are rejected pre-publication; valid pairs land in the file
  and survive staged verification (§26/§27);
- artifact commit without physical evidence fails (§22), and metadata-only
  repos remain usable for unit-level tests.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionPreconditionError,
    ProjectionSchemaMismatch,
    ProjectionSchemaNotFound,
    ProjectionSourceNotUsable,
    RowProjectionLineage,
    write_projection,
)
from crypto_sensor_fabric.providers.base.enums import QualityFlagAcquisition
from crypto_sensor_fabric.storage.models import RawProjectionArtifact

NATIVE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)

ROWS = [{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}]


class Harness:
    """Minimal writer harness on a short root (Windows MAX_PATH)."""

    def __init__(self, tmp_path) -> None:
        import shutil

        self.root = _ROOT
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)
        self.registry = ProjectionSchemaRegistry(
            self.root / "catalogs" / "projection_schemas"
        )
        self.definition = ProjectionSchemaDefinition(
            projection_schema_id="r1d.schema",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE,
        )
        self.registry.register(self.definition)
        self._tmp = tmp_path

    def close(self) -> None:
        import shutil

        if self.root.exists():
            shutil.rmtree(self.root)

    def write(self, *, rows=ROWS, register=True, schema=None, **kwargs):
        return write_projection(
            root=self.root,
            rows=rows,
            schema_definition=schema or self.definition,
            schema_registry=self.registry if register else None,
            projection_id=kwargs.pop("projection_id", "proj-r1d"),
            source_blob_sha256=kwargs.pop("source_blob_sha256", ["a" * 64]),
            acquisition_ids=kwargs.pop("acquisition_ids", ["acq-1"]),
            provider=kwargs.pop("provider", "kraken"),
            venue=kwargs.pop("venue", "futures"),
            sensor_family=kwargs.pop("sensor_family", "market_data"),
            native_instrument=kwargs.pop("native_instrument", "BTC-USDT"),
            native_granularity=kwargs.pop("native_granularity", "1m"),
            parser_version=kwargs.pop("parser_version", "1.0.0"),
            partition_key=kwargs.pop(
                "partition_key", "kraken/futures/BTC-USDT/2026-01-15"
            ),
            logical_year=2026,
            logical_month=1,
            logical_day=15,
            **kwargs,
        )


_ROOT = Path("C:/tmp_r1d_proj")


# ---------------------------------------------------------------------------
# §24 — reserved _t0_* row keys rejected
# ---------------------------------------------------------------------------


class TestReservedRowKeys:
    def test_reserved_source_key_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [dict(ROWS[0], **{"_t0_source_blob_sha256": "f" * 64})]
            with pytest.raises(ProjectionPreconditionError, match="reserved"):
                h.write(rows=rows)
            # Nothing was physically published.
            assert not any(h.root.glob("projections/**/*.parquet"))
        finally:
            h.close()

    def test_reserved_acquisition_key_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [dict(ROWS[0], **{"_t0_acquisition_id": "fake-acq"})]
            with pytest.raises(ProjectionPreconditionError, match="reserved"):
                h.write(rows=rows)
        finally:
            h.close()

    def test_all_reserved_names_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            for col in (
                "_t0_projection_id",
                "_t0_provider",
                "_t0_venue",
                "_t0_sensor_family",
                "_t0_native_instrument",
                "_t0_parser_version",
                "_t0_schema_version",
                "_t0_row_ordinal",
            ):
                rows = [dict(ROWS[0], **{col: "x"})]
                with pytest.raises(ProjectionPreconditionError, match="reserved"):
                    h.write(rows=rows)
        finally:
            h.close()

    def test_t0_layer_always_overwrites_by_construction(self, tmp_path) -> None:
        """Injected metadata is layer-owned: values come from arguments."""
        h = Harness(tmp_path)
        try:
            artifact, path = h.write()
            import pyarrow.parquet as pq

            table = pq.read_table(str(path))
            assert set(table.column("_t0_provider").to_pylist()) == {"kraken"}
            assert set(table.column("_t0_row_ordinal").to_pylist()) == {0}
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §29 — quality flags validated before physical publication
# ---------------------------------------------------------------------------


class TestQualityFlagPrevalidation:
    def test_invalid_flag_fails_before_publication(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="quality flag"):
                h.write(quality_flags=["NOT_A_REAL_FLAG"])
            assert not any(h.root.glob("projections/**/*.parquet"))
        finally:
            h.close()

    def test_enum_flags_accepted(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            artifact, _ = h.write(
                quality_flags=[
                    QualityFlagAcquisition.PARTIAL_INTERVAL,
                    QualityFlagAcquisition.SCHEMA_ADDITIVE,
                ]
            )
            assert artifact.quality_flags == [
                QualityFlagAcquisition.PARTIAL_INTERVAL,
                QualityFlagAcquisition.SCHEMA_ADDITIVE,
            ]
        finally:
            h.close()

    def test_string_flags_normalized(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            artifact, _ = h.write(quality_flags=["PARTIAL_INTERVAL"])
            assert artifact.quality_flags == [QualityFlagAcquisition.PARTIAL_INTERVAL]
        finally:
            h.close()

    def test_flag_failure_leaves_no_staging_trace(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError):
                h.write(quality_flags=["BOGUS"])
            staging = h.root / "_staging"
            if staging.exists():
                assert not any(staging.glob("*.parquet"))
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §28 — cheap deterministic inputs validated first
# ---------------------------------------------------------------------------


class TestSourcePrevalidation:
    def test_malformed_sha_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="malformed"):
                h.write(source_blob_sha256=["nothex"])
        finally:
            h.close()

    def test_duplicate_sources_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="duplicate"):
                h.write(
                    source_blob_sha256=["a" * 64, "a" * 64],
                    acquisition_ids=["acq-1", "acq-2"],
                )
        finally:
            h.close()

    def test_acquisition_id_count_mismatch_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="parallel"):
                h.write(
                    source_blob_sha256=["a" * 64, "b" * 64],
                    acquisition_ids=["only-one"],
                )
        finally:
            h.close()

    def test_empty_acquisition_id_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError):
                h.write(acquisition_ids=[""])
        finally:
            h.close()

    def test_negative_shard_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="shard_id"):
                h.write(shard_id=-1)
        finally:
            h.close()

    def test_projection_id_with_path_chars_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="structural"):
                h.write(projection_id="../evil")
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §30 — registered-schema publication gate
# ---------------------------------------------------------------------------


class TestRegisteredSchemaGate:
    def test_unregistered_schema_refused(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            unregistered = ProjectionSchemaDefinition(
                projection_schema_id="never.registered",
                projection_schema_version="1.0.0",
                provider_native_schema=NATIVE,
            )
            with pytest.raises(ProjectionSchemaNotFound, match="registered"):
                h.write(schema=unregistered)
            assert not any(h.root.glob("projections/**/*.parquet"))
        finally:
            h.close()

    def test_no_registry_refused(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            with pytest.raises(ProjectionPreconditionError, match="registry"):
                h.write(register=False)
        finally:
            h.close()

    def test_fingerprint_drift_refused(self, tmp_path) -> None:
        """Same id/version, different structure than registered → mismatch."""
        h = Harness(tmp_path)
        try:
            drifted = ProjectionSchemaDefinition(
                projection_schema_id="r1d.schema",
                projection_schema_version="1.0.0",
                provider_native_schema=pa.schema(
                    [
                        pa.field("price", pa.float32(), nullable=False),
                        pa.field("qty", pa.int64(), nullable=True),
                        pa.field("symbol", pa.string(), nullable=False),
                    ]
                ),
            )
            with pytest.raises(ProjectionSchemaMismatch, match="fingerprint"):
                h.write(schema=drifted)
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §31 — exact native row-field contract
# ---------------------------------------------------------------------------


class TestNativeFieldContract:
    def test_unknown_field_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [dict(ROWS[0], **{"mystery_column": 1})]
            with pytest.raises(ProjectionSchemaMismatch, match="unknown"):
                h.write(rows=rows)
        finally:
            h.close()

    def test_missing_nonnullable_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [{"qty": 1, "symbol": "BTC"}]  # price (non-nullable) missing
            with pytest.raises(ProjectionSchemaMismatch, match="non-nullable"):
                h.write(rows=rows)
        finally:
            h.close()

    def test_missing_nullable_becomes_null(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [{"price": 2.0, "symbol": "BTC"}]  # qty nullable, absent
            artifact, path = h.write(rows=rows)
            import pyarrow.parquet as pq

            table = pq.read_table(str(path))
            assert table.column("qty")[0].as_py() is None
            assert artifact.row_count == 1
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §26/§27 — RowProjectionLineage ownership
# ---------------------------------------------------------------------------


class TestRowLineageOwnership:
    def test_row_lineage_type_rejects_bad_ordinal(self) -> None:
        with pytest.raises(ProjectionPreconditionError):
            RowProjectionLineage(-1, "a" * 64, "acq")

    def test_row_lineage_type_rejects_bad_sha(self) -> None:
        # validate_sha256_hex raises ValueError; the writer surfaces typed
        # ProjectionPreconditionError.  At the type level, the ValueError is
        # the fail-closed contract.
        with pytest.raises((ProjectionPreconditionError, ValueError)):
            RowProjectionLineage(0, "nothex", "acq")

    def test_row_lineage_type_rejects_empty_acq(self) -> None:
        with pytest.raises(ProjectionPreconditionError):
            RowProjectionLineage(0, "a" * 64, "")

    def test_undeclared_pair_rejected_prepublication(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rl = RowProjectionLineage(0, "b" * 64, "acq-undeclared")
            with pytest.raises(ProjectionPreconditionError, match="undeclared"):
                h.write(row_lineage=[rl])
            assert not any(h.root.glob("projections/**/*.parquet"))
        finally:
            h.close()

    def test_single_source_row_lineage_must_match_source(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rl = RowProjectionLineage(0, "b" * 64, "acq-1")
            # ("b"*64, "acq-1") is not the declared single-source pair.
            with pytest.raises(ProjectionPreconditionError, match="undeclared"):
                h.write(row_lineage=[rl])
        finally:
            h.close()

    def test_valid_multi_source_row_lineage(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rows = [
                {"price": 1.0, "qty": 1, "symbol": "BTC-USDT"},
                {"price": 2.0, "qty": 2, "symbol": "ETH-USDT"},
            ]
            rl = RowProjectionLineage(0, "b" * 64, "acq-b")
            artifact, path = h.write(
                rows=rows,
                source_blob_sha256=["a" * 64, "b" * 64],
                acquisition_ids=["acq-a", "acq-b"],
                row_lineage=[rl],
            )
            import pyarrow.parquet as pq

            table = pq.read_table(str(path))
            # Row 0 carries its defensible attribution; row 1 stays NULL.
            assert table.column("_t0_source_blob_sha256").to_pylist() == [
                "b" * 64,
                None,
            ]
            assert table.column("_t0_acquisition_id").to_pylist() == [
                "acq-b",
                None,
            ]
            assert artifact.row_count == 2
        finally:
            h.close()

    def test_duplicate_row_lineage_rejected(self, tmp_path) -> None:
        h = Harness(tmp_path)
        try:
            rl = RowProjectionLineage(0, "a" * 64, "acq-1")
            with pytest.raises(ProjectionPreconditionError, match="duplicate"):
                h.write(row_lineage=[rl, rl])
        finally:
            h.close()


# ---------------------------------------------------------------------------
# §22 — artifact commit requires physical evidence
# ---------------------------------------------------------------------------


class TestArtifactPhysicalGate:
    def _artifact(self, **overrides) -> RawProjectionArtifact:
        kwargs = dict(
            projection_id="proj-phys",
            source_blob_sha256=["a" * 64],
            projection_schema_id="r1d.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=1,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri="projections/does/not/exist.parquet",
            projection_sha256="d" * 64,
        )
        kwargs.update(overrides)
        return RawProjectionArtifact(**kwargs)

    def test_metadata_only_repo_allows_commit(self, tmp_path) -> None:
        repo = ProjectionArtifactRepository(tmp_path / "artifacts")
        committed = repo.commit(self._artifact())
        assert committed.projection_id == "proj-phys"

    def test_commit_without_physical_fails_when_wired(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.projections import ProjectionCorruption

        repo = ProjectionArtifactRepository(
            tmp_path / "artifacts",
            projection_root=tmp_path / "t0",
            schema_registry=None,
        )
        with pytest.raises(ProjectionCorruption, match="missing"):
            repo.commit(self._artifact())

    def test_commit_with_sha_mismatch_fails(self, tmp_path) -> None:
        import pyarrow.parquet as pq
        from crypto_sensor_fabric.storage.projections import ProjectionCorruption

        t0 = tmp_path / "t0"
        t0.mkdir()
        table = pa.table({"x": [1]})
        uri = "projections/fake/part-00000.parquet"
        target = t0 / uri
        target.parent.mkdir(parents=True)
        pq.write_table(table, str(target))

        repo = ProjectionArtifactRepository(
            tmp_path / "artifacts", projection_root=t0
        )
        with pytest.raises(ProjectionCorruption, match="SHA"):
            repo.commit(self._artifact(projection_uri=uri))

    def test_commit_with_row_count_mismatch_fails(self, tmp_path) -> None:
        import pyarrow.parquet as pq
        from crypto_sensor_fabric.storage.checksums import sha256_file
        from crypto_sensor_fabric.storage.projections import ProjectionCorruption

        t0 = tmp_path / "t0"
        t0.mkdir()
        table = pa.table({"x": [1, 2, 3]})
        uri = "projections/fake/part-00001.parquet"
        target = t0 / uri
        target.parent.mkdir(parents=True)
        pq.write_table(table, str(target))
        sha = sha256_file(str(target)).hex_digest

        repo = ProjectionArtifactRepository(
            tmp_path / "artifacts", projection_root=t0
        )
        with pytest.raises(ProjectionCorruption, match="row count"):
            repo.commit(
                self._artifact(
                    projection_uri=uri, projection_sha256=sha, row_count=99
                )
            )

    def test_unsafe_uri_fails(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.projections import ProjectionCorruption

        repo = ProjectionArtifactRepository(
            tmp_path / "artifacts", projection_root=tmp_path / "t0"
        )
        with pytest.raises(ProjectionCorruption, match="resolve"):
            repo.commit(self._artifact(projection_uri="../../escape.parquet"))
