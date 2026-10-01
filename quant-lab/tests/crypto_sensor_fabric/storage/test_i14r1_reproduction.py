"""SENSOR-B4-I14R1 — FAILURE-FIRST reproductions of the three operator
review blockers (I14R1 §1).

Each class reproduces one blocker against the CURRENT accepted I14
implementation, exactly as the operator review found it.  They are the
RED evidence for I14R1A-C; once the repairs land, they become the
permanent blocking regression suite for the repaired contract.

- Blocker A (§2): persist_batch() on a job at CHECKPOINT_ADVANCED with a
  genuine NEXT paginated batch raises BatchAlreadyCompleted — the public
  caller is forced to drive I07 internals (advance_status) by hand.
- Blocker B (§11): an EMPTY_VALID durable batch commits the zero-blob
  manifest but never advances the checkpoint; a valid next_resume_token
  is dropped and the receipt disagrees with durable state.
- Blocker C (§19): a multi-envelope batch registers revisions from
  acquisition_ids[0] ONLY — a non-first envelope change is durable in
  T0A/manifest without becoming revision-visible.

All fixtures are synthetic/offline: no socket, no live provider.
"""

from __future__ import annotations

import hashlib
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
make_context = i14.make_context
register_job = i14.register_job

from crypto_sensor_fabric.providers.base.enums import (  # noqa: E402
    PaginationMode,
    QualityFlagAcquisition,
)
from crypto_sensor_fabric.providers.base.models import (  # noqa: E402
    ResumeToken,
)
from crypto_sensor_fabric.storage.enums import StorageJobStatus  # noqa: E402
from crypto_sensor_fabric.storage.integration import (  # noqa: E402
    BatchAlreadyCompleted,
    DivergentBatchRewrite,
    FaultSimulated,
)


def make_context(**overrides):  # type: ignore[no-untyped-def]  # noqa: F811
    """I14 fixture context with the upstream request_resume_token seam.

    Intentionally shadows the sibling fixture of the same name (same
    defaults) to add the ``request_resume_token`` override seam."""
    defaults: dict = {
        "venue": "kraken_spot",
        "source_granularity": i14.Granularity.G1M,
        "endpoint_host": "api.kraken.example",
        "endpoint_path": "/v3/trades",
        "request_family": "trades",
    }
    defaults.update(overrides)
    return i14.Bloc3StorageContext(**defaults)


def _token(page: int) -> ResumeToken:
    return ResumeToken(mode=PaginationMode.PAGE, page_number=page)


class TestNextBatchContinuationRepro:
    """Blocker A reproduction (§2): public API only, no external I07 drive."""

    def test_next_paginated_batch_after_checkpoint_without_external_drive(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        page1 = make_batch(
            [b'{"page": 1}'],
            next_resume_token=_token(2),
        )
        register_job(stack, "job-1", page1)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
        )
        assert stack.jobs_repo.get_job("job-1").resume_token == _token(2)

        # Page 2: the SAME job, the genuine NEXT batch, fetched FROM the
        # checkpoint's resume token — proven by the accepted upstream
        # request context (context.request_resume_token), and NO external
        # advance_status call.
        page2 = make_batch(
            [b'{"page": 2}'],
            next_resume_token=_token(3),
            # A real paginated fetch observes page 2 LATER than page 1;
            # I06 §40 refuses same-instant differing observations.
            retrieved_at=page1.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=page2,
            context=make_context(request_resume_token=_token(2)),
        )
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token == _token(3)
        assert r2.checkpoint_advanced is True
        assert r2.manifest_id != r1.manifest_id


class TestEmptyValidProgressRepro:
    """Blocker B reproduction (§11): EMPTY_VALID cannot progress."""

    def test_empty_partial_drops_valid_next_token(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [],
            row_count=0,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            next_resume_token=_token(5),
        )
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        state = stack.jobs_repo.get_job("job-1")
        # A valid adapter next token must survive an EMPTY_VALID page and
        # the durable job must actually progress to CHECKPOINT_ADVANCED.
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token == _token(5)
        assert receipt.resume_token == _token(5)
        assert receipt.checkpoint_advanced is True
        # No fake bytes anywhere.
        assert receipt.blob_shas == ()
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        assert manifest.blob_refs == []

    def test_empty_complete_reaches_complete(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [],
            row_count=0,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            is_complete=True,
        )
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.COMPLETE
        assert receipt.complete is True
        assert receipt.blob_shas == ()


class TestMultiEnvelopeRevisionRepro:
    """Blocker C reproduction (§19): non-first envelope change is
    revision-invisible under the current acquisition_ids[0] rule."""

    def test_non_first_envelope_change_becomes_revision_visible(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        first = make_batch(
            [b'{"env": "X"}', b'{"env": "Y1"}'],
        )
        register_job(stack, "job-1", first)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=first, context=make_context()
        )
        keys1 = list(r1.revision_keys)
        segments1 = sorted(
            s.segment_id
            for key in stack.registry.list_source_revision_keys()
            for s in stack.registry.list_segment_records(key)
        )
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )

        # Batch B: envelope 1 IDENTICAL (X), envelope 2 CHANGED (Y1 -> Y2),
        # later observation instant (I06 §40 refuses same-instant ordering).
        second = make_batch(
            [b'{"env": "X"}', b'{"env": "Y2"}'],
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        keys2 = list(r2.revision_keys)
        segments2 = sorted(
            s.segment_id
            for key in stack.registry.list_source_revision_keys()
            for s in stack.registry.list_segment_records(key)
        )

        # The changed SECOND envelope must move revision state: the
        # observation covers the COMPLETE ordered envelope group, so the
        # observation evidence set must differ between the two batches.
        assert keys2 != keys1 or segments2 != segments1
        # ...and never regress the durable job state.
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
        )


class TestContinuationMandate:
    """I14R1 §7-§10: the mandated continuation proofs."""

    def test_three_pages_public_api_only(self, tmp_path) -> None:
        """§7: three sequential pages, single job, ONLY persist_batch.
        No external job-state manipulation anywhere (manipulation count = 0)."""
        stack = HandoffStack(tmp_path / "s")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        ctx1 = make_context()
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=ctx1
        )
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
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
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
        )

        page3 = make_batch(
            [b'{"page": 3}'],
            is_complete=True,
            retrieved_at=page1.retrieved_at + timedelta(minutes=2),
        )
        r3 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=page3,
            context=make_context(request_resume_token=_token(3)),
        )
        assert r3.complete is True
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.COMPLETE
        transitions = [
            [t.from_status.value, t.to_status.value]
            for t in stack.jobs_repo.list_transitions("job-1")
        ]
        checkpoint_moves = [
            t for t in transitions if t[1] == "CHECKPOINT_ADVANCED"
        ]
        # EXACTLY 3 checkpoint transitions; each continuation advanced
        # through the accepted annotated edge, no skipped page, no double.
        assert len(checkpoint_moves) == 3
        continuation_edges = [
            t for t in transitions if t == ["CHECKPOINT_ADVANCED", "ACQUIRING"]
        ]
        assert len(continuation_edges) == 2
        assert r1.checkpoint_advanced and r2.checkpoint_advanced
        assert r1.manifest_id != r2.manifest_id != r3.manifest_id

    def test_exact_retry_after_checkpoint_adopts_then_continues(
        self, tmp_path
    ) -> None:
        """§8: page 1 re-delivery adopts exactly; page 2 then continues."""
        stack = HandoffStack(tmp_path / "s")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        frozen = stack.jobs_repo.get_job("job-1")
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        # EXACT retry: same batch, same context.
        retry = stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        assert retry.checkpoint_advanced is False
        assert retry.manifest_id == first.manifest_id
        after = stack.jobs_repo.get_job("job-1")
        assert after.resume_token == frozen.resume_token
        assert len(stack.jobs_repo.list_transitions("job-1")) == (
            transitions_before
        )
        # No new manifest version.
        pointer = stack.manifest_repo.read_current_pointer(
            first.manifest_id.split("::v")[0]
        )
        assert pointer is not None
        assert stack.manifest_repo.get_manifest(
            pointer.partition_manifest_id
        ).manifest_version == first.manifest_version
        # Then page 2 continues normally.
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
        assert r2.checkpoint_advanced is True
        assert stack.jobs_repo.get_job("job-1").resume_token == _token(3)

    def test_stale_request_token_refused_before_mutation(
        self, tmp_path
    ) -> None:
        """§9: an incoming batch claiming an unrelated resume source fails
        typed BEFORE any evidence mutation."""
        stack = HandoffStack(tmp_path / "s")
        page1 = make_batch(
            [b'{"page": 1}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", page1)
        stack.handoff.persist_batch(
            job_id="job-1", batch=page1, context=make_context()
        )
        frozen_digest = i14.semantic_digest(stack, "job-1")
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        stale = make_batch(
            [b'{"stale": true}'],
            next_resume_token=_token(9),
            retrieved_at=page1.retrieved_at + timedelta(minutes=1),
        )
        with pytest.raises(DivergentBatchRewrite):
            stack.handoff.persist_batch(
                job_id="job-1",
                batch=stale,
                # Claims it was fetched from page 7 — unrelated to the
                # durable page-2 token.
                context=make_context(request_resume_token=_token(7)),
            )
        # Zero mutation: no ACQUIRING transition, no checkpoint movement,
        # no durable write.
        assert i14.semantic_digest(stack, "job-1") == frozen_digest
        assert len(stack.jobs_repo.list_transitions("job-1")) == (
            transitions_before
        )
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
        )

    def test_complete_is_terminal_no_reopen(self, tmp_path) -> None:
        """§10: exact final-batch retry adopts read-only; any NEW batch is
        a typed terminal refusal (never COMPLETE -> ACQUIRING)."""
        stack = HandoffStack(tmp_path / "s")
        final = make_batch([b'{"final": 1}'], is_complete=True)
        register_job(stack, "job-1", final)
        stack.handoff.persist_batch(
            job_id="job-1", batch=final, context=make_context()
        )
        frozen_digest = i14.semantic_digest(stack, "job-1")
        # Exact retry: read-only adoption.
        again = stack.handoff.persist_batch(
            job_id="job-1", batch=final, context=make_context()
        )
        assert again.checkpoint_advanced is False
        assert again.complete is True
        assert i14.semantic_digest(stack, "job-1") == frozen_digest
        # New next batch: typed terminal refusal.
        with pytest.raises(BatchAlreadyCompleted):
            stack.handoff.persist_batch(
                job_id="job-1",
                batch=make_batch(
                    [b'{"after": 1}'],
                    next_resume_token=_token(2),
                    retrieved_at=final.retrieved_at + timedelta(minutes=1),
                ),
                context=make_context(request_resume_token=None),
            )
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.COMPLETE
        )
        assert i14.semantic_digest(stack, "job-1") == frozen_digest

    def test_duplicate_next_page_delivery_is_stable(self, tmp_path) -> None:
        """§28: duplicate next-page delivery — exact retry adoption, no
        cursor skip, no second checkpoint."""
        stack = HandoffStack(tmp_path / "s")
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
        ctx2 = make_context(request_resume_token=_token(2))
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=page2, context=ctx2
        )
        transitions_after_first = len(
            stack.jobs_repo.list_transitions("job-1")
        )
        frozen_digest = i14.semantic_digest(stack, "job-1")
        dup = stack.handoff.persist_batch(
            job_id="job-1", batch=page2, context=ctx2
        )
        assert dup.checkpoint_advanced is False
        assert dup.manifest_id == first.manifest_id
        assert i14.semantic_digest(stack, "job-1") == frozen_digest
        assert len(stack.jobs_repo.list_transitions("job-1")) == (
            transitions_after_first
        )
        # No cursor skip: durable token is exactly page 3.
        assert stack.jobs_repo.get_job("job-1").resume_token == _token(3)


class TestEmptyValidMandate:
    """I14R1 §11/§17/§18/§29: EMPTY_VALID progress + restart law."""

    def _empty_batch(
        self,
        *,
        is_complete: bool = False,
        page: int | None = None,
        retrieved_at=None,
    ):
        return make_batch(
            [],
            row_count=0,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            is_complete=is_complete,
            next_resume_token=_token(page) if page is not None else None,
            retrieved_at=retrieved_at,
        )

    def test_empty_partial_checkpoints_with_token(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = self._empty_batch(page=4)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token == _token(4)
        assert state.last_committed_blob_sha256 is None
        assert receipt.checkpoint_advanced is True
        assert receipt.blob_shas == ()
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        assert manifest.blob_refs == []
        # No fake T0A blob anywhere.
        assert list(stack.t0a.glob("objects/**/*")) == []

    def test_empty_complete_reaches_complete_via_gate(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = self._empty_batch(is_complete=True)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.COMPLETE
        transitions = [
            [t.from_status.value, t.to_status.value]
            for t in stack.jobs_repo.list_transitions("job-1")
        ]
        # The gate ran: CHECKPOINT_ADVANCED happened before COMPLETE.
        assert ["MANIFEST_COMMITTED", "CHECKPOINT_ADVANCED"] in transitions
        assert ["CHECKPOINT_ADVANCED", "COMPLETE"] in transitions
        assert receipt.complete is True

    def test_empty_exact_retry_adopts_without_mutation(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = self._empty_batch(page=4)
        register_job(stack, "job-1", batch)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        frozen_digest = i14.semantic_digest(stack, "job-1")
        transitions_before = len(stack.jobs_repo.list_transitions("job-1"))
        again = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert again.checkpoint_advanced is False
        assert again.manifest_id == first.manifest_id
        assert i14.semantic_digest(stack, "job-1") == frozen_digest
        assert len(stack.jobs_repo.list_transitions("job-1")) == (
            transitions_before
        )

    def test_empty_w7_restart_adopts_and_advances_exactly_once(
        self, tmp_path
    ) -> None:
        """§18: manifest durable / checkpoint old -> retry adopts the exact
        empty manifest/acquisition and advances the checkpoint EXACTLY once.
        No fake blob ever appears."""
        clean_root = tmp_path / "clean"
        clean_root.mkdir()
        clean = HandoffStack(clean_root)
        batch = self._empty_batch(page=6)
        register_job(clean, "job-1", batch)
        clean_receipt = clean.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        clean_digest = i14.semantic_digest(clean, "job-1")

        crash_root = tmp_path / "crash"
        crash_root.mkdir()
        crashed = HandoffStack(crash_root)
        register_job(crashed, "job-1", batch)
        crashed.handoff.fault_windows = {i14.FAULT_WINDOWS[6]}  # W7
        with pytest.raises(FaultSimulated):
            crashed.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        # Manifest IS durable, checkpoint is OLD.
        assert crashed.manifest_repo.get_manifest(
            clean_receipt.manifest_id
        ) is not None
        state = crashed.jobs_repo.get_job("job-1")
        assert state.status is not StorageJobStatus.CHECKPOINT_ADVANCED

        restarted = crashed.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert retry.manifest_id == clean_receipt.manifest_id
        assert retry.checkpoint_advanced is True
        # EXACTLY one checkpoint transition across BOTH runs.
        checkpoint_transitions = [
            t
            for t in restarted.jobs_repo.list_transitions("job-1")
            if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        assert len(checkpoint_transitions) == 1
        assert i14.semantic_digest(restarted, "job-1") == clean_digest
        # No fake blob ever appeared.
        assert list(restarted.t0a.glob("objects/**/*")) == []

    def test_empty_followed_by_nonempty_next_page(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        empty = self._empty_batch(page=2)
        register_job(stack, "job-1", empty)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=empty, context=make_context()
        )
        assert r1.checkpoint_advanced is True
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
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token == _token(3)
        assert state.last_committed_blob_sha256 == r2.blob_shas[0]

    def test_nonempty_followed_by_empty_next_page(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        nonempty = make_batch(
            [b'{"rows": [1]}'], next_resume_token=_token(2)
        )
        register_job(stack, "job-1", nonempty)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=nonempty, context=make_context()
        )
        assert r1.checkpoint_advanced is True
        empty = self._empty_batch(
            page=3,
            retrieved_at=nonempty.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1",
            batch=empty,
            context=make_context(request_resume_token=_token(2)),
        )
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token == _token(3)
        assert r2.blob_shas == ()
        assert r2.manifest_id != r1.manifest_id


class TestMultiEnvelopeMandate:
    """I14R1 §24/§25/§30: full multi-envelope revision law through I06."""

    def _segments(self, stack):  # type: ignore[no-untyped-def]
        return sorted(
            s.segment_id
            for key in stack.registry.list_source_revision_keys()
            for s in stack.registry.list_segment_records(key)
        )

    def _advance(self, stack, batch):  # type: ignore[no-untyped-def]
        """Drive a continuation between two DIFFERENT-window observations
        (distinct partitions) — or same partition via the classifier."""
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )

    def _register(self, stack, batch, **ctx):  # type: ignore[no-untyped-def]
        register_job(stack, "job-1", batch)
        return stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context(**ctx)
        )

    def test_unchanged_group_no_new_revision(self, tmp_path) -> None:
        """§24A: identical group bytes re-observed later — no new revision."""
        stack = HandoffStack(tmp_path / "s")
        first = make_batch([b'{"a": "X"}', b'{"b": "Y"}'])
        r1 = self._register(stack, first)
        segs1 = self._segments(stack)
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        second = make_batch(
            [b'{"a": "X"}', b'{"b": "Y"}'],
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        segs2 = self._segments(stack)
        assert segs2 == segs1  # no new revision segment
        # The re-delivery is a durable IDENTICAL_REFETCH observation.
        key = r1.revision_keys[0]
        obs_states = {
            o.observation_state
            for o in stack.registry.list_segment_records(key) and []
        }
        observations = [
            o
            for o in stack.registry._observations_by_key.get(  # noqa: SLF001
                key, []
            )
        ]
        assert any(
            o.observation_state == "IDENTICAL_REFETCH" for o in observations
        ) or obs_states

    def test_non_first_component_mutation_new_revision(
        self, tmp_path
    ) -> None:
        """§24B: first unchanged / second CHANGED — explicit new revision."""
        stack = HandoffStack(tmp_path / "s")
        first = make_batch([b'{"a": "X"}', b'{"b": "Y1"}'])
        r1 = self._register(stack, first)
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        second = make_batch(
            [b'{"a": "X"}', b'{"b": "Y2"}'],
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        assert len(segments) == 2
        assert segments[-1].revision_state == "SOURCE_MUTATION"

    def test_first_component_mutation_new_revision(self, tmp_path) -> None:
        """§24C: first CHANGED / second unchanged — explicit new revision."""
        stack = HandoffStack(tmp_path / "s")
        first = make_batch([b'{"a": "X"}', b'{"b": "Y"}'])
        r1 = self._register(stack, first)
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        second = make_batch(
            [b'{"a": "X2"}', b'{"b": "Y"}'],
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        assert len(segments) == 2
        assert segments[-1].revision_state == "SOURCE_MUTATION"

    def test_component_count_change_new_revision(self, tmp_path) -> None:
        """§24D: envelope added — explicit new revision."""
        stack = HandoffStack(tmp_path / "s")
        first = make_batch([b'{"a": "X"}'])
        r1 = self._register(stack, first)
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        second = make_batch(
            [b'{"a": "X"}', b'{"b": "NEW"}'],
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        key = r1.revision_keys[0]
        segments = stack.registry.list_segment_records(key)
        assert len(segments) == 2
        assert segments[-1].revision_state == "SOURCE_MUTATION"

    def test_manifest_evidence_set_matches_observation_group(
        self, tmp_path
    ) -> None:
        """§25: manifest evidence set == revision observation set for a
        multi-envelope batch (no surrogate first-blob-only tracking)."""
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [b'{"p": 1}', b'{"p": 2}', b'{"p": 3}']
        )
        receipt = self._register(stack, batch)
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        assert sorted(manifest.blob_refs) == sorted(receipt.blob_shas)
        assert len(manifest.blob_refs) == 3
        # The group observation digest covers ALL THREE member shas over
        # the domain-separated canonical set (I14R1 §13).
        key = receipt.revision_keys[0]
        observation = stack.registry._observations_by_key[key][  # noqa: SLF001
            0
        ]
        member_shas = [
            hashlib.sha256(b).hexdigest()
            for b in (b'{"p": 1}', b'{"p": 2}', b'{"p": 3}')
        ]
        expected_digest = hashlib.sha256(
            (
                "sensor-revision-group-v1\n"
                + "\n".join(sorted(set(member_shas)))
            ).encode("utf-8")
        ).hexdigest()
        assert observation.blob_sha256 == expected_digest
        # §16: the complete member lineage is durably reconstructible.
        assert observation.content_scope == "GROUP_OBSERVATION"
        assert sorted(observation.member_blob_sha256 or []) == sorted(
            set(member_shas)
        )
        assert sorted(observation.member_acquisition_ids or []) == sorted(
            receipt.acquisition_ids
        )


if __name__ == "__main__":
    raise SystemExit("run with pytest")
