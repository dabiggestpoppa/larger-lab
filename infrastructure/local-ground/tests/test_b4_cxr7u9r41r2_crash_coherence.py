#!/usr/bin/env python3
"""B4-CXR7U9R41-R2 — real crash/restart coherence at every finalize boundary.

The production engine has no crash switch. These proofs inject a boundary only
through the existing test-only child-process bridge: after promotion, the bridge
stalls immediately after one real engine action and the parent kills the actual
CLI process. A fresh CLI process must then reconcile or resume the same operation.

The eight named positive cases are intentionally separate node IDs. The three
negative controls execute weakened engine copies and observe the defect; they
never substitute source-string assertions for runtime behavior.
"""
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

import recovery_cli

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "scripts"
CLI = SCRIPTS / "pg-recovery.py"
BASH = shutil.which("bash") or "bash"

INVENTORY = {
    "format": "oce-pg-inventory-v1",
    "database": "oce_local",
    "table_count": 1,
    "tables": [{"name": "public.widgets", "row_count": 3,
                "fingerprint": "deadbeef"}],
}


@dataclass
class Harness:
    tmp: Path
    bridge_dir: Path
    bridge: Path
    root: Path
    promote: Path
    inventory: Path
    inventory_sha: Path
    env: dict

    @property
    def transitions(self):
        return self.root / "transitions"

    @property
    def signal(self):
        return self.bridge_dir / "signal"


BRIDGE_SOURCE = r'''import hashlib
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "dbs.json")
CONFIG = os.path.join(HERE, "crash.json")
SIGNAL = os.path.join(HERE, "signal")
EVENTS = os.path.join(HERE, "events.jsonl")


def _read():
    with open(STATE, encoding="utf-8") as f:
        return set(json.load(f))


def _write(dbs):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(sorted(dbs), f)
        f.flush()
        os.fsync(f.fileno())


def _boundary(name):
    try:
        with open(CONFIG, encoding="utf-8") as f:
            configured = json.load(f).get("boundary")
    except (OSError, ValueError):
        configured = None
    if configured != name:
        return
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"boundary": name}) + "\n")
        f.flush()
        os.fsync(f.fileno())
    with open(SIGNAL, "w", encoding="utf-8") as f:
        f.write(name)
        f.flush()
        os.fsync(f.fileno())
    while True:
        time.sleep(0.1)


if not os.path.exists(STATE):
    _write({"postgres", "oce_local"})


def _clone(container, archive_path):
    return str(archive_path)


def _validate(container, remote):
    return "ok"


def _remote_hash(container, remote):
    return hashlib.sha256(open(str(remote), "rb").read()).hexdigest()


def _staging(container, user, base_db, stamp):
    dbs = _read()
    dbs.add("oce_local_restore_" + stamp)
    _write(dbs)
    return "oce_local_restore_" + stamp


def _drop(container, user, name):
    dbs = _read()
    if name not in dbs:
        raise RuntimeError("bridge drop of unknown database " + name)
    dbs.remove(name)
    _write(dbs)
    _boundary("after_drop_before_commit_point")


def _rename(container, user, from_name, to_name):
    dbs = _read()
    dbs.remove(from_name)
    dbs.add(to_name)
    _write(dbs)


def _terminate(container, user, *dbs):
    return None


def _verify(container, db, user, inventory, probe):
    _boundary("after_claim_before_verification")
    result = (True, [], {"public.widgets": 3}, {"public.widgets": "deadbeef"})
    _boundary("after_verification_before_intent")
    return result


def _rows(container, db, user, tables):
    return {table: 3 for table in tables}


def _fps(container, db, user, tables):
    return {table: "deadbeef" for table in tables}


def _exists(container, user, name):
    result = name in _read()
    if not result:
        _boundary("after_removal_verification")
    return result


def _catalog(container, user):
    return _read()


class _Result:
    returncode = 0
    stdout = b"16.2\n"
    stderr = b""


def _docker_exec(container, cmd, stdin_bytes=None, timeout=600):
    return _Result()


def install(mod):
    mod.clone_archive_into_container = _clone
    mod.validate_archive = _validate
    mod.sha256_remote_file = _remote_hash
    mod.create_staging_db = _staging
    mod.drop_db = _drop
    mod.rename_db = _rename
    mod.terminate_local_connections = _terminate
    mod._verify_db = _verify
    mod.collect_observed_rows = _rows
    mod.collect_observed_fingerprints = _fps
    mod.db_exists = _exists
    mod._catalog_names = _catalog
    mod.docker_exec = _docker_exec

    record_transition = mod._record_transition
    def record(operation_id, state, receipt, extra=None):
        record_transition(operation_id, state, receipt, extra=extra)
        if state == "COMMIT_INTENT_RECORDED":
            _boundary("after_intent_before_drop")
        elif state == "COMMIT_POINT_REACHED":
            _boundary("after_commit_point_before_removal_check")
        elif state == "FINALIZED":
            _boundary("after_finalized_before_receipt")
    mod._record_transition = record

    commit_receipt = mod._commit_receipt
    def commit(path, receipt):
        _boundary("after_finalized_before_receipt_commit")
        return commit_receipt(path, receipt)
    mod._commit_receipt = commit
'''


def _env(tmp_path):
    return {
        "OCE_BACKUP_ROOTS": str(tmp_path),
        "OCE_COMMIT": "a" * 40,
        "OCE_TREE": "b" * 40,
        "OCE_RUN_ID": "0123456789abcdef",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _prepare(tmp_path):
    bridge_dir = tmp_path / "bridge"
    bridge_dir.mkdir()
    bridge = bridge_dir / "bridge.py"
    bridge.write_text(BRIDGE_SOURCE, encoding="utf-8")
    (bridge_dir / "crash.json").write_text(json.dumps({"boundary": None}),
                                          encoding="utf-8")
    content = tmp_path / "content"
    content.mkdir()
    inventory_doc = json.dumps(INVENTORY, sort_keys=True, separators=(",", ":"))
    inventory = content / "inventory.json"
    inventory_sha = content / "inventory.json.sha256"
    inventory.write_text(inventory_doc, encoding="utf-8")
    inventory_sha.write_text(hashlib.sha256(inventory_doc.encode()).hexdigest(),
                             encoding="utf-8")
    (content / "archive.dump").write_bytes(b"PGDMP")
    root = tmp_path / "recovery"
    (root / "transitions").mkdir(parents=True)
    promote = root / "promote.json"
    env = {**os.environ, **_env(tmp_path)}
    result = recovery_cli.run_cli(
        ["--phase", "promote", "--archive", str(content / "archive.dump"),
         "--inventory", str(inventory), "--inventory-sha", str(inventory_sha),
         "--db", "oce_local", "--user", "oce_local_admin",
         "--container", "oce-local-postgresql", "--receipt-out", str(promote)],
        write_root=str(root), bridge=str(bridge), env_extra=_env(tmp_path),
        timeout=60)
    assert result.returncode == 0, result.stderr
    return Harness(tmp_path, bridge_dir, bridge, root, promote, inventory,
                   inventory_sha, env)


def _finalize_argv(harness, output):
    return [
        "--phase", "finalize", "--receipt-in", str(harness.promote),
        "--inventory", str(harness.inventory), "--inventory-sha",
        str(harness.inventory_sha), "--db", "oce_local", "--user",
        "oce_local_admin", "--container", "oce-local-postgresql",
        "--receipt-out", str(output),
    ]


def _resume_argv(harness, output):
    return ["--phase", "resume-finalize", *_finalize_argv(harness, output)[2:]]


def _arm(harness, boundary):
    harness.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": boundary}), encoding="utf-8")
    harness.signal.unlink(missing_ok=True)


def _clear(harness):
    harness.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": None}), encoding="utf-8")
    harness.signal.unlink(missing_ok=True)


def _kill_at_signal(process, signal, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if signal.is_file():
            process.kill()
            process.communicate(timeout=10)
            assert process.returncode != 0
            return
        if process.poll() is not None:
            out, err = process.communicate()
            raise AssertionError(f"child exited before crash boundary: {out!r} {err!r}")
        time.sleep(0.01)
    process.kill()
    process.communicate(timeout=10)
    raise AssertionError("child never reached injected crash boundary")


def _crash_finalize(harness, boundary, output):
    _arm(harness, boundary)
    process = subprocess.Popen(
        recovery_cli.cli_argv(_finalize_argv(harness, output), str(harness.root),
                              str(harness.bridge)),
        env=harness.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True)
    _kill_at_signal(process, harness.signal)
    _clear(harness)
    assert not output.exists(), f"crash boundary {boundary} unexpectedly wrote receipt"


def _record(harness):
    receipt = json.loads(harness.promote.read_text(encoding="utf-8"))
    opid = receipt["operation_id"]
    return json.loads((harness.transitions / f"{opid}.json").read_text(
        encoding="utf-8"))


def _dbs(harness):
    return set(json.loads((harness.bridge_dir / "dbs.json").read_text(
        encoding="utf-8")))


def _classify(harness):
    return subprocess.run(
        [sys.executable, str(CLI), "--phase", "reconcile",
         "--classify-rollback", str(harness.promote), "--transition-dir",
         str(harness.transitions)], env=harness.env, capture_output=True,
        text=True, timeout=30).returncode


def _reconcile(harness, name):
    output = harness.root / name
    result = recovery_cli.run_cli(
        ["--phase", "reconcile", "--receipt-in", str(harness.promote),
         "--inventory", str(harness.inventory), "--inventory-sha",
         str(harness.inventory_sha), "--db", "oce_local", "--user",
         "oce_local_admin", "--container", "oce-local-postgresql",
         "--receipt-out", str(output)], write_root=str(harness.root),
        bridge=str(harness.bridge), env_extra=_env(harness.tmp), timeout=60)
    assert result.returncode in (0, 1), result.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def _resume(harness, name):
    output = harness.root / name
    result = recovery_cli.run_cli(
        _resume_argv(harness, output), write_root=str(harness.root),
        bridge=str(harness.bridge), env_extra=_env(harness.tmp), timeout=60)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["resumed"] is True
    assert receipt["commit_intent_recorded"] is True
    assert receipt["commit_point_recorded"] is True
    assert _record(harness)["state"] == "FINALIZED"
    assert _classify(harness) == 3
    return receipt


def _finish_from_intent(harness):
    decision = _reconcile(harness, "reconcile-after-crash.json")
    assert decision["verdict"] == "resume_required", decision
    assert _classify(harness) == 3
    _resume(harness, "resume-after-crash.json")


def _finish_from_commit_point(harness):
    decision = _reconcile(harness, "reconcile-after-crash.json")
    assert decision["verdict"] == "committed", decision
    assert _classify(harness) == 3
    _resume(harness, "resume-after-crash.json")


def test_crash_01_after_finalize_claim_before_verification(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_claim_before_verification", h.root / "crash.json")
    assert _record(h)["state"] == "FINALIZING"
    decision = _reconcile(h, "reconcile-01.json")
    assert decision["verdict"] == "preintent_abort_required", decision
    assert _classify(h) == 5


def test_crash_02_after_verification_before_intent(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_verification_before_intent", h.root / "crash.json")
    assert _record(h)["state"] == "FINALIZING"
    decision = _reconcile(h, "reconcile-02.json")
    assert decision["verdict"] == "preintent_abort_required", decision
    assert _classify(h) == 5


def test_crash_03_after_commit_intent_before_drop(tmp_path):
    h = _prepare(tmp_path)
    receipt = json.loads(h.promote.read_text(encoding="utf-8"))
    _crash_finalize(h, "after_intent_before_drop", h.root / "crash.json")
    assert _record(h)["state"] == "COMMIT_INTENT_RECORDED"
    assert receipt["quarantine_database"] in _dbs(h)
    _finish_from_intent(h)


def test_crash_04_after_drop_before_commit_point_record(tmp_path):
    h = _prepare(tmp_path)
    receipt = json.loads(h.promote.read_text(encoding="utf-8"))
    _crash_finalize(h, "after_drop_before_commit_point", h.root / "crash.json")
    assert _record(h)["state"] == "COMMIT_INTENT_RECORDED"
    assert receipt["quarantine_database"] not in _dbs(h)
    _finish_from_intent(h)


def test_crash_05_after_commit_point_before_removal_check(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_commit_point_before_removal_check",
                    h.root / "crash.json")
    assert _record(h)["state"] == "COMMIT_POINT_REACHED"
    _finish_from_commit_point(h)


def test_crash_06_after_removal_verification_before_finalized(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_removal_verification", h.root / "crash.json")
    assert _record(h)["state"] == "COMMIT_POINT_REACHED"
    _finish_from_commit_point(h)


def test_crash_07_after_finalized_before_receipt_commit(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_finalized_before_receipt_commit",
                    h.root / "crash.json")
    assert _record(h)["state"] == "FINALIZED"
    assert _reconcile(h, "reconcile-07.json")["verdict"] == "committed"
    _resume(h, "resume-07.json")


def test_crash_08_after_finalize_receipt_before_shell_commit_flag(tmp_path):
    h = _prepare(tmp_path)
    _clear(h)
    output = h.root / "finalize-shell.json"
    command = recovery_cli.cli_argv(_finalize_argv(h, output), str(h.root),
                                    str(h.bridge))
    worker = h.tmp / "restore-worker.sh"
    worker.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        + shlex.join(command) + "\n"
        + f"test -f {shlex.quote(output.as_posix())}\n"
        + f": > {shlex.quote(h.signal.as_posix())}\n"
        + "exec sleep 300\n"
        + "PG_FINALIZED=true\n",
        encoding="utf-8")
    process = subprocess.Popen([BASH, str(worker)], env=h.env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
    _kill_at_signal(process, h.signal)
    assert output.is_file()
    assert _record(h)["state"] == "FINALIZED"
    assert _reconcile(h, "reconcile-08.json")["verdict"] == "committed"
    _resume(h, "resume-08.json")


@pytest.mark.parametrize("binding", [
    "operation_id",
    "promote_receipt_digest",
    "existing_finalize_claim",
    "canonical_database_identity",
    "durable_intent",
])
def test_resume_authority_rejects_mismatched_binding(tmp_path, binding):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_intent_before_drop", h.root / "crash.json")
    promote_path = h.promote
    promote = json.loads(promote_path.read_text(encoding="utf-8"))
    opid = promote["operation_id"]
    record_path = h.transitions / f"{opid}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    before = dict(record)
    if binding == "operation_id":
        promote["operation_id"] = "f" * 32
        promote_path.write_text(json.dumps(promote), encoding="utf-8")
    elif binding == "promote_receipt_digest":
        promote["source_archive_sha256"] = "e" * 64
        promote_path.write_text(json.dumps(promote), encoding="utf-8")
    elif binding == "existing_finalize_claim":
        claim_path = h.transitions / f"{opid}.claim"
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        claim["receipt_sha256"] = "e" * 64
        claim_path.write_text(json.dumps(claim), encoding="utf-8")
    elif binding == "canonical_database_identity":
        record["container"] = "different-postgresql"
        record_path.write_text(json.dumps(record), encoding="utf-8")
    else:
        record.pop("commit_intent")
        record_path.write_text(json.dumps(record), encoding="utf-8")

    result = recovery_cli.run_cli(
        _resume_argv(h, h.root / f"refused-{binding}.json"),
        write_root=str(h.root), bridge=str(h.bridge),
        env_extra=_env(h.tmp), timeout=60)
    assert result.returncode == 1
    assert "refusing recovery resume authority" in result.stderr
    assert promote["quarantine_database"] in _dbs(h)
    durable = json.loads(record_path.read_text(encoding="utf-8"))
    if binding in ("canonical_database_identity", "durable_intent"):
        assert durable == record
    else:
        assert durable == before


def _weakened_engine(tmp_path, transform):
    source = CLI.read_text(encoding="utf-8")
    changed = transform(source)
    assert changed != source
    path = tmp_path / "weakened-pg-recovery.py"
    path.write_text(changed, encoding="utf-8")
    return path


def _weakened_cli(engine, write_root, bridge, argv):
    base = [sys.executable, "-c", recovery_cli._BOOTSTRAP, str(engine),
            str(write_root)]
    if bridge is not None:
        base += ["--test-bridge", str(bridge)]
    return base + list(map(str, argv))


def test_control_old_drop_order_reproduces_lost_intent_window(tmp_path):
    """Negative control: execute the former DROP-before-record ordering in a
    real child. It loses the quarantine and leaves FINALIZING, exactly the
    incoherence the real intent boundary prevents."""
    h = _prepare(tmp_path)

    def old_order(source):
        block = '''        if not resumed or durable_state == TRANSITION_STATE_FINALIZING:\n            _record_transition(\n                operation_id, TRANSITION_STATE_COMMIT_INTENT, promote,\n                extra={"commit_intent": {\n                    "marker": "forward_commit",\n                    "operation_id": operation_id,\n                    "receipt_sha256": _receipt_digest(promote),\n                    "database": db,\n                    "user": user,\n                    "container": container,\n                    "quarantine_database": quarantine,\n                    "at": now_iso()}})\n            durable_state = TRANSITION_STATE_COMMIT_INTENT\n        receipt["commit_intent_recorded"] = True\n'''
        assert block in source
        return source.replace(block, "")

    engine = _weakened_engine(tmp_path, old_order)
    _arm(h, "after_drop_before_commit_point")
    process = subprocess.Popen(
        _weakened_cli(engine, h.root, h.bridge,
                      _finalize_argv(h, h.root / "old-order.json")),
        env=h.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _kill_at_signal(process, h.signal)
    _clear(h)
    receipt = json.loads(h.promote.read_text(encoding="utf-8"))
    assert _record(h)["state"] == "FINALIZING"
    assert receipt["quarantine_database"] not in _dbs(h)
    decision = _reconcile(h, "old-order-reconcile.json")
    assert decision["verdict"] == "unreconciled"


def test_control_impossible_marker_classifier_reopens_old_window(tmp_path):
    """Negative control: the former marker exception runs and classifies the
    impossible FINALIZING+marker record as rollback-safe/postcommit; the real
    engine rejects that malformed state."""
    record = tmp_path / "impossible.json"
    record.write_text(json.dumps({
        "state": "FINALIZING",
        "commit_point": {"marker": "quarantine_dropped",
                         "at": "2026-09-24T00:00:00Z"},
    }), encoding="utf-8")

    def old_marker(source):
        old = '''        if record.get("commit_intent") is not None or record.get("commit_point") is not None:\n            return 4\n        if record.get("selected_transition") == "finalize":\n            return 5\n        return 4\n'''
        new = '''        marker = record.get("commit_point")\n        return 3 if isinstance(marker, dict) and marker.get("marker") else 0\n'''
        assert old in source
        return source.replace(old, new)

    engine = _weakened_engine(tmp_path, old_marker)
    args = ["--phase", "reconcile", "--classify-state", str(record)]
    weak = subprocess.run(_weakened_cli(engine, tmp_path / "unused", None, args),
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                          capture_output=True, text=True, timeout=30)
    real = subprocess.run([sys.executable, str(CLI), *args],
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                          capture_output=True, text=True, timeout=30)
    assert weak.returncode == 3
    assert real.returncode == 4


def test_control_permissive_missing_record_classifier(tmp_path):
    """Negative control: execute a classifier that treats a missing durable
    record as precommit. The real engine fails closed with code 4."""
    h = _prepare(tmp_path)
    h.transitions.joinpath(
        json.loads(h.promote.read_text(encoding="utf-8"))["operation_id"]
        + ".json").unlink()

    def permissive(source):
        old = '''    except (OSError, ValueError, RuntimeError, TypeError):\n        return 4\n\n\ndef _parse_cli'''
        new = '''    except (OSError, ValueError, RuntimeError, TypeError):\n        return 0\n\n\ndef _parse_cli'''
        assert old in source
        return source.replace(old, new)

    engine = _weakened_engine(tmp_path, permissive)
    args = ["--phase", "reconcile", "--classify-rollback", str(h.promote),
            "--transition-dir", str(h.transitions)]
    weak = subprocess.run(
        _weakened_cli(engine, h.root, h.bridge, args), env=h.env,
        capture_output=True, text=True, timeout=30)
    real = subprocess.run([sys.executable, str(CLI), *args], env=h.env,
                          capture_output=True, text=True, timeout=30)
    assert weak.returncode == 0
    assert real.returncode == 4
