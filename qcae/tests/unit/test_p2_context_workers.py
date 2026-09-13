"""P2-C06 — Context Packet + worker contract qualification (directive §18-20)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.orchestration.context.packet import ContextPacket, make_context_packet
from qcae.orchestration.workers.base import (
    ApprovalRequiredWorker,
    CrashWorker,
    DeterministicSuccessWorker,
    EchoWorker,
    PermanentFailureWorker,
    RetryOnceWorker,
)
from qcae.orchestration.workers.contracts import (
    WorkerClaim,
    WorkerRequest,
    WorkerResult,
    WorkerStatus,
    make_worker_request,
    make_worker_result,
)


def _packet(**over):
    base = dict(
        packet_id="pkt-00000001",
        job_id="job-12345678",
        step_id="s-00000001",
        worker_type="echo",
    )
    base.update(over)
    return ContextPacket(**base)


def _request(**over):
    base = dict(
        job_id="job-12345678",
        step_id="s-00000001",
        worker_type="echo",
    )
    base.update(over)
    return WorkerRequest(**base)


class TestContextPacket:
    def test_round_trip_and_digest_stable(self):
        p = _packet(
            evidence_refs=("ev-1", "ev-2"),
            allowed_tools=("fetch",),
            contract_ref="CAP-1",
            contract_version=2,
        )
        restored = ContextPacket.from_dict(p.to_dict())
        assert restored == p
        assert restored.digest() == p.digest()

    def test_least_context_no_project_memory_field(self):
        """The packet cannot smuggle unbounded prose/history fields."""
        assert not hasattr(_packet(), "history")
        assert not hasattr(_packet(), "conversation")
        assert not hasattr(_packet(), "project_memory")

    def test_unrelated_registry_context_absent_by_construction(self):
        """A packet built for step B does not carry step A's registry refs."""
        packet_b = make_context_packet(
            packet_id="pkt-2", job_id="job-12345678", step_id="s-00000002",
            worker_type="echo", registry_refs=("reg-for-step-b",),
        )
        assert "reg-for-step-b" in packet_b.registry_refs
        assert all("step-a" not in r for r in packet_b.registry_refs)

    def test_authority_constraints_included(self):
        p = _packet(authority_decision_ref="authdec-00000001")
        assert p.authority_decision_ref == "authdec-00000001"

    def test_contract_version_requires_ref(self):
        with pytest.raises(QcaeValidationError, match="contract_ref"):
            _packet(contract_version=3).validate()

    def test_duplicate_evidence_refs_rejected(self):
        with pytest.raises(QcaeValidationError, match="duplicate"):
            _packet(evidence_refs=("ev-1", "ev-1")).validate()


class TestWorkerContracts:
    def test_status_vocabulary_is_canon_123(self):
        assert {s.value for s in WorkerStatus} == {
            "SUCCESS", "PARTIAL", "FAILED", "BLOCKED_POLICY", "BLOCKED_INPUT",
            "INCONCLUSIVE", "RETRYABLE", "CANCELLED",
        }

    def test_request_round_trip(self):
        r = _request(
            input_artifact_refs=("art-1",),
            requested_outputs=("out-1",),
            idempotency_key="key-1",
        )
        assert WorkerRequest.from_dict(r.to_dict()) == r

    def test_result_round_trip_with_claims(self):
        result = make_worker_result(
            step_id="s-00000001", job_id="job-12345678",
            status=WorkerStatus.SUCCESS,
            claims=(
                WorkerClaim(
                    claim_id="claim-1", statement="X is Y",
                    verification_state="SOURCE_SUPPORTED",
                    evidence_refs=("ev-1",),
                ),
            ),
        )
        restored = WorkerResult.from_dict(result.to_dict())
        assert restored == result
        assert isinstance(restored.claims[0], WorkerClaim)

    def test_claim_without_evidence_rejected(self):
        with pytest.raises(QcaeValidationError, match="evidence"):
            make_worker_result(
                step_id="s-00000001", job_id="job-12345678",
                status=WorkerStatus.SUCCESS,
                claims=(
                    WorkerClaim(
                        claim_id="claim-1", statement="X is Y",
                        verification_state="CLAIMED",
                    ),
                ),
            )

    def test_failed_result_requires_failure_class(self):
        with pytest.raises(QcaeValidationError, match="failure_class"):
            make_worker_result(
                step_id="s-00000001", job_id="job-12345678",
                status=WorkerStatus.FAILED, error_summary="boom",
            )

    def test_retryable_requires_error_summary(self):
        with pytest.raises(QcaeValidationError, match="error_summary"):
            make_worker_result(
                step_id="s-00000001", job_id="job-12345678",
                status=WorkerStatus.RETRYABLE, failure_class="TRANSIENT",
            )

    def test_unknown_status_rejected(self):
        with pytest.raises(QcaeValidationError, match="status"):
            make_worker_result(
                step_id="s-00000001", job_id="job-12345678", status="MIRACLE"
            )


class TestBuiltinWorkers:
    def test_echo_worker(self):
        result = EchoWorker().execute(
            _request(requested_outputs=("out-1",), input_artifact_refs=("in-1",)),
            _packet(),
        )
        assert result.status is WorkerStatus.SUCCESS

    def test_deterministic_success_counts_calls(self):
        w = DeterministicSuccessWorker()
        r1 = w.execute(_request(), _packet())
        r2 = w.execute(_request(), _packet())
        assert r1.status is r2.status is WorkerStatus.SUCCESS
        assert w.calls == 2

    def test_retry_once_then_success(self):
        w = RetryOnceWorker()
        first = w.execute(_request(), _packet())
        assert first.status is WorkerStatus.RETRYABLE
        assert first.failure_class == "TRANSIENT"
        second = w.execute(_request(), _packet())
        assert second.status is WorkerStatus.SUCCESS

    def test_permanent_failure_classified(self):
        result = PermanentFailureWorker().execute(_request(), _packet())
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "PERMANENT"

    def test_approval_required_blocked(self):
        result = ApprovalRequiredWorker().execute(_request(), _packet())
        assert result.status is WorkerStatus.BLOCKED_POLICY
        assert result.failure_class == "APPROVAL_REQUIRED"

    def test_crash_worker_raises(self):
        with pytest.raises(RuntimeError, match="crash"):
            CrashWorker().execute(_request(), _packet())

    def test_workers_satisfy_protocol(self):
        for w in (
            EchoWorker(), DeterministicSuccessWorker(), RetryOnceWorker(),
            PermanentFailureWorker(), ApprovalRequiredWorker(), CrashWorker(),
        ):
            assert isinstance(w, type(EchoWorker())) or callable(w.execute)
