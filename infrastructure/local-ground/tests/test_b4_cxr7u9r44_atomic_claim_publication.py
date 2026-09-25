#!/usr/bin/env python3
"""B4-CXR7U9R44 - crash-atomic claim publication, denial-free provisioning,
and attempt-owned execution evidence.

Post-R43 review found three defects the R43 suite never exercised:

  1. the canonical branch selector became VISIBLE before its payload was
     durable (O_CREAT|O_EXCL create, then write), so any death in that window
     left a zero-byte claim: the one-time authority was spent, unreadable, and
     the operation was stranded in PROMOTED with no governed continuation;
  2. entering execution authority CREATED the permanent lock coordinate, so a
     denial - including one carrying an arbitrary 32-hex operation id that was
     never registered - left a durable one-byte file and grew the governed
     transition directory;
  3. a denied fresh retry could ERASE an earlier committed owner's execution
     metadata.

These proofs are real child processes against the real engine. Crash points
are injected ONLY through the existing test bridge (the engine itself has no
crash switch), and every weakened control is an executable engine COPY whose
defect is observed at runtime - never a source-string assertion.
"""
import hashlib
import json
import os
import secrets
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

# The seven publication boundaries R44 must survive. 1-4 are BEFORE the
# canonical name is bound (fresh authority must survive); 5-7 are AFTER
# (exactly one complete, attributable, resumable branch must survive).
PRE_PUBLICATION_BOUNDARIES = [
    "after_claim_temporary_created",
    "during_claim_payload_construction",
    "after_claim_temporary_fsync",
    "before_canonical_claim_publication",
]
POST_PUBLICATION_BOUNDARIES = [
    "after_canonical_claim_publication",
    "before_claim_directory_fsync",
    "after_publication_before_state_advance",
]


# The bridge observes the engine's own primitives. It never decides anything:
# every wrapped call is the real implementation, with one boundary hook around
# the claim publication the R44 law is about.
_R44_PATCH = r'''

_R44_BASE_INSTALL = install
_R44_TMP = {"fd": None, "path": None, "published": False, "fired": set()}


def _r44_once(name):
    if name in _R44_TMP["fired"]:
        return
    _R44_TMP["fired"].add(name)
    _boundary(name)


class _R44ClaimStream:
    """Real stream; the boundary fires on the FIRST payload write, so the
    process dies with a private, still-empty temporary and no canonical name."""

    def __init__(self, inner):
        self._inner = inner

    def write(self, data):
        _r44_once("during_claim_payload_construction")
        return self._inner.write(data)

    def flush(self):
        return self._inner.flush()

    def fileno(self):
        return self._inner.fileno()

    def __enter__(self):
        self._inner.__enter__()
        return self

    def __exit__(self, *exc):
        return self._inner.__exit__(*exc)


def install(mod):
    _R44_BASE_INSTALL(mod)
    base_mkstemp = mod.tempfile.mkstemp
    base_fdopen = mod.os.fdopen
    base_fsync = mod.os.fsync
    base_publish = mod._publish_no_replace
    base_fsync_dir = mod._fsync_dir
    base_record = mod._record_transition

    def mkstemp(*a, **k):
        fd, path = base_mkstemp(*a, **k)
        prefix = k.get("prefix", a[0] if a else "")
        if isinstance(prefix, str) and ".claim." in prefix:
            _R44_TMP["fd"] = fd
            _R44_TMP["path"] = path
            _r44_once("after_claim_temporary_created")
        return fd, path

    def fdopen(fd, *a, **k):
        stream = base_fdopen(fd, *a, **k)
        if _R44_TMP["fd"] is not None and fd == _R44_TMP["fd"]:
            return _R44ClaimStream(stream)
        return stream

    def fsync(fd):
        result = base_fsync(fd)
        if _R44_TMP["fd"] is not None and fd == _R44_TMP["fd"]:
            _r44_once("after_claim_temporary_fsync")
        return result

    def publish(source, destination):
        _r44_once("before_canonical_claim_publication")
        result = base_publish(source, destination)
        _R44_TMP["published"] = True
        _r44_once("after_canonical_claim_publication")
        return result

    def fsync_dir(directory):
        if _R44_TMP["published"]:
            _r44_once("before_claim_directory_fsync")
        return base_fsync_dir(directory)

    def record(operation_id, state, receipt, extra=None):
        if _R44_TMP["published"]:
            _r44_once("after_publication_before_state_advance")
        result = base_record(operation_id, state, receipt, extra=extra)
        if _R44_TMP["published"] and state == "ROLLING_BACK":
            _boundary("after_claim_state_advance")
        return result

    mod.tempfile.mkstemp = mkstemp
    mod.os.fdopen = fdopen
    mod.os.fsync = fsync
    mod._publish_no_replace = publish
    mod._fsync_dir = fsync_dir
    mod._record_transition = record
'''


# The weakened control restores the PRE-R44 primitive exactly (canonical name
# created with O_EXCL, payload written afterwards) and the bridge signals the
# death in the poison window. The invariant MUST fail here.
_R44_POISON_PATCH = r'''

_R44_POISON_BASE_INSTALL = install


def install(mod):
    _R44_POISON_BASE_INSTALL(mod)
    base_open = mod.os.open

    def open_(path, flags, mode=0o777, **kwargs):
        fd = base_open(path, flags, mode, **kwargs)
        if isinstance(path, str) and path.endswith(".claim") and flags & os.O_EXCL:
            _boundary("pre_r44_after_claim_path_reservation")
        return fd

    mod.os.open = open_
'''

_R44_POISON_TRANSFORM = (
    "        _publish_no_replace(tmp, claim_path)",
    "        _pre_r44_publish_claim(claim_path, payload)",
)

_R44_POISON_HELPER = '''

def _pre_r44_publish_claim(claim_path, payload):
    """The pre-R44 publication primitive, verbatim in shape: the canonical
    name becomes visible FIRST and the payload is written afterwards."""
    fd = os.open(claim_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(os.path.dirname(claim_path))
'''


def _wait_for_path(path, timeout=30):
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.is_file():
            return
        time.sleep(0.01)
    raise AssertionError(f"barrier was not reached: {path}")


def _r44_bridge(harness):
    harness.bridge.write_text(BRIDGE_SOURCE + _R44_PATCH, encoding="utf-8")
    _clear(harness)


def _poison_bridge(harness):
    harness.bridge.write_text(BRIDGE_SOURCE + _R44_PATCH + _R44_POISON_PATCH,
                              encoding="utf-8")
    _clear(harness)


def _arm(harness, boundary):
    harness.bridge_dir.joinpath("crash.json").write_text(
        json.dumps({"boundary": boundary}), encoding="utf-8")
    harness.signal.unlink(missing_ok=True)


def _rollback_argv(harness, output):
    return ["--phase", "rollback", "--receipt-in", str(harness.promote),
            "--inventory", str(harness.inventory), "--inventory-sha",
            str(harness.inventory_sha), "--db", "oce_local", "--user",
            "oce_local_admin", "--container", "oce-local-postgresql",
            "--receipt-out", str(output)]


def _finalize_argv(harness, output):
    return ["--phase", "finalize", "--receipt-in", str(harness.promote),
            "--inventory", str(harness.inventory), "--inventory-sha",
            str(harness.inventory_sha), "--db", "oce_local", "--user",
            "oce_local_admin", "--container", "oce-local-postgresql",
            "--receipt-out", str(output)]


def _resume_rollback_argv(harness, output):
    return ["--phase", "resume-rollback", *_rollback_argv(harness, output)[2:]]


def _classify_rollback(harness):
    return subprocess.run(
        [sys.executable, str(CLI), "--classify-rollback", str(harness.promote),
         "--transition-dir", str(harness.transitions)],
        env=harness.env, capture_output=True, text=True, timeout=60)


def _reconcile(harness, output):
    return subprocess.run(
        recovery_cli.cli_argv(
            ["--phase", "reconcile", "--receipt-in", str(harness.promote),
             "--inventory", str(harness.inventory), "--inventory-sha",
             str(harness.inventory_sha), "--db", "oce_local", "--user",
             "oce_local_admin", "--container", "oce-local-postgresql",
             "--receipt-out", str(output)],
            str(harness.root), str(harness.bridge)),
        env=harness.env, capture_output=True, text=True, timeout=60)


def _spawn(harness, argv, engine=None):
    if engine is None:
        command = recovery_cli.cli_argv(argv, str(harness.root),
                                        str(harness.bridge))
    else:
        command = [sys.executable, "-c", recovery_cli._BOOTSTRAP, str(engine),
                   str(harness.root), "--test-bridge", str(harness.bridge)]
        command.extend(map(str, argv))
    return subprocess.Popen(command, env=harness.env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)


def _run(harness, argv):
    return recovery_cli.run_cli(argv, write_root=str(harness.root),
                                bridge=str(harness.bridge),
                                env_extra=_env(harness.tmp), timeout=60)


def _terminate(processes):
    for process in processes:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)


def _opid(harness):
    return json.loads(harness.promote.read_text(encoding="utf-8"))["operation_id"]


def _claim(harness):
    return harness.transitions / f"{_opid(harness)}.claim"


def _coordinate(harness):
    return harness.transitions / f"{_opid(harness)}.execution.lock"


def _metadata(harness):
    return harness.transitions / f"{_opid(harness)}.execution.json"


def _tree(root):
    """Byte-exact census of a directory: every file's relative name, size and
    content digest. A denial that leaves this unchanged created nothing."""
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = (
                path.stat().st_size,
                hashlib.sha256(path.read_bytes()).hexdigest())
    return out


def _claim_temporaries(harness):
    prefix = f".{_opid(harness)}.claim."
    return sorted(p for p in harness.transitions.iterdir()
                  if p.name.startswith(prefix) and p.name.endswith(".tmp"))


def _unregistered_receipt(harness, name):
    """A structurally valid receipt naming an operation that was NEVER
    registered: the R44-02 denial trigger, byte-for-byte."""
    forged = json.loads(harness.promote.read_text(encoding="utf-8"))
    forged["operation_id"] = secrets.token_hex(16)
    path = harness.root / name
    path.write_text(json.dumps(forged), encoding="utf-8")
    return forged, path


# --------------------------------------------------------------------- #
# R44-01 / R44-05 A,B,C,H: the publication crash matrix
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("boundary", PRE_PUBLICATION_BOUNDARIES)
def test_death_before_publication_leaves_fresh_authority(boundary, tmp_path):
    """R44-01: a death before the canonical name is bound must leave NO
    canonical claim and must leave the operation's fresh authority intact."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _arm(h, boundary)
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)

    assert not _claim(h).exists(), "a pre-publication death published a claim"
    assert _claim(h).stat().st_size == 0 if _claim(h).exists() else True
    assert _record(h)["state"] == "PROMOTED"
    # the private temporary may survive; it is never the selector
    assert all(not p.name.endswith(".claim") for p in _claim_temporaries(h))

    result = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert result.returncode == 0, result.stderr
    assert _record(h)["state"] == "ROLLED_BACK"
    claim = json.loads(_claim(h).read_text(encoding="utf-8"))
    assert claim["transition"] == "rollback"
    assert claim["operation_id"] == _opid(h)
    # H: the abandoned temporary is discarded, never adopted
    assert _claim_temporaries(h) == []
    assert len(list(h.transitions.glob("*.claim"))) == 1


@pytest.mark.parametrize("boundary", POST_PUBLICATION_BOUNDARIES)
def test_death_after_publication_leaves_one_resumable_branch(boundary, tmp_path):
    """R44-01: a death after the canonical name is bound must leave exactly
    ONE complete, attributable, resumable branch - never an empty, partial or
    malformed selector."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _arm(h, boundary)
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)

    assert _claim(h).is_file()
    claim = json.loads(_claim(h).read_text(encoding="utf-8"))
    assert claim["format"] == "oce-transition-claim-v1"
    assert claim["operation_id"] == _opid(h)
    assert claim["transition"] == "rollback"
    assert len(claim["receipt_sha256"]) == 64
    assert _record(h)["state"] in ("PROMOTED", "ROLLING_BACK")
    assert len(list(h.transitions.glob("*.claim"))) == 1

    resumed = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert resumed.returncode == 0, resumed.stderr
    receipt = json.loads((h.root / "resumed.json").read_text(encoding="utf-8"))
    assert receipt["exit_status"] == 0
    assert receipt["resumed"] is True
    assert receipt["rollback_succeeded"] is True
    assert receipt["operation_id"] == _opid(h)
    assert _record(h)["state"] == "ROLLED_BACK"
    assert json.loads(_claim(h).read_text(encoding="utf-8")) == claim
    assert len(list(h.transitions.glob("*.claim"))) == 1


def test_no_publication_boundary_can_ever_leave_a_malformed_selector(tmp_path):
    """R44-01/05 E,F,G: sweep all seven boundaries on BOTH branches and prove
    the selector is never empty, partial or malformed at any of them."""
    for boundary in PRE_PUBLICATION_BOUNDARIES + POST_PUBLICATION_BOUNDARIES:
        for phase, argv, resume in (
                ("rollback", _rollback_argv, _resume_rollback_argv),
                ("finalize", _finalize_argv, None)):
            root = tmp_path / f"{phase}-{boundary}"
            root.mkdir()
            h = _prepare(root)
            _r44_bridge(h)
            _arm(h, boundary)
            process = _spawn(h, argv(h, h.root / "crash.json"))
            _kill_at_signal(process, h.signal)
            _clear(h)
            if _claim(h).exists():
                claim = json.loads(_claim(h).read_text(encoding="utf-8"))
                assert claim["transition"] == phase, (boundary, phase, claim)
                assert claim["operation_id"] == _opid(h)
            else:
                assert boundary in PRE_PUBLICATION_BOUNDARIES, (boundary, phase)
            assert _classify_rollback(h).returncode in (0, 4, 5, 6)


# --------------------------------------------------------------------- #
# R44-05 D: two processes, opposite branches, at publication time
# --------------------------------------------------------------------- #

def test_two_processes_selecting_opposite_branches_have_exactly_one_winner(
        tmp_path):
    """A finalize process dies with its claim already published; a real
    rollback process then enters the same mutation interval with the coordinate
    FREE. The durable selector - not the OS lock, and not the spent claim -
    decides, so the rollback can never win a finalize-selected operation."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _arm(h, "after_canonical_claim_publication")
    winner = _spawn(h, _finalize_argv(h, h.root / "finalize.json"))
    try:
        _wait_for_path(h.signal)
        # The finalize branch is durably selected while the executor still
        # holds the mutation interval. Kill it: the OS lock is released, so a
        # real rollback process can now ENTER the mutation interval - the
        # decision it faces is the durable selector, not lock contention.
        winner.kill()
        winner.communicate(timeout=10)
    finally:
        _terminate([winner])
        _clear(h)

    assert json.loads(_claim(h).read_text(encoding="utf-8"))["transition"] \
        == "finalize"
    metadata_before = _metadata(h).read_bytes()

    contender = _run(h, _rollback_argv(h, h.root / "rollback.json"))
    assert contender.returncode == 1, contender.stderr
    # refused in activate(), on the durable selector - not on the spent claim
    assert "already claimed for 'finalize'" in contender.stderr, contender.stderr
    # the refusal is recorded truthfully as evidence, and it claims nothing
    denial = json.loads((h.root / "rollback.json").read_text(encoding="utf-8"))
    assert denial["exit_status"] == 1
    assert "already claimed for 'finalize'" in denial["error"]

    assert len(list(h.transitions.glob("*.claim"))) == 1
    assert json.loads(_claim(h).read_text(encoding="utf-8"))["transition"] \
        == "finalize"
    assert _record(h)["state"] == "PROMOTED"
    assert _metadata(h).read_bytes() == metadata_before
    assert "oce_local" in _dbs(h)

    # The operation is finalize-selected for good: a governed rollback resume
    # cannot become the second winner, and the finalize branch still completes.
    resumed = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert resumed.returncode == 1
    assert "durable rollback claim" in resumed.stderr
    assert len(list(h.transitions.glob("*.claim"))) == 1
    assert _record(h)["state"] == "PROMOTED"


# --------------------------------------------------------------------- #
# R44-02 / R44-05 I,J: denial must not provision a coordinate
# --------------------------------------------------------------------- #

def test_unregistered_operation_id_cannot_create_a_coordinate(tmp_path):
    """R44-02 A: a syntactically valid but UNREGISTERED 32-hex operation id
    must leave the governed transition tree byte-identical."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _forged, path = _unregistered_receipt(h, "unregistered.json")
    before = _tree(h.transitions)
    catalog_before = _dbs(h)

    result = _run(h, ["--phase", "rollback", "--receipt-in", str(path),
                      "--inventory", str(h.inventory), "--inventory-sha",
                      str(h.inventory_sha), "--db", "oce_local", "--user",
                      "oce_local_admin", "--container",
                      "oce-local-postgresql", "--receipt-out",
                      str(h.root / "denied.json")])
    assert result.returncode == 1
    assert not (h.root / "denied.json").exists()
    assert _tree(h.transitions) == before
    assert _dbs(h) == catalog_before


def test_substituted_receipt_for_a_registered_operation_is_byte_identical(
        tmp_path):
    """R44-02 B: the operation IS registered, but the presented receipt is not
    the one bound to its durable record."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    forged = json.loads(h.promote.read_text(encoding="utf-8"))
    forged["source_commit"] = "c" * 40
    path = h.root / "substituted.json"
    path.write_text(json.dumps(forged), encoding="utf-8")
    before = _tree(h.transitions)
    catalog_before = _dbs(h)

    result = _run(h, ["--phase", "rollback", "--receipt-in", str(path),
                      "--inventory", str(h.inventory), "--inventory-sha",
                      str(h.inventory_sha), "--db", "oce_local", "--user",
                      "oce_local_admin", "--container",
                      "oce-local-postgresql", "--receipt-out",
                      str(h.root / "denied.json")])
    assert result.returncode == 1
    assert not (h.root / "denied.json").exists()
    assert _tree(h.transitions) == before
    assert _dbs(h) == catalog_before


def test_malformed_receipt_is_byte_identical(tmp_path):
    """R44-02 C: a receipt that is not even JSON must be refused with zero
    persistent effect."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    path = h.root / "malformed.json"
    path.write_text("{not json", encoding="utf-8")
    before = _tree(h.transitions)
    catalog_before = _dbs(h)

    result = _run(h, ["--phase", "rollback", "--receipt-in", str(path),
                      "--inventory", str(h.inventory), "--inventory-sha",
                      str(h.inventory_sha), "--db", "oce_local", "--user",
                      "oce_local_admin", "--container",
                      "oce-local-postgresql", "--receipt-out",
                      str(h.root / "denied.json")])
    assert result.returncode == 1
    assert _tree(h.transitions) == before
    assert _dbs(h) == catalog_before


def test_many_hostile_operation_ids_cause_no_persistent_growth(tmp_path):
    """R44-02 D: repeated hostile ids must not grow the governed directory."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    before = _tree(h.transitions)
    for index in range(20):
        _forged, path = _unregistered_receipt(h, f"hostile-{index}.json")
        result = _run(h, ["--phase", "rollback", "--receipt-in", str(path),
                          "--inventory", str(h.inventory), "--inventory-sha",
                          str(h.inventory_sha), "--db", "oce_local", "--user",
                          "oce_local_admin", "--container",
                          "oce-local-postgresql", "--receipt-out",
                          str(h.root / f"denied-{index}.json")])
        assert result.returncode == 1, result.stderr
    after = _tree(h.transitions)
    assert set(after) - set(before) <= {f"hostile-{i}.json"
                                        for i in range(20)} - set(before)
    assert not list(h.transitions.glob("*.execution.lock")) or \
        len(list(h.transitions.glob("*.execution.lock"))) == 1
    # the only coordinate in the governed tree is the promoted operation's own
    assert sorted(p.name for p in h.transitions.glob("*.execution.lock")) == \
        [f"{_opid(h)}.execution.lock"]


def test_successful_promotion_provisions_exactly_one_coordinate(tmp_path):
    """R44-02 E: the coordinate is provisioned by operation INITIALIZATION,
    not by a later entry, and it is provisioned exactly once."""
    h = _prepare(tmp_path)
    coordinate = _coordinate(h)
    assert coordinate.is_file()
    assert coordinate.stat().st_size == 1
    assert len(list(h.transitions.glob("*.execution.lock"))) == 1
    assert _record(h)["execution_coordinate"] == "provisioned"

    result = _run(h, _rollback_argv(h, h.root / "once.json"))
    assert result.returncode == 0, result.stderr
    assert len(list(h.transitions.glob("*.execution.lock"))) == 1
    assert _record(h)["state"] == "ROLLED_BACK"


# --------------------------------------------------------------------- #
# R44-05 M,N,O: coordinate validation
# --------------------------------------------------------------------- #

def _broken_coordinate_case(tmp_path, name, build):
    h = _prepare(tmp_path)
    _r44_bridge(h)
    coordinate = _coordinate(h)
    coordinate.unlink()
    build(coordinate)
    before = _tree(h.transitions)
    catalog_before = _dbs(h)
    result = _run(h, _rollback_argv(h, h.root / "denied.json"))
    assert result.returncode == 1
    assert not _claim(h).exists()
    assert _record(h)["state"] == "PROMOTED"
    assert _dbs(h) == catalog_before
    assert _tree(h.transitions) == before
    return h


def test_symlink_coordinate_is_refused(tmp_path):
    """R44-05 M: a symlink at the coordinate name is never followed."""
    target = tmp_path / "outside-coordinate"

    def build(coordinate):
        target.write_bytes(b"\0")
        try:
            os.symlink(target, coordinate)
        except (OSError, NotImplementedError) as e:
            pytest.skip(f"symlink creation is unavailable on this platform: {e}")

    _broken_coordinate_case(tmp_path, "symlink", build)


def test_non_regular_coordinate_is_refused(tmp_path):
    """R44-05 N: a directory at the coordinate name is refused, not locked."""
    _broken_coordinate_case(
        tmp_path, "directory", lambda coordinate: coordinate.mkdir())


def test_redirected_coordinate_is_refused_by_the_real_engine(tmp_path):
    """R44-05 O: if the coordinate PATH is swapped for another inode between
    the open and its validation, the real engine refuses rather than locking
    a name that no longer names its inode."""
    h = _prepare(tmp_path)
    h.bridge.write_text(BRIDGE_SOURCE + _R44_PATCH + r'''

_R44_REDIRECT_BASE_INSTALL = install


def install(mod):
    _R44_REDIRECT_BASE_INSTALL(mod)
    base_open = mod.os.open

    def open_(path, flags, mode=0o777, **kwargs):
        fd = base_open(path, flags, mode, **kwargs)
        if isinstance(path, str) and path.endswith(".execution.lock") \
                and not (flags & os.O_EXCL):
            replacement = path + ".redirected"
            fd2 = base_open(replacement, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd2)
            os.replace(replacement, path)
        return fd

    mod.os.open = open_
''', encoding="utf-8")
    _clear(h)
    result = _run(h, _rollback_argv(h, h.root / "redirected.json"))
    assert result.returncode == 1
    assert not _claim(h).exists()
    assert _record(h)["state"] == "PROMOTED"


# --------------------------------------------------------------------- #
# R44-03 / R44-05 K,L: attempt-owned execution metadata
# --------------------------------------------------------------------- #

def _crash_after_publication(h):
    """A rollback process that durably published its claim and its execution
    metadata, then died before the transition record advanced."""
    _r44_bridge(h)
    _arm(h, "after_canonical_claim_publication")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
    _kill_at_signal(process, h.signal)
    _clear(h)
    assert _claim(h).is_file()
    assert _metadata(h).is_file()
    return _metadata(h).read_bytes()


def test_denied_fresh_retry_preserves_committed_metadata(tmp_path):
    """R44-03 K: with a rollback selector durable, a FRESH finalize retry is
    refused in activate() and must leave the committed evidence byte-identical.
    A same-branch fresh retry that is refused by the spent claim must RESTORE
    the prior owner's bytes, never erase them."""
    h = _prepare(tmp_path)
    committed = _crash_after_publication(h)

    cross_branch = _run(h, _finalize_argv(h, h.root / "cross.json"))
    assert cross_branch.returncode == 1
    assert _metadata(h).read_bytes() == committed
    assert _record(h)["state"] == "PROMOTED"

    same_branch = _run(h, _rollback_argv(h, h.root / "same.json"))
    assert same_branch.returncode == 1
    assert "already claimed" in same_branch.stderr
    assert _metadata(h).read_bytes() == committed
    assert json.loads(_claim(h).read_text(encoding="utf-8"))["transition"] \
        == "rollback"
    assert _record(h)["state"] == "PROMOTED"


def test_correct_resume_after_committed_metadata_is_attributable(tmp_path):
    """R44-03 L: the governed resume completes the selected branch, and the
    evidence it publishes names the branch, the durable selector and its own
    attempt token."""
    h = _prepare(tmp_path)
    before = _crash_after_publication(h)

    resumed = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert resumed.returncode == 0, resumed.stderr
    assert _record(h)["state"] == "ROLLED_BACK"

    metadata = json.loads(_metadata(h).read_text(encoding="utf-8"))
    assert metadata["format"] == "oce-operation-execution-authority-v3"
    assert metadata["operation_id"] == _opid(h)
    assert metadata["branch"] == "rollback"
    assert metadata["durable_selected_transition"] == "rollback"
    # resume activates BEFORE the state advance, so the evidence truthfully
    # records the PROMOTED it was admitted against, not a state it invented.
    assert metadata["durable_state"] == "PROMOTED"
    assert metadata["receipt_sha256"] == hashlib.sha256(
        (json.dumps(json.loads(h.promote.read_text(encoding="utf-8")),
                    sort_keys=True, separators=(",", ":"))
         ).encode("utf-8")).hexdigest()
    assert metadata["attempt_token"] == metadata["token"]
    assert metadata["predecessor_token"] == \
        json.loads(before)["attempt_token"]
    assert _metadata(h).read_bytes() != before


# --------------------------------------------------------------------- #
# R44-04: the one branch-selection law
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("stage,state,expected", [
    ("fresh", "PROMOTED", 0),
    ("in_flight", "ROLLING_BACK", 6),
    ("terminal", "ROLLED_BACK", 6),
])
def test_shell_classifier_derives_its_verdict_from_the_durable_selector(
        stage, state, expected, tmp_path):
    """The classifier reads the SAME durable selector/state the engine writes;
    it never invents authority. Fresh rollback is 0; a spent rollback branch is
    6 whether or not it has already converged."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    if stage == "fresh":
        pass
    elif stage == "in_flight":
        _arm(h, "after_claim_state_advance")
        process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
        _kill_at_signal(process, h.signal)
        _clear(h)
    else:
        result = _run(h, _rollback_argv(h, h.root / "run.json"))
        assert result.returncode == 0, result.stderr
    record = _record(h)
    assert record["state"] == state
    assert _classify_rollback(h).returncode == expected, record["state"]


def test_malformed_selector_is_a_deterministic_fail_closed_verdict(tmp_path):
    """R44-04: a canonical claim NAME that is not a complete engine-published
    claim is never reported as fresh authority. It is named and blocked."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _claim(h).write_bytes(b"")
    assert _classify_rollback(h).returncode == 4
    assert _classify_state(h).returncode == 4

    reconciled = _reconcile(h, h.root / "reconcile.json")
    assert reconciled.returncode == 1
    verdict = json.loads((h.root / "reconcile.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "unreconciled"
    assert verdict["claim_state"] == "malformed"
    assert "fail-closed" in verdict["error"]

    fresh = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert fresh.returncode == 1
    resumed = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert resumed.returncode == 1
    assert _record(h)["state"] == "PROMOTED"


def _classify_state(harness):
    return subprocess.run(
        [sys.executable, str(CLI), "--classify-state",
         str(harness.transitions / f"{_opid(harness)}.json")],
        env=harness.env, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("poison", [b"", b'{"format": "oce-transition-claim-v1"',
                                   b"\x00\x01\x02not json at all"])
def test_empty_partial_and_malformed_selectors_all_fail_closed(poison, tmp_path):
    """R44-05 E,F,G: the three selector corruption shapes, each of which used
    to be either silently treated as fresh or silently repaired."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _claim(h).write_bytes(poison)
    assert _classify_rollback(h).returncode == 4
    fresh = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert fresh.returncode == 1
    assert _record(h)["state"] == "PROMOTED"
    assert len(list(h.transitions.glob("*.claim"))) == 1


# --------------------------------------------------------------------- #
# R44-05 P,Q: platform lock and inode identity
# --------------------------------------------------------------------- #

def test_coordinate_identity_is_stable_across_the_whole_lifecycle(tmp_path):
    """R44-05 Q/P: one coordinate inode, from promotion through the selected
    branch to its terminal state, with no replacement in between."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    coordinate = _coordinate(h)
    inode = coordinate.stat().st_ino
    if inode:  # POSIX exposes a real inode; Windows has none to compare
        assert _run(h, _rollback_argv(h, h.root / "run.json")).returncode == 0
        assert coordinate.stat().st_ino == inode
        assert _record(h)["state"] == "ROLLED_BACK"
        assert not Path(str(coordinate) + ".replacement").exists()
        assert not Path(str(coordinate) + ".redirected").exists()


def test_a_concurrent_contender_is_refused_while_the_coordinate_is_held(
        tmp_path):
    """R44-05 P: the OS lock owns mutual exclusion only; a contender that
    cannot have the mutation interval is refused and writes no evidence."""
    h = _prepare(tmp_path)
    _r44_bridge(h)
    _arm(h, "after_canonical_claim_publication")
    holder = _spawn(h, _rollback_argv(h, h.root / "holder.json"))
    processes = [holder]
    try:
        _wait_for_path(h.signal)
        contender = _spawn(h, _rollback_argv(h, h.root / "contender.json"))
        processes.append(contender)
        out, err = contender.communicate(timeout=60)
        assert contender.returncode == 1, (out, err)
        assert "execution authority" in err, err
        assert not (h.root / "contender.json").exists()
    finally:
        _terminate(processes)
    _clear(h)
    assert len(list(h.transitions.glob("*.claim"))) == 1


# --------------------------------------------------------------------- #
# executable weakened controls
# --------------------------------------------------------------------- #

def _poison_engine(tmp_path):
    source = CLI.read_text(encoding="utf-8")
    old, new = _R44_POISON_TRANSFORM
    assert old in source, "the R44 publication primitive changed shape"
    source = source.replace(old, new) + _R44_POISON_HELPER
    path = tmp_path / "poison-pg-recovery.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_weakened_pre_r44_publication_creates_a_zero_byte_poison_claim(tmp_path):
    """The executable weakened control. Restoring the O_EXCL-create-then-write
    primitive and dying in that window MUST reproduce the R44-01 defect: a
    durably visible EMPTY claim that spends the one-time authority, refuses
    fresh authority, rejects resume, and strands PROMOTED forever. The
    strengthened engine must NOT exhibit any of that."""
    h = _prepare(tmp_path)
    _poison_bridge(h)
    weak = _poison_engine(tmp_path)
    _arm(h, "pre_r44_after_claim_path_reservation")
    process = _spawn(h, _rollback_argv(h, h.root / "crash.json"), engine=weak)
    _kill_at_signal(process, h.signal)
    _clear(h)

    # ---- the defect, observed at runtime ----
    assert _claim(h).is_file(), "the weakened control published no poison claim"
    assert _claim(h).stat().st_size == 0
    assert _record(h)["state"] == "PROMOTED"
    fresh = _run(h, _rollback_argv(h, h.root / "fresh.json"))
    assert fresh.returncode == 1, "the poison claim reopened fresh authority"
    assert "already claimed" in fresh.stderr
    resumed = _run(h, _resume_rollback_argv(h, h.root / "resumed.json"))
    assert resumed.returncode == 1, "the poison claim admitted resume"
    assert _record(h)["state"] == "PROMOTED"
    assert "oce_local" in _dbs(h)
    # stranded: no governed continuation exists for this operation any more
    assert _classify_rollback(h).returncode == 4


def test_strengthened_publication_never_creates_a_poison_claim(tmp_path):
    """The same sweep against the REAL engine: the same seven boundaries, and
    not one of them leaves an empty, partial or malformed canonical claim."""
    for boundary in PRE_PUBLICATION_BOUNDARIES + POST_PUBLICATION_BOUNDARIES:
        root = tmp_path / boundary
        root.mkdir()
        h = _prepare(root)
        _r44_bridge(h)
        _arm(h, boundary)
        process = _spawn(h, _rollback_argv(h, h.root / "crash.json"))
        _kill_at_signal(process, h.signal)
        _clear(h)
        if _claim(h).exists():
            assert _claim(h).stat().st_size > 0, boundary
            claim = json.loads(_claim(h).read_text(encoding="utf-8"))
            assert claim["format"] == "oce-transition-claim-v1", boundary
            assert claim["transition"] == "rollback", boundary
        assert _classify_rollback(h).returncode != 4, boundary


# --------------------------------------------------------------------- #
# authoritative runner wiring
# --------------------------------------------------------------------- #

# Every platform-gated node id in this module, with the reason it is gated.
# The runner proof fails if a proof is gated without being declared here, so
# no Linux-only proof can be silently skipped in authoritative Linux CI.
PLATFORM_GATED = {
    "test_symlink_coordinate_is_refused": "symlink creation may be "
                                          "unprivileged-unavailable on Windows",
    "test_coordinate_identity_is_stable_across_the_whole_lifecycle":
        "POSIX inode identity only; Windows exposes no comparable inode",
}


def test_authoritative_runner_selects_r44_with_unique_node_ids(tmp_path):
    runner = SCRIPTS / "run-validation.sh"
    source = runner.read_text(encoding="utf-8")
    assert "R44_ATOMIC_CLAIM_PUBLICATION_TEST=" in source
    assert "test_b4_cxr7u9r44_atomic_claim_publication.py" in source
    # R43 and every earlier mandatory suite must remain selected
    for retained in ("R43_LOCK_ROLLBACK_RESUME_TEST",
                     "R42_EXECUTION_AUTHORITY_RACE_TEST",
                     "R41R4_COMPLETION_TEST", "CRASH_COHERENCE_TEST",
                     "NEGATIVE_CONTROL_TEST", "TRANSITION_AUTHORITY_TEST"):
        assert retained in source, retained

    env = dict(os.environ)
    env.pop("OCE_EVIDENCE_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         str(Path(__file__))],
        cwd=str(TESTS.parent), env=env, capture_output=True, text=True,
        timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    nodeids = [line.strip() for line in result.stdout.splitlines()
               if "::" in line and Path(__file__).name in line]
    assert nodeids
    assert len(nodeids) == len(set(nodeids)), "duplicate full node ids"
    assert all(Path(__file__).name + "::" in nodeid for nodeid in nodeids)

    # no proof is hidden: every skip this module can produce is declared
    module = Path(__file__).read_text(encoding="utf-8")
    for name in PLATFORM_GATED:
        assert f"def {name}(" in module, name
    assert len(PLATFORM_GATED) <= 2


def test_r44_module_declares_every_platform_gate_it_uses():
    """A new skipif in this module must be declared, so a Linux-only proof can
    never disappear from authoritative Linux CI unnoticed."""
    module = Path(__file__).read_text(encoding="utf-8")
    gated = module.count("pytest.skip(")
    assert gated <= len(PLATFORM_GATED), (
        "this module gained an undeclared platform gate")
