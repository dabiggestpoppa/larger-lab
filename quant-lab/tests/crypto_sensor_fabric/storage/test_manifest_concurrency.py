"""SENSOR-B4-I04D — concurrent manifest versioning (I04 §72-§74).

Partition-scoped filesystem lock + expected-current CAS: exactly ONE of many
same-base writers may advance the current pointer; stale writers fail with
ManifestCASConflict and never auto-promote; readers always observe a valid
old-or-new pointer, never partial state.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import (
    BlobMetadataRepository,
    IntegrityState,
    LocalBlobStore,
    ManifestCASConflict,
    ManifestLockHeld,
    PartitionManifest,
    PartitionManifestRepository,
)

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


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


def _make_repo(
    tmp_path: Path,
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


class TestEightWritersSameBase:
    def test_exactly_one_current_v2(self, tmp_path: Path) -> None:
        """I04 §72: 8 same-base writers -> exactly ONE advances to v2.

        Losers get ManifestCASConflict (or transient ManifestLockHeld);
        stale writers never silently create v3; no two v2 branches become
        current; the loser fragments are never published.
        """
        _, _, repo = _make_repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)

        outcomes: list[str] = []
        lock = threading.Lock()
        results: dict[str, Any] = {"committed": [], "candidates": []}

        def writer(index: int) -> None:
            manifest_id = f"pm-2-w{index}"
            candidate = _manifest(
                partition_manifest_id=manifest_id,
                manifest_version=2,
                supersedes_manifest_id="pm-1",
                row_count=index + 1,
            )
            with lock:
                results["candidates"].append(manifest_id)
            try:
                result = repo.append_partition_manifest(
                    candidate, expected_current=("pm-1", 1)
                )
                outcome = f"{result.disposition.value}:{manifest_id}"
            except ManifestLockHeld:
                outcome = f"ManifestLockHeld:{manifest_id}"
            except ManifestCASConflict:
                outcome = f"ManifestCASConflict:{manifest_id}"
            with lock:
                outcomes.append(outcome)

        threads = [
            threading.Thread(target=writer, args=(i,)) for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        committed = [o for o in outcomes if o.startswith("COMMITTED_NEW")]
        idempotent = [o for o in outcomes if o.startswith("IDEMPOTENT_COMPLETION")]
        cas = [o for o in outcomes if o.startswith("ManifestCASConflict")]
        held = [o for o in outcomes if o.startswith("ManifestLockHeld")]
        assert len(committed) == 1, outcomes
        assert len(idempotent) == 0
        assert len(cas) + len(held) == 7, outcomes

        current = repo.get_current_manifest(PK)
        assert current.manifest_version == 2
        assert current.partition_manifest_id in results["candidates"]
        assert len(repo.list_manifest_versions(PK)) == 2
        assert repo.list_orphan_manifest_fragments(PK) == []
        # no v3 anywhere, no silent rebase
        versions = repo.list_manifest_versions(PK)
        assert [m.manifest_version for m in versions] == [1, 2]

    def test_stale_writer_cannot_create_v3(self, tmp_path: Path) -> None:
        """I04 §73: writer A based on v1 must fail once B committed v2."""
        _, _, repo = _make_repo(tmp_path)
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
                expected_current=("pm-1", 1),
            )
        assert repo.get_current_manifest(PK).partition_manifest_id == "pm-2"
        assert len(repo.list_manifest_versions(PK)) == 2

    def test_duplicate_writer_race_single_fragment(self, tmp_path: Path) -> None:
        """Two writers with the SAME v2: one COMMITTED_NEW, the other resolves
        idempotently; exactly one current v2 and one fragment."""
        _, _, repo = _make_repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)

        outcomes: list[str] = []
        lock = threading.Lock()
        v2 = _manifest(
            partition_manifest_id="pm-2",
            manifest_version=2,
            supersedes_manifest_id="pm-1",
            row_count=7,
        )

        def writer() -> None:
            outcome: str = ""
            for _ in range(100):  # bounded retry on transient lock contention
                try:
                    result = repo.append_partition_manifest(
                        v2, expected_current=("pm-1", 1)
                    )
                    outcome = result.disposition.value
                    break
                except ManifestLockHeld:
                    # transient contention: explicit retry must resolve
                    # idempotently against the (possibly already advanced)
                    # state; the winner holds the lock only briefly
                    outcome = ""
                    import time

                    time.sleep(0.01)
            assert outcome, "lock never became acquirable within the bound"
            with lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=writer) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert outcomes.count("COMMITTED_NEW") == 1
        assert all(o == "IDEMPOTENT_COMPLETION" for o in outcomes if o != "COMMITTED_NEW")
        current = repo.get_current_manifest(PK)
        assert current.partition_manifest_id == "pm-2"
        assert current.manifest_version == 2
        assert len(repo.list_manifest_versions(PK)) == 2


class TestPointerVisibility:
    def test_readers_never_observe_partial_pointer(self, tmp_path: Path) -> None:
        """I04 §36/§74: during pointer updates readers see old or new valid
        pointers — never partial JSON, never missing pointer after v1."""
        _, _, repo = _make_repo(tmp_path)
        repo.append_partition_manifest(_manifest(), expected_current=None)

        stop = threading.Event()
        observations: list[int] = []
        lock = threading.Lock()

        def reader() -> None:
            while not stop.is_set():
                current = repo.get_current_manifest(PK)
                with lock:
                    observations.append(current.manifest_version)
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
                    assert int(payload["manifest_version"]) >= 1

        threads = [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()
        try:
            for version in range(2, 7):
                repo.append_partition_manifest(
                    _manifest(
                        partition_manifest_id=f"pm-{version}",
                        manifest_version=version,
                        supersedes_manifest_id=f"pm-{version - 1}",
                    ),
                    expected_current=(f"pm-{version - 1}", version - 1),
                )
        finally:
            stop.set()
            for t in threads:
                t.join()

        assert observations
        assert all(1 <= v <= 6 for v in observations)
        # final state is the newest manifest
        assert repo.get_current_manifest(PK).manifest_version == 6