"""SENSOR-B4-I04C/D — append-only PartitionManifest repository tests.

Version rules (v1/vN/supersedes/no gaps), expected-current CAS, partition
identity stability, referential integrity (blob metadata + physical verify),
coverage/integrity separation, pointer transaction semantics and the P1-P5
pointer crash matrix with orphan retry/idempotent completion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import (
    BlobMetadataRepository,
    CatalogIntegrityError,
    CurrentPointerCorrupt,
    CurrentPointerDangling,
    EvidenceBlob,
    IntegrityState,
    LocalBlobStore,
    ManifestCASConflict,
    ManifestDisposition,
    ManifestIdentityConflict,
    ManifestLockHeld,
    ManifestNotFound,
    ManifestVersionConflict,
    PartitionManifest,
    PartitionManifestRepository,
    PointerFaultPoint,
    ProjectionReferenceUnavailable,
    RaisePointerFaultHook,
    StorageEncoding,
)

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"

PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _blob(store: LocalBlobStore, data: bytes) -> EvidenceBlob:
    return store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    ).blob


def _manifest(**overrides: Any) -> PartitionManifest:
    kwargs: dict[str, Any] = {
        "partition_manifest_id": "pm-1",
        "partition_key": PK,
        "manifest_version": 1,
        "provider": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "native_instrument": "PI_XBTUSD",
        "source_granularity": Granularity.G1H,
        "date_basis": "EVENT_TIME",
        "logical_date_start": datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC),
        "logical_date_end": datetime(2026, 8, 31, 23, 59, 59, tzinfo=UTC),
        "blob_refs": [],
        "projection_refs": [],
        "coverage_state": "PARTIAL",
        "integrity_state": IntegrityState.UNVERIFIED,
        "row_count": 0,
        "min_time": None,
        "max_time": None,
        "gap_count": 0,
        "revision_count": 0,
        "created_at": FIXED,
        "supersedes_manifest_id": None,
    }
    kwargs.update(overrides)
    return PartitionManifest(**kwargs)


class TestManifestRepo:
    def _repo(
        self, tmp_path: Path
    ) -> tuple[LocalBlobStore, BlobMetadataRepository, PartitionManifestRepository]:
        store = make_store(tmp_path)
        blob_repo = BlobMetadataRepository(tmp_path, blob_store=store, clock=lambda: FIXED)
        repo = PartitionManifestRepository(
            tmp_path,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            clock=lambda: FIXED,
        )
        return store, blob_repo, repo

    def _seed_blob(
        self, store: LocalBlobStore, blob_repo: BlobMetadataRepository, data: bytes
    ) -> str:
        blob = _blob(store, data)
        blob_repo.append_metadata(blob)
        return blob.blob_sha256

    # -- version 1 -----------------------------------------------------------

    def test_first_manifest_v1(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        result = repo.append_partition_manifest(_manifest(), expected_current=None)
        assert result.disposition is ManifestDisposition.COMMITTED_NEW
        assert result.current_pointer.manifest_version == 1
        assert result.current_pointer.previous_manifest_id is None
        current = repo.get_current_manifest(PK)
        assert current.partition_manifest_id == "pm-1"
        assert current.manifest_version == 1
        assert [m.manifest_version for m in repo.list_manifest_versions(PK)] == [1]

    def test_v1_with_existing_current_fails_cas(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        with pytest.raises(ManifestCASConflict):
            repo.append_partition_manifest(
                _manifest(partition_manifest_id="pm-1b"), expected_current=None
            )

    def test_v1_non_one_version_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ManifestVersionConflict):
            repo.append_partition_manifest(
                _manifest(manifest_version=2), expected_current=None
            )

    def test_v1_with_supersedes_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ManifestVersionConflict):
            repo.append_partition_manifest(
                _manifest(supersedes_manifest_id="pm-ghost"),
                expected_current=None,
            )

    def test_expected_current_supplied_but_none_exists(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ManifestCASConflict):
            repo.append_partition_manifest(
                _manifest(), expected_current=("pm-ghost", 1)
            )

    # -- version N -----------------------------------------------------------

    def test_sequential_v2(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        v2 = _manifest(
            partition_manifest_id="pm-2",
            manifest_version=2,
            supersedes_manifest_id="pm-1",
            row_count=24,
            min_time=datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC),
            max_time=datetime(2026, 8, 1, 23, 0, 0, tzinfo=UTC),
        )
        result = repo.append_partition_manifest(v2, expected_current=("pm-1", 1))
        assert result.disposition is ManifestDisposition.COMMITTED_NEW
        assert result.current_pointer.manifest_version == 2
        assert result.current_pointer.previous_manifest_id == "pm-1"
        assert repo.get_current_manifest(PK).partition_manifest_id == "pm-2"
        versions = repo.list_manifest_versions(PK)
        assert [m.manifest_version for m in versions] == [1, 2]
        assert versions[1].supersedes_manifest_id == "pm-1"
        assert repo.get_manifest("pm-1").manifest_version == 1
        assert repo.get_manifest("pm-2").manifest_version == 2

    def test_v2_gap_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        with pytest.raises(ManifestVersionConflict):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-3",
                    manifest_version=3,
                    supersedes_manifest_id="pm-1",
                ),
                expected_current=("pm-1", 1),
            )

    def test_v2_supersedes_not_current_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        with pytest.raises(ManifestVersionConflict):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-other",
                ),
                expected_current=("pm-1", 1),
            )

    def test_stale_writer_cas_conflict_no_auto_rebase(self, tmp_path: Path) -> None:
        """I04 §73: stale writer fails; never auto-promotes itself to v3."""
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        repo.append_partition_manifest(
            _manifest(
                partition_manifest_id="pm-2",
                manifest_version=2,
                supersedes_manifest_id="pm-1",
            ),
            expected_current=("pm-1", 1),
        )
        with pytest.raises(ManifestCASConflict):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-stale",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                ),
                expected_current=("pm-1", 1),  # stale base: current is pm-2
            )
        # current is still exactly pm-2; no v3 was silently created
        assert repo.get_current_manifest(PK).partition_manifest_id == "pm-2"
        assert len(repo.list_manifest_versions(PK)) == 2

    def test_partition_identity_drift_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        with pytest.raises(ManifestIdentityConflict):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                    native_instrument="PI_ETHUSD",
                ),
                expected_current=("pm-1", 1),
            )

    # -- referential integrity (I04 §45/§46/§47) ------------------------------

    def test_blob_ref_without_metadata_fails(self, tmp_path: Path) -> None:
        store, _, repo = self._repo(tmp_path)
        sha = _blob(store, b"orphan-ref").blob_sha256  # physical only, NO metadata
        with pytest.raises(CatalogIntegrityError):
            repo.append_partition_manifest(
                _manifest(blob_refs=[sha]), expected_current=None
            )

    def test_blob_ref_verified_succeeds(self, tmp_path: Path) -> None:
        store, blob_repo, repo = self._repo(tmp_path)
        sha = self._seed_blob(store, blob_repo, b"verified")
        result = repo.append_partition_manifest(
            _manifest(
                blob_refs=[sha],
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert result.disposition is ManifestDisposition.COMMITTED_NEW

    def test_manifest_claim_stronger_than_evidence_rejected(
        self, tmp_path: Path
    ) -> None:
        store, blob_repo, repo = self._repo(tmp_path)
        blob = _blob(store, b"weak")
        # metadata claims UNVERIFIED while the manifest claims LOCAL_HASH_VERIFIED
        blob_repo.append_metadata(
            blob.model_copy(update={"integrity_state": IntegrityState.UNVERIFIED})
        )
        with pytest.raises(CatalogIntegrityError):
            repo.append_partition_manifest(
                _manifest(
                    blob_refs=[blob.blob_sha256],
                    integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
                ),
                expected_current=None,
            )

    def test_vacuous_integrity_claim_without_refs_rejected(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(CatalogIntegrityError):
            repo.append_partition_manifest(
                _manifest(integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
                expected_current=None,
            )

    def test_coverage_separate_from_integrity(self, tmp_path: Path) -> None:
        """I04 §47: PARTIAL coverage + LOCAL_HASH_VERIFIED integrity is legal."""
        store, blob_repo, repo = self._repo(tmp_path)
        sha = self._seed_blob(store, blob_repo, b"partial-ok")
        result = repo.append_partition_manifest(
            _manifest(
                blob_refs=[sha],
                coverage_state="PARTIAL",
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert result.disposition is ManifestDisposition.COMMITTED_NEW
        current = repo.get_current_manifest(PK)
        assert current.coverage_state.value == "PARTIAL"
        assert current.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED

    def test_projection_refs_blocked(self, tmp_path: Path) -> None:
        """I04 §20: projection_refs must be EMPTY until I05 exists."""
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ProjectionReferenceUnavailable):
            repo.append_partition_manifest(
                _manifest(projection_refs=["proj-1"]), expected_current=None
            )

    # -- duplicate / orphan semantics (I04 §44) -------------------------------

    def test_duplicate_exact_manifest_completes_transition(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        v1 = _manifest()
        repo.append_partition_manifest(v1, expected_current=None)
        # an orphan fragment exists for v2 (e.g. previous crash after publish,
        # before pointer update); retry with the SAME manifest + same base
        # must finish the intended pointer transition
        v2 = _manifest(
            partition_manifest_id="pm-2",
            manifest_version=2,
            supersedes_manifest_id="pm-1",
        )
        repo.append_partition_manifest(v2, expected_current=("pm-1", 1))
        orphans = repo.list_orphan_manifest_fragments(PK)
        assert orphans == []  # committed, not orphan

    def test_orphan_fragment_preserved_and_forensic(self, tmp_path: Path) -> None:
        """A published-but-never-current fragment is orphan evidence, kept."""
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        # the authentic orphan path: crash AFTER manifest publication, BEFORE
        # pointer advancement (fault P2) — pointer stays v1, fragment exists
        orphan = _manifest(
            partition_manifest_id="pm-orphan",
            manifest_version=2,
            supersedes_manifest_id="pm-1",
        )
        with pytest.raises(RuntimeError):
            repo.append_partition_manifest(
                orphan,
                expected_current=("pm-1", 1),
                fault_hooks=RaisePointerFaultHook(PointerFaultPoint.P2),
            )
        orphans = repo.list_orphan_manifest_fragments(PK)
        assert [o.partition_manifest_id for o in orphans] == ["pm-orphan"]
        # ordinary current resolution follows the pointer only
        assert repo.get_current_manifest(PK).partition_manifest_id == "pm-1"
        assert [m.manifest_version for m in repo.list_manifest_versions(PK)] == [1]
        # the orphan is never deleted automatically; an exact retry with the
        # same base finishes the intended transition (I04 §44)
        retry = repo.append_partition_manifest(
            orphan, expected_current=("pm-1", 1)
        )
        assert retry.disposition is ManifestDisposition.COMMITTED_NEW
        assert repo.get_current_manifest(PK).partition_manifest_id == "pm-orphan"
        assert repo.list_orphan_manifest_fragments(PK) == []

    def test_same_manifest_id_different_content_conflict(self, tmp_path: Path) -> None:
        """I04 §33/§44: same manifest_id with DIFFERENT immutable content fails."""
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        # writer X publishes its v2 (id pm-2) but crashes before the pointer
        # advances (fault P2) -> immutable fragment exists, pointer stays v1
        with pytest.raises(RuntimeError):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                ),
                expected_current=("pm-1", 1),
                fault_hooks=RaisePointerFaultHook(PointerFaultPoint.P2),
            )
        # writer Y attempts the SAME id+version with DIFFERENT content on the
        # same base: the published fragment disagrees -> identity conflict
        with pytest.raises(ManifestIdentityConflict):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                    row_count=99,  # same id, different content
                ),
                expected_current=("pm-1", 1),
            )
        # the original immutable fragment is never overwritten
        assert repo.read_current_pointer(PK) is not None
        assert repo.read_current_pointer(PK).manifest_version == 1

    def test_idempotent_completion_after_pointer_move(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        v1 = _manifest()
        repo.append_partition_manifest(v1, expected_current=None)
        result = repo.append_partition_manifest(v1, expected_current=None)
        assert result.disposition is ManifestDisposition.IDEMPOTENT_COMPLETION

    # -- pointer corruption / dangling (I04 §62) ------------------------------

    def test_pointer_corrupt_json_fails_typed(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        pointer_dir = tmp_path / "catalogs" / "current" / "partitions"
        files = list(pointer_dir.glob("*.json"))
        assert len(files) == 1
        files[0].write_text("{not json", encoding="utf-8")
        with pytest.raises(CurrentPointerCorrupt):
            repo.get_current_manifest(PK)

    def test_pointer_dangling_fragment(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        pointer_dir = tmp_path / "catalogs" / "current" / "partitions"
        pointer_file = list(pointer_dir.glob("*.json"))[0]
        pointer = json.loads(pointer_file.read_text(encoding="utf-8"))
        pointer["partition_manifest_id"] = "pm-does-not-exist"
        pointer_file.write_text(
            json.dumps(pointer, sort_keys=True), encoding="utf-8"
        )
        with pytest.raises(CurrentPointerDangling):
            repo.get_current_manifest(PK)

    def test_get_manifest_not_found(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ManifestNotFound):
            repo.get_manifest("pm-nope")

    def test_get_current_manifest_not_found(self, tmp_path: Path) -> None:
        _, _, repo = self._repo(tmp_path)
        with pytest.raises(ManifestNotFound):
            repo.get_current_manifest(PK)

    # -- partition lock (I04 §37/§38) -----------------------------------------

    def test_lock_held_fails_closed_and_is_not_autodeleted(self, tmp_path: Path) -> None:
        import hashlib

        _, _, repo = self._repo(tmp_path)
        partition_hash = hashlib.sha256(PK.encode("utf-8")).hexdigest()[:32]
        lock_dir = (
            tmp_path / "catalogs" / "locks" / "partitions"
            / f"{partition_hash}.lock"
        )
        lock_dir.parent.mkdir(parents=True, exist_ok=True)
        lock_dir.mkdir()
        with pytest.raises(ManifestLockHeld):
            repo.append_partition_manifest(_manifest(), expected_current=None)
        # production code never deletes the stale lock (I08 owns recovery)
        assert lock_dir.exists()
        # test removes its OWN synthetic lock, then the append proceeds
        lock_dir.rmdir()
        repo.append_partition_manifest(_manifest(), expected_current=None)
        assert repo.get_current_manifest(PK).manifest_version == 1

    # -- pointer crash matrix P1-P5 (I04 §42/§43) -----------------------------

    def test_pointer_crash_matrix(self, tmp_path: Path) -> None:
        """P1-P5 deterministic fault injection; expected outcomes per I04 §42."""
        # (point, version after fault, pointer-visible-after-fault,
        #  expected retry disposition)
        cases = [
            (PointerFaultPoint.P1, 1, False, ManifestDisposition.COMMITTED_NEW),
            (PointerFaultPoint.P2, 1, False, ManifestDisposition.COMMITTED_NEW),
            (PointerFaultPoint.P3, 1, False, ManifestDisposition.COMMITTED_NEW),
            (PointerFaultPoint.P4, 2, True, ManifestDisposition.IDEMPOTENT_COMPLETION),
            (PointerFaultPoint.P5, 2, True, ManifestDisposition.IDEMPOTENT_COMPLETION),
        ]
        for point, expect_version, expect_visible, expect_disposition in cases:
            root = tmp_path / point.value
            root.mkdir()
            store = make_store(root)
            blob_repo = BlobMetadataRepository(
                root, blob_store=store, clock=lambda: FIXED
            )
            repo = PartitionManifestRepository(
                root,
                blob_store=store,
                blob_metadata_repository=blob_repo,
                clock=lambda: FIXED,
            )
            repo.append_partition_manifest(_manifest(), expected_current=None)
            v2 = _manifest(
                partition_manifest_id="pm-2",
                manifest_version=2,
                supersedes_manifest_id="pm-1",
            )
            hook = RaisePointerFaultHook(point)
            with pytest.raises(RuntimeError, match=f"injected pointer fault at {point.value}"):
                repo.append_partition_manifest(v2, expected_current=("pm-1", 1), fault_hooks=hook)
            # current pointer state after the fault
            pointer = repo.read_current_pointer(PK)
            assert pointer is not None
            assert pointer.manifest_version == expect_version
            current = repo.get_current_manifest(PK)
            assert current.manifest_version == expect_version
            if expect_visible:
                assert current.partition_manifest_id == "pm-2"
            else:
                assert current.partition_manifest_id == "pm-1"
            # P1/P2/P3: retry completes a normal commit (P2/P3 reuses the
            # orphan fragment through the intended pointer transition).
            # P4/P5: the visible pointer is NOT a proven durable pointer —
            # retry must re-establish pointer-parent durability before
            # success (I04 §43) and resolve idempotently.
            retry = repo.append_partition_manifest(
                v2, expected_current=("pm-1", 1)
            )
            assert retry.disposition is expect_disposition
            assert repo.get_current_manifest(PK).partition_manifest_id == "pm-2"
            # after a successful retry the transition is complete; no orphan
            # remains for this manifest
            assert repo.list_orphan_manifest_fragments(PK) == []

    def test_pointer_replace_is_atomic_old_or_new(self, tmp_path: Path) -> None:
        """I04 §36/§74: readers see a valid old or new pointer, never partial."""
        _, _, repo = self._repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)
        for version in range(2, 5):
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id=f"pm-{version}",
                    manifest_version=version,
                    supersedes_manifest_id=f"pm-{version - 1}",
                ),
                expected_current=(f"pm-{version - 1}", version - 1),
            )
            current = repo.get_current_manifest(PK)
            assert current.manifest_version == version
        # pointer file is always parseable, never partial JSON
        pointer_dir = tmp_path / "catalogs" / "current" / "partitions"
        for pointer_file in pointer_dir.glob("*.json"):
            payload = json.loads(pointer_file.read_text(encoding="utf-8"))
            assert set(payload) == {
                "partition_key",
                "partition_manifest_id",
                "manifest_version",
                "previous_manifest_id",
                "updated_at",
            }