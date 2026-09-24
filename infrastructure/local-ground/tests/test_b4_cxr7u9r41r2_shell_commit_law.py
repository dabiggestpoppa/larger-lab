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
4. the drop-before-record crash window: FINALIZING **with** a durable
   commit_point marker classifies 3 — the state advance never landed but the
   quarantine drop happened, so artifact-only rollback is forbidden;
5. FINALIZING without a marker classifies 0;
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
POSTCOMMIT_STATES = ["COMMIT_POINT_REACHED", "FINALIZED"]
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
        assert _classify({"state": state}, tmp_path) == 3, state


def test_terminal_states_classify_zero(tmp_path):
    """ROLLED_BACK/FAILED are not rollback targets; the shell must treat them
    as nothing left to restore rather than as an error."""
    for state in TERMINAL_STATES:
        assert _classify({"state": state}, tmp_path) == 0, state


def test_crash_window_finalizing_with_commit_point_marker_is_postcommit(tmp_path):
    """The drop-before-record window: the quarantine drop happened but the
    state advance to COMMIT_POINT_REACHED never landed. The durable marker
    makes the truth classifiable — post-commit, rollback FORBIDDEN."""
    rc = _classify({"state": "FINALIZING",
                    "commit_point": {"marker": "quarantine_dropped",
                                     "at": "2026-09-23T00:00:00Z"}}, tmp_path)
    assert rc == 3, rc


def test_finalizing_without_marker_is_precommit(tmp_path):
    assert _classify({"state": "FINALIZING"}, tmp_path) == 0


def test_unknowable_record_fails_closed(tmp_path):
    rec = tmp_path / "broken.json"
    rec.write_text("{not json", encoding="utf-8")
    r = subprocess.run([sys.executable, str(CLI), "--phase", "reconcile",
                        "--classify-state", str(rec)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 4, r.returncode
    assert _classify({"state": "SOME_FUTURE_STATE"}, tmp_path) == 4
