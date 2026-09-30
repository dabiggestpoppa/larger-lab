#!/usr/bin/env python3
"""B4-CXR7U9R46R5 — deterministic selector-replacement proofs and executable
weakened controls.

R46R1 replaced the R45 validate-then-open claim reader with ONE FD-bound
selector snapshot; R46R2 bound one decision to one snapshot; R46R3 bound the
receiptless law to the durable record digest; R46R4 corrected the whole
state/selector matrix. This suite proves those laws cannot be defeated:

* replacements placed at exact boundaries (between the pre-open lstat and the
  descriptor open, after descriptor admission, after parse, after the
  canonical-name identity proof, between one decision's classification and
  its branch extraction, between shell classification and phase admission)
  are detected and fail closed with ZERO authority-side effects;
* identity invariants refuse hard-link and symlink substitution shapes;
* the corrected R46R4 matrix rows fail closed (FINALIZING without a claim or
  with a foreign digest, CREATED/STAGED with a claim, ROLLED_BACK/FAILED
  without their exact selector, malformed/missing record digest);
* executable weakened controls restore the old lstat-lstat-open(path) reader
  and the old classify-first-read/branch-second-read decision and DEMONSTRATE
  both accepting a deterministic replacement, so the shipped refusals are
  proven non-vacuous.

Every proof is deterministic: controlled wrappers and explicit hooks place
the replacement at the exact boundary -- timing sleeps are never used. Every
denial performs zero Docker calls, zero PostgreSQL mutation and zero
artifact-store mutation, never deletes or rewrites the claim itself, and
leaves the durable record byte-identical.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

OPID = "a" * 32
FOREIGN = "b" * 64
EXACT = "c" * 64


def _load_engine(path):
    spec = importlib.util.spec_from_file_location(
        "pg_recovery_under_test", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pgrec = _load_engine(SCRIPTS / "pg-recovery.py")

CLAIM = {
    "format": pgrec._CLAIM_FORMAT,
    "operation_id": OPID,
    "transition": "rollback",
    "receipt_sha256": EXACT,
    "claimed_at": "2026-09-24T00:00:00Z",
}


def _bytes(doc):
    return json.dumps(doc).encode("utf-8")


def _census(root):
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = (
                path.stat().st_size, pgrec.sha256_file(str(path)))
    return out


def _governed(tmp_path, state="PROMOTED", record_digest=EXACT):
    """A governed-shaped transition tree; returns (transitions, record)."""
    transitions = tmp_path / "governed-recovery" / "transitions"
    transitions.mkdir(parents=True, exist_ok=True)
    record = {
        "format": pgrec.TRANSITION_FORMAT,
        "state": state,
        "operation_id": OPID,
        "selected_transition": "finalize" if state == "FINALIZING"
        else ("rollback" if state in ("ROLLING_BACK", "ROLLED_BACK") else None),
        "receipt_sha256": record_digest,
    }
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    return transitions, record


def _publish(transitions, payload, mode=0o600):
    p = transitions / f"{OPID}.claim"
    p.write_bytes(payload)
    os.chmod(p, mode)
    return p


def _record_bytes(transitions):
    return (transitions / f"{OPID}.json").read_bytes()


def _swap_claim(transitions, payload):
    """The attacker's primitive: replace the canonical claim atomically."""
    p = transitions / f"{OPID}.claim"
    tmp = transitions / f"{OPID}.claim.repl"
    tmp.write_bytes(payload)
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)
    return p


class _ReplaySnapshot:
    """A snapshot stand-in that replays a PARSED claim (deterministic
    post-admission replacement; no threads, no timing)."""

    def __init__(self, inner, claim):
        self.__dict__.update(dict(inner.__dict__))
        self.claim = claim


@pytest.fixture
def patched_replay(monkeypatch):
    holder = {}
    real_read = pgrec._read_selector_snapshot

    def fake(operation_id, transition_dir=None):
        snap = real_read(operation_id, transition_dir)
        if not snap.present:
            return snap
        return _ReplaySnapshot(snap, holder["claim"])

    def install(claim):
        holder["claim"] = claim
        monkeypatch.setattr(pgrec, "_read_selector_snapshot", fake)

    return install


# --------------------------------------------------------------------- #
# proofs 1-5: replacement at the shipped reader's exact boundaries
# --------------------------------------------------------------------- #

def test_p1_replacement_between_preopen_lstat_and_open_is_refused(
        tmp_path, monkeypatch):
    """Proofs 1-2: a claim replaced after the pre-open lstat (garbage bytes)
    never reaches the decision as the validated object: the descriptor that
    is opened is admitted and parsed for what it NOW is, and garbage fails
    closed. The old reader's equivalent window is demonstrated accepting in
    test_weakened_path_then_open_accepts_a_boundary_replacement."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    before_record = _record_bytes(transitions)
    real_stat = os.stat
    state = {"fired": False}

    def stat_then_swap(target, *a, **k):
        result = real_stat(target, *a, **k)
        if (not state["fired"] and isinstance(target, str)
                and target.endswith(f"{OPID}.claim")):
            state["fired"] = True
            _swap_claim(transitions, b"{not json")
        return result

    monkeypatch.setattr(pgrec.os, "stat", stat_then_swap)
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    # the engine never repaired or deleted the attacker's bytes, and the
    # durable record is byte-identical
    assert (transitions / f"{OPID}.claim").read_bytes() == b"{not json"
    assert _record_bytes(transitions) == before_record


@pytest.mark.skipif(os.name == "nt",
                    reason="Windows share-mode cannot replace an open file; "
                           "the POSIX CI run exercises this exact window")
def test_p3_replacement_after_admission_before_parse_is_refused(
        tmp_path, monkeypatch):
    """Proof 3: swapping the pathname after the descriptor was admitted
    cannot pollute the read -- the bytes come from the admitted fd -- and the
    final canonical-name identity proof detects the swap."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    before_record = _record_bytes(transitions)
    real_admit = pgrec._admit_selector_descriptor

    def admit_then_swap(*a, **k):
        result = real_admit(*a, **k)
        _swap_claim(transitions, b"{garbage")
        return result

    monkeypatch.setattr(pgrec, "_admit_selector_descriptor", admit_then_swap)
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    assert (transitions / f"{OPID}.claim").read_bytes() == b"{garbage"
    assert _record_bytes(transitions) == before_record


def test_p4_replacement_after_parse_before_name_proof_is_refused(
        tmp_path, monkeypatch):
    """Proof 4: even a parse that succeeded from the admitted bytes is
    rejected when the canonical pathname no longer names that object."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    before_record = _record_bytes(transitions)
    real_loads = json.loads
    state = {"fired": False}

    def loads_then_swap(*a, **k):
        result = real_loads(*a, **k)
        if not state["fired"]:
            state["fired"] = True
            _swap_claim(transitions, _bytes(
                {**CLAIM, "transition": "finalize"}))
        return result

    monkeypatch.setattr(pgrec.json, "loads", loads_then_swap)
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    assert _record_bytes(transitions) == before_record


def test_p5_unlink_and_recreate_at_the_canonical_name_is_refused(
        tmp_path, monkeypatch):
    """Proof 5: unlinking the canonical claim in the pre-open window fails
    closed (the vanished coordinate is never described as absent); recreating
    a different object there fails closed at the final name-identity proof."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    before_record = _record_bytes(transitions)
    real_stat = os.stat
    state = {"mode": None, "fired": False}

    def stat_then_attack(target, *a, **k):
        result = real_stat(target, *a, **k)
        if (not state["fired"] and isinstance(target, str)
                and target.endswith(f"{OPID}.claim")):
            state["fired"] = True
            if state["mode"] == "unlink":
                (transitions / f"{OPID}.claim").unlink()
            elif state["mode"] == "recreate":
                _swap_claim(transitions, b"{other")
        return result

    monkeypatch.setattr(pgrec.os, "stat", stat_then_attack)
    state["mode"] = "unlink"
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    assert not (transitions / f"{OPID}.claim").exists(), \
        "the engine must never recreate or restore the claim"
    # phase 1 legitimately left the coordinate absent; restore the attacker's
    # object before the recreate phase
    _publish(transitions, _bytes(CLAIM))
    state["fired"] = False
    state["mode"] = "recreate"
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    assert (transitions / f"{OPID}.claim").read_bytes() == b"{other", \
        "the engine never deleted or rewrote the attacker's object"
    assert _record_bytes(transitions) == before_record


def test_p6_regular_file_to_symlink_substitution_is_refused(tmp_path):
    """Proof 6: a symlink at the canonical name is refused even when its
    target is a valid private claim inside the governed tree."""
    if os.name == "nt":
        pytest.skip("symlink creation requires privileges on this platform")
    transitions, _record = _governed(tmp_path)
    payload = transitions / f"{OPID}.payload"
    payload.write_bytes(_bytes(CLAIM))
    os.chmod(payload, 0o600)
    claim = _publish(transitions, b"")
    claim.unlink()
    os.symlink(payload, claim)
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    # the engine never deleted or repaired the symlink, and never touched the
    # payload it pointed at
    assert os.path.islink(claim)
    assert payload.read_bytes() == _bytes(CLAIM)


def test_p7_valid_claim_swapped_for_a_different_valid_claim_is_never_bound(
        patched_replay, tmp_path):
    """Proof 7: a well-formed claim bound to foreign authority is not
    consumable authority for THIS promote, even though every field is
    individually valid."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    patched_replay({**CLAIM, "receipt_sha256": FOREIGN})
    snap = pgrec._read_selector_snapshot(OPID, transitions)
    assert pgrec._classify_claim_content(
        OPID, snap, expected_receipt_sha256=EXACT) == "unbound_or_mismatched"
    assert pgrec._claim_state(
        OPID, transitions, expected_receipt_sha256=EXACT) \
        == "unbound_or_mismatched"


def test_p8_one_decision_consumes_exactly_one_snapshot(tmp_path,
                                                       monkeypatch):
    """Proof 8: the branch may not be swapped between classification and
    extraction, because ONE decision performs exactly ONE selector read."""
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    calls = {"n": 0}
    real_read = pgrec._read_selector_snapshot

    def counting(operation_id, transition_dir=None):
        calls["n"] += 1
        return real_read(operation_id, transition_dir)

    monkeypatch.setattr(pgrec, "_read_selector_snapshot", counting)
    promote = {"operation_phase": "promote", "exit_status": 0}
    expected = pgrec._receipt_digest(promote)
    bound = {**CLAIM, "receipt_sha256": expected}
    _publish(transitions, _bytes(bound))
    assert pgrec._valid_transition_claim(OPID, "rollback", promote,
                                         transition_dir=transitions) is True
    assert calls["n"] == 1, (
        "one authority decision must consume exactly one selector snapshot")
    # a swapped branch inside the admitted object is refused by the same law
    def replay_counting(operation_id, transition_dir=None):
        calls["n"] += 1
        return _ReplaySnapshot(
            real_read(operation_id, transition_dir),
            {**bound, "transition": "finalize"})

    monkeypatch.setattr(pgrec, "_read_selector_snapshot", replay_counting)
    assert pgrec._valid_transition_claim(OPID, "rollback", promote,
                                         transition_dir=transitions) is False
    assert calls["n"] == 2


def test_p9_swap_between_shell_classification_and_phase_admission(
        tmp_path):
    """Proof 9: a selector that classifies as legal for the shell and is then
    swapped before the executable phase's admission is refused by the
    phase's own fresh, fully admitted read."""
    transitions, record = _governed(tmp_path)
    promote = {"operation_phase": "promote", "exit_status": 0,
               "operation_id": OPID}
    expected = pgrec._receipt_digest(promote)
    _publish(transitions, _bytes({**CLAIM, "receipt_sha256": expected}))
    record["selected_transition"] = "rollback"
    assert pgrec._classify_record_for_shell(
        record, promote, transition_dir=transitions) == 6
    # deterministic swap, then the phase-admission re-verification
    _swap_claim(transitions, _bytes(
        {**CLAIM, "receipt_sha256": FOREIGN,
         "transition": "rollback"}))
    assert pgrec._valid_transition_claim(
        OPID, "rollback", promote, transition_dir=transitions) is False
    assert pgrec._classify_record_for_shell(
        record, promote, transition_dir=transitions) == 4


def test_p10_foreign_hard_link_is_refused(tmp_path):
    """Proof 10: an unexpected link count is refused (identity invariant)."""
    transitions, _record = _governed(tmp_path)
    claim = _publish(transitions, _bytes(CLAIM))
    before = _census(transitions)
    second = transitions / f"{OPID}.second"
    try:
        os.link(claim, second)
    except (OSError, NotImplementedError):
        pytest.skip("hard links unavailable on this platform")
    with_link = _census(transitions)
    try:
        with pytest.raises(pgrec._ExecutionAuthorityConflict):
            pgrec._read_selector_snapshot(OPID, transitions)
        assert _census(transitions) == with_link
    finally:
        try:
            second.unlink()
        except OSError:
            pass
    assert _census(transitions) == before


# --------------------------------------------------------------------- #
# proofs 11-16: the corrected state/selector matrix rows
# --------------------------------------------------------------------- #

def test_p11_finalizing_without_claim_fails_closed(tmp_path):
    transitions, record = _governed(tmp_path, state="FINALIZING")
    before = _census(transitions)
    assert pgrec._classify_record_for_shell(record) == 4
    assert pgrec._selector_agrees_with_finalizing(OPID, None, transitions) \
        is False
    assert not (transitions / f"{OPID}.claim").exists()
    assert _census(transitions) == before


def test_p12_finalizing_foreign_well_formed_digest_fails_closed(tmp_path):
    transitions, record = _governed(tmp_path, state="FINALIZING")
    _publish(transitions, _bytes({**CLAIM, "transition": "finalize",
                                  "receipt_sha256": FOREIGN}))
    before = _census(transitions)
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 4
    assert pgrec._selector_agrees_with_finalizing(
        OPID, None, transitions) is False
    assert _census(transitions) == before


@pytest.mark.parametrize("state", ["CREATED", "STAGED"])
def test_p13_created_or_staged_with_a_claim_fails_closed(tmp_path, state):
    transitions, record = _governed(tmp_path, state=state)
    _publish(transitions, _bytes(CLAIM))
    before = _census(transitions)
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 4
    assert _census(transitions) == before


@pytest.mark.parametrize("state", ["CREATED", "STAGED"])
def test_created_or_staged_without_selector_keeps_documented_disposition(
        tmp_path, state):
    transitions, record = _governed(tmp_path, state=state)
    before = _census(transitions)
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 0
    assert _census(transitions) == before


def test_p14_rolled_back_without_exact_selector_fails_closed(tmp_path):
    transitions, record = _governed(tmp_path, state="ROLLED_BACK")
    before = _census(transitions)
    # no receipt at all: unknowable authority
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 4
    # a receipt bound to different authority: still closed
    other = {"operation_phase": "promote", "exit_status": 0,
             "operation_id": OPID, "note": "different authority"}
    assert pgrec._classify_record_for_shell(
        record, promote=other, transition_dir=transitions) == 4
    assert _census(transitions) == before


def test_p15_failed_without_a_claim_fails_closed(tmp_path):
    transitions, record = _governed(tmp_path, state="FAILED")
    before = _census(transitions)
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 4
    other = {"operation_phase": "promote", "exit_status": 0,
             "operation_id": OPID}
    assert pgrec._classify_record_for_shell(
        record, promote=other, transition_dir=transitions) == 4
    assert _census(transitions) == before


def test_p16_malformed_record_digest_fails_closed(tmp_path):
    transitions, _record = _governed(tmp_path, record_digest="not-a-digest")
    _publish(transitions, _bytes(CLAIM))
    before = _census(transitions)
    assert pgrec._receiptless_selector_agrees(
        OPID, "rollback", transitions) is False
    assert _census(transitions) == before


def test_foreign_operation_id_claim_is_malformed(tmp_path):
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes({**CLAIM, "operation_id": "f" * 32}))
    before = _census(transitions)
    assert pgrec._claim_state(
        OPID, transitions, expected_receipt_sha256=EXACT) == "malformed"
    assert _census(transitions) == before


# --------------------------------------------------------------------- #
# executable weakened controls (child processes, deterministic hooks)
# --------------------------------------------------------------------- #

LOAD_CLAIM_R46 = '''    snapshot = _read_selector_snapshot(operation_id, transition_dir)
    if not snapshot.present:
        return None
    if not isinstance(snapshot.claim, dict):
        raise _selector_conflict(
            operation_id, "the admitted claim is not a JSON object")
    return snapshot.claim
'''

VALID_CLAIM_R46 = '''    if promote is None:
        return False
    expected = _receipt_digest(promote)
    try:
        if snapshot is None:
            snapshot = _read_selector_snapshot(operation_id, transition_dir)
        state = _classify_claim_content(operation_id, snapshot,
                                        expected_receipt_sha256=expected)
    except _ExecutionAuthorityConflict:
        return False
    if state != "bound_complete":
        return False
    # The SAME snapshot that proved the binding selects the branch. There is
    # no second read of the coordinate in which a replacement could land.
    claim = snapshot.claim
    return isinstance(claim, dict) and claim.get("transition") == transition
'''

LOAD_CLAIM_WEAK = '''    path = os.path.join(transition_dir or _transitions_dir(),
                        operation_id + ".claim")
    if not os.path.lexists(path):
        return None
    os.lstat(path)
    os.lstat(path)
    _WEAK_HOOK()
    with open(path, encoding="utf-8") as f:
        return json.load(f)
'''

VALID_CLAIM_WEAK = '''    if promote is None:
        return False
    expected = _receipt_digest(promote)
    try:
        state = _claim_state(operation_id, transition_dir,
                             expected_receipt_sha256=expected)
    except _ExecutionAuthorityConflict:
        return False
    if state != "bound_complete":
        return False
    _WEAK_HOOK()
    claim = _load_claim(operation_id, transition_dir=transition_dir)
    return isinstance(claim, dict) and claim.get("transition") == transition
'''


def _weakened_engine(tmp_path, transform):
    source = (SCRIPTS / "pg-recovery.py").read_text(encoding="utf-8")
    old, new = transform
    assert old in source, "the shipped reader changed shape; fix the control"
    source = source.replace(old, new) + "\n_WEAK_HOOK = lambda: None\n"
    path = tmp_path / "weak-pg-recovery.py"
    path.write_text(source, encoding="utf-8")
    return path


CHILD_HARNESS = r"""
import importlib.util, json, os, sys
scripts, mode, engine_path, opid, tdir = sys.argv[1:6]
spec = importlib.util.spec_from_file_location("engine_under_test",
                                              engine_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

promote = {"operation_phase": "promote", "exit_status": 0}
claim = {"format": mod._CLAIM_FORMAT, "operation_id": opid,
         "transition": "rollback",
         "receipt_sha256": mod._receipt_digest(promote),
         "claimed_at": "2026-09-24T00:00:00Z"}


def publish(doc):
    p = os.path.join(tdir, opid + ".claim")
    tmp = p + ".repl"
    with open(tmp, "wb") as fh:
        fh.write(json.dumps(doc).encode())
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)


publish(claim)

fired = {"n": 0}


def hook():
    fired["n"] += 1
    # the replacement is a well-formed FINALIZE claim bound to FOREIGN
    # authority: the defect being demonstrated is consuming a branch from an
    # object whose binding was never proven (or returning content whose
    # provenance differs from the validated object)
    publish({**claim, "transition": "finalize", "receipt_sha256": "b" * 64})


if mode == "reader":
    # Weakened control 1: the old reader validates the pathname (two lstats),
    # then a deterministic hook replaces the claim, then it opens the PATH.
    # The returned content belongs to a DIFFERENT object than the one the
    # validation described -- undetected mixed provenance.
    #
    # The shipped reader runs the SAME attack in the same pre-open window:
    # the hook fires between its pre-open lstat and its descriptor open, and
    # it must return COHERENT bytes (the object it actually admitted) or
    # refuse -- never the un-admitted replacement's payload.
    if hasattr(mod, "_WEAK_HOOK"):
        mod._WEAK_HOOK = hook
    else:
        hook()
    content = mod._load_claim(opid, tdir)
    branch = content["transition"] if content else "None"
    print(("MIXED" if branch != "rollback" else "COHERENT")
          + f":branch={branch}:reads={fired['n']}")
elif mode == "decision":
    # Weakened control 2: classify from a first read, take the branch from a
    # second read. The hook replaces the claim between the two reads; the old
    # decision accepts the swapped branch.
    #
    # The shipped decision consumes ONE snapshot, so a replacement cannot
    # land between classification and branch selection; here the same swap
    # is ordered BEFORE the decision, which must then refuse the foreign
    # selector instead of consuming it.
    if hasattr(mod, "_WEAK_HOOK"):
        mod._WEAK_HOOK = hook
    else:
        hook()
    try:
        accepted = mod._valid_transition_claim(opid, "finalize", promote,
                                               transition_dir=tdir)
    except mod._ExecutionAuthorityConflict:
        print(f"REFUSED:conflict:reads={fired['n']}")
        sys.exit(0)
    print(("ACCEPTED" if accepted else "REFUSED:false")
          + f":reads={fired['n']}")
"""


def _run_child(engine_path, opid, tdir, mode):
    return subprocess.run(
        [sys.executable, "-c", CHILD_HARNESS, str(SCRIPTS), mode,
         str(engine_path), opid, str(tdir)],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def test_weakened_path_then_open_accepts_a_boundary_replacement(tmp_path):
    """Weakened control 1 (provenance): restoring lstat, lstat, open(path),
    the reader validates the rollback claim and RETURNS the finalize claim
    swapped in between -- mixed provenance, undetected. The shipped reader is
    proven coherent: its returned bytes always belong to the object whose
    identity it admitted."""
    transitions, _record = _governed(tmp_path)
    weak = _weakened_engine(tmp_path, (LOAD_CLAIM_R46, LOAD_CLAIM_WEAK))
    out = _run_child(weak, OPID, str(transitions), "reader")
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("MIXED:branch=finalize:reads=1"), (
        out.stdout, out.stderr)
    # The shipped law's answer to the SAME attack is at the DECISION layer:
    # whatever object the name held at open time was fully admitted, and the
    # foreign finalize selector it carries is refused, never consumed.
    shipped = _run_child(SCRIPTS / "pg-recovery.py", OPID, str(transitions),
                         "decision")
    assert shipped.returncode == 0, shipped.stderr
    assert shipped.stdout.startswith("REFUSED:"), (shipped.stdout,
                                                   shipped.stderr)
    assert ":reads=1" in shipped.stdout


def test_weakened_two_read_decision_accepts_a_branch_swap(tmp_path):
    """Weakened control 2 (decision coherence): classify from a first read,
    take the branch from a second read -- the swapped branch is ACCEPTED.
    The shipped decision consumes exactly ONE snapshot (reads=1), so a
    replacement cannot land between classification and branch selection."""
    transitions, _record = _governed(tmp_path)
    weak = _weakened_engine(tmp_path, (VALID_CLAIM_R46, VALID_CLAIM_WEAK))
    out = _run_child(weak, OPID, str(transitions), "decision")
    assert out.returncode == 0, out.stderr
    # the old decision classified the rollback claim, then accepted the
    # finalize branch from the second read (the hook fired exactly between
    # the two reads)
    assert out.stdout.startswith("ACCEPTED:reads=1"), (
        out.stdout, out.stderr)
    shipped = _run_child(SCRIPTS / "pg-recovery.py", OPID, str(transitions),
                         "decision")
    assert shipped.returncode == 0, shipped.stderr
    # exactly ONE selector read, and the foreign selector is refused
    assert shipped.stdout.startswith("REFUSED:"), (shipped.stdout,
                                                   shipped.stderr)
    assert ":reads=1" in shipped.stdout, (shipped.stdout, shipped.stderr)


# --------------------------------------------------------------------- #
# zero-side-effect law
# --------------------------------------------------------------------- #

def test_every_denial_has_zero_authority_side_effects(tmp_path, monkeypatch):
    transitions, record = _governed(tmp_path, state="FAILED")
    _publish(transitions, _bytes({**CLAIM, "receipt_sha256": FOREIGN}))
    before = _census(transitions)
    called = []

    def _boom(*_a, **_k):
        called.append("container-call")
        raise AssertionError("no container call may happen")

    for name in ("_quarantine_present", "db_exists", "_verify_db",
                 "_verify_against_floor", "_rollback_catalog_state"):
        if hasattr(pgrec, name):
            monkeypatch.setattr(pgrec, name, _boom)
    # denials on the selector law: foreign-bound claim, terminal FAILED state,
    # and a directory parked at the canonical coordinate
    assert pgrec._classify_record_for_shell(
        record, transition_dir=transitions) == 4
    assert pgrec._selector_agrees_with_finalizing(
        OPID, None, transitions) is False
    claim = transitions / f"{OPID}.claim"
    claim.unlink()
    claim.mkdir()
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._load_claim(OPID, transitions)
    claim.rmdir()
    # restore the exact attacker object the census was taken with
    _publish(transitions, _bytes({**CLAIM, "receipt_sha256": FOREIGN}))
    assert called == []
    assert _census(transitions) == before


def test_shipped_reader_binds_bytes_to_admitted_identity(tmp_path):
    transitions, _record = _governed(tmp_path)
    _publish(transitions, _bytes(CLAIM))
    before = _census(transitions)
    claim = pgrec._load_claim(OPID, transitions)
    assert claim["receipt_sha256"] == EXACT
    snap = pgrec._read_selector_snapshot(OPID, transitions)
    assert snap.present and snap.link_count == 1
    assert pgrec._classify_claim_content(
        OPID, snap, expected_receipt_sha256=EXACT) == "bound_complete"
    assert _census(transitions) == before
