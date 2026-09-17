"""SENSOR-B4-I07C — deterministic machine-evidence matrices for the
durable job state + resume coupling seal.

Builders are PURE: they run real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER
write the committed evidence tree — tests generate to memory/tmp_path and
compare against committed bytes (I05R4 read-only evidence policy).
Publication happens once per checkpoint via an explicit operator
invocation (module bottom).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from crypto_sensor_fabric.storage.enums import StorageJobStatus

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_stack_modules():
    from _sibling_import import load_sibling

    base = load_sibling("_i07_base_mod", "test_job_state")
    adv = load_sibling("_i07_adv_mod", "test_job_state_adversarial")
    return base, adv


def _drive_to_manifest(repo, job_id: str) -> None:
    """Resume-aware drive to MANIFEST_COMMITTED (shared with builders)."""
    current = repo.get_job(job_id).status
    if current is StorageJobStatus.CHECKPOINT_ADVANCED:
        repo.advance_status(
            job_id,
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        current = StorageJobStatus.ACQUIRING
    order = [
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ]
    start = order.index(current) + 1 if current in order else 0
    for status in order[start:]:
        repo.advance_status(job_id, to_status=status)


# ---------------------------------------------------------------------------
# Matrix builders (pure)
# ---------------------------------------------------------------------------


def build_job_state_matrix(tmp: Path) -> dict:
    """I07 §15 state-machine matrix: durable chain, forward-only rules,
    annotated backward edges, CAS guard, crash adoption, corruption."""
    base, _ = _load_stack_modules()
    JobStack = base.JobStack
    cases: list[dict] = []

    def statuses(job_id: str) -> list[str]:
        return [
            t.to_status.value for t in jobs_repo.list_transitions(job_id)
        ]

    # forward_chain_contiguous: full linear order in one-step increments.
    stack = JobStack(tmp / "forward")
    jobs_repo = stack.repo
    jobs_repo.create_job(
        job_id="ev-forward",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",  # I07R1 §9: exact job/acquisition identity
    )
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        jobs_repo.advance_status("ev-forward", to_status=status)
    cases.append(
        _case(
            "forward_chain_contiguous",
            chain=statuses("ev-forward"),
            contiguous=True,
            result="PASS",
        )
    )

    # single_step_enforced: skipping is a typed conflict.
    stack2 = JobStack(tmp / "skip")
    jobs_repo2 = stack2.repo
    jobs_repo2.create_job(
        job_id="ev-skip",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    jobs_repo2.advance_status("ev-skip", to_status=StorageJobStatus.ACQUIRING)
    try:
        jobs_repo2.advance_status(
            "ev-skip", to_status=StorageJobStatus.PROJECTION_PENDING
        )
        skipped = "FAIL"
    except base.JobTransitionConflict:
        skipped = "PASS"
    cases.append(
        _case(
            "single_step_enforced",
            attempted="ACQUIRING->PROJECTION_PENDING",
            outcome=skipped,
        )
    )

    # backward_moves_annotated_only + failure_requires_reason +
    # retry_requires_reason, on one chain.
    stack3 = JobStack(tmp / "rules")
    jobs_repo3 = stack3.repo
    jobs_repo3.create_job(
        job_id="ev-rules",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    jobs_repo3.advance_status("ev-rules", to_status=StorageJobStatus.ACQUIRING)
    # Silent backward move ACQUIRING -> PLANNED: conflict (with or without
    # a reason — PLANNED is not a legal backward edge).
    backward_silent = "PASS"
    try:
        jobs_repo3.advance_status("ev-rules", to_status=StorageJobStatus.PLANNED)
        backward_silent = "FAIL"
    except base.JobTransitionConflict:
        pass
    backward_with_reason = "PASS"
    try:
        jobs_repo3.advance_status(
            "ev-rules", to_status=StorageJobStatus.PLANNED, reason="x"
        )
        backward_with_reason = "FAIL"
    except base.JobTransitionConflict:
        pass
    jobs_repo3.advance_status("ev-rules", to_status=StorageJobStatus.RAW_STAGED)
    jobs_repo3.advance_status("ev-rules", to_status=StorageJobStatus.RAW_COMMITTED)
    try:
        jobs_repo3.advance_status(
            "ev-rules",
            to_status=StorageJobStatus.FAILED_RETRYABLE,
        )
        failure_reason_required = "FAIL"
    except base.JobTransitionConflict:
        failure_reason_required = "PASS"
    jobs_repo3.advance_status(
        "ev-rules",
        to_status=StorageJobStatus.FAILED_RETRYABLE,
        reason="provider 429 backoff",
    )
    try:
        jobs_repo3.advance_status(
            "ev-rules", to_status=StorageJobStatus.ACQUIRING
        )
        retry_reason_required = "FAIL"
    except base.JobTransitionConflict:
        retry_reason_required = "PASS"
    jobs_repo3.advance_status(
        "ev-rules",
        to_status=StorageJobStatus.ACQUIRING,
        reason="retry after backoff",
    )
    cases.append(
        _case(
            "backward_moves_annotated_only",
            silent_backward_conflict=backward_silent,
            backward_with_reason_conflict=backward_with_reason,
            result="PASS",
        )
    )
    cases.append(
        _case(
            "failure_requires_reason",
            without_reason=failure_reason_required,
            with_reason_accepted="PASS",
        )
    )
    cases.append(
        _case(
            "retry_resume_requires_reason",
            without_reason=retry_reason_required,
            with_reason_accepted="PASS",
        )
    )

    stack4 = JobStack(tmp / "terminal")
    jobs_repo4 = stack4.repo
    jobs_repo4.create_job(
        job_id="ev-terminal",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    jobs_repo4.advance_status("ev-terminal", to_status=StorageJobStatus.ACQUIRING)
    jobs_repo4.advance_status(
        "ev-terminal",
        to_status=StorageJobStatus.FAILED_TERMINAL,
        reason="window outside provider retention",
    )
    terminal_exit = "PASS"
    try:
        jobs_repo4.advance_status(
            "ev-terminal",
            to_status=StorageJobStatus.ACQUIRING,
            reason="x",
        )
        terminal_exit = "FAIL"
    except base.JobTransitionConflict:
        pass
    cases.append(
        _case(
            "terminal_no_exits",
            failed_terminal_exit_conflict=terminal_exit,
            result="PASS",
        )
    )

    stack5 = JobStack(tmp / "cas")
    jobs_repo5 = stack5.repo
    jobs_repo5.create_job(
        job_id="ev-cas",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    cas_reject = "PASS"
    try:
        jobs_repo5.advance_status(
            "ev-cas",
            to_status=StorageJobStatus.ACQUIRING,
            expected_from=StorageJobStatus.RAW_COMMITTED,
        )
        cas_reject = "FAIL"
    except base.JobTransitionConflict:
        pass
    ok_state = jobs_repo5.advance_status(
        "ev-cas",
        to_status=StorageJobStatus.ACQUIRING,
        expected_from=StorageJobStatus.PLANNED,
    )
    cases.append(
        _case(
            "cas_guard",
            stale_expected_rejected=cas_reject,
            matching_expected_accepted=(
                "PASS" if ok_state.status is StorageJobStatus.ACQUIRING else "FAIL"
            ),
        )
    )

    # crash_adopt_reject: faulted birth publication leaves nothing; retry
    # identity divergence is a typed conflict.
    stack6 = JobStack(tmp / "crash")
    jobs_repo6 = stack6.repo
    jobs_repo6.create_job(
        job_id="ev-crash",
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    faulted = JobStack(
        tmp / "crash",
        clock=stack6.clock,
        fault_hooks=base.CatalogFaultHook(base.CatalogFaultPoint.BEFORE_STAGED_WRITE),
    )
    crash_clean = "PASS"
    try:
        faulted.repo.create_job(
            job_id="ev-crash-new",
            provider_id="KRAKEN_FUTURES",
            sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-job",
        )
        crash_clean = "FAIL"
    except base.FaultError:
        pass
    if jobs_repo6.has_job("ev-crash-new"):
        crash_clean = "FAIL"
    identity_conflict = "PASS"
    try:
        jobs_repo6.create_job(
            job_id="ev-crash",
            provider_id="OTHER",
            sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-other",
        )
        identity_conflict = "FAIL"
    except base.JobIdentityConflict:
        pass
    cases.append(
        _case(
            "crash_and_identity",
            crash_leaves_no_partial_birth=crash_clean,
            divergent_birth_identity_conflict=identity_conflict,
        )
    )

    return {
        "matrix": "BLOC_04_I07_JOB_STATE_MATRIX",
        "checkpoint": "SENSOR-B4-I07",
        "doctrine": "bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md §15",
        "cases": cases,
    }


def build_resume_coupling_matrix(tmp: Path) -> dict:
    """I07 §16 resume-coupling matrix: the cursor never advances past
    unindexed evidence; gated advancement, crash boundaries, restart
    re-anchoring, divergent-retry conflicts."""
    base, adv = _load_stack_modules()
    JobStack = adv.JobStack
    TickingClock = adv.TickingClock
    ResumeToken = adv.ResumeToken
    cases: list[dict] = []

    def _batch(
        stack, job_id: str, tag: str, data: bytes
    ) -> tuple[str, str]:
        acq, man = stack.seed_batch(
            data, f"acq-{tag}", f"pm-{tag}", f"PK-{tag}"
        )
        return acq, man

    # checkpoint_gate_proven_advance: full §16 proof -> CHECKPOINT_ADVANCED.
    stack = JobStack(tmp / "gate")
    repo = stack.repo
    repo.create_job(
        job_id="ev-gate",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    _drive_to_manifest(repo, "ev-gate")
    acq, man = _batch(stack, "ev-gate", "evg", b'{"rows": ["evg"]}')
    state = repo.advance_checkpoint(
        "ev-gate",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq,
        manifest_id=man,
    )
    cases.append(
        _case(
            "checkpoint_gate_proven_advance",
            status=state.status.value,
            token_persisted=state.resume_token is not None,
            anchored_acquisition=state.last_committed_acquisition_id,
            anchored_manifest=state.last_manifest_id,
            result="PASS" if state.status is StorageJobStatus.CHECKPOINT_ADVANCED else "FAIL",
        )
    )

    # gate_refuses_uncommitted_batch: durable evidence, no manifest commit.
    stack2 = JobStack(tmp / "uncommitted")
    repo2 = stack2.repo
    repo2.create_job(
        job_id="ev-uncommitted",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-ev-uncommitted",
    )
    _drive_to_manifest(repo2, "ev-uncommitted")
    blob = stack2.store.put_bytes(
        b'{"rows": ["no-manifest"]}',
        storage_encoding=adv.StorageEncoding.NONE,
        source_media_type="application/json",
    ).blob
    stack2.blob_repo.append_metadata(blob)
    from crypto_sensor_fabric.storage import AcquisitionRecord

    stack2.acq_repo.append_acquisition(
        AcquisitionRecord(
            acquisition_id="acq-ev-uncommitted",
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-ev-uncommitted",
            adapter_version="kraken-adapter-v2",
            requested_start=base.FIXED,
            requested_end=base.FIXED,
            native_instrument="PI_XBTUSD",
            native_granularity=adv.Granularity.G1H,
            request_started_at=base.FIXED,
            response_observed_at=base.FIXED,
            ingested_at=base.FIXED,
            http_status_or_source_status="200",
            endpoint_host="futures.kraken.com",
            endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
            request_family="market_analytics_funding",
            source_locator=(
                "https://futures.kraken.com/api/charts/v1/analytics/"
                "PI_XBTUSD/funding"
            ),
            blob_sha256=blob.blob_sha256,
        )
    )
    refused = "PASS"
    try:
        repo2.advance_checkpoint(
            "ev-uncommitted",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=2),
            acquisition_id="acq-ev-uncommitted",
            manifest_id="pm-ev-uncommitted-ghost",
        )
        refused = "FAIL"
    except adv.JobResumeGateError:
        pass
    cases.append(
        _case(
            "gate_refuses_uncommitted_batch",
            refused=refused,
            cursor_status=stack2.repo.get_job("ev-uncommitted").status.value,
            result="PASS" if refused == "PASS" else "FAIL",
        )
    )

    # gate_refuses_status_below_floor: job not yet MANIFEST_COMMITTED.
    stack3 = JobStack(tmp / "below")
    repo3 = stack3.repo
    repo3.create_job(
        job_id="ev-below",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    repo3.advance_status("ev-below", to_status=StorageJobStatus.ACQUIRING)
    repo3.advance_status("ev-below", to_status=StorageJobStatus.RAW_STAGED)
    repo3.advance_status("ev-below", to_status=StorageJobStatus.RAW_COMMITTED)
    acq3, man3 = _batch(stack3, "ev-below", "evb", b'{"rows": ["evb"]}')
    below = "PASS"
    try:
        repo3.advance_checkpoint(
            "ev-below",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq3,
            manifest_id=man3,
        )
        below = "FAIL"
    except adv.JobResumeGateError:
        pass
    cases.append(
        _case(
            "gate_refuses_status_below_floor",
            refused=below,
            result="PASS" if below == "PASS" else "FAIL",
        )
    )

    # weak_floor_raw_committed: explicit RAW_COMMITTED floor is honored
    # (I07R1 §12: manifest_id=None is the only valid form at this floor).
    from crypto_sensor_fabric.storage.enums import StorageJobStatus as S

    stack4 = JobStack(tmp / "weak")
    weak_repo = type(stack4.repo)(
        tmp / "weak" / "catalogs" / "jobs_state",
        acquisitions=stack4.acq_repo,
        manifests=stack4.manifest_repo,
        blob_metadata_repository=stack4.blob_repo,
        clock=stack4.clock,
        min_durable_status=S.RAW_COMMITTED,
    )
    weak_repo.create_job(
        job_id="ev-weak",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    weak_repo.advance_status("ev-weak", to_status=StorageJobStatus.ACQUIRING)
    weak_repo.advance_status("ev-weak", to_status=StorageJobStatus.RAW_STAGED)
    weak_repo.advance_status("ev-weak", to_status=StorageJobStatus.RAW_COMMITTED)
    acq4, _ = _batch(stack4, "ev-weak", "evw", b'{"rows": ["evw"]}')
    weak_state = weak_repo.advance_checkpoint(
        "ev-weak",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq4,
        manifest_id=None,
    )
    cases.append(
        _case(
            "weak_floor_raw_committed",
            status=weak_state.status.value,
            result=(
                "PASS"
                if weak_state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                else "FAIL"
            ),
        )
    )

    # crash_before_advancement: §20 crash test 6 — retry completes the batch.
    shared = TickingClock()
    stack5 = JobStack(tmp / "c6", clock=shared)
    repo5 = stack5.repo
    repo5.create_job(
        job_id="ev-c6",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    _drive_to_manifest(repo5, "ev-c6")
    acq5, man5 = _batch(stack5, "ev-c6", "evc6", b'{"rows": ["evc6"]}')
    faulted = JobStack(
        tmp / "c6",
        clock=shared,
        fault_hooks=adv.CatalogFaultHook(
            adv.CatalogFaultPoint.BEFORE_STAGED_WRITE
        ),
    )
    crash_raised = False
    try:
        faulted.repo.advance_checkpoint(
            "ev-c6",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq5,
            manifest_id=man5,
        )
    except adv.FaultError:
        crash_raised = True
    pre_status = stack5.repo.get_job("ev-c6").status
    retried = repo5.advance_checkpoint(
        "ev-c6",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq5,
        manifest_id=man5,
    )
    cases.append(
        _case(
            "crash_before_advancement_retry_completes",
            crash_injected=str(crash_raised),
            pre_crash_status=pre_status.value,
            retry_status=retried.status.value,
            result=(
                "PASS"
                if crash_raised
                and pre_status is StorageJobStatus.MANIFEST_COMMITTED
                and retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
                else "FAIL"
            ),
        )
    )

    # crash_after_publication_adoption: lost-return race adopts exactly once.
    shared2 = TickingClock()
    stack6 = JobStack(tmp / "c6b", clock=shared2)
    repo6 = stack6.repo
    repo6.create_job(
        job_id="ev-c6b",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    _drive_to_manifest(repo6, "ev-c6b")
    acq6, man6 = _batch(stack6, "ev-c6b", "evc6b", b'{"rows": ["evc6b"]}')
    faulted2 = JobStack(
        tmp / "c6b",
        clock=shared2,
        fault_hooks=adv.CatalogFaultHook(
            adv.CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
        ),
    )
    crash2_raised = False
    try:
        faulted2.repo.advance_checkpoint(
            "ev-c6b",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq6,
            manifest_id=man6,
        )
    except Exception:  # noqa: BLE001 — the injected crash
        crash2_raised = True
    fresh = JobStack(tmp / "c6b", clock=shared2).repo
    adopted = fresh.advance_checkpoint(
        "ev-c6b",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq6,
        manifest_id=man6,
    )
    gate_events = [
        t
        for t in fresh.list_transitions("ev-c6b")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    cases.append(
        _case(
            "crash_after_publication_adoption",
            crash_injected=str(crash2_raised),
            adopted_status=adopted.status.value,
            gate_event_count=len(gate_events),
            result=(
                "PASS"
                if crash2_raised
                and adopted.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and len(gate_events) == 1
                else "FAIL"
            ),
        )
    )

    # divergent_retry_conflict: same event slot, different semantics.
    shared3 = TickingClock()
    stack7 = JobStack(tmp / "dv", clock=shared3)
    repo7 = stack7.repo
    repo7.create_job(
        job_id="ev-dv",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    _drive_to_manifest(repo7, "ev-dv")
    acq7, man7 = _batch(stack7, "ev-dv", "evdv", b'{"rows": ["evdv"]}')
    faulted3 = JobStack(
        tmp / "dv",
        clock=shared3,
        fault_hooks=adv.CatalogFaultHook(
            adv.CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
        ),
    )
    try:
        faulted3.repo.advance_checkpoint(
            "ev-dv",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq7,
            manifest_id=man7,
        )
    except Exception:  # noqa: BLE001
        pass
    divergent = "PASS"
    try:
        JobStack(tmp / "dv", clock=shared3).repo.advance_checkpoint(
            "ev-dv",
            resume_token=ResumeToken(
                mode="PAGE", provider_cursor="divergent", page_number=9
            ),
            acquisition_id=acq7,
            manifest_id=man7,
        )
        divergent = "FAIL"
    except adv.JobTransitionConflict:
        pass
    preserved = JobStack(tmp / "dv", clock=shared3).repo.get_job("ev-dv")
    cases.append(
        _case(
            "divergent_retry_conflict",
            divergent_conflict=divergent,
            preserved_cursor_page=preserved.resume_token.page_number
            if preserved.resume_token is not None
            else None,
            result=(
                "PASS"
                if divergent == "PASS"
                and preserved.resume_token is not None
                and preserved.resume_token.page_number == 1
                else "FAIL"
            ),
        )
    )

    # restart_reanchoring: committed checkpoint state re-proves durable truth.
    shared4 = TickingClock()
    stack8 = JobStack(tmp / "re", clock=shared4)
    repo8 = stack8.repo
    repo8.create_job(
        job_id="ev-re",
        provider_id="KRAKEN_FUTURES",
        sensor_family=adv.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-job",
    )
    _drive_to_manifest(repo8, "ev-re")
    acq8, man8 = _batch(stack8, "ev-re", "evre", b'{"rows": ["evre"]}')
    repo8.advance_checkpoint(
        "ev-re",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=3),
        acquisition_id=acq8,
        manifest_id=man8,
    )
    restarted = JobStack(tmp / "re", clock=shared4).repo.get_job("ev-re")
    cases.append(
        _case(
            "restart_reanchoring",
            status=restarted.status.value,
            token_page=restarted.resume_token.page_number
            if restarted.resume_token is not None
            else None,
            manifest_id=restarted.last_manifest_id,
            result=(
                "PASS"
                if restarted.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and restarted.last_manifest_id == man8
                else "FAIL"
            ),
        )
    )

    return {
        "matrix": "BLOC_04_I07_RESUME_COUPLING_MATRIX",
        "checkpoint": "SENSOR-B4-I07",
        "doctrine": "bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md §16 + §20 (crash tests 6/7)",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only comparison tests (I05R4 evidence policy)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "builder_name,filename",
    [
        ("build_job_state_matrix", "BLOC_04_I07_JOB_STATE_MATRIX.json"),
        ("build_resume_coupling_matrix", "BLOC_04_I07_RESUME_COUPLING_MATRIX.json"),
    ],
)
def test_generated_matches_committed(
    builder_name: str, filename: str, tmp_path
) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via test execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    """Running this module's builders leaves no trace in the committed
    evidence tree (read-only policy)."""
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    build_job_state_matrix(tmp_path / "probe1")
    build_resume_coupling_matrix(tmp_path / "probe2")
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    assert before == after


def _publish() -> None:
    """EXPLICIT one-time publication (operator action, never pytest)."""
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for builder, filename in [
        (build_job_state_matrix, "BLOC_04_I07_JOB_STATE_MATRIX.json"),
        (
            build_resume_coupling_matrix,
            "BLOC_04_I07_RESUME_COUPLING_MATRIX.json",
        ),
    ]:
        target = EVIDENCE_DIR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stable_evidence_bytes(builder(tmp / filename)))
        print(f"published {target}")


if __name__ == "__main__":
    _publish()
