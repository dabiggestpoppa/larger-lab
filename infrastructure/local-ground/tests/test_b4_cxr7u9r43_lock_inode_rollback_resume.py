#!/usr/bin/env python3
"""B4-CXR7U9R43 — stable lock inode and governed rollback-resume proofs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import recovery_cli
from test_b4_cxr7u9r41r2_crash_coherence import (
    BRIDGE_SOURCE,
    _clear,
    _dbs,
    _env,
    _kill_at_signal,
    _prepare,
    _record,
)

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "scripts"
CLI = SCRIPTS / "pg-recovery.py"


_R43_PATCH = r'''

_R43_BASE_INSTALL = install
_R43_BASE_CATALOG = _catalog
_R43_BASE_DROP = _drop
_R43_BASE_RENAME = _rename
_R43_BASE_FLOOR = None


def _r43_after(name, result):
    _boundary(name)
    return result


def install(mod):
    _R43_BASE_INSTALL(mod)
    base_activate = mod._OperationExecutionAuthority.activate
    base_claim = mod._claim_transition
    base_catalog = mod._catalog_names
    base_drop = mod.drop_db
    base_rename = mod.rename_db
    base_floor = mod._verify_against_floor
    base_record = mod._record_transition

    def activate(self):
        return _r43_after("after_execution_metadata", base_activate(self))

    def claim(operation_id, transition, promote=None):
        return _r43_after("after_rollback_claim", base_claim(operation_id, transition, promote))

    def catalog(container, user):
        return _r43_after("before_first_catalog_mutation", base_catalog(container, user))

    def drop(container, user, name):
        return _r43_after("after_promoted_canonical_removal", base_drop(container, user, name))

    def rename(container, user, source, target):
        return _r43_after("after_quarantine_rename", base_rename(container, user, source, target))

    def floor(container, db, user, value):
        return _r43_after("after_old_content_verification", base_floor(container, db, user, value))

    def record(operation_id, state, receipt, extra=None):
        if state == "ROLLED_BACK":
            _boundary("before_terminal_rolled_back_record")
        return base_record(operation_id, state, receipt, extra=extra)

    mod._OperationExecutionAuthority.activate = activate
    mod._claim_transition = claim
    mod._catalog_names = catalog
    mod.drop_db = drop
    mod.rename_db = rename
    mod._verify_against_floor = floor
    mod._record_transition = record
'''


def _r43_bridge(harness):
    harness.bridge.write_text(BRIDGE_SOURCE + _R43_PATCH, encoding="utf-8")
    _clear(harness)


def _rollback_argv(harness, output):
    return [
        "--phase", "rollback", "--receipt-in", str(harness.promote),
        "--inventory", str(harness.inventory), "--inventory-sha",
        str(harness.inventory_sha), "--db", "oce_local", "--user",
        "oce_local_admin", "--container", "oce-local-postgresql",
        "--receipt-out", str(output),
    ]


def _resume_rollback_argv(harness, output):
    return [
        "--phase", "resume-rollback", "--receipt-in", str(harness.promote),
        "--inventory", str(harness.inventory), "--inventory-sha",
        str(harness.inventory_sha), "--db", "oce_local", "--user",
        "oce_local_admin", "--container", "oce-local-postgresql",
        "--receipt-out", str(output),
    ]


def _spawn(harness, argv):
    return subprocess.Popen(
        recovery_cli.cli_argv(argv, str(harness.root), str(harness.bridge)),
        env=harness.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _run(harness, argv):
    result = recovery_cli.run_cli(
        argv, write_root=str(harness.root), bridge=str(harness.bridge),
        env_extra=_env(harness.tmp), timeout=60)
    return result


@pytest.mark.parametrize("boundary", [
    "after_rollback_claim", "before_first_catalog_mutation",
    "after_promoted_canonical_removal", "after_quarantine_rename",
    "after_old_content_verification", "before_terminal_rolled_back_record",
])
def test_real_process_rollback_crash_boundaries_resume_to_old(boundary, tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": boundary}), encoding="utf-8")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)
    assert _record(h)["state"] == "ROLLING_BACK"
    result = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert result.returncode == 0, result.stderr
    receipt = json.loads((h.root / "resumed.json").read_text(encoding="utf-8"))
    assert receipt["exit_status"] == 0
    assert receipt["resumed"] is True
    assert receipt["rollback_succeeded"] is True
    assert _record(h)["state"] == "ROLLED_BACK"
    assert h.root.joinpath("transitions", receipt["operation_id"] + ".claim").is_file()
    assert receipt["quarantine_database"] not in _dbs(h)
    assert "oce_local" in _dbs(h)


def test_claim_before_finalize_state_keeps_governed_abort_authority(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    promote = json.loads(h.promote.read_text(encoding="utf-8"))
    opid = promote["operation_id"]
    record_path = h.transitions / f"{opid}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["state"] = "PROMOTED"
    record.pop("selected_transition", None)
    record_path.write_text(json.dumps(record), encoding="utf-8")
    canonical = json.dumps(promote, sort_keys=True, separators=(",", ":"))
    (h.transitions / f"{opid}.claim").write_text(json.dumps({
        "format": "oce-transition-claim-v1", "operation_id": opid,
        "transition": "finalize",
        "receipt_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "claimed_at": "2026-09-24T00:00:00Z",
    }), encoding="utf-8")
    result = _run(h, [
        "--phase", "preintent-rollback", "--receipt-in", str(h.promote),
        "--inventory", str(h.inventory), "--inventory-sha", str(h.inventory_sha),
        "--db", "oce_local", "--user", "oce_local_admin", "--container",
        "oce-local-postgresql", "--receipt-out", str(h.root / "abort.json"),
    ])
    assert result.returncode == 0, result.stderr
    assert _record(h)["state"] == "ROLLED_BACK"


def test_metadata_publication_before_claim_keeps_fresh_authority(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": "after_execution_metadata"}), encoding="utf-8")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)
    assert _record(h)["state"] == "PROMOTED"
    assert not h.transitions.joinpath(
        json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"] + ".claim"
    ).exists()
    result = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert result.returncode == 0, result.stderr
    assert _record(h)["state"] == "ROLLED_BACK"


def test_stable_coordinate_inode_and_metadata_survive_contending_process(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    coordinate = h.transitions / f"{opid}.execution.lock"
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": "after_execution_metadata"}), encoding="utf-8")
    first = _spawn(h, _rollback_argv(h, h.root / "first.json"))
    _kill_at_signal(first, h.signal)
    inode = coordinate.stat().st_ino
    _clear(h)
    contender = _run(h, _rollback_argv(h, h.root / "contender.json"))
    assert contender.returncode == 0, contender.stderr
    assert coordinate.stat().st_ino == inode
    metadata = h.transitions / f"{opid}.execution.json"
    assert json.loads(metadata.read_text(encoding="utf-8"))["operation_id"] == opid
    assert _record(h)["state"] == "ROLLED_BACK"


def _weakened_engine(tmp_path, transform):
    source = CLI.read_text(encoding="utf-8")
    changed = transform(source)
    assert changed != source
    path = tmp_path / "weakened-pg-recovery.py"
    path.write_text(changed, encoding="utf-8")
    return path


def test_weakened_missing_resume_routes_back_to_fresh_and_fails(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": "after_rollback_claim"}), encoding="utf-8")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)
    weak = _weakened_engine(
        tmp_path, lambda source: source.replace(
            'elif phase == "resume-rollback":',
            'elif phase == "disabled-resume-rollback":'))
    args = _resume_rollback_argv(h, h.root / "weak.json")
    base = [sys.executable, "-c", recovery_cli._BOOTSTRAP, str(weak),
            str(h.root), "--test-bridge", str(h.bridge)]
    result = subprocess.run(base + list(map(str, args)), env=h.env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 1
    assert "no longer available" in result.stderr or "authority" in result.stderr
    real = _run(h, _resume_rollback_argv(h, h.root / "real.json"))
    assert real.returncode == 0, real.stderr


def test_weakened_rolling_back_classifier_reopens_fresh_authority(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": "after_rollback_claim"}), encoding="utf-8")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)
    args = ["--phase", "reconcile", "--classify-rollback", str(h.promote),
            "--transition-dir", str(h.transitions)]
    weak = _weakened_engine(
        tmp_path, lambda source: source.replace(
            '        return 6\n    if state == "ROLLED_BACK":',
            '        return 0\n    if state == "ROLLED_BACK":'))
    base = [sys.executable, "-c", recovery_cli._BOOTSTRAP, str(weak),
            str(h.root), "--test-bridge", str(h.bridge)]
    weakened = subprocess.run(base + args, env=h.env, capture_output=True,
                               text=True, timeout=60)
    real = subprocess.run([sys.executable, str(CLI), *args], env=h.env,
                          capture_output=True, text=True, timeout=60)
    assert weakened.returncode == 0
    assert real.returncode == 6
