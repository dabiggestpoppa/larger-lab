#!/usr/bin/env python3
"""B4-CXR7U9R40-R2 — the cross-store commit boundary is crash-coherent.

R39's finalize sequence had fallible steps AFTER PostgreSQL's irreversible
point (the quarantine drop) but BEFORE restore.sh set its volatile
PG_FINALIZED/COMMITTED flags. A failure in that window made the EXIT trap
treat the transaction as pre-commit, restore the artifact snapshot, and
attempt a PostgreSQL rollback that can no longer happen — the exact
cross-store divergence (new PostgreSQL + old artifacts) R39 exists to prevent.

The law now: the commit point is DURABLY recorded in the operation record at
the moment the quarantine drops; the shell's rollback authority is derived
from that durable state, never from volatile flags alone; and a restart
reconciles by OBSERVING durable truth (transition state, quarantine presence,
canonical content) without guessing. The shell law itself is proven here by
executing restore.sh's own durable_precommit logic (extracted and run as
bash, the production code path, byte for byte) against every durable state;
the container-backed fault injections at every boundary live in
test_b4_cxr7u9r40r2_commit_boundary_container.py.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)

SCRIPTS = Path(pgrec.__file__).resolve().parent
# the SAME bash the other shell-driving suites use: Python's bare "bash"
# resolution can find a WSL stub on Windows, which is not the interpreter
# restore.sh runs under.
BASH = shutil.which("bash") or "bash"


# --------------------------------------------------------------------- #
# the shell's durable rollback authority, executed as production bash
# --------------------------------------------------------------------- #

def _extract_durable_precommit_bash():
    """Pull the REAL durable_precommit implementation out of restore.sh and
    run it — no reimplementation, so the proof covers the production code."""
    text = (SCRIPTS / "restore.sh").read_text(encoding="utf-8")
    m = re.search(r"(durable_precommit\(\) \{.*?\n\})\n", text, re.S)
    assert m, "durable_precommit not found in restore.sh"
    return m.group(1)


@pytest.fixture
def shell_law(tmp_path):
    """Run restore.sh's real durable_precommit against a temp receipt/record
    layout. Returns a callable: (promote_receipt_bytes_or_None,
    record_state_or_None) -> exit code."""
    functions = _extract_durable_precommit_bash()

    python_exe = sys.executable.replace("\\", "/")

    def run(promote_receipt, record_state):
        receipts = tmp_path / "shell" / "receipts"
        transitions = tmp_path / "shell" / "recovery" / "transitions"
        receipts.mkdir(parents=True, exist_ok=True)
        transitions.mkdir(parents=True, exist_ok=True)
        promote = None
        if promote_receipt is not None:
            promote = receipts / "promote-receipt.json"
            promote.write_text(promote_receipt, encoding="utf-8")
        if record_state is not None:
            opid = "0123456789abcdef0123456789abcdef"
            authority = {
                "format": pgrec.RECEIPT_FORMAT,
                "operation_phase": "promote",
                "exit_status": 0,
                "promoted": True,
                "operation_id": opid,
                "database": pgrec.DB,
                "user": pgrec.USER,
                "container": pgrec.CONTAINER,
                "source_commit": "a" * 40,
                "source_tree": "b" * 40,
                "run_id": "0123456789abcdef",
                "stamp": "0123456789ab",
                "quarantine_database": pgrec.QUARANTINE_PREFIX + "0123456789ab",
                "staging_database": pgrec.STAGING_PREFIX + "0123456789ab",
                "source_archive_sha256": "c" * 64,
                "inventory_sha256": "d" * 64,
            }
            record = {
                "format": pgrec.TRANSITION_FORMAT,
                "state": record_state,
                **{key: authority[key] for key in (
                    "operation_id", "database", "user", "container",
                    "source_commit", "source_tree", "run_id", "stamp",
                    "quarantine_database", "staging_database",
                    "source_archive_sha256", "inventory_sha256")},
                "receipt_sha256": pgrec._receipt_digest(authority),
            }
            if record_state == pgrec.TRANSITION_STATE_FINALIZING:
                record["selected_transition"] = "finalize"
            if record_state == pgrec.TRANSITION_STATE_ROLLING_BACK:
                record["selected_transition"] = "rollback"
                claim_path = transitions / f"{opid}.claim"
                claim_path.write_text(json.dumps({
                    "format": pgrec._CLAIM_FORMAT,
                    "operation_id": opid,
                    "transition": "rollback",
                    "receipt_sha256": record["receipt_sha256"],
                    "claimed_at": "2026-09-24T00:00:00Z",
                }), encoding="utf-8")
                # The engine publishes claims 0600 (B4-CXR7U9R45R2 admission
                # refuses widened claims on POSIX); mirror that here so the
                # hand-written fixture is admissible on Linux CI too.
                os.chmod(claim_path, 0o600)
            if record_state in (pgrec.TRANSITION_STATE_COMMIT_INTENT,
                                pgrec.TRANSITION_STATE_COMMIT_POINT,
                                "FINALIZED"):
                record["selected_transition"] = "finalize"
                record["commit_intent"] = {
                    "marker": "forward_commit",
                    "operation_id": opid,
                    "receipt_sha256": record["receipt_sha256"],
                    "database": pgrec.DB,
                    "user": pgrec.USER,
                    "container": pgrec.CONTAINER,
                    "quarantine_database": authority["quarantine_database"],
                    "at": "2026-09-24T00:00:00Z",
                }
            if record_state in (pgrec.TRANSITION_STATE_COMMIT_POINT,
                                "FINALIZED"):
                record["commit_point"] = {
                    "marker": "quarantine_dropped",
                    "at": "2026-09-24T00:00:01Z",
                }
            promote.write_text(json.dumps(authority), encoding="utf-8")
            (transitions / f"{opid}.json").write_text(
                json.dumps(record), encoding="utf-8")
        script = (
            "set -uo pipefail\n"
            f"OCE_PYTHON=\"{python_exe}\"\n"
            f"BIN='{SCRIPTS.as_posix()}'\n"
            f"PROMOTE_RECEIPT='{promote}'\n"
            f"VAR_DIR='{tmp_path / 'shell'}'\n"
            f"export OCE_BACKUP_ROOTS='{tmp_path / 'shell'}'\n"
            + functions +
            "\ndurable_precommit\n"
        )
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True,
                           timeout=60)
        return r.returncode, r.stderr

    return run


def test_no_promotion_means_precommit(shell_law):
    """No promote receipt: nothing was promoted, rollback of both stores is
    legal (and then a no-op)."""
    rc, _err = shell_law(None, None)
    assert rc == 0


@pytest.mark.parametrize("state,expect_precommit", [
    ("CREATED", True),
    ("STAGED", True),
    ("PROMOTED", True),
    ("FINALIZING", True),
    ("ROLLING_BACK", True),
    (pgrec.TRANSITION_STATE_COMMIT_INTENT, False),
    ("COMMIT_POINT_REACHED", False),
    ("FINALIZED", False),
])
def test_durable_state_controls_rollback_legality(shell_law, state,
                                                  expect_precommit):
    rc, err = shell_law(json.dumps({"operation_id": "0123456789abcdef0123456789abcdef"}),
                        state)
    assert rc == (0 if expect_precommit else 1), (state, rc, err)
    if not expect_precommit:
        assert "irreversible commit point" in err, err


def test_unknowable_durable_state_fails_closed(shell_law):
    """A state the law does not recognize is NOT treated as pre-commit."""
    rc, _err = shell_law(json.dumps({"operation_id": "0123456789abcdef0123456789abcdef"}),
                         "SOMETHING_ELSE")
    assert rc == 1


def test_existing_promote_receipt_with_missing_record_fails_closed(shell_law):
    """Once a promote receipt exists, absence of its record is unknowable—not
    evidence that no operation happened."""
    rc, err = shell_law(
        json.dumps({"operation_id": "0123456789abcdef0123456789abcdef"}), None)
    assert rc == 1
    assert "UNKNOWABLE" in err


def test_unreadable_existing_promote_receipt_fails_closed(shell_law):
    rc, err = shell_law("{not json", None)
    assert rc == 1
    assert "UNKNOWABLE" in err


# --------------------------------------------------------------------- #
# the engine records the commit point durably, and never relabels it FAILED
# --------------------------------------------------------------------- #

@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _promoted(bridge, tmp_path, monkeypatch):
    from test_b4_cxr7u9r35_recovery_authority import _write_inputs
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive, "p.json")
    return receipt, path, inv, sha


def test_finalize_records_the_commit_point_before_any_further_fallible_step(
        bridge, tmp_path, monkeypatch):
    """The durable COMMIT_POINT_REACHED is written the moment the quarantine
    drops — before the removal verification, before the record update, before
    the receipt commit — so any later crash is attributable as committed."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    # make the removal VERIFICATION fail (boundary 4): the drop already happened
    monkeypatch.setattr(pgrec, "db_exists", lambda *a, **k: True)
    out = pgrec.phase_finalize(str(path), str(inv), str(sha), pgrec.DB,
                               pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1, out
    record = pgrec._load_transition_record(opid)
    # DURABLE truth: committed, no matter what the volatile receipt says
    assert record["state"] == pgrec.TRANSITION_STATE_COMMIT_POINT, record
    assert record["commit_point"]["marker"] == "quarantine_dropped"
    # and the receipt itself names the commit point for the shell
    assert out.get("commit_point_recorded") is True
    assert out.get("postgres_committed") is True


def test_post_commit_failure_is_never_relabelled_failed(
        bridge, tmp_path, monkeypatch):
    """A post-quarantine-drop failure keeps the durable COMMIT_POINT state:
    'FAILED' would license a rollback that can no longer happen and must not."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    monkeypatch.setattr(pgrec, "db_exists", lambda *a, **k: True)
    out = pgrec.phase_finalize(str(path), str(inv), str(sha), pgrec.DB,
                               pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1
    assert pgrec._load_transition_record(opid)["state"] \
        != "FAILED"


def test_failure_before_the_drop_still_rolls_back(
        bridge, tmp_path, monkeypatch):
    """Boundary 1 (final verification fails pre-drop): the quarantine is the
    rollback source and the original IS restored — the pre-commit law is
    unchanged."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    monkeypatch.setattr(pgrec, "_verify_db",
                        lambda *a, **k: (False, ["verification broke"], {}, None))
    out = pgrec.phase_finalize(str(path), str(inv), str(sha), pgrec.DB,
                               pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1, out
    assert out.get("rollback_succeeded") is True, out
    record = pgrec._load_transition_record(opid)
    assert record["state"] == "ROLLED_BACK", record


# --------------------------------------------------------------------- #
# restart reconciliation observes durable truth without guessing
# --------------------------------------------------------------------- #

def _reconcile(bridge, tmp_path, monkeypatch, promote, path, inv, sha,
               quarantine_present, canonical_ok):
    monkeypatch.setattr(pgrec, "db_exists", lambda *a, **k: quarantine_present)
    monkeypatch.setattr(pgrec, "_verify_db",
                        lambda *a, **k: (canonical_ok, [], {}, None))
    return pgrec.phase_reconcile(str(path), str(inv), str(sha), pgrec.DB,
                                 pgrec.USER, pgrec.CONTAINER, None)


def test_reconcile_reads_the_durable_commit_point(
        bridge, tmp_path, monkeypatch):
    """Boundary 7/9: a crash after the drop, before PG_FINALIZED. Restart
    reconcile observes: durable COMMIT_POINT_REACHED + quarantine gone +
    canonical content matches the backup -> committed, without mutating."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    pgrec._claim_transition(opid, "finalize", receipt)
    pgrec._record_transition(
        opid, pgrec.TRANSITION_STATE_COMMIT_INTENT, receipt,
        extra={"commit_intent": {
            "marker": "forward_commit", "operation_id": opid,
            "receipt_sha256": pgrec._receipt_digest(receipt),
            "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER,
            "quarantine_database": receipt["quarantine_database"],
            "at": "2026-09-24T00:00:00Z"}})
    pgrec._record_transition(opid, pgrec.TRANSITION_STATE_COMMIT_POINT, receipt,
                             extra={"commit_point": {
                                 "marker": "quarantine_dropped",
                                 "at": "2026-09-24T00:00:01Z"}})
    bridge.reset()
    out = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                     quarantine_present=False, canonical_ok=True)
    assert out["exit_status"] == 0, out
    assert out["verdict"] == "committed", out
    assert out["committed"] is True
    # reconciliation consumed nothing: the claim and record are untouched
    assert pgrec._load_claim(opid)["transition"] == "finalize"
    assert pgrec._load_transition_record(opid)["state"] \
        == pgrec.TRANSITION_STATE_COMMIT_POINT


def test_reconcile_rollback_after_rename_requires_explicit_resume(bridge, tmp_path, monkeypatch):
    """A rolled-back catalog with a valid rollback claim is resumable, not fresh."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    pgrec._claim_transition(receipt["operation_id"], "rollback", receipt)
    out = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                     quarantine_present=False, canonical_ok=True)
    assert out["exit_status"] == 0, out
    assert out["verdict"] == "resume_rollback_required", out


def test_reconcile_with_quarantine_intact_reports_rollback_available(
        bridge, tmp_path, monkeypatch):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    out = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                     quarantine_present=True, canonical_ok=False)
    assert out["exit_status"] == 0, out
    assert out["verdict"] == "fresh_rollback_available", out


def test_reconcile_consumes_no_authority(bridge, tmp_path, monkeypatch):
    """Reconciliation is read-only: a later legitimate transition still sees
    PROMOTED authority exactly as it was."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    out = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                     quarantine_present=True, canonical_ok=False)
    assert out["verdict"] == "fresh_rollback_available"
    assert pgrec._load_transition_record(opid)["state"] \
        == pgrec.TRANSITION_STATE_PROMOTED
    assert pgrec._load_claim(opid) is None
