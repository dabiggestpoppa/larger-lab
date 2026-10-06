#!/usr/bin/env python3
"""B4-CXR7U9R42-R2 — real-process execution-authority convergence proofs.

The production wrappers bind only enough receipt identity to name the OS lock.
All receipt/state authorization happens after lock acquisition. These tests use
separate Python processes, file barriers, the real OS advisory lock, and a
bridge that records every observable mutation call. The weakened-engine control
restores the pre-R42 unlocked fallback and must observe the defect.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

import recovery_cli
from test_b4_cxr7u9r41r2_crash_coherence import (
    BRIDGE_SOURCE,
    _arm,
    _finalize_argv,
    _prepare,
    _record,
    _resume_argv,
)
from test_b4_cxr7u9r41r4_completion import _abort_argv

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "scripts"
CLI = SCRIPTS / "pg-recovery.py"

_R42_PATCH = r'''

_MUTATIONS = os.path.join(HERE, "mutations.jsonl")
_R42_EVENTS = os.path.join(HERE, "r42-events.jsonl")
_BASE_STAGING = _staging
_BASE_DROP = _drop
_BASE_RENAME = _rename
_BASE_CATALOG = _catalog
_BASE_INSTALL = install


def _r42_event(path, event):
    event = dict(event)
    event["pid"] = os.getpid()
    with open(path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _r42_staging(container, user, base_db, stamp):
    result = _BASE_STAGING(container, user, base_db, stamp)
    _r42_event(_MUTATIONS, {"action": "staging", "name": result})
    return result


def _r42_drop(container, user, name):
    result = _BASE_DROP(container, user, name)
    _r42_event(_MUTATIONS, {"action": "drop", "name": name})
    return result


def _r42_rename(container, user, source, target):
    result = _BASE_RENAME(container, user, source, target)
    _r42_event(_MUTATIONS, {"action": "rename", "source": source, "target": target})
    return result


def _r42_catalog(container, user):
    _r42_event(_MUTATIONS, {"action": "catalog-read"})
    return _BASE_CATALOG(container, user)


def install(mod):
    _BASE_INSTALL(mod)
    mod.create_staging_db = _r42_staging
    mod.drop_db = _r42_drop
    mod.rename_db = _r42_rename
    mod._catalog_names = _r42_catalog
    record_transition = mod._record_transition

    def record(operation_id, state, receipt, extra=None):
        result = record_transition(operation_id, state, receipt, extra=extra)
        _r42_event(_MUTATIONS, {"action": "transition", "operation_id": operation_id,
                                "state": state})
        return result

    mod._record_transition = record

    if os.environ.get("R42_POSITIVE_PREFLIGHT") == "1":
        production_phase = mod.phase_resume_finalize

        def observed_phase(*args, **kwargs):
            try:
                mod._validated_resume_finalize_receipt(
                    args[0], args[3], args[4], args[5], args[1], args[2])
            except Exception as exc:
                _r42_event(_R42_EVENTS,
                           {"action": "initial-resume-validation-denied",
                            "error": str(exc)})
            return production_phase(*args, **kwargs)

        mod.phase_resume_finalize = observed_phase

    if os.environ.get("R42_PREFLIGHT_RESUME") == "1":
        validation = mod._validated_resume_finalize_receipt
        first = {"done": False}

        def preflight(*args, **kwargs):
            if not first["done"]:
                first["done"] = True
                try:
                    return validation(*args, **kwargs)
                except Exception as exc:
                    _r42_event(_R42_EVENTS, {"action": "initial-resume-validation-denied",
                                             "error": str(exc)})
                    release = os.path.join(HERE, "release-preflight")
                    if os.environ.get("R42_PAUSE_PREFLIGHT") == "1":
                        while not os.path.exists(release):
                            time.sleep(0.01)
                    raise
            return validation(*args, **kwargs)

        mod._validated_resume_finalize_receipt = preflight

    if os.environ.get("R42_PAUSE_BINDING") == "1":
        binding = mod._execution_receipt_binding

        def paused_binding(path):
            result = binding(path)
            _r42_event(_R42_EVENTS, {"action": "minimal-receipt-bound",
                                     "operation_id": result[1]})
            release = os.path.join(HERE, "release-binding")
            while not os.path.exists(release):
                time.sleep(0.01)
            return result

        mod._execution_receipt_binding = paused_binding
'''

R42_BASE_SOURCE = BRIDGE_SOURCE.replace(
    "    while True:\n        time.sleep(0.1)",
    "    while not os.path.exists(os.path.join(HERE, \"release\")):\n        time.sleep(0.01)")
R42_BRIDGE_SOURCE = R42_BASE_SOURCE + _R42_PATCH


def _wait_for(path, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.is_file():
            return
        time.sleep(0.01)
    raise AssertionError(f"barrier was not reached: {path}")


def _spawn(harness, argv, output, env_extra=None):
    env = dict(harness.env)
    env.update(env_extra or {})
    return subprocess.Popen(
        recovery_cli.cli_argv(argv, str(harness.root), str(harness.bridge)),
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _r42_bridge(harness):
    harness.bridge.write_text(R42_BRIDGE_SOURCE, encoding="utf-8")
    harness.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": None}), encoding="utf-8")
    harness.bridge_dir.joinpath("mutations.jsonl").unlink(missing_ok=True)
    harness.bridge_dir.joinpath("r42-events.jsonl").unlink(missing_ok=True)
    harness.signal.unlink(missing_ok=True)
    for name in ("release", "release-preflight", "release-binding"):
        harness.bridge_dir.joinpath(name).unlink(missing_ok=True)


def _bytes(path):
    if not path.is_file():
        return None
    try:
        return path.read_bytes()
    except PermissionError:
        metadata = path.stat()
        return {"os_locked": True, "size": metadata.st_size,
                "mtime_ns": metadata.st_mtime_ns}


def _wait_for_event(harness, action, timeout=30):
    path = harness.bridge_dir / "r42-events.jsonl"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                if event.get("action") == action:
                    return event
        time.sleep(0.01)
    raise AssertionError(f"R42 event barrier was not reached: {action}")


def _mutation_log(harness):
    path = harness.bridge_dir / "mutations.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _snapshot(harness, artifact):
    receipt = json.loads(harness.promote.read_text(encoding="utf-8"))
    opid = receipt["operation_id"]
    transitions = harness.transitions
    return {
        "transition": _bytes(transitions / f"{opid}.json"),
        "claim": _bytes(transitions / f"{opid}.claim"),
        # R43 creates this stable, evidence-free coordinate before full
        # authorization. Its lifecycle/inode safety is proven separately.
        "execution_metadata": _bytes(transitions / f"{opid}.execution.json"),
        "receipts": {p.name: _bytes(p) for p in sorted(harness.root.glob("*.json"))},
        "postgres_catalog": _bytes(harness.bridge_dir / "dbs.json"),
        "artifact": {p.name: _bytes(p) for p in sorted(artifact.iterdir())},
        "mutation_log": _mutation_log(harness),
    }


def _assert_denied_without_side_effects(before, after):
    assert after == before


def _release_and_join(process, harness):
    harness.bridge_dir.joinpath("release-intent").unlink(missing_ok=True)
    process.communicate(timeout=60)


def test_resume_finalize_invalid_to_valid_race_is_denied_with_zero_effects(tmp_path):
    h = _prepare(tmp_path)
    _r42_bridge(h)
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "sentinel").write_bytes(b"unchanged")

    a = _spawn(h, _resume_argv(h, h.root / "a-denied.json"), h.root / "a-denied.json",
               {"R42_POSITIVE_PREFLIGHT": "1", "R42_PAUSE_BINDING": "1"})
    _wait_for_event(h, "initial-resume-validation-denied")
    _wait_for_event(h, "minimal-receipt-bound")

    _arm(h, "after_intent_before_drop")
    b = _spawn(h, _finalize_argv(h, h.root / "b-finalize.json"), h.root / "b-finalize.json")
    _wait_for(h.signal)
    assert h.signal.is_file()
    before = _snapshot(h, artifact)
    h.bridge_dir.joinpath("release-binding").write_text("go", encoding="utf-8")
    result_a = a.communicate(timeout=60)
    after = _snapshot(h, artifact)
    _assert_denied_without_side_effects(before, after)
    assert result_a[1].find("execution authority") >= 0, result_a
    assert not (h.root / "a-denied.json").exists()
    assert _record(h)["state"] == "COMMIT_INTENT_RECORDED"
    assert all(item.get("pid") != a.pid for item in _mutation_log(h))

    h.bridge_dir.joinpath("release").write_text("go", encoding="utf-8")
    result_b = b.communicate(timeout=60)
    assert result_b[0].strip().endswith("b-finalize.json") or result_b[1] == "", result_b
    assert _record(h)["state"] == "FINALIZED"


@pytest.mark.parametrize("phase", ["finalize", "rollback", "preintent-rollback"])
def test_all_recovery_wrappers_have_zero_effects_under_active_lock_contention(
        phase, tmp_path):
    h = _prepare(tmp_path)
    _r42_bridge(h)
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "sentinel").write_bytes(b"unchanged")
    _arm(h, "after_intent_before_drop")
    holder = _spawn(h, _finalize_argv(h, h.root / "holder.json"), h.root / "holder.json")
    _wait_for(h.signal)
    before = _snapshot(h, artifact)
    if phase == "finalize":
        argv = _finalize_argv(h, h.root / "contender.json")
    elif phase == "rollback":
        argv = ["--phase", "rollback", *_finalize_argv(h, h.root / "contender.json")[2:]]
    else:
        argv = _abort_argv(h, h.root / "contender.json")
    argv = [arg for index, arg in enumerate(argv)
            if not (index > 0 and argv[index - 1] == "--receipt-out")]
    contender = subprocess.Popen(
        recovery_cli.cli_argv(argv, str(h.root), str(h.bridge)), env=h.env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = contender.communicate(timeout=60)
    assert contender.returncode == 1, (stdout, stderr)
    _assert_denied_without_side_effects(before, _snapshot(h, artifact))
    assert not (h.root / "contender.json").exists()
    h.bridge_dir.joinpath("release").write_text("go", encoding="utf-8")
    holder.communicate(timeout=60)
    assert holder.returncode == 0


def _run_denial_without_receipt(harness, receipt, phase):
    argv = ["--phase", phase, "--receipt-in", str(receipt), "--inventory",
            str(harness.inventory), "--inventory-sha", str(harness.inventory_sha),
            "--db", "oce_local", "--user", "oce_local_admin", "--container",
            "oce-local-postgresql"]
    return subprocess.run(recovery_cli.cli_argv(argv, str(harness.root),
                                                str(harness.bridge)), env=harness.env,
                          capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("kind", ["malformed", "digest-substitution", "unregistered"])
def test_invalid_receipts_have_zero_authority_side_effects(kind, tmp_path):
    h = _prepare(tmp_path)
    _r42_bridge(h)
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "sentinel").write_bytes(b"unchanged")
    if kind == "malformed":
        receipt = h.root / "malformed.json"
        receipt.write_text("{not-json", encoding="utf-8")
    else:
        promote = json.loads(h.promote.read_text(encoding="utf-8"))
        if kind == "digest-substitution":
            promote["source_archive_sha256"] = "e" * 64
        else:
            promote["operation_id"] = "f" * 32
        receipt = h.root / f"{kind}.json"
        receipt.write_text(json.dumps(promote), encoding="utf-8")
    before = _snapshot(h, artifact)
    result = _run_denial_without_receipt(h, receipt, "resume-finalize")
    assert result.returncode == 1
    _assert_denied_without_side_effects(before, _snapshot(h, artifact))


def _weakened_engine(tmp_path):
    source = CLI.read_text(encoding="utf-8")
    start = source.index("def phase_finalize(")
    end = source.index("# ── phase: rollback", start)
    old = '''def phase_finalize(receipt_in_path, inventory_path, inventory_sha_path, db,
                   user, container, probe_spec):
    try:
        promote, _stamp, _quarantine, _staging, operation_id = \\
            _validated_transition_receipt(receipt_in_path, db, user, container,
                                          inventory_path, inventory_sha_path, "finalize")
    except Exception:
        return _phase_finalize_locked(receipt_in_path, inventory_path, inventory_sha_path,
                                      db, user, container, probe_spec, None, False)
    with _OperationExecutionAuthority(operation_id, "finalize", promote) as authority:
        return _phase_finalize_locked(receipt_in_path, inventory_path, inventory_sha_path,
                                      db, user, container, probe_spec, authority, False)


def phase_resume_finalize(receipt_in_path, inventory_path, inventory_sha_path,
                           db, user, container, probe_spec):
    try:
        (promote, _stamp, _quarantine, _staging, operation_id, _state) = \\
            _validated_resume_finalize_receipt(receipt_in_path, db, user, container,
                                               inventory_path, inventory_sha_path)
    except Exception:
        return _phase_finalize_locked(receipt_in_path, inventory_path, inventory_sha_path,
                                      db, user, container, probe_spec, None, True)
    with _OperationExecutionAuthority(operation_id, "resume-finalize", promote) as authority:
        return _phase_finalize_locked(receipt_in_path, inventory_path, inventory_sha_path,
                                      db, user, container, probe_spec, authority, True)


'''
    source = source[:start] + old + source[end:]
    source = source.replace("execution_authority, resume_only=False",
                            "execution_authority=None, resume_only=False")
    source = source.replace("execution_authority):", "execution_authority=None):")
    source = source.replace("\n            execution_authority.activate()\n",
                            "\n            if execution_authority is not None:\n"
                            "                execution_authority.activate()\n")
    source = source.replace("\n            execution_authority.commit()\n",
                            "\n            if execution_authority is not None:\n"
                            "                execution_authority.commit()\n")
    source = source.replace("\n        execution_authority.activate()\n",
                            "\n        if execution_authority is not None:\n"
                            "            execution_authority.activate()\n")
    source = source.replace("\n        execution_authority.commit()\n",
                            "\n        if execution_authority is not None:\n"
                            "            execution_authority.commit()\n")
    weak = tmp_path / "weakened-pg-recovery.py"
    weak.write_text(source, encoding="utf-8")
    return weak


def _weak_runner(weak, root, bridge):
    runner = weak.parent / "weakened-runner.py"
    runner.write_text(
        "import importlib.util, sys\n"
        "spec=importlib.util.spec_from_file_location('weak_pgrec', sys.argv[1])\n"
        "mod=importlib.util.module_from_spec(spec); sys.modules['weak_pgrec']=mod\n"
        "spec.loader.exec_module(mod); mod._bind_test_recovery_root(sys.argv[2])\n"
        "spec=importlib.util.spec_from_file_location('weak_bridge', sys.argv[3])\n"
        "bridge=importlib.util.module_from_spec(spec); sys.modules['weak_bridge']=bridge\n"
        "spec.loader.exec_module(bridge); bridge.install(mod)\n"
        "sys.argv=[sys.argv[1]]+sys.argv[4:]; mod.main()\n", encoding="utf-8")
    return runner


def test_negative_control_unlocked_fallback_enters_mutation_interval(tmp_path):
    h = _prepare(tmp_path)
    _r42_bridge(h)
    weak = _weakened_engine(tmp_path)
    runner = _weak_runner(weak, h.root, h.bridge)
    env = dict(h.env)
    env.update({"R42_PREFLIGHT_RESUME": "1", "R42_PAUSE_PREFLIGHT": "1"})
    contender = subprocess.Popen(
        [sys.executable, str(runner), str(weak), str(h.root), str(h.bridge),
         *_resume_argv(h, h.root / "weak.json")], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        _wait_for_event(h, "initial-resume-validation-denied")
    except AssertionError:
        if contender.poll() is not None:
            stdout, stderr = contender.communicate(timeout=10)
            pytest.fail(f"weakened contender exited before barrier: {stdout!r} {stderr!r}")
        raise
    _arm(h, "after_intent_before_drop")
    holder = _spawn(h, _finalize_argv(h, h.root / "holder.json"), h.root / "holder.json")
    _wait_for(h.signal)
    h.bridge_dir.joinpath("release-preflight").write_text("go", encoding="utf-8")
    observed = False
    deadline = time.time() + 30
    while time.time() < deadline and not observed:
        observed = any(item.get("pid") == contender.pid
                       for item in _mutation_log(h))
        time.sleep(0.01)
    assert holder.poll() is None
    assert observed, "weakened engine did not enter the mutation interval unlocked"
    holder.kill()
    holder.communicate(timeout=10)
    contender.kill()
    contender.communicate(timeout=10)
