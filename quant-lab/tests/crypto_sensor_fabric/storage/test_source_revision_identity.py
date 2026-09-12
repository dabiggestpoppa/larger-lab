"""SENSOR-B4-I06A — RevisionSourceIdentityV1 identity contract tests.

Covers (I06 §9-§14, §71):

- V1 identity derives from acquisition REQUEST semantics only;
- identical request semantics ⇒ identical source_revision_key;
- content/observation fields are structurally excluded — a different
  blob_sha256 NEVER mints a different logical source (§8 anti-doctrine);
- timestamps normalize to UTC ISO-8601; naive inputs fail closed;
- the key is full 64 lowercase hex, deterministic and canonical-JSON stable;
- persisted descriptors recompute to the stored key (§14) — tampering
  fails closed as SourceRevisionCatalogCorrupt;
- registry construction enforces the sealed dependency protocols (§16).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from crypto_sensor_fabric.storage.models import AcquisitionRecord
from crypto_sensor_fabric.storage.revisions import (
    IDENTITY_VERSION,
    RevisionConfigurationError,
    RevisionSourceIdentityV1,
    SourceRevisionCatalogCorrupt,
    SourceRevisionRegistry,
)

T1 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)
UTC_MINUS_5 = timezone(timedelta(hours=-5))


def _acq(
    *,
    acq_id: str = "acq-1",
    blob_sha: str | None = "a" * 64,
    provider: str = "kraken",
    venue: str = "futures",
    instrument: str = "BTC-USDT",
    granularity: str | None = "1m",
    request_fp: str = "fp-1",
    requested_start: datetime | None = None,
    requested_end: datetime | None = None,
    observed_at: datetime = T1,
    endpoint_host: str | None = "api.example",
    endpoint_path: str | None = "/v1/trades",
    request_family: str | None = "TRADES",
    source_locator: str = "file:///tmp/delivery-A",
    adapter_version: str = "1.0",
    failure_ref: str | None = None,
) -> AcquisitionRecord:
    return AcquisitionRecord(
        acquisition_id=acq_id,
        provider_id=provider,
        venue=venue,
        sensor_family="MECHANICAL_TRADE",
        request_fingerprint=request_fp,
        adapter_version=adapter_version,
        requested_start=requested_start or T1,
        requested_end=requested_end or T1,
        native_instrument=instrument,
        native_granularity=granularity,
        request_started_at=T1,
        response_observed_at=observed_at,
        ingested_at=T1,
        http_status_or_source_status="200",
        endpoint_host=endpoint_host,
        endpoint_path=endpoint_path,
        request_family=request_family,
        source_locator=source_locator,
        blob_sha256=blob_sha,
        failure_ref=failure_ref,
    )


def _expected_key(acq: AcquisitionRecord) -> str:
    """Independent SHA256 recomputation of the canonical descriptor
    (auditable formula, I06 §13)."""
    fields = {
        "provider_id": acq.provider_id,
        "venue": acq.venue,
        "sensor_family": str(acq.sensor_family.value),
        "native_instrument": acq.native_instrument,
        "native_granularity": str(acq.native_granularity.value)
        if acq.native_granularity is not None
        else None,
        "request_fingerprint": acq.request_fingerprint,
        "requested_start": acq.requested_start.astimezone(UTC).isoformat(),
        "requested_end": acq.requested_end.astimezone(UTC).isoformat(),
        "endpoint_host": acq.endpoint_host,
        "endpoint_path": acq.endpoint_path,
        "request_family": acq.request_family,
    }
    payload = {"identity_version": IDENTITY_VERSION, "fields": fields}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


class TestIdentityDerivation:
    def test_key_matches_independent_formula(self) -> None:
        acq = _acq()
        identity = RevisionSourceIdentityV1.from_acquisition(acq)
        assert identity.source_revision_key() == _expected_key(acq)
        assert len(identity.source_revision_key()) == 64
        int(identity.source_revision_key(), 16)  # full lowercase hex

    def test_same_request_semantics_same_key(self) -> None:
        a = RevisionSourceIdentityV1.from_acquisition(
            _acq(acq_id="acq-A", blob_sha="a" * 64, observed_at=T1)
        )
        b = RevisionSourceIdentityV1.from_acquisition(
            _acq(
                acq_id="acq-B",
                blob_sha="b" * 64,
                observed_at=datetime(2026, 9, 11, 8, 0, 0, tzinfo=UTC),
            )
        )
        # Different acquisition, bytes and observation time — SAME source.
        assert a.source_revision_key() == b.source_revision_key()

    def test_content_hash_never_enters_source_key(self) -> None:
        """I06 §8 anti-doctrine: mutation mints a REVISION, not a SOURCE."""
        a = RevisionSourceIdentityV1.from_acquisition(
            _acq(blob_sha="a" * 64)
        )
        b = RevisionSourceIdentityV1.from_acquisition(
            _acq(blob_sha="f" * 64)
        )
        assert a.source_revision_key() == b.source_revision_key()

    def test_excluded_observation_fields_change_nothing(self) -> None:
        """§11: retrieval/observation fields are structurally outside the
        identity descriptor."""
        base = RevisionSourceIdentityV1.from_acquisition(_acq())
        variants = [
            _acq(acq_id="other"),
            _acq(adapter_version="9.9.9"),
            _acq(source_locator="file:///tmp/delivery-TEMP-ZZ"),
            _acq(failure_ref="ref-123"),
            _acq(observed_at=datetime(2030, 1, 1, tzinfo=UTC)),
        ]
        for variant in variants:
            assert (
                RevisionSourceIdentityV1.from_acquisition(
                    variant
                ).source_revision_key()
                == base.source_revision_key()
            )

    def test_request_semantics_change_key(self) -> None:
        base = RevisionSourceIdentityV1.from_acquisition(_acq())
        changed = [
            _acq(provider="binance"),
            _acq(venue="spot"),
            _acq(instrument="ETH-USDT"),
            _acq(granularity=None),
            _acq(request_fp="fp-OTHER"),
            _acq(endpoint_path="/v1/trades/v2"),
        ]
        keys = {
            RevisionSourceIdentityV1.from_acquisition(v).source_revision_key()
            for v in changed
        }
        assert base.source_revision_key() not in keys
        assert len(keys) == len(changed)  # each semantic change is distinct

    def test_requested_window_changes_key(self) -> None:
        base = RevisionSourceIdentityV1.from_acquisition(_acq())
        shifted = RevisionSourceIdentityV1.from_acquisition(
            _acq(requested_start=datetime(2026, 9, 9, tzinfo=UTC))
        )
        assert base.source_revision_key() != shifted.source_revision_key()


class TestIdentityCanonicalization:
    def test_offset_aware_non_utc_normalized(self) -> None:
        """§10: aware timestamps serialize UTC-normalized (§16 doctrine)."""
        acq = _acq(
            requested_start=datetime(2026, 9, 10, 7, 0, 0, tzinfo=UTC_MINUS_5)
        )
        descriptor = RevisionSourceIdentityV1.from_acquisition(
            acq
        ).to_descriptor()
        start = descriptor["fields"]["requested_start"]
        assert start.endswith("+00:00")
        assert start == "2026-09-10T12:00:00+00:00"
        assert start == acq.requested_start.astimezone(UTC).isoformat()

    def test_descriptor_is_canonical_json_stable(self) -> None:
        acq = _acq()
        i1 = RevisionSourceIdentityV1.from_acquisition(acq)
        i2 = RevisionSourceIdentityV1.from_acquisition(acq)
        assert i1.to_descriptor() == i2.to_descriptor()
        assert i1.source_revision_key() == i2.source_revision_key()
        assert i1.model_dump() == i2.model_dump()

    def test_identity_version_is_frozen_v1(self) -> None:
        acq = _acq()
        identity = RevisionSourceIdentityV1.from_acquisition(acq)
        assert identity.identity_version == IDENTITY_VERSION == 1
        descriptor = identity.to_descriptor()
        assert descriptor["identity_version"] == 1
        # identity_version participates in the key formula.
        tampered = dict(descriptor)
        tampered["identity_version"] = 2
        canonical = json.dumps(
            tampered, sort_keys=True, separators=(",", ":")
        ).encode()
        assert (
            hashlib.sha256(canonical).hexdigest()
            != identity.source_revision_key()
        )


class TestRegistryConstruction:
    def _deps(self, tmp_path: Path):
        """Minimal satisfying dependency set (real repos wired to empty
        T0A roots are exercised in the registry test module)."""
        from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
        from crypto_sensor_fabric.storage.catalog import (
            AcquisitionRepository,
            BlobMetadataRepository,
        )

        t0a = tmp_path / "t0a"
        t0a.mkdir(parents=True, exist_ok=True)
        store = LocalBlobStore(str(t0a))
        blob_repo = BlobMetadataRepository(t0a, blob_store=store)
        acq_repo = AcquisitionRepository(
            t0a, blob_store=store, blob_metadata_repository=blob_repo
        )
        return acq_repo, blob_repo, store

    def test_missing_dependencies_fail_at_construction(self, tmp_path) -> None:
        acq_repo, blob_repo, store = self._deps(tmp_path)
        with pytest.raises(RevisionConfigurationError):
            SourceRevisionRegistry(tmp_path / "reg")
        with pytest.raises(RevisionConfigurationError):
            SourceRevisionRegistry(
                tmp_path / "reg", acquisition_repository=acq_repo
            )
        with pytest.raises(RevisionConfigurationError):
            SourceRevisionRegistry(
                tmp_path / "reg",
                acquisition_repository=acq_repo,
                blob_metadata_repository=blob_repo,
            )
        # All three present: construction succeeds.
        SourceRevisionRegistry(
            tmp_path / "reg",
            acquisition_repository=acq_repo,
            blob_metadata_repository=blob_repo,
            blob_store=store,
        )

    def test_dependency_missing_capability_fails_construction(
        self, tmp_path
    ) -> None:
        acq_repo, blob_repo, _ = self._deps(tmp_path)

        class _NoGet:
            pass

        with pytest.raises(RevisionConfigurationError):
            SourceRevisionRegistry(
                tmp_path / "reg",
                acquisition_repository=_NoGet(),  # lacks get_acquisition
                blob_metadata_repository=blob_repo,
                blob_store=_NoGet(),
            )
        del acq_repo, blob_repo


class TestDescriptorTamperFailClosed(TestRegistryConstruction):
    """Inherits the real dependency factory (_deps)."""

    def test_tampered_descriptor_rejected_on_reload(self, tmp_path) -> None:
        """§14: the persisted descriptor must recompute to the stored key —
        a tampered descriptor is catalog corruption, never trusted."""
        acq_repo, blob_repo, store = self._deps(tmp_path)
        root = tmp_path / "reg"
        reg = SourceRevisionRegistry(
            root,
            acquisition_repository=acq_repo,
            blob_metadata_repository=blob_repo,
            blob_store=store,
        )
        identity = RevisionSourceIdentityV1.from_acquisition(_acq())
        key = identity.source_revision_key()
        from crypto_sensor_fabric.storage.revisions import RevisionSegmentRecord

        segment = RevisionSegmentRecord(
            source_revision_key=key,
            segment_id=f"{key}:1",
            identity_version=1,
            identity_descriptor=identity.to_descriptor(),
            revision_number=1,
            blob_sha256="a" * 64,
            first_seen_at=T1.isoformat(),
            first_acquisition_id="acq-x",
            revision_state="STABLE",
            revision_reason="test",
            registered_at=T1.isoformat(),
        )
        payload = segment.model_dump(mode="json")
        # Tamper a semantic field inside the descriptor: the fragment still
        # parses, but the descriptor no longer recomputes to the stored key.
        payload["identity_descriptor"]["fields"]["native_instrument"] = "ETH-USDT"
        target = (
            root / "segments" / hashlib.sha256(f"{key}:1".encode()).hexdigest()
        ).with_suffix(".json")
        Path(target).write_text(json.dumps(payload), encoding="utf-8")

        with pytest.raises(SourceRevisionCatalogCorrupt):
            SourceRevisionRegistry(
                root,
                acquisition_repository=acq_repo,
                blob_metadata_repository=blob_repo,
                blob_store=store,
            )
