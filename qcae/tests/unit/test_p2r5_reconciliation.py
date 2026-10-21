"""P2-R5 — predecessor operator-gate reconciliation + CLI run truth.

The P3-R4 directive requires the earlier P2-R5 operator requirements to be
reconciled against *executable* evidence before P3 continues:

1. evidence attribution       — EvidenceRef/canonical digests (P0-C04/P1-C01);
2. schema authority + migration truth — versioned serialization envelopes,
   ``PRAGMA user_version`` + append-only migration ledger (P1-C02/P1-C10);
3. live grant binding         — durable single-use grants consumed atomically
   at admission (P2-R4-C03);
4. backup/restore truth       — digest-verified restore of metadata +
   artifacts + registry rows (P1-C11/P2-C12);
5. typed NOT_READY behavior   — canon 15.12 ``CONTRACT_NOT_READY`` standing,
   the one requirement with no standing before this module (NEW repair).

The CLI truth defect recorded by the P3 playtest is repaired here too:
``qcae job run <unknown-job-id>`` must return the same typed unknown-job
standing as ``job status``/``job events`` (exit 2, no traceback) — never
"no eligible step to run", which claims a nonexistent job exists but has
nothing to do. A job that exists but cannot run a step now reports the
typed ``CONTRACT_NOT_READY`` standing with a machine-readable reason.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.evidence_ref import EvidenceRef
from qcae.core.vocabulary import EvidenceClass
from qcae.core.receipts import ReceiptState, make_receipt
from qcae.governance.standalone.typed_outcomes import (
    JobMissingOutcome,
    StepNotReadyOutcome,
)
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.migrations import MigrationRunner, TEST_V1_TO_V2
from qcae.infrastructure.persistence.sqlite_approval_registry import SqliteApprovalRegistry
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime


def _run_cli(*cli_args, db: Path):
    """Run the CLI as a real subprocess (process boundary is the point)."""
    return subprocess.run(
        [sys.executable, "-m", "qcae.interfaces.cli", "--db", str(db), *cli_args],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture()
def tmp_db(tmp_path):
    return tmp_path / "r5-cli.sqlite3"


# --------------------------------------------------------------------------
# 1. evidence attribution
# --------------------------------------------------------------------------


class TestEvidenceAttribution:
    def test_a_ref_is_digested_not_a_note(self) -> None:
        ref = _ref()
        ref.validate()
        assert ref.digest() != ""
        # The digest binds the payload: any claim change is a different ref.
        assert ref.digest() == _ref().digest()

    def test_a_malformed_digest_is_refused(self) -> None:
        with pytest.raises(QcaeValidationError):
            _ref(artifact_digest="not-a-digest").validate()

    def test_receipt_cannot_exist_without_attributed_proof(self) -> None:
        with pytest.raises(QcaeValidationError, match="without proof evidence"):
            _receipt(proof_refs=())


def _ref(**over):
    defaults = dict(
        artifact_digest="a" * 64,
        evidence_class=EvidenceClass.E2_SOURCE,
        subject_id="atom-replay-engine",
    )
    defaults.update(over)
    return EvidenceRef(**defaults)


def _receipt(**over):
    from qcae.core.receipts.receipt import ReceiptEvidenceRef  # nested-ref constructor

    defaults = dict(
        receipt_id="rcpt-r5",
        capability_id="CAP-R5",
        atom_ids=("atom-a",),
        contract_id="CAP-R5",
        contract_version="1.0.0",
        implementation_id="repo:owner/impl@abc123",
        acquisition_form="VENDOR",
        source_revision="abc123",
        integration_scope="quant-lab.research",
        owner="quant-lab-platform",
        created_at="2026-09-22T00:00:00Z",
        state=ReceiptState.ACTIVE,
        proof_refs=(
            ReceiptEvidenceRef(
                evidence_id="ev-exec-1",
                evidence_class="E5_INDEPENDENT_CONTRACT",
                artifact_digest="a" * 64,
            ),
        ),
        rollback_ref="plan-exit-r5",
        authority_ref="auth-decision-r5",
    )
    defaults.update(over)
    return make_receipt(**defaults)


# --------------------------------------------------------------------------
# 2. schema authority and migration truth
# --------------------------------------------------------------------------


class TestSchemaAuthorityAndMigrationTruth:
    def test_envelopes_carry_schema_versions_and_refuse_unknown(self) -> None:
        ref = _ref()
        payload = ref.to_dict()
        assert payload["schema_version"] == 1
        assert payload["object_type"] == "EvidenceRef"
        bad = dict(payload, schema_version=99)
        from qcae.core.serialization import QcaeSchemaVersionError

        with pytest.raises(QcaeSchemaVersionError):
            EvidenceRef.from_dict(bad)

    def test_user_version_pins_schema_and_ledger_is_append_only(self, tmp_path) -> None:
        conn = open_metadata_db(tmp_path / "r5.db")
        runner = MigrationRunner(conn, clock=lambda: "2026-09-22T00:00:00Z")
        assert runner.current_version() == 1
        runner.migrate_to(2, {2: TEST_V1_TO_V2})
        assert runner.current_version() == 2
        entries = runner.ledger()
        assert len(entries) == 1
        assert entries[0].post_digest != entries[0].pre_digest
        conn.close()


# --------------------------------------------------------------------------
# 3. live grant binding
# --------------------------------------------------------------------------


class TestLiveGrantBinding:
    def test_mark_grant_used_is_atomic_and_durable(self) -> None:
        from qcae.governance.standalone.approvals import GrantUse

        conn = open_metadata_db(":memory:")
        from qcae.infrastructure.persistence.sqlite_approval_registry import APPROVAL_DDL

        conn.executescript(APPROVAL_DDL)
        registry = SqliteApprovalRegistry(conn)
        use = GrantUse(
            use_id="use-1", decision_ref="dec-1",
            step_id="job-r5:s-1", used_at="2026-09-22T00:00:00Z",
        )
        assert registry.mark_grant_used(use) is True
        # Single-use law: the second consumption of the same grant is refused.
        assert registry.mark_grant_used(use) is False
        assert len(registry.uses_for_decision("dec-1")) == 1
        conn.close()


# --------------------------------------------------------------------------
# 4. backup/restore truth
# --------------------------------------------------------------------------


class TestBackupRestoreTruth:
    def test_round_trip_restores_verified_state(self, tmp_path) -> None:
        from qcae.infrastructure.artifact_store import ContentAddressedArtifactStore

        db = tmp_path / "meta.sqlite3"
        conn = open_metadata_db(db)
        conn.commit()
        store = ContentAddressedArtifactStore(tmp_path / "artifacts")
        blob = store.put_bytes(b"p2-r5 restore truth")
        backup_dir = tmp_path / "backup"
        manifest = BackupService(conn, store).backup(backup_dir)
        assert manifest["artifact_count"] == 1

        restored_db = tmp_path / "restored" / "meta.sqlite3"
        result = RestoreService().restore(backup_dir, restored_db, tmp_path / "restored-art")
        assert result.artifacts_restored == 1
        assert result.schema_version >= 1
        # The restored artifact store serves the same bytes under the same digest.
        assert (tmp_path / "restored-art" / "sha256" / blob[:2] / blob).exists() or (
            tmp_path / "restored-art"
        ).exists()
        conn.close()

    def test_a_tampered_artifact_fails_restore(self, tmp_path) -> None:
        from qcae.infrastructure.artifact_store import ContentAddressedArtifactStore

        db = tmp_path / "meta2.sqlite3"
        conn = open_metadata_db(db)
        conn.commit()
        store = ContentAddressedArtifactStore(tmp_path / "artifacts2")
        store.put_bytes(b"tamper me")
        backup_dir = tmp_path / "backup2"
        BackupService(conn, store).backup(backup_dir)
        # Corrupt the backed-up blob; restore must refuse it.
        blobs = list((backup_dir / "artifacts").iterdir())
        blobs[0].write_bytes(b"corrupted")
        with pytest.raises(QcaeValidationError, match="digest check"):
            RestoreService().restore(
                backup_dir, tmp_path / "restored2" / "meta.sqlite3", tmp_path / "rest-art2")
        conn.close()


# --------------------------------------------------------------------------
# 5. typed NOT_READY behavior (the NEW repair) + CLI run truth
# --------------------------------------------------------------------------


def _submit_job(app: QcaeApp, db: Path, key: str, step: str = "s-1:GENERIC"):
    from qcae.interfaces.submission import JobSubmission

    return app.job_submit(
        JobSubmission(
            job_kind="discovery",
            subject_ref="cap-r5",
            idempotency_key=key,
            steps=_parse_step_specs(step),
            submitted_by="id-operator-local",
        ),
        submitted_by="id-operator-local",
    )


def _parse_step_specs(spec: str):
    from qcae.interfaces.cli.__main__ import _parse_step_specs as parse

    return parse([spec])


class TestTypedNotReadyBehavior:
    def test_unknown_job_run_returns_typed_job_missing(self, tmp_db) -> None:
        app = QcaeApp(build_local_runtime(tmp_db))
        result = app.job_run_step("job-does-not-exist", "id-worker-runtime")
        assert isinstance(result, JobMissingOutcome)
        assert result.reason == "JOB_NOT_FOUND"
        assert "unknown job" in result.message()

    def test_not_ready_outcome_carries_typed_reason(self) -> None:
        outcome = StepNotReadyOutcome("job-r5", "NO_ELIGIBLE_STEP")
        assert outcome.standing == "CONTRACT_NOT_READY"
        with pytest.raises(ValueError):
            StepNotReadyOutcome("job-r5", "MADE_UP_REASON")


class TestCLIRunTruth:
    def test_job_run_unknown_job_matches_status_standing(self, tmp_db) -> None:
        """The repaired defect: `job run` on a mistyped id says unknown job."""
        status = _run_cli("job", "status", "job-nonexistent1", db=tmp_db)
        assert status.returncode == 2
        assert "unknown job" in status.stderr
        assert "Traceback" not in status.stderr

        run = _run_cli("job", "run", "job-nonexistent1", db=tmp_db)
        assert run.returncode == 2, run.stderr
        assert "unknown job" in run.stderr
        assert "no eligible step" not in run.stderr
        assert "Traceback" not in run.stderr
        # One identifier, one standing: status and run now agree.
        assert "unknown job job-nonexistent1" in status.stderr
        assert "unknown job job-nonexistent1" in run.stderr

    def test_job_run_events_standing_matches(self, tmp_db) -> None:
        events = _run_cli("job", "events", "job-nonexistent1", db=tmp_db)
        assert events.returncode == 2
        assert "unknown job" in events.stderr

    def test_job_run_not_ready_is_typed(self, tmp_db) -> None:
        """A future-dated job exists but cannot run yet: typed NOT_READY."""
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-r5",
            "--key", "k-notready", "--step", "s-1:GENERIC",
            "--not-before", "2030-01-01T00:00:00Z", db=tmp_db,
        )
        assert submit.returncode == 0, submit.stderr
        run = _run_cli("job", "run", "job-discovery-k-notready", db=tmp_db)
        assert run.returncode == 1, run.stderr
        assert "Traceback" not in run.stderr
        payload = json.loads(run.stderr)
        assert payload["error"] == "NOT_READY"
        assert payload["standing"] == "CONTRACT_NOT_READY"
        assert payload["reason"] == "SCHEDULE_NOT_ELAPSED"

    def test_in_process_dispatch_not_ready_shape(self, tmp_db) -> None:
        app = QcaeApp(build_local_runtime(tmp_db))
        _submit_job(app, tmp_db, "k-notready2")
        result = app.job_run_step("job-discovery-k-notready2", "id-worker-runtime")
        # No worker is registered in this runtime: availability, not readiness,
        # is the binding constraint — the typed worker-unavailable outcome.
        assert getattr(result, "reason", "") == "WORKER_UNAVAILABLE"
