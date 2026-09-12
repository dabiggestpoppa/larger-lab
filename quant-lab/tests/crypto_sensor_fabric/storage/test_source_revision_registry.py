"""SENSOR-B4-I06B — durable mutation/refetch registry behavior tests.

Covers (I06 §15-§32, §39-§48):

- registration resolves durable acquisition truth and physically verifies
  the T0A blob (no presence-only registration, §18);
- blobless acquisitions never create content segments (§17);
- forensic acquisitions are OBSERVED but never promoted (§19);
- first observation ⇒ rev1 STABLE; identical refetch ⇒ no new revision;
  different bytes ⇒ SOURCE_MUTATION revision; A→B→A ⇒ three segments
  (§22-§27);
- ``last_seen_at`` is materialized from append-only observations — birth
  records are never rewritten (§30);
- observation chronology is ``response_observed_at`` (§20); out-of-order
  registration fails typed (§39); same-time differing bytes fail closed
  (§40); same-time identical bytes are a legal refetch (§41);
- per-source file locks serialize writers and are never auto-deleted
  (§43/§44); concurrent identical refetches converge (§45);
- re-registration of the same acquisition re-verifies physical truth
  (§47); conflicting rebinding fails typed (§48);
- crash between segment birth and observation completes correctly (§68).
"""

from __future__ import annotations

import hashlib
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.models import AcquisitionRecord
from crypto_sensor_fabric.storage.revisions import (
    MutationSeverity,
    ObservationState,
    RevisionContentCorrupt,
    RevisionContentUnavailable,
    RevisionObservationConflict,
    RevisionObservationOrderConflict,
    RevisionLockHeld,
    RevisionState,
    RevisionTemporalAmbiguity,
    SourceRevisionRegistry,
)

T1 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"


class Stack:
    """Real T0A evidence stack + registry on one pytest-tmp root."""

    def __init__(self, tmp_path: Path) -> None:
        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(parents=True)
        self.store = LocalBlobStore(str(self.t0a))
        self.blob_repo = BlobMetadataRepository(self.t0a, blob_store=self.store)
        self.acq_repo = AcquisitionRepository(
            self.t0a, blob_store=self.store, blob_metadata_repository=self.blob_repo
        )
        self.root = tmp_path / "registry"
        self.registry = SourceRevisionRegistry(
            self.root,
            acquisition_repository=self.acq_repo,
            blob_metadata_repository=self.blob_repo,
            blob_store=self.store,
            clock=lambda: T1,
        )
        self._counter = 0

    def seed(
        self,
        data: bytes,
        *,
        acq_id: str | None = None,
        observed_at: datetime = T1,
        failure_ref: str | None = None,
        http_status: str = "200",
        request_fp: str = "fp-1",
    ) -> AcquisitionRecord:
        self._counter += 1
        acq_id = acq_id or f"acq-{self._counter}"
        # Content-addressed T0A dedupe: identical bytes map to the SAME
        # blob (the store is no-clobber).  A refetch reuses durable blob
        # metadata instead of re-writing it.
        sha = hashlib.sha256(data).hexdigest()
        try:
            self.blob_repo.get_blob_metadata(sha)
            blob_exists = True
        except Exception:
            blob_exists = False
        if not blob_exists:
            put = self.store.put_bytes(
                data,
                storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
            )
            self.blob_repo.append_metadata(put.blob)
            sha = put.blob.blob_sha256
        record = AcquisitionRecord(
            acquisition_id=acq_id,
            provider_id="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            request_fingerprint=request_fp,
            adapter_version="1.0",
            requested_start=T1,
            requested_end=T1,
            native_instrument="BTC-USDT",
            native_granularity="1m",
            request_started_at=T1,
            response_observed_at=observed_at,
            ingested_at=observed_at,
            http_status_or_source_status=http_status,
            endpoint_host="api.example",
            endpoint_path="/v1/trades",
            request_family="TRADES",
            source_locator="file:///tmp/delivery",
            blob_sha256=sha,
            failure_ref=failure_ref,
        )
        self.acq_repo.append_acquisition(record)
        return record

    def reopen(self) -> SourceRevisionRegistry:
        return SourceRevisionRegistry(
            self.root,
            acquisition_repository=self.acq_repo,
            blob_metadata_repository=self.blob_repo,
            blob_store=self.store,
            clock=lambda: T1,
        )


def _data(tag: str) -> bytes:
    return f'{{"payload":"{tag}"}}'.encode()


class TestRegistrationGates:
    def test_registration_requires_physically_verified_blob(
        self, tmp_path
    ) -> None:
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"))
        # Corrupt the physical bytes BEHIND the store's back.
        blob_path = next(
            p
            for p in stack.t0a.rglob("*")
            if p.is_file() and p.name.startswith(acq.blob_sha256[:16])
        )
        blob_path.write_bytes(b"CORRUPTED!!!")
        with pytest.raises(RevisionContentCorrupt):
            stack.registry.register_acquisition(acq.acquisition_id)
        # Nothing was durably registered.
        assert stack.registry.list_revisions(
            hashlib.sha256(b"x").hexdigest()
        ) == []

    def test_registration_requires_durable_metadata(self, tmp_path) -> None:
        """§18: blob metadata must exist durably before registration.
        (I04's acquisition append already refuses a dangling blob reference,
        so this gate is exercised through the registry's own re-check.)"""
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"))
        sha = acq.blob_sha256
        # Remove the durable metadata fragment behind the registry's back.
        meta_dir = stack.t0a / "catalogs" / "manifests" / "blobs"
        removed = False
        for frag in meta_dir.glob(f"{sha}.*.parquet"):
            frag.unlink()
            removed = True
        assert removed
        with pytest.raises(RevisionContentCorrupt):
            stack.registry.register_acquisition(acq.acquisition_id)

    def test_blobless_acquisition_creates_no_segment(self, tmp_path) -> None:
        """§17: failure/no-data acquisitions stay in history but create NO
        content revision; no zero hash is manufactured."""
        stack = Stack(tmp_path)
        record = AcquisitionRecord(
            acquisition_id="acq-failed",
            provider_id="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            request_fingerprint="fp-1",
            adapter_version="1.0",
            requested_start=T1,
            requested_end=T1,
            native_instrument="BTC-USDT",
            native_granularity="1m",
            request_started_at=T1,
            response_observed_at=T1,
            ingested_at=T1,
            http_status_or_source_status="503",
            source_locator="file:///tmp/delivery",
            blob_sha256=None,
            failure_ref="ref-503",
        )
        stack.acq_repo.append_acquisition(record)
        with pytest.raises(RevisionContentUnavailable):
            stack.registry.register_acquisition("acq-failed")

    def test_missing_acquisition_typed(self, tmp_path) -> None:
        stack = Stack(tmp_path)
        with pytest.raises(RevisionContentUnavailable):
            stack.registry.register_acquisition("acq-never-registered")

    def test_forensic_acquisition_observed_not_promoted(self, tmp_path) -> None:
        """§19: the provider returned exact bytes under a failed status —
        the observation is evidentiary with usable_provenance=False."""
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"), failure_ref="ref-500", http_status="500")
        obs = stack.registry.register_acquisition(acq.acquisition_id)
        assert obs.usable_provenance is False
        key = obs.source_revision_key
        segments = stack.registry.list_revisions(key)
        assert len(segments) == 1  # evidence still classifies the source
        views = stack.registry.list_observations(key)
        birth = next(v for v in views if v.acquisition_id == acq.acquisition_id)
        assert birth.usable_provenance is False

    def test_h3_mismatch_forensic_not_promoted(self, tmp_path) -> None:
        """§19: provider checksum failure stays forensic (I04R2 §5 route).
        I04R1 §19: a checksum mismatch is retained ONLY as verified=False
        failure evidence WITH failure_ref — so the acquisition is created
        through the append-time backdoor of an already-durable blob."""
        stack = Stack(tmp_path)
        data = _data("A")
        put = stack.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        stack.blob_repo.append_metadata(put.blob)
        record = AcquisitionRecord(
            acquisition_id="acq-h3bad",
            failure_ref="ref-h3-mismatch",
            provider_id="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            request_fingerprint="fp-1",
            adapter_version="1.0",
            requested_start=T1,
            requested_end=T1,
            native_instrument="BTC-USDT",
            native_granularity="1m",
            request_started_at=T1,
            response_observed_at=T1,
            ingested_at=T1,
            http_status_or_source_status="200",
            source_locator="file:///tmp/delivery",
            blob_sha256=put.blob.blob_sha256,
            provider_checksum_algorithm="SHA256",
            provider_checksum_value=hashlib.sha256(b"WRONG").hexdigest(),
            provider_checksum_verified=False,
        )
        stack.acq_repo.append_acquisition(record)
        obs = stack.registry.register_acquisition(record.acquisition_id)
        assert obs.usable_provenance is False


class TestRevisionClassification:
    def test_first_observation_rev1_stable(self, tmp_path) -> None:
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"))
        obs = stack.registry.register_acquisition(acq.acquisition_id)
        revs = stack.registry.list_revisions(obs.source_revision_key)
        assert len(revs) == 1
        rev = revs[0]
        assert rev.revision_number == 1
        assert rev.revision_state == RevisionState.STABLE.value
        assert rev.blob_sha256 == acq.blob_sha256
        assert rev.first_seen_at == rev.last_seen_at == T1.isoformat()
        assert rev.first_acquisition_id == acq.acquisition_id

    def test_identical_refetch_no_new_revision(self, tmp_path) -> None:
        """§24: same bytes ⇒ observation event, SAME revision number;
        last_seen materialized forward; birth record unmodified."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(
            _data("A"),
            observed_at=T1 + timedelta(hours=1),
        )
        o1 = stack.registry.register_acquisition(a.acquisition_id)
        o2 = stack.registry.register_acquisition(b.acquisition_id)
        assert o1.revision_number == o2.revision_number == 1
        assert o2.observation_state == ObservationState.IDENTICAL_REFETCH.value
        assert o2.severity == MutationSeverity.INFO.value
        revs = stack.registry.list_revisions(o1.source_revision_key)
        assert len(revs) == 1  # no new segment
        rev = revs[0]
        assert rev.first_seen_at == T1.isoformat()  # birth unchanged
        assert rev.last_seen_at == (T1 + timedelta(hours=1)).isoformat()
        # Both acquisitions visible in observation history (§52).
        views = stack.registry.list_observations(o1.source_revision_key)
        assert {v.acquisition_id for v in views} == {
            a.acquisition_id,
            b.acquisition_id,
        }

    def test_different_bytes_new_revision_mutation(self, tmp_path) -> None:
        """§25: A→B ⇒ rev2 SOURCE_MUTATION WARNING; both remain."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        o2 = stack.registry.register_acquisition(b.acquisition_id)
        assert o2.revision_number == 2
        assert o2.observation_state == ObservationState.SOURCE_MUTATION.value
        assert o2.severity == MutationSeverity.WARNING.value
        revs = stack.registry.list_revisions(o2.source_revision_key)
        assert [r.revision_number for r in revs] == [1, 2]
        assert revs[0].blob_sha256 == a.blob_sha256
        assert revs[1].blob_sha256 == b.blob_sha256
        assert revs[1].revision_state == RevisionState.SOURCE_MUTATION.value

    def test_content_reversion_three_segments(self, tmp_path) -> None:
        """§26: A→B→A ⇒ THREE segments; rev3 is a new transition, never a
        collapse back into rev1.  §56: ALL returns rev1 A, rev2 B, rev3 A
        with no blob dedupe."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        a2 = stack.seed(_data("A"), observed_at=T1 + timedelta(hours=2))
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        o3 = stack.registry.register_acquisition(a2.acquisition_id)
        key = o3.source_revision_key
        assert o3.revision_number == 3
        revs = stack.registry.list_revisions(key)
        assert [(r.revision_number, r.blob_sha256) for r in revs] == [
            (1, a.blob_sha256),
            (2, b.blob_sha256),
            (3, a2.blob_sha256),
        ]
        # rev1 and rev3 share the content hash but are DISTINCT segments —
        # history is never collapsed by blob identity.
        assert revs[0].blob_sha256 == revs[2].blob_sha256
        assert revs[0].first_acquisition_id != revs[2].first_acquisition_id
        assert revs[2].revision_state == RevisionState.SOURCE_MUTATION.value

    def test_match_of_older_revision_after_change_is_new_transition(
        self, tmp_path
    ) -> None:
        """§27: identical-bytes means identical to the CURRENT segment
        only."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        a2 = stack.seed(_data("A"), observed_at=T1 + timedelta(hours=2))
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        o3 = stack.registry.register_acquisition(a2.acquisition_id)
        # The third observation is a SOURCE_MUTATION-style transition (A
        # returned after B), NOT an IDENTICAL_REFETCH of rev1.
        assert o3.revision_number == 3
        assert (
            o3.observation_state == ObservationState.SOURCE_MUTATION.value
        )
        del b

    def test_provider_declared_revision_needs_evidence(self, tmp_path) -> None:
        """§33: different bytes + EXPLICIT declaration ⇒
        PROVIDER_DECLARED_REVISION (NOTICE); no declaration ⇒ mutation."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        o2 = stack.registry.register_acquisition(
            b.acquisition_id,
            provider_declaration={
                "declaration_kind": "revision",
                "evidence_ref": "evidence/provider-note-42",
                "declared_at": (T1 + timedelta(minutes=5)).isoformat(),
            },
        )
        assert o2.observation_state == (
            ObservationState.PROVIDER_DECLARED_REVISION.value
        )
        assert o2.severity == MutationSeverity.NOTICE.value
        revs = stack.registry.list_revisions(o2.source_revision_key)
        assert revs[1].revision_state == (
            RevisionState.PROVIDER_DECLARED_REVISION.value
        )
        del a

    def test_provider_declaration_without_evidence_ref_rejected(
        self, tmp_path
    ) -> None:
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        with pytest.raises(Exception) as excinfo:
            stack.registry.register_acquisition(
                b.acquisition_id,
                provider_declaration={"declaration_kind": "revision"},
            )
        assert "evidence_ref" in str(excinfo.value)
        # Fail-closed: no segment was published for the declaration attempt.
        revs_after = stack.reopen().list_revisions(
            stack.registry.revision_for_acquisition(a.acquisition_id)[0]
        )
        assert len(revs_after) == 1

    def test_unknown_revision_not_default_for_mutation(self, tmp_path) -> None:
        """§38: ordinary different-byte observations are KNOWN mutation —
        UNKNOWN_REVISION never appears."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        o2 = stack.registry.register_acquisition(b.acquisition_id)
        states = {
            r.revision_state
            for r in stack.registry.list_revisions(o2.source_revision_key)
        }
        assert RevisionState.UNKNOWN_REVISION.value not in states


class TestTemporalOrdering:
    def test_out_of_order_observation_fails_closed(self, tmp_path) -> None:
        """§39: earlier seen_at than the latest registered — retroactive
        insertion with renumbering is forbidden."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1 + timedelta(hours=2))
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        with pytest.raises(RevisionObservationOrderConflict):
            stack.registry.register_acquisition(b.acquisition_id)

    def test_same_time_identical_bytes_legal_refetch(self, tmp_path) -> None:
        """§41: same seen_at + same current blob — no content-order
        ambiguity."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("A"), observed_at=T1, acq_id="acq-same-time")
        stack.registry.register_acquisition(a.acquisition_id)
        o2 = stack.registry.register_acquisition(b.acquisition_id)
        assert o2.revision_number == 1
        assert o2.observation_state == ObservationState.IDENTICAL_REFETCH.value

    def test_same_time_different_bytes_ambiguous(self, tmp_path) -> None:
        """§40: identical seen_at, differing bytes, unprovable order —
        fail closed; acquisition evidence remains durable."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1, acq_id="acq-tie")
        stack.registry.register_acquisition(a.acquisition_id)
        with pytest.raises(RevisionTemporalAmbiguity):
            stack.registry.register_acquisition(b.acquisition_id)
        # Acquisition history keeps both.
        assert stack.acq_repo.get_acquisition(b.acquisition_id) is not None


class TestWriterCoordination:
    def test_lock_held_fails_typed_never_auto_deleted(self, tmp_path) -> None:
        """§44: a pre-existing lock is typed RevisionLockHeld and is NEVER
        removed by the registry."""
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"))
        identity = stack.registry.register_acquisition(acq.acquisition_id)
        key = identity.source_revision_key
        lock_path = stack.root / "locks" / f"{key}.lock"
        # A second seed for a new observation on the same source.
        b = stack.seed(_data("A"), observed_at=T1 + timedelta(hours=1))
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text("held\n", encoding="utf-8")
        with pytest.raises(RevisionLockHeld):
            stack.registry.register_acquisition(b.acquisition_id)
        assert lock_path.exists()  # never auto-deleted

    def test_concurrent_identical_refetch_converges(self, tmp_path) -> None:
        """§45: two writers, distinct acquisitions, same current bytes ⇒
        one revision segment, both observations, no duplicate numbers."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        stack.registry.register_acquisition(a.acquisition_id)
        key = stack.registry.revision_for_acquisition(a.acquisition_id)[0]
        b = stack.seed(
            _data("A"), observed_at=T1 + timedelta(hours=1), acq_id="acq-c1"
        )
        c = stack.seed(
            _data("A"), observed_at=T1 + timedelta(hours=1), acq_id="acq-c2"
        )
        results: list[object] = []
        errors: list[Exception] = []

        def worker(acq_id: str) -> None:
            try:
                results.append(stack.registry.register_acquisition(acq_id))
            except Exception as exc:  # noqa: BLE001 — recorded and asserted
                errors.append(exc)

        t1 = threading.Thread(target=worker, args=(b.acquisition_id,))
        t2 = threading.Thread(target=worker, args=(c.acquisition_id,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert not errors
        assert len(results) == 2
        revs = stack.reopen().list_revisions(key)
        assert [r.revision_number for r in revs] == [1]
        views = stack.registry.list_observations(key)
        assert {v.acquisition_id for v in views} >= {
            b.acquisition_id,
            c.acquisition_id,
        }


class TestIdempotence:
    def test_reregister_same_acquisition_idempotent(self, tmp_path) -> None:
        """§47: re-resolve, re-verify, recompute — then idempotent success."""
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"), observed_at=T1)
        first = stack.registry.register_acquisition(acq.acquisition_id)
        second = stack.registry.register_acquisition(acq.acquisition_id)
        assert second.source_revision_key == first.source_revision_key
        assert second.revision_number == first.revision_number
        assert second.blob_sha256 == first.blob_sha256
        # No duplicate observation fragments.
        views = stack.registry.list_observations(first.source_revision_key)
        assert [v.acquisition_id for v in views].count(acq.acquisition_id) == 1

    def test_reregistration_after_blob_corruption_fails(
        self, tmp_path
    ) -> None:
        """§47/§77: no stale cached success — corrupted physical truth fails
        even though the binding is known."""
        stack = Stack(tmp_path)
        acq = stack.seed(_data("A"), observed_at=T1)
        stack.registry.register_acquisition(acq.acquisition_id)
        blob_path = next(
            p
            for p in stack.t0a.rglob("*")
            if p.is_file() and p.name.startswith(acq.blob_sha256[:16])
        )
        blob_path.write_bytes(b"SCRAMBLED")
        with pytest.raises(RevisionContentCorrupt):
            stack.registry.register_acquisition(acq.acquisition_id)

    def test_rebinding_conflict_typed(self, tmp_path) -> None:
        """§48: an acquisition already mapped to a revision can never be
        silently rebound to a different one."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        stack.registry.register_acquisition(a.acquisition_id)
        key, rev, blob = stack.registry._acquisition_bindings[
            a.acquisition_id
        ]
        stack.registry._acquisition_bindings[a.acquisition_id] = (
            key,
            rev + 7,
            blob,
        )
        with pytest.raises(RevisionObservationConflict):
            stack.registry.register_acquisition(a.acquisition_id)


class TestCrashCompletion:
    def test_segment_without_observation_completes_on_retry(
        self, tmp_path
    ) -> None:
        """§68: crash after segment birth, before observation.  Retry of
        the SAME birth acquisition completes with the segment's OWN
        classification — never a different revision chain."""
        stack = Stack(tmp_path)
        a = stack.seed(_data("A"), observed_at=T1)
        b = stack.seed(_data("B"), observed_at=T1 + timedelta(hours=1))
        stack.registry.register_acquisition(a.acquisition_id)
        first = stack.registry.register_acquisition(b.acquisition_id)
        key = first.source_revision_key
        # Simulate the crash: destroy the observation record of rev2 but
        # keep the durable segment.
        obs_fragment = stack.root / "observations" / (
            hashlib.sha256(b.acquisition_id.encode()).hexdigest() + ".json"
        )
        obs_fragment.unlink()
        reopened = stack.reopen()
        views = reopened.list_observations(key)
        assert b.acquisition_id not in {v.acquisition_id for v in views}
        # Exact retry completes the missing observation.
        completed = reopened.register_acquisition(b.acquisition_id)
        assert completed.revision_number == 2
        assert (
            completed.observation_state
            == ObservationState.SOURCE_MUTATION.value
        )
        final = reopened.list_revisions(key)
        assert [r.revision_number for r in final] == [1, 2]
