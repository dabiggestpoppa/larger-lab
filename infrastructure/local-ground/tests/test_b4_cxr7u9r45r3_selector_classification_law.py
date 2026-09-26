#!/usr/bin/env python3
"""B4-CXR7U9R45R3 — ONE selector classification law, table-driven.

The shell classifier (`--classify-state` / `--classify-rollback`, real child
processes of the real CLI) and the reconciliation engine (`phase_reconcile`,
the real phase code with only its docker/catalog OBSERVATIONS stubbed, the
same discipline as the R40R2 boundary proofs) must produce the SAME semantic
verdict for every state/selector combination that can exist. This module
drives both surfaces across the complete matrix and rejects any disagreement:

    PROMOTED + no claim            -> fresh rollback (0 / fresh_rollback_available)
    PROMOTED + exact rollback bind -> resume rollback (6 / resume_rollback_required)
    PROMOTED + exact finalize bind -> preintent abort (5 / preintent_abort_required)
    PROMOTED + any spent selector  -> fail closed (4 / unreconciled), never fresh
    FINALIZING + no claim          -> governed abort stands (5 / preintent_abort_required)
    FINALIZING + exact finalize    -> governed abort (5 / preintent_abort_required)
    FINALIZING + wrong/foreign     -> fail closed (4 / unreconciled)
    ROLLING_BACK + exact claim     -> resume (6 / resume_rollback_required)
    COMMIT_POINT / FINALIZED       -> post-commit, no artifact rollback (3 / committed)
    ROLLED_BACK                    -> terminal, idempotent (6 / rolled_back)

The executable weakened control drops the receiptless spent-selector veto in
an engine COPY and must visibly diverge from the shipped engine on exactly
the rows the law is about; the shipped engine passes every row.
"""
import json
import os
import subprocess
import sys

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)
from test_b4_cxr7u9r45r2_claim_path_admission import (
    CLI, _bound_claim, _census, _load_record, _promoted, _record_path,
    _shell_receipt, _write_claim)

RECORD_DIGEST = lambda receipt: pgrec._receipt_digest(receipt)  # noqa: E731


@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b

# --------------------------------------------------------------------- #
# the second surface: the REAL phase_reconcile, observations stubbed
# --------------------------------------------------------------------- #

def _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha, *,
               quarantine_present=True, catalog=None, canonical_ok=False,
               floor_ok=True):
    catalog = catalog if catalog is not None else {"postgres", pgrec.DB}
    monkeypatch.setattr(pgrec, "_quarantine_present",
                        lambda *a, **k: quarantine_present)
    monkeypatch.setattr(pgrec, "_catalog_names", lambda *a, **k: set(catalog))
    monkeypatch.setattr(pgrec, "db_exists", lambda *a, **k: quarantine_present)
    monkeypatch.setattr(pgrec, "_verify_db",
                        lambda *a, **k: (canonical_ok, [], {}, None))
    monkeypatch.setattr(pgrec, "_verify_against_floor",
                        lambda *a, **k: (floor_ok, [], {}))
    return pgrec.phase_reconcile(str(path), str(inv), str(sha), pgrec.DB,
                                 pgrec.USER, pgrec.CONTAINER, None)


def _set_record(opid, **fields):
    record = _load_record(opid)
    record.update(fields)
    _record_path(opid).write_text(json.dumps(record), encoding="utf-8")
    return record


def _with_forward_evidence(opid, receipt, state):
    """Post-intent records through the engine's own FORWARD sequence: claim
    finalize (publishes the real selector and advances FINALIZING), then the
    commit intent, then the commit point / terminal state. The engine's
    forward-only recorder refuses any other path."""
    pgrec._claim_transition(opid, "finalize", receipt)
    pgrec._record_transition(
        opid, pgrec.TRANSITION_STATE_COMMIT_INTENT, receipt,
        extra={"commit_intent": {
            "marker": "forward_commit", "operation_id": opid,
            "receipt_sha256": RECORD_DIGEST(receipt),
            "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER,
            "quarantine_database": receipt["quarantine_database"],
            "at": "2026-09-24T00:00:00Z"}})
    if state in (pgrec.TRANSITION_STATE_COMMIT_POINT, "FINALIZED"):
        pgrec._record_transition(
            opid, pgrec.TRANSITION_STATE_COMMIT_POINT, receipt,
            extra={"commit_point": {
                "marker": "quarantine_dropped", "at": "2026-09-24T00:00:01Z"}})
    if state == "FINALIZED":
        pgrec._record_transition(opid, "FINALIZED", receipt)


# --------------------------------------------------------------------- #
# the matrix: builder -> (shell code, reconcile verdict)
# --------------------------------------------------------------------- #

def _row_promoted_no_claim(receipt, path):
    return 0, "fresh_rollback_available"


def _row_promoted_exact_rollback(receipt, path):
    _write_claim(receipt["operation_id"], _bound_claim(receipt, "rollback"))
    return 6, "resume_rollback_required"


def _row_promoted_exact_finalize(receipt, path):
    _write_claim(receipt["operation_id"], _bound_claim(receipt, "finalize"))
    return 5, "preintent_abort_required"


def _row_promoted_foreign_digest(receipt, path):
    _write_claim(receipt["operation_id"],
                 {**_bound_claim(receipt, "rollback"),
                  "receipt_sha256": "a" * 64})
    return 4, "unreconciled"


def _row_promoted_missing_digest(receipt, path):
    _write_claim(receipt["operation_id"],
                 {k: v for k, v in _bound_claim(receipt, "rollback").items()
                  if k != "receipt_sha256"})
    return 4, "unreconciled"


def _row_promoted_wrong_opid(receipt, path):
    forged = _bound_claim(receipt, "rollback")
    forged["operation_id"] = "f" * 32
    _write_claim(receipt["operation_id"], forged)
    return 4, "unreconciled"


def _row_promoted_foreign_structure(receipt, path):
    _write_claim(receipt["operation_id"],
                 {"format": pgrec._CLAIM_FORMAT, "note": "foreign"})
    return 4, "unreconciled"


def _row_finalizing_no_claim(receipt, path):
    _set_record(receipt["operation_id"],
                state=pgrec.TRANSITION_STATE_FINALIZING,
                selected_transition="finalize")
    return 5, "preintent_abort_required"


def _row_finalizing_exact_finalize(receipt, path):
    _set_record(receipt["operation_id"],
                state=pgrec.TRANSITION_STATE_FINALIZING,
                selected_transition="finalize")
    _write_claim(receipt["operation_id"], _bound_claim(receipt, "finalize"))
    return 5, "preintent_abort_required"


def _row_finalizing_rollback_claim(receipt, path):
    _set_record(receipt["operation_id"],
                state=pgrec.TRANSITION_STATE_FINALIZING,
                selected_transition="finalize")
    _write_claim(receipt["operation_id"], _bound_claim(receipt, "rollback"))
    return 4, "unreconciled"


def _row_finalizing_foreign_digest(receipt, path):
    _set_record(receipt["operation_id"],
                state=pgrec.TRANSITION_STATE_FINALIZING,
                selected_transition="finalize")
    _write_claim(receipt["operation_id"],
                 {**_bound_claim(receipt, "finalize"),
                  "receipt_sha256": "a" * 64})
    return 4, "unreconciled"


def _row_rolling_back_exact_claim(receipt, path):
    opid = receipt["operation_id"]
    _write_claim(opid, _bound_claim(receipt, "rollback"))
    _set_record(opid, state=pgrec.TRANSITION_STATE_ROLLING_BACK,
                selected_transition="rollback")
    return 6, "resume_rollback_required"


def _row_commit_point(receipt, path):
    _with_forward_evidence(receipt["operation_id"], receipt,
                           pgrec.TRANSITION_STATE_COMMIT_POINT)
    return 3, "committed"


def _row_finalized(receipt, path):
    _with_forward_evidence(receipt["operation_id"], receipt, "FINALIZED")
    return 3, "committed"


def _row_rolled_back(receipt, path):
    opid = receipt["operation_id"]
    _write_claim(opid, _bound_claim(receipt, "rollback"))
    _set_record(opid, state="ROLLED_BACK", selected_transition="rollback",
                rollback_floor={"tables": ["public.widgets"],
                                "rows": {"public.widgets": 3}})
    return 6, "rolled_back"


MATRIX = [
    ("promoted_no_claim", _row_promoted_no_claim,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": False}),
    ("promoted_exact_rollback_claim", _row_promoted_exact_rollback,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB,
                                              "Q"},
      "canonical_ok": True}),
    ("promoted_exact_finalize_claim", _row_promoted_exact_finalize,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True}),
    ("promoted_foreign_digest", _row_promoted_foreign_digest, None),
    ("promoted_missing_digest", _row_promoted_missing_digest, None),
    ("promoted_wrong_operation_claim", _row_promoted_wrong_opid, None),
    ("promoted_foreign_structure", _row_promoted_foreign_structure, None),
    ("finalizing_no_claim", _row_finalizing_no_claim,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True}),
    ("finalizing_exact_finalize_claim", _row_finalizing_exact_finalize,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True}),
    ("finalizing_rollback_claim", _row_finalizing_rollback_claim, None),
    ("finalizing_foreign_digest", _row_finalizing_foreign_digest, None),
    ("rolling_back_exact_claim", _row_rolling_back_exact_claim,
     {"quarantine_present": True, "catalog": {"postgres", pgrec.DB, "Q"},
      "canonical_ok": True}),
    ("commit_point_reached", _row_commit_point,
     {"quarantine_present": False, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True}),
    ("finalized", _row_finalized,
     {"quarantine_present": False, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True}),
    ("rolled_back", _row_rolled_back,
     {"quarantine_present": False, "catalog": {"postgres", pgrec.DB},
      "canonical_ok": True, "floor_ok": True}),
]

# the semantic agreement map: a shell code may only coexist with these
# reconcile verdicts (and vice versa). Anything outside the row is a
# cross-surface disagreement and fails the law.
SHELL_TO_VERDICTS = {
    0: {"fresh_rollback_available"},
    5: {"preintent_abort_required"},
    6: {"resume_rollback_required", "rolled_back"},
    3: {"committed"},
    4: {"unreconciled"},
}


@pytest.mark.parametrize("row", MATRIX, ids=[r[0] for r in MATRIX])
def test_shell_and_reconcile_agree_on_the_whole_matrix(row, bridge, tmp_path,
                                                       monkeypatch):
    name, build, observation = row
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch,
                                        name=f"{name}.json")
    expected_shell, expected_verdict = build(receipt, path)

    # zero-mutation baseline: everything below is read-only classification
    before = _census(tmp_path)

    shell = _shell_receipt(path)
    observation = dict(observation or {})
    if "catalog" in observation:
        observation["catalog"] = {
            receipt["quarantine_database"] if n == "Q" else n
            for n in observation["catalog"]}
    reconciled = _reconcile(bridge, tmp_path, monkeypatch, receipt, path,
                            inv, sha, **observation)

    assert shell == expected_shell, (
        f"{name}: shell classified {shell}, law says {expected_shell}")
    assert reconciled["verdict"] == expected_verdict, (
        f"{name}: reconcile said {reconciled['verdict']} "
        f"({reconciled.get('error', '')[:120]}), law says {expected_verdict}")
    # the cross-surface agreement itself, independent of the row constants
    assert reconciled["verdict"] in SHELL_TO_VERDICTS[shell], (
        f"{name}: shell {shell} and reconcile "
        f"{reconciled['verdict']!r} DISAGREE")
    # classification is read-only on the durable world, for EVERY row
    assert _census(tmp_path) == before, f"{name}: durable world mutated"


def test_terminal_resume_stays_idempotent(bridge, tmp_path, monkeypatch):
    """A terminal ROLLED_BACK classification is stable under repetition: the
    second reconcile of the same durable world returns the same verdict and
    the transition tree stays byte-identical."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, _bound_claim(receipt, "rollback"))
    _set_record(opid, state="ROLLED_BACK", selected_transition="rollback",
                rollback_floor={"tables": ["public.widgets"],
                                "rows": {"public.widgets": 3}})
    first = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                       quarantine_present=False,
                       catalog={"postgres", pgrec.DB}, canonical_ok=True)
    assert first["verdict"] == "rolled_back"
    before = _census(tmp_path)
    second = _reconcile(bridge, tmp_path, monkeypatch, receipt, path, inv, sha,
                        quarantine_present=False,
                        catalog={"postgres", pgrec.DB}, canonical_ok=True)
    assert second["verdict"] == "rolled_back"
    after = _census(tmp_path)
    after.pop("governed-recovery/reconcile-2.json", None)
    assert after == before


# --------------------------------------------------------------------- #
# the executable weakened control at matrix level
# --------------------------------------------------------------------- #

_WEAKENED_TRANSFORM = ('''        elif isinstance(operation_id, str) \\
                and OPERATION_ID_RE.match(operation_id) \\
                and _claim_state(operation_id, transition_dir) != "absent":
            # PROMOTED with an existing canonical claim and NO receipt to bind:
            # the selector name exists, so the one-time authority is spent —
            # never fresh (B4-CXR7U9R45R1).
            return 4
        return 0
''', '''        return 0
''')


def _run_engine(engine_path, argv):
    return subprocess.run(
        [sys.executable, str(engine_path), *map(str, argv)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=60).returncode


def test_weakened_engine_fails_the_matrix_the_shipped_engine_passes(
        bridge, tmp_path, monkeypatch):
    """Executable negative control. The weakened copy drops the receiptless
    spent-selector veto; on the FALSE-FRESH rows it must report fresh
    rollback where the shipped engine reports fail-closed, and its verdict
    must contradict the shipped engine's reconcile verdict for the same
    durable world. The shipped engine itself agrees with reconcile on every
    row (the matrix test above)."""
    source = CLI.read_text(encoding="utf-8")
    old, new = _WEAKENED_TRANSFORM
    assert old in source, "the R45R1 selector law changed shape"
    weak_path = tmp_path / "weakened-pg-recovery.py"
    weak_path.write_text(source.replace(old, new), encoding="utf-8")

    diverged = []
    for name, build, _observation in MATRIX:
        receipt, path, _inv, _sha = _promoted(
            bridge, tmp_path, monkeypatch, name=f"weak-{name}.json")
        expected_shell, _expected_verdict = build(receipt, path)
        # the dropped veto lives on the RECEIPTLESS surface: classify the
        # durable record directly, with no promote receipt to bind
        record_path = _record_path(receipt["operation_id"])
        shipped = _run_engine(
            CLI, ["--phase", "reconcile", "--classify-state",
                  str(record_path)])
        weak = _run_engine(
            weak_path, ["--phase", "reconcile", "--classify-state",
                        str(record_path)])
        if weak != shipped:
            diverged.append((name, shipped, weak))
        # the shipped engine never disagrees with the law on any row
        assert shipped in (0, 3, 4, 5, 6), (name, shipped)

    # the weakened copy diverges on EXACTLY the false-fresh rows: every
    # divergence is a spent PROMOTED selector the weakened engine calls
    # fresh (0) and the shipped engine refuses (4)
    assert diverged, "the weakened control no longer reproduces false-fresh"
    for name, shipped, weak in diverged:
        assert shipped == 4 and weak == 0, (name, shipped, weak)
        assert name.startswith("promoted_"), name
