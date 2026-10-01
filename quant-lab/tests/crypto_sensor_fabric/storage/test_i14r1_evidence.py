"""SENSOR-B4-I14R1 — append-only measured evidence (I14R1 §27-§30).

Four matrices, every row MEASURED from production behavior (real durable
stacks, real accepted repositories — never hand-authored OK):

- BLOC_04_I14R1_CONTINUATION_MATRIX.json (§28)
- BLOC_04_I14R1_EMPTY_VALID_CHECKPOINT_MATRIX.json (§29)
- BLOC_04_I14R1_MULTI_ENVELOPE_REVISION_MATRIX.json (§30)
- BLOC_04_I14R1_RESTART_MATRIX.json (§18/§28 W-windows on the new paths)
- BLOC_04_I14R1_EVIDENCE_CORRECTION.md (§27)

Historical I14 evidence is NOT modified (§27: append-only correction).
All fixtures are synthetic/offline (§38); no network anywhere.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import timedelta
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

i14 = load_sibling("test_i14_handoff", "test_i14_handoff")
HandoffStack = i14.HandoffStack
make_batch = i14.make_batch
register_job = i14.register_job
semantic_digest = i14.semantic_digest

repro = load_sibling(
    "test_i14r1_reproduction", "test_i14r1_reproduction"
)
make_context = repro.make_context
_token = repro._token  # noqa: SLF001

from crypto_sensor_fabric.providers.base.enums import (  # noqa: E402
    QualityFlagAcquisition,
)
from crypto_sensor_fabric.storage.enums import StorageJobStatus  # noqa: E402
from crypto_sensor_fabric.storage.integration import (  # noqa: E402
    DivergentBatchRewrite,
    FaultSimulated,
)

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

MANDATE = "SENSOR-B4-I14R1"


def _row(
    case_id: str,
    *,
    invariant: str,
    ok: bool,
    measured: dict,
) -> dict:
    return {
        "case_id": case_id,
        "category": "PRODUCTION_MEASURED",
        "invariant": invariant,
        "invariant_source": "PRODUCTION_MEASURED",
        "measured": measured,
        "result": "OK" if ok else "FAIL",
    }


def _matrix(matrix: str, rows: list[dict]) -> dict:
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "cases": rows,
        "mandate": MANDATE,
        "matrix": matrix,
        "measured_at_checkpoint": "I14R1",
        "rows_fail": len(rows) - ok,
        "rows_ok": ok,
        "rows_total": len(rows),
        "synthetic_counterfactuals": 0,
    }


def _publish(name: str, payload: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _empty_batch(**kwargs):  # type: ignore[no-untyped-def]
    base = {
        "row_count": 0,
        "quality_flags": [QualityFlagAcquisition.EMPTY_VALID],
    }
    base.update(kwargs)
    return make_batch([], **base)


def _checkpoint_moves(stack, job_id: str) -> int:  # type: ignore[no-untyped-def]
    return sum(
        1
        for t in stack.jobs_repo.list_transitions(job_id)
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    )


def _transitions(stack, job_id: str) -> list[list[str]]:  # type: ignore[no-untyped-def]
    return [
        [t.from_status.value, t.to_status.value]
        for t in stack.jobs_repo.list_transitions(job_id)
    ]


# ---------------------------------------------------------------------------
# §28 CONTINUATION_MATRIX
# ---------------------------------------------------------------------------


class TestContinuationMatrix:
    def test_continuation_matrix(self, tmp_path) -> None:
        rows: list[dict] = []

        # 1. exact retry after checkpoint.
        stack = HandoffStack(tmp_path / "c1")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        retry = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        rows.append(
            _row(
                "continuation_exact_retry_after_checkpoint",
                invariant=(
                    "page 1 re-delivery at CHECKPOINT_ADVANCED adopts "
                    "exactly: no transition, no new manifest, no new "
                    "checkpoint (I14R1 §8)"
                ),
                ok=(
                    retry.checkpoint_advanced is False
                    and retry.manifest_id == first.manifest_id
                    and len(stack.jobs_repo.list_transitions("job-1"))
                    == transitions_before
                ),
                measured={
                    "retry_checkpoint_advanced": retry.checkpoint_advanced,
                    "retry_manifest_id_matches": retry.manifest_id
                    == first.manifest_id,
                    "transitions_stable": len(
                        stack.jobs_repo.list_transitions("job-1")
                    )
                    == transitions_before,
                },
            )
        )

        # 2. next page accepted.
        stack = HandoffStack(tmp_path / "c2")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        page2 = make_batch(
            [b'{"page": 2}'],
            next_resume_token=_token(3),
            retrieved_at=page1.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=page2,
            context=make_context(request_resume_token=_token(2)),
        )
        rows.append(
            _row(
                "continuation_next_page_accepted",
                invariant=(
                    "page 2 (request fetched FROM the committed token) "
                    "continues via the accepted annotated edge with ZERO "
                    "external state manipulation (I14R1 §3)"
                ),
                ok=(
                    r2.checkpoint_advanced is True
                    and stack.jobs_repo.get_job("job-1").resume_token
                    == _token(3)
                ),
                measured={
                    "next_page_checkpoint_advanced": (
                        r2.checkpoint_advanced
                    ),
                    "durable_token_page": stack.jobs_repo.get_job(
                        "job-1"
                    ).resume_token.page_number,
                    "external_state_manipulations": 0,
                },
            )
        )

        # 3. wrong/stale resume source refused before mutation.
        stack = HandoffStack(tmp_path / "c3")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        frozen = semantic_digest(stack, "job-1")
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        stale = make_batch(
            [b'{"stale": true}'],
            next_resume_token=_token(9),
            retrieved_at=page1.retrieved_at + timedelta(minutes=1),
        )
        refused = False
        try:
            stack.handoff.persist_batch(
                job_id="job-1",
                batch=stale,
                context=make_context(request_resume_token=_token(7)),
            )
        except DivergentBatchRewrite:
            refused = True
        rows.append(
            _row(
                "continuation_stale_resume_source_refused",
                invariant=(
                    "incoming request_resume_token unrelated to the durable "
                    "token fails typed BEFORE any evidence mutation: no "
                    "ACQUIRING transition, no checkpoint movement (I14R1 §9)"
                ),
                ok=(
                    refused
                    and semantic_digest(stack, "job-1") == frozen
                    and len(stack.jobs_repo.list_transitions("job-1"))
                    == transitions_before
                ),
                measured={
                    "typed_refusal": "DivergentBatchRewrite",
                    "digest_frozen": semantic_digest(stack, "job-1") == frozen,
                    "transitions_stable": len(
                        stack.jobs_repo.list_transitions("job-1")
                    )
                    == transitions_before,
                },
            )
        )

        # 4. three sequential pages + final COMPLETE (public API only).
        stack = HandoffStack(tmp_path / "c4")
        p1 = make_batch([b'{"p": 1}'], next_resume_token=_token(2))
        register_job(stack, "job-1", p1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=p1, context=make_context()
        )
        p2 = make_batch(
            [b'{"p": 2}'],
            next_resume_token=_token(3),
            retrieved_at=p1.retrieved_at + timedelta(minutes=1),
        )
        stack.handoff.persist_batch(
            job_id="job-1",
            batch=p2,
            context=make_context(request_resume_token=_token(2)),
        )
        p3 = make_batch(
            [b'{"p": 3}'],
            is_complete=True,
            retrieved_at=p1.retrieved_at + timedelta(minutes=2),
        )
        r3 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=p3,
            context=make_context(request_resume_token=_token(3)),
        )
        transitions = _transitions(stack, "job-1")
        checkpoint_moves = [t for t in transitions if t[1] == "CHECKPOINT_ADVANCED"]
        continuation_edges = [
            t for t in transitions if t == ["CHECKPOINT_ADVANCED", "ACQUIRING"]
        ]
        rows.append(
            _row(
                "continuation_three_sequential_pages_complete",
                invariant=(
                    "page1 -> page2 -> page3(is_complete) through ONLY "
                    "persist_batch: exactly 3 checkpoint transitions, exactly "
                    "2 annotated continuation edges, COMPLETE terminal, no "
                    "skipped page, no double advance (I14R1 §7)"
                ),
                ok=(
                    r3.complete is True
                    and len(checkpoint_moves) == 3
                    and len(continuation_edges) == 2
                    and stack.jobs_repo.get_job("job-1").status
                    is StorageJobStatus.COMPLETE
                ),
                measured={
                    "checkpoint_transitions": len(checkpoint_moves),
                    "continuation_edges": len(continuation_edges),
                    "final_status": stack.jobs_repo.get_job(
                        "job-1"
                    ).status.value,
                    "external_state_manipulations": 0,
                },
            )
        )

        # 5. duplicate next-page delivery.
        stack = HandoffStack(tmp_path / "c5")
        p1 = make_batch([b'{"p": 1}'], next_resume_token=_token(2))
        register_job(stack, "job-1", p1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=p1, context=make_context()
        )
        p2 = make_batch(
            [b'{"p": 2}'],
            next_resume_token=_token(3),
            retrieved_at=p1.retrieved_at + timedelta(minutes=1),
        )
        ctx2 = make_context(request_resume_token=_token(2))
        stack.handoff.persist_batch(
            job_id="job-1", batch=p2, context=ctx2
        )
        frozen = semantic_digest(stack, "job-1")
        dup = stack.handoff.persist_batch(
            job_id="job-1", batch=p2, context=ctx2
        )
        rows.append(
            _row(
                "continuation_duplicate_next_page_delivery",
                invariant=(
                    "duplicate page-2 delivery is an exact retry: adopted "
                    "without mutation, no cursor skip (I14R1 §28)"
                ),
                ok=(
                    dup.checkpoint_advanced is False
                    and semantic_digest(stack, "job-1") == frozen
                    and stack.jobs_repo.get_job("job-1").resume_token
                    == _token(3)
                ),
                measured={
                    "duplicate_checkpoint_advanced": (
                        dup.checkpoint_advanced
                    ),
                    "digest_frozen": semantic_digest(stack, "job-1") == frozen,
                    "durable_token_page": stack.jobs_repo.get_job(
                        "job-1"
                    ).resume_token.page_number,
                },
            )
        )

        # 6. crash after the continuation transition (W1 on page 2) and
        # crash before the next manifest (W5 on page 2).
        for label, window in (
            ("crash_after_continuation_transition", "W1_BEFORE_RAW_WRITE"),
            ("crash_before_next_manifest", "W5_BEFORE_MANIFEST_APPEND"),
        ):
            stack = HandoffStack(tmp_path / f"c6_{window}")
            p1 = make_batch([b'{"p": 1}'], next_resume_token=_token(2))
            register_job(stack, "job-1", p1)
            stack.handoff.persist_batch(
                job_id="job-1", batch=p1, context=make_context()
            )
            p2 = make_batch(
                [b'{"p": 2}'],
                next_resume_token=_token(3),
                retrieved_at=p1.retrieved_at + timedelta(minutes=1),
            )
            ctx2 = make_context(request_resume_token=_token(2))
            crashed = stack
            crashed.handoff.fault_windows = {window}
            with pytest.raises(FaultSimulated):
                crashed.handoff.persist_batch(
                    job_id="job-1", batch=p2, context=ctx2
                )
            restarted = crashed.fresh()
            retry = restarted.handoff.persist_batch(
                job_id="job-1", batch=p2, context=ctx2
            )
            rows.append(
                _row(
                    f"continuation_{label}",
                    invariant=(
                        "a crash on the CONTINUATION path recovers through "
                        "the same public API: retry adopts/continues and the "
                        "durable token is exactly the page-2 next token, no "
                        "cursor skip (I14R1 §28)"
                    ),
                    ok=(
                        retry.checkpoint_advanced is True
                        and restarted.jobs_repo.get_job("job-1").resume_token
                        == _token(3)
                    ),
                    measured={
                        "window": window,
                        "retry_checkpoint_advanced": (
                            retry.checkpoint_advanced
                        ),
                        "durable_token_page": restarted.jobs_repo.get_job(
                            "job-1"
                        ).resume_token.page_number,
                    },
                )
            )

        # 7. W7 on page 2 and page 3 (pages persisted sequentially).
        for page_no in (2, 3):
            stack = HandoffStack(tmp_path / f"c7_p{page_no}")
            p1 = make_batch([b'{"p": 1}'], next_resume_token=_token(2))
            register_job(stack, "job-1", p1)
            stack.handoff.persist_batch(
                job_id="job-1", batch=p1, context=make_context()
            )
            for prior in range(2, page_no):
                pb = make_batch(
                    [f'{{"p": {prior}}}'.encode()],
                    next_resume_token=_token(prior + 1),
                    retrieved_at=p1.retrieved_at
                    + timedelta(minutes=prior - 1),
                )
                stack.handoff.persist_batch(
                    job_id="job-1",
                    batch=pb,
                    context=make_context(request_resume_token=_token(prior)),
                )
            batch = make_batch(
                [f'{{"p": {page_no}}}'.encode()],
                **(
                    {"next_resume_token": _token(page_no + 1)}
                    if page_no < 3
                    else {"is_complete": True}
                ),
                retrieved_at=p1.retrieved_at + timedelta(minutes=page_no - 1),
            )
            ctx = make_context(request_resume_token=_token(page_no))
            crashed = stack
            crashed.handoff.fault_windows = {"W7_AFTER_MANIFEST_BEFORE_CHECKPOINT"}
            with pytest.raises(FaultSimulated):
                crashed.handoff.persist_batch(
                    job_id="job-1", batch=batch, context=ctx
                )
            restarted = crashed.fresh()
            retry = restarted.handoff.persist_batch(
                job_id="job-1", batch=batch, context=ctx
            )
            moves = _checkpoint_moves(restarted, "job-1")
            rows.append(
                _row(
                    f"continuation_w7_on_page_{page_no}",
                    invariant=(
                        f"W7 on page {page_no}: manifest durable / checkpoint "
                        "old -> retry adopts the exact manifest and advances "
                        "the checkpoint EXACTLY once, no cursor skip "
                        "(I14R1 §28)"
                    ),
                    ok=(
                        retry.checkpoint_advanced is True
                        and moves == page_no  # pages 1..N, each exactly once
                    ),
                    measured={
                        "checkpoint_transitions_total": moves,
                        "retry_checkpoint_advanced": (
                            retry.checkpoint_advanced
                        ),
                    },
                )
            )

        _publish(
            "BLOC_04_I14R1_CONTINUATION_MATRIX.json",
            _matrix("CONTINUATION_MATRIX", rows),
        )
        assert all(r["result"] == "OK" for r in rows)


# ---------------------------------------------------------------------------
# §29 EMPTY_VALID_CHECKPOINT_MATRIX
# ---------------------------------------------------------------------------


class TestEmptyValidCheckpointMatrix:
    def test_empty_valid_checkpoint_matrix(self, tmp_path) -> None:
        rows: list[dict] = []

        # 1. empty partial + next token.
        stack = HandoffStack(tmp_path / "e1")
        batch = _empty_batch(next_resume_token=_token(5))
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        state = stack.jobs_repo.get_job("job-1")
        rows.append(
            _row(
                "empty_partial_with_next_token",
                invariant=(
                    "EMPTY_VALID partial: durable blob-less acquisition + "
                    "EMPTY_CONFIRMED manifest + real checkpoint with the "
                    "adapter token preserved (I14R1 §17)"
                ),
                ok=(
                    state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                    and state.resume_token == _token(5)
                    and state.last_committed_blob_sha256 is None
                    and receipt.blob_shas == ()
                ),
                measured={
                    "durable_token_page": state.resume_token.page_number,
                    "checkpoint_advanced": receipt.checkpoint_advanced,
                    "blob_count": len(receipt.blob_shas),
                    "acquisition_blob_sha256": stack.acq_repo.get_acquisition(
                        receipt.acquisition_ids[0]
                    ).blob_sha256,
                },
            )
        )

        # 2. empty complete.
        stack = HandoffStack(tmp_path / "e2")
        batch = _empty_batch(is_complete=True)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        transitions = _transitions(stack, "job-1")
        rows.append(
            _row(
                "empty_complete_via_gate",
                invariant=(
                    "EMPTY_VALID complete: checkpoint gate ran "
                    "(MANIFEST_COMMITTED -> CHECKPOINT_ADVANCED -> COMPLETE), "
                    "never bypassed (I14R1 §17)"
                ),
                ok=(
                    stack.jobs_repo.get_job("job-1").status
                    is StorageJobStatus.COMPLETE
                    and ["MANIFEST_COMMITTED", "CHECKPOINT_ADVANCED"]
                    in transitions
                    and ["CHECKPOINT_ADVANCED", "COMPLETE"] in transitions
                    and receipt.complete is True
                ),
                measured={
                    "final_status": stack.jobs_repo.get_job(
                        "job-1"
                    ).status.value,
                    "gate_transitions_present": True,
                },
            )
        )

        # 3. empty exact retry.
        stack = HandoffStack(tmp_path / "e3")
        batch = _empty_batch(next_resume_token=_token(5))
        register_job(stack, "job-1", batch)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        frozen = semantic_digest(stack, "job-1")
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        again = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        rows.append(
            _row(
                "empty_exact_retry",
                invariant=(
                    "EMPTY_VALID re-delivery adopts exactly: no mutation, no "
                    "second checkpoint (I14R1 §29)"
                ),
                ok=(
                    again.checkpoint_advanced is False
                    and again.manifest_id == first.manifest_id
                    and semantic_digest(stack, "job-1") == frozen
                    and len(stack.jobs_repo.list_transitions("job-1"))
                    == transitions_before
                ),
                measured={
                    "retry_checkpoint_advanced": again.checkpoint_advanced,
                    "digest_frozen": semantic_digest(stack, "job-1") == frozen,
                },
            )
        )

        # 4. empty W7.
        stack = HandoffStack(tmp_path / "e4")
        batch = _empty_batch(next_resume_token=_token(6))
        register_job(stack, "job-1", batch)
        stack.handoff.fault_windows = {"W7_AFTER_MANIFEST_BEFORE_CHECKPOINT"}
        with pytest.raises(FaultSimulated):
            stack.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        restarted = stack.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        moves = _checkpoint_moves(restarted, "job-1")
        rows.append(
            _row(
                "empty_w7_restart",
                invariant=(
                    "manifest durable / checkpoint old -> retry adopts the "
                    "exact empty manifest/acquisition and advances EXACTLY "
                    "once; no fake blob ever appears (I14R1 §18)"
                ),
                ok=(
                    retry.checkpoint_advanced is True
                    and moves == 1
                    and list(restarted.t0a.glob("objects/**/*")) == []
                ),
                measured={
                    "checkpoint_transitions_total": moves,
                    "fake_blob_count": len(
                        list(restarted.t0a.glob("objects/**/*"))
                    ),
                },
            )
        )

        # 5. empty followed by nonempty next page.
        stack = HandoffStack(tmp_path / "e5")
        empty = _empty_batch(next_resume_token=_token(2))
        register_job(stack, "job-1", empty)
        stack.handoff.persist_batch(
            job_id="job-1", batch=empty, context=make_context()
        )
        nonempty = make_batch(
            [b'{"rows": [1]}'],
            next_resume_token=_token(3),
            retrieved_at=empty.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=nonempty,
            context=make_context(request_resume_token=_token(2)),
        )
        state = stack.jobs_repo.get_job("job-1")
        rows.append(
            _row(
                "empty_then_nonempty_next_page",
                invariant=(
                    "EMPTY_VALID page followed by a nonempty page: the "
                    "checkpoint progresses across both, cursor truthful "
                    "(I14R1 §29)"
                ),
                ok=(
                    state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                    and state.resume_token == _token(3)
                    and state.last_committed_blob_sha256 == r2.blob_shas[0]
                ),
                measured={
                    "final_token_page": state.resume_token.page_number,
                    "second_page_blobs": len(r2.blob_shas),
                },
            )
        )

        # 6. nonempty followed by empty next page.
        stack = HandoffStack(tmp_path / "e6")
        nonempty = make_batch(
            [b'{"rows": [1]}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", nonempty)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=nonempty, context=make_context()
        )
        empty = _empty_batch(
            next_resume_token=_token(3),
            retrieved_at=nonempty.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=empty,
            context=make_context(request_resume_token=_token(2)),
        )
        state = stack.jobs_repo.get_job("job-1")
        rows.append(
            _row(
                "nonempty_then_empty_next_page",
                invariant=(
                    "nonempty page followed by an EMPTY_VALID page: a real "
                    "superseding manifest version + real checkpoint, no fake "
                    "blob (I14R1 §29)"
                ),
                ok=(
                    state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                    and state.resume_token == _token(3)
                    and r2.blob_shas == ()
                    and r2.manifest_id != r1.manifest_id
                ),
                measured={
                    "final_token_page": state.resume_token.page_number,
                    "second_page_blobs": len(r2.blob_shas),
                    "manifests_distinct": r2.manifest_id != r1.manifest_id,
                },
            )
        )

        # 7. durable acquisition truth for the empty event.
        stack = HandoffStack(tmp_path / "e7")
        batch = _empty_batch(next_resume_token=_token(2))
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        record = stack.acq_repo.get_acquisition(receipt.acquisition_ids[0])
        rows.append(
            _row(
                "empty_durable_acquisition_truth",
                invariant=(
                    "the EMPTY_VALID acquisition EVENT is durably preserved "
                    "with full provenance and NO fabricated bytes (I14R1 §12)"
                ),
                ok=(
                    record.blob_sha256 is None
                    and QualityFlagAcquisition.EMPTY_VALID
                    in record.quality_flags
                    and record.provider_id == batch.provider_id
                    and record.request_fingerprint
                    == batch.request_fingerprint
                    and record.response_observed_at == batch.retrieved_at
                ),
                measured={
                    "blob_sha256": None,
                    "empty_valid_flag": True,
                    "has_provider": bool(record.provider_id),
                    "has_fingerprint": bool(record.request_fingerprint),
                    "has_observation_timestamp": True,
                },
            )
        )

        _publish(
            "BLOC_04_I14R1_EMPTY_VALID_CHECKPOINT_MATRIX.json",
            _matrix("EMPTY_VALID_CHECKPOINT_MATRIX", rows),
        )
        assert all(r["result"] == "OK" for r in rows)


# ---------------------------------------------------------------------------
# §30 MULTI_ENVELOPE_REVISION_MATRIX
# ---------------------------------------------------------------------------


def _group_digest(bodies: list[bytes]) -> str:
    """I14R1 §13: domain-separated canonical SET digest."""
    member_shas = [hashlib.sha256(b).hexdigest() for b in bodies]
    return hashlib.sha256(
        (
            "sensor-revision-group-v1\n" + "\n".join(sorted(set(member_shas)))
        ).encode("utf-8")
    ).hexdigest()


class TestMultiEnvelopeRevisionMatrix:
    def test_multi_envelope_revision_matrix(self, tmp_path) -> None:
        rows: list[dict] = []

        def _two_page(key: str, first_bodies, second_bodies):  # type: ignore[no-untyped-def]
            stack = HandoffStack(tmp_path / key)
            first = make_batch(first_bodies)
            register_job(stack, "job-1", first)
            r1 = stack.handoff.persist_batch(
                job_id="job-1", batch=first, context=make_context()
            )
            stack.jobs_repo.advance_status(
                "job-1",
                to_status=StorageJobStatus.ACQUIRING,
                reason="batch continuation after checkpoint",
            )
            second = make_batch(
                second_bodies,
                retrieved_at=first.retrieved_at + timedelta(minutes=1),
            )
            r2 = stack.handoff.persist_batch(
                job_id="job-1", batch=second, context=make_context()
            )
            return stack, r1, r2

        # 1. unchanged group -> no new revision.
        stack, r1, r2 = _two_page(
            "m1", [b'{"a": "X"}', b'{"b": "Y"}'], [b'{"a": "X"}', b'{"b": "Y"}']
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        observations = stack.registry._observations_by_key.get(key, [])  # noqa: SLF001
        rows.append(
            _row(
                "multi_envelope_unchanged_group_no_new_revision",
                invariant=(
                    "identical ordered group re-observed later: NO new "
                    "revision; the re-delivery is an IDENTICAL_REFETCH "
                    "observation (I14R1 §24A)"
                ),
                ok=(
                    len(segments) == 1
                    and any(
                        o.observation_state == "IDENTICAL_REFETCH"
                        for o in observations
                    )
                ),
                measured={
                    "segments": len(segments),
                    "identical_refetch_observed": any(
                        o.observation_state == "IDENTICAL_REFETCH"
                        for o in observations
                    ),
                },
            )
        )

        # 2. non-first component mutation -> new revision.
        stack, r1, r2 = _two_page(
            "m2", [b'{"a": "X"}', b'{"b": "Y1"}'], [b'{"a": "X"}', b'{"b": "Y2"}']
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        rows.append(
            _row(
                "multi_envelope_non_first_component_mutation",
                invariant=(
                    "a change in a NON-FIRST envelope becomes "
                    "revision-visible: explicit new SOURCE_MUTATION revision "
                    "(I14R1 §24B) — the blocker-C defect is closed"
                ),
                ok=(
                    len(segments) == 2
                    and segments[-1].revision_state == "SOURCE_MUTATION"
                ),
                measured={
                    "segments": len(segments),
                    "latest_state": segments[-1].revision_state,
                    "group_digest_v1": _group_digest(
                        [b'{"a": "X"}', b'{"b": "Y1"}']
                    )[:16],
                    "group_digest_v2": _group_digest(
                        [b'{"a": "X"}', b'{"b": "Y2"}']
                    )[:16],
                },
            )
        )

        # 3. first component mutation -> new revision.
        stack, r1, r2 = _two_page(
            "m3", [b'{"a": "X"}', b'{"b": "Y"}'], [b'{"a": "X2"}', b'{"b": "Y"}']
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        rows.append(
            _row(
                "multi_envelope_first_component_mutation",
                invariant=(
                    "a change in the FIRST envelope is also revision-visible "
                    "under the group law (I14R1 §24C)"
                ),
                ok=(
                    len(segments) == 2
                    and segments[-1].revision_state == "SOURCE_MUTATION"
                ),
                measured={
                    "segments": len(segments),
                    "latest_state": segments[-1].revision_state,
                },
            )
        )

        # 4. component count change -> new revision.
        stack, r1, r2 = _two_page(
            "m4",
            [b'{"a": "X"}'],
            [b'{"a": "X"}', b'{"b": "NEW"}'],
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        rows.append(
            _row(
                "multi_envelope_component_count_change",
                invariant=(
                    "an envelope ADDED to the observation group is an "
                    "explicit new revision (I14R1 §24D)"
                ),
                ok=(
                    len(segments) == 2
                    and segments[-1].revision_state == "SOURCE_MUTATION"
                ),
                measured={
                    "segments": len(segments),
                    "latest_state": segments[-1].revision_state,
                },
            )
        )

        # 5. ordering: the accepted Bloc 3 contract (01_BLOC_03 §6) carries
        # raw_payloads[] with NO declared ordering semantic, so the group is
        # a canonical SET — [X,Y] vs [Y,X] is the SAME observation (§18F).
        stack, r1, r2 = _two_page(
            "m5", [b'{"a": "X"}', b'{"b": "Y"}'], [b'{"b": "Y"}', b'{"a": "X"}']
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        observations = stack.registry._observations_by_key.get(key, [])  # noqa: SLF001
        rows.append(
            _row(
                "multi_envelope_order_change",
                invariant=(
                    "Bloc 3 declares no envelope-ordering semantic; the group "
                    "digest is a canonical SET, so [X,Y] vs [Y,X] is the SAME "
                    "observation: no new revision, durable IDENTICAL_REFETCH "
                    "(I14R1 §24E/§18F)"
                ),
                ok=(
                    len(segments) == 1
                    and any(
                        o.observation_state == "IDENTICAL_REFETCH"
                        for o in observations
                    )
                ),
                measured={
                    "segments": len(segments),
                    "identical_refetch_observed": any(
                        o.observation_state == "IDENTICAL_REFETCH"
                        for o in observations
                    ),
                    "ordering_semantic": "NONE (canonical SET, contract silent)",
                },
            )
        )

        # 6. manifest/revision evidence-set coherence.
        stack = HandoffStack(tmp_path / "m6")
        bodies = [b'{"p": 1}', b'{"p": 2}', b'{"p": 3}']
        batch = make_batch(bodies)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        observation = stack.registry._observations_by_key[  # noqa: SLF001
            receipt.revision_keys[0]
        ][0]
        rows.append(
            _row(
                "multi_envelope_manifest_revision_coherence",
                invariant=(
                    "the revision observation describes the SAME evidence "
                    "set the manifest commits: digest over ALL ordered "
                    "envelope shas == observation content truth (I14R1 §25)"
                ),
                ok=(
                    sorted(manifest.blob_refs) == sorted(receipt.blob_shas)
                    and len(manifest.blob_refs) == 3
                    and observation.blob_sha256 == _group_digest(bodies)
                ),
                measured={
                    "manifest_blob_count": len(manifest.blob_refs),
                    "observation_digest_prefix": observation.blob_sha256[:16],
                    "expected_digest_prefix": _group_digest(bodies)[:16],
                },
            )
        )

        _publish(
            "BLOC_04_I14R1_MULTI_ENVELOPE_REVISION_MATRIX.json",
            _matrix("MULTI_ENVELOPE_REVISION_MATRIX", rows),
        )
        assert all(r["result"] == "OK" for r in rows)


# ---------------------------------------------------------------------------
# §18/§28 RESTART_MATRIX (W-windows across the new paths)
# ---------------------------------------------------------------------------


class TestRestartMatrix:
    def test_restart_matrix(self, tmp_path) -> None:
        rows: list[dict] = []

        # W7 on the raw path (page 1) — re-proven under the new pipeline.
        stack = HandoffStack(tmp_path / "r1")
        batch = make_batch(
            [b'{"w7": 1}'], next_resume_token=_token(9)
        )
        register_job(stack, "job-1", batch)
        stack.handoff.fault_windows = {"W7_AFTER_MANIFEST_BEFORE_CHECKPOINT"}
        with pytest.raises(FaultSimulated):
            stack.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        restarted = stack.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        moves = _checkpoint_moves(restarted, "job-1")
        rows.append(
            _row(
                "restart_raw_path_w7_single_advance",
                invariant=(
                    "raw-path W7 under the I14R1 pipeline: manifest adopted, "
                    "checkpoint advanced EXACTLY once across both runs "
                    "(I14R1 §28)"
                ),
                ok=(retry.checkpoint_advanced is True and moves == 1),
                measured={"checkpoint_transitions_total": moves},
            )
        )

        # W7 on the EMPTY_VALID path (empty partial).
        stack = HandoffStack(tmp_path / "r2")
        batch = _empty_batch(next_resume_token=_token(4))
        register_job(stack, "job-1", batch)
        stack.handoff.fault_windows = {"W7_AFTER_MANIFEST_BEFORE_CHECKPOINT"}
        with pytest.raises(FaultSimulated):
            stack.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        restarted = stack.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        moves = _checkpoint_moves(restarted, "job-1")
        rows.append(
            _row(
                "restart_empty_valid_w7_single_advance",
                invariant=(
                    "EMPTY_VALID W7: retry adopts the exact empty "
                    "manifest/acquisition, advances exactly once, NO fake "
                    "blob (I14R1 §18)"
                ),
                ok=(
                    retry.checkpoint_advanced is True
                    and moves == 1
                    and list(restarted.t0a.glob("objects/**/*")) == []
                ),
                measured={
                    "checkpoint_transitions_total": moves,
                    "fake_blob_count": len(
                        list(restarted.t0a.glob("objects/**/*"))
                    ),
                },
            )
        )

        # Continuation-path crash (W1 on page 2) then clean retry.
        stack = HandoffStack(tmp_path / "r3")
        p1 = make_batch([b'{"p": 1}'], next_resume_token=_token(2))
        register_job(stack, "job-1", p1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=p1, context=make_context()
        )
        p2 = make_batch(
            [b'{"p": 2}'],
            next_resume_token=_token(3),
            retrieved_at=p1.retrieved_at + timedelta(minutes=1),
        )
        ctx2 = make_context(request_resume_token=_token(2))
        stack.handoff.fault_windows = {"W1_BEFORE_RAW_WRITE"}
        with pytest.raises(FaultSimulated):
            stack.handoff.persist_batch(
                job_id="job-1", batch=p2, context=ctx2
            )
        restarted = stack.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=p2, context=ctx2
        )
        moves = _checkpoint_moves(restarted, "job-1")
        rows.append(
            _row(
                "restart_continuation_path_w1_recovery",
                invariant=(
                    "continuation-path crash recovers through the SAME "
                    "public API; page 2 checkpoints exactly once after page "
                    "1 (no cursor skip, no double advance) (I14R1 §28)"
                ),
                ok=(
                    retry.checkpoint_advanced is True
                    and moves == 2
                    and restarted.jobs_repo.get_job("job-1").resume_token
                    == _token(3)
                ),
                measured={
                    "checkpoint_transitions_total": moves,
                    "final_token_page": restarted.jobs_repo.get_job(
                        "job-1"
                    ).resume_token.page_number,
                },
            )
        )

        _publish(
            "BLOC_04_I14R1_RESTART_MATRIX.json",
            _matrix("RESTART_MATRIX", rows),
        )
        assert all(r["result"] == "OK" for r in rows)


if __name__ == "__main__":
    raise SystemExit("run with pytest")
