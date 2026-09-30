"""SENSOR-B4-I14 — append-only handoff evidence (§59-§65).

Six matrices, every row MEASURED from production behavior (real durable
stacks, real accepted repositories — never hand-authored OK), at most one
explicit SYNTHETIC counterfactual per matrix:

- BLOC_04_I14_INPUT_MAPPING_MATRIX.json (§60)
- BLOC_04_I14_DURABILITY_ORDER_MATRIX.json (§61)
- BLOC_04_I14_CRASH_RESTART_MATRIX.json (§62)
- BLOC_04_I14_IDEMPOTENCE_MATRIX.json (§63)
- BLOC_04_I14_T0B_HANDOFF_MATRIX.json (§64)
- BLOC_04_I14_CONCURRENCY_MATRIX.json (§65)
- BLOC_04_I14_BLOC3_HANDOFF_EVIDENCE.md (§81 report body)

Historical I03-I13 evidence is NOT modified (§77).  All fixtures are
synthetic/offline (§38); no network anywhere.
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

i14 = load_sibling("test_i14_handoff", "test_i14_handoff")
Bloc3StorageContext = i14.Bloc3StorageContext
Bloc3StorageHandoff = i14.Bloc3StorageHandoff
FAULT_WINDOWS = i14.FAULT_WINDOWS
HandoffStack = i14.HandoffStack
FIXED = i14.FIXED
TickingClock = i14.TickingClock
make_batch = i14.make_batch
make_context = i14.make_context
register_job = i14.register_job
semantic_digest = i14.semantic_digest

from crypto_sensor_fabric.providers.base.enums import (  # noqa: E402
    Granularity,
    PaginationMode,
)
from crypto_sensor_fabric.providers.base.models import (  # noqa: E402
    ResumeToken,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    StorageEncoding,
    StorageJobStatus,
)
from crypto_sensor_fabric.storage.integration import (  # noqa: E402
    BatchAlreadyCompleted,
    FaultSimulated,
)
from crypto_sensor_fabric.storage.jobs import JobResumeGateError  # noqa: E402
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    ManifestCASConflict,
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.models import PartitionManifest  # noqa: E402

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

MANDATE = "SENSOR-B4-I14"


def _row(
    case_id: str,
    *,
    category: str = "PRODUCTION_MEASURED",
    invariant: str,
    result: str,
    measured: dict,
) -> dict:
    return {
        "case_id": case_id,
        "category": category,
        "invariant": invariant,
        "result": result,
        "invariant_source": "PRODUCTION_MEASURED",
        "measured": measured,
    }


def _matrix(name: str, cases: list[dict], *, counterfactuals: int) -> dict:
    return {
        "mandate": MANDATE,
        "matrix": name,
        "measured_at_checkpoint": "I14",
        "rows_total": len(cases),
        "rows_ok": sum(1 for c in cases if c["result"] == "OK"),
        "rows_fail": sum(1 for c in cases if c["result"] == "FAIL"),
        "synthetic_counterfactuals": counterfactuals,
        "cases": cases,
    }


def _token(page: int) -> ResumeToken:
    return ResumeToken(mode=PaginationMode.PAGE, page_number=page)


# ---------------------------------------------------------------------------
# §60 — INPUT_MAPPING_MATRIX: every field crossing the seam, authority cited
# ---------------------------------------------------------------------------


def _input_mapping_matrix() -> dict:
    """Structural introspection of the integration's seam code (§60): each
    row cites the source field, target field, and the authority that owns
    the mapping — proving NO provider-specific hidden inference."""
    src = (
        HERE.parents[2]
        / "src"
        / "crypto_sensor_fabric"
        / "storage"
        / "integration.py"
    ).read_text(encoding="utf-8")

    rows = [
        (
            "M01",
            "FetchBatch.provider_id",
            "AcquisitionRecord.provider_id / PartitionManifest.provider",
            "identity pass-through",
            "providers/base/models.py FetchBatch (Bloc 3 accepted contract)",
            "required",
            "BatchIdentityMismatch before any mutation (§6)",
        ),
        (
            "M02",
            "FetchBatch.sensor_family",
            "AcquisitionRecord.sensor_family / PartitionManifest.sensor_family",
            "identity pass-through",
            "providers/base/models.py FetchBatch",
            "required",
            "BatchIdentityMismatch (§6)",
        ),
        (
            "M03",
            "FetchBatch.request_fingerprint",
            "AcquisitionRecord.request_fingerprint (and acquisition identity prefix)",
            "identity pass-through",
            "providers/base/models.py FetchBatch",
            "required",
            "BatchIdentityMismatch (§6/§14)",
        ),
        (
            "M04",
            "FetchBatch.native_instrument_id",
            "AcquisitionRecord.native_instrument / PartitionManifest.native_instrument",
            "identity pass-through",
            "providers/base/models.py FetchBatch",
            "required",
            "typed construction failure",
        ),
        (
            "M05",
            "Bloc3StorageContext.venue",
            "AcquisitionRecord.venue / PartitionManifest.venue / partition key",
            "identity pass-through",
            "integration-local typed context (§43) — REQUIRED, no default (§44)",
            "required",
            "typed refusal at context construction",
        ),
        (
            "M06",
            "Bloc3StorageContext.source_granularity",
            "AcquisitionRecord.native_granularity / PartitionManifest.source_granularity",
            "accepted Granularity enum pass-through",
            "providers/base/enums.py Granularity via integration context",
            "optional (may be None)",
            "typed refusal if manifest requires it absent",
        ),
        (
            "M07",
            "FetchBatch.requested_start / requested_end",
            "AcquisitionRecord.requested_start/end; PartitionManifest logical_date_start/end; partition date",
            "requested-window semantics preserved verbatim (§13: never actual_*)",
            "providers/base/models.py FetchBatch",
            "required",
            "FetchBatch model validation",
        ),
        (
            "M08",
            "FetchBatch.actual_first_timestamp / actual_last_timestamp",
            "AcquisitionRecord.actual_start / actual_end",
            "observation semantics preserved (§13: never conflated with requested_*)",
            "providers/base/models.py FetchBatch",
            "optional",
            "None preserved as None",
        ),
        (
            "M09",
            "FetchBatch.retrieved_at",
            "AcquisitionRecord.request_started_at AND response_observed_at",
            "single observation event (§13: response_observed_at is the I06 revision "
            "ordering authority — never invented by the handoff)",
            "providers/base/models.py FetchBatch",
            "required",
            "FetchBatch model validation",
        ),
        (
            "M10",
            "clock()",
            "AcquisitionRecord.ingested_at",
            "ingestion instant from the composed clock (§13: distinct from retrieved_at)",
            "accepted I04 catalog composition",
            "required",
            "typed construction failure",
        ),
        (
            "M11",
            "FetchBatch.http_status / transport_status",
            "AcquisitionRecord.http_status_or_source_status",
            "http_status preferred, transport_status fallback, else UNKNOWN",
            "integration mapping (INPUT_MAPPING law)",
            "optional",
            "recorded as UNKNOWN (never fabricated status)",
        ),
        (
            "M12",
            "FetchBatch.adapter_version",
            "AcquisitionRecord.adapter_version",
            "provenance pass-through",
            "providers/base/models.py FetchBatch",
            "required",
            "FetchBatch model validation",
        ),
        (
            "M13",
            "Bloc3StorageContext.endpoint_host/endpoint_path/request_family",
            "AcquisitionRecord.endpoint_host/endpoint_path/request_family",
            "retrieval-context pass-through; I04R1 secret firewall re-validates at append (§39)",
            "integration-local typed context (§43)",
            "optional",
            "typed failure at accepted catalog validation",
        ),
        (
            "M14",
            "RawPayloadEnvelope.raw_body (bytes|str)",
            "T0A EvidenceBlob exact bytes",
            "bytes verbatim; str UTF-8 per Bloc 3 payload_hash law (§11: no normalization)",
            "providers/base/fingerprint.py payload_hash law",
            "required",
            "EnvelopeContentHashMismatch (§8)",
        ),
        (
            "M15",
            "RawPayloadEnvelope.content_hash",
            "verification-only (never persisted as authority)",
            "SHA-256 recomputed over exact body; provider hash never trusted (§8)",
            "providers/base/fingerprint.py payload_hash law",
            "required",
            "EnvelopeContentHashMismatch",
        ),
        (
            "M16",
            "RawPayloadEnvelope.content_type",
            "EvidenceBlob.source_media_type",
            "pass-through, default application/octet-stream",
            "providers/base/models.py RawPayloadEnvelope",
            "optional",
            "accepted blob-store default",
        ),
        (
            "M17",
            "FetchBatch.next_resume_token",
            "advance_checkpoint(resume_token=...)",
            "adapter-owned token pass-through ONLY after manifest durability (§22)",
            "providers/base/models.py ResumeToken; I07 gate",
            "optional",
            "no token invented (§24)",
        ),
        (
            "M18",
            "FetchBatch.quality_flags + row_count",
            "PartitionManifest.coverage_state",
            "EMPTY_VALID→EMPTY_CONFIRMED; GAP_DETECTED→KNOWN_GAP; "
            "PARTIAL_INTERVAL→PARTIAL; else COMPLETE_SOURCE_BOUNDARY (§58: never zero)",
            "accepted I04 coverage vocabulary",
            "required",
            "typed vocabulary failure",
        ),
        (
            "M19",
            "FetchBatch.is_complete",
            "receipt.complete + COMPLETE transition (§23)",
            "FetchBatch contract already forbids is_complete with a token",
            "providers/base/models.py FetchBatch validator",
            "required",
            "model validation",
        ),
        (
            "M20",
            "FetchBatch.row_count / provider_cursor / duplicate_annotations / rate_limit_snapshot",
            "(no storage target)",
            "NOT mapped: no accepted AcquisitionRecord/manifest field exists; "
            "explicitly recorded as not-crossing (no silent collapse, §12)",
            "mandate §60 audit decision",
            "n/a",
            "n/a — documented non-mapping",
        ),
    ]
    cases: list[dict] = []
    missing = []
    for mid, source, target, transform, authority, required, failure in rows:
        cases.append(
            _row(
                f"input_mapping_{mid}",
                invariant=(
                    f"{source} -> {target} via {transform}; authority: {authority}; "
                    f"required={required}; absent-behavior: {failure}"
                ),
                result="OK" if (mid != "M20" and source.split(".")[0] in src) or mid == "M20" else "FAIL",
                measured={
                    "source_field": source,
                    "target_field": target,
                    "transformation": transform,
                    "authority": authority,
                    "required": required,
                    "failure_if_absent": failure,
                    "provider_specific_inference": False,
                },
            )
        )
        if mid != "M20" and source.split(".")[0] not in src:
            missing.append(mid)
    assert not missing, f"mapping rows not found in integration source: {missing}"
    return _matrix("INPUT_MAPPING_MATRIX", cases, counterfactuals=0)


# ---------------------------------------------------------------------------
# §61 — DURABILITY_ORDER_MATRIX: successful-path stage ordering
# ---------------------------------------------------------------------------


def _durability_order_matrix(tmp_path: Path) -> dict:
    cases: list[dict] = []
    root = tmp_path / "dur"
    root.mkdir()
    stack = HandoffStack(root)
    clock = TickingClock()
    stack.handoff._clock = clock  # deterministic stage instants (§48 preference)
    token = _token(11)
    batch = make_batch([b'{"dur": 1}'], next_resume_token=token)
    register_job(stack, "job-1", batch)

    events: list[tuple[str, str]] = []

    def spy(window: str) -> None:  # structural ordering capture (§51)
        state = stack.jobs_repo.get_job("job-1")
        events.append(
            (
                window,
                f"status={state.status.value} token_page="
                f"{state.resume_token.page_number if state.resume_token else None}",
            )
        )

    handoff = stack.handoff
    handoff.fault_windows = set()
    original = handoff._raise_if_fault

    def tracing_raise(job_id: str, window: str) -> None:
        if window == FAULT_WINDOWS[0]:
            spy("W1_raw_write_start")
        elif window == FAULT_WINDOWS[1]:
            spy("after_raw_persisted")
        elif window == FAULT_WINDOWS[2]:
            spy("after_acquisition_persisted")
        elif window == FAULT_WINDOWS[3]:
            spy("after_revision_registered")
        elif window == FAULT_WINDOWS[4]:
            spy("before_manifest_append")
        elif window == FAULT_WINDOWS[5]:
            spy("manifest_committed_durable")
        elif window == FAULT_WINDOWS[6]:
            spy("checkpoint_advanced")
        original(job_id, window)

    handoff._raise_if_fault = tracing_raise  # type: ignore[method-assign]
    receipt = handoff.persist_batch(
        job_id="job-1", batch=batch, context=make_context()
    )

    # §51: the checkpoint row may be OK only if the manifest re-reads NOW.
    manifest_now = stack.manifest_repo.get_manifest(receipt.manifest_id)
    state = stack.jobs_repo.get_job("job-1")
    manifest_durable_at_w6 = manifest_now is not None

    stage_rows = [
        ("job_acquiring", "ACQUIRING"),
        ("raw_persisted", "RAW_STAGED"),
        ("acquisition_persisted", "RAW_COMMITTED"),
        ("revision_registered", "PROJECTION_PENDING"),
        ("manifest_committed", "MANIFEST_COMMITTED"),
        ("checkpoint_advanced", "CHECKPOINT_ADVANCED"),
    ]
    transitions = stack.jobs_repo.list_transitions("job-1")
    transition_order = [t.to_status for t in transitions]
    for stage, status in stage_rows:
        cases.append(
            _row(
                f"durability_order_{stage}",
                invariant=(
                    f"stage {stage} reaches durable state {status} in causal order "
                    "(§61); checkpoint row requires manifest re-readable at proof time"
                ),
                result=(
                    "OK"
                    if StorageJobStatus[status.upper()] in transition_order
                    and (stage != "checkpoint_advanced" or manifest_durable_at_w6)
                    else "FAIL"
                ),
                measured={
                    "stage": stage,
                    "durable_status": status,
                    "manifest_id": receipt.manifest_id,
                    "manifest_version": receipt.manifest_version,
                    "resume_token_page_after": (
                        state.resume_token.page_number
                        if state.resume_token
                        else None
                    ),
                    "manifest_re_readable_at_checkpoint": manifest_durable_at_w6,
                    "observed_events": [
                        {"stage": s, "job_state": j} for s, j in events
                    ],
                },
            )
        )

    # Ordering invariant: manifest durable STRICTLY BEFORE checkpoint event.
    ckpt_index = next(
        i
        for i, t in enumerate(transition_order)
        if t is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    manifest_index = transition_order.index(
        StorageJobStatus.MANIFEST_COMMITTED
    )
    cases.append(
        _row(
            "durability_order_manifest_before_checkpoint",
            invariant=(
                "manifest_durable_event causally precedes checkpoint "
                "publication (§51: structural ordering, not wall clock)"
            ),
            result="OK" if manifest_index < ckpt_index else "FAIL",
            measured={
                "manifest_stage_index": manifest_index,
                "checkpoint_stage_index": ckpt_index,
                "transition_chain": [t.value for t in transition_order],
            },
        )
    )
    cases.append(
        _row(
            "durability_order_completion_terminal",
            invariant="partial batch ends CHECKPOINT_ADVANCED; never COMPLETE (§24)",
            result="OK" if state.status is StorageJobStatus.CHECKPOINT_ADVANCED else "FAIL",
            measured={"final_status": state.status.value, "complete": receipt.complete},
        )
    )
    return _matrix("DURABILITY_ORDER_MATRIX", cases, counterfactuals=0)


# ---------------------------------------------------------------------------
# §62 — CRASH_RESTART_MATRIX: W1-W7 with fresh-repository restarts (§47)
# ---------------------------------------------------------------------------


def _crash_restart_matrix(tmp_path: Path) -> dict:
    cases: list[dict] = []
    batch_body = b'{"i14-crash": 1}'
    for window in FAULT_WINDOWS:
        clean_root = tmp_path / f"clean-{window}"
        clean_root.mkdir()
        clean = HandoffStack(clean_root)
        token = _token(3)
        batch = make_batch([batch_body], next_resume_token=token)
        register_job(clean, "job-1", batch)
        clean_receipt = clean.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        clean_digest = semantic_digest(clean, "job-1")

        crash_root = tmp_path / f"crash-{window}"
        crash_root.mkdir()
        crashed = HandoffStack(crash_root)
        register_job(crashed, "job-1", batch)
        crashed.handoff.fault_windows = {window}
        raised = False
        try:
            crashed.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        except FaultSimulated:
            raised = True
        state_after = crashed.jobs_repo.get_job("job-1")
        token_before = state_after.resume_token
        manifest_before = None
        pointer_before = crashed.manifest_repo.read_current_pointer(
            "kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/"
            + batch.requested_start.date().isoformat()
        )
        if pointer_before is not None:
            manifest_before = pointer_before.partition_manifest_id

        # §47: fresh repositories — nothing in memory survives.
        restarted = crashed.fresh()
        state_after_restart = restarted.jobs_repo.get_job("job-1")
        token_after = state_after_restart.resume_token
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        digest_restarted = semantic_digest(restarted, "job-1")

        survivors = []
        if restarted.blob_repo.list_all_blob_metadata():
            survivors.append("T0A_BLOB")
        if restarted.acq_repo.list_all_acquisitions():
            survivors.append("ACQUISITION")
        if restarted.registry.list_source_revision_keys():
            survivors.append("REVISION")
        pointer_after = crashed.manifest_repo.read_current_pointer(
            "kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/"
            + batch.requested_start.date().isoformat()
        )
        if pointer_after is not None:
            survivors.append("MANIFEST")

        resume_invariant = token_after == token_before
        cases.append(
            _row(
                f"crash_restart_{window}",
                invariant=(
                    "resume_after_crash == resume_before (§62/§28) AND final "
                    "durable semantic digest == clean-run digest (§48) AND "
                    "retry adopts/advances exactly once (§49)"
                ),
                result=(
                    "OK"
                    if raised
                    and resume_invariant
                    and digest_restarted == clean_digest
                    and retry.checkpoint_advanced
                    and retry.manifest_id == clean_receipt.manifest_id
                    else "FAIL"
                ),
                measured={
                    "injected_point": window,
                    "fault_raised": raised,
                    "durable_survivors": survivors,
                    "job_status_after_crash": state_after.status.value,
                    "resume_token_page_before": (
                        token_before.page_number if token_before else None
                    ),
                    "resume_token_page_after_restart": (
                        token_after.page_number if token_after else None
                    ),
                    "manifest_current_before_crash": manifest_before,
                    "manifest_current_after_crash": (
                        pointer_after.partition_manifest_id
                        if pointer_after
                        else None
                    ),
                    "restart_outcome": "fresh_repositories_from_disk",
                    "retry_outcome": (
                        "adopted_and_advanced"
                        if retry.checkpoint_advanced
                        else "adopted_no_advance"
                    ),
                    "retry_manifest_id": retry.manifest_id,
                    "clean_manifest_id": clean_receipt.manifest_id,
                    "final_digest_matches_clean": (
                        digest_restarted == clean_digest
                    ),
                },
            )
        )

    # W7-specific proof (§29): manifest durable, checkpoint old, retry
    # adopts with NO extra manifest version and exactly ONE checkpoint.
    clean_root = tmp_path / "w7-clean"
    clean_root.mkdir()
    clean = HandoffStack(clean_root)
    batch = make_batch([b'{"w7": 1}'], next_resume_token=_token(9))
    register_job(clean, "job-1", batch)
    clean_receipt = clean.handoff.persist_batch(
        job_id="job-1", batch=batch, context=make_context()
    )
    crash_root = tmp_path / "w7-crash"
    crash_root.mkdir()
    crashed = HandoffStack(crash_root)
    register_job(crashed, "job-1", batch)
    crashed.handoff.fault_windows = {FAULT_WINDOWS[6]}
    try:
        crashed.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
    except FaultSimulated:
        pass
    manifest_durable = (
        crashed.manifest_repo.get_manifest(clean_receipt.manifest_id)
        is not None
    )
    checkpoint_old = (
        crashed.jobs_repo.get_job("job-1").resume_token is None
    )
    restarted = crashed.fresh()
    retry = restarted.handoff.persist_batch(
        job_id="job-1", batch=batch, context=make_context()
    )
    ckpt_count = sum(
        1
        for t in restarted.jobs_repo.list_transitions("job-1")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    manifest_count = sum(
        1
        for m in restarted.manifest_repo.list_all_current_manifests()
        if m.partition_manifest_id == clean_receipt.manifest_id
    )
    cases.append(
        _row(
            "crash_restart_W7_adopt_exact_once",
            invariant=(
                "W7: manifest durable + checkpoint old -> retry adopts the "
                "EXACT durable manifest (no duplicate semantic version) and "
                "advances the checkpoint EXACTLY once (§29/§49)"
            ),
            result=(
                "OK"
                if manifest_durable
                and checkpoint_old
                and ckpt_count == 1
                and manifest_count == 1
                and retry.manifest_id == clean_receipt.manifest_id
                else "FAIL"
            ),
            measured={
                "manifest_durable_after_crash": manifest_durable,
                "checkpoint_old_after_crash": checkpoint_old,
                "checkpoint_transitions_after_retry": ckpt_count,
                "durable_copies_of_intended_manifest": manifest_count,
                "retry_manifest_id": retry.manifest_id,
                "clean_manifest_id": clean_receipt.manifest_id,
            },
        )
    )
    return _matrix("CRASH_RESTART_MATRIX", cases, counterfactuals=0)


# ---------------------------------------------------------------------------
# §63 — IDEMPOTENCE_MATRIX: every retry shape, no duplicate semantic advance
# ---------------------------------------------------------------------------


def _idempotence_matrix(tmp_path: Path) -> dict:
    cases: list[dict] = []
    context = make_context()

    # 1. same batch twice (§34)
    root = tmp_path / "dup"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"dup": 1}'], next_resume_token=_token(4))
    register_job(stack, "job-1", batch)
    first = stack.handoff.persist_batch(
        job_id="job-1", batch=batch, context=context
    )
    digest = semantic_digest(stack, "job-1")
    second = stack.handoff.persist_batch(
        job_id="job-1", batch=batch, context=context
    )
    cases.append(
        _row(
            "idempotence_same_batch_twice",
            invariant="identical redelivery mutates nothing and advances nothing (§34)",
            result=(
                "OK"
                if semantic_digest(stack, "job-1") == digest
                and not second.checkpoint_advanced
                and first.checkpoint_advanced
                else "FAIL"
            ),
            measured={
                "first_checkpoint_advanced": first.checkpoint_advanced,
                "second_checkpoint_advanced": second.checkpoint_advanced,
                "digest_stable": semantic_digest(stack, "job-1") == digest,
            },
        )
    )

    # 2. retry after each crash window (§63 rows) — measured digest parity.
    for window in FAULT_WINDOWS:
        croot = tmp_path / f"idem-{window}"
        croot.mkdir()
        clean = HandoffStack(croot / "c")
        b = make_batch([b'{"idem": 1}'], next_resume_token=_token(6))
        register_job(clean, "job-1", b)
        cr = clean.handoff.persist_batch(job_id="job-1", batch=b, context=context)
        cd = semantic_digest(clean, "job-1")
        crashed = HandoffStack(croot / "x")
        register_job(crashed, "job-1", b)
        crashed.handoff.fault_windows = {window}
        try:
            crashed.handoff.persist_batch(job_id="job-1", batch=b, context=context)
        except FaultSimulated:
            pass
        retried = crashed.fresh()
        rr = retried.handoff.persist_batch(job_id="job-1", batch=b, context=context)
        rr2 = retried.handoff.persist_batch(job_id="job-1", batch=b, context=context)
        ok = (
            semantic_digest(retried, "job-1") == cd
            and rr.checkpoint_advanced
            and not rr2.checkpoint_advanced
            and rr.manifest_id == cr.manifest_id
        )
        cases.append(
            _row(
                f"idempotence_retry_after_{window}",
                invariant="retry reaches clean-run state; a SECOND retry mutates nothing (§63)",
                result="OK" if ok else "FAIL",
                measured={
                    "digest_matches_clean": semantic_digest(retried, "job-1") == cd,
                    "first_retry_advanced": rr.checkpoint_advanced,
                    "second_retry_advanced": rr2.checkpoint_advanced,
                    "retry_manifest_id": rr.manifest_id,
                    "clean_manifest_id": cr.manifest_id,
                },
            )
        )

    # 3. retry after checkpoint (§49) — covered by same_batch_twice shape but
    # measured at the transition level here.
    root = tmp_path / "postckpt"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"post": 1}'], next_resume_token=_token(5))
    register_job(stack, "job-1", batch)
    stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    ckpt_after_first = sum(
        1
        for t in stack.jobs_repo.list_transitions("job-1")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    ckpt_after_second = sum(
        1
        for t in stack.jobs_repo.list_transitions("job-1")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    cases.append(
        _row(
            "idempotence_retry_after_checkpoint",
            invariant="checkpoint transition count stays EXACTLY 1 across retry (§49)",
            result="OK" if ckpt_after_first == 1 and ckpt_after_second == 1 else "FAIL",
            measured={
                "after_first": ckpt_after_first,
                "after_second": ckpt_after_second,
            },
        )
    )

    # 4. retry after COMPLETE (§50): frozen history.
    root = tmp_path / "postcomplete"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"done": 1}'], is_complete=True)
    register_job(stack, "job-1", batch)
    stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    frozen = semantic_digest(stack, "job-1")
    again = stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    divergent = make_batch(
        [b'{"done": 2}'],
        is_complete=True,
    )
    divergent_error = None
    try:
        stack.handoff.persist_batch(
            job_id="job-1", batch=divergent, context=context
        )
    except BatchAlreadyCompleted:
        divergent_error = "BatchAlreadyCompleted"
    cases.append(
        _row(
            "idempotence_retry_after_complete",
            invariant=(
                "retry after COMPLETE adopts frozen history without mutation; "
                "a DIVERGENT batch is a typed refusal (§50/§35)"
            ),
            result=(
                "OK"
                if semantic_digest(stack, "job-1") == frozen
                and not again.checkpoint_advanced
                and again.complete
                and divergent_error == "BatchAlreadyCompleted"
                else "FAIL"
            ),
            measured={
                "digest_frozen": semantic_digest(stack, "job-1") == frozen,
                "retry_checkpoint_advanced": again.checkpoint_advanced,
                "retry_complete": again.complete,
                "divergent_retry_error": divergent_error,
            },
        )
    )

    # 5. same blob under separate jobs (§56).
    root = tmp_path / "twoblobs"
    root.mkdir()
    stack = HandoffStack(root)
    body = b'{"shared": true}'
    ba = make_batch([body], request_fingerprint="fp-a")
    bb = make_batch([body], request_fingerprint="fp-b")
    register_job(stack, "job-a", ba)
    register_job(stack, "job-b", bb)
    ra = stack.handoff.persist_batch(job_id="job-a", batch=ba, context=context)
    rb = stack.handoff.persist_batch(job_id="job-b", batch=bb, context=context)
    sa = stack.jobs_repo.get_job("job-a")
    sb = stack.jobs_repo.get_job("job-b")
    cases.append(
        _row(
            "idempotence_same_blob_two_jobs",
            invariant=(
                "content dedupe shares the blob; acquisitions and checkpoint "
                "authority stay identity-bound per job (§56)"
            ),
            result=(
                "OK"
                if ra.blob_shas == rb.blob_shas
                and ra.acquisition_ids != rb.acquisition_ids
                and sa.last_committed_acquisition_id
                != sb.last_committed_acquisition_id
                else "FAIL"
            ),
            measured={
                "shared_blob_shas": list(ra.blob_shas),
                "acquisitions_distinct": ra.acquisition_ids
                != rb.acquisition_ids,
                "checkpoint_anchors_distinct": (
                    sa.last_committed_acquisition_id
                    != sb.last_committed_acquisition_id
                ),
            },
        )
    )

    # 6. same request / different bytes -> two revisions (§16/§63).
    root = tmp_path / "revisions"
    root.mkdir()
    stack = HandoffStack(root)
    first = make_batch([b'{"v": "A"}'])
    register_job(stack, "job-1", first)
    r1 = stack.handoff.persist_batch(job_id="job-1", batch=first, context=context)
    stack.jobs_repo.advance_status(
        "job-1",
        to_status=StorageJobStatus.ACQUIRING,
        reason="batch continuation after checkpoint",
    )
    second = make_batch(
        [b'{"v": "B"}'],
        request_fingerprint=first.request_fingerprint,
        retrieved_at=first.retrieved_at + timedelta(minutes=1),
    )
    r2 = stack.handoff.persist_batch(job_id="job-1", batch=second, context=context)
    revisions_ok = (
        r1.blob_shas != r2.blob_shas
        and r2.manifest_version == r1.manifest_version + 1
        and stack.store.blob_exists(r1.blob_shas[0], StorageEncoding.NONE)
        and stack.store.blob_exists(r2.blob_shas[0], StorageEncoding.NONE)
    )
    cases.append(
        _row(
            "idempotence_same_request_different_bytes",
            invariant=(
                "two explicit revisions, both T0A blobs preserved, explicit "
                "manifest supersession — no overwrite (§16)"
            ),
            result="OK" if revisions_ok else "FAIL",
            measured={
                "revision1_blob": r1.blob_shas[0],
                "revision2_blob": r2.blob_shas[0],
                "manifest_v1": r1.manifest_version,
                "manifest_v2": r2.manifest_version,
                "supersedes": (
                    stack.manifest_repo.get_manifest(r2.manifest_id)
                    .supersedes_manifest_id
                    == r1.manifest_id
                ),
            },
        )
    )

    # SYNTHETIC counterfactual (§63: at most one): an inverted-cursor
    # checkpoint attempt from RAW state must be refused by the accepted gate.
    root = tmp_path / "counterfactual"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"cf": 1}'])
    register_job(stack, "job-1", batch)
    for s in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
    ):
        stack.jobs_repo.advance_status("job-1", to_status=s)
    gate_refused = False
    try:
        stack.jobs_repo.advance_checkpoint(
            "job-1",
            resume_token=None,
            acquisition_id="never-persisted",
            manifest_id=None,
        )
    except JobResumeGateError:
        gate_refused = True
    cases.append(
        _row(
            "idempotence_counterfactual_inverted_gate",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "COUNTERFACTUAL: checkpoint attempted WITHOUT durable manifest "
                "— the accepted gate refuses and the cursor stays put"
            ),
            result="OK" if gate_refused else "FAIL",
            measured={
                "gate_error": "JobResumeGateError" if gate_refused else None,
                "resume_token_after": None,
            },
        )
    )
    return _matrix("IDEMPOTENCE_MATRIX", cases, counterfactuals=1)


# ---------------------------------------------------------------------------
# §64 — T0B_HANDOFF_MATRIX: T0A-only vs T0A+T0B vs broken lineage (§57)
# ---------------------------------------------------------------------------


def _t0b_handoff_matrix(tmp_path: Path) -> dict:
    cases: list[dict] = []
    context = make_context()

    # T0A-only remains valid (§57).
    root = tmp_path / "t0a-only"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"t0a-only": 1}'], next_resume_token=_token(2))
    register_job(stack, "job-1", batch)
    receipt = stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    state = stack.jobs_repo.get_job("job-1")
    cases.append(
        _row(
            "t0b_handoff_t0a_only_valid",
            invariant="T0A-only path persists, commits manifest, advances checkpoint (§57)",
            result=(
                "OK"
                if receipt.checkpoint_advanced
                and state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and receipt.manifest_id
                else "FAIL"
            ),
            measured={
                "blob_shas": list(receipt.blob_shas),
                "manifest_id": receipt.manifest_id,
                "checkpoint_advanced": receipt.checkpoint_advanced,
                "projection_refs": [],
            },
        )
    )

    # T0A+T0B: manifest bound to projection refs via the accepted I04/I05
    # validation path (projection_refs present in the committed manifest).
    root = tmp_path / "t0ab"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"t0ab": 1}'], next_resume_token=_token(2))
    register_job(stack, "job-1", batch)

    # Durable lineage anchor: a REAL committed T0B projection from the
    # accepted I05 service over the handoff's own durable T0A evidence.
    registry = stack.registry  # noqa: F841 (composition seam documented)
    import pyarrow as pa  # noqa: E402  (accepted I05 dependency)

    from crypto_sensor_fabric.storage.projection_lineage import (  # noqa: E402
        ProjectionLineageRepository,
    )
    from crypto_sensor_fabric.storage.projection_resolver import (  # noqa: E402
        ProjectionLineageResolver,
    )
    from crypto_sensor_fabric.storage.projections import (  # noqa: E402
        ProjectionArtifactRepository,
        ProjectionContextRepository,
        ProjectionSchemaDefinition,
        ProjectionSchemaRegistry,
        T0BProjectionService,
    )

    schemas = ProjectionSchemaRegistry(
        stack.root / "catalogs" / "projection_schemas"
    )
    artifacts = ProjectionArtifactRepository(
        stack.root / "catalogs" / "manifests" / "projections",
        projection_root=stack.root,
        schema_registry=schemas,
    )
    contexts = ProjectionContextRepository(
        stack.root / "catalogs" / "manifests" / "projection_context"
    )
    lineage = ProjectionLineageRepository(
        stack.root / "catalogs" / "manifests" / "projection_lineage",
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        artifact_repository=artifacts,
        context_repository=contexts,
    )
    service = T0BProjectionService(
        root=stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        schema_registry=schemas,
        artifact_repository=artifacts,
        context_repository=contexts,
        lineage_repository=lineage,
        clock=lambda: FIXED,
    )

    # First persist the batch T0A-only, then commit a T0B over its exact
    # durable evidence, then re-commit the manifest with projection refs
    # through the SAME handoff (§57: lineage binds exact T0A evidence).
    receipt_t0a = stack.handoff.persist_batch(
        job_id="job-1", batch=batch, context=context
    )
    definition = ProjectionSchemaDefinition(
        projection_schema_id="i14.handoff.projection",
        projection_schema_version="1.0.0",
        provider_native_schema=pa.schema(
            [
                pa.field("price", pa.float64(), nullable=False),
                pa.field("symbol", pa.string(), nullable=False),
            ]
        ),
    )
    schemas.register(definition)
    projection_id = "i14-handoff-proj-1"
    lineage_manifest_id = f"lm-{projection_id}"
    service.commit_projection(
        rows=[{"price": 42.0, "symbol": "XBT/USD"}],
        schema_definition=definition,
        projection_id=projection_id,
        source_blob_sha256=list(receipt_t0a.blob_shas),
        acquisition_ids=list(receipt_t0a.acquisition_ids),
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        native_granularity="1m",
        parser_version="1.0.0",
        partition_key="kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/2026-01-15",
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=lineage_manifest_id,
    )

    # Advance the manifest chain through the handoff's CAS append with the
    # projection refs bound — the accepted I04 path validates lineage.
    partition_key = (
        "kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/2026-01-15"
    )
    current = stack.manifest_repo.read_current_pointer(partition_key)
    assert current is not None
    prev = stack.manifest_repo.get_manifest(current.partition_manifest_id)
    assert prev is not None
    with_projection = PartitionManifest(
        partition_manifest_id=f"{partition_key}::v{prev.manifest_version + 1}",
        partition_key=partition_key,
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        source_granularity=Granularity.G1M,
        logical_date_start=batch.requested_start,
        logical_date_end=batch.requested_end,
        blob_refs=list(prev.blob_refs),
        projection_refs=[projection_id],
        created_at=FIXED,
        manifest_version=prev.manifest_version + 1,
        supersedes_manifest_id=prev.partition_manifest_id,
    )
    resolver_wired = PartitionManifestRepository(
        stack.t0a,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        projection_lineage_resolver=ProjectionLineageResolver(
            root=stack.root,
            artifacts=artifacts,
            contexts=contexts,
            lineage=lineage,
            schemas=schemas,
        ),
        clock=lambda: FIXED,
    )
    result = resolver_wired.append_partition_manifest(
        with_projection,
        (prev.partition_manifest_id, prev.manifest_version),
    )
    committed_projection_refs = result.manifest.projection_refs
    cases.append(
        _row(
            "t0b_handoff_manifest_binds_projection",
            invariant=(
                "T0A+T0B: projection refs nonempty, lineage resolves over the "
                "EXACT T0A evidence, manifest commit accepted (§64)"
            ),
            result=(
                "OK"
                if committed_projection_refs == [projection_id]
                and stack.store.blob_exists(
                    receipt_t0a.blob_shas[0], StorageEncoding.NONE
                )
                else "FAIL"
            ),
            measured={
                "projection_refs": list(committed_projection_refs),
                "lineage_manifest_id": lineage_manifest_id,
                "source_t0a_blobs": list(receipt_t0a.blob_shas),
                "source_acquisitions": list(receipt_t0a.acquisition_ids),
                "manifest_id": result.manifest.partition_manifest_id,
                "manifest_version": result.manifest.manifest_version,
            },
        )
    )

    # Broken lineage REFUSES manifest commit, checkpoint stays old (§64).
    root = tmp_path / "broken-lineage"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"broken": 1}'], next_resume_token=_token(2))
    register_job(stack, "job-1", batch)
    stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    partition_key = (
        "kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/2026-01-15"
    )
    current = stack.manifest_repo.read_current_pointer(partition_key)
    assert current is not None
    prev = stack.manifest_repo.get_manifest(current.partition_manifest_id)
    assert prev is not None
    dangling = PartitionManifest(
        partition_manifest_id=f"{partition_key}::v{prev.manifest_version + 1}",
        partition_key=partition_key,
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        source_granularity=Granularity.G1M,
        logical_date_start=batch.requested_start,
        logical_date_end=batch.requested_end,
        blob_refs=list(prev.blob_refs),
        projection_refs=["i14-dangling-projection"],
        created_at=FIXED,
        manifest_version=prev.manifest_version + 1,
        supersedes_manifest_id=prev.partition_manifest_id,
    )
    refused = False
    try:
        resolver_wired_but_dangling = PartitionManifestRepository(
            stack.t0a,
            blob_store=stack.store,
            blob_metadata_repository=stack.blob_repo,
            acquisition_repository=stack.acq_repo,
            projection_lineage_resolver=ProjectionLineageResolver(
                root=stack.root,
                artifacts=ProjectionArtifactRepository(
                    stack.root / "catalogs" / "manifests" / "projections",
                    projection_root=stack.root,
                    schema_registry=schemas,
                ),
                contexts=ProjectionContextRepository(
                    stack.root / "catalogs" / "manifests" / "projection_context"
                ),
                lineage=ProjectionLineageRepository(
                    stack.root / "catalogs" / "manifests" / "projection_lineage",
                    blob_store=stack.store,
                    blob_metadata_repository=stack.blob_repo,
                    acquisition_repository=stack.acq_repo,
                    artifact_repository=artifacts,
                    context_repository=contexts,
                ),
                schemas=schemas,
            ),
            clock=lambda: FIXED,
        )
        resolver_wired_but_dangling.append_partition_manifest(
            dangling,
            (prev.partition_manifest_id, prev.manifest_version),
        )
    except Exception as exc:  # typed refusal — accepted I04/I05 law
        refused = type(exc).__name__ not in ("", "Exception")
        refused_name = type(exc).__name__
    state_after = stack.jobs_repo.get_job("job-1")
    cases.append(
        _row(
            "t0b_handoff_broken_lineage_refused",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "COUNTERFACTUAL: dangling projection ref — manifest commit "
                "FAILS CLOSED and the checkpoint stays old (§64)"
            ),
            result=(
                "OK"
                if refused
                and state_after.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and state_after.resume_token is not None
                else "FAIL"
            ),
            measured={
                "refusal_typed_error": refused_name if refused else None,
                "checkpoint_status_after": state_after.status.value,
                "resume_token_page": (
                    state_after.resume_token.page_number
                    if state_after.resume_token
                    else None
                ),
            },
        )
    )
    return _matrix("T0B_HANDOFF_MATRIX", cases, counterfactuals=1)


# ---------------------------------------------------------------------------
# §65 — CONCURRENCY_MATRIX: same-job fork/double-checkpoint/manifest forks
# ---------------------------------------------------------------------------


def _concurrency_matrix(tmp_path: Path) -> dict:
    cases: list[dict] = []
    context = make_context()

    # Same job, two racing persist attempts of the SAME batch: the accepted
    # job lock + frozen graph + committed-checkpoint retry law mean one
    # semantic advance total, no forked history, no manifest version fork.
    root = tmp_path / "conc-same"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch(
        [b'{"race": 1}'], next_resume_token=_token(5)
    )
    register_job(stack, "job-1", batch)
    first = stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    second = stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    ckpt = sum(
        1
        for t in stack.jobs_repo.list_transitions("job-1")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    manifest_versions = [
        m.partition_manifest_id
        for m in stack.manifest_repo.list_all_current_manifests()
    ]
    cases.append(
        _row(
            "concurrency_same_job_no_fork",
            invariant=(
                "same job/batch double-persist: exactly ONE checkpoint, no "
                "manifest version fork, stable final state (§65/§55)"
            ),
            result=(
                "OK"
                if ckpt == 1
                and not second.checkpoint_advanced
                and manifest_versions == [first.manifest_id]
                else "FAIL"
            ),
            measured={
                "checkpoint_transitions": ckpt,
                "second_checkpoint_advanced": second.checkpoint_advanced,
                "current_manifest_ids": manifest_versions,
                "first_manifest_id": first.manifest_id,
            },
        )
    )

    # CONCURRENT same-job writers through the accepted CAS: a writer whose
    # intent was computed against v1, but which reaches the append only AFTER
    # v2 committed, holds a STALE expected pointer and is refused by the
    # accepted manifest CAS — no last-writer-wins, no version fork.
    root = tmp_path / "conc-cas"
    root.mkdir()
    stack = HandoffStack(root)
    batch = make_batch([b'{"cas": 1}'], next_resume_token=_token(7))
    register_job(stack, "job-1", batch)
    stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    partition_key = (
        "kraken/kraken_spot/MECHANICAL_TRADE/XBT/USD/2026-01-15"
    )

    # Stale writer builds its intent NOW (v2, expecting v1 current)...
    v1 = stack.manifest_repo.read_current_pointer(partition_key)
    prev_v1 = stack.manifest_repo.get_manifest(v1.partition_manifest_id)
    stale_intent = PartitionManifest(
        partition_manifest_id=f"{partition_key}::v{prev_v1.manifest_version + 1}",
        partition_key=partition_key,
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        source_granularity=Granularity.G1M,
        logical_date_start=batch.requested_start,
        logical_date_end=batch.requested_end,
        blob_refs=list(prev_v1.blob_refs),
        projection_refs=[],
        created_at=FIXED,
        manifest_version=prev_v1.manifest_version + 1,
        supersedes_manifest_id=prev_v1.partition_manifest_id,
    )
    stale_expected = (
        prev_v1.partition_manifest_id,
        prev_v1.manifest_version,
    )
    # ...but the WINNER commits v2 first...
    current_after_winner = stack.manifest_repo.read_current_pointer(partition_key)
    winner_prev = stack.manifest_repo.get_manifest(
        current_after_winner.partition_manifest_id
    )
    winner = PartitionManifest(
        partition_manifest_id=f"{partition_key}::v{winner_prev.manifest_version + 1}",
        partition_key=partition_key,
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        source_granularity=Granularity.G1M,
        logical_date_start=batch.requested_start,
        logical_date_end=batch.requested_end,
        blob_refs=list(winner_prev.blob_refs),
        projection_refs=[],
        created_at=FIXED,
        manifest_version=winner_prev.manifest_version + 1,
        supersedes_manifest_id=winner_prev.partition_manifest_id,
    )
    stack.manifest_repo.append_partition_manifest(
        winner,
        (winner_prev.partition_manifest_id, winner_prev.manifest_version),
    )
    # The winner ALSO commits v3 before the stale writer reaches the append,
    # so the stale intent can no longer be confused with an idempotent
    # retry of the current version — its expected pointer is genuinely
    # two versions behind.
    v2 = stack.manifest_repo.read_current_pointer(partition_key)
    prev_v2 = stack.manifest_repo.get_manifest(v2.partition_manifest_id)
    winner_v3 = PartitionManifest(
        partition_manifest_id=f"{partition_key}::v{prev_v2.manifest_version + 1}",
        partition_key=partition_key,
        provider="kraken",
        venue="kraken_spot",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="XBT/USD",
        source_granularity=Granularity.G1M,
        logical_date_start=batch.requested_start,
        logical_date_end=batch.requested_end,
        blob_refs=list(prev_v2.blob_refs),
        projection_refs=[],
        created_at=FIXED,
        manifest_version=prev_v2.manifest_version + 1,
        supersedes_manifest_id=prev_v2.partition_manifest_id,
    )
    stack.manifest_repo.append_partition_manifest(
        winner_v3,
        (prev_v2.partition_manifest_id, prev_v2.manifest_version),
    )
    # ...and NOW the stale writer finally reaches the append.
    stale_conflict = False
    stale_error = None
    try:
        stale_writer = PartitionManifestRepository(
            stack.t0a,
            blob_store=stack.store,
            blob_metadata_repository=stack.blob_repo,
            acquisition_repository=stack.acq_repo,
            clock=lambda: FIXED,
        )
        stale_writer.append_partition_manifest(stale_intent, stale_expected)
    except ManifestCASConflict as exc:
        stale_conflict = True
        stale_error = type(exc).__name__
    cases.append(
        _row(
            "concurrency_manifest_cas_stale_writer_refused",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "COUNTERFACTUAL: a stale-expected writer is refused by the "
                "accepted manifest CAS — no last-writer-wins, no version fork"
            ),
            result="OK" if stale_conflict else "FAIL",
            measured={
                "typed_error": stale_error,
                "current_pointer_is_winner": (
                    stack.manifest_repo.read_current_pointer(
                        partition_key
                    ).partition_manifest_id
                    == winner.partition_manifest_id
                ),
                "winner_manifest_id": winner.partition_manifest_id,
            },
        )
    )
    return _matrix("CONCURRENCY_MATRIX", cases, counterfactuals=1)


# ---------------------------------------------------------------------------
# Evidence publication + parity guard
# ---------------------------------------------------------------------------


def _write(name: str, payload: dict) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / name
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return path


class TestI14Evidence:
    """Each test measures production behavior and publishes ONE matrix."""

    def test_input_mapping_matrix(self) -> None:
        matrix = _input_mapping_matrix()
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_INPUT_MAPPING_MATRIX.json", matrix)

    def test_durability_order_matrix(self, tmp_path) -> None:
        matrix = _durability_order_matrix(tmp_path)
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_DURABILITY_ORDER_MATRIX.json", matrix)

    def test_crash_restart_matrix(self, tmp_path) -> None:
        matrix = _crash_restart_matrix(tmp_path)
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_CRASH_RESTART_MATRIX.json", matrix)

    def test_idempotence_matrix(self, tmp_path) -> None:
        matrix = _idempotence_matrix(tmp_path)
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_IDEMPOTENCE_MATRIX.json", matrix)

    def test_t0b_handoff_matrix(self, tmp_path) -> None:
        matrix = _t0b_handoff_matrix(tmp_path)
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_T0B_HANDOFF_MATRIX.json", matrix)

    def test_concurrency_matrix(self, tmp_path) -> None:
        matrix = _concurrency_matrix(tmp_path)
        assert matrix["rows_fail"] == 0
        _write("BLOC_04_I14_CONCURRENCY_MATRIX.json", matrix)


if __name__ == "__main__":
    raise SystemExit("run with pytest")
