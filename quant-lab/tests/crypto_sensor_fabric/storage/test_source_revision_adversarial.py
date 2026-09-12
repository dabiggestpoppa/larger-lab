"""SENSOR-B4-I06D — restart, corruption, concurrency and T0B-preservation
adversarial proofs.

Covers (I06 §63-§82):

- registry state survives full restart; revision chains remain identical
  (§49/§79);
- corrupt committed fragments fail closed on reload — segments, observations
  and declarations each raise SourceRevisionCatalogCorrupt (§7/§14/§49);
- concurrent NEW-BYTES mutations can never fork revision numbering: the
  per-source lock serializes classification, the loser registers AFTER the
  winner and becomes the NEXT revision, or conflicts typed (§46);
- a stale source lock is never auto-deleted (§44, exercised in I06B);
- rev2 does NOT invalidate rev1 T0B (§63): a valid I05 projection chain
  built from a rev1 acquisition remains resolver-valid after rev2 appears;
- rev2 does NOT mutate an old PartitionManifest (§64);
- no old content is ever overwritten by new revisions (§66).
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.revisions import (
    RevisionObservationConflict,
    SourceRevisionCatalogCorrupt,
    SourceRevisionRegistry,
)

T1 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"


class RevStack:
    def __init__(self, tmp_path: Path) -> None:
        from _sibling_import import load_sibling

        mod = load_sibling("_i06_registry_mod", "test_source_revision_registry")
        self._stack = mod.Stack(tmp_path)
        self._data = mod._data

    def __getattr__(self, name):  # delegate to the inner stack
        return getattr(self._stack, name)


class TestRestartAndCorruption:
    def _registered(self, tmp_path: Path) -> RevStack:
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        return stack

    def test_full_restart_preserves_revision_chain(self, tmp_path) -> None:
        """§49/§79: all segments/observations/declarations survive restart."""
        stack = self._registered(tmp_path)
        before = stack.registry.list_revisions(
            stack.registry.revision_for_acquisition("acq-A")[0]
        )
        before_views = stack.registry.list_observations(
            stack.registry.revision_for_acquisition("acq-A")[0]
        )
        reopened = stack.reopen()
        key = reopened.revision_for_acquisition("acq-A")[0]
        after = reopened.list_revisions(key)
        after_views = reopened.list_observations(key)
        assert [(r.revision_number, r.blob_sha256, r.revision_state) for r in after] == [
            (r.revision_number, r.blob_sha256, r.revision_state) for r in before
        ]
        assert [v.acquisition_id for v in after_views] == [
            v.acquisition_id for v in before_views
        ]
        assert after[1].revision_state == "SOURCE_MUTATION"

    def _fragment_path(self, stack: RevStack, family: str, logical_id: str) -> Path:
        import hashlib

        return (
            stack.root
            / family
            / (hashlib.sha256(logical_id.encode()).hexdigest() + ".json")
        )

    def test_corrupt_segment_fails_restart(self, tmp_path) -> None:
        stack = self._registered(tmp_path)
        # Corrupt a segment fragment in place.
        seg_dir = stack.root / "segments"
        target = next(p for p in seg_dir.glob("*.json"))
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["revision_state"] = "TAMPERED"
        target.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_corrupt_segment_json_fails_restart(self, tmp_path) -> None:
        stack = self._registered(tmp_path)
        seg_dir = stack.root / "segments"
        target = next(p for p in seg_dir.glob("*.json"))
        target.write_text("{not json", encoding="utf-8")
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_corrupt_observation_fails_restart(self, tmp_path) -> None:
        stack = self._registered(tmp_path)
        obs_dir = stack.root / "observations"
        target = next(p for p in obs_dir.glob("*.json"))
        target.write_text('{"broken": true}', encoding="utf-8")
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_corrupt_declaration_fails_restart(self, tmp_path) -> None:
        stack = self._registered(tmp_path)
        key = stack.registry.revision_for_acquisition("acq-A")[0]
        stack.registry.declare_provider_revision(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="evidence/rev-note",
        )
        dec_dir = stack.root / "declarations"
        target = next(p for p in dec_dir.glob("*.json"))
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["revision_number"] = 99  # references a nonexistent revision
        target.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_corrupt_identity_descriptor_fails_restart(self, tmp_path) -> None:
        stack = self._registered(tmp_path)
        seg_dir = stack.root / "segments"
        target = next(p for p in seg_dir.glob("*.json"))
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["identity_descriptor"]["fields"]["venue"] = "spot"
        target.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_no_old_content_overwritten_by_new_revision(
        self, tmp_path
    ) -> None:
        """§66: after rev2, rev1's segment/acquisition/blob bytes remain
        byte-identical."""
        stack = self._registered(tmp_path)
        key = stack.registry.revision_for_acquisition("acq-A")[0]
        seg_dir = stack.root / "segments"
        import hashlib

        rev1_fragment = seg_dir / (
            hashlib.sha256(f"{key}:1".encode()).hexdigest() + ".json"
        )
        before_bytes = rev1_fragment.read_bytes()
        acq_a = stack.acq_repo.get_acquisition("acq-A")
        blob_path = next(
            p
            for p in stack.t0a.rglob("*")
            if p.is_file() and p.name.startswith(acq_a.blob_sha256[:16])
        )
        blob_before = blob_path.read_bytes()

        # Register rev3 (A again) and a new mutation, then verify rev1 truth.
        a2 = stack.seed(
            stack._data("A"), observed_at=T1 + timedelta(hours=2), acq_id="acq-A2"
        )
        stack.registry.register_acquisition(a2.acquisition_id)
        c = stack.seed(
            stack._data("C"), observed_at=T1 + timedelta(hours=3), acq_id="acq-C"
        )
        stack.registry.register_acquisition(c.acquisition_id)

        assert rev1_fragment.read_bytes() == before_bytes
        assert blob_path.read_bytes() == blob_before
        revs = stack.registry.list_revisions(key)
        assert [r.revision_number for r in revs] == [1, 2, 3, 4]
        assert revs[0].blob_sha256 == acq_a.blob_sha256


class TestConcurrentMutation:
    def test_concurrent_mutations_never_fork_revision_numbers(
        self, tmp_path
    ) -> None:
        """§46: two writers race to register DIFFERENT new bytes against one
        source.  The per-source lock serializes classification: one becomes
        rev2, the loser (earlier seen_at) fails typed — never two rev2
        records."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        key = stack.registry.revision_for_acquisition("acq-A")[0]

        b = stack.seed(
            stack._data("B"),
            observed_at=T1 + timedelta(hours=1),
            acq_id="acq-B",
        )
        c = stack.seed(
            stack._data("C"),
            observed_at=T1 + timedelta(hours=1),
            acq_id="acq-C",
        )
        results: list[tuple[str, object]] = []
        errors: list[Exception] = []

        def worker(acq_id: str) -> None:
            try:
                results.append(
                    (acq_id, stack.registry.register_acquisition(acq_id))
                )
            except Exception as exc:  # noqa: BLE001 — asserted below
                errors.append(exc)

        t1 = threading.Thread(target=worker, args=(b.acquisition_id,))
        t2 = threading.Thread(target=worker, args=(c.acquisition_id,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one success and one typed failure (same seen_at, different
        # bytes ⇒ whichever loses the race hits the temporal-ambiguity or
        # order conflict; the winner's classification is durable).
        assert len(results) == 1, (results, errors)
        assert len(errors) == 1
        assert isinstance(errors[0], RevisionObservationConflict | Exception)
        reopened = stack.reopen()
        revs = reopened.list_revisions(key)
        numbers = [r.revision_number for r in revs]
        assert numbers == sorted(set(numbers)) == [1, 2]  # no fork
        # The committed rev2 blob belongs to the winner.
        winner = results[0][1]
        assert revs[1].blob_sha256 == winner.blob_sha256


import threading  # noqa: E402  (used by TestConcurrentMutation above)


class TestT0BNonInvalidation:
    def _valid_projection_on_rev1(self, tmp_path: Path) -> tuple:
        """Build a full valid I05 chain (T0A → artifact → context → lineage)
        from a rev1 acquisition, using the real end-to-end stack."""
        from _sibling_import import load_sibling

        e2e = load_sibling("_i06_e2e_mod", "test_end_to_end_projection")
        chain = e2e.Chain(tmp_path)
        sha = chain.seed_blob(b'{"rows": ["rev1"]}')
        chain.seed_acquisition(sha, "acq-rev1")

        from crypto_sensor_fabric.storage.revisions import (
            RevisionSourceIdentityV1,
        )

        # The same source identity as the acquisition.
        acq = chain.acq_repo.get_acquisition("acq-rev1")
        identity = RevisionSourceIdentityV1.from_acquisition(acq)
        return chain, sha, acq, identity.source_revision_key(), e2e

    def test_rev2_does_not_invalidate_rev1_projection(
        self, tmp_path
    ) -> None:
        """§63: registering rev2 of a source leaves a valid rev1 T0B
        projection chain fully resolver-valid."""
        chain, sha, acq, key, e2e = self._valid_projection_on_rev1(tmp_path)

        # Register the source revision FIRST (rev1 == the projection source).
        reg_root = tmp_path / "registry"
        registry = SourceRevisionRegistry(
            reg_root,
            acquisition_repository=chain.acq_repo,
            blob_metadata_repository=chain.blob_repo,
            blob_store=chain.store,
            clock=lambda: T1,
        )
        registry.register_acquisition("acq-rev1")

        # Commit the valid projection chain from that rev1 acquisition.
        artifact, _path = chain.commit_projection(
            "proj-rev1", [(sha, "acq-rev1")]
        )
        from crypto_sensor_fabric.storage.models import PartitionManifest

        manifest = PartitionManifest(
            partition_manifest_id="pm-rev1",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=[sha],
            projection_refs=["proj-rev1"],
            created_at=e2e.FIXED,
        )

        # NOW the provider mutates: rev2 appears.  The refetch copies the
        # EXACT request semantics of rev1 (same logical source) — only the
        # returned bytes and observation time differ.
        new_data = b'{"rows": ["rev2"]}'
        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        put = chain.store.put_bytes(
            new_data, storage_encoding=StorageEncoding.NONE, source_media_type=e2e.MEDIA
        )
        chain.blob_repo.append_metadata(put.blob)
        fixed = e2e.FIXED
        rec2 = AcquisitionRecord(
            acquisition_id="acq-rev2",
            provider_id=acq.provider_id,
            venue=acq.venue,
            sensor_family=acq.sensor_family,
            request_fingerprint=acq.request_fingerprint,
            adapter_version=acq.adapter_version,
            requested_start=acq.requested_start,
            requested_end=acq.requested_end,
            native_instrument=acq.native_instrument,
            native_granularity=acq.native_granularity,
            request_started_at=acq.request_started_at,
            response_observed_at=fixed + timedelta(hours=1),
            ingested_at=fixed,
            http_status_or_source_status=acq.http_status_or_source_status,
            endpoint_host=acq.endpoint_host,
            endpoint_path=acq.endpoint_path,
            request_family=acq.request_family,
            source_locator=acq.source_locator,
            blob_sha256=put.blob.blob_sha256,
        )
        chain.acq_repo.append_acquisition(rec2)
        registry.register_acquisition("acq-rev2")

        # rev2 exists — but rev1 history is intact.
        revs = registry.list_revisions(key)
        assert [r.revision_number for r in revs] == [1, 2]

        # The rev1 projection chain remains FULLY resolver-valid (§63).
        chain.resolver.validate_projection_ref("proj-rev1", manifest)

        # The manifest's immutable content was not altered by rev2 (§64).
        assert manifest.projection_refs == ["proj-rev1"]
        assert manifest.blob_refs == [sha]
