"""SENSOR-B4-I04B/D — durable EvidenceBlob metadata + AcquisitionRecord catalog.

Covers the immutable Parquet fragment catalog: physical verification gate,
idempotence/conflict typing, repeated-acquisition semantics, empty-body
evidence, policy-B (blob_sha256, storage_encoding) physical keys, lossless
I04A round trips, and fail-closed fragment reads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import (
    Granularity,
    QualityFlagAcquisition,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.models import AdapterEvidenceRef, ResumeToken
from crypto_sensor_fabric.storage import (
    AcquisitionIdentityConflict,
    AcquisitionNotFound,
    AcquisitionRecord,
    BlobMetadataConflict,
    BlobMetadataNotFound,
    BlobStorageKey,
    CatalogIntegrityError,
    DanglingBlobReference,
    EvidenceBlob,
    IntegrityState,
    LocalBlobStore,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.catalog import (
    ACQUISITION_SCHEMA,
    BLOB_SCHEMA,
    AcquisitionRepository,
    BlobMetadataRepository,
    LocalEvidenceCatalog,
    read_fragment,
)

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def put_data(store: LocalBlobStore, data: bytes) -> EvidenceBlob:
    result = store.put_bytes(
        data,
        storage_encoding=StorageEncoding.NONE,
        source_media_type=MEDIA,
    )
    return result.blob


def make_blob_repo(root: Path) -> tuple[LocalBlobStore, BlobMetadataRepository]:
    store = make_store(root)
    repo = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
    return store, repo


def _record(**overrides: Any) -> AcquisitionRecord:
    kwargs: dict[str, Any] = {
        "acquisition_id": "acq-1",
        "provider_id": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "request_fingerprint": "fp-abc",
        "adapter_version": "kraken-adapter-v2",
        "adapter_capability_version": "kraken-capability-v2",
        "requested_start": FIXED,
        "requested_end": FIXED,
        "actual_start": None,
        "actual_end": None,
        "native_instrument": "PI_XBTUSD",
        "native_granularity": Granularity.G1H,
        "request_started_at": FIXED,
        "response_observed_at": FIXED,
        "ingested_at": FIXED,
        "http_status_or_source_status": "200",
        "endpoint_host": "futures.kraken.com",
        "endpoint_path": "/api/charts/v1/analytics/PI_XBTUSD/funding",
        "request_family": "market_analytics_funding",
        "source_locator": "https://futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/funding",
        "blob_sha256": None,
        "schema_state": SchemaState.KNOWN_SCHEMA,
        "evidence_ref": AdapterEvidenceRef(
            evidence_id="ev-1",
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        ),
        "provider_checksum_algorithm": None,
        "provider_checksum_value": None,
        "provider_checksum_verified": None,
        "resume_token_before": None,
        "resume_token_after": None,
        "quality_flags": [QualityFlagAcquisition.PARTIAL_INTERVAL],
        "failure_ref": None,
    }
    kwargs.update(overrides)
    return AcquisitionRecord(**kwargs)


class TestBlobMetadataRepository:
    def test_commit_creates_immutable_fragment(self, tmp_path: Path) -> None:
        store, repo = make_blob_repo(tmp_path)
        blob = put_data(store, b'{"a": 1}')
        returned, receipt = repo.append_metadata(blob)
        assert returned == blob
        path = tmp_path / "catalogs" / "manifests" / "blobs" / (
            f"{blob.blob_sha256}.NONE.parquet"
        )
        assert path.exists()
        assert receipt.fragment_sha256
        # exactly one durable row, schema-enforced
        rows = read_fragment(path, BLOB_SCHEMA)
        assert len(rows) == 1
        assert rows[0]["blob_sha256"] == blob.blob_sha256
        assert rows[0]["storage_encoding"] == "NONE"
        # the I03 commit already proved local hash verification
        assert rows[0]["integrity_state"] == "LOCAL_HASH_VERIFIED"

    def test_idempotent_same_key_same_record(self, tmp_path: Path) -> None:
        store, repo = make_blob_repo(tmp_path)
        blob = put_data(store, b"x" * 10)
        _, first = repo.append_metadata(blob)
        _, second = repo.append_metadata(blob)
        assert first.fragment_sha256 == second.fragment_sha256

    def test_same_key_conflicting_record_fails_typed(self, tmp_path: Path) -> None:
        store, repo = make_blob_repo(tmp_path)
        blob = put_data(store, b"x" * 10)
        repo.append_metadata(blob)
        conflict = blob.model_copy(update={"storage_uri": "t0://different"})
        with pytest.raises(BlobMetadataConflict):
            repo.append_metadata(conflict)
        # original is never overwritten
        rows = read_fragment(
            tmp_path / "catalogs" / "manifests" / "blobs"
            / f"{blob.blob_sha256}.NONE.parquet",
            BLOB_SCHEMA,
        )
        assert rows[0]["storage_uri"] == blob.storage_uri

    def test_missing_physical_blob_fails_closed(self, tmp_path: Path) -> None:
        _, repo = make_blob_repo(tmp_path)
        phantom = EvidenceBlob(
            blob_sha256="a" * 64,
            byte_length=1,
            stored_byte_length=1,
            source_media_type=MEDIA,
            storage_encoding=StorageEncoding.NONE,
            created_at=FIXED,
            storage_uri="t0://blobs/phantom",
            integrity_state=IntegrityState.UNVERIFIED,
        )
        with pytest.raises(DanglingBlobReference):
            repo.append_metadata(phantom)

    def test_stored_length_mismatch_fails_closed(self, tmp_path: Path) -> None:
        store, repo = make_blob_repo(tmp_path)
        blob = put_data(store, b"y" * 20)
        bad = blob.model_copy(update={"stored_byte_length": 999})
        with pytest.raises(CatalogIntegrityError):
            repo.append_metadata(bad)

    def test_corrupt_fragment_never_becomes_truth(self, tmp_path: Path) -> None:
        store, repo = make_blob_repo(tmp_path)
        blob = put_data(store, b"z" * 5)
        repo.append_metadata(blob)
        path = (
            tmp_path / "catalogs" / "manifests" / "blobs"
            / f"{blob.blob_sha256}.NONE.parquet"
        )
        path.write_bytes(b"not a parquet file at all")
        with pytest.raises(CatalogIntegrityError):
            repo.get_blob_metadata(blob.blob_sha256)

    def test_get_blob_metadata_not_found(self, tmp_path: Path) -> None:
        _, repo = make_blob_repo(tmp_path)
        with pytest.raises(BlobMetadataNotFound):
            repo.get_blob_metadata("b" * 64)

    def test_policy_b_two_encodings_for_one_content_hash(
        self, tmp_path: Path
    ) -> None:
        """Same H1 may exist under NONE and ZSTD; BOTH are durable metadata.

        Policy B (I04 §66/§67): blob_sha256 stays CONTENT identity; the
        physical-object record key is (blob_sha256, storage_encoding).
        """
        store = make_store(tmp_path)
        repo = BlobMetadataRepository(tmp_path, blob_store=store, clock=lambda: FIXED)
        data = b'{"funding": [1, 2, 3]}'
        none_blob = store.put_bytes(
            data,
            storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
        ).blob
        zstd_blob = store.put_bytes(
            data,
            storage_encoding=StorageEncoding.ZSTD,
            source_media_type=MEDIA,
        ).blob
        assert none_blob.blob_sha256 == zstd_blob.blob_sha256
        repo.append_metadata(none_blob)
        repo.append_metadata(zstd_blob)
        metas = repo.get_blob_metadata(none_blob.blob_sha256)
        assert [m.storage_encoding for m in metas] == [
            StorageEncoding.NONE,
            StorageEncoding.ZSTD,
        ]
        assert (
            repo.get_blob_metadata_exact(
                none_blob.blob_sha256, StorageEncoding.ZSTD
            ).stored_byte_length
            == zstd_blob.stored_byte_length
        )


class TestAcquisitionRepository:
    def _repo(
        self, tmp_path: Path
    ) -> tuple[LocalBlobStore, BlobMetadataRepository, AcquisitionRepository]:
        store = make_store(tmp_path)
        blob_repo = BlobMetadataRepository(tmp_path, blob_store=store, clock=lambda: FIXED)
        acq_repo = AcquisitionRepository(
            tmp_path,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            clock=lambda: FIXED,
        )
        return store, blob_repo, acq_repo

    def test_commit_with_blob_requires_metadata_and_physical(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b'{"ok": true}')
        # metadata missing -> dangling ref
        with pytest.raises(DanglingBlobReference):
            acq_repo.append_acquisition(
                _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-a")
            )
        blob_repo.append_metadata(blob)
        record, receipt = acq_repo.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-a")
        )
        assert record.acquisition_id == "acq-a"
        assert receipt.fragment_sha256
        loaded = acq_repo.get_acquisition("acq-a")
        assert loaded.model_dump() == record.model_dump()

    def test_acquisition_idempotent_exact(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b"dup")
        blob_repo.append_metadata(blob)
        rec = _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-x")
        _, r1 = acq_repo.append_acquisition(rec)
        _, r2 = acq_repo.append_acquisition(rec)
        assert r1.fragment_sha256 == r2.fragment_sha256

    def test_acquisition_id_conflict_never_mutates(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b"conflict")
        blob_repo.append_metadata(blob)
        acq_repo.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-1", venue="V1")
        )
        with pytest.raises(AcquisitionIdentityConflict):
            acq_repo.append_acquisition(
                _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-1", venue="V2")
            )
        assert acq_repo.get_acquisition("acq-1").venue == "V1"

    def test_successful_without_blob_and_without_failure_rejected(
        self, tmp_path: Path
    ) -> None:
        _, _, acq_repo = self._repo(tmp_path)
        with pytest.raises(CatalogIntegrityError):
            acq_repo.append_acquisition(
                _record(acquisition_id="acq-nob", http_status_or_source_status="200")
            )

    def test_blobless_failure_explainable_via_failure_ref(self, tmp_path: Path) -> None:
        _, _, acq_repo = self._repo(tmp_path)
        rec, _ = acq_repo.append_acquisition(
            _record(
                acquisition_id="acq-fail",
                blob_sha256=None,
                http_status_or_source_status="503",
                failure_ref="gate:rate_limited",
                quality_flags=[QualityFlagAcquisition.RATE_LIMITED],
            )
        )
        assert acq_repo.get_acquisition("acq-fail").failure_ref == "gate:rate_limited"

    def test_blobless_explicit_status_explainable(self, tmp_path: Path) -> None:
        _, _, acq_repo = self._repo(tmp_path)
        acq_repo.append_acquisition(
            _record(
                acquisition_id="acq-503",
                blob_sha256=None,
                http_status_or_source_status="503",
                failure_ref="provider:gate_geo",
            )
        )
        assert acq_repo.get_acquisition("acq-503").http_status_or_source_status == "503"

    def test_repeated_acquisitions_same_blob_all_visible(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b"same-bytes")
        blob_repo.append_metadata(blob)
        acq_repo.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-A")
        )
        acq_repo.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-B")
        )
        # acquisition history is NOT deduped; only bytes are (I04 §29)
        assert acq_repo.get_acquisition("acq-A").blob_sha256 == blob.blob_sha256
        assert acq_repo.get_acquisition("acq-B").blob_sha256 == blob.blob_sha256
        fragments = list(
            (tmp_path / "catalogs" / "manifests" / "acquisitions").glob("*.parquet")
        )
        assert len(fragments) == 2

    def test_empty_body_is_valid_blob_evidence(self, tmp_path: Path) -> None:
        """b'' is valid zero-byte source evidence, NOT 'no blob' (I04 §14)."""
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b"")
        assert blob.byte_length == 0
        blob_repo.append_metadata(blob)
        rec, _ = acq_repo.append_acquisition(
            _record(
                blob_sha256=blob.blob_sha256,
                acquisition_id="acq-empty",
                quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            )
        )
        assert rec.blob_sha256 == blob.blob_sha256

    def test_get_acquisition_not_found(self, tmp_path: Path) -> None:
        _, _, acq_repo = self._repo(tmp_path)
        with pytest.raises(AcquisitionNotFound):
            acq_repo.get_acquisition("does-not-exist")

    def test_same_request_different_bytes_both_stored(self, tmp_path: Path) -> None:
        """request_fingerprint F with blob X then blob Y: both persist (I04 §55)."""
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob_x = put_data(store, b"bytes-X")
        blob_y = put_data(store, b"bytes-Y")
        blob_repo.append_metadata(blob_x)
        blob_repo.append_metadata(blob_y)
        acq_repo.append_acquisition(
            _record(
                acquisition_id="acq-FX",
                request_fingerprint="F",
                blob_sha256=blob_x.blob_sha256,
            )
        )
        acq_repo.append_acquisition(
            _record(
                acquisition_id="acq-FY",
                request_fingerprint="F",
                blob_sha256=blob_y.blob_sha256,
            )
        )
        assert acq_repo.get_acquisition("acq-FX").blob_sha256 == blob_x.blob_sha256
        assert acq_repo.get_acquisition("acq-FY").blob_sha256 == blob_y.blob_sha256
        # never collapsed, never labeled canonical (I06 owns revisions)

    def test_lossless_round_trip_all_handoff_fields(self, tmp_path: Path) -> None:
        """I04 §59: model -> row -> fragment -> model preserves semantic equality."""
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b'{"n": 1}')
        blob_repo.append_metadata(blob)
        rec = _record(
            acquisition_id="acq-rt",
            blob_sha256=blob.blob_sha256,
            actual_start=datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC),
            actual_end=datetime(2026, 8, 31, 11, 0, 0, tzinfo=UTC),
            provider_checksum_algorithm="MD5",
            provider_checksum_value="0" * 32,
            provider_checksum_verified=True,
            resume_token_before=ResumeToken(
                mode="TIME_RANGE",
                provider_cursor="since=1234",
                last_timestamp=datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC),
            ),
            resume_token_after=None,
            quality_flags=[
                QualityFlagAcquisition.PARTIAL_INTERVAL,
                QualityFlagAcquisition.SCHEMA_ADDITIVE,
            ],
        )
        acq_repo.append_acquisition(rec)
        loaded = acq_repo.get_acquisition("acq-rt")
        assert loaded.model_dump() == rec.model_dump()
        # native symbol exact case/punctuation survives
        assert loaded.native_instrument == "PI_XBTUSD"
        # nested objects survive
        assert loaded.evidence_ref is not None
        assert loaded.evidence_ref.evidence_id == "ev-1"
        assert loaded.resume_token_before is not None
        assert loaded.resume_token_before.provider_cursor == "since=1234"
        assert loaded.provider_checksum_verified is True

    def test_fragment_holds_only_language_neutral_values(self, tmp_path: Path) -> None:
        """No Python repr/pickle artifacts in the durable row (I04 §60)."""
        store, blob_repo, acq_repo = self._repo(tmp_path)
        blob = put_data(store, b"neutral")
        blob_repo.append_metadata(blob)
        acq_repo.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-neut")
        )
        path = (
            tmp_path / "catalogs" / "manifests" / "acquisitions"
            / (AcquisitionRepository._fragment_name("acq-neut"))
        )
        table = pq.read_table(str(path))
        row = table.to_pylist()[0]
        for key, value in row.items():
            if isinstance(value, list):
                assert all(isinstance(v, str) for v in value)
            else:
                assert value is None or isinstance(
                    value, (str, int, bool, datetime)
                )
        raw = path.read_bytes()
        assert b"object at 0x" not in raw
        assert b"<enum " not in raw


class TestLocalEvidenceCatalogFacade:
    def test_facade_wires_three_repositories(self, tmp_path: Path) -> None:
        store = make_store(tmp_path)
        catalog = LocalEvidenceCatalog(
            tmp_path, blob_store=store, clock=lambda: FIXED
        )
        blob = put_data(store, b"facade")
        catalog.blob_metadata.append_metadata(blob)
        catalog.acquisitions.append_acquisition(
            _record(blob_sha256=blob.blob_sha256, acquisition_id="acq-f")
        )
        assert catalog.blob_metadata.get_blob_metadata(blob.blob_sha256)
        assert catalog.acquisitions.get_acquisition("acq-f").acquisition_id == "acq-f"

    def test_missing_root_created_durably(self, tmp_path: Path) -> None:
        """ACTUAL ROOT POLICY: missing root may be created durably (I04 §3)."""
        nested = tmp_path / "t0" / "root"
        assert not nested.exists()
        # store and catalog share the SAME configured root; the blob store's
        # first put durably creates the missing namespace chain
        store = make_store(nested)
        repo = BlobMetadataRepository(nested, blob_store=store, clock=lambda: FIXED)
        blob = put_data(store, b"root-policy")
        repo.append_metadata(blob)
        assert (nested / "catalogs" / "manifests" / "blobs").is_dir()

    def test_root_as_file_fails_closed(self, tmp_path: Path) -> None:
        store = make_store(tmp_path)
        not_a_dir = tmp_path / "file-root"
        not_a_dir.write_text("nope", encoding="utf-8")
        from crypto_sensor_fabric.storage import InvalidStorageRoot

        with pytest.raises(InvalidStorageRoot):
            BlobMetadataRepository(
                not_a_dir, blob_store=store, clock=lambda: FIXED
            )

    def test_blob_storage_key_fragment_name(self) -> None:
        key = BlobStorageKey("a" * 64, StorageEncoding.ZSTD)
        assert key.fragment_name == f"{'a' * 64}.ZSTD.parquet"

    def test_arrow_schemas_are_stable_explicit(self) -> None:
        # fields/types/nullability fully declared; no inference anywhere
        for schema in (BLOB_SCHEMA, ACQUISITION_SCHEMA):
            for field in schema:
                assert isinstance(field, pa.Field)
                assert field.name
        assert BLOB_SCHEMA.field("blob_sha256").nullable is False
        assert ACQUISITION_SCHEMA.field("actual_start").nullable is True
        assert ACQUISITION_SCHEMA.field("quality_flags").type == pa.list_(pa.string())
        assert str(BLOB_SCHEMA.field("created_at").type).startswith("timestamp")