#!/usr/bin/env python3
"""B4-CXR7U9R43 — stable lock inode and governed rollback-resume proofs."""
import hashlib
import json
import os
import subprocess
import sys
import time
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

# The bridge records lock ownership as an observation, never as authority.
# This lets the race proofs observe whether a contender acquired the same
# coordinate while another process was paused inside its mutation interval.
_R43_DENIAL_PATCH = r'''

_R43_DENIAL_BASE_INSTALL = install
_R43_DENIAL_READY = os.path.join(HERE, "denial-ready")
_R43_DENIAL_RELEASE = os.path.join(HERE, "denial-release")
_R43_DENIAL_USED = os.path.join(HERE, "denial-used")
_R43_LOCK_EVENT_PATH = os.path.join(HERE, "lock-events.jsonl")


def _r43_lock_event(kind, operation_id):
    with open(_R43_LOCK_EVENT_PATH, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": kind, "operation_id": operation_id,
                                 "pid": os.getpid()}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def install(mod):
    _R43_DENIAL_BASE_INSTALL(mod)
    base_acquire = mod._OperationExecutionAuthority.acquire
    base_activate = mod._OperationExecutionAuthority.activate

    def acquire(authority):
        result = base_acquire(authority)
        _r43_lock_event("acquired", authority.operation_id)
        return result

    def activate(authority):
        result = base_activate(authority)
        if not os.path.exists(_R43_DENIAL_USED):
            with open(_R43_DENIAL_USED, "w", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
                stream.flush()
                os.fsync(stream.fileno())
            with open(_R43_DENIAL_READY, "w", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
                stream.flush()
                os.fsync(stream.fileno())
            while not os.path.exists(_R43_DENIAL_RELEASE):
                time.sleep(0.01)
            raise RuntimeError("injected metadata activation denial")
        return result

    mod._OperationExecutionAuthority.acquire = acquire
    mod._OperationExecutionAuthority.activate = activate
'''


_R43_FAULT_PATCH = r'''

_R43_FAULT_BASE_INSTALL = install

def install(mod):
    _R43_FAULT_BASE_INSTALL(mod)
    base_fsync = mod.os.fsync

    def fsync(fd):
        if os.environ.get("R43_FAIL_METADATA_FSYNC") == "1":
            raise OSError("injected metadata fsync failure")
        return base_fsync(fd)

    mod.os.fsync = fsync
'''


def _wait_for_path(path, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.is_file():
            return
        time.sleep(0.01)
    raise AssertionError(f"barrier was not reached: {path}")


def _lock_events(harness):
    path = harness.bridge_dir / "lock-events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _r43_denial_bridge(harness):
    harness.bridge.write_text(BRIDGE_SOURCE + _R43_PATCH + _R43_DENIAL_PATCH,
                              encoding="utf-8")
    for name in ("crash.json", "denial-ready", "denial-release", "denial-used",
                 "lock-events.jsonl"):
        harness.bridge_dir.joinpath(name).unlink(missing_ok=True)
    harness.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": None}), encoding="utf-8")


def _r43_fault_bridge(harness):
    harness.bridge.write_text(BRIDGE_SOURCE + _R43_PATCH + _R43_FAULT_PATCH,
                              encoding="utf-8")
    _clear(harness)


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


def _spawn(harness, argv, env_extra=None, engine=None):
    env = dict(harness.env)
    env.update(env_extra or {})
    if engine is None:
        command = recovery_cli.cli_argv(argv, str(harness.root), str(harness.bridge))
    else:
        command = [sys.executable, "-c", recovery_cli._BOOTSTRAP, str(engine),
                   str(harness.root), "--test-bridge", str(harness.bridge)]
        command.extend(map(str, argv))
    return subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)


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


def _wait_for_lock_count(harness, count, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        events = _lock_events(harness)
        if len(events) >= count:
            return events
        time.sleep(0.01)
    raise AssertionError(f"lock acquisition barrier was not reached: {events!r}")


def _terminate(processes):
    for process in processes:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)


def test_three_process_denial_race_keeps_one_inode_and_succeeding_metadata(tmp_path):
    h = _prepare(tmp_path)
    _r43_denial_bridge(h)
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    coordinate = h.transitions / f"{opid}.execution.lock"
    processes = []
    try:
        denied = _spawn(h, _rollback_argv(h, h.root / "denied.json"))
        processes.append(denied)
        _wait_for_path(h.bridge_dir / "denial-ready")
        original_inode = coordinate.stat().st_ino
        _wait_for_lock_count(h, 1)

        h.bridge_dir.joinpath("denial-release").write_text("go", encoding="utf-8")
        denied_out, denied_err = denied.communicate(timeout=30)
        assert denied.returncode == 1, (denied_out, denied_err)
        assert _lock_events(h) == _lock_events(h)[:1]

        winner = _spawn(h, _rollback_argv(h, h.root / "winner.json"))
        processes.append(winner)
        h.bridge_dir.joinpath("crash.json").write_text(
            json.dumps({"boundary": "after_execution_metadata"}), encoding="utf-8")
        if winner.poll() is not None:
            winner_out, winner_err = winner.communicate()
            pytest.fail(f"winner exited before metadata barrier: {winner_out!r} {winner_err!r}")
        _wait_for_path(h.signal)
        _wait_for_lock_count(h, 2)
        metadata_path = h.transitions / f"{opid}.execution.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["pid"] == winner.pid

        contender = _spawn(h, _rollback_argv(h, h.root / "contender.json"))
        processes.append(contender)
        contender_out, contender_err = contender.communicate(timeout=30)
        assert contender.returncode == 1, (contender_out, contender_err)
        assert "execution authority" in contender_err
        assert len(_lock_events(h)) == 2
        assert coordinate.stat().st_ino == original_inode
        assert json.loads(metadata_path.read_text(encoding="utf-8")) == metadata

        winner.kill()
        winner.communicate(timeout=10)
        _clear(h)
        assert coordinate.stat().st_ino == original_inode
        assert _record(h)["state"] == "PROMOTED"
        assert not (h.transitions / f"{opid}.claim").exists()
    finally:
        _terminate(processes)


def test_metadata_fsync_failure_before_claim_keeps_fresh_authority(tmp_path):
    h = _prepare(tmp_path)
    _r43_fault_bridge(h)
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    process = _spawn(
        h, _rollback_argv(h, h.root / "fsync-failed.json"),
        {"R43_FAIL_METADATA_FSYNC": "1"})
    stdout, stderr = process.communicate(timeout=30)
    assert process.returncode == 1, (stdout, stderr)
    assert _record(h)["state"] == "PROMOTED"
    assert not h.transitions.joinpath(f"{opid}.claim").exists()
    assert not h.transitions.joinpath(f"{opid}.execution.json").exists()
    coordinate = h.transitions / f"{opid}.execution.lock"
    assert coordinate.is_file() and coordinate.stat().st_size == 1

    result = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert result.returncode == 0, result.stderr
    assert _record(h)["state"] == "ROLLED_BACK"


@pytest.mark.parametrize("catalog_state", [
    "staging_present", "canonical_and_original_absent", "forward_intent",
])
def test_rollback_resume_failures_never_guess_catalog_or_artifact_mutation(
        catalog_state, tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    h.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": "after_rollback_claim"}), encoding="utf-8")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)

    promote = json.loads(h.promote.read_text(encoding="utf-8"))
    dbs = _dbs(h)
    if catalog_state == "staging_present":
        dbs.add(promote["staging_database"])
    elif catalog_state == "canonical_and_original_absent":
        dbs = {"postgres"}
    h.bridge_dir.joinpath("dbs.json").write_text(
        json.dumps(sorted(dbs)), encoding="utf-8")
    if catalog_state == "forward_intent":
        record_path = h.transitions / f"{promote['operation_id']}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["commit_intent"] = {
            "marker": "forward_commit", "operation_id": promote["operation_id"],
            "receipt_sha256": record["receipt_sha256"], "at": "2026-09-24T00:00:00Z",
        }
        record_path.write_text(json.dumps(record), encoding="utf-8")

    artifact = tmp_path / "artifact-store"
    artifact.mkdir()
    marker = artifact / "old.bin"
    marker.write_bytes(b"verified-old-artifact")
    artifact_before = marker.read_bytes()
    catalog_before = _dbs(h)
    result = _run(h, _resume_rollback_argv(h, h.root / "failed.json"))
    assert result.returncode == 1
    assert _dbs(h) == catalog_before
    assert marker.read_bytes() == artifact_before
    assert _record(h)["state"] in ("ROLLING_BACK", "COMMIT_INTENT_RECORDED")
    assert len(list(h.transitions.glob("*.claim"))) == 1


def test_rolled_back_resume_is_idempotent_and_keeps_one_claim(tmp_path):
    h = _prepare(tmp_path)
    _r43_bridge(h)
    first = _run(h, _rollback_argv(h, h.root / "first.json"))
    assert first.returncode == 0, first.stderr
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    inode = h.transitions.joinpath(f"{opid}.execution.lock").stat().st_ino

    repeated = _run(h, _resume_rollback_argv(h, h.root / "repeated.json"))
    assert repeated.returncode == 0, repeated.stderr
    receipt = json.loads(h.root.joinpath("repeated.json").read_text(encoding="utf-8"))
    assert receipt["durable_state_at_admission"] == "ROLLED_BACK"
    assert receipt["catalog_state_at_admission"] == "quarantine_renamed"
    assert receipt["rollback_succeeded"] is True
    assert _record(h)["state"] == "ROLLED_BACK"
    assert len(list(h.transitions.glob("*.claim"))) == 1
    assert h.transitions.joinpath(f"{opid}.execution.lock").stat().st_ino == inode


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


def _post_unlock_unlink_engine(tmp_path):
    def transform(source):
        source = source.replace("import tempfile\n", "import tempfile\nimport time\n")
        return source.replace(
            "            os.close(self.fd)\n            self.fd = None\n        return False",
            "            os.close(self.fd)\n            self.fd = None\n"
            "            marker = os.environ.get('R43_WEAK_COORDINATE')\n"
            "            if marker:\n"
            "                with open(marker + '.ready', 'w', encoding='utf-8') as stream:\n"
            "                    stream.write(str(os.getpid()))\n"
            "                while not os.path.exists(marker + '.release'):\n"
            "                    time.sleep(0.01)\n"
            "            if self.activated and not self.metadata_committed:\n"
            "                try:\n"
            "                    os.unlink(self.path)\n"
            "                except FileNotFoundError:\n"
            "                    pass\n"
            "        return False",
        )
    return _weakened_engine(tmp_path, transform)


def _coordinate_replacement_engine(tmp_path):
    def transform(source):
        source = source.replace("import tempfile\n", "import tempfile\nimport time\n")
        return source.replace(
            "        except FileExistsError:\n            fd = os.open(self.path, os.O_RDWR, 0o600)",
            "        except FileExistsError:\n"
            "            fd = os.open(self.path + '.replacement', os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)",
        )
    return _weakened_engine(tmp_path, transform)


@pytest.mark.skipif(os.name == "nt", reason="unlink-open-coordinate race is exercised on Linux")
def test_weakened_post_unlock_unlink_allows_a_second_coordinate(tmp_path):
    h = _prepare(tmp_path)
    _r43_denial_bridge(h)
    weak = _post_unlock_unlink_engine(tmp_path)
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    coordinate = h.transitions / f"{opid}.execution.lock"
    processes = []
    try:
        denied = _spawn(
            h, _rollback_argv(h, h.root / "denied.json"), engine=weak,
            env_extra={"R43_WEAK_COORDINATE": str(h.bridge_dir / "weak-coordinate")})
        processes.append(denied)
        _wait_for_path(h.bridge_dir / "denial-ready")
        original_inode = coordinate.stat().st_ino
        h.bridge_dir.joinpath("denial-release").write_text("go", encoding="utf-8")
        _wait_for_path(h.bridge_dir / "weak-coordinate.ready")
        h.bridge_dir.joinpath("crash.json").write_text(
            json.dumps({"boundary": "after_execution_metadata"}), encoding="utf-8")
        winner = _spawn(h, _rollback_argv(h, h.root / "winner.json"), engine=weak)
        processes.append(winner)
        _wait_for_path(h.signal)
        _wait_for_lock_count(h, 2)
        h.bridge_dir.joinpath("weak-coordinate.release").write_text(
            "go", encoding="utf-8")
        denied.communicate(timeout=30)
        assert denied.returncode == 1
        contender = _spawn(h, _rollback_argv(h, h.root / "contender.json"), engine=weak)
        processes.append(contender)
        _wait_for_lock_count(h, 3)
        assert contender.poll() is None
        assert coordinate.stat().st_ino != original_inode
        assert len(_lock_events(h)) == 3
    finally:
        _terminate(processes)


def test_weakened_coordinate_replacement_lets_contender_lock_a_new_inode(tmp_path):
    h = _prepare(tmp_path)
    _r43_denial_bridge(h)
    weak = _coordinate_replacement_engine(tmp_path)
    opid = json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
    coordinate = h.transitions / f"{opid}.execution.lock"
    processes = []
    try:
        denied = _spawn(h, _rollback_argv(h, h.root / "denied.json"), engine=weak)
        processes.append(denied)
        _wait_for_path(h.bridge_dir / "denial-ready")
        original_inode = coordinate.stat().st_ino
        h.bridge_dir.joinpath("denial-release").write_text("go", encoding="utf-8")
        denied.communicate(timeout=30)
        assert denied.returncode == 1
        h.bridge_dir.joinpath("crash.json").write_text(
            json.dumps({"boundary": "after_execution_metadata"}), encoding="utf-8")
        winner = _spawn(h, _rollback_argv(h, h.root / "winner.json"), engine=weak)
        processes.append(winner)
        _wait_for_path(h.signal)
        _wait_for_lock_count(h, 2)
        assert winner.poll() is None
        replacement = Path(str(coordinate) + ".replacement")
        assert replacement.is_file()
        assert replacement.stat().st_ino != original_inode
    finally:
        _terminate(processes)


def test_authoritative_runner_selects_r43_and_collected_node_ids_are_unique(tmp_path):
    runner = SCRIPTS / "run-validation.sh"
    source = runner.read_text(encoding="utf-8")
    assert "R43_LOCK_ROLLBACK_RESUME_TEST=" in source
    assert "test_b4_cxr7u9r43_lock_inode_rollback_resume.py" in source
    env = dict(os.environ)
    env.pop("OCE_EVIDENCE_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", str(Path(__file__))],
        cwd=str(TESTS.parent), env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    nodeids = [line.strip() for line in result.stdout.splitlines()
               if "::" in line and Path(__file__).name in line]
    assert nodeids
    assert len(nodeids) == len(set(nodeids))
    assert all("test_b4_cxr7u9r43_lock_inode_rollback_resume.py::" in nodeid
               for nodeid in nodeids)
