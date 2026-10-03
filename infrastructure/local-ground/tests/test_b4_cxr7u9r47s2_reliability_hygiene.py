#!/usr/bin/env python3
"""B4-CXR7U9R47S2 - the small, provable Reliability findings in the engine.

Sonar's Reliability rating on new code is C. Five of its findings sit in
`pg-recovery.py` and every one of them is a STRUCTURAL defect rather than a
design disagreement, so each is repaired by removing the shape and keeping the
behaviour:

  * `_read_admitted_claim` caught `(UnicodeDecodeError, ValueError)`.
    `UnicodeDecodeError` IS a subclass of `ValueError`, so the second name
    never added a case; the handler claimed a breadth it did not have.
  * `_validated_resume_finalize_receipt` had a branch whose whole body was
    `pass` (`if state == PROMOTED: pass`). Stating the complement removes the
    empty branch and moves no condition.
  * `_OperationExecutionAuthority.__exit__` returned `False` from two places,
    which is what "this method always returns the same value" reports. A lock
    release never suppresses the exception unwinding through it, so the release
    is now guarded and the single return states that once, visibly.
  * The refusal message "refusing recovery target: " was concatenated at five
    sites; a wording change had five places to miss.
  * `_execute_rollback_by_catalog_state` took a `staging` parameter it never
    read, and its caller passed a live local to it.

The proofs here are mostly structural, because the mechanisms are structural.
Where behaviour is touched at all the proof is behavioural: the rollback
dispatch table is exercised state by state, because dropping that parameter
must not change which recovery action any catalog state selects.
"""
import ast
import os

import pytest

from recovery_cli import CLI, load_engine

pgrec = load_engine()
ENGINE = CLI.read_text(encoding="utf-8")
TREE = ast.parse(ENGINE)


def _fn(name):
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("no function %r in the engine" % name)


def _bare_lock():
    """An authority instance with only the attributes __exit__ touches.

    Deliberately not built through the constructor: the point of these proofs
    is the RELEASE path, not the governed provisioning that would need a
    receipt-bound operation to have been admitted first.
    """
    lock = pgrec._OperationExecutionAuthority.__new__(
        pgrec._OperationExecutionAuthority)
    lock.fd = None
    lock.activated = False
    lock.metadata_committed = True
    return lock


# --------------------------------------------------------------------- #
# 1. no exception class that is already covered by another in the same tuple
# --------------------------------------------------------------------- #

REDUNDANT = {frozenset(("UnicodeDecodeError", "ValueError")),
             frozenset(("JSONDecodeError", "ValueError")),
             frozenset(("TimeoutError", "OSError")),
             frozenset(("FileNotFoundError", "OSError")),
             frozenset(("ConnectionError", "OSError")),
             frozenset(("PermissionError", "OSError")),
             frozenset(("FileExistsError", "OSError"))}


def test_no_except_tuple_names_a_class_its_own_base_class():
    """The defect class, proved module-wide so it cannot recur elsewhere."""
    offenders = []
    for node in ast.walk(TREE):
        if not isinstance(node, ast.ExceptHandler) or node.type is None:
            continue
        parts = (node.type.elts if isinstance(node.type, ast.Tuple)
                 else [node.type])
        names = {p.id for p in parts if isinstance(p, ast.Name)}
        for pair in REDUNDANT:
            if pair <= names:
                offenders.append((node.lineno, sorted(names)))
    assert not offenders, (
        "these handlers name a class and its own base; the base already "
        "catches it: %r" % (offenders,))


def test_the_selector_reader_still_refuses_a_non_json_claim(tmp_path):
    """Behaviour, not shape: an unparseable claim is refused, never parsed."""
    opid = "b" * 32
    claim = tmp_path / (opid + ".claim")
    claim.write_bytes(b"this is not json")
    fd = os.open(str(claim), os.O_RDONLY)
    try:
        with pytest.raises(pgrec._ExecutionAuthorityConflict):
            pgrec._read_admitted_claim(opid, fd)
    finally:
        os.close(fd)


def test_the_selector_reader_still_parses_a_valid_claim(tmp_path):
    """Positive control: the repair narrowed no behaviour at all."""
    import json

    opid = "c" * 32
    claim = tmp_path / (opid + ".claim")
    claim.write_bytes(json.dumps({"format": "x", "operation_id": opid}).encode())
    fd = os.open(str(claim), os.O_RDONLY)
    try:
        stat, doc = pgrec._read_admitted_claim(opid, fd)
        assert doc["operation_id"] == opid
        assert stat.st_size == claim.stat().st_size
    finally:
        os.close(fd)


# --------------------------------------------------------------------- #
# 2. no branch whose entire body is `pass`
# --------------------------------------------------------------------- #

def test_no_if_branch_is_only_pass():
    offenders = []
    for node in ast.walk(TREE):
        if isinstance(node, ast.If):
            for field in ("body", "orelse"):
                block = getattr(node, field)
                if len(block) == 1 and isinstance(block[0], ast.Pass):
                    offenders.append((node.lineno, field))
    assert not offenders, (
        "a branch whose whole body is `pass` says nothing and hides the "
        "condition that matters: %r" % (offenders,))


def test_the_resume_authority_still_states_its_exemption_as_a_complement():
    """The PROMOTED exemption is still a single readable condition.

    The behavioural coverage of the resume-finalize law already lives in the
    R40R2 / R41R2 suites that drive the real engine; what this proof adds is
    that the exemption cannot silently regrow a branch that decides nothing.
    """
    fn = _fn("_validated_resume_finalize_receipt")
    prose = ast.unparse(fn)
    assert "if state != TRANSITION_STATE_PROMOTED" in prose, (
        "the PROMOTED exemption must be expressed as the complement, so the "
        "branch that has work to do is the visible one")
    assert "pass" not in [n for n in prose.split()], prose


# --------------------------------------------------------------------- #
# 3. the lock release returns once, visibly
# --------------------------------------------------------------------- #

def test_the_execution_authority_exit_has_exactly_one_return_statement():
    fn = _fn("__exit__")
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    assert len(returns) == 1, (
        "__exit__ returns from %d places; a lock release must state its "
        "non-suppression once, visibly" % len(returns))
    value = returns[0].value
    assert isinstance(value, ast.Constant) and value.value is False


def test_the_release_still_closes_the_descriptor_and_returns_false(tmp_path):
    lock = _bare_lock()
    assert lock.__exit__(None, None, None) is False, (
        "releasing a lock that was never acquired is a no-op, not a failure")

    # The release path unlocks before it closes, so the byte range has to be
    # genuinely locked first -- on this host's own primitive, whichever it is.
    path = tmp_path / "lock"
    path.write_bytes(b"\0")
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    if os.name == "nt":
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)

    lock = _bare_lock()
    lock.fd = fd
    assert lock.__exit__(None, None, None) is False
    assert lock.fd is None, "the descriptor handle must be cleared"
    with pytest.raises(OSError):
        os.fstat(fd)


# --------------------------------------------------------------------- #
# 4. one refusal message, one spelling
# --------------------------------------------------------------------- #

def test_the_refusal_message_is_defined_once_and_used_not_retyped():
    definitions = [n for n in TREE.body
                   if isinstance(n, ast.Assign)
                   and any(getattr(t, "id", "") == "_REFUSING_RECOVERY_TARGET"
                           for t in n.targets)]
    assert len(definitions) == 1, (
        "the refusal message must be a single named constant")

    literal = "refusing recovery target: "
    sites = []
    for node in ast.walk(TREE):
        if isinstance(node, ast.Constant) and node.value == literal:
            sites.append(node.lineno)
    assert len(sites) == 1, (
        "the message literal appears %d times (line(s) %r); every other use "
        "must name the constant" % (len(sites), sites))


def test_every_refusal_site_still_reports_the_same_words():
    receipt = {"phases": []}
    pgrec._blocked(receipt, pgrec._REFUSING_RECOVERY_TARGET + "x; y")
    assert receipt["error"] == "refusing recovery target: x; y"
    assert receipt["exit_status"] == 1
    assert receipt["finished_at"]


# --------------------------------------------------------------------- #
# 5. the rollback decision table: same states, same actions
# --------------------------------------------------------------------- #

def test_no_module_function_declares_an_unused_parameter():
    """The dropped-parameter defect class, proved module-wide.

    Only module-level functions are in scope: a context manager's `__exit__`
    signature is fixed by the protocol, and a method may ignore a parameter
    its callers must still pass.
    """
    offenders = []
    for fn in TREE.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        used = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        used |= {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        for arg in fn.args.args:
            if arg.arg in ("self", "cls"):
                continue
            if arg.arg not in used:
                offenders.append((fn.name, arg.arg))
    assert not offenders, (
        "a parameter nobody reads is a caller promise the body does not "
        "keep: %r" % (offenders,))


def _stub_rollback(monkeypatch, present, actions):
    """Minimal catalog surface: `present` names the databases that exist."""
    monkeypatch.setattr(pgrec, "_catalog_names", lambda c, u: set(present))
    monkeypatch.setattr(
        pgrec, "_verify_db",
        lambda *a, **k: (actions.append("verify_canonical"),
                         (True, [], {}, {}))[1])
    monkeypatch.setattr(
        pgrec, "_verify_against_floor",
        lambda *a, **k: (actions.append("verify_floor"), (True, [], {}))[1])
    monkeypatch.setattr(
        pgrec, "rollback_recovery",
        lambda *a, **k: (actions.append("rollback"), (True, [], {}))[1])


CONTAINER, USER, DB, QUARANTINE, STAGING = (
    "oce-pg", "oce", "app", "app_orig", "app_staging_9f2c")


@pytest.mark.parametrize("present,expected", [
    (["app", "app_orig"], "before_mutation"),
    (["app_orig"], "canonical_removed"),
    (["app"], "quarantine_renamed"),
    (["app_orig", "unrelated"], "canonical_removed"),
    ([], "unreconciled"),
    (["app", "app_orig", "app_staging_9f2c"], "unreconciled"),
])
def test_the_catalog_state_classification_is_unchanged(present, expected,
                                                       monkeypatch):
    actions = []
    _stub_rollback(monkeypatch, present, actions)
    assert pgrec._rollback_catalog_state(
        CONTAINER, USER, DB, QUARANTINE, STAGING) == expected


@pytest.mark.parametrize("state,expect", [
    ("before_mutation", ["verify_canonical", "rollback"]),
    ("canonical_removed", ["rollback"]),
    ("quarantine_renamed", ["verify_floor"]),
])
def test_the_dispatch_table_still_selects_the_same_action(state, expect,
                                                         monkeypatch):
    actions = []
    _stub_rollback(monkeypatch, ["app", "app_orig"], actions)
    pgrec._execute_rollback_by_catalog_state(
        state, CONTAINER, USER, DB, QUARANTINE, {}, {}, {})
    assert actions == expect, (
        "%s selected %r; the rollback decision table must not move" % (state, actions))


def test_an_unreconciled_catalog_state_is_still_refused(monkeypatch):
    actions = []
    _stub_rollback(monkeypatch, ["app", "app_orig"], actions)
    with pytest.raises(RuntimeError, match="unreconciled"):
        pgrec._execute_rollback_by_catalog_state(
            "unreconciled", CONTAINER, USER, DB, QUARANTINE, {}, {}, {})
    assert actions == [], "a refused state must take no action"


def test_the_dispatch_table_caller_passes_exactly_the_declared_parameters():
    """A signature change is only safe if the call site moved with it."""
    declared = [a.arg for a in _fn("_execute_rollback_by_catalog_state").args.args]
    assert "staging" not in declared, declared
    outer = [a.arg for a in _fn("_execute_rollback_verdict").args.args]
    assert "staging" not in outer, outer
    calls = [n for n in ast.walk(TREE)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name)
             and n.func.id == "_execute_rollback_by_catalog_state"]
    assert calls, "the dispatch table must still have a caller"
    for call in calls:
        assert len(call.args) == len(declared), (
            "call passes %d arguments, the function declares %d"
            % (len(call.args), len(declared)))
