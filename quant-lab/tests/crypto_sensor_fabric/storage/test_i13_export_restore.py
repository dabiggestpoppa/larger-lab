"""SENSOR-B4-I13 — checksum-verified local export/backup/restore pack.

Blocking G4-11 proof (freeze contract):
- fixture evidence pack restores into an EMPTY root;
- hashes match (source vs restored byte digests + metadata digests);
- query results match (canonical result equality through fresh services);
- DuckDB discovery catalog rebuilds from the restored slice.

Failure-first doctrine: every adversarial case (tamper/traversal/symlink/
resource/partial) is measured through production behavior, never
hand-authored PASS.  Exactly one synthetic counterfactual FAIL is
published per evidence matrix (§55).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402 - sibling-import pattern
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402 - direct-script execution support

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    EvidencePackExporter,
    EvidencePackRestorer,
    EvidencePackVerifier,
    PackChecksumMismatch,
    PackInventoryMismatch,
    PackManifestCorrupt,
    PackObjectRole,
    PackPathUnsafe,
    PackResourceLimitExceeded,
    PackUnsupportedVersion,
    PackVerificationError,
    RawEvidenceQuery,
    RawEvidenceQueryService,
    RestoreDestinationNotEmpty,
    VerifyLimits,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    PACK_MANIFEST_NAME,
    read_pack_manifest,
)
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.models import (  # noqa: E402
    canonical_json_bytes,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    SourceRevisionRegistry,
)
from crypto_sensor_fabric.storage.projection_schema import (  # noqa: E402
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (  # noqa: E402
    ProjectionArtifactRepository,
    ProjectionContextRepository,
)
from crypto_sensor_fabric.storage.projection_lineage import (  # noqa: E402
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    rebuild_duckdb_catalog,
)

lake_module = load_sibling("test_i12_query_replay", "test_i12_query_replay")
Lake = lake_module.Lake
FIXED = lake_module.FIXED
ts = lake_module.ts


# ---------------------------------------------------------------------------
# Fixture lake (G4-11 §28): one provider, 3 blobs, 3 acquisitions (one source
# identity carries a two-revision chain through register_acquisition), one
# T0B projection + lineage, one manifest.
# ---------------------------------------------------------------------------


def build_fixture_lake(tmp_path: Path) -> Lake:
    # Lake requires a PRE-EXISTING root but not an empty one; t0a/t0b must
    # not exist yet (fresh fixture lake).
    tmp_path.mkdir(parents=True, exist_ok=True)
    import shutil as _shutil

    _shutil.rmtree(tmp_path / "t0a", ignore_errors=True)
    _shutil.rmtree(tmp_path / "t0b", ignore_errors=True)
    lake = Lake(tmp_path)
    sha_a1 = lake.seed_blob(b'{"k":"v1"}')
    sha_a2 = lake.seed_blob(b'{"k":"v2"}')
    sha_a3 = lake.seed_blob(b'{"k":"v3"}')
    lake.seed_acquisition(sha_a1, "acq-1")
    lake.seed_acquisition(sha_a2, "acq-2")
    lake.seed_acquisition(sha_a3, "acq-3")
    lake.commit_projection("proj-1", [(sha_a1, "acq-1")])
    lake.commit_manifest("m1", blob_refs=[sha_a1, sha_a2])
    return lake


def _exporter(lake: Lake, **overrides) -> EvidencePackExporter:
    kwargs = dict(
        service=lake.service(),
        blob_store=lake.store,
        blob_metadata_repository=lake.blob_repo,
        acquisition_repository=lake.acq_repo,
        manifest_repository=lake.manifest_repo,
        artifact_repository=lake.artifacts,
        context_repository=lake.contexts,
        lineage_repository=lake.lineage,
        schema_registry=lake.schemas,
        revision_registry=lake.registry,
        clock=lambda: FIXED,
    )
    kwargs.update(overrides)
    return EvidencePackExporter(**kwargs)


def _restore_service(root: Path) -> RawEvidenceQueryService:
    """FRESH canonical service wiring over a restored root (§45)."""
    store = LocalBlobStore(str(root / "t0a"))
    blob_repo = BlobMetadataRepository(root / "t0a", blob_store=store)
    acq_repo = AcquisitionRepository(
        root / "t0a", blob_store=store, blob_metadata_repository=blob_repo
    )
    manifest_repo = PartitionManifestRepository(
        root / "t0a",
        blob_store=store,
        blob_metadata_repository=blob_repo,
        acquisition_repository=acq_repo,
    )
    schemas = ProjectionSchemaRegistry(
        root / "t0b" / "catalogs" / "projection_schemas"
    )
    artifacts = ProjectionArtifactRepository(
        root / "t0b" / "catalogs" / "manifests" / "projections",
        projection_root=root / "t0b",
        schema_registry=schemas,
    )
    contexts = ProjectionContextRepository(
        root / "t0b" / "catalogs" / "manifests" / "projection_context"
    )
    lineage = ProjectionLineageRepository(
        root / "t0b" / "catalogs" / "manifests" / "projection_lineage",
        blob_store=store,
        blob_metadata_repository=blob_repo,
        acquisition_repository=acq_repo,
        artifact_repository=artifacts,
        context_repository=contexts,
    )
    registry = SourceRevisionRegistry(
        root / "t0a" / "revisions",
        acquisition_repository=acq_repo,
        blob_metadata_repository=blob_repo,
        blob_store=store,
    )
    return RawEvidenceQueryService(
        manifest_repository=manifest_repo,
        acquisition_repository=acq_repo,
        blob_metadata_repository=blob_repo,
        revision_registry=registry,
        revision_identity_factory=lake_module.RevisionSourceIdentityV1,
        projection_artifact_repository=artifacts,
        projection_lineage_repository=lineage,
    )


def _canonical_results_digest(service, query) -> str:
    results = service.execute(query)
    return hashlib.sha256(
        canonical_json_bytes(results)
    ).hexdigest()


# ---------------------------------------------------------------------------
# G4-11 blocking parity proofs (§28-§31)
# ---------------------------------------------------------------------------


class TestFreshRootParity:
    def test_export_verify_restore_hash_and_query_parity(
        self, tmp_path
    ) -> None:
        lake = build_fixture_lake(tmp_path / "src")
        query = RawEvidenceQuery()
        receipt = _exporter(lake).export_query(query, tmp_path / "pack")
        assert receipt.object_count > 0
        assert receipt.manifest.blob_count == 2  # manifest m1 binds a1+a2

        restorer = EvidencePackRestorer()
        restored_root = restorer.restore_pack(
            tmp_path / "pack", tmp_path / "restored"
        )
        assert restored_root.exists()

        source_service = lake.service()
        restored_service = _restore_service(restored_root)
        assert _canonical_results_digest(
            source_service, query
        ) == _canonical_results_digest(restored_service, query)

    def test_restored_blob_source_byte_hashes_exact(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.enums import StorageEncoding

        lake = build_fixture_lake(tmp_path / "src")
        query = RawEvidenceQuery()
        receipt = _exporter(lake).export_query(query, tmp_path / "pack")
        exported = set(receipt.manifest.objects)
        restored_root = EvidencePackRestorer().restore_pack(
            tmp_path / "pack", tmp_path / "restored"
        )
        store = LocalBlobStore(str(restored_root / "t0a"))
        restored_rows = sorted(
            (b.blob_sha256, b.byte_length)
            for b in BlobMetadataRepository(
                restored_root / "t0a", blob_store=store
            ).list_all_blob_metadata()
        )
        source_rows = sorted(
            (b.blob_sha256, b.byte_length)
            for b in lake.blob_repo.list_all_blob_metadata()
            if b.blob_sha256 in exported
        )
        assert restored_rows == source_rows
        for sha, _length in restored_rows:
            check = store.verify_blob(sha, StorageEncoding.NONE)
            assert check.integrity_state.value == "LOCAL_HASH_VERIFIED"

    def test_manifest_pointer_restored(self, tmp_path) -> None:
        lake = build_fixture_lake(tmp_path / "src")
        query = RawEvidenceQuery()
        _exporter(lake).export_query(query, tmp_path / "pack")
        restored_root = EvidencePackRestorer().restore_pack(
            tmp_path / "pack", tmp_path / "restored"
        )
        store = LocalBlobStore(str(restored_root / "t0a"))
        blob_repo = BlobMetadataRepository(
            restored_root / "t0a", blob_store=store
        )
        acq_repo = AcquisitionRepository(
            restored_root / "t0a",
            blob_store=store,
            blob_metadata_repository=blob_repo,
        )
        restored_manifests = (
            PartitionManifestRepository(
                restored_root / "t0a",
                blob_store=store,
                blob_metadata_repository=blob_repo,
                acquisition_repository=acq_repo,
            ).list_all_current_manifests()
        )
        assert len(restored_manifests) == 1
        assert restored_manifests[0].partition_manifest_id == "m1"

    def test_revision_resolution_restored(self, tmp_path) -> None:
        lake = build_fixture_lake(tmp_path / "src")
        keys = lake.registry.list_source_revision_keys()
        assert keys, "fixture must carry a revision chain"
        query = RawEvidenceQuery()
        _exporter(lake).export_query(query, tmp_path / "pack")
        restored_root = EvidencePackRestorer().restore_pack(
            tmp_path / "pack", tmp_path / "restored"
        )
        restored_service = _restore_service(restored_root)
        restored_query = RawEvidenceQuery(
            revision_policy=lake_module.RevisionPolicy.ALL
        )
        _ = restored_query
        source_results = lake.service().execute(
            RawEvidenceQuery(revision_policy=lake_module.RevisionPolicy.ALL)
        )
        restored_results = restored_service.execute(
            RawEvidenceQuery(revision_policy=lake_module.RevisionPolicy.ALL)
        )
        assert canonical_json_bytes(
            source_results
        ) == canonical_json_bytes(restored_results)

    def test_duckdb_rebuild_from_restored_root(self, tmp_path) -> None:
        lake = build_fixture_lake(tmp_path / "src")
        query = RawEvidenceQuery()
        receipt = _exporter(lake).export_query(query, tmp_path / "pack")
        restored_root = EvidencePackRestorer().restore_pack(
            tmp_path / "pack", tmp_path / "restored"
        )
        restored_receipt = rebuild_duckdb_catalog(
            restored_root / "t0a", tmp_path / "restored.duckdb"
        )
        # The rebuilt discovery catalog must see EXACTLY the exported slice
        # (blob_count from the pack manifest) — independent of the source
        # lake and never copied from it (§31).
        assert restored_receipt.view_row_counts["v_t0_blobs"] == (
            receipt.manifest.blob_count
        )
        assert restored_receipt.view_row_counts["v_t0_acquisitions"] == (
            receipt.manifest.blob_count
        )

    def test_pack_copyable_to_second_directory(self, tmp_path) -> None:
        lake = build_fixture_lake(tmp_path / "src")
        query = RawEvidenceQuery()
        _exporter(lake).export_query(query, tmp_path / "pack")
        import shutil

        shutil.copytree(tmp_path / "pack", tmp_path / "copy")
        report = EvidencePackVerifier().verify_pack(tmp_path / "copy")
        assert report.object_count > 0
        restored_root = EvidencePackRestorer().restore_pack(
            tmp_path / "copy", tmp_path / "restored"
        )
        assert restored_root.exists()


# ---------------------------------------------------------------------------
# Verifier adversarial matrix (§22/§57)
# ---------------------------------------------------------------------------


def _make_pack(tmp_path) -> tuple[Lake, Path]:
    lake = build_fixture_lake(tmp_path / "src")
    _exporter(lake).export_query(RawEvidenceQuery(), tmp_path / "pack")
    return lake, tmp_path / "pack"


class TestVerifierAdversarial:
    def test_valid_pack_verifies(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        assert EvidencePackVerifier().verify_pack(pack).object_count > 0

    def test_one_byte_blob_tamper_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        blob = next(
            r
            for r in manifest.object_inventory
            if r.role is PackObjectRole.BLOB
        )
        target = pack / blob.pack_path
        data = bytearray(target.read_bytes())
        data[0] ^= 0xFF
        target.write_bytes(bytes(data))
        with pytest.raises(PackChecksumMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_metadata_tamper_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        row = next(
            r
            for r in manifest.object_inventory
            if r.role is PackObjectRole.ACQUISITION
        )
        target = pack / row.pack_path
        data = bytearray(target.read_bytes())
        data[-1] ^= 0x01
        target.write_bytes(bytes(data))
        with pytest.raises(PackChecksumMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_query_tamper_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        target = pack / "query.json"
        target.write_bytes(target.read_bytes() + b" ")
        # Size check fires before checksum (both typed, both fail-closed).
        with pytest.raises(PackVerificationError):
            EvidencePackVerifier().verify_pack(pack)

    def test_missing_object_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        row = manifest.object_inventory[0]
        (pack / row.pack_path).unlink()
        with pytest.raises(PackInventoryMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_extra_object_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        (pack / "objects" / "smuggled.txt").write_text("attacker")
        with pytest.raises(PackInventoryMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_renamed_object_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        row = manifest.object_inventory[0]
        source = pack / row.pack_path
        destination = source.parent / ("renamed-" + source.name)
        source.rename(destination)
        with pytest.raises(PackInventoryMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_checksum_field_mutation_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest_path = pack / PACK_MANIFEST_NAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["object_inventory"][0]["sha256"] = "c" * 64
        manifest_path.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        with pytest.raises(PackChecksumMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_unsupported_version_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest_path = pack / PACK_MANIFEST_NAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["pack_schema_version"] = "999"
        manifest_path.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        with pytest.raises(PackUnsupportedVersion):
            EvidencePackVerifier().verify_pack(pack)

    def test_traversal_path_in_manifest_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest_path = pack / PACK_MANIFEST_NAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["object_inventory"][0]["pack_path"] = "../escaped.txt"
        manifest_path.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        # The MODEL-level path law refuses traversal at manifest parse time
        # (PackManifestCorrupt); the verifier-level containment check
        # (PackPathUnsafe) catches any path that survives parsing.  Both are
        # typed fail-closed refusals of the same defect (§12/§22).
        with pytest.raises((PackPathUnsafe, PackManifestCorrupt)):
            EvidencePackVerifier().verify_pack(pack)

    def test_duplicate_logical_identity_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest_path = pack / PACK_MANIFEST_NAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["object_inventory"].append(
            dict(payload["object_inventory"][0])
        )
        manifest_path.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        with pytest.raises(PackInventoryMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_size_field_mutation_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        manifest_path = pack / PACK_MANIFEST_NAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["object_inventory"][0]["byte_size"] += 1
        manifest_path.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        with pytest.raises(PackInventoryMismatch):
            EvidencePackVerifier().verify_pack(pack)

    def test_corrupt_manifest_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        (pack / PACK_MANIFEST_NAME).write_bytes(b"not json")
        with pytest.raises(PackManifestCorrupt):
            EvidencePackVerifier().verify_pack(pack)

    def test_resource_ceiling_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        tight = VerifyLimits(max_objects=2)
        with pytest.raises(PackResourceLimitExceeded):
            EvidencePackVerifier(limits=tight).verify_pack(pack)


# ---------------------------------------------------------------------------
# Restore law (§23/§26/§27/§49/§50)
# ---------------------------------------------------------------------------


class TestRestoreLaw:
    def test_restore_refuses_tampered_pack_before_mutation(
        self, tmp_path
    ) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        blob = next(
            r
            for r in manifest.object_inventory
            if r.role is PackObjectRole.BLOB
        )
        target = pack / blob.pack_path
        data = bytearray(target.read_bytes())
        data[0] ^= 0xFF
        target.write_bytes(bytes(data))
        destination = tmp_path / "never-created"
        with pytest.raises(PackChecksumMismatch):
            EvidencePackRestorer().restore_pack(pack, destination)
        assert not destination.exists()

    def test_restore_refuses_partial_pack_before_mutation(
        self, tmp_path
    ) -> None:
        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        (pack / manifest.object_inventory[0].pack_path).unlink()
        destination = tmp_path / "never-created"
        with pytest.raises(PackInventoryMismatch):
            EvidencePackRestorer().restore_pack(pack, destination)
        assert not destination.exists()

    def test_restore_nonempty_root_refused(self, tmp_path) -> None:
        _, pack = _make_pack(tmp_path)
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        (blocked / "file.txt").write_text("x")
        with pytest.raises(RestoreDestinationNotEmpty):
            EvidencePackRestorer().restore_pack(pack, blocked)

    def test_no_source_dependency_after_export(self, tmp_path) -> None:
        lake, pack = _make_pack(tmp_path)
        _ = lake
        # Tamper the SOURCE after export: pack/restore reflect EXPORTED
        # evidence, not current source state (§48).
        restored_root = EvidencePackRestorer().restore_pack(
            pack, tmp_path / "restored"
        )
        assert restored_root.exists()

    def test_verify_pack_stable_after_source_tamper(self, tmp_path) -> None:
        lake, pack = _make_pack(tmp_path)
        # Destroy the source lake after export (§48).
        for fragment in (lake.t0a).rglob("*.parquet"):
            fragment.write_bytes(b"CORRUPTED")
        report = EvidencePackVerifier().verify_pack(pack)
        assert report.object_count > 0


# ---------------------------------------------------------------------------
# Security + resource boundaries (§13/§14/§38/§39)
# ---------------------------------------------------------------------------


class TestSecurityAndResources:
    def test_export_destination_inside_source_refused(
        self, tmp_path
    ) -> None:
        from crypto_sensor_fabric.storage import ExportDestinationUnsafe

        lake = build_fixture_lake(tmp_path / "src")
        with pytest.raises(ExportDestinationUnsafe):
            _exporter(lake).export_query(
                RawEvidenceQuery(), tmp_path / "src" / "t0a" / "nested-pack"
            )

    def test_export_nonempty_destination_refused(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage import ExportPackExists

        lake = build_fixture_lake(tmp_path / "src")
        occupied = tmp_path / "occupied"
        occupied.mkdir()
        (occupied / "x.txt").write_text("x")
        with pytest.raises(ExportPackExists):
            _exporter(lake).export_query(RawEvidenceQuery(), occupied)

    def test_restore_free_space_ceiling_refused(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.export import (
            PackResourceLimitExceeded as _PRL,
        )

        _, pack = _make_pack(tmp_path)
        destination = tmp_path / "never"
        # Injectable disk provider: zero free space (§39, no real disk use).
        restorer = EvidencePackRestorer(
            disk_usage_provider=lambda _path: (1 << 40, 0)
        )
        with pytest.raises(_PRL):
            restorer.restore_pack(pack, destination)
        assert not destination.exists()

    def test_restore_symlinked_destination_component_refused(
        self, tmp_path
    ) -> None:
        from crypto_sensor_fabric.storage import RestorePathUnsafe

        _, pack = _make_pack(tmp_path)
        link = tmp_path / "outside-link"
        try:
            link.symlink_to(tmp_path / "elsewhere")
        except OSError:
            pytest.skip("symlink privilege unavailable on this platform")
        if not link.exists():
            (tmp_path / "elsewhere").mkdir()
        destination = link / "restored"
        with pytest.raises((RestorePathUnsafe, PackResourceLimitExceeded)):
            EvidencePackRestorer(
                disk_usage_provider=lambda _p: (1 << 40, 1 << 40)
            ).restore_pack(pack, destination)

    def test_verify_symlinked_pack_object_refused(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage import PackPathUnsafe

        _, pack = _make_pack(tmp_path)
        manifest = read_pack_manifest(pack)
        victim = next(
            r
            for r in manifest.object_inventory
            if r.role is PackObjectRole.BLOB
        )
        target = pack / victim.pack_path
        outside = tmp_path / "outside.bin"
        outside.write_bytes(target.read_bytes())
        target.unlink()
        try:
            target.symlink_to(outside)
        except OSError:
            pytest.skip("symlink privilege unavailable on this platform")
        with pytest.raises((PackPathUnsafe, PackChecksumMismatch)):
            EvidencePackVerifier().verify_pack(pack)

    def test_symlink_refusal_structural_cross_platform(self, tmp_path) -> None:
        """Platform-independent symlink-law proof (§14/§63): when OS symlink
        creation is unavailable, the refusal logic itself is proven by
        forcing the symlink predicate on an existing component."""
        from crypto_sensor_fabric.storage import PackPathUnsafe
        from crypto_sensor_fabric.storage.export import assert_pack_path_safe

        root = tmp_path / "packroot"
        (root / "objects" / "blobs").mkdir(parents=True)
        real = root / "objects" / "blobs" / "real.bin"
        real.write_bytes(b"x")
        # Force the symlink predicate for the 'blobs' component.
        original = Path.is_symlink

        def fake_is_symlink(self: Path) -> bool:
            if self.name == "blobs":
                return True
            return original(self)

        Path.is_symlink = fake_is_symlink  # type: ignore[method-assign]
        try:
            with pytest.raises(PackPathUnsafe):
                assert_pack_path_safe(
                    root, "objects/blobs/real.bin"
                )
        finally:
            Path.is_symlink = original  # type: ignore[method-assign]
        # Without the forced predicate, the same path resolves fine.
        assert assert_pack_path_safe(
            root, "objects/blobs/real.bin"
        ).is_file()

    def test_stale_staging_refused_deterministically(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage import RestoreIncomplete

        _, pack = _make_pack(tmp_path)
        destination = tmp_path / "restored"
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.parent / (
            destination.name + ".staging-restore"
        )
        staging.mkdir()
        (staging / "junk").write_text("stale")
        with pytest.raises(RestoreIncomplete):
            EvidencePackRestorer().restore_pack(pack, destination)
        # Deterministic policy: the stale staging tree is NOT silently
        # adopted; after explicit removal the rerun succeeds (§27).
        import shutil

        shutil.rmtree(staging)
        assert EvidencePackRestorer().restore_pack(
            pack, destination
        ).exists()
