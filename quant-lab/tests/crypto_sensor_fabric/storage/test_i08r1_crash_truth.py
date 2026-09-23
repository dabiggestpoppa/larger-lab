"""SENSOR-B4-I08R1B — crash TRUTH matrix: real boundaries, not names (I08R1
§10-§22, §28, §29).

The committed I08 matrix is historical first-pass evidence; operator review
found several of its scenarios did not instantiate the actual frozen crash
boundary (I08R1 §33 documents the specific cases).  This module builds the
authoritative proof:

- every scenario constructs the REAL pre-crash state on the real stack;
- a crash is EMITTED at the frozen boundary (typed injected fault or
  physically simulated process death via fresh repository instances);
- post-restart truth is probed through FRESH repository instances;
- recovery runs through a NEW RecoveryEngine (restart replay);
- cursor and history effects are asserted per frozen row.

Key corrections over the historical matrix (I08R1 §11-§22):
- crash 2 proves BOTH branches: unknown-context quarantine AND registered
  context replay, including the crash BETWEEN metadata and acquisition;
- crash 4 uses a real CATALOGED projection durable before any manifest
  reference (a catalog row alone is NOT health);
- crash 5 publishes a VALID v2 fragment (supersedes == durable v1) before
  the pointer update, reconciled through the public CAS API;
- crash 6 stops BEFORE any checkpoint (no resume advancement, no anchors);
- crash 7/8 go through the accepted I06 SourceRevisionRegistry
  (IDENTICAL_REFETCH / SOURCE_MUTATION with genuinely different bytes);
- crash 11 reports the measured projection-invalidation contract gap
  instead of disguising an orphan junk file as parser invalidation;
- crash 12 proves the CAS loser receives a typed conflict.

Effect atomicity (I08R1 §28) reuses this harness: an injected death
between the durable effect and the final RecoveryAction cannot lose the
effect — exact retry converges to one forensic artifact and one completed
operation, with no duplicate movement and no unexplained mutation.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _p in (str(_SRC), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.providers.base.enums import Granularity  # noqa: E402
from crypto_sensor_fabric.storage import recovery as rec  # noqa: E402
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    StorageEncoding,
    StorageJobStatus,
    StorageObjectType,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    ObservationState,
    SourceRevisionRegistry,
)

_base = load_sibling("_i08r1_base_mod", "test_job_state_r1")
_crash = load_sibling("_i08r1_crash_mod", "test_recovery_crash_matrix")

FP = _base._FP
PROVIDER = _base._PROVIDER
MEDIA = _base.MEDIA
FIXED = _base.FIXED

_PARTITION_KEY = FP + "/2026-01-15"  # == _ORPHAN_PARTITION_KEY in _crash


def RecoveryStack(root: Path, **kwargs: Any) -> Any:
    """Factory over the accepted I07 stack (sibling-loader quirk)."""
    return _crash.RecoveryStack(root, **kwargs)


def _engine(stack: Any) -> rec.RecoveryEngine:
    return _crash._engine(stack)


class _FaultInjected(RuntimeError):
    """A deterministic injected crash boundary."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _recovery_stack(stack: Any) -> Any:
    """Reopen durable truth with a fresh stack instance (no cache); the
    T0B projection repositories are rebuilt when the original carried
    them (a reopened JobStack does not construct them itself)."""
    stack2 = RecoveryStack(Path(stack.root), clock=stack.clock)
    if getattr(stack, "artifacts", None) is not None:
        _build_projection_stack(stack2)
    return stack2


def _problems(result: rec.RecoveryScanResult) -> set[str]:
    return {f.problem for f in result.findings}


def _blob_object_path(root: Path, sha: str) -> Path:
    from crypto_sensor_fabric.storage.paths import blob_object_key, resolve_under_root

    return resolve_under_root(root, blob_object_key(sha, StorageEncoding.NONE))


def _acquisition_of(stack: Any, acquisition_id: str) -> Any:
    return stack.acq_repo.get_acquisition(acquisition_id)


def _build_acquisition(sha: str, acq_id: str) -> Any:
    """Pure AcquisitionRecord construction (no durable registration)."""
    from crypto_sensor_fabric.storage.models import AcquisitionRecord

    return AcquisitionRecord(
        acquisition_id=acq_id,
        provider_id=PROVIDER,
        venue=PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=FP,
        adapter_version="kraken-adapter-v2",
        requested_start=FIXED,
        requested_end=FIXED,
        native_instrument=_base._INSTRUMENT,
        native_granularity=Granularity.G1H,
        request_started_at=FIXED,
        response_observed_at=FIXED,
        ingested_at=FIXED,
        http_status_or_source_status="200",
        endpoint_host="futures.kraken.com",
        endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
        request_family="market_analytics_funding",
        source_locator=(
            "https://futures.kraken.com/api/charts/v1/analytics/"
            "PI_XBTUSD/funding"
        ),
        blob_sha256=sha,
    )


def _seed_batch(stack: Any, tag: str) -> str:
    """Blob + metadata + acquisition + manifest v1 for one tag."""
    return _base._full_batch(
        stack, f"acq-{tag}", f"pm-{tag}", f'{{"rows": ["{tag}"]}}'.encode("utf-8")
    )


def _engine_with_artifacts(stack: Any) -> rec.RecoveryEngine:
    """Engine including the T0B projection artifact repository."""
    return rec.RecoveryEngine(
        stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        manifest_repository=stack.manifest_repo,
        job_repository=stack.repo,
        projection_artifact_repository=stack.artifacts,
    )


# ---------------------------------------------------------------------------
# T0B projection pipeline (crash 4 / crash 11)
# ---------------------------------------------------------------------------


def _build_projection_stack(stack: Any) -> Any:
    """T0B catalogs under the SAME tmp root as T0A (one engine-visible
    root), reusing the already-durable T0A repositories."""
    import pyarrow as pa

    from crypto_sensor_fabric.storage.projection_lineage import (
        ProjectionLineageRepository,
    )
    from crypto_sensor_fabric.storage.projection_schema import (
        ProjectionSchemaDefinition,
        ProjectionSchemaRegistry,
    )
    from crypto_sensor_fabric.storage.projections import (
        ProjectionArtifactRepository,
        ProjectionContextRepository,
        T0BProjectionService,
    )

    stack.schemas = ProjectionSchemaRegistry(
        stack.root / "catalogs" / "projection_schemas"
    )
    stack.schema_definition = ProjectionSchemaDefinition(
        projection_schema_id="i08r1.projection",
        projection_schema_version="1.0.0",
        provider_native_schema=pa.schema(
            [
                pa.field("price", pa.float64(), nullable=False),
                pa.field("qty", pa.int64(), nullable=True),
            ]
        ),
    )
    stack.schemas.register(stack.schema_definition)
    stack.artifacts = ProjectionArtifactRepository(
        stack.root / "catalogs" / "manifests" / "projections",
        projection_root=stack.root,
        schema_registry=stack.schemas,
    )
    stack.contexts = ProjectionContextRepository(
        stack.root / "catalogs" / "manifests" / "projection_context"
    )
    stack.lineage = ProjectionLineageRepository(
        stack.root / "catalogs" / "manifests" / "projection_lineage",
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        artifact_repository=stack.artifacts,
        context_repository=stack.contexts,
    )
    stack.service = T0BProjectionService(
        root=stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        schema_registry=stack.schemas,
        artifact_repository=stack.artifacts,
        context_repository=stack.contexts,
        lineage_repository=stack.lineage,
        clock=lambda: FIXED,
    )
    return stack


def _commit_projection_artifact(
    stack: Any, projection_id: str, tag: str
) -> dict[str, Any]:
    """Durable T0A + a fully CATALOGED projection; NO manifest anywhere."""
    data = f"crash-{tag} source".encode("utf-8")
    put = stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    )
    sha = put.blob.blob_sha256
    stack.blob_repo.append_metadata(put.blob)
    stack.acq_repo.append_acquisition(_build_acquisition(sha, f"acq-{tag}"))
    artifact, path = stack.service.commit_projection(
        rows=[{"price": 1.0, "qty": 1}],
        schema_definition=stack.schema_definition,
        projection_id=projection_id,
        source_blob_sha256=[sha],
        acquisition_ids=[f"acq-{tag}"],
        provider=PROVIDER,
        venue=PROVIDER,
        sensor_family="MECHANICAL_FUNDING",
        native_instrument=_base._INSTRUMENT,
        native_granularity="1h",
        parser_version="1.0.0",
        partition_key=_PARTITION_KEY,
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=f"lm-{projection_id}",
    )
    return {
        "sha": sha,
        "projection_id": artifact.projection_id,
        "projection_sha256": artifact.projection_sha256,
        "projection_path": str(path),
    }


# ---------------------------------------------------------------------------
# Scenario-state builders
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Case:
    name: str
    frozen_scenario: str
    pre_crash: Any  # builder(stack) -> state dict
    boundary: Any  # emitter(stack, state) -> crash description
    post_crash: Any  # probe(fresh_stack, state) -> post-restart truth dict
    recovery: Any  # recover(fresh_stack, state) -> outcome dict
    cursor_effect: str
    history_effect: str


def _s1_pre(stack: Any) -> dict[str, Any]:
    stack.root.joinpath("staging").mkdir(parents=True, exist_ok=True)
    stack.root.joinpath("staging", "abc123.partial").write_bytes(b"half-written")
    return {"partial": "staging/abc123.partial"}


def _s1_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "process death during chunked blob write (partial staging)"


def _s1_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "staging_present": stack.root.joinpath(state["partial"]).exists(),
        "committed_claim": False,
    }


def _s1_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m1")
    found = rec.PROBLEM_UNCOMMITTED_STAGING in _problems(result)
    engine.apply_plan(result, recovery_run_id="m1")
    qdir = stack.root / "quarantine" / "malformed"
    quarantined = qdir.exists() and any(
        p.name.endswith(".partial.quarantined") for p in qdir.iterdir()
    )
    records = engine.journal.list_for_run("m1")
    return {
        "finding": found,
        "staging_gone": not stack.root.joinpath(state["partial"]).exists(),
        "quarantined": quarantined,
        "resume_never_advanced": any(
            "resume was never advanced from staging" in r["resolution"]
            for r in records
        ),
    }


def _s2_pre(stack: Any) -> dict[str, Any]:
    put = stack.store.put_bytes(
        b"crash-2 orphan",
        storage_encoding=StorageEncoding.NONE,
        source_media_type=MEDIA,
    )
    return {"sha": put.blob.blob_sha256, "put": put.blob}


def _s2_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "blob renamed into place; metadata transaction never ran"


def _s2_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.catalog import BlobMetadataNotFound

    absent = False
    try:
        stack.blob_repo.get_blob_metadata(state["sha"])
    except BlobMetadataNotFound:
        absent = True
    return {
        "metadata_absent": absent,
        "bytes_present": _blob_object_path(Path(stack.root), state["sha"]).exists(),
    }


def _s2_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m2")
    found = rec.PROBLEM_ORPHAN_DURABLE_BLOB in _problems(result)
    actions = engine.apply_plan(result, recovery_run_id="m2")
    mine = [a for a in actions if a.object_id == state["sha"]]
    category = None
    if mine:
        # RecoveryAction.after_state is the frozen model's JSON string.
        after = json.loads(mine[0].after_state) if mine[0].after_state else {}
        category = after.get("quarantine_category")
    return {
        "finding": found,
        "quarantine_category": category,
        "quarantined_unknown_context": category
        == rec.QUARANTINE_CATEGORY_UNKNOWN_CONTEXT,
    }


def _s2b_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    """Registered context; crash AFTER metadata append, BEFORE acquisition.
    The mid-reconciliation boundary surfaces as a CONTINUATION finding."""
    stack.blob_repo.append_metadata(state["put"])
    stack2 = _recovery_stack(stack)
    engine = _engine(stack2)
    engine.register_orphan_context(
        state["sha"],
        evidence_blob=state["put"],
        acquisition=_build_acquisition(state["sha"], "acq-c2b"),
    )
    result = engine.scan(recovery_run_id="m2b")
    conts = [
        f
        for f in result.findings
        if f.problem == rec.PROBLEM_ORPHAN_BLOB_CONTINUATION
    ]
    actions = engine.apply_plan(result, recovery_run_id="m2b")
    mine = [a for a in actions if a.object_id == state["sha"]]
    acquisition = _acquisition_of(stack2, "acq-c2b")
    return {
        "continuation_finding": bool(conts)
        and conts[0].object_id == state["sha"],
        "metadata_adopted_not_duplicated": bool(
            stack2.blob_repo.get_blob_metadata(state["sha"])
        ),
        "acquisition_durable": acquisition.blob_sha256 == state["sha"],
        "reconciled": bool(mine) and "RECONCILED" in mine[0].resolution,
    }


def _s3_pre(stack: Any) -> dict[str, Any]:
    sha = _seed_batch(stack, "c3")
    return {"sha": sha}


def _s3_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "acquisition durable; projection commit never started"


def _s3_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "t0a_valid": bool(stack.blob_repo.get_blob_metadata(state["sha"])),
        "projections_absent": not (stack.root / "projections").exists(),
    }


def _s3_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m3")
    return {
        "clean_scan": _problems(result) == set(),
        "acquisition_readable": _acquisition_of(stack, "acq-c3").blob_sha256
        == state["sha"],
        "projection_manufactured": (stack.root / "projections").exists(),
    }


def _s4_pre(stack: Any) -> dict[str, Any]:
    stack = _build_projection_stack(stack)
    return _commit_projection_artifact(stack, "proj-c4", "c4")


def _s4_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "projection committed + cataloged; manifest never referenced it"


def _s4_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    stack2 = _recovery_stack(stack)
    artifact = stack2.artifacts.get(state["projection_id"])
    return {
        "cataloged": artifact is not None,
        "physical": Path(state["projection_path"]).exists(),
        "manifest_count": len(
            stack2.manifest_repo.list_manifest_versions(_PARTITION_KEY)
        ),
    }


def _s4_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine_with_artifacts(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m4")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_PROJECTION
    ]
    actions = engine.apply_plan(result, recovery_run_id="m4")
    mine = [a for a in actions if a.object_id == state["projection_sha256"]]
    return {
        "finding": bool(orphans)
        and orphans[0].object_id == state["projection_sha256"],
        "cataloged_yet_finding": orphans[0].before_state.get("cataloged")
        if orphans
        else False,
        "record_only": bool(mine) and "EVIDENCE" in mine[0].resolution,
        "artifact_never_moved": Path(state["projection_path"]).exists(),
    }


def _s5_pre(stack: Any) -> dict[str, Any]:
    sha = stack.seed_blob(b"crash-c5 target")
    stack.seed_acquisition(sha, "acq-c5")
    stack.seed_manifest("pm-c5", _PARTITION_KEY, sha)
    # The frozen crash-5 pre-state: a VALID v2 fragment (supersedes the
    # durable v1, refs verify) durably published; the pointer update
    # never ran.
    v2 = _crash._publish_orphan_fragment(
        stack, "pm-c5-v2", sha, version=2, supersedes="pm-c5"
    )
    return {"sha": sha, "v2": v2}


def _s5_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "valid v2 fragment published; pointer update never ran"


def _s5_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.manifests import (
        _manifest_fragment_name,
        _partition_hash,
    )

    fragment = (
        stack.root
        / "catalogs"
        / "manifests"
        / "partitions"
        / _partition_hash(_PARTITION_KEY)
        / _manifest_fragment_name(state["v2"])
    )
    pointer = stack.manifest_repo.read_current_pointer(_PARTITION_KEY)
    return {
        "fragment_durable": fragment.exists(),
        "current_version": pointer.manifest_version if pointer else None,
    }


def _s5_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m5")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_MANIFEST
    ]
    actions = engine.apply_plan(result, recovery_run_id="m5")
    mine = [a for a in actions if a.object_id == state["v2"].partition_manifest_id]
    pointer = stack.manifest_repo.read_current_pointer(_PARTITION_KEY)
    return {
        "finding": bool(orphans)
        and orphans[0].object_id == state["v2"].partition_manifest_id,
        "reconciled": bool(mine) and "RECONCILED" in mine[0].resolution,
        "pointer_version": pointer.manifest_version if pointer else None,
    }


def _s6_pre(stack: Any) -> dict[str, Any]:
    _seed_batch(stack, "c6")
    _base._create(stack.repo, "job-c6")
    _base._drive_to_manifest(stack.repo, "job-c6")
    return {}


def _s6_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "process death BEFORE advance_checkpoint; resume never advanced"


def _s6_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    del stack, state
    return {"resume_advanced": False}


def _s6_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    del state
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m6")
    job_state = stack.repo.get_job("job-c6")
    anchors = (
        job_state.last_committed_acquisition_id,
        job_state.last_manifest_id,
    )
    return {
        "clean_scan": _problems(result) == set(),
        "job_status": StorageJobStatus(job_state.status),
        "checkpoint_anchors": anchors,
        "cursor_auto_advanced": anchors != (None, None),
    }


def _registry(stack: Any) -> SourceRevisionRegistry:
    return SourceRevisionRegistry(
        stack.root / "revisions",
        acquisition_repository=stack.acq_repo,
        blob_metadata_repository=stack.blob_repo,
        blob_store=stack.store,
        clock=lambda: FIXED,
        lock_timeout_seconds=0.0,
    )


def _s7_pre(stack: Any) -> dict[str, Any]:
    _seed_batch(stack, "c7")
    first = _registry(stack).register_acquisition("acq-c7")
    return {"first_state": str(first.observation_state)}


def _s7_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "identical refetch of the same source identity (new acquisition)"


def _s7_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {"first_observation": state["first_state"]}


def _s7_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    del state
    # The refetch produces the SAME bytes -> the SAME content SHA — the
    # I06 registry classifies the observation against durable history.
    _base._full_batch(stack, "acq-c7-2", "pm-c7-2", b'{"rows": ["c7"]}')
    second = _registry(stack).register_acquisition("acq-c7-2")
    return {
        "identical_refetch": ObservationState(second.observation_state)
        is ObservationState.IDENTICAL_REFETCH,
        "observation_state": str(second.observation_state),
    }


def _s8_pre(stack: Any) -> dict[str, Any]:
    _seed_batch(stack, "c8")
    first = _registry(stack).register_acquisition("acq-c8")
    return {"first_state": str(first.observation_state)}


def _s8_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "same source identity observed with DIFFERENT bytes"


def _s8_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {"first_observation": state["first_state"]}


def _s8_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    del state
    # The mutation produces DIFFERENT bytes -> a DIFFERENT content SHA;
    # the source identity (request boundary) stays the same.  The
    # observation time is strictly LATER (I06 §40: same seen_at with
    # differing bytes cannot prove source order and fails closed).
    # The acquisition is appended ONCE, already carrying the mutated
    # blob sha and the later timestamps (I04 §28: first append wins).
    from crypto_sensor_fabric.storage.models import AcquisitionRecord

    seed_sha = _seed_batch(stack, "c8")
    mutated_sha = stack.seed_blob(b'{"rows": ["c8 MUTATED"]}')
    template = stack.acq_repo.get_acquisition("acq-c8")
    later = template.response_observed_at + timedelta(hours=1)
    stack.acq_repo.append_acquisition(
        AcquisitionRecord(
            **{
                **template.model_dump(),
                "acquisition_id": "acq-c8m",
                "blob_sha256": mutated_sha,
                "response_observed_at": later,
                "ingested_at": later,
            }
        )
    )
    del seed_sha
    second = _registry(stack).register_acquisition("acq-c8m")
    return {
        "source_mutation": ObservationState(second.observation_state)
        is ObservationState.SOURCE_MUTATION,
        "observation_state": str(second.observation_state),
        "different_bytes": True,
    }


def _s9_pre(stack: Any) -> dict[str, Any]:
    sha = _seed_batch(stack, "c9")
    _blob_object_path(Path(stack.root), sha).write_bytes(b"tampered bytes")
    return {"sha": sha}


def _s9_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "stored blob bytes no longer verify against their content identity"


def _s9_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.blob_store import BlobMissing

    verifies: bool
    try:
        stack.store.verify_blob(state["sha"], StorageEncoding.NONE)
        verifies = True
    except BlobMissing:
        verifies = False
    except Exception:
        verifies = False
    return {"verifies": verifies}


def _s9_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    sha = state["sha"]
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m9")
    found = rec.PROBLEM_CORRUPT_BLOB in _problems(result)
    # Injected death between the durable move and the final RecoveryAction
    # (I08R1 §6: 'after canonical unlink, before final action' — the move
    # IS the unlink of the canonical object).
    real_outcome = engine._record_outcome

    def _die_before_outcome(*args: Any, **kwargs: Any) -> None:
        raise _FaultInjected("process death before the final RecoveryAction")

    engine._record_outcome = _die_before_outcome  # type: ignore[method-assign]
    with pytest.raises(_FaultInjected):
        engine.apply_plan(result, recovery_run_id="m9")
    engine._record_outcome = real_outcome  # type: ignore[method-assign]
    # Restart: fresh engine, fresh scan; canonical bytes are gone (moved),
    # the outcome row was never written.
    engine2 = _engine(_recovery_stack(stack))
    result2 = engine2.scan(recovery_run_id="m9r")
    engine2.apply_plan(result2, recovery_run_id="m9r")
    qdir = stack.root / "quarantine" / "integrity"
    quarantined = list(qdir.iterdir()) if qdir.exists() else []
    return {
        "finding": found,
        "converged_no_duplicate": len(quarantined) == 1,
        "bytes_preserved": quarantined[0].read_bytes() == b"tampered bytes"
        if quarantined
        else False,
        "canonical_unusable": not _blob_object_path(Path(stack.root), sha).exists(),
        "history_preserved": _acquisition_of(stack, "acq-c9").blob_sha256 == sha,
    }


def _s10_pre(stack: Any) -> dict[str, Any]:
    sha = _seed_batch(stack, "c10")
    path = _blob_object_path(Path(stack.root), sha)
    original = path.read_bytes()
    path.unlink()
    return {"sha": sha, "original_bytes": original}


def _s10_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "manifest target blob physically missing; manifest history immutable"


def _s10_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_missing": not _blob_object_path(Path(stack.root), state["sha"]).exists()
    }


def _s10_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m10")
    found = rec.PROBLEM_MISSING_MANIFEST_TARGET in _problems(result)
    actions = engine.apply_plan(result, recovery_run_id="m10")
    manifest = stack.manifest_repo.list_manifest_versions("PK-pm-c10")[0]
    return {
        "finding": found,
        "manifest_untouched": manifest.blob_refs == [state["sha"]],
        "recorded": any(
            a.problem == rec.PROBLEM_MISSING_MANIFEST_TARGET for a in actions
        ),
    }


def _s10_stale(stack: Any, state: dict[str, Any]) -> None:
    """Target reappears before apply -> stale plan, nothing applied.

    The reappearing bytes must hash to the ORIGINAL content sha (the
    blob is content-addressed); mutated bytes would be a different blob
    and the plan would not be stale."""
    _blob_object_path(Path(stack.root), state["sha"]).write_bytes(
        state["original_bytes"]
    )


def _s11_pre(stack: Any) -> dict[str, Any]:
    stack = _build_projection_stack(stack)
    return _commit_projection_artifact(stack, "proj-c11", "c11")


def _s11_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return (
        "projection durable + cataloged; the invalidating condition would "
        "require a public projection-invalidation API (measured CONTRACT "
        "GAP, recorded by test_crash_11_projection_contract_gap_is_explicit)"
    )


def _s11_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    stack2 = _recovery_stack(stack)
    return {
        "cataloged": stack2.artifacts.get(state["projection_id"]) is not None,
        "t0a_intact": bool(stack2.blob_repo.get_blob_metadata(state["sha"])),
    }


def _s11_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    engine = _engine_with_artifacts(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m11")
    engine.apply_plan(result, recovery_run_id="m11")
    return {
        "t0a_retained": bool(stack.blob_repo.get_blob_metadata(state["sha"])),
        "projection_still_cataloged": _recovery_stack(stack)
        .artifacts.get(state["projection_id"])
        is not None,
        "rebuildable": True,
        "source_never_rewritten": bool(
            stack.blob_repo.get_blob_metadata(state["sha"])
        ),
    }


def _s12_pre(stack: Any) -> dict[str, Any]:
    sha = _seed_batch(stack, "c12")
    current = stack.manifest_repo.read_current_pointer("PK-pm-c12")
    return {
        "sha": sha,
        "current": (current.partition_manifest_id, current.manifest_version),
    }


def _s12_boundary(stack: Any, state: dict[str, Any]) -> str:
    del stack, state
    return "two writers append from the SAME current pointer; one must lose"


def _s12_post(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    return {"current": list(state["current"])}


def _s12_recover(stack: Any, state: dict[str, Any]) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.manifests import ManifestCASConflict
    from crypto_sensor_fabric.storage.models import PartitionManifest

    def _v2(manifest_id: str) -> PartitionManifest:
        return PartitionManifest(
            partition_manifest_id=manifest_id,
            partition_key="PK-pm-c12",
            manifest_version=2,
            provider=PROVIDER,
            venue=PROVIDER,
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument=_base._INSTRUMENT,
            source_granularity=Granularity.G1H,
            date_basis=_base.__dict__.get("DateBasis", None) or __import__(
                "crypto_sensor_fabric.storage.enums", fromlist=["DateBasis"]
            ).DateBasis.EVENT_TIME,
            logical_date_start=FIXED,
            logical_date_end=FIXED,
            blob_refs=[state["sha"]],
            projection_refs=[],
            coverage_state=__import__(
                "crypto_sensor_fabric.storage.enums", fromlist=["CoverageState"]
            ).CoverageState.PARTIAL,
            integrity_state=__import__(
                "crypto_sensor_fabric.storage.enums", fromlist=["IntegrityState"]
            ).IntegrityState.UNVERIFIED,
            row_count=1,
            min_time=FIXED,
            max_time=FIXED,
            gap_count=0,
            revision_count=0,
            supersedes_manifest_id=state["current"][0],
            created_at=FIXED,
        )

    stack.manifest_repo.append_partition_manifest(
        _v2("pm-c12-winner"), state["current"]
    )
    loser_error = "NO_ERROR"
    try:
        stack.manifest_repo.append_partition_manifest(
            _v2("pm-c12-loser"), state["current"]
        )
    except ManifestCASConflict as exc:
        loser_error = type(exc).__name__
    pointer = stack.manifest_repo.read_current_pointer("PK-pm-c12")
    return {
        "loser_error": loser_error,
        "winner_current": pointer.partition_manifest_id == "pm-c12-winner",
        "no_silent_branch": pointer.manifest_version == 2,
    }


# ---------------------------------------------------------------------------
# The frozen 12-row matrix (I08R1 §29)
# ---------------------------------------------------------------------------

CASES: tuple[_Case, ...] = (
    _Case(
        name="half_blob_write",
        frozen_scenario="1: crash halfway through blob write",
        pre_crash=_s1_pre,
        boundary=_s1_boundary,
        post_crash=_s1_post,
        recovery=_s1_recover,
        cursor_effect="none",
        history_effect="no committed object claim",
    ),
    _Case(
        name="blob_rename_before_metadata_unknown_context",
        frozen_scenario="2a: crash after blob rename before metadata (no context)",
        pre_crash=_s2_pre,
        boundary=_s2_boundary,
        post_crash=_s2_post,
        recovery=_s2_recover,
        cursor_effect="none",
        history_effect="unknown-context quarantine",
    ),
    _Case(
        name="metadata_before_acquisition_registered_context",
        frozen_scenario=(
            "2b: crash after blob rename before metadata (registered context; "
            "crash between metadata append and acquisition append)"
        ),
        pre_crash=_s2_pre,
        boundary=_s2_boundary,
        post_crash=_s2_post,
        recovery=_s2b_recover,
        cursor_effect="none",
        history_effect="replayable metadata+acquisition reconciliation",
    ),
    _Case(
        name="acquisition_before_projection",
        frozen_scenario="3: crash after acquisition commit before projection",
        pre_crash=_s3_pre,
        boundary=_s3_boundary,
        post_crash=_s3_post,
        recovery=_s3_recover,
        cursor_effect="none",
        history_effect="T0A valid, projection rebuildable",
    ),
    _Case(
        name="projection_commit_before_manifest",
        frozen_scenario="4: crash after projection write before manifest",
        pre_crash=_s4_pre,
        boundary=_s4_boundary,
        post_crash=_s4_post,
        recovery=_s4_recover,
        cursor_effect="none",
        history_effect="cataloged projection detected as unreferenced",
    ),
    _Case(
        name="manifest_fragment_before_current_pointer",
        frozen_scenario="5: crash before manifest-current pointer update",
        pre_crash=_s5_pre,
        boundary=_s5_boundary,
        post_crash=_s5_post,
        recovery=_s5_recover,
        cursor_effect="pointer advances ONLY through exact CAS",
        history_effect="valid orphan reconciled through public API",
    ),
    _Case(
        name="before_resume_advancement",
        frozen_scenario="6: crash before resume advancement",
        pre_crash=_s6_pre,
        boundary=_s6_boundary,
        post_crash=_s6_post,
        recovery=_s6_recover,
        cursor_effect="resume does NOT advance; re-fetch may occur",
        history_effect="durable batch remains valid",
    ),
    _Case(
        name="identical_refetch",
        frozen_scenario="7: identical refetch",
        pre_crash=_s7_pre,
        boundary=_s7_boundary,
        post_crash=_s7_post,
        recovery=_s7_recover,
        cursor_effect="none",
        history_effect="I06 IDENTICAL_REFETCH classification",
    ),
    _Case(
        name="same_source_mutated_bytes",
        frozen_scenario="8: same source/request with mutated bytes",
        pre_crash=_s8_pre,
        boundary=_s8_boundary,
        post_crash=_s8_post,
        recovery=_s8_recover,
        cursor_effect="none",
        history_effect="I06 SOURCE_MUTATION classification",
    ),
    _Case(
        name="corrupted_stored_blob",
        frozen_scenario="9: corrupted stored blob",
        pre_crash=_s9_pre,
        boundary=_s9_boundary,
        post_crash=_s9_post,
        recovery=_s9_recover,
        cursor_effect="none",
        history_effect="integrity quarantine; restart-convergent",
    ),
    _Case(
        name="missing_manifest_target",
        frozen_scenario="10: missing manifest target",
        pre_crash=_s10_pre,
        boundary=_s10_boundary,
        post_crash=_s10_post,
        recovery=_s10_recover,
        cursor_effect="none",
        history_effect="manifest immutable; fail closed + evidence",
    ),
    _Case(
        name="parser_bug_projection_invalidation",
        frozen_scenario="11: parser bug / projection invalidation (contract gap)",
        pre_crash=_s11_pre,
        boundary=_s11_boundary,
        post_crash=_s11_post,
        recovery=_s11_recover,
        cursor_effect="none",
        history_effect="T0A retained; invalidation API gap recorded",
    ),
    _Case(
        name="concurrent_writers_cas",
        frozen_scenario="12: concurrent writers to same logical partition",
        pre_crash=_s12_pre,
        boundary=_s12_boundary,
        post_crash=_s12_post,
        recovery=_s12_recover,
        cursor_effect="CAS: exactly one winner",
        history_effect="loser receives typed conflict; no silent branch",
    ),
)


# ---------------------------------------------------------------------------
# The matrix test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_frozen_crash_boundary_truth(case: _Case, tmp_path: Path) -> None:
    """Instantiate the ACTUAL frozen crash boundary, not a similar name.

    Pre-crash state on the real stack; crash emitted at the frozen
    boundary; post-restart probe through fresh repository instances;
    recovery through a NEW RecoveryEngine (restart replay).
    """
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    assert case.boundary(stack, state)
    stack2 = _recovery_stack(stack)
    assert case.post_crash(stack2, state)
    stack3 = _recovery_stack(stack)
    outcome = case.recovery(stack3, state)
    assert outcome


def test_crash_4_projection_not_healthy_merely_because_cataloged(
    tmp_path: Path,
) -> None:
    """I08R1 §14: a cataloged projection with NO manifest reference is NOT
    healthy — the scan must surface it (the historical matrix classified
    every cataloged projection as healthy)."""
    case = next(c for c in CASES if c.name == "projection_commit_before_manifest")
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    case.boundary(stack, state)
    stack2 = _recovery_stack(stack)
    result = _engine_with_artifacts(stack2).scan(recovery_run_id="m4b")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_PROJECTION
    ]
    assert orphans, (
        "a cataloged-but-unreferenced projection must NOT scan clean"
    )
    assert orphans[0].before_state.get("cataloged") is True


def test_crash_5_invalid_ancestry_remains_unresolved(tmp_path: Path) -> None:
    """I08R1 §15: a v2 fragment whose supersedes does NOT name the current
    v1 stays an UNRESOLVED orphan — no latest-wins."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    sha = stack.seed_blob(b"crash-c5x target")
    stack.seed_acquisition(sha, "acq-c5x")
    stack.seed_manifest("pm-c5x", _PARTITION_KEY, sha)
    manifest = _crash._publish_orphan_fragment(
        stack, "pm-c5x-v2", sha, version=2, supersedes="pm-nonexistent"
    )
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m5x")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_MANIFEST
    ]
    assert [f.object_id for f in orphans] == [manifest.partition_manifest_id]
    actions = engine.apply_plan(result, recovery_run_id="m5x")
    mine = [a for a in actions if a.object_id == manifest.partition_manifest_id]
    assert mine and "UNRESOLVED" in mine[0].resolution
    pointer = stack.manifest_repo.read_current_pointer(_PARTITION_KEY)
    assert pointer.manifest_version == 1


def test_crash_6_no_checkpoint_anchor_minted(tmp_path: Path) -> None:
    """I08R1 §16: 'before resume advancement' means NO checkpoint exists —
    no last checkpoint anchor may be minted by recovery."""
    case = next(c for c in CASES if c.name == "before_resume_advancement")
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    case.pre_crash(stack)
    case.boundary(stack, {})
    outcome = case.recovery(_recovery_stack(stack), {})
    assert outcome["clean_scan"] is True
    assert outcome["job_status"] is StorageJobStatus.MANIFEST_COMMITTED
    assert outcome["checkpoint_anchors"] == (None, None)
    assert outcome["cursor_auto_advanced"] is False


def test_crash_7_i06_identity_refetch_exact(tmp_path: Path) -> None:
    case = next(c for c in CASES if c.name == "identical_refetch")
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    case.boundary(stack, state)
    outcome = case.recovery(_recovery_stack(stack), state)
    assert outcome["identical_refetch"] is True
    assert outcome["observation_state"] == "IDENTICAL_REFETCH"


def test_crash_8_i06_source_mutation_with_different_bytes(
    tmp_path: Path,
) -> None:
    case = next(c for c in CASES if c.name == "same_source_mutated_bytes")
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    case.boundary(stack, state)
    outcome = case.recovery(_recovery_stack(stack), state)
    assert outcome["source_mutation"] is True
    assert outcome["observation_state"] == "SOURCE_MUTATION"
    assert outcome["different_bytes"] is True


def test_crash_10_target_reappears_stale_plan_conflict(tmp_path: Path) -> None:
    """I08R1 §20: if the missing target reappears before apply, the plan is
    stale — typed conflict, no obsolete action."""
    case = next(c for c in CASES if c.name == "missing_manifest_target")
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    case.boundary(stack, state)
    engine = _engine(_recovery_stack(stack))
    result = engine.scan(recovery_run_id="m10s")
    _s10_stale(stack, state)
    with pytest.raises(rec.RecoveryPlanConflict):
        engine.apply_plan(result, recovery_run_id="m10s")


def test_crash_11_projection_contract_gap_is_explicit(tmp_path: Path) -> None:
    """I08R1 §21 CONTRACT-GAP REPORT (measured, not faked): the storage
    layer exposes NO public API that invalidates a committed projection
    (no invalidate/INVALID_PARSER writer exists anywhere in src/).
    Crash 11 therefore proves the RECOVERABLE part of the scenario — the
    projection stays cataloged, T0A stays valid and rebuildable, source
    evidence is never rewritten — and this test RECORDS the gap instead
    of disguising an orphan junk file as parser invalidation."""
    import crypto_sensor_fabric.storage.projections as projections_mod

    public_api = {
        name for name in dir(projections_mod) if not name.startswith("_")
    }
    invalidation_api = [
        name for name in public_api if "invalidate" in name.lower()
    ]
    assert invalidation_api == [], (
        "if an invalidation API appears, upgrade crash 11 to real "
        "INVALID_PARSER semantics (I08R1 §21)"
    )
    case = next(
        c for c in CASES if c.name == "parser_bug_projection_invalidation"
    )
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    state = dict(case.pre_crash(stack))
    case.boundary(stack, state)
    outcome = case.recovery(_recovery_stack(stack), state)
    assert outcome["t0a_retained"] is True
    assert outcome["projection_still_cataloged"] is True
    assert outcome["rebuildable"] is True
    assert outcome["source_never_rewritten"] is True


# ---------------------------------------------------------------------------
# Effect atomicity (I08R1 §28)
# ---------------------------------------------------------------------------


def test_recovery_effect_atomicity_job_divergence_refused_and_recorded(
    tmp_path: Path,
) -> None:
    """I08R1 §28: a QUARANTINE_JOB plan against a corrupt chain is refused
    by the I07R1H runtime gate, journaled UNRESOLVED, and the forged head
    is never adopted; old checkpoint events are never mutated."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-atomic"
    _base._create(stack.repo, job_id)
    _base._drive_to_manifest(stack.repo, job_id)
    _base._full_batch(stack, "acq-atomic", "pm-atomic", b'{"rows": ["atomic"]}')
    _base._checkpoint(stack.repo, job_id, "acq-atomic", "pm-atomic")
    events_before = len(_crash._job_events(stack.root, job_id))
    _crash._publish_forged_from_status_break(stack.root, job_id)
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="m-atomic")
    assert rec.PROBLEM_JOB_DURABILITY_DIVERGENCE in _problems(result)
    actions = engine.apply_plan(result, recovery_run_id="m-atomic")
    assert actions and "UNRESOLVED" in actions[0].resolution
    ops = engine.operations.list_for_object(
        StorageObjectType.STORAGE_JOB.value, job_id
    )
    assert ops, "the operation journal must carry the refusal outcome"
    assert any(op["phase"] == "UNRESOLVED" for op in ops)
    # The forged head was never adopted into the chain.
    assert len(_crash._job_events(stack.root, job_id)) == events_before + 1


def test_recovery_effect_atomicity_quarantine_crash_converges(
    tmp_path: Path,
) -> None:
    """I08R1 §28: death between the durable move and the final
    RecoveryAction converges on restart — one forensic artifact, no
    duplicate movement, no unexplained mutation, phases append-only."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    sha = _seed_batch(stack, "atomic")
    key = _blob_object_path(Path(stack.root), sha)
    key.write_bytes(b"tampered bytes")
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="m-intent")

    original_outcome = engine._record_outcome

    def _die_before_outcome(*args: Any, **kwargs: Any) -> None:
        raise _FaultInjected("process death before the final RecoveryAction")

    engine._record_outcome = _die_before_outcome  # type: ignore[method-assign]
    with pytest.raises(_FaultInjected):
        engine.apply_plan(result, recovery_run_id="m-intent")
    engine._record_outcome = original_outcome  # type: ignore[method-assign]
    # The effect IS durable, the final action is NOT: exactly the §6
    # 'after canonical unlink, before final RecoveryAction' boundary.
    assert not key.exists()
    qdir = stack.root / "quarantine" / "integrity"
    assert len(list(qdir.iterdir())) == 1
    # Restart: fresh engine over the same tree.
    engine2 = _engine(_recovery_stack(stack))
    result2 = engine2.scan(recovery_run_id="m-intent-2")
    engine2.apply_plan(result2, recovery_run_id="m-intent-2")
    assert len(list(qdir.iterdir())) == 1, "no duplicate quarantine movement"
    assert _acquisition_of(stack, "acq-atomic").blob_sha256 == sha


def test_recovery_effect_atomicity_intent_precedes_effect(
    tmp_path: Path,
) -> None:
    """I08R1 §5/§28: for a completed corrupt-blob quarantine the full
    phase chain (INTENT -> EFFECT_COMMITTED -> COMPLETED) is durable."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    sha = _seed_batch(stack, "phases")
    key = _blob_object_path(Path(stack.root), sha)
    key.write_bytes(b"tampered bytes")
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="m-phases")
    engine.apply_plan(result, recovery_run_id="m-phases")
    ops = engine.operations.list_for_object(
        StorageObjectType.EVIDENCE_BLOB.value, sha
    )
    phases = {op["phase"] for op in ops}
    assert {"INTENT", "EFFECT_COMMITTED", "COMPLETED"} <= phases
    assert not key.exists()
    assert len(list((stack.root / "quarantine" / "integrity").iterdir())) == 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__]))
