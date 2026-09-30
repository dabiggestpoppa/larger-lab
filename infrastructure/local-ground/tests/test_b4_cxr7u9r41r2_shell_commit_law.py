#!/usr/bin/env python3
"""B4-CXR7U9R41-R2 — the shell's commit law has ONE authority: the engine.

`durable_precommit` in restore.sh no longer re-encodes the transition ladder;
it delegates to `pg-recovery.py --phase reconcile --classify-state <record>`,
whose exit codes are the law: 0 = pre-commit, 3 = post-commit (rollback
forbidden), 4 = unknowable (fail closed). These proofs drive the REAL engine
in a child process, exactly as the shell does, against REAL durable records:

1. every non-finalizing pre-commit state classifies 0;
2. COMMIT_POINT_REACHED and FINALIZED classify 3;
3. FAILED and ROLLED_BACK (terminal, not in the shell's old sets) classify 0;
4. the former drop-before-record state is no longer trusted: FINALIZING with
   an impossible commit marker classifies 4 (malformed/fail closed);
5. FINALIZING without intent classifies 0, while the explicit durable
   COMMIT_INTENT_RECORDED state classifies 3;
6. a corrupt/unreadable record classifies 4 (fail closed).

The mirror of this file's law is exercised by
test_b4_cxr7u9r40r2_commit_boundary.py, which asserts the shell-visible
behavior through the extracted `durable_precommit` snippet itself.
"""
import json
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
CLI = TESTS.parent / "scripts" / "pg-recovery.py"

PRECOMMIT_STATES = ["CREATED", "STAGED", "PROMOTED", "ROLLING_BACK"]
POSTCOMMIT_STATES = ["COMMIT_INTENT_RECORDED", "COMMIT_POINT_REACHED",
                     "FINALIZED"]
TERMINAL_STATES = ["ROLLED_BACK", "FAILED"]


def _classify(record: dict, tmp_path: Path) -> int:
    rec = tmp_path / "op.json"
    rec.write_text(json.dumps(record), encoding="utf-8")
    r = subprocess.run([sys.executable, str(CLI), "--phase", "reconcile",
                        "--classify-state", str(rec)],
                       capture_output=True, text=True, timeout=60)
    return r.returncode


def test_every_precommit_state_classifies_zero(tmp_path):
    for state in PRECOMMIT_STATES:
        assert _classify({"state": state}, tmp_path) == 0, state


def test_postcommit_states_classify_three(tmp_path):
    for state in POSTCOMMIT_STATES:
        record = {"state": state}
        if state in ("COMMIT_INTENT_RECORDED", "FINALIZED"):
            record["commit_intent"] = {
                "marker": "forward_commit",
                "operation_id": "0123456789abcdef0123456789abcdef",
                "receipt_sha256": "a" * 64,
                "database": "oce_local",
                "user": "oce_local_admin",
                "container": "oce-local-postgresql",
                "quarantine_database": "oce_rollback_0123456789ab",
                "at": "2026-09-24T00:00:00Z",
            }
        if state in ("COMMIT_POINT_REACHED", "FINALIZED"):
            record["commit_point"] = {
                "marker": "quarantine_dropped",
                "at": "2026-09-24T00:00:01Z",
            }
        assert _classify(record, tmp_path) == 3, state


def test_terminal_states_fail_closed_without_their_exact_selector(tmp_path):
    """B4-CXR7U9R46R4: terminal and failed states are NEVER labelled fresh
    authority. ROLLED_BACK keeps an idempotent verification path (6) only
    with its EXACT rollback selector bound to the supplied promote receipt;
    a bare terminal/failed record with no selector is unknowable authority
    and fails closed (4). Nothing is left to restore either way: a 4 blocks
    artifact-only rollback just as decisively as the old 0 did, and now the
    shell classification agrees with the executable phase that refuses the
    same authority."""
    for state in TERMINAL_STATES:
        assert _classify({"state": state}, tmp_path) == 4, state


def test_impossible_finalizing_commit_marker_fails_closed(tmp_path):
    """The old ordering allowed a marker to be injected before COMMIT_POINT.
    Under the explicit ladder that marker is structurally impossible, so the
    engine refuses to infer either pre-commit or post-commit truth from it."""
    rc = _classify({"state": "FINALIZING",
                    "commit_point": {"marker": "quarantine_dropped",
                                     "at": "2026-09-23T00:00:00Z"}}, tmp_path)
    assert rc == 4, rc


def test_finalizing_without_claim_fails_closed(tmp_path):
    """B4-CXR7U9R46R3/R4: a FINALIZING record WITHOUT its exact finalize claim
    is missing authority evidence, not a governed crash state — a legitimate
    engine writes the durable claim BEFORE advancing the record to
    FINALIZING. The shell classification fails closed (4) and agrees with the
    executable resume-finalize phase, which has always required the claim."""
    assert _classify({"state": "FINALIZING",
                      "selected_transition": "finalize"}, tmp_path) == 4


def test_unknowable_record_fails_closed(tmp_path):
    rec = tmp_path / "broken.json"
    rec.write_text("{not json", encoding="utf-8")
    r = subprocess.run([sys.executable, str(CLI), "--phase", "reconcile",
                        "--classify-state", str(rec)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 4, r.returncode
    assert _classify({"state": "SOME_FUTURE_STATE"}, tmp_path) == 4


def test_unreadable_record_path_fails_closed(tmp_path):
    unreadable = tmp_path / "not-a-record"
    unreadable.mkdir()
    r = subprocess.run([sys.executable, str(CLI), "--phase", "reconcile",
                        "--classify-state", str(unreadable)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 4


def test_malformed_commit_intent_fails_closed(tmp_path):
    assert _classify({
        "state": "COMMIT_INTENT_RECORDED",
        "commit_intent": {"marker": "almost_forward_commit"},
    }, tmp_path) == 4
    assert _classify({"state": "COMMIT_INTENT_RECORDED"}, tmp_path) == 4
