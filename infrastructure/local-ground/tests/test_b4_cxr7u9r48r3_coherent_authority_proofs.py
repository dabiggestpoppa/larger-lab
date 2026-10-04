"""B4-CXR7U9R48R3 - deterministic proofs of coherent authority and immutability.

R47 proved "one record read and one selector read per decision". It did not
prove those two reads came from the SAME authority generation, and its
authority structures were only shallowly frozen. Both facts were reproducible:

  * a whole-directory replacement landing between the record read and the
    selector read produced an ACCEPTED decision combining a PROMOTED record
    from generation A with a finalize selector from generation B;
  * `snapshot.record["state"] = "FINALIZED"` mutated the material a decision
    was reading.

Every proof here is deterministic -- no threads, no sleeps, no races. Where a
proof would be vacuous against a shipped implementation that was never
vulnerable, a deliberately WEAKENED control is built from the shipped source
and shown to fail, so a green suite means the proof discriminates rather than
that the attack was impossible.
"""
import ast
import base64
import builtins
import dataclasses
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from test_b4_cxr7u9r47r1_authority_snapshot import (  # noqa: F401
    CLI, OPID, _build, _bytes, _census, _claim_doc, _publish, pgrec)

ENGINE = Path(pgrec.__file__).resolve()
FOREIGN = "b" * 64


# --------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------- #

def _weakened(tmp_path, old, new, name="weakened-pg-recovery.py"):
    """Rewrite the shipped engine into a deliberately weaker one.

    The anchor is ASSERTED, not assumed. A stale anchor would make
    `str.replace` return the source unchanged, handing the control the
    shipped engine and turning the proof vacuous.
    """
    source = CLI.read_text(encoding="utf-8")
    assert old in source, "the shipped engine changed shape: anchor is stale"
    changed = source.replace(old, new)
    assert changed != source, "the weakening produced no change"
    path = Path(tmp_path) / name
    path.write_text(changed, encoding="utf-8")
    compile(changed, str(path), "exec")
    return path


def _import(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECORD_READ_ANCHOR = """    dir_fd, identity = _open_governed_directory(governed, operation_id)
    try:
        # B4-CXR7U9R48R1: ONE admitted directory descriptor owns BOTH reads.
        # The record is opened descriptor-relative through this same dir_fd --
        # `os.open(name, flags, dir_fd=dir_fd)` -- so a whole-directory
        # replacement between the two reads cannot produce a decision that
        # combines a record from one generation with a selector from another.
        # `_load_transition_record`, which resolves a PATHNAME, is deliberately
        # NOT called on this path: it would reintroduce exactly the window R47
        # left open.
        record_name = _derive_record_coordinate_name(operation_id)
        try:
            record_snapshot = _read_record_snapshot_admitted(
                operation_id, governed, record_name, dir_fd, identity)
            admitted_record = record_snapshot.record
        except (OSError, ValueError, RuntimeError, TypeError,
                _ExecutionAuthorityConflict):
            admitted_record = None
            record_snapshot = RecordSnapshot(
                operation_id=operation_id, transition_dir=governed,
                canonical_path=os.path.join(governed, record_name),
                present=False, governed_device=identity[0],
                governed_inode=identity[1], device=0, inode=0, size=0, mode=0,
                link_count=0, record=None, record_digest=None,
                raw_digest=None, read_error="refused")
"""


RECORD_READ_WEAKENED = """    record_name = _derive_record_coordinate_name(operation_id)
    try:
        admitted_record = _load_transition_record(operation_id)
    except (OSError, ValueError, RuntimeError, TypeError,
            _ExecutionAuthorityConflict):
        admitted_record = None
    dir_fd, identity = _open_governed_directory(governed, operation_id)
    try:
        record_snapshot = RecordSnapshot(
            operation_id=operation_id, transition_dir=governed,
            canonical_path=os.path.join(governed, record_name),
            present=admitted_record is not None,
            governed_device=identity[0],
            governed_inode=identity[1], device=0, inode=0, size=0, mode=0,
            link_count=0, record=admitted_record,
            record_digest=None, raw_digest=None, read_error=None)
"""


COHERENCE_ANCHOR = """        _assert_one_directory_generation(
            operation_id, governed, dir_fd, identity, record_snapshot, selector)
"""


def _r47_shape(tmp_path):
    """The R47 shape: a pathname record read and no coherence proof.

    Two asserted rewrites, because R48 changed two things. Each anchor is
    checked BEFORE the replacement, so a drifted engine makes this control
    fail loudly instead of silently rebuilding the shipped engine.
    """
    weakened = _weakened(tmp_path, RECORD_READ_ANCHOR, RECORD_READ_WEAKENED)
    source = weakened.read_text(encoding="utf-8")
    assert COHERENCE_ANCHOR in source, "coherence anchor is stale"
    weakened.write_text(source.replace(COHERENCE_ANCHOR, ""),
                        encoding="utf-8")
    compile(weakened.read_text(encoding="utf-8"), str(weakened), "exec")
    return weakened


# The state the replacement generation publishes. It differs from the
# build generation's PROMOTED so the two are distinguishable, and it is
# paired with a finalize selector so that neither generation's
# (state, transition) pair can be mistaken for the other's.
GENERATION_B_STATE = "STAGED"


def _swap_whole_directory(transitions, opid, new_transition,
                          new_state=GENERATION_B_STATE, publish_record=True):
    """Replace the ENTIRE governed directory with a COMPLETE new generation.

    Two properties matter for the proofs below to mean anything:

    * generation A is renamed aside and LEFT IN PLACE. A pinned directory
      descriptor keeps a renamed inode readable, which is exactly the state a
      real whole-directory replacement leaves behind and exactly what the
      R48R1 pin is supposed to keep reading. Deleting it would remove the
      generation under test rather than exercise it.
    * generation B publishes its own record as well as its own claim, with a
      different record state. "Mixed" is then decidable from the CONTENT PAIR
      (record state, selector transition) instead of from which file happened
      to be missing, so the same assertion means the same thing on a platform
      that pins the selector and on one that does not.

    The receipt digest is carried over unchanged on purpose: that is what makes
    this a real attack, because a differing digest would be refused by the
    claim-to-receipt binding before any coherence question arose.
    """
    aside = transitions.with_name(transitions.name + ".aside")
    os.rename(transitions, aside)
    fresh = transitions
    fresh.mkdir(mode=0o700)
    origin = json.loads(
        (aside / f"{opid}.json").read_text(encoding="utf-8"))
    # `publish_record=False` publishes a generation that carries a selector
    # but NO admissible record. That is a real generation, not a missing
    # file: without it the no-record branch below is dormant, because the
    # helper would always publish one.
    if publish_record:
        record_path = fresh / f"{opid}.json"
        record_path.write_text(json.dumps(
            {**origin, "state": new_state,
             "selected_transition": new_transition}),
            encoding="utf-8")
        os.chmod(record_path, 0o600)
    _publish(fresh, {"format": pgrec._CLAIM_FORMAT,
                     "operation_id": opid,
                     "transition": new_transition,
                     "receipt_sha256": origin["receipt_sha256"]})
    return fresh


def _capture(module, operation_id, promote, swap, hook="_selector"):
    """Acquire authority, forcing `swap` at a chosen point in the sequence.

    ``hook`` names the window:

    ``_selector``
        after the record read, before the selector read;
    ``_record``
        immediately after the record read completes;
    ``after_admission``
        after the governed-directory descriptor has been pinned but BEFORE
        either read;
    ``pathname_record``
        after a PATHNAME record read and before the governed directory is
        admitted at all. This is the R47 ordering the weakened control
        reproduces.
    """
    fired = []
    if hook == "_selector":
        attribute = "_read_selector_snapshot_admitted"
        real = getattr(module, attribute)

        def wrapped(op, governed, name, dir_fd, identity):
            if not fired:
                fired.append(True)
                swap()
            return real(op, governed, name, dir_fd, identity)
    elif hook == "_record":
        attribute = "_read_record_snapshot_admitted"
        real = getattr(module, attribute)

        def wrapped(op, governed, name, dir_fd, identity):
            snap = real(op, governed, name, dir_fd, identity)
            if not fired:
                fired.append(True)
                swap()
            return snap
    elif hook == "after_admission":
        attribute = "_open_governed_directory"
        real = getattr(module, attribute)

        def wrapped(coordinate, operation):
            admitted = real(coordinate, operation)
            if not fired:
                fired.append(True)
                swap()
            return admitted
    elif hook == "pathname_record":
        # The real R47 ordering. The R47 engine read the record by PATHNAME
        # and only afterwards derived the claim coordinate and admitted the
        # transitions directory for the selector. Firing the swap here --
        # after the pathname record read, before that admission -- reconstructs
        # the defect itself: an OLD record paired with a NEW selector, because
        # the two reads were never governed by one admission.
        attribute = "_load_transition_record"
        real = getattr(module, attribute)

        def wrapped(op):
            loaded = real(op)
            if not fired:
                fired.append(True)
                swap()
            return loaded
    else:
        raise AssertionError(f"unknown swap window {hook!r}")
    setattr(module, attribute, wrapped)
    try:
        try:
            return "acquired", module._acquire_recovery_authority(
                operation_id, promote)
        except Exception as exc:                # noqa: BLE001 - shape probe
            return "refused", exc
    finally:
        setattr(module, attribute, real)


# The (record state, selector transition) pairs the two generations built
# by _build and _swap_whole_directory actually contain. A bundle is MIXED
# when its pair is neither of these, because then its two reads cannot have
# come from one governed-directory generation. Naming both pairs, rather than
# only the PROMOTED/finalize pair that the Windows shape produces, is what
# keeps the proof meaningful on POSIX, where the R47 defect mixes the other
# way round.
_COHERENT_PAIRS = frozenset({
    ("PROMOTED", "rollback"),
    (GENERATION_B_STATE, "finalize"),
})


def _authority_pair(authority):
    """The (record state, selector transition) an accepted bundle paired."""
    record = authority.record
    selector = authority.selector
    if not isinstance(record, dict) or not isinstance(selector.claim, dict):
        return None
    return (record.get("state"), selector.claim.get("transition"))


def _cross_generation(authority):
    """True when a bundle paired material that never coexisted in one
    governed-directory generation."""
    pair = _authority_pair(authority)
    return pair is not None and pair not in _COHERENT_PAIRS


# ===================================================================== #
# A. WHOLE-DIRECTORY GENERATION SWAP
# ===================================================================== #

def test_a_shipped_never_accepts_a_mixed_generation_decision(tmp_path):
    """A.1 The shipped engine stays pinned or fails closed."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    outcome, bundle = _capture(
        pgrec, OPID, promote,
        lambda: _swap_whole_directory(transitions, OPID, "finalize"))
    if outcome == "acquired":
        assert not _cross_generation(bundle), (
            "a whole-directory replacement yielded an accepted mixed-"
            f"generation decision: {_authority_pair(bundle)!r}")
    else:
        assert isinstance(bundle, pgrec._ExecutionAuthorityConflict), bundle
        assert "generation" in str(bundle), str(bundle)


def test_a_weakened_control_reproduces_the_mixed_generation(tmp_path):
    """A.2 The R47 shape MUST still be exploitable, or A.1 proves nothing.

    The R47 defect was an ORDERING defect, not a per-platform one. R47 read the
    transition record by PATHNAME and only afterwards derived the claim
    coordinate and admitted the transitions directory for the selector, so the
    two reads were never governed by a single admission. A whole-directory
    replacement landing between them produced an accepted decision built from
    an OLD PROMOTED record and the replacement generation's NEW finalize
    selector.

    The control therefore fires the swap AFTER the pathname record read and
    BEFORE the directory is admitted, which is exactly that sequence, and the
    proof requires the exact mixture: acquired, PROMOTED, finalize. Asserting
    any weaker property here would let a control that no longer reproduces the
    defect pass.
    """
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    weak = _import(_r47_shape(tmp_path), "r48r3_a_weak")
    weak._bind_test_recovery_root(str(transitions.parents[0]))
    outcome, bundle = _capture(
        weak, OPID, promote,
        lambda: _swap_whole_directory(transitions, OPID, "finalize"),
        hook="pathname_record")
    assert outcome == "acquired", outcome
    assert _authority_pair(bundle) == ("PROMOTED", "finalize"), (
        "the weakened control must combine the old PROMOTED record with the "
        "replacement finalize selector, proving the proof discriminates")


# ===================================================================== #
# B. REPLACEMENT WINDOWS
# ===================================================================== #

@pytest.mark.parametrize("window", [
    "before_admission",
    "after_admission",
    "between_record_open_and_selector",
    "after_record_before_selector",
    "during_selector",
    "after_both_before_classification",
])
def test_b_every_replacement_window_is_coherent_or_denied(tmp_path, window):
    """B.1 Each named window either keeps one generation or fails closed."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    real_dir = pgrec._open_governed_directory

    def swap():
        _swap_whole_directory(transitions, OPID, "finalize")

    if window == "before_admission":
        def wrapped(coordinate, operation_id):
            swap()
            return real_dir(coordinate, operation_id)
        pgrec._open_governed_directory = wrapped
        try:
            try:
                bundle = pgrec._acquire_recovery_authority(OPID, promote)
                outcome = "acquired"
            except Exception:                   # noqa: BLE001
                bundle, outcome = None, "refused"
        finally:
            pgrec._open_governed_directory = real_dir
        # The replacement happened BEFORE admission, so generation B is the
        # one admitted. Every one of these is concrete: the admitted identity,
        # both snapshots naming it, the record/selector pair, and the absence
        # of a mixed generation. The expression this replaced ended in
        # `or True`, which made the whole window pass unconditionally.
        if outcome == "acquired":
            info = os.stat(transitions)
            replacement_identity = (info.st_dev, info.st_ino)
            assert (bundle.governed_device, bundle.governed_inode) == \
                replacement_identity, (
                "the admitted identity is not the replacement directory's")
            assert (bundle.record_snapshot.governed_device,
                    bundle.record_snapshot.governed_inode) == \
                replacement_identity, (
                "the record snapshot does not name the replacement directory")
            assert (bundle.selector.governed_device,
                    bundle.selector.governed_inode) == replacement_identity, (
                "the selector snapshot does not name the replacement "
                "directory")
            # This window always publishes a record, so there is no
            # `bundle.record is None` case here to assert. The branch that
            # used to sit in this place called
            # `_classify_record_for_shell(bundle, None)`, handing the
            # classifier an authority BUNDLE where it expects a record
            # object. It returned 4 purely because a bundle is not a dict,
            # so it proved a type check, not fail-closed authority -- and it
            # never ran, because the replacement helper always publishes a
            # record. The genuine no-record generation is now exercised,
            # through the real shell route, in
            # `test_b_a_no_record_generation_fails_closed_through_the_shell_route`.
            assert _authority_pair(bundle) == (GENERATION_B_STATE,
                                               "finalize")
            assert not _cross_generation(bundle), (
                "the before-admission window accepted a mixed generation")
        return

    # Each named window has to fire the swap where its NAME says. This
    # mapping used to send "after_admission" to the selector hook as well,
    # so that window silently re-ran the "during_selector" case and the
    # window between pinning the governed directory and reading the record
    # -- the one the R47 pathname defect actually lives in on POSIX -- was
    # never exercised at all.
    hook = {
        "after_admission": "after_admission",
        "between_record_open_and_selector": "_record",
        "after_record_before_selector": "_record",
    }.get(window, "_selector")
    outcome, bundle = _capture(pgrec, OPID, promote, swap, hook=hook)
    if outcome == "acquired":
        assert not _cross_generation(bundle), (
            f"window {window} produced a mixed-generation decision: "
            f"{_authority_pair(bundle)!r}")
    else:
        assert isinstance(bundle, pgrec._ExecutionAuthorityConflict), bundle


def test_b_after_both_reads_the_bundle_is_already_coherent(tmp_path):
    """B.2 After both reads, the bundle is self-consistent by construction."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    info = os.stat(transitions)
    assert (bundle.record_snapshot.governed_device,
            bundle.record_snapshot.governed_inode) == (info.st_dev, info.st_ino)
    assert (bundle.selector.governed_device,
            bundle.selector.governed_inode) == (info.st_dev, info.st_ino)
    assert (bundle.governed_device, bundle.governed_inode) == (info.st_dev,
                                                              info.st_ino)


# ===================================================================== #
# C. RECORD ATTACKS
# ===================================================================== #

def test_b_a_no_record_generation_fails_closed_through_the_shell_route(
        tmp_path):
    """A generation publishing NO record fails closed for the authority
    reason, through the real public route with correct argument types.

    This is the case the deleted dormant branch pretended to cover. The
    authority bundle is a frozen snapshot, not a record, so passing it to
    `_classify_record_for_shell` returned `_VERDICT_FAIL_CLOSED` through its
    `isinstance(record, dict)` guard. That is a type check, not a decision
    about missing durable authority, and it would have passed identically
    for a bundle, a string, or an integer.

    So the case is driven the way restore.sh drives it: a replacement
    generation that carries a selector but publishes no record, judged by
    `_classify_rollback_for_shell(receipt_path)`.
    """
    transitions, _record, promote, receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    fresh = _swap_whole_directory(transitions, OPID, "finalize",
                                  publish_record=False)
    assert not (fresh / f"{OPID}.json").exists(), (
        "the no-record generation published a record")
    assert _census(pgrec._transitions_dir()), "the selector was not published"

    verdict = pgrec._classify_rollback_for_shell(str(receipt))
    assert verdict == 4, (
        "a generation with no durable record must fail closed, not decide")

    # The refusal is for the AUTHORITY reason, not a type check: the durable
    # record the receipt would bind to is genuinely absent at the governed
    # coordinate, which is what _bound_operation refuses on.
    with pytest.raises(RuntimeError) as caught:
        pgrec._load_transition_record(OPID)
    assert "no durable recovery operation record" in str(caught.value), (
        "the refusal was not about missing durable authority")
    # And the failure is a refusal, not a crash or a silent success.
    assert verdict not in (0, 5, 6), verdict


def test_c_oversized_record_is_refused(tmp_path):
    """C.1 An over-bound record is refused whole, before any buffer grows."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = transitions / f"{OPID}.json"
    path.write_bytes(b"{" + b" " * (pgrec._RECORD_MAX_BYTES + 10))
    before = _census(pgrec._transitions_dir())
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record is None, "an oversized record was admitted"
    assert pgrec._classify_record_for_shell(record, promote) == 4
    assert _census(pgrec._transitions_dir()) == before


def test_c_malformed_record_json_is_refused(tmp_path):
    """C.2 Malformed JSON never yields decision material."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = transitions / f"{OPID}.json"
    path.write_bytes(b"{not json")
    os.chmod(path, 0o600)
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record is None
    assert pgrec._classify_record_for_shell(record, promote) == 4


def test_c_receipt_digest_mismatch_fails_closed(tmp_path):
    """C.3 A caller record that disagrees with the admitted one is refused.

    The authority may not decide from either copy of a crossed read.
    """
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    # The census is captured BEFORE the denial. Comparing a census with itself
    # proves nothing, which is what this assertion used to do.
    before = _census(pgrec._transitions_dir())
    record["receipt_sha256"] = FOREIGN
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._acquire_recovery_authority(OPID, promote, record=record)
    assert _census(pgrec._transitions_dir()) == before


def test_c_contradictory_state_and_selector_fail_closed(tmp_path):
    """C.4 A FINALIZING record whose selector says rollback is not authority."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "FINALIZING", "rollback")
    assert pgrec._classify_record_for_shell(record, promote) == 4


@pytest.mark.parametrize("mutation,label", [
    ({"operation_id": "c" * 32}, "internal operation id names another op"),
    ({"operation_id": None}, "internal operation id is null"),
    ({"operation_id": ""}, "internal operation id is empty"),
    ({"operation_id": 7}, "internal operation id is not a string"),
    ({"format": "oce-pg-recovery-transition-v0"}, "unknown record format"),
    ({"format": None}, "record format is null"),
    ({"format": "not-a-format"}, "record format is arbitrary text"),
])
def test_c_record_internal_identity_is_bound_at_admission(
        tmp_path, mutation, label):
    """C.5/C.6 A record filed under a coordinate must DESCRIBE that
    operation, or it never becomes authority material.

    Admission proved the bytes came from the canonical file in the pinned
    governed directory. These proofs cover the remaining half: that the object
    inside those bytes is really this operation's record. Each case must be a
    denial at admission, raised before any selector authority is read, and
    must leave the governed directory byte-identical.
    """
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    record.update(mutation)
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    before = _census(pgrec._transitions_dir())

    # The selector read is the LAST thing acquisition does; if it is never
    # reached, no selector authority was consumed on a crossed record.
    real_selector = pgrec._read_selector_snapshot_admitted

    def forbidden(*_a, **_k):
        raise AssertionError(
            "selector authority must not be consumed after a crossed record "
            "identity")

    pgrec._read_selector_snapshot_admitted = forbidden
    try:
        with pytest.raises(pgrec._ExecutionAuthorityConflict) as caught:
            pgrec._acquire_recovery_authority(OPID, promote)
    finally:
        pgrec._read_selector_snapshot_admitted = real_selector
    assert "operation id" in str(caught.value) or "format" in str(caught.value), \
        (label, str(caught.value))
    assert _census(pgrec._transitions_dir()) == before, label


def test_c_a_record_that_is_not_an_object_is_refused(tmp_path):
    """C.7 Valid JSON that is not an object is not a record."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = transitions / f"{OPID}.json"
    path.write_bytes(b"[1, 2, 3]")
    os.chmod(path, 0o600)
    before = _census(pgrec._transitions_dir())
    with pytest.raises(pgrec._ExecutionAuthorityConflict) as caught:
        pgrec._acquire_recovery_authority(OPID, promote)
    assert "JSON object" in str(caught.value), str(caught.value)
    assert _census(pgrec._transitions_dir()) == before


def test_c_a_missing_internal_operation_id_is_refused(tmp_path):
    """C.8 A record with no operation id at all is not this authority."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    record.pop("operation_id", None)
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    with pytest.raises(pgrec._ExecutionAuthorityConflict) as caught:
        pgrec._acquire_recovery_authority(OPID, promote)
    assert "operation id" in str(caught.value), str(caught.value)


@pytest.mark.skipif(os.name == "nt",
                    reason="symlink record is exercised on Linux")
def test_c_symlink_record_is_refused(tmp_path):
    """C.6 A redirected record coordinate is never followed."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = transitions / f"{OPID}.json"
    real = path.read_bytes()
    path.unlink()
    other = transitions / "elsewhere.json"
    other.write_bytes(real)
    os.chmod(other, 0o600)
    os.symlink(other, path)
    before = _census(pgrec._transitions_dir())
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record is None, "a symlinked record was admitted"
    assert _census(pgrec._transitions_dir()) == before


@pytest.mark.skipif(os.name == "nt",
                    reason="FIFO record is exercised on Linux")
def test_c_fifo_record_is_refused(tmp_path):
    """C.7 A non-regular object at the record coordinate is refused."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = transitions / f"{OPID}.json"
    path.unlink()
    os.mkfifo(path)
    before = _census(pgrec._transitions_dir())
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record is None
    assert _census(pgrec._transitions_dir()) == before


def test_c_widened_record_permissions_are_refused(tmp_path):
    """C.8 A group/other-accessible record is refused."""
    if os.name == "nt":
        pytest.skip("POSIX mode law is exercised on Linux")
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    os.chmod(transitions / f"{OPID}.json", 0o644)
    before = _census(pgrec._transitions_dir())
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record is None, "a widened record was admitted"
    assert _census(pgrec._transitions_dir()) == before


def test_c_deriving_a_traversing_record_coordinate_is_refused():
    """C.9 The derived record coordinate is always a bare basename."""
    for hostile in ("../../etc/passwd", "a/b", "a\\b", "..", ".",
                    "x\x00y"):
        with pytest.raises(Exception):
            pgrec._derive_record_coordinate_name(hostile)
    assert pgrec._derive_record_coordinate_name(OPID) == f"{OPID}.json"


# ===================================================================== #
# D. DEEP IMMUTABILITY
# ===================================================================== #

def _bundle(tmp_path):
    _t, _record, promote, _receipt = _build(tmp_path, "PROMOTED", "rollback")
    return pgrec._acquire_recovery_authority(OPID, promote)


def test_d_top_level_assignment_fails(tmp_path):
    bundle = _bundle(tmp_path)
    with pytest.raises(Exception):
        bundle.record = {}


def test_d_nested_record_assignment_fails(tmp_path):
    bundle = _bundle(tmp_path)
    with pytest.raises(TypeError):
        bundle.record["state"] = "FINALIZED"


def test_d_nested_selector_claim_assignment_fails(tmp_path):
    bundle = _bundle(tmp_path)
    with pytest.raises(TypeError):
        bundle.selector.claim["transition"] = "finalize"


def test_d_source_mutation_cannot_alter_the_snapshot():
    """A private deep copy, not an alias."""
    source = {"state": "PROMOTED", "nested": {"a": 1}, "items": [1, 2]}
    frozen = pgrec._deep_freeze(source)
    source["state"] = "FINALIZED"
    source["nested"]["a"] = 99
    source["items"].append(3)
    assert frozen["state"] == "PROMOTED"
    assert frozen["nested"]["a"] == 1
    assert tuple(frozen["items"]) == (1, 2)


def test_d_no_nested_container_is_indirectly_mutable(tmp_path):
    bundle = _bundle(tmp_path)
    for _key, value in bundle.record.items():
        assert not isinstance(value, (list, set)), value
        if isinstance(value, dict):
            with pytest.raises(TypeError):
                value["anything"] = 1


def test_d_digest_and_decision_are_stable(tmp_path):
    bundle = _bundle(tmp_path)
    first = bundle.record_digest
    for _ in range(3):
        assert pgrec._receipt_digest(bundle.record) == first
    assert pgrec._classify_record_for_shell(bundle.record) in (0, 4, 5, 6)


def test_d_shallow_frozen_control_is_observably_mutable():
    """The negative control: shallow freezing is not deep freezing."""
    @dataclasses.dataclass(frozen=True)
    class Shallow:
        record: object

    shallow = Shallow(record={"state": "PROMOTED"})
    with pytest.raises(Exception):
        shallow.record = {}
    shallow.record["state"] = "FINALIZED"          # succeeds -- the defect
    assert shallow.record["state"] == "FINALIZED"


def test_d_shipped_bundle_is_a_single_type():
    """Exactly one authority bundle type, so no weaker variant can be used."""
    assert pgrec.RecoveryAuthorityBundle is pgrec.RecoveryAuthoritySnapshot


# ===================================================================== #
# E. DIRECTORY IDENTITY
# ===================================================================== #

def test_e_every_bundle_proves_one_directory_generation(tmp_path):
    """E.1 Record and selector carry the admitted directory identity."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    info = os.stat(transitions)
    identity = (info.st_dev, info.st_ino)
    assert (bundle.governed_device, bundle.governed_inode) == identity
    assert (bundle.record_snapshot.governed_device,
            bundle.record_snapshot.governed_inode) == identity
    assert (bundle.selector.governed_device,
            bundle.selector.governed_inode) == identity
    # bound to the objects actually admitted, not to copied expected values
    assert bundle.record_snapshot.inode == os.stat(
        transitions / f"{OPID}.json").st_ino
    assert bundle.selector.inode == os.stat(
        transitions / f"{OPID}.claim").st_ino
    assert record["state"] == "PROMOTED"


def test_e_identity_is_bound_to_real_descriptors(tmp_path):
    """E.2 The proof must come from descriptors, not from a stored copy."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    seen = {}
    real = pgrec._assert_one_directory_generation

    def probe(operation_id, governed, dir_fd, identity, record, selector):
        seen["dir_fd"] = dir_fd
        seen["identity"] = identity
        seen["record_identity"] = (record.governed_device,
                                   record.governed_inode)
        seen["selector_identity"] = (selector.governed_device,
                                     selector.governed_inode)
        if os.name != "nt" and dir_fd is not None:
            # fstat INSIDE the decision. _acquire_recovery_authority closes
            # the directory descriptor in its finally block before it returns,
            # so stat-ing it after the call proves nothing but a closed fd --
            # which is why this proof raised EBADF on Linux. Pin liveness has
            # to be observed while the descriptor is still the one the
            # decision is reading through.
            live = os.fstat(dir_fd)
            seen["live_identity"] = (live.st_dev, live.st_ino)
        return real(operation_id, governed, dir_fd, identity, record,
                    selector)
    pgrec._assert_one_directory_generation = probe
    try:
        pgrec._acquire_recovery_authority(OPID, promote)
    finally:
        pgrec._assert_one_directory_generation = real
    assert seen["record_identity"] == seen["identity"]
    assert seen["selector_identity"] == seen["identity"]
    if os.name != "nt":
        assert seen["dir_fd"] is not None, (
            "POSIX must hold a real directory descriptor during the decision")
        assert seen["live_identity"] == seen["identity"], (
            "the pinned descriptor must still name the admitted directory "
            "while the decision is reading through it")
        # ...and it must be GONE once the bundle is returned. The engine owns
        # the descriptor, not its caller: a live fd reachable from a returned
        # object is a leak, and a proof that only ever observed the fd while
        # the decision was running would not notice one.
        with pytest.raises(OSError):
            os.fstat(seen["dir_fd"])


# ===================================================================== #
# F. REAL CONSUMERS
# ===================================================================== #

def test_f_the_shell_route_uses_the_coherent_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    transitions, _record, _promote, receipt = _build(
        tmp_path / "engine", "PROMOTED", "rollback")
    assert pgrec._classify_rollback_for_shell(str(receipt)) == 6
    assert transitions.is_dir()


def test_f_the_pure_classifier_touches_no_filesystem(tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("the classifier must not touch the filesystem")
    for name in ("_read_selector_snapshot", "_read_selector_snapshot_admitted",
                 "_read_record_snapshot_admitted", "_load_transition_record",
                 "_load_claim", "_acquire_recovery_authority"):
        monkeypatch.setattr(pgrec, name, boom)
    assert pgrec._classify_claim_content(
        OPID, bundle.selector,
        expected_receipt_sha256=bundle.expected_receipt_sha256) \
        == "bound_complete"
    assert pgrec._claim_state(OPID, authority=bundle,
                              expected_receipt_sha256=
                              bundle.expected_receipt_sha256) == "bound_complete"


def test_f_every_verdict_row_stays_coherent(tmp_path):
    """F.3 The whole decision matrix still runs off one coherent bundle."""
    for state, transition, expected in (
            ("CREATED", None, 0), ("STAGED", None, 0),
            ("PROMOTED", "rollback", 6), ("PROMOTED", "finalize", 5),
            ("FINALIZING", "finalize", 5), ("ROLLED_BACK", "rollback", 6),
            ("FAILED", None, 4)):
        _t, record, promote, _r = _build(
            Path(tempfile.mkdtemp()), state, transition)
        assert pgrec._classify_record_for_shell(record, promote) == expected, \
            (state, transition)


# ===================================================================== #
# G. ZERO SIDE EFFECTS
# ===================================================================== #

def _census_outside(root, *excluded_names):
    """A byte census of `root` EXCLUDING the subtree the attacker replaces.

    `_census` walks the whole recovery root, which contains the governed
    transitions directory. In the replacement proofs that directory is the
    ATTACKER's to rewrite, so comparing it before and after measures the
    attack rather than the engine. The attacker also leaves generation A
    behind under `<name>.aside`, so both subtrees are excluded.

    This keeps everything else -- above all the promote receipt, which lives
    outside the transitions directory and which a decision has no licence to
    touch.
    """
    excluded = set(excluded_names)
    return {
        name: value
        for name, value in _census(root).items()
        if name.split(os.sep)[0] not in excluded
    }


class _MutationTripwire:
    """Record every MUTATION the engine attempts, and nothing else.

    Distinguishing attacker mutations from engine mutations is the whole
    point, and it is done structurally rather than by convention. The
    attacker here is `_swap_whole_directory`, which runs in THIS module and
    therefore uses the real `os`. The engine reaches the filesystem through
    its own `pgrec.os` global, so binding that one name to a proxy separates
    the two without any allow-list of "expected" writes: if the engine
    unlinks, renames, replaces, truncates, chmods, links, mkdirs or opens
    anything for writing, it is recorded -- and the attacker's identical
    syscall through the real `os` is not.

    COVERAGE. The audited surface is enumerated by the closed-world
    call-site audit in `_audit_source`/`_assert_closed_world`,
    which classifies EVERY reachable call site and fails closed on an
    unrecognised one. Three kinds of channel are covered:

    1. `os.<name>` for the unconditionally-mutating names in `MUTATORS`.
    2. `os.open`/`os.fdopen`/builtin `open` -- CONDITIONAL on the flags or
       mode, because the engine legitimately OPENS governed files to read
       them, and a tripwire that recorded every open would report the
       read-only authority path as a mutation. Only write-capable
       flag/mode combinations are recorded.
    3. `tempfile.mkstemp` and `shutil.copyfileobj`, which create or fill a
       file without touching `pgrec.os` at all.

    The engine's own durable-write helpers are wrapped for attribution, so a
    helper-layer write is distinguishable from an `os` layer one.
    """

    MUTATORS = frozenset({
        "unlink", "remove", "rmdir", "removedirs", "truncate", "chmod",
        "chown", "link", "symlink", "rename", "replace", "mkdir",
        "makedirs", "rmtree", "write", "fsync", "ftruncate", "fchmod",
        "lchmod", "utime", "rmtree",
    })

    # os.O_* bits that make an open write-capable. O_RDONLY is 0 on both
    # platforms, so an absent bit is a read.
    _WRITE_FLAGS = tuple(
        getattr(os, name, 0) for name in
        ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"))

    # Characters that make a mode string write-capable.
    _WRITE_MODE_CHARS = frozenset("wax+")

    WRITE_HELPERS = (
        "_write_transition_record", "_record_transition", "_commit_receipt",
        "_exclusive_copy", "_publish_no_replace", "_fsync_dir",
    )

    # Module-level channels that mutate without going through `os`.
    TEMPFILE_MUTATORS = ("mkstemp", "NamedTemporaryFile", "mkdtemp")
    SHUTIL_MUTATORS = ("copyfileobj", "copyfile", "copy2", "move",
                        "rmtree", "copytree", "copymode")

    def __init__(self, engine):
        self.engine = engine
        self.real_os = engine.os
        self.real_helpers = {}
        self.real_tempfile = getattr(engine, "tempfile", None)
        self.real_shutil = getattr(engine, "shutil", None)
        self.real_builtin_open = builtins.open
        self.mutations = []

    def __enter__(self):
        tripwire = self

        def note(kind, args):
            tripwire.mutations.append(
                (kind, [str(a) for a in args[:2]]))

        class _OsProxy:
            """Forwards everything; intercepts only mutating names/args."""

            def __getattr__(self, name):
                real = getattr(tripwire.real_os, name)
                if name in tripwire.MUTATORS:
                    def intercepted(*args, **kwargs):
                        note("os." + name, args)
                        return real(*args, **kwargs)
                    return intercepted
                if name == "open":
                    def intercepted_open(*args, **kwargs):
                        flags = args[1] if len(args) > 1 else 0
                        if tripwire._is_write_flags(flags):
                            note("os.open", args)
                        return real(*args, **kwargs)
                    return intercepted_open
                if name == "fdopen":
                    def intercepted_fdopen(*args, **kwargs):
                        mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")
                        if tripwire._is_write_mode(mode):
                            note("os.fdopen", args)
                        return real(*args, **kwargs)
                    return intercepted_fdopen
                return real

        self.engine.os = _OsProxy()

        class _ModuleProxy:
            """Forwards everything; intercepts only the mutating names."""

            def __init__(self, real, names):
                self._real = real
                self._names = names

            def __getattr__(self, name):
                real_attr = getattr(self._real, name)
                if name in self._names:
                    def intercepted(*args, **kwargs):
                        note(self._prefix + "." + name, args)
                        return real_attr(*args, **kwargs)
                    return intercepted
                return real_attr

        if self.real_tempfile is not None:
            proxy = _ModuleProxy(self.real_tempfile, self.TEMPFILE_MUTATORS)
            proxy._prefix = "tempfile"
            self.engine.tempfile = proxy
        if self.real_shutil is not None:
            proxy = _ModuleProxy(self.real_shutil, self.SHUTIL_MUTATORS)
            proxy._prefix = "shutil"
            self.engine.shutil = proxy

        real_open = self.real_builtin_open

        def intercepted_builtin_open(*args, **kwargs):
            mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")
            # `builtins.open` is process-global, so unlike `pgrec.os` a
            # rebind cannot separate the engine from this test module by
            # namespace alone. Attributing by CALLER preserves the
            # separation: a write-capable open issued from a frame whose
            # globals are the engine module's dict is the engine's, and
            # the attacker's identical write from this module's frames is
            # not. Without this the zero-mutation result in G.1 would be
            # unreachable rather than earned.
            if self._is_write_mode(mode) and self._caller_is_engine():
                note("open", args)
            return real_open(*args, **kwargs)

        builtins.open = intercepted_builtin_open
        for name in self.WRITE_HELPERS:
            real = getattr(self.engine, name, None)
            if real is None:
                continue
            self.real_helpers[name] = real

            def make(name=name, real=real):
                def intercepted(*args, **kwargs):
                    note(name, args)
                    return real(*args, **kwargs)
                return intercepted

            setattr(self.engine, name, make())
        return self

    def __exit__(self, *exc_info):
        self.engine.os = self.real_os
        for name, real in self.real_helpers.items():
            setattr(self.engine, name, real)
        if self.real_tempfile is not None:
            self.engine.tempfile = self.real_tempfile
        if self.real_shutil is not None:
            self.engine.shutil = self.real_shutil
        builtins.open = self.real_builtin_open
        return False

    def kinds(self):
        return [kind for kind, _args in self.mutations]

    def _caller_is_engine(self):
        """True when the frame that issued `open` is an engine frame.

        Depth: 0 is this method, 1 is `intercepted_builtin_open`, and 2
        is the frame that actually called `open`.
        """
        try:
            frame = sys._getframe(2)
        except ValueError:  # pragma: no cover - shallow stack
            return False
        return frame.f_globals is self.engine.__dict__

    @classmethod
    def _is_write_flags(cls, flags):
        if not isinstance(flags, int) or isinstance(flags, bool):
            return True  # unknown flag shape: assume write-capable
        return any(flags & bit for bit in cls._WRITE_FLAGS)

    @classmethod
    def _is_write_mode(cls, mode):
        if not isinstance(mode, str):
            return True  # unknown mode shape: assume write-capable
        return bool(set(mode) & cls._WRITE_MODE_CHARS)


def test_g_a_denied_authority_mutates_nothing(tmp_path):
    """G.1 A replacement is refused or fully pinned, and never mutates.

    The two platforms reach those two outcomes by different routes and the
    proof must accept both, because requirement 7 is "complete pinning OR
    fail-closed", never an accepted mix. On Windows the engine re-identifies
    the coordinate after the reads and refuses, because the replacement
    changed the directory the coordinate names. On POSIX it does not need to:
    a pinned descriptor keeps naming the admitted generation even after the
    directory is renamed away, so the decision completes coherently on
    generation A.

    What this used to prove was weaker than its name. It compared only the
    resulting FILENAME SET, after the attacker had already replaced the whole
    directory, and its `fingerprint` loop variable was bound and then never
    asserted. A census of names cannot see a truncate, an in-place rewrite,
    a receipt edited outside the transitions directory, or a temporary file
    that was created and then removed again -- and generation B
    legitimately republishes the same two coordinates, so the comparison was
    comparing the attacker's work, not the engine's.

    So the mutation claim is now an executable tripwire. `_MutationTripwire`
    binds the ENGINE's `os` global and its durable-write helpers, and nothing
    else: the attacker's rename/mkdir/chmod run through the real `os` in this
    module and are structurally unobservable to it. Zero recorded mutations
    therefore means zero engine mutations, not "the names look unchanged".
    """
    transitions, _record, promote, receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    # The authority artifacts that live OUTSIDE the replaced directory, so
    # an edit to the promote receipt cannot hide behind the attacker's swap.
    outside_before = _census_outside(
        receipt.parent, transitions.name, transitions.name + ".aside")
    census_before = _census(pgrec._transitions_dir())

    with _MutationTripwire(pgrec) as trip:
        # A tripwire that silently failed to install would report zero
        # mutations and look exactly like a clean run, so prove it is LIVE:
        # the engine is currently routed through the proxy, not the real os.
        assert pgrec.os is not trip.real_os, (
            "the mutation tripwire was not installed on the engine")
        assert pgrec._write_transition_record is not trip.real_helpers[
            "_write_transition_record"], (
            "the durable-write helper tripwire was not installed")
        outcome, bundle = _capture(
            pgrec, OPID, promote,
            lambda: _swap_whole_directory(transitions, OPID, "finalize"))

    if outcome == "acquired":
        # A coherent pin to the OLD generation is a legal result, not a
        # defect, so it is accepted -- but only once the bundle is shown to be
        # internally consistent and still pinned to the admitted generation.
        assert not _cross_generation(bundle), (
            "a replacement yielded an accepted mixed-generation decision: "
            f"{_authority_pair(bundle)!r}")
        if bundle.record is not None:
            assert bundle.selector.governed_device == \
                bundle.record_snapshot.governed_device
            assert bundle.record.get("operation_id") == OPID
    else:
        assert isinstance(bundle, pgrec._ExecutionAuthorityConflict), bundle

    assert trip.mutations == [], (
        "the engine mutated durable authority during a read-only decision: "
        f"{trip.mutations!r}")

    # The census still has a job, but a smaller one: it proves the attacker's
    # replacement did not smuggle in a coordinate the engine invented, and
    # it is taken against the pre-swap census rather than against itself.
    after = set(_census(pgrec._transitions_dir()))
    assert after - set(census_before) == set(), (
        f"the engine created governed files: {sorted(after - set(census_before))}")

    # Byte-identical authority outside the replaced directory. The receipt
    # lives here, and the attacker's swap does not touch it, so this is a
    # real comparison rather than a restatement of the attack.
    assert _census_outside(
        receipt.parent, transitions.name,
        transitions.name + ".aside") == outside_before, (
        "an authority artifact outside the replaced directory changed")
    assert (receipt.parent / "promote-receipt.json").exists()


def test_g_a_the_mutation_tripwire_detects_a_real_engine_mutation(tmp_path):
    """G.2 A tripwire nobody has seen fire is not evidence.

    So the tripwire is required to fire, on a mutation the ENGINE makes:
    `_write_transition_record` is the production publisher of the durable
    transition record, and calling it directly performs a genuine write,
    a genuine os.replace and a genuine os.chmod through `pgrec.os`.
    """
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")

    with _MutationTripwire(pgrec) as trip:
        assert trip.mutations == []
        record["state"] = "PROMOTED"
        pgrec._write_transition_record(OPID, record)
        assert trip.mutations, (
            "the tripwire did not fire on a real engine write; every "
            "zero-mutation assertion built on it would be vacuous")
        kinds = trip.kinds()
        assert "_write_transition_record" in kinds, kinds
        # The syscall layer is wired too, not just the helper layer: the
        # engine's own durability primitives must appear.
        assert any(kind.startswith("os.") for kind in kinds), kinds

    # And it disarms cleanly, so a later test cannot inherit a live proxy.
    recorded = len(trip.mutations)
    pgrec._write_transition_record(OPID, record)
    assert len(trip.mutations) == recorded, "the tripwire stayed armed"
    assert pgrec.os is trip.real_os



def _engine_open_writer(engine, path):
    """Issue a write-capable builtin `open` FROM the engine module.

    `builtins.open` is process-global, so the tripwire attributes it by
    caller (see `_caller_is_engine`). The probe below is compiled with the
    ENGINE module's own globals dict -- that identity is exactly what the
    attribution compares -- so its frame is an engine frame and the write
    is recognised, while the same call from this test module is not.
    """
    name = "_r48x5_open_probe_%d" % id(path)
    source = (
        "def " + name + "(target):\n"
        "    with open(target, 'w', encoding='utf-8') as h:\n"
        "        h.write('engine-write')\n"
    )
    exec(compile(source, "<r48x5-engine-open-probe>", "exec"), engine.__dict__)
    try:
        engine.__dict__[name](str(path))
    finally:
        engine.__dict__.pop(name, None)

# ===================================================================== #
# H. TRIPWIRE COMPLETENESS
# ===================================================================== #

# The authority decision path this gate proves read-only. Every reachability
# question below is asked of exactly these three functions, because they are
# the ones `_MutationTripwire` is installed around.

# ===================================================================== #
# I. CLOSED-WORLD CALL-SITE AUDIT (B4-CXR7U9R48X6)
# ===================================================================== #

# X5 discovered mutation channels by ALLOWLIST: a call was reported only if
# its rendered spelling matched a selected os/tempfile/shutil/builtin list,
# and anything else was silently ignored. Measured on this engine, X5
# recognised 2 of 59 distinct external callees reachable from the authority
# entry points and ignored the other 57 -- 194 call sites. An injected
# `Path(target).write_text(...)` inside a reachable function therefore
# vanished from the audited set while H.1, H.2 and H.7 all stayed green.
#
# The audit below is closed-world in the only sense a static analysis can be:
# EVERY reachable call site is assigned exactly one classification, and a
# call matching no registry entry becomes UNKNOWN_OR_DYNAMIC, which fails the
# proof. A new attribute call can no longer disappear; it can only be
# reviewed and admitted.

AUTHORITY_ENTRY_POINTS = (
    "_acquire_recovery_authority",
    "_classify_record_for_shell",
    "_classify_rollback_for_shell",
)

CLASS_INTERNAL = "INTERNAL_CALL"
CLASS_READ_ONLY = "PROVEN_READ_ONLY_OR_PURE"
CLASS_MUTATION = "INSTRUMENTED_MUTATION_CHANNEL"
CLASS_UNKNOWN = "UNKNOWN_OR_DYNAMIC"

CLASSIFICATIONS = (CLASS_INTERNAL, CLASS_READ_ONLY, CLASS_MUTATION,
                   CLASS_UNKNOWN)


class _ClassifiedCall:
    """One reachable call site, classified exactly once."""

    __slots__ = ("owner", "lineno", "col", "callee", "expression",
                 "classification", "observer", "reason")

    def __init__(self, owner, lineno, callee, classification, observer=None,
                 col=0, expression=None, reason=""):
        self.owner = owner
        self.lineno = lineno
        self.col = col
        self.callee = callee
        self.expression = expression
        self.classification = classification
        self.observer = observer
        self.reason = reason

    @property
    def identity(self):
        """Stable identity: owner + rendered callee + line + column.

        Line alone is NOT sufficient: `pg-recovery.py:2518` reads
            and _receipt_digest(record) != _receipt_digest(admitted_record):
        and calls the same callee twice on one line. The column offset
        separates them, so the uniqueness assertion in `_assert_closed_world`
        is a real check rather than a formality. A shifted line or column
        changes the identity string; it never silently re-binds.
        """
        return f"{self.owner}|{self.callee}|{self.lineno}:{self.col}"

    def as_row(self):
        # X7: a refusal must name the owning function, the NORMALIZED call
        # expression, the source coordinate and the reason, so an operator can
        # adjudicate it without re-deriving the classifier's internals.
        return (f"{self.owner}:{self.lineno}:{self.col} {self.expression or self.callee} "
                f"{self.classification} observer={self.observer or '-'} "
                f"reason={self.reason or '-'}")

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"<{self.identity} {self.classification}>"


# Reviewed registry of external calls that provably do not mutate the
# filesystem on the authority decision path. This is a REVIEWED list, not a
# heuristic: entries are admitted deliberately and anything absent is
# UNKNOWN_OR_DYNAMIC. Justifications, at the level the classifier can
# actually guarantee:
#   * os.stat / os.fstat / os.lstat -- metadata read, no write descriptor;
#   * os.read / os.close -- consume or close an ALREADY OPEN descriptor;
#   * os.scandir / os.listdir -- enumeration;
#   * os.path.* / os.environ.get -- pure string or environment reads;
#   * stat.S_* -- pure mode-bit predicates;
#   * json.* / hashlib.* -- pure (de)serialisation and hashing;
#   * constructors, predicates and aggregation builtins.
#
# X7 CORRECTION. This registry used to carry BARE METHOD NAMES -- "get",
# "append", "update", "replace", "stat" and friends -- so ANY receiver could
# inherit read-only authority from a spelling alone. That admitted
# `Path(src).replace(dst)` (a filesystem rename) as the reviewed string
# operation "replace", and let any object named `external` or `sink` use
# .update/.append. Every bare method name has been REMOVED. Method calls are
# now admitted only as a reviewed (receiver, method) PAIR, or as a reviewed
# complete expression -- see REVIEWED_RECEIVER_METHODS below.
#
# The boundary this registry does NOT cross: it says nothing about code
# paths outside the authority closure, and it does not assert that a
# reviewed call is safe in general -- only that it performs no filesystem
# mutation at these call sites.
READ_ONLY_REGISTRY = frozenset({
    "os.stat", "os.fstat", "os.lstat",
    "os.read", "os.close",
    "os.scandir", "os.listdir",
    "os.path.abspath", "os.path.basename", "os.path.commonpath",
    "os.path.dirname", "os.path.isdir", "os.path.isfile", "os.path.join",
    "os.path.realpath", "os.path.samefile", "os.path.split",
    "os.path.exists", "os.path.lexists", "os.path.relpath",
    "os.environ.get", "os.getenv",
    "stat.S_IMODE", "stat.S_ISDIR", "stat.S_ISREG", "stat.S_ISLNK",
    "json.dumps", "json.load", "json.loads",
    "hashlib.sha256", "hashlib.sha1", "hashlib.md5", "hashlib.new",
    "len", "bool", "int", "str", "bytes", "float", "tuple", "list", "dict",
    "set", "frozenset", "sorted", "any", "all", "isinstance", "issubclass",
    "type", "repr", "range", "enumerate", "zip", "min", "max", "sum", "abs",
    "divmod", "round", "hasattr", "getattr", "id", "hash", "iter", "next",
    "callable", "chr", "ord",
    "RuntimeError", "ValueError", "TypeError", "OSError", "Exception",
    "NotImplementedError", "StopIteration",
})

# In-memory snapshot construction, reviewed and admitted separately so the
# reason for admission stays legible next to the registry.
PURE_CONSTRUCTORS = frozenset({
    "RecordSnapshot", "SelectorSnapshot", "RecoveryAuthoritySnapshot",
})

# Bare LOCAL names that hold a value looked up from a dispatch table. The
# callee is therefore not statically knowable from the spelling alone, and a
# bare name could in principle hold anything -- so admission is conditional
# on an executable proof, not on the name: `_assert_dispatch_is_pure`
# (test I.G) asserts that every value of the engine's `_STATE_DISPATCH` is a
# function DEFINED BY THE ENGINE, and each such handler's own body is audited
# by the closure walk because it is itself reachable.
#
# If the engine ever dispatched to a non-engine callable under one of these
# names, I.G fails and this admission is withdrawn with it.
REVIEWED_DISPATCH_LOCALS = frozenset({"handler"})


# X7: RECEIVER-BOUND METHOD ADMISSION.
#
# A method name alone proves nothing about what it mutates. `record.get` reads a
# dictionary; `Path(target).replace(other)` RENAMES A FILE and renders to the
# same attribute spelling. So admission is by the PAIR (receiver, method), where
# the receiver is the normalized name path at that call site.
#
# This set is MEASURED, not guessed: it is exactly the (receiver, method) pairs
# present in the 35-function authority closure at this head. Each entry is a
# deliberate review decision; a pair that appears anywhere else is refused.
REVIEWED_RECEIVER_METHODS = frozenset({
    # admitted JSON/dict reads on already-parsed, already-admitted material
    "record.get", "promote.get", "claim.get", "admitted_record.get",
    # the dispatch table lookup is the dynamic-dispatch seam; see I.G
    "_STATE_DISPATCH.get",
    # in-memory list construction for census/receipt payloads only
    "census.append", "chunks.append", "roots.append",
    # string predicates on an admitted record name
    "name.startswith", "name.endswith", "part.strip",
    # pure transforms on admitted values
    "value.items", "canonical.encode", "raw.decode",
    # os.DirEntry.stat -- metadata read on a directory entry; opens no
    # descriptor for writing and cannot mutate the tree.
    "entry.stat",
    # compiled-pattern match on the operation-id pattern object
    "OPERATION_ID_RE.match",
})

# Calls whose receiver is itself a CALL EXPRESSION. The receiver is normalized
# with its arguments elided (`f(...)`), so this admits one specific shape and
# refuses every other, including `Path(x).replace(y)`. Every entry was MEASURED
# against the closure at this head, not guessed from the owning function:
#   os.environ.get(...).split      -- read an env var, split it: pure
#   bytes.join(...).decode         -- join admitted byte chunks, decode: pure
#   hashlib.sha256(...).hexdigest  -- hash already-admitted bytes: pure
REVIEWED_EXPRESSION_RECEIVERS = frozenset({
    "os.environ.get(...).split",
    "bytes.join(...).decode",
    "hashlib.sha256(...).hexdigest",
})

# Receivers that are LITERALS (`b""`, `""`, `0`, ...). A literal cannot be
# rebound, so it cannot denote a filesystem object; `b", ".join(...)` is
# unambiguously an in-memory bytes join. Normalized to the literal's TYPE so
# every bytes literal shares one reviewed entry.
LITERAL_RECEIVER_METHODS = frozenset({
    "bytes.join", "str.join",
})


# X7X: RECEIVER-NAME BINDING PROVENANCE.
#
# X7 bound a reviewed METHOD to a reviewed receiver NAME. It did not bind that
# NAME to a VALUE, so the same failure X6 exposed one level up remained open:
# any binding form that rebinds a reviewed receiver name inherits the review
# outright. Measured against the classifier as shipped at df19763a3, ALL of
# these were ADMITTED as PROVEN_READ_ONLY_OR_PURE:
#
#     [record.get(k) for record in externals]   # comprehension target
#     {entry.stat() for entry in out}           # comprehension target
#     record, sink = unpacked(a); record.get(..)# tuple unpack
#     if (record := attacker): record.get(..)   # walrus
#     sorted(xs, key=lambda record: record.get)# lambda parameter
#     for record in attacker: record.get(..)    # for target
#     with attacker as record: record.get(..)   # with target
#
# A method call whose receiver is a TUPLE, NAMED EXPR, COMPREHENSION or
# LAMBDA already failed closed -- those shapes are refused as receivers. The
# hole was one level down: the SHAPE OF THE BINDING, not the shape of the
# receiver. This registry closes it.
#
# `REVIEWED_RECEIVER_BINDINGS` maps each reviewed receiver to the binding forms
# measured for that name across the 35-function closure. It is a FROZEN literal
# -- the reviewed baseline, not a value recomputed from whatever source is
# being audited -- so an injected binding form cannot define itself admissible.
# `REVIEWED_RECEIVER_SITES` then narrows admission to the specific
# (owner, receiver, method) triples measured at this head, because a name that
# legitimately unpacks a tuple SOMEWHERE must not inherit that tolerance
# EVERYWHERE.
REVIEWED_RECEIVER_BINDINGS = {
    "OPERATION_ID_RE": frozenset(),
    "_STATE_DISPATCH": frozenset(),
    "admitted_record": frozenset({"assign"}),
    "canonical": frozenset({"assign"}),
    "census": frozenset({"assign"}),
    "chunks": frozenset({"assign"}),
    "claim": frozenset({"assign", "assign-unpack"}),
    "entry": frozenset({"for"}),
    "name": frozenset({"assign", "assign-unpack", "for-unpack", "param"}),
    "part": frozenset({"for"}),
    "promote": frozenset({"assign", "param"}),
    "raw": frozenset({"assign", "assign-unpack"}),
    "record": frozenset({"assign", "assign-unpack", "param"}),
    "roots": frozenset({"assign"}),
    "value": frozenset({"param"}),
}

# Measured, not guessed: every (owner, receiver, method) triple admitted by the
# rule above at this head. 27 entries, 40 call sites. Anything else -- the same
# receiver name used in a function that did not review it -- is refused.
REVIEWED_RECEIVER_SITES = frozenset({
    ("_acquire_recovery_authority", "OPERATION_ID_RE", "match"),
    ("_acquire_recovery_authority", "admitted_record", "get"),
    ("_approved_roots", "part", "strip"),
    ("_approved_roots", "roots", "append"),
    ("_assert_record_authority_names", "census", "append"),
    ("_assert_record_authority_names", "name", "startswith"),
    ("_assert_record_identity", "record", "get"),
    ("_assert_selector_authority_names", "census", "append"),
    ("_assert_selector_authority_names", "entry", "stat"),
    ("_assert_selector_authority_names", "name", "endswith"),
    ("_assert_selector_authority_names", "name", "startswith"),
    ("_bound_operation", "OPERATION_ID_RE", "match"),
    ("_bound_operation", "promote", "get"),
    ("_bound_operation", "record", "get"),
    ("_classify_claim_content", "claim", "get"),
    ("_classify_record_for_shell", "OPERATION_ID_RE", "match"),
    ("_classify_record_for_shell", "_STATE_DISPATCH", "get"),
    ("_classify_record_for_shell", "record", "get"),
    ("_classify_rollback_for_shell", "promote", "get"),
    ("_deep_freeze", "value", "items"),
    ("_derive_claim_coordinate", "OPERATION_ID_RE", "match"),
    ("_derive_record_coordinate_name", "OPERATION_ID_RE", "match"),
    ("_read_admitted_claim", "chunks", "append"),
    ("_read_admitted_record", "chunks", "append"),
    ("_read_admitted_record", "raw", "decode"),
    ("_receipt_digest", "canonical", "encode"),
    ("_thaw", "value", "items"),
})


# Every binding-form label `_binding_form_index` can emit. Used by the K.K
# loosening (which must permit every form, not merely the ones the engine
# happens to use today) and asserted against the walker in K.J so the list
# cannot rot into permitting less than it claims.
ALL_BINDING_FORMS = frozenset({
    "assign", "assign-unpack", "augassign", "annassign", "walrus",
    "for", "for-unpack", "comprehension", "comprehension-unpack",
    "with", "with-unpack", "except", "param", "lambda-param",
    # X9: PEP 695 type parameters are real lexical bindings, visible inside
    # the generic function body, so they are a binding FORM like any other.
    "type-param",
})


# X8: EXACT CALL-SITE AND BINDING AUTHORITY.
#
# The X7 and X7X rules both authorize a REVIEWED SPELLING. X7 authorized a
# (receiver, method) pair anywhere; X7X narrowed that to a
# (owner, receiver, method) triple plus reviewed binding forms. Neither binds
# the review to the INDIVIDUAL SOURCE SITE, so all of these are still admitted:
#
#     roots.append(payload)          # a SECOND call in the owner that owns it
#     roots = attacker; roots.append(payload)   # receiver rebound by an
#                                               # already-reviewed form
#     os = attacker; os.stat(path)   # the module NAME is shadowed
#     hashlib = attacker; hashlib.sha256(b"x")
#     RecordSnapshot = attacker; RecordSnapshot(record)
#     _transitions_dir = attacker; _transitions_dir()
#
# The last four are the substantive ones: EVERY spelling-based rule in this
# file matches identifier strings, so assigning to a name defeats it. A name
# that has been reassigned is not the thing the review was about, and no
# amount of string comparison can tell.
#
# So authority is bound to the exact site AND to the source context that gives
# the receiver its meaning:
#
#   * EXACT_SITE_MANIFEST records, per (owner function, normalized call
#     expression), the exact number of times that call occurs in the reviewed
#     source. A new call, or a DUPLICATE of an approved one, changes the count.
#   * REVIEWED_OWNER_DIGESTS records a coordinate-independent digest of each
#     owning function's AST. Any change to the owner -- a rebinding, a
#     shadowing assignment, an added or duplicated call, a reordering --
#     changes the digest and withdraws every grant in that owner.
#
# The digest is a deterministic serialisation of the owning function's AST:
# node kinds plus the frozen `_STABLE_AST_FIELDS` schema, emitted in the
# PROOF's sorted field order (X9: never the interpreter's `_fields` order) and
# encoded as structured JSON. Line and column numbers are never emitted, so it
# is stable under line and column shifts and cannot be satisfied by
# re-indenting, while changing under every semantic edit -- a bare rename
# (which the vocabulary once could not see, having omitted `id`) and a PEP 695
# type parameter (which the first version-normalisation repair dropped as
# "interpreter metadata") included. Coordinates REMAIN DIAGNOSTIC ONLY. The
# digest is intentionally coarse and fail-closed: it does not model what each
# name holds, it refuses when anything in the owner changed, and an AST field
# outside the schema raises `_UnreviewedAstFieldError` instead of being
# silently ignored.
#
# Interpreter stability is a REQUIREMENT rather than a nicety, and it was
# learned the hard way. The first implementation used `ast.dump`, which is a
# function of the source AND the interpreter: CPython 3.12 appended
# `type_params` to `FunctionDef._fields`, so every frozen digest moved on the
# Linux runner while every 3.11 local run stayed green -- same source, same
# coordinates, same 312 reachable call sites, only the serialisation differed.
# X8's repair then over-corrected: it kept the digest stable across versions by
# DROPPING `type_params` and by consuming the interpreter's field order. X9
# normalises the VALUE instead (`[]` for a non-generic definition on either
# interpreter) and emits in a proof-controlled order, so the digest is stable
# where it must be and sensitive where it must be. M.A..M.F and the N section
# prove both directions, and an unreviewed field is RED rather than invisible.
#
# Both registries are FROZEN literals measured from the shipped engine. An
# audited source is judged against them, never against itself.
#
# Stated boundary: this is NOT semantic type resolution. It is exact-site and
# exact-owner-context binding. It does not prove that `record` holds a dict --
# it proves that the site is the reviewed one in the reviewed owner and that
# the owner has not been edited. Stated rather than implied.
EXACT_SITE_MANIFEST = {
    ("_acquire_recovery_authority", "OPERATION_ID_RE.match"): 1,
    ("_acquire_recovery_authority", "RecordSnapshot"): 1,
    ("_acquire_recovery_authority", "RecoveryAuthoritySnapshot"): 1,
    ("_acquire_recovery_authority", "_ExecutionAuthorityConflict"): 2,
    ("_acquire_recovery_authority", "_assert_one_directory_generation"): 1,
    ("_acquire_recovery_authority", "_assert_record_identity"): 1,
    ("_acquire_recovery_authority", "_deep_freeze"): 1,
    ("_acquire_recovery_authority", "_derive_claim_coordinate"): 1,
    ("_acquire_recovery_authority", "_derive_record_coordinate_name"): 1,
    ("_acquire_recovery_authority", "_open_governed_directory"): 1,
    ("_acquire_recovery_authority", "_read_record_snapshot_admitted"): 1,
    ("_acquire_recovery_authority", "_read_selector_snapshot_admitted"): 1,
    ("_acquire_recovery_authority", "_receipt_digest"): 3,
    ("_acquire_recovery_authority", "admitted_record.get"): 1,
    ("_acquire_recovery_authority", "isinstance"): 2,
    ("_acquire_recovery_authority", "os.close"): 1,
    ("_acquire_recovery_authority", "os.path.join"): 1,
    ("_admit_record_descriptor", "_assert_record_authority_names"): 1,
    ("_admit_record_descriptor", "_record_conflict"): 7,
    ("_admit_record_descriptor", "bool"): 2,
    ("_admit_record_descriptor", "getattr"): 2,
    ("_admit_record_descriptor", "os.fstat"): 2,
    ("_admit_record_descriptor", "os.path.basename"): 1,
    ("_admit_record_descriptor", "os.stat"): 1,
    ("_admit_record_descriptor", "stat.S_IMODE"): 1,
    ("_admit_record_descriptor", "stat.S_ISREG"): 1,
    ("_admit_selector_descriptor", "_assert_selector_authority_names"): 1,
    ("_admit_selector_descriptor", "_selector_conflict"): 7,
    ("_admit_selector_descriptor", "bool"): 2,
    ("_admit_selector_descriptor", "getattr"): 2,
    ("_admit_selector_descriptor", "os.fstat"): 2,
    ("_admit_selector_descriptor", "os.stat"): 1,
    ("_admit_selector_descriptor", "stat.S_IMODE"): 1,
    ("_admit_selector_descriptor", "stat.S_ISREG"): 1,
    ("_approved_roots", "os.environ.get"): 1,
    ("_approved_roots", "os.environ.get(...).split"): 1,
    ("_approved_roots", "os.path.dirname"): 2,
    ("_approved_roots", "os.path.isdir"): 1,
    ("_approved_roots", "os.path.join"): 1,
    ("_approved_roots", "os.path.realpath"): 2,
    ("_approved_roots", "part.strip"): 1,
    ("_approved_roots", "roots.append"): 1,
    ("_assert_one_directory_generation", "_record_conflict"): 7,
    ("_assert_one_directory_generation", "bool"): 1,
    ("_assert_one_directory_generation", "getattr"): 1,
    ("_assert_one_directory_generation", "os.fstat"): 1,
    ("_assert_one_directory_generation", "os.stat"): 1,
    ("_assert_one_directory_generation", "stat.S_ISDIR"): 1,
    ("_assert_record_authority_names", "_record_conflict"): 4,
    ("_assert_record_authority_names", "census.append"): 2,
    ("_assert_record_authority_names", "len"): 2,
    ("_assert_record_authority_names", "name.startswith"): 1,
    ("_assert_record_authority_names", "os.listdir"): 1,
    ("_assert_record_authority_names", "os.stat"): 1,
    ("_assert_record_authority_names", "stat.S_IMODE"): 1,
    ("_assert_record_authority_names", "stat.S_ISREG"): 1,
    ("_assert_record_identity", "_record_conflict"): 3,
    ("_assert_record_identity", "isinstance"): 1,
    ("_assert_record_identity", "record.get"): 2,
    ("_assert_selector_authority_names", "_claim_temp_prefix"): 1,
    ("_assert_selector_authority_names", "_selector_conflict"): 5,
    ("_assert_selector_authority_names", "census.append"): 1,
    ("_assert_selector_authority_names", "entry.stat"): 1,
    ("_assert_selector_authority_names", "len"): 2,
    ("_assert_selector_authority_names", "name.endswith"): 1,
    ("_assert_selector_authority_names", "name.startswith"): 1,
    ("_assert_selector_authority_names", "os.scandir"): 1,
    ("_assert_selector_authority_names", "stat.S_IMODE"): 1,
    ("_assert_selector_authority_names", "stat.S_ISREG"): 1,
    ("_bound_operation", "OPERATION_ID_RE.match"): 1,
    ("_bound_operation", "RuntimeError"): 4,
    ("_bound_operation", "_load_transition_record"): 1,
    ("_bound_operation", "_receipt_digest"): 1,
    ("_bound_operation", "isinstance"): 1,
    ("_bound_operation", "promote.get"): 2,
    ("_bound_operation", "record.get"): 3,
    ("_claim_state", "_classify_claim_content"): 1,
    ("_claim_state", "_read_selector_snapshot"): 1,
    ("_classify_claim_content", "any"): 1,
    ("_classify_claim_content", "claim.get"): 4,
    ("_classify_claim_content", "isinstance"): 2,
    ("_classify_claim_content", "len"): 1,
    ("_classify_claim_coordinate", "_selector_conflict"): 4,
    ("_classify_claim_coordinate", "bool"): 1,
    ("_classify_claim_coordinate", "getattr"): 1,
    ("_classify_claim_coordinate", "os.stat"): 1,
    ("_classify_claim_coordinate", "stat.S_IMODE"): 1,
    ("_classify_claim_coordinate", "stat.S_ISREG"): 1,
    ("_classify_record_coordinate", "_record_conflict"): 4,
    ("_classify_record_coordinate", "bool"): 1,
    ("_classify_record_coordinate", "getattr"): 1,
    ("_classify_record_coordinate", "os.stat"): 1,
    ("_classify_record_coordinate", "stat.S_IMODE"): 1,
    ("_classify_record_coordinate", "stat.S_ISREG"): 1,
    ("_classify_record_for_shell", "OPERATION_ID_RE.match"): 1,
    ("_classify_record_for_shell", "_STATE_DISPATCH.get"): 1,
    ("_classify_record_for_shell", "_acquire_recovery_authority"): 1,
    ("_classify_record_for_shell", "_claim_state"): 1,
    ("_classify_record_for_shell", "handler"): 1,
    ("_classify_record_for_shell", "isinstance"): 2,
    ("_classify_record_for_shell", "record.get"): 3,
    ("_classify_rollback_for_shell", "_bound_operation"): 1,
    ("_classify_rollback_for_shell", "_classify_record_for_shell"): 1,
    ("_classify_rollback_for_shell", "_load_receipt"): 1,
    ("_classify_rollback_for_shell", "isinstance"): 1,
    ("_classify_rollback_for_shell", "promote.get"): 4,
    ("_deep_freeze", "_FrozenDict"): 1,
    ("_deep_freeze", "_deep_freeze"): 3,
    ("_deep_freeze", "frozenset"): 1,
    ("_deep_freeze", "isinstance"): 3,
    ("_deep_freeze", "tuple"): 1,
    ("_deep_freeze", "value.items"): 1,
    ("_derive_claim_coordinate", "OPERATION_ID_RE.match"): 1,
    ("_derive_claim_coordinate", "_ExecutionAuthorityConflict"): 1,
    ("_derive_claim_coordinate", "_transitions_dir"): 1,
    ("_derive_claim_coordinate", "isinstance"): 1,
    ("_derive_record_coordinate_name", "OPERATION_ID_RE.match"): 1,
    ("_derive_record_coordinate_name", "_record_conflict"): 3,
    ("_derive_record_coordinate_name", "isinstance"): 1,
    ("_derive_record_coordinate_name", "os.path.basename"): 1,
    ("_load_receipt", "_validated_open_path"): 1,
    ("_load_receipt", "json.load"): 1,
    ("_load_receipt", "open"): 1,
    ("_load_transition_record", "RuntimeError"): 1,
    ("_load_transition_record", "_transitions_dir"): 1,
    ("_load_transition_record", "json.load"): 1,
    ("_load_transition_record", "open"): 1,
    ("_load_transition_record", "os.path.isfile"): 1,
    ("_load_transition_record", "os.path.join"): 1,
    ("_open_claim_descriptor", "_selector_conflict"): 2,
    ("_open_claim_descriptor", "os.open"): 2,
    ("_open_governed_directory", "_ExecutionAuthorityConflict"): 6,
    ("_open_governed_directory", "getattr"): 1,
    ("_open_governed_directory", "os.close"): 2,
    ("_open_governed_directory", "os.fstat"): 1,
    ("_open_governed_directory", "os.open"): 1,
    ("_open_governed_directory", "os.stat"): 1,
    ("_open_governed_directory", "stat.S_ISDIR"): 2,
    ("_read_admitted_claim", "_selector_conflict"): 5,
    ("_read_admitted_claim", "bytes.join"): 1,
    ("_read_admitted_claim", "bytes.join(...).decode"): 1,
    ("_read_admitted_claim", "chunks.append"): 1,
    ("_read_admitted_claim", "json.loads"): 1,
    ("_read_admitted_claim", "len"): 1,
    ("_read_admitted_claim", "os.fstat"): 2,
    ("_read_admitted_claim", "os.read"): 1,
    ("_read_admitted_record", "_record_conflict"): 5,
    ("_read_admitted_record", "bytes.join"): 1,
    ("_read_admitted_record", "chunks.append"): 1,
    ("_read_admitted_record", "json.loads"): 1,
    ("_read_admitted_record", "len"): 1,
    ("_read_admitted_record", "os.fstat"): 2,
    ("_read_admitted_record", "os.read"): 1,
    ("_read_admitted_record", "raw.decode"): 1,
    ("_read_record_snapshot_admitted", "RecordSnapshot"): 2,
    ("_read_record_snapshot_admitted", "_admit_record_descriptor"): 1,
    ("_read_record_snapshot_admitted", "_classify_record_coordinate"): 1,
    ("_read_record_snapshot_admitted", "_deep_freeze"): 1,
    ("_read_record_snapshot_admitted", "_read_admitted_record"): 1,
    ("_read_record_snapshot_admitted", "_receipt_digest"): 1,
    ("_read_record_snapshot_admitted", "_record_conflict"): 4,
    ("_read_record_snapshot_admitted", "hashlib.sha256"): 1,
    ("_read_record_snapshot_admitted", "hashlib.sha256(...).hexdigest"): 1,
    ("_read_record_snapshot_admitted", "isinstance"): 1,
    ("_read_record_snapshot_admitted", "os.close"): 2,
    ("_read_record_snapshot_admitted", "os.open"): 2,
    ("_read_record_snapshot_admitted", "os.path.join"): 1,
    ("_read_record_snapshot_admitted", "os.stat"): 1,
    ("_read_record_snapshot_admitted", "stat.S_IMODE"): 1,
    ("_read_selector_snapshot", "_derive_claim_coordinate"): 1,
    ("_read_selector_snapshot", "_open_governed_directory"): 1,
    ("_read_selector_snapshot", "_read_selector_snapshot_admitted"): 1,
    ("_read_selector_snapshot", "os.close"): 1,
    ("_read_selector_snapshot_admitted", "SelectorSnapshot"): 2,
    ("_read_selector_snapshot_admitted", "_admit_selector_descriptor"): 1,
    ("_read_selector_snapshot_admitted", "_classify_claim_coordinate"): 1,
    ("_read_selector_snapshot_admitted", "_deep_freeze"): 1,
    ("_read_selector_snapshot_admitted", "_open_claim_descriptor"): 1,
    ("_read_selector_snapshot_admitted", "_read_admitted_claim"): 1,
    ("_read_selector_snapshot_admitted", "_selector_conflict"): 2,
    ("_read_selector_snapshot_admitted", "os.close"): 2,
    ("_read_selector_snapshot_admitted", "os.path.join"): 1,
    ("_read_selector_snapshot_admitted", "os.stat"): 1,
    ("_read_selector_snapshot_admitted", "stat.S_IMODE"): 1,
    ("_receipt_digest", "_thaw"): 1,
    ("_receipt_digest", "canonical.encode"): 1,
    ("_receipt_digest", "hashlib.sha256"): 1,
    ("_receipt_digest", "hashlib.sha256(...).hexdigest"): 1,
    ("_receipt_digest", "json.dumps"): 1,
    ("_record_conflict", "_selector_conflict"): 1,
    ("_recovery_state_dir", "os.path.dirname"): 2,
    ("_recovery_state_dir", "os.path.join"): 1,
    ("_recovery_state_dir", "os.path.realpath"): 1,
    ("_selector_conflict", "_ExecutionAuthorityConflict"): 1,
    ("_thaw", "_thaw"): 3,
    ("_thaw", "isinstance"): 3,
    ("_thaw", "sorted"): 1,
    ("_thaw", "value.items"): 1,
    ("_transitions_dir", "_recovery_state_dir"): 1,
    ("_transitions_dir", "os.path.join"): 1,
    ("_validated_open_path", "RuntimeError"): 3,
    ("_validated_open_path", "_approved_roots"): 1,
    ("_validated_open_path", "os.path.abspath"): 1,
    ("_validated_open_path", "os.path.commonpath"): 1,
    ("_validated_open_path", "os.path.isfile"): 1,
    ("_validated_open_path", "os.path.realpath"): 1,
}

REVIEWED_OWNER_DIGESTS = {
    "_acquire_recovery_authority": "0c98d9b8d827fb4dd49cbd239c48a8c96611275fa939120e29ba6876b01e9fd6",
    "_admit_record_descriptor": "7c5c5b4012800269bcacabe8d2242e9521ff39eac3cd9e60b743e9648e1f975b",
    "_admit_selector_descriptor": "bf74584ee9193b2086d828bcfe3114dc02bd0c141f198ef2602f267ec75d66aa",
    "_approved_roots": "492217c17be9f824bb628ce687c84595a13de6db5e983a7ae58f774d07fd21d7",
    "_assert_one_directory_generation": "e02c03e360532228355e395e14a7ed1c577f6254ee00b4e2bf952d7f776666e3",
    "_assert_record_authority_names": "a64d56ebebf4b5d23e9a5d1a976575b571d7c3066e774c872f653ca494b02d71",
    "_assert_record_identity": "30f4b2151634e9aa5c7fe9a20b9982ed620084b13eca56cfdff3df2ae6b9492c",
    "_assert_selector_authority_names": "b94ab968c36273497e14fefb2fb323d9a1f06b74553614f2b05a935149a27621",
    "_bound_operation": "e9473252ff37bfbf0e5733a35bb5b30f262f0fd09a498efa5a98feb620c491c2",
    "_claim_state": "2bbe63cb409fabea054bca9b5347ea0789eba28583a9aec9eda3e7aa0aaceea3",
    "_claim_temp_prefix": "0f6ec973493f1f2842b8be2a1e55d38e8ec379da597e9861bbf4de14044af297",
    "_classify_claim_content": "932d7f2cc05ee16a99cc9844248dde7409488148d007c7bc9034e2fc9ef21b4d",
    "_classify_claim_coordinate": "1f75f29e38c238a42332b3a6d8c6c6d4436ce1baaebc9617fe0f9898bbd951f9",
    "_classify_record_coordinate": "8a0b3303ed547cf35b3765a152f562015a0a03dc598e157118e2dfd674a61208",
    "_classify_record_for_shell": "0b7103d69d7e417ef27230dd3121a51c0a5449e55e07e0d0616de215d3708c21",
    "_classify_rollback_for_shell": "3a18b78e49031528eaeeede3e89545a5ba62297fabc546dd89777e9275b031a0",
    "_deep_freeze": "6b84107ffda5ded2ac8da6682159c17cb481d04a20219afd7ef451d0df1521e3",
    "_derive_claim_coordinate": "85c49e8375a54b65a46ba2f423d16ad973d76e01bcf016f3ab589877f2701716",
    "_derive_record_coordinate_name": "6d438cc609f9a9e7fe22d0809453d726ab5a22e00729686372fdcbd7428de542",
    "_load_receipt": "943586a4364bd0fab24cb842ba8fec3999911bc172c4367083983531d1092378",
    "_load_transition_record": "b89ac1d62913f8424e590751c242f658fdb509d3d6331c08716f1d2c9351011b",
    "_open_claim_descriptor": "7dd82c4542821a6b911bae4722a9924c63f74117ea5a511d033305e7e4040138",
    "_open_governed_directory": "000cb3effaea45b52157512cf52f784cdbd9a304f37dccaf130c670a35e1e491",
    "_read_admitted_claim": "eacbd081851e5c9f91980321655a66596698b3ade16070aead4ef33d5d8653b7",
    "_read_admitted_record": "3cd984cdffa2452b0a42a570a26878c440cb2b4114867624e66f399802b9cd85",
    "_read_record_snapshot_admitted": "aea435e83a95ee35af761c8c39e56f14c4ce14628b24b5aedf9b1827ffe4e445",
    "_read_selector_snapshot": "6e7c48c7eed3bfb167d1d1464f5b4ce021b7b7357ffc7f693408a5077296cd91",
    "_read_selector_snapshot_admitted": "f156b22e1f5d94000cf8e9deaebedb2b3735c1e533fe24dbf6f2f2d0884340c5",
    "_receipt_digest": "d730dd1640f1cf63ff7caa2509e7f47fd40a859f0368a8179bfa1e6da65fe947",
    "_record_conflict": "ecc88e205c2be4b73f4968858aaaecc1c090a8260ee80e5f188fecde6115bab6",
    "_recovery_state_dir": "3635ff44957b90149481871d450fd576f14cf4299dc3b6205dcefbbeea351910",
    "_selector_conflict": "c999265408c0f49d9743c3494a3c715c1f6f40dfb41476496818ef3a72777087",
    "_thaw": "7c0a21a0576ef2d642149dfed8c527ac209b1d3b8ca721fcc8f083484457f67c",
    "_transitions_dir": "1454fa64360fc9a50a7c3ef8b88b1df8ed370fb5ec07031b5fe1459efbe73c0a",
    "_validated_open_path": "8b5ab6b43195b0ed26b01c9d5d2c8f72a2445034a8444f958ba826945199dfd3",
}


# The canonical serializer's schema: the meaning-bearing AST field names the
# owner digest may read. FROZEN, deliberately, and FAIL-CLOSED in both
# directions.
#
# This started as `ast.dump`, and that was a defect with exactly the shape this
# mission exists to find: `ast.dump` is not interpreter-stable, because CPython
# 3.12 added `type_params` to function and class definitions. So the dump of a
# `FunctionDef` silently gained a field, and every frozen digest became a claim
# about the PYTHON VERSION rather than about the source.
#
# That is what turned the Linux runner red -- 33 failed, 704 passed -- while
# every local run stayed green, with the SAME source, the SAME coordinates and
# the SAME 312 reachable call sites. The parse agreed on both interpreters and
# only the serialisation differed. `ast.dump` was therefore a second, hidden
# baseline whose value depended on where the proof was executed, which is not a
# property a reviewed baseline may have.
#
# X9 CORRECTION of the first repair. That repair read this frozen allow-list,
# iterated `ast.iter_fields` in the interpreter's own field order, and DROPPED
# any field the list did not name -- including `type_params`, which it
# documented as "merely interpreter metadata" that "cannot change what a NAME
# in the owner means". Both claims were false. PEP 695 type parameters are
# real lexical bindings visible inside the function body, so `def f[os]():
# os.stat(path)` resolves `os` to the TYPE PARAMETER. The dropped field made
# that change invisible to the owner digest and to the binding walker while
# the manifest, the occurrence count and the module-head string all stayed
# unchanged; and the field ORDER the serializer consumed was still the
# interpreter's, so permuting `_fields` (same values, same source) moved the
# digest. Reproduced against the shipped X8 implementation before this repair:
#
#   A. digest with type_params=[os]       dbb47ffe4249a39e... (unchanged)
#   B. binding walker reported `os`       no
#   C. manifest / occurrence count        unchanged (1)
#   D. `os.stat` verdict                  PROVEN_READ_ONLY_OR_PURE
#   E. `RecordSnapshot` shadow            "reviewed pure constructor"
#      `_transitions_dir` shadow          INTERNAL_CALL, unchanged
#   F. swap FunctionDef._fields[0:2]      c649a4c9df70b303... ->
#                                         4953c178717f43fe... (values equal)
#   G. unknown Call field `default_value` digest identical for two different
#                                         values while `ast.dump` moved -- the
#                                         serializer was silently blind
#
# The law this schema now implements:
#
#   1. the field SET is closed: a field not named here RAISES
#      `_UnreviewedAstFieldError` naming the node type and the field, so a
#      future interpreter's addition is RED until an operator reviews it --
#      never silently invisible;
#   2. the field ORDER is the PROOF's: fields are emitted in sorted-name
#      order, never in `node._fields` order, so interpreter ordering cannot
#      move the digest;
#   3. version normalisation is done on the VALUE: an interpreter whose nodes
#      lack `type_params` (3.11) synthesises [], and an interpreter that
#      carries it natively (3.12+) yields [] for a non-generic definition --
#      the same canonical value by two routes;
#   4. the encoding is STRUCTURED (JSON, every value tagged by type) rather
#      than undelimited concatenation, so distinct trees cannot collide by
#      juxtaposition;
#   5. coordinates are never emitted, so line and column shifts stay neutral.
#
# Stated boundary: "validated on CPython 3.11 and 3.12". No arbitrary
# future-version independence is claimed -- a new field or a new AST kind is a
# review decision, which is the point.
_STABLE_AST_FIELDS = frozenset({
    "arg", "annotation", "args", "asname", "attr", "bases", "body",
    "bound",
    "cases", "cause", "comparators", "context_expr", "conversion", "ctx",
    "decorator_list", "decorators", "defaults", "elt", "elts", "exc",
    "finalbody", "format_spec", "func", "generators", "guard", "handlers",
    "id", "ifs", "is_async", "items", "iter", "key", "keys", "keywords",
    "kind", "kw_defaults", "kwarg", "kwonlyargs", "left", "level", "lower",
    "module",
    "msg", "n", "name", "names", "op", "operand", "ops", "optional_vars",
    "orelse",
    "pattern", "patterns", "posonlyargs", "rest", "returns", "right", "s",
    "simple", "slice", "step", "subject", "target", "targets", "test",
    "type", "type_comment", "type_params", "upper", "value", "values",
    "vararg",
})

# Node kinds whose interpreter-provided `_fields` gained `type_params` in 3.12
# (PEP 695). On an interpreter that lacks the field, the serializer supplies
# an empty list, so a non-generic definition has ONE canonical form.
_TYPE_PARAMETER_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_TYPE_PARAMS = "type_params"


class _UnreviewedAstFieldError(RuntimeError):
    """An AST field or value is neither in the canonical schema nor normalised.

    Fail-closed by construction: an interpreter that adds a meaning-bearing
    field must make the proof RED until an operator reviews it, rather than
    becoming silently invisible to the digest.
    """


def _canonical_field_value(node, field):
    """One field's canonical value, with `type_params` version-normalised.

    On 3.11 the attribute does not exist at all; a 3.11-shaped presentation
    may carry it as None. Both normalise to the 3.12 parser's empty list, so
    the canonical form of a non-generic definition does not depend on which
    interpreter produced the tree.
    """
    value = getattr(node, field, None)
    if field == _TYPE_PARAMS and value is None:
        return []
    return value


def _encode_ast_scalar(value, field, node_kind):
    """Tagged, structurally unambiguous encoding of one non-AST value."""
    if value is None:
        return {"none": True}
    if isinstance(value, bool):
        return {"bool": value}
    if isinstance(value, int):
        return {"int": str(value)}
    if isinstance(value, float):
        return {"float": repr(value)}
    if isinstance(value, complex):
        return {"complex": repr(value)}
    if isinstance(value, str):
        return {"str": value}
    if isinstance(value, bytes):
        return {"bytes": base64.b64encode(value).decode("ascii")}
    if value is Ellipsis:
        return {"ellipsis": True}
    raise _UnreviewedAstFieldError(
        f"{node_kind}.{field}: value of type {type(value).__name__} has no "
        f"canonical encoding; review it before this source can carry "
        f"authority")


def _encode_ast_value(value, field, node_kind):
    """Recursive canonical encoding: AST -> object, list -> array, scalar -> tag."""
    if isinstance(value, ast.AST):
        return {"node": type(value).__name__,
                "fields": _canonical_fields(value)}
    if isinstance(value, (list, tuple)):
        return [_encode_ast_value(item, field, node_kind) for item in value]
    return _encode_ast_scalar(value, field, node_kind)


def _canonical_fields(node):
    """`[(name, encoded)]` for one node: fixed order, fail-closed on unknowns.

    The ORDER is the proof's (sorted by field name), never the interpreter's
    `_fields` order, so permuting a class's `_fields` cannot move the digest.
    The SET is closed: a field outside `_STABLE_AST_FIELDS` raises instead of
    being silently dropped.
    """
    kind = type(node).__name__
    observed = {}
    for field in node._fields:
        if field not in _STABLE_AST_FIELDS:
            raise _UnreviewedAstFieldError(
                f"{kind}.{field}: AST field {field!r} on {kind} is not in the "
                f"canonical schema and is not a documented normalisation; it "
                f"may carry meaning, so the proof refuses to serialise this "
                f"source until an operator reviews the field")
        observed[field] = _canonical_field_value(node, field)
    if isinstance(node, _TYPE_PARAMETER_NODES) and _TYPE_PARAMS not in observed:
        if _TYPE_PARAMS not in _STABLE_AST_FIELDS:
            raise _UnreviewedAstFieldError(
                f"{kind}.{_TYPE_PARAMS}: the normalised field "
                f"{_TYPE_PARAMS!r} is missing from the canonical schema, so "
                f"PEP 695 type parameters would be invisible")
        observed[_TYPE_PARAMS] = []
    return [(name, _encode_ast_value(observed[name], name, kind))
            for name in sorted(observed)]


def _canonical_ast_serialization(node):
    """Deterministic, unambiguous, INTERPRETER-STABLE rendering of a subtree.

    The output is JSON built from a structured encoding: node kind names,
    field/value pairs in the PROOF's sorted order, tagged scalars, and lists
    as arrays. No concatenation of undelimited fragments is involved, so
    distinct trees cannot collide by juxtaposition, and no line or column
    number is ever emitted.
    """
    return json.dumps(
        {"node": type(node).__name__, "fields": _canonical_fields(node)},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _owner_ast_digest(node):
    """Coordinate-independent digest of an owning function's AST.

    Line and column numbers are excluded, so re-indenting or shifting the file
    does not change the digest. Every meaning-bearing field participates --
    including PEP 695 type parameters, which the first version-normalisation
    repair dropped -- and an unreviewed field raises instead of being silently
    ignored. Interpreter STABILITY across 3.11/3.12 comes from the value-level
    normalisation in `_canonical_field_value`, not from discarding anything:
    see `_STABLE_AST_FIELDS` for the stated law and its boundary.
    """
    canonical = _canonical_ast_serialization(node)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _audit_context(tree):
    """Everything the classifier needs about the source UNDER AUDIT.

    Rebuilt on every audit, so a monkeypatched registry is picked up and a
    weakened source reports its own counts and digests -- which is what lets
    them be compared against the frozen reviewed baseline.
    """
    funcs, closure = _authority_closure(tree)
    counts = {}
    for owner in closure:
        for call in ast.walk(funcs[owner]):
            if not isinstance(call, ast.Call):
                continue
            key = (owner, _normalized_call_expression(call))
            counts[key] = counts.get(key, 0) + 1
    return {
        "definitions": _engine_definitions(tree),
        "bindings": _receiver_binding_forms(funcs, closure),
        "type_params": _type_param_bindings(funcs, closure),
        "digests": {o: _owner_ast_digest(funcs[o]) for o in closure},
        "counts": counts,
        "funcs": funcs,
        "closure": closure,
    }


def _site_authority(owner, expr, context):
    """None when this exact site is reviewed; else the refusal reason.

    Three independent ways to fail, each naming the identity it compared, so
    an operator can tell "this call was never reviewed" from "this owner was
    edited" without re-deriving the classifier.
    """
    key = (owner, expr)
    expected = EXACT_SITE_MANIFEST.get(key)
    if expected is None:
        return (f"exact source site {key!r} is not in EXACT_SITE_MANIFEST, "
                f"so this {expr!r} call has no review decision of its own")
    observed = context["counts"].get(key, 0)
    if observed != expected:
        return (f"exact source site {key!r} occurs {observed} time(s) in the "
                f"source under audit but {expected} time(s) in the reviewed "
                f"manifest; a duplicate does not inherit the review")
    want = REVIEWED_OWNER_DIGESTS.get(owner)
    if want is None:
        return f"owner {owner!r} has no reviewed source digest"
    have = context["digests"].get(owner)
    if have != want:
        return (f"owner {owner!r} source context changed: reviewed digest "
                f"{want[:16]}..., observed {have[:16]}... -- a rebinding, "
                f"shadowing or edit withdraws every grant in this owner")
    return None


def _note_arg_names(args, form, note):
    """Record every name a signature binds under `form`."""
    for arg in (list(args.posonlyargs) + list(args.args)
                + list(args.kwonlyargs)):
        note(arg.arg, form)
    if args.vararg:
        note(args.vararg.arg, form)
    if args.kwarg:
        note(args.kwarg.arg, form)


def _type_parameter_name(node):
    """The bound identifier of ONE PEP 695 type parameter.

    CPython 3.12 documents `TypeVar(identifier name, expr? bound)`,
    `ParamSpec(identifier name)` and `TypeVarTuple(identifier name)`, so
    `name` is a plain string. Later interpreters moved it to an expression
    (`ast.Name`); both shapes are read, because a name this walker cannot see
    is a name that could shadow a reviewed one silently.
    """
    name = getattr(node, "name", None)
    if isinstance(name, str):
        return name
    if isinstance(name, ast.Name):
        return name.id
    return None


def _note_type_parameter_names(node, note):
    """Record every type parameter on a definition as a `type-param` binding.

    X9. Type parameters create a lexical scope inside the generic definition,
    so they can silently take over a name the classifier matches as a string
    (`os`, `hashlib`, a reviewed constructor, a module-level internal name, a
    reviewed receiver). Recording them here makes that collision visible to
    the binding proof and to `_type_param_shadow`.
    """
    for param in getattr(node, "type_params", None) or []:
        name = _type_parameter_name(param)
        if name:
            note(name, "type-param")


def _binding_form_index(node):
    """Every name BOUND anywhere inside `node`, mapped to its binding forms.

    X7X. Deliberately conservative: it collects forms for the WHOLE owning
    function, not just those dominating a particular call site, because the
    classifier has no value flow and a call site cannot prove which binding
    reached it. Refusing on ambiguity is the fail-closed direction.

    The forms are the ones that can rebind a name without the receiver's
    spelling changing: assignment (plain and container-target), augmented
    assignment, annotated assignment, walrus, for target (plain and unpacked),
    comprehension target (plain and unpacked), with target, except handler
    name, function parameter, and lambda parameter. A plain function parameter
    is tracked SEPARATELY from a lambda parameter on purpose -- `sorted(xs,
    key=lambda record: record.get(..))` binds `record` at a scope the caller
    never sees, and X7X requires it refused.
    """
    forms = {}

    def note(name, form):
        forms.setdefault(name, set()).add(form)

    def note_target(target, form):
        if isinstance(target, ast.Name):
            note(target.id, form)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                note_target(element, form + "-unpack")
        elif isinstance(target, ast.Starred):
            note_target(target.value, form + "-unpack")

    for sub in ast.walk(node):
        if isinstance(sub, ast.Assign):
            for target in sub.targets:
                note_target(target, "assign")
        elif isinstance(sub, ast.AugAssign):
            note_target(sub.target, "augassign")
        elif isinstance(sub, ast.AnnAssign):
            note_target(sub.target, "annassign")
        elif isinstance(sub, ast.NamedExpr):
            note_target(sub.target, "walrus")
        elif isinstance(sub, (ast.For, ast.AsyncFor)):
            note_target(sub.target, "for")
        elif isinstance(sub, ast.comprehension):
            note_target(sub.target, "comprehension")
        elif isinstance(sub, ast.withitem):
            if sub.optional_vars is not None:
                note_target(sub.optional_vars, "with")
        elif isinstance(sub, ast.ExceptHandler):
            if sub.name:
                note(sub.name, "except")
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _note_arg_names(sub.args, "param", note)
            _note_type_parameter_names(sub, note)
        elif isinstance(sub, ast.ClassDef):
            _note_type_parameter_names(sub, note)
        elif isinstance(sub, ast.Lambda):
            _note_arg_names(sub.args, "lambda-param", note)
    return forms


def _receiver_binding_forms(funcs, closure):
    """Per closure function: name -> frozenset of binding forms in that scope.

    Measured from the source BEING AUDITED, so a weakened or injected engine
    reports its own bindings and is judged against the frozen
    REVIEWED_RECEIVER_BINDINGS baseline rather than against itself.
    """
    out = {}
    for owner in closure:
        index = _binding_form_index(funcs[owner])
        out[owner] = {name: frozenset(forms)
                      for name, forms in index.items()}
    return out


def _type_param_bindings(funcs, closure):
    """Per closure function: the names bound by PEP 695 type parameters.

    Derived from the SAME measured binding index as the receiver forms, so
    the binding proof and the owner digest agree independently: a type
    parameter changes the digest (its content is serialised) AND appears here
    (its name is a binding), and either mechanism alone can refuse.
    """
    out = {}
    for owner in closure:
        index = _binding_form_index(funcs[owner])
        out[owner] = frozenset(
            name for name, forms in index.items() if "type-param" in forms)
    return out


def _referenced_names(call):
    """Every name the CALLABLE expression reads, receiver included.

    `os.stat` -> {"os"}; `record.get` -> {"record"}; `RecordSnapshot` -> its
    own bare name; `os.path.join` -> {"os"}. Arguments are deliberately not
    included: authority is about what the callee expression resolves to.
    """
    return {sub.id for sub in ast.walk(call.func)
            if isinstance(sub, ast.Name)}


def _type_param_shadow(owner, call, context):
    """The reviewed name(s) this owner's type parameters shadow, or None.

    X9, and deliberately INDEPENDENT of the owner digest: the refusal is
    computed from the measured binding inventory, so the diagnostic can name
    the actual binding form (`type-param`) and the shadowed name even if the
    digest rule were ever weakened by a later edit. A type parameter is a real
    lexical binding, so a generic definition cannot take authority for a name
    it re-binds -- `def f[os](): os.stat(path)` does NOT call the `os` module.
    """
    shadowed = context.get("type_params", {}).get(owner, frozenset())
    if not shadowed:
        return None
    hits = sorted(shadowed & _referenced_names(call))
    if not hits:
        return None
    return (f"type parameter(s) {hits!r} declared by {owner!r} create a "
            f"lexical binding with form 'type-param' that shadows the "
            f"reviewed name(s); a generic definition cannot take authority "
            f"for a name it re-binds")


def _qualified_callee(call):
    """Render `a.b.c(...)` as 'a.b.c'; a bare name as itself."""
    parts = []
    node = call.func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts)) if parts else None


def _normalized_expression(node):
    """Render an AST receiver canonically, with structure preserved.

    X7. `_qualified_callee` collapses `Path(src).replace(dst)` to the bare name
    `replace`, which is precisely how a filesystem rename acquired string
    authority. This renderer keeps the receiver, so the pair can be reviewed:

        Name                -> `record`
        Attribute chain     -> `self.promote`
        Call                -> `_receipt_digest(...)`   (arguments elided)
        Constant            -> the literal's TYPE (`bytes`), never its content
        Subscript           -> `record[...]`
        anything else       -> `ast.<Kind>`

    Argument lists are elided because the argument VALUES are what vary, and
    the authority question is about the receiver, not the payload.
    """
    if node is None:
        return "<none>"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_normalized_expression(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return f"{_normalized_expression(node.func)}(...)"
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Subscript):
        return f"{_normalized_expression(node.value)}[...]"
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return type(node).__name__.lower()
    if isinstance(node, ast.Dict):
        return "dict"
    if isinstance(node, ast.Starred):
        return f"{_normalized_expression(node.value)}[*]"
    return f"ast.{type(node).__name__}"


def _normalized_call_expression(call):
    """`receiver.method` for a method call; the bare callee otherwise."""
    callee = _qualified_callee(call)
    if callee is None:
        return "<dynamic>"
    if isinstance(call.func, ast.Attribute):
        return f"{_normalized_expression(call.func.value)}.{call.func.attr}"
    return callee


def _is_literal_receiver(node):
    """True when the receiver is a literal constant (unrebindable by name)."""
    return isinstance(node, ast.Constant)


def _observer_for(callee):
    """Map a mutation channel to the tripwire observer that would catch it.

    Returns None when a channel is not observed, which is exactly the
    condition the proof must refuse to tolerate.
    """
    head, _, attr = callee.rpartition(".")
    if head == "os":
        if attr in _MutationTripwire.MUTATORS:
            return f"os.{attr}"
        if attr == "open":
            return "os.open (write-capable flags only)"
        if attr == "fdopen":
            return "os.fdopen (write-capable mode only)"
    if head == "tempfile" and attr in _MutationTripwire.TEMPFILE_MUTATORS:
        return f"tempfile.{attr}"
    if head == "shutil" and attr in _MutationTripwire.SHUTIL_MUTATORS:
        return f"shutil.{attr}"
    if callee == "open":
        return "builtins.open (write-capable mode, engine-frame only)"
    return None


# Modules whose attribute names are NOT bare method names. Anything with one
# of these heads is matched on the FULL dotted spelling only, so a registry
# entry like "open" can never admit `shutil.open` or `io.open`.
QUALIFIED_MODULES = frozenset({
    "os", "os.path", "os.environ", "tempfile", "shutil", "stat", "json",
    "hashlib", "io", "subprocess", "sys", "fcntl", "msvcrt", "pathlib",
})


def _classify_call(owner, call, context):
    """Assign exactly one classification to a single reachable call site.

    Matching order matters and is deliberate:
      1. no renderable callee            -> UNKNOWN (dynamic call)
      2. maps to a tripwire observer      -> MUTATION
      3. explicitly reviewed constructor  -> READ_ONLY
      4. reviewed dotted module call      -> READ_ONLY
      5. bare local name                  -> dispatch seam / module-level
                                            engine definition / reviewed
                                            builtin, else UNKNOWN
      6. method call on a receiver        -> literal receiver, expression
                                            receiver, or the reviewed
                                            (owner, receiver, method)
                                            triple with reviewed binding
                                            forms -- else UNKNOWN

    X7: a METHOD call is no longer admitted on its attribute name alone. The
    receiver is normalized and the (receiver, method) PAIR must be reviewed, so
    `record.get` is admitted while `Path(src).replace(dst)` and
    `external.update(...)` are refused.

    X7X: step 6 is further bound to the OWNING FUNCTION and to the binding
    FORMS that name is allowed to take, so a reviewed receiver name rebound by
    a walrus, comprehension target, tuple unpack, lambda parameter or with
    target no longer inherits the review.

    X8: steps 2-6 no longer GRANT authority on their own. Every grant is routed
    through `_grant`, which additionally requires the exact source site to
    appear in `EXACT_SITE_MANIFEST` with the reviewed occurrence count and the
    owning function to carry the reviewed AST digest. A rule can therefore
    RECOGNIZE a call and still refuse it: recognition is not authority.
    """
    callee = _qualified_callee(call)
    expr = _normalized_call_expression(call)
    col = getattr(call, "col_offset", 0)
    engine_definitions = context["definitions"]
    receiver_bindings = context["bindings"].get(owner, {})

    def _ret(classification, reason="", observer=None):
        return _ClassifiedCall(owner, call.lineno, callee, classification,
                               observer, col=col, expression=expr,
                               reason=reason)

    def _grant(classification, reason, observer=None):
        """Authorize ONE exact source site. X8: recognition is not authority.

        Every path that would grant authority passes through here, so no rule
        can admit a call by itself. The mutation path is deliberately included:
        `os.open` earns its observer mapping from the SPELLING `os.open`, and
        a shadowed `os` is not the real module, so the runtime tripwire would
        never see a write issued through it.
        """
        denied = _site_authority(owner, expr, context)
        if denied is not None:
            return _ret(CLASS_UNKNOWN, denied)
        return _ret(classification, reason, observer)

    # X9: a PEP 695 type parameter is a real lexical binding, so it is refused
    # BEFORE any rule can recognize the callee -- and independently of the
    # owner digest, so the diagnostic always names the binding form.
    shadow = _type_param_shadow(owner, call, context)
    if shadow is not None:
        return _ret(CLASS_UNKNOWN, shadow)
    if callee is None:
        return _ret(CLASS_UNKNOWN, "no renderable callee (dynamic call)")
    observer = _observer_for(callee)
    if observer is not None:
        return _grant(CLASS_MUTATION, "maps to a tripwire observer", observer)
    # X7 rule F: a reviewed constructor must be decidable on its own reviewed
    # merits. Previously engine_definitions was consulted first, so every name
    # in PURE_CONSTRUCTORS was unreachable and the policy was dead.
    if callee in PURE_CONSTRUCTORS:
        return _grant(CLASS_READ_ONLY, "reviewed pure constructor")
    head, _, attr = callee.rpartition(".")
    # X7: the receiver/method vs bare-name discriminator is the AST SHAPE, not
    # the rendered spelling. `hashlib.sha256(x).hexdigest()` renders as the
    # dotless "hexdigest" yet IS a method call on an expression receiver, so
    # routing on the dot would misclassify it as a bare local name.
    is_method = isinstance(call.func, ast.Attribute)
    if head in QUALIFIED_MODULES:
        # Known module: only the full dotted spelling may be admitted, so a
        # new module call cannot be absorbed by a bare-name registry entry.
        # X8: a module HEAD is matched by string, so a shadowed `os` reaches
        # this branch; `_grant` is what refuses it.
        if callee in READ_ONLY_REGISTRY:
            return _grant(CLASS_READ_ONLY, "reviewed dotted module call")
        return _ret(CLASS_UNKNOWN,
                    f"module call {callee!r} is not in READ_ONLY_REGISTRY")
    if not is_method:
        # X7 rule E: the dispatch-table seam stays explicit and separately
        # proven by I.G.
        if callee in REVIEWED_DISPATCH_LOCALS:
            return _grant(CLASS_INTERNAL,
                          "engine dispatch table (proven by I.G)",
                          "engine dispatch table (proven by I.G)")
        # X7 rule D: only genuine MODULE-LEVEL engine functions and classes may
        # take INTERNAL_CALL from a bare name. Nested defs and class methods are
        # deliberately absent from engine_definitions, so `commit()` cannot be
        # mistaken for an engine function.
        # X8: this is a bare-name match too, so it is exactly as shadowable as
        # the module case; `_grant` is what refuses it.
        if callee in engine_definitions:
            return _grant(CLASS_INTERNAL, "module-level engine definition")
        if callee in READ_ONLY_REGISTRY:
            return _grant(CLASS_READ_ONLY, "reviewed bare builtin")
        return _ret(CLASS_UNKNOWN,
                    f"bare name {callee!r} is neither a module-level engine "
                    f"definition nor a reviewed builtin")
    # X7 rules B and C: method call on a non-module receiver.
    receiver = call.func.value
    if _is_literal_receiver(receiver):
        if expr in LITERAL_RECEIVER_METHODS:
            return _grant(CLASS_READ_ONLY,
                          "literal receiver cannot be rebound")
        return _ret(CLASS_UNKNOWN,
                    f"literal-receiver call {expr!r} is not reviewed")
    if isinstance(receiver, ast.Call):
        if expr in REVIEWED_EXPRESSION_RECEIVERS:
            return _grant(CLASS_READ_ONLY, "reviewed expression receiver")
        return _ret(CLASS_UNKNOWN,
                    f"expression receiver {expr!r} is not in "
                    f"REVIEWED_EXPRESSION_RECEIVERS")
    if expr in REVIEWED_RECEIVER_METHODS:
        # X7X rule G: the reviewed pair is not enough on its own. The receiver
        # NAME must be bound here only by forms the review covers, and this
        # OWNING FUNCTION must be one that reviewed this pair.
        recv, _, meth = expr.rpartition(".")
        allowed = REVIEWED_RECEIVER_BINDINGS.get(recv)
        if allowed is None:
            return _ret(CLASS_UNKNOWN,
                        f"receiver {recv!r} has no reviewed binding forms")
        forms = receiver_bindings.get(recv, frozenset())
        extra = sorted(forms - allowed)
        if extra:
            return _ret(CLASS_UNKNOWN,
                        f"receiver {recv!r} is bound in {owner!r} by "
                        f"unreviewed binding form(s) {extra!r}; reviewed "
                        f"forms are {sorted(allowed)!r}")
        if (owner, recv, meth) not in REVIEWED_RECEIVER_SITES:
            return _ret(CLASS_UNKNOWN,
                        f"(owner, receiver, method) "
                        f"{(owner, recv, meth)!r} is not in "
                        f"REVIEWED_RECEIVER_SITES")
        return _grant(CLASS_READ_ONLY,
                      "reviewed (owner, receiver, method) triple, receiver "
                      "bound only by reviewed forms")
    return _ret(CLASS_UNKNOWN,
                f"(receiver, method) pair {expr!r} is not in "
                f"REVIEWED_RECEIVER_METHODS")


def _authority_closure(tree):
    """Transitive intra-module call closure from the authority entry points."""
    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[node.name] = node
    seen, stack = set(), list(AUTHORITY_ENTRY_POINTS)
    while stack:
        name = stack.pop()
        if name in seen or name not in funcs:
            continue
        seen.add(name)
        for call in ast.walk(funcs[name]):
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            target = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None)
            if target and target in funcs and target not in seen:
                stack.append(target)
    return funcs, seen


def _engine_definitions(tree):
    """Names DEFINED at MODULE LEVEL by this engine: functions and classes.

    A module-level class such as `_ExecutionAuthorityConflict` is defined
    here, so calling it is an internal edge rather than an unknown one. It is
    also instantiated, which is why PURE_CONSTRUCTORS alone was not enough.

    X7 rule D. This used to walk the WHOLE tree, so nested functions and class
    METHODS entered the generic internal namespace: `commit`, `activate`,
    `acquire`, `_refuse`, `__enter__` and friends all became "engine
    functions". An injected bare `commit()` was therefore classified
    INTERNAL_CALL. Only module-level definitions belong there now. Measured at
    this head: narrowing to module level breaks no reachable call site.

    Stated boundary: a class BODY is not itself walked by the closure. A
    reviewed constructor is admitted as a pure construction; the calls inside
    its `__init__` are outside the closure unless `__enter__`-style reachability
    pulls them in. This is recorded, not asserted away.
    """
    return {node.name for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef))}


def _audit_source(source):
    """Classify every reachable call site. Returns (closure, sites)."""
    tree = ast.parse(source)
    context = _audit_context(tree)
    funcs, closure = context["funcs"], context["closure"]
    sites = []
    for owner in sorted(closure):
        calls = [c for c in ast.walk(funcs[owner]) if isinstance(c, ast.Call)]
        for call in sorted(calls,
                           key=lambda c: (c.lineno, _qualified_callee(c) or "")):
            sites.append(_classify_call(owner, call, context))
    return closure, sites


def _unknown_sites(sites):
    return [s for s in sites if s.classification == CLASS_UNKNOWN]


def _assert_closed_world(source, label="engine"):
    """Fail closed unless every reachable call site is classified.

    The single choke point every X6 proof calls, so a newly added
    unrecognised write API anywhere in the authority closure turns the
    mutation proof red instead of quietly shrinking the audited set.
    """
    closure, sites = _audit_source(source)
    unknown = _unknown_sites(sites)
    assert not unknown, (
        f"{label}: {len(unknown)} reachable call site(s) in the authority "
        "closure are UNKNOWN_OR_DYNAMIC, so mutation-channel coverage is NOT "
        "closed-world:\n" +
        "\n".join("    " + s.as_row() for s in unknown[:25]) +
        ("\n    ..." if len(unknown) > 25 else "") +
        "\nReview each: either admit to READ_ONLY_REGISTRY / "
        "PURE_CONSTRUCTORS with a stated reason, or prove it maps to a "
        "tripwire observer.")
    ids = [s.identity for s in sites]
    assert len(ids) == len(set(ids)), (
        "call-site identities are not unique; the audit cannot distinguish "
        "structurally identical calls")
    return closure, sites


def _engine_source():
    return Path(pgrec.__file__).read_text(encoding="utf-8")


def _reachable_functions(tree):
    return _authority_closure(tree)


def _reachable_mutation_channels(sites):
    """Reachable mutation CHANNELS (distinct rendered callees).

    Deliberately distinct from total reachable call sites and from the
    globally instrumented channel set.
    """
    return {s.callee for s in sites if s.classification == CLASS_MUTATION}


def _globally_instrumented_channels():
    """What the tripwire CAN observe, reachable or not.

    A global capability is NOT automatically a reachable authority-path
    channel: tempfile.* and shutil.* are instrumented yet currently have
    zero reachable sites on this path.
    """
    channels = {"os." + n for n in _MutationTripwire.MUTATORS}
    channels |= {"os.open", "os.fdopen", "open"}
    channels |= {"tempfile." + n for n in _MutationTripwire.TEMPFILE_MUTATORS}
    channels |= {"shutil." + n for n in _MutationTripwire.SHUTIL_MUTATORS}
    return channels


def _weakened_source(inject_into, injected_call):
    """Engine source with `injected_call` added to `inject_into`.

    The target function's NAME is preserved, so an anchor-only drift check
    cannot notice the change -- the exact X5 blind spot control A exhibits.
    """
    source = _engine_source()
    tree = ast.parse(source)
    target = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)
                   and n.name == inject_into), None)
    assert target is not None, f"{inject_into} not found in the engine"
    lines = source.splitlines()
    lines.insert(target.body[0].lineno - 1, "    " + injected_call)
    mutated = "\n".join(lines) + "\n"
    ast.parse(mutated)
    return mutated



def test_h_a_the_audited_channel_surface_is_not_empty(tmp_path):
    """H.1 The closure must contain channels, or completeness is theatre.

    If the engine were pure, "the tripwire records nothing" would be
    unfalsifiable. So the surface is asserted non-empty AND asserted to
    contain the conditional channels X5 added: `os.open` and builtin `open`.
    """
    closure, sites = _assert_closed_world(_engine_source())
    assert len(closure) > 1, "the authority closure collapsed to a stub"
    assert sites, "no reachable call sites were audited"
    channels = _reachable_mutation_channels(sites)
    assert channels, (
        "no mutation channel is reachable from the authority entry points; "
        "the mutation proof would have nothing to observe")
    for required in ("os.open", "open"):
        assert required in channels, (
            f"{required!r} is not a reachable mutation channel, so the "
            f"tripwire does not claim it; measured: {sorted(channels)}")


def test_h_b_reachable_channels_are_a_subset_of_instrumented_channels():
    """H.2 Set relation, stated as SUBSET coverage -- never equality.

    X5's evidence claimed "instrumented set == audited set" while this test
    only ever asserted containment, because the tripwire deliberately
    instruments more than the authority path currently reaches
    (`tempfile.*`/`shutil.*` have zero reachable sites here). Equality was
    therefore never proven and is not claimed.

    Four distinct quantities, deliberately not conflated:
      1. reachable call sites          -- `_audit_source`
      2. reachable mutation channels   -- `_reachable_mutation_channels`
      3. globally instrumented channels-- `_globally_instrumented_channels`
      4. executable probe coverage     -- asserted in H.C, not here
    """
    _, sites = _assert_closed_world(_engine_source())
    reachable = _reachable_mutation_channels(sites)
    instrumented = _globally_instrumented_channels()

    missing = sorted(reachable - instrumented)
    assert not missing, (
        "reachable mutation channels with NO tripwire observer: "
        f"{missing!r}; reachable={sorted(reachable)} "
        f"instrumented={sorted(instrumented)}")

    # The superset direction is expected and must stay expected: a global
    # capability is not automatically a reachable authority-path channel.
    extra = sorted(instrumented - reachable)
    assert extra, (
        "the instrumented set no longer exceeds the reachable set; if that "
        "is now genuinely true, equality must be asserted explicitly here "
        "rather than implied")

    # Every mutating site must name an observer, and the named observer must
    # be one the tripwire really implements.
    for site in sites:
        if site.classification != CLASS_MUTATION:
            continue
        assert site.observer, f"{site.identity} is mutating with no observer"
        assert _observer_for(site.callee) == site.observer, site.as_row()


def test_i_a_an_unknown_mutation_call_fails_the_closed_world_audit():
    """I.A (control A) An UNRECOGNISED write API must turn the proof RED.

    Reproduces the X5 blind spot the audit is being built to close. The
    target function's NAME is preserved, so an anchor-only drift check
    cannot see the change -- yet the closed-world audit must fail, and must
    name the offending call site.
    """
    weakened = _weakened_source(
        "_load_transition_record",
        "Path(operation_id).write_text('injected')",
    )
    # Sanity: the injection is real and the entry points are untouched.
    for entry in AUTHORITY_ENTRY_POINTS:
        assert f"def {entry}(" in weakened, (
            f"the control weakened {entry}, so it no longer proves what it "
            "claims")
    closure, sites = _audit_source(weakened)
    assert "_load_transition_record" in closure, (
        "the injected call site is not in the closure; the control is not "
        "exercising the reachable path")

    unknown = _unknown_sites(sites)
    assert unknown, (
        "an unregistered Path.write_text in a reachable function was NOT "
        "detected -- this is the exact failure mode X5 had")
    write_text_sites = [s for s in unknown if s.callee == "write_text"]
    assert write_text_sites, (
        f"the audit failed closed, but did not identify the injected "
        f"write_text; unknown callees: "
        f"{sorted({s.callee for s in unknown})}")
    assert all(s.owner == "_load_transition_record"
               for s in write_text_sites), write_text_sites

    # And the choke point itself must refuse the weakened source.
    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    message = str(excinfo.value)
    assert "UNKNOWN_OR_DYNAMIC" in message
    assert "write_text" in message, (
        f"the failure message does not name the offending call: {message}")


def test_i_b_a_known_mutation_maps_to_its_observer_and_loses_its_observer():
    """I.B (control B) Known channels classify as mutations WITH observers.

    Two directions are proven: a known write-capable channel is classified
    and mapped, and REMOVING its observer makes the proof fail. The second
    half is what stops the observer mapping from being decorative.
    """
    _, sites = _assert_closed_world(_engine_source())
    by_callee = {}
    for site in sites:
        if site.classification == CLASS_MUTATION:
            by_callee.setdefault(site.callee, []).append(site)

    assert "os.open" in by_callee, sorted(by_callee)
    for site in by_callee["os.open"]:
        assert site.observer == "os.open (write-capable flags only)", (
            site.as_row())

    # os.chmod is instrumented by the tripwire but is NOT reachable from the
    # authority entry points. Prove it maps to an observer, and that
    # dropping the observer breaks the mapping.
    assert "os.chmod" in _globally_instrumented_channels()
    assert _observer_for("os.chmod") == "os.chmod"
    assert "os.chmod" not in by_callee, (
        "os.chmod became reachable; re-derive the reachable channel set")

    saved = _MutationTripwire.MUTATORS
    try:
        _MutationTripwire.MUTATORS = frozenset(
            n for n in saved if n != "chmod")
        assert _observer_for("os.chmod") is None, (
            "removing chmod from the tripwire did not remove its observer")
        weakened = _weakened_source(
            "_load_transition_record", "os.chmod(operation_id, 0o600)")
        _, weak_sites = _audit_source(weakened)
        chmod_sites = [s for s in weak_sites
                       if s.callee == "os.chmod"]
        assert chmod_sites, "the injected os.chmod was not audited"
        for site in chmod_sites:
            assert site.classification == CLASS_UNKNOWN, (
                "os.chmod was classified as a mutation with no observer; it "
                f"must fail closed instead: {site.as_row()}")
    finally:
        _MutationTripwire.MUTATORS = saved
    assert _observer_for("os.chmod") == "os.chmod", (
        "the observer was not restored")


def test_i_c_read_only_channels_are_classified_but_stay_silent(tmp_path):
    """I.C (control C) Read-capable opens are READY: silent and classified.

    Two independent properties, both required:
      * STATICALLY the read-only calls in the closure are classified
        (as mutations where the channel is conditional, or as read-only
        registry entries) -- never UNKNOWN;
      * RUNTIME a read-mode open records nothing, so a non-zero mutation
        count still means a real mutation.
    """
    _, sites = _assert_closed_world(_engine_source())
    assert not _unknown_sites(sites), "closure is not closed-world"
    read_only = {s.callee for s in sites
                 if s.classification == CLASS_READ_ONLY}
    for expected in ("os.stat", "os.read", "os.path.realpath", "json.loads"):
        assert expected in read_only, (
            f"{expected!r} should be classified read-only; got "
            f"{sorted(read_only)}")

    # Runtime silence.
    probe = Path(tmp_path) / "i-c.txt"
    probe.write_text("readable", encoding="utf-8")
    with _MutationTripwire(pgrec) as trip:
        fd = pgrec.os.open(str(probe), os.O_RDONLY)
        os.close(fd)
        with open(str(probe), encoding="utf-8") as handle:
            assert handle.read() == "readable"
        with pgrec.os.fdopen(os.open(str(probe), os.O_RDONLY), "rb") as h:
            assert h.read() == b"readable"
    assert trip.mutations == [], (
        "a read-capable open was recorded as a mutation: "
        f"{trip.mutations!r}")


def test_i_d_builtin_open_attribution_limit_is_explicit(tmp_path):
    """I.D (control D) Two-sided attribution, with its limit stated.

    A write-capable builtin `open` is attributed by IMMEDIATE caller frame.
    That is exact for a direct call, and this test states the boundary
    rather than implying more: an indirect file API reached through another
    callee is not covered by frame attribution, and must instead be rejected
    by the closed-world audit unless separately instrumented.
    """
    probe = Path(tmp_path) / "i-d.txt"

    _engine_open_writer(pgrec, probe)
    assert probe.read_text(encoding="utf-8") == "engine-write"
    probe.unlink()

    with _MutationTripwire(pgrec) as trip:
        _engine_open_writer(pgrec, probe)
    assert "open" in trip.kinds(), sorted(trip.kinds())
    probe.unlink()

    with _MutationTripwire(pgrec) as trip:
        with open(str(probe), "w", encoding="utf-8") as handle:
            handle.write("attacker-write")
    assert "open" not in trip.kinds(), (
        f"a test-module write was attributed to the engine: {trip.mutations!r}")
    probe.unlink()

    # The limit: an indirect write API is NOT covered by frame attribution,
    # so it must be refused by the audit. `write_text` is exactly such a
    # channel and is unknown to the registry.
    assert _observer_for("write_text") is None
    assert _observer_for("io.open") is None, (
        "io.open must not be treated as covered by the builtin-open "
        "observer; it is a different call and stays unknown")
    weakened = _weakened_source(
        "_load_transition_record", "Path(operation_id).write_text('x')")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_i_e_body_drift_fails_even_when_every_anchor_is_present():
    """I.E (control E) A real body-drift control, replacing anchor-only H.7.

    X5's H.7 asserted only that the three entry-point NAMES appear in the
    source. Keeping all three names while adding an unclassified call is
    invisible to that check. Here the names are deliberately preserved and
    the audit must still fail.
    """
    source = _engine_source()
    # The shipped source IS closed-world; that is the baseline.
    _assert_closed_world(source)

    # Anchor-only truth: all three names are present before and after.
    weakened = _weakened_source(
        "_load_transition_record", "Path(operation_id).write_text('x')")
    for entry in AUTHORITY_ENTRY_POINTS:
        assert f"def {entry}(" in weakened
        assert f"def {entry}(" in source

    # Yet the audit fails on the drifted body.
    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    assert "write_text" in str(excinfo.value)

    # And the reverse: removing a channel the audit depends on also fails,
    # so the check is not vacuously satisfied.
    renamed = source.replace("def _acquire_recovery_authority(",
                             "def _acquire_recovery_authority_RENAMED(")
    assert renamed != source
    closure, _ = _audit_source(renamed)
    assert "_acquire_recovery_authority" not in closure, (
        "renaming an entry point should collapse the closure")


def test_i_g_the_dispatch_local_admission_is_proven_executably():
    """I.G `REVIEWED_DISPATCH_LOCALS` is backed by a real proof.

    The bare local `handler` is admitted as an internal edge on the strength
    of a claim about the engine's dispatch table. This test makes that claim
    executable: every value of `_STATE_DISPATCH` must be a function DEFINED
    BY THE ENGINE, and every one of those handlers must itself appear in the
    authority closure, so its body is audited by the same closed-world check.

    It also pins the reverse: a name NOT in the reviewed set stays unknown.

    X8 strengthens the reverse direction. The direct probe used to assert that
    a bare `handler(record)` in an UNRELATED owner took INTERNAL_CALL on the
    strength of its spelling. It no longer does: the dispatch admission is now
    bound to the exact reviewed site in the engine, so the same spelling
    outside that site is refused. The real site is still asserted internal, in
    the loop above, so this narrows the admission rather than deleting it.
    """
    dispatch = pgrec._STATE_DISPATCH
    assert isinstance(dispatch, dict) and dispatch, "no state dispatch table"
    # The handlers must be DEFINED in the engine source, not
    # merely importable from it, so an injected or monkeypatched
    # callable cannot satisfy the reviewed-dispatch admission.
    engine_source_names = _engine_definitions(
        ast.parse(_engine_source()))

    handlers = set()
    for state, handler in dispatch.items():
        assert callable(handler), (
            f"state {state!r} dispatches to a non-callable {handler!r}")
        assert handler.__name__ in engine_source_names, (
            f"state {state!r} dispatches to {handler!r}, which is NOT defined "
            "by the engine; the reviewed dispatch admission does not hold")
        handlers.add(handler.__name__)
    assert handlers, "no handler names resolved"

    _, sites = _assert_closed_world(_engine_source())
    closure, _ = _authority_closure(ast.parse(_engine_source()))
    # Every dispatch handler is itself audited.
    for name in sorted(handlers):
        assert name in closure, (
            f"dispatch handler {name!r} is not in the audited authority "
            "closure, so its body is unclassified")

    # And every reviewed dispatch local is genuinely classified as internal.
    dispatch_sites = [s for s in sites if s.callee in REVIEWED_DISPATCH_LOCALS]
    assert dispatch_sites, "the reviewed dispatch local is not exercised"
    for site in dispatch_sites:
        assert site.classification == CLASS_INTERNAL, site.as_row()
        assert "proven by I.G" in (site.observer or ""), site.as_row()

    # A bare name outside the reviewed set stays unknown -- the admission is
    # not a blanket allowance for bare locals.
    probe_context = {"definitions": set(), "bindings": {}, "digests": {},
                     "counts": {}, "funcs": {}, "closure": set()}
    assert _classify_call(
        "_probe", ast.parse("handler(record)").body[0].value,
        probe_context).classification == CLASS_UNKNOWN, (
        "X8: a dispatch-local name that is NOT an exact reviewed site must "
        "not take INTERNAL_CALL from its spelling alone")
    assert _classify_call(
        "_probe", ast.parse("rogue(value)").body[0].value,
        probe_context).classification == CLASS_UNKNOWN


def test_i_f_the_four_quantities_are_reported_separately():
    """I.F The four counts are distinct, and the report keeps them apart.

    Guards against re-conflating reachable call sites, reachable mutation
    channels, globally instrumented channels and probe coverage -- the exact
    conflation that made X5's evidence wrong.
    """
    _, sites = _assert_closed_world(_engine_source())
    reachable_channels = _reachable_mutation_channels(sites)
    instrumented = _globally_instrumented_channels()

    counts = {
        "reachable_call_sites": len(sites),
        "reachable_mutation_channels": len(reachable_channels),
        "globally_instrumented_channels": len(instrumented),
    }
    # Call sites are far more numerous than distinct channels.
    assert counts["reachable_call_sites"] >         counts["reachable_mutation_channels"], counts
    # The instrumented superset exceeds the reachable set.
    assert counts["globally_instrumented_channels"] >         counts["reachable_mutation_channels"], counts
    # tempfile/shutil are instrumented yet unreachable here: the concrete
    # proof that a global capability is not a reachable channel.
    unreachable_but_instrumented = sorted(
        c for c in instrumented - reachable_channels
        if c.split(".")[0] in ("tempfile", "shutil"))
    assert unreachable_but_instrumented, (
        "expected tempfile/shutil channels to be instrumented but "
        f"unreachable; got {sorted(instrumented - reachable_channels)}")
    for channel in unreachable_but_instrumented:
        assert channel not in _reachable_mutation_channels(sites)



def test_h_c_reachable_channels_are_probed_and_unreachable_ones_are_named(
        tmp_path):
    """H.3 Probe coverage, stated for exactly the channels that are reachable.

    X5's version of this test asserted "every audited channel is observed
    live" but probed `tempfile.mkstemp` and `shutil.copyfileobj`, which are
    INSTRUMENTED yet have ZERO reachable sites on the authority path. It was
    therefore measuring global tripwire capability while claiming reachable
    coverage.

    What is proven here, precisely:
      * every channel the closed-world audit marks MUTATION is driven and
        recorded on a live tripwire -- this is the reachable coverage claim;
      * the instrumented-but-unreachable channels are named explicitly as
        capability, not coverage, and each is still probed so the observer is
        known to work when it is exercised.
    """
    _, sites = _assert_closed_world(_engine_source())
    reachable = _reachable_mutation_channels(sites)
    instrumented = _globally_instrumented_channels()

    seen_kinds = set()
    # The capability/reachable split, asserted here because it is the
    # distinction H.C exists to draw: instrumented does NOT mean reachable.
    unreachable_capability = sorted(instrumented - reachable)
    assert unreachable_capability, (
        "the instrumented set no longer exceeds the reachable set; the "
        "capability-vs-coverage distinction in this test is now vacuous")
    for channel in ("tempfile.mkstemp", "shutil.copyfileobj"):
        assert channel in unreachable_capability, (
            f"{channel!r} is no longer instrumented-but-unreachable: "
            f"reachable={sorted(reachable)}")



    # -- reachable channel 1: os.open with write-capable flags --------
    target = Path(tmp_path) / "h-c.bin"
    with _MutationTripwire(pgrec) as trip:
        fd = pgrec.os.open(str(target), os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(fd, b"x")
        finally:
            os.close(fd)
        seen_kinds |= set(trip.kinds())
    target.unlink()

    # -- reachable channel 2: builtin open, engine-frame attribution --
    engine_probe = Path(tmp_path) / "h-c-engine-open.txt"
    with _MutationTripwire(pgrec) as trip:
        _engine_open_writer(pgrec, engine_probe)
    assert engine_probe.read_text(encoding="utf-8") == "engine-write"
    engine_probe.unlink()
    seen_kinds |= set(trip.kinds())

    # -- instrumented but NOT reachable: probed as capability ---------
    with _MutationTripwire(pgrec) as trip:
        fd, name = pgrec.tempfile.mkstemp(prefix="h-c-")
        os.close(fd)
        Path(name).unlink()
        src = Path(tmp_path) / "h-c-src"
        src.write_bytes(b"payload")
        dst = Path(tmp_path) / "h-c-dst"
        with open(src, "rb") as reader, open(dst, "wb") as writer:
            pgrec.shutil.copyfileobj(reader, writer)
        capability_kinds = set(trip.kinds())
        src.unlink()
        dst.unlink()

    for required in sorted(reachable):
        assert required in seen_kinds, (
            f"reachable mutation channel {required!r} was never recorded on a "
            f"live tripwire; observed: {sorted(seen_kinds)}")

    for required in ("tempfile.mkstemp", "shutil.copyfileobj"):
        assert required in capability_kinds, (
            f"instrumented-but-unreachable channel {required!r} did not fire; "
            f"its observer is not wired: {sorted(capability_kinds)}")
        assert required not in reachable, (
            f"{required!r} is now reachable; the capability/reachable split in "
            "this test must be re-derived")

    # And the tripwire disarmed after exit.
    with _MutationTripwire(pgrec) as trip:
        pass
    marker = Path(tmp_path) / "h-c-disarm.txt"
    marker.write_text("x", encoding="utf-8")
    assert not trip.mutations, "the tripwire stayed armed after exit"
    marker.unlink()


def test_h_d_a_read_mode_open_is_NOT_recorded(tmp_path):
    """H.4 The tripwire must not cry wolf on the read-only authority path.

    G.1 asserts zero mutations. If the tripwire recorded every `open`, that
    assertion would pass only because the engine never opens anything --
    which would make it a measure of the engine's I/O style rather than of
    its side effects. So a genuinely read-capable open is asserted silent.
    """
    probe = Path(tmp_path) / "h-d.txt"
    probe.write_text("readable", encoding="utf-8")

    with _MutationTripwire(pgrec) as trip:
        fd = pgrec.os.open(str(probe), os.O_RDONLY)
        os.close(fd)
        with open(str(probe), encoding="utf-8") as handle:
            assert handle.read() == "readable"
        with pgrec.os.fdopen(os.open(str(probe), os.O_RDONLY), "rb") as handle:
            assert handle.read() == b"readable"

    assert trip.mutations == [], (
        "a read-only open was recorded as a mutation; the zero-mutation "
        f"assertion in G.1 is measuring the wrong thing: {trip.mutations!r}")


def test_h_e_the_tripwire_attributes_a_helper_write_not_an_os_one(tmp_path):
    """H.5 Attribution: attacker, helper and os layers stay distinguishable.

    The engine's own publisher is wrapped as a helper, so its write is
    recorded under the helper's name even though it also performs os.replace
    and os.chmod underneath. A caller must be able to tell WHICH layer did it.
    """
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")

    with _MutationTripwire(pgrec) as trip:
        pgrec._write_transition_record(OPID, record)

    kinds = trip.kinds()
    assert "_write_transition_record" in kinds, kinds
    assert any(k.startswith("os.") for k in kinds), kinds


def test_h_f_the_attackers_own_writes_are_structurally_unobservable(
        tmp_path):
    """H.6 The separation that makes zero meaningful is two-sided.

    The attacker runs in THIS module and writes through the real `os`. If it
    were recorded, a non-zero mutation count would conflate the attack with an
    engine side effect. Assert the real `os` write is invisible to the
    tripwire while the engine namespace is provably proxied.
    """
    transitions, _record, _promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    victim = Path(tmp_path) / "attacker-owned.txt"

    with _MutationTripwire(pgrec) as trip:
        assert pgrec.os is not trip.real_os, "the tripwire is not installed"
        # The attacker's own mutation, through the REAL os.
        with open(victim, "w", encoding="utf-8") as handle:
            handle.write("attacker")
        moved = Path(tmp_path) / "attacker-owned-2.txt"
        os.replace(victim, moved)
        os.chmod(moved, 0o600)
        assert trip.mutations == [], (
            "an attacker mutation was attributed to the engine: "
            f"{trip.mutations!r}")

    moved.unlink()


# The size bound the denial proof depends on. Both the BEFORE-read and the
# DURING-read comparison are anchored, each asserted to occur exactly once,
# so a drifted engine makes the control fail loudly instead of quietly
# rebuilding the shipped engine and proving nothing.
# ===================================================================== #
# X7 -- RECEIVER-BOUND CALL-SITE AUTHORITY
# ===================================================================== #
# X6 made UNKNOWN SPELLINGS fail closed, but still admitted ambiguous KNOWN
# method names without proving their receiver: the bare attribute name alone
# bought read-only authority. So `Path(target).replace(dst)` -- a filesystem
# RENAME -- was admitted as the reviewed string operation "replace", any object
# named `external` could use `.update`, and a bare `commit()` was labelled an
# engine function because class methods had been harvested into the generic
# internal namespace.
#
# Every control below was verified to DISCRIMINATE: each was checked against a
# deliberately weakened classifier, not only against the shipped one.


def _inject_into_reachable(injected_call, into="_load_transition_record"):
    """Weakened engine source with ONE added call, target NAME preserved."""
    return _weakened_source(into, injected_call)


def _refusals(source):
    """Unknown sites keyed by normalized expression, for readable assertions."""
    _, sites = _audit_source(source)
    return {s.expression: s for s in _unknown_sites(sites)}


def test_j_a_path_replace_cannot_inherit_string_authority():
    """J.A `Path(src).replace(dst)` is a filesystem RENAME, not str.replace."""
    weakened = _inject_into_reachable("Path(operation_id).replace('/tmp/x7')")
    # The spelling collapse is real and is why this was exploitable at all.
    callee = _qualified_callee(
        ast.parse("Path(a).replace(b)").body[0].value)
    assert callee == "replace", (
        f"expected _qualified_callee to collapse Path(a).replace(b) to "
        f"'replace', got {callee!r}; if this ever changes the X6 defect is no "
        f"longer being reproduced")

    refusals = _refusals(weakened)
    assert refusals, (
        "Path(src).replace(dst) in a reachable function was NOT detected; "
        "a filesystem rename still inherits string authority")
    hit = refusals.get("Path(...).replace")
    assert hit is not None, (
        f"the refusal does not name the normalized expression "
        f"'Path(...).replace'; refused instead: {sorted(refusals)}")
    assert hit.owner == "_load_transition_record"
    assert hit.lineno > 0 and hit.col >= 0
    assert "REVIEWED_RECEIVER_METHODS" in hit.reason or \
        "REVIEWED_EXPRESSION_RECEIVERS" in hit.reason, hit.reason

    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    msg = str(excinfo.value)
    for required in ("_load_transition_record", "Path(...).replace",
                     "reason="):
        assert required in msg, (
            f"the diagnostic omits {required!r}; X7 requires the owning "
            f"function, the normalized expression and the reason: {msg}")


def test_j_b_arbitrary_update_cannot_inherit_dict_authority():
    """J.B `.update` was reviewed for in-memory dicts; any receiver may use it."""
    weakened = _inject_into_reachable("external.update(payload)")
    refusals = _refusals(weakened)
    assert "external.update" in refusals, (
        f"an unreviewed .update receiver was admitted; refused: "
        f"{sorted(refusals)}")
    assert "update" not in READ_ONLY_REGISTRY, (
        "the bare method name 'update' is back in READ_ONLY_REGISTRY, which "
        "re-opens the X6 defect for every receiver")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_j_c_arbitrary_append_cannot_inherit_list_authority():
    """J.C `.append` was reviewed for specific census/receipt lists only."""
    weakened = _inject_into_reachable("sink.append(payload)")
    refusals = _refusals(weakened)
    assert "sink.append" in refusals, (
        f"an unreviewed .append receiver was admitted; refused: "
        f"{sorted(refusals)}")
    assert "append" not in READ_ONLY_REGISTRY
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_j_d_expression_receiver_cannot_inherit_engine_internal_status():
    """J.D A bare `commit()` must not be an engine function.

    `_engine_definitions` used to walk the WHOLE tree, so every class method
    (`commit`, `activate`, `acquire`, `_refuse`, `__enter__`, ...) entered the
    generic internal namespace. Rule D restricts it to MODULE-LEVEL definitions.
    """
    tree = ast.parse(_engine_source())
    defs = _engine_definitions(tree)
    module_level = {n.name for n in tree.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef))}
    assert defs == module_level, (
        "engine_definitions drifted from module-level definitions; nested "
        f"names re-entered the internal namespace: "
        f"{sorted(defs - module_level)}")
    for nested in ("commit", "activate", "acquire", "_refuse", "__enter__",
                   "__exit__", "__init__", "_release_lock"):
        assert nested not in defs, (
            f"{nested!r} is a nested/method name and must not be able to take "
            "INTERNAL_CALL from a bare call")

    weakened = _inject_into_reachable("Factory().commit()")
    refusals = _refusals(weakened)
    assert "Factory(...).commit" in refusals, (
        f"an expression-receiver .commit() was admitted; refused: "
        f"{sorted(refusals)}")
    # The constructor itself may be reviewed; the METHOD on it may not.
    assert "Factory" in refusals, (
        "Factory is not a reviewed constructor, so it should itself refuse")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_j_e_reviewed_dictionary_get_calls_remain_admitted():
    """J.E The policy must not be so strict that real reads are refused."""
    _, sites = _assert_closed_world(_engine_source())
    admitted = {s.expression for s in sites
                if s.classification == CLASS_READ_ONLY}
    for pair in ("record.get", "promote.get", "claim.get",
                 "admitted_record.get", "_STATE_DISPATCH.get"):
        assert pair in admitted, (
            f"the reviewed dictionary read {pair!r} is no longer admitted; "
            f"the policy has become too strict and the real source would fail")
    assert "record.get" in REVIEWED_RECEIVER_METHODS


def test_j_f_reviewed_list_append_calls_remain_admitted():
    """J.F `.append` stays admitted at its reviewed receivers only."""
    _, sites = _assert_closed_world(_engine_source())
    admitted = {s.expression for s in sites
                if s.classification == CLASS_READ_ONLY}
    for pair in ("census.append", "chunks.append", "roots.append"):
        assert pair in admitted, (
            f"the reviewed list append {pair!r} is no longer admitted")
    for pair in ("census.append", "chunks.append", "roots.append"):
        assert pair in REVIEWED_RECEIVER_METHODS


def test_j_g_reviewed_string_methods_admitted_only_at_reviewed_receivers():
    """J.G String methods are receiver-bound, exactly like everything else."""
    _, sites = _assert_closed_world(_engine_source())
    admitted = {s.expression for s in sites
                if s.classification == CLASS_READ_ONLY}
    for pair in ("name.startswith", "name.endswith", "part.strip",
                 "canonical.encode", "raw.decode", "value.items"):
        assert pair in admitted, f"reviewed string/pure call {pair!r} refused"
    # The SAME method name at a DIFFERENT receiver must not be admitted.
    weakened = _inject_into_reachable("record.startswith('x')")
    assert "record.startswith" in _refusals(weakened), (
        "a reviewed METHOD NAME at an unreviewed receiver was admitted")


def test_j_h_direntry_stat_remains_admitted_at_its_reviewed_receiver():
    """J.H `entry.stat` stays admitted; `other.stat` must not."""
    _, sites = _assert_closed_world(_engine_source())
    admitted = {s.expression for s in sites
                if s.classification == CLASS_READ_ONLY}
    assert "entry.stat" in admitted, (
        "os.DirEntry.stat at its reviewed receiver is no longer admitted")
    assert "entry.stat" in REVIEWED_RECEIVER_METHODS
    weakened = _inject_into_reachable("other.stat()")
    assert "other.stat" in _refusals(weakened), (
        "an unreviewed .stat receiver was admitted")


def test_j_i_reachable_os_open_still_maps_to_the_runtime_tripwire(tmp_path):
    """J.I Removing receiver binding must not cost mutation coverage.

    The 7 reachable mutation sites still classify as mutations WITH a real
    observer, and the observer is proven live -- not merely named.
    """
    _, sites = _assert_closed_world(_engine_source())
    mutations = [s for s in sites if s.classification == CLASS_MUTATION]
    assert mutations, "the reachable mutation surface vanished"
    for site in mutations:
        assert site.observer, (
            f"{site.identity} is a mutation with no observer; exit gate 7 "
            f"requires every reachable mutation site to map to a tested "
            f"observer")
    os_open_sites = [s for s in mutations if s.callee == "os.open"]
    assert os_open_sites, "os.open is no longer a reachable mutation channel"

    target = Path(tmp_path) / "j-i.bin"
    with _MutationTripwire(pgrec) as trip:
        fd = pgrec.os.open(str(target), os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(fd, b"x")
        finally:
            os.close(fd)
        kinds = set(trip.kinds())
    target.unlink()
    assert "os.open" in kinds, (
        f"the os.open observer did not fire on a live tripwire; observed: "
        f"{sorted(kinds)}")


def test_j_j_removing_the_os_open_observer_makes_the_proof_fail(monkeypatch):
    """J.J A mutation channel with no observer must turn the audit RED."""
    saved = _observer_for
    monkeypatch.setattr(
        sys.modules[__name__], "_observer_for",
        lambda callee: None if callee == "os.open" else saved(callee))
    try:
        weakened_refused = False
        try:
            _assert_closed_world(_engine_source())
        except AssertionError:
            weakened_refused = True
        assert weakened_refused, (
            "removing the os.open observer did NOT fail the proof, so the "
            "observer mapping is decorative")
    finally:
        monkeypatch.setattr(sys.modules[__name__], "_observer_for", saved)
    # And the restored classifier is green again, so the control is reversible.
    _assert_closed_world(_engine_source())


def test_j_k_the_x6_unknown_write_control_remains_red():
    """J.K Tightening the policy must not have blinded the X6 control."""
    weakened = _inject_into_reachable(
        "Path(operation_id).write_text('injected')")
    refusals = _refusals(weakened)
    assert "Path(...).write_text" in refusals, (
        f"the X6 unknown-write control no longer fires; refused: "
        f"{sorted(refusals)}")
    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    assert "write_text" in str(excinfo.value)


def test_j_l_every_reachable_call_site_is_classified_exactly_once():
    """J.L Completeness and uniqueness under the receiver-bound policy."""
    closure, sites = _assert_closed_world(_engine_source())
    assert not _unknown_sites(sites), (
        f"{len(_unknown_sites(sites))} reachable call site(s) unclassified")
    identities = [s.identity for s in sites]
    assert len(identities) == len(set(identities)), (
        "two reachable call sites share an identity, so 'exactly once' is "
        "not actually established")
    # Every READ_ONLY site carries a reason naming WHICH rule admitted it.
    for site in sites:
        if site.classification == CLASS_READ_ONLY:
            assert site.reason, (
                f"{site.identity} is READ_ONLY with no admission reason")
        assert site.expression, (
            f"{site.identity} has no normalized expression")


def test_j_m_the_reviewed_constructor_policy_is_reachable_and_not_dead():
    """J.M Rule F: `PURE_CONSTRUCTORS` must actually decide something.

    X6 consulted `engine_definitions` BEFORE the constructor rule, and every
    name in `PURE_CONSTRUCTORS` is a module-level class, so the rule was
    unreachable: all three snapshot constructors classified INTERNAL_CALL and
    the reviewed-constructor reason was dead text. The check now runs first, so
    this asserts the policy is live rather than decorative.
    """
    tree = ast.parse(_engine_source())
    defs = _engine_definitions(tree)
    assert PURE_CONSTRUCTORS, "the reviewed constructor set is empty"
    for name in PURE_CONSTRUCTORS:
        assert name in defs, (
            f"{name!r} is no longer an engine definition, so this control no "
            "longer exercises the ordering it was written for")
    _, sites = _assert_closed_world(_engine_source())
    by_reason = {s.callee: s.reason for s in sites
                 if s.classification == CLASS_READ_ONLY}
    hits = [n for n in PURE_CONSTRUCTORS if by_reason.get(n) ==
            "reviewed pure constructor"]
    assert hits, (
        "no reviewed constructor classified via the constructor rule, so the "
        "rule is dead again: " +
        str({n: by_reason.get(n) for n in PURE_CONSTRUCTORS}))


# --------------------------------------------------------------------- #
# X8: EXACT CALL-SITE AND BINDING AUTHORITY
# --------------------------------------------------------------------- #
#
# Sections I, J and K all prove that a RULE recognizes or refuses a call. None
# of them proves that the call is the one that was reviewed. X8's question is
# narrower and harder: can a call be authorized that was never reviewed -- by
# REUSING an approved spelling somewhere else, by DUPLICATING it, or by
# REBINDING the name it is spelled with? At X7X the answer was yes to all
# three, and the shadowing form (`os = attacker`) was the worst of them,
# because every spelling-based rule in this file compares identifier strings.
#
# Each control below therefore asserts WHICH rule fired. A control caught by
# the wrong rule would still be green while proving nothing about the rule it
# is named for, which is the ordering mistake K.F exists to prevent.

# Neutralizers used to isolate one rule from another. Each is a monkeypatch
# target, never a weakening of the shipped classifier.
_GATE_DENY_ALL = "NEUTRALIZED: the exact-site gate was removed"


def _gate_off():
    """The exact-site gate as a no-op, for isolating an older rule."""
    return lambda *a, **k: None


def test_l_a_a_known_pair_in_a_different_owner_fails_closed():
    """L.A (section 4.1) `roots.append` is reviewed in `_approved_roots` ONLY.

    X7 admitted any reviewed pair anywhere in the closure. X7X scoped it to
    the owning function. This pins that, and asserts the refusal comes from
    the owner comparison rather than from a missing manifest entry -- `roots`
    still has an entry, just not with THIS owner.
    """
    weakened = _inject_into_reachable("roots.append(payload)")
    refusals = _refusals(weakened)
    assert "roots.append" in refusals, (
        f"a reviewed pair was re-used in a different owner; refused: "
        f"{sorted(refusals)}")
    reason = refusals["roots.append"].reason
    assert ("REVIEWED_RECEIVER_SITES" in reason
            or "EXACT_SITE_MANIFEST" in reason), reason
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_b_a_duplicate_known_call_fails_closed():
    """L.B (section 4.2) A SECOND identical call does not inherit the review.

    X7X keyed authority on (owner, receiver, method), so duplicating an
    approved call inside its own owner was admitted with no new decision. The
    manifest records the reviewed OCCURRENCE COUNT, so the duplicate is a
    different site identity even though every string matches.
    """
    key = ("_approved_roots", "roots.append")
    assert EXACT_SITE_MANIFEST[key] == 1, (
        f"this control assumes one reviewed occurrence, got "
        f"{EXACT_SITE_MANIFEST[key]}")
    # The source really changed, and the injected site exists exactly once.
    weakened = _inject_into_reachable("roots.append(payload)",
                                      into="_approved_roots")
    assert weakened != _engine_source()
    injected_sites = [c for c in ast.walk(
        next(n for n in ast.parse(weakened).body
             if isinstance(n, ast.FunctionDef)
             and n.name == "_approved_roots"))
        if isinstance(c, ast.Call)
        and _normalized_call_expression(c) == "roots.append"]
    assert len(injected_sites) == 2, (
        f"the duplicate was not injected exactly once; found "
        f"{len(injected_sites)} sites")

    refusals = _refusals(weakened)
    assert "roots.append" in refusals, (
        "a duplicate of an approved call was admitted; a duplicate is a new "
        "site and needs a new review decision")
    assert "2 time(s)" in refusals["roots.append"].reason, (
        "the refusal did not come from the occurrence count, so this control "
        f"is not proving what it claims: {refusals['roots.append'].reason}")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_c_rebinding_a_reviewed_receiver_fails_closed():
    """L.C (section 4.3) `roots = attacker` before `roots.append` is refused.

    Two independent guards, proven separately rather than assumed:
      * the injector's literal form also adds a second `.append` CALL, which
        the occurrence count catches;
      * a rebinding with NO new call leaves the count untouched, so only the
        owner AST digest can catch it. That is the case X7X could not see at
        all, because `assign` was already a reviewed binding form for `roots`.
    """
    weakened = _inject_into_reachable(
        "roots = attacker; roots.append(payload)", into="_approved_roots")
    refusals = _refusals(weakened)
    assert "roots.append" in refusals, (
        f"a rebound receiver still inherited the review; refused: "
        f"{sorted(refusals)}")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)

    # -- the digest rule on its own: a rebinding with no new call -------- #
    rebind_only = _inject_into_reachable("roots = attacker",
                                         into="_approved_roots")
    _, sites = _audit_source(rebind_only)
    keys = {(s.owner, s.expression) for s in sites}
    assert ("_approved_roots", "roots.append") in keys, (
        "the rebinding removed the site, so this control no longer isolates "
        "the digest rule")
    refusals = _refusals(rebind_only)
    assert "roots.append" in refusals, (
        "a rebinding with NO new call was admitted: the occurrence count is "
        "unchanged, so only the owner digest can refuse it, and it did not")
    reason = refusals["roots.append"].reason
    assert "source context changed" in reason, (
        f"the refusal did not come from the owner digest: {reason}")
    assert REVIEWED_OWNER_DIGESTS["_approved_roots"][:16] in reason, reason


def test_l_d_rebinding_a_reviewed_dict_receiver_fails_closed():
    """L.D (section 4.4) `record = attacker` before `record.get` is refused.

    `assign` is a reviewed binding form for `record`, so X7X's form rule
    passed here by construction. This is the injection that X7X recorded as an
    open residual; X8 closes it.
    """
    weakened = _inject_into_reachable(
        "record = attacker; record.get('x')",
        into="_classify_record_for_shell")
    refusals = _refusals(weakened)
    assert "record.get" in refusals, (
        f"a rebound `record` still inherited the review; refused: "
        f"{sorted(refusals)}")
    assert "assign" in str(sorted(REVIEWED_RECEIVER_BINDINGS["record"])), (
        "this control assumes `assign` is a reviewed form for `record`; "
        "if it is not, the control is no longer exercising the X7X blind spot")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_e_shadowing_a_module_name_fails_closed():
    """L.E (section 4.5) `os = attacker` before `os.stat` is refused.

    `QUALIFIED_MODULES` matches the module HEAD as a string, so a shadowed
    module name reached the reviewed dotted-module branch. Nothing compared
    the string to the actual import. The exact-site gate is what refuses it.
    """
    weakened = _inject_into_reachable("os = attacker; os.stat(path)")
    refusals = _refusals(weakened)
    assert "os.stat" in refusals, (
        f"a shadowed `os` still took module authority; refused: "
        f"{sorted(refusals)}")
    # Attribution: with the gate neutralized, the SAME injection is a plain
    # reviewed dotted module call, i.e. X7X would have admitted it.
    saved = _site_authority
    try:
        sys.modules[__name__]._site_authority = _gate_off()
        assert "os.stat" not in _refusals(
            _inject_into_reachable("os = attacker; os.stat(path)")), (
            "the shadowed-module injection is refused even with the gate "
            "neutralized, so this control does not isolate the gate")
    finally:
        sys.modules[__name__]._site_authority = saved
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_f_shadowing_a_hash_module_fails_closed():
    """L.F (section 4.6) `hashlib = attacker` before a reviewed hash call.

    Same shape as L.E for a second qualified module, because a single
    example would not distinguish "the rule works" from "`os` is special".
    """
    weakened = _inject_into_reachable(
        "hashlib = attacker; hashlib.sha256(b'x')", into="_receipt_digest")
    refusals = _refusals(weakened)
    assert "hashlib.sha256" in refusals, (
        f"a shadowed `hashlib` still took module authority; refused: "
        f"{sorted(refusals)}")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_g_shadowing_a_reviewed_constructor_fails_closed():
    """L.G (section 4.7) `RecordSnapshot = attacker` before constructing it.

    `PURE_CONSTRUCTORS` is a bare-name set, so the shadowing assignment made
    the name denote anything at all while the rule went on admitting it as a
    reviewed pure construction.
    """
    weakened = _inject_into_reachable(
        "RecordSnapshot = attacker; RecordSnapshot(record)",
        into="_read_record_snapshot_admitted")
    refusals = _refusals(weakened)
    assert "RecordSnapshot" in refusals, (
        f"a shadowed constructor still took constructor authority; refused: "
        f"{sorted(refusals)}")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_h_shadowing_a_module_level_internal_name_fails_closed():
    """L.H (section 4.8) `_transitions_dir = attacker` before calling it.

    INTERNAL_CALL was granted from a bare name being a module-level engine
    definition. That is a string comparison, so rebinding the name won
    internal authority for an arbitrary callable.
    """
    weakened = _inject_into_reachable(
        "_transitions_dir = attacker; _transitions_dir()")
    refusals = _refusals(weakened)
    assert "_transitions_dir" in refusals, (
        f"a shadowed engine function still took INTERNAL_CALL; refused: "
        f"{sorted(refusals)}")
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_l_i_the_unchanged_shipped_source_remains_green():
    """L.I (section 4.9) The manifest is measured from this engine, so it holds.

    A guard that refuses everything would also be closed-world. The shipped
    source must still classify completely, and every site that was granted
    before X8 must still be granted -- the guard adds a requirement, it does
    not withdraw the reviewed surface.
    """
    closure, sites = _assert_closed_world(_engine_source())
    assert len(closure) == 35, f"closure moved: {len(closure)}"
    assert not _unknown_sites(sites), (
        f"{len(_unknown_sites(sites))} site(s) became UNKNOWN; the X8 gate is "
        f"too strict for the shipped engine")
    assert len(sites) == 312, f"reachable site count moved: {len(sites)}"


# The measured totals X8 section 4 requires to be reported. Asserted rather
# than printed, so a drift in any of them fails the suite instead of quietly
# changing the numbers in the evidence.
X8_TOTALS = {
    "closure_functions": 35,
    "reachable_call_sites": 312,
    "exact_site_manifest": 206,
    "owner_digests": 35,
    "duplicate_site_identities": 0,
    "missing_manifest_entries": 0,
    "surplus_manifest_entries": 0,
    "provenance_mismatches": 0,
    "read_only": 182,
    "internal": 123,
    "mutation": 7,
    "unknown": 0,
}


def test_l_j_the_manifest_is_exact_in_both_directions():
    """L.J (sections 4.10, 4.11) No missing entry, no surplus entry.

    Both directions are defects. A MISSING entry means an authorized site
    nobody reviewed. A SURPLUS entry means reviewed permission for a site that
    does not exist -- latent authority that would silently apply if a future
    edit happened to create it.
    """
    closure, sites = _assert_closed_world(_engine_source())
    granted = [s for s in sites if s.classification != CLASS_UNKNOWN]

    # Every authorized site is in the manifest, with the right count.
    observed = {}
    for site in granted:
        key = (site.owner, site.expression)
        observed[key] = observed.get(key, 0) + 1
    assert observed == EXACT_SITE_MANIFEST, (
        "the manifest is not an exact record of the granted surface: "
        f"missing={sorted(set(observed) - set(EXACT_SITE_MANIFEST))} "
        f"surplus={sorted(set(EXACT_SITE_MANIFEST) - set(observed))} "
        f"count-mismatch="
        f"{sorted(k for k in observed if k in EXACT_SITE_MANIFEST and observed[k] != EXACT_SITE_MANIFEST[k])}")
    assert sum(EXACT_SITE_MANIFEST.values()) == len(granted), (
        f"manifest counts total {sum(EXACT_SITE_MANIFEST.values())} but "
        f"{len(granted)} sites are granted")

    # Every owner digest corresponds to a closure function, and vice versa.
    assert set(REVIEWED_OWNER_DIGESTS) == set(closure), (
        "owner digests and the closure disagree: "
        f"missing={sorted(set(closure) - set(REVIEWED_OWNER_DIGESTS))} "
        f"surplus={sorted(set(REVIEWED_OWNER_DIGESTS) - set(closure))}")

    # And no site identity is ambiguous, so "exactly once" is meaningful.
    identities = [s.identity for s in sites]
    assert len(identities) == len(set(identities)), (
        "two reachable call sites share an identity")


def test_l_k_no_grant_bypasses_the_exact_site_gate(monkeypatch):
    """L.K (section 4.12) Every grant flows through the gate -- none bypasses.

    If any rule granted authority without consulting `_site_authority`, making
    the gate deny EVERYTHING would leave that site still classified. So with
    the gate replaced by an unconditional denial, every one of the 312 sites
    must become UNKNOWN. Nothing else can explain a green result.
    """
    closure, sites = _assert_closed_world(_engine_source())
    assert sum(1 for s in sites
               if s.classification != CLASS_UNKNOWN) == 312, (
        "every reachable site is granted at this head (182 read-only, 123 "
        "internal, 7 mutation), so a gate denial must remove all of them")

    monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                        lambda *a, **k: _GATE_DENY_ALL)
    try:
        _, sites = _audit_source(_engine_source())
        still_granted = [s for s in sites if s.classification != CLASS_UNKNOWN]
        assert not still_granted, (
            f"{len(still_granted)} site(s) were authorized WITHOUT consulting "
            f"the exact-site gate, so an approved spelling can still "
            f"authorize a replacement site: "
            f"{[s.as_row() for s in still_granted[:8]]}")
    finally:
        monkeypatch.undo()
    _assert_closed_world(_engine_source())

    # And a pair the registry still recognises is refused once its manifest
    # entry is withdrawn: recognition alone is never authority.
    key = ("_approved_roots", "roots.append")
    saved = dict(EXACT_SITE_MANIFEST)
    try:
        del EXACT_SITE_MANIFEST[key]
        refusals = _refusals(_engine_source())
        assert "roots.append" in refusals, (
            "withdrawing the manifest entry did NOT refuse the site, so the "
            "pair spelling is still sufficient on its own")
        assert "REVIEWED_RECEIVER_METHODS" in refusals[
            "roots.append"].reason or "EXACT_SITE_MANIFEST" in refusals[
            "roots.append"].reason, refusals["roots.append"].reason
    finally:
        EXACT_SITE_MANIFEST.clear()
        EXACT_SITE_MANIFEST.update(saved)
    _assert_closed_world(_engine_source())


def test_l_l_mutation_coverage_is_unchanged_and_non_vacuous(monkeypatch):
    """L.L (section 4.13) Gating mutations must not cost the mutation proof.

    Mutation sites are gated too, deliberately: `os.open` earns its observer
    from the SPELLING `os.open`, and a shadowed `os` is not the real module,
    so the runtime tripwire would never see a write issued through it.
    """
    _, sites = _assert_closed_world(_engine_source())
    channels = _reachable_mutation_channels(sites)
    assert channels == {"open", "os.open"}, (
        f"the reachable mutation surface moved: {sorted(channels)}")
    mutations = [s for s in sites if s.classification == CLASS_MUTATION]
    assert len(mutations) == X8_TOTALS["mutation"], sorted(
        s.identity for s in mutations)
    for site in mutations:
        assert site.observer, site.as_row()
        assert _observer_for(site.callee) == site.observer, site.as_row()
    missing = sorted(channels - _globally_instrumented_channels())
    assert not missing, f"reachable channels with no observer: {missing}"

    # Non-vacuous: mutation authority is gated like everything else, so an
    # unconditional denial removes it entirely rather than silently keeping it.
    monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                        lambda *a, **k: _GATE_DENY_ALL)
    try:
        _, denied = _audit_source(_engine_source())
        assert _reachable_mutation_channels(denied) == set(), (
            "a mutation site survived an unconditional gate denial, so it is "
            "NOT gated and a shadowed module could still claim its observer")
    finally:
        monkeypatch.undo()
    _assert_closed_world(_engine_source())


def test_l_m_removing_the_exact_site_rule_lets_the_controls_through(
        monkeypatch):
    """L.M (section 4.14) The gate is load-bearing for the X8 controls.

    Neutralizing it must re-open EVERY injection the X8 controls rely on, so
    each control is discriminating rather than passing for an unrelated
    reason. Restored, the proof goes green.
    """
    # The injections the X8 gate is RESPONSIBLE for: each is refused today,
    # and every one of them must be admitted once the gate is off. If any is
    # still refused, its control is passing for a different reason and is not
    # discriminating the X8 rule at all.
    gate_injections = (
        ("roots.append(payload)", "_approved_roots", "roots.append"),
        ("roots = attacker; roots.append(payload)", "_approved_roots",
         "roots.append"),
        ("record = attacker; record.get('x')",
         "_classify_record_for_shell", "record.get"),
        ("os = attacker; os.stat(path)", "_load_transition_record",
         "os.stat"),
        ("hashlib = attacker; hashlib.sha256(b'x')", "_receipt_digest",
         "hashlib.sha256"),
        ("RecordSnapshot = attacker; RecordSnapshot(record)",
         "_read_record_snapshot_admitted", "RecordSnapshot"),
        ("_transitions_dir = attacker; _transitions_dir()",
         "_load_transition_record", "_transitions_dir"),
    )
    # Reported honestly rather than folded in: this one is caught by the X7X
    # SITE rule, which fires before the gate, so the gate cannot re-open it.
    # L.A is where it is proven; asserting it here keeps this control from
    # claiming credit for a rule it does not exercise.
    cross_owner = ("roots.append(payload)", "_load_transition_record",
                   "roots.append")
    refused = _refusals(_inject_into_reachable(cross_owner[0],
                                               into=cross_owner[1]))
    assert cross_owner[2] in refused, cross_owner
    assert "REVIEWED_RECEIVER_SITES" in refused[cross_owner[2]].reason, (
        f"the cross-owner case is no longer caught by the site rule: "
        f"{refused[cross_owner[2]].reason}")

    # Each must be refused BY THE GATE, not by an older rule that happens to
    # cover it too. This half is what keeps L.M sensitive to a mutation that
    # removes the gate -- without it, L.M would neutralize the gate itself and
    # could not notice the gate being gone.
    for injected, owner, expr in gate_injections:
        refusals = _refusals(_inject_into_reachable(injected, into=owner))
        assert expr in refusals, (
            f"{injected!r} in {owner} is not refused at all")
        reason = refusals[expr].reason
        assert ("EXACT_SITE_MANIFEST" in reason
                or "time(s)" in reason
                or "source context changed" in reason), (
            f"{injected!r} in {owner} is refused, but by an older rule rather "
            f"than by the X8 gate, so L.M would not discriminate the gate: "
            f"{reason}")

    monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                        _gate_off())
    try:
        reopened = []
        for injected, owner, expr in gate_injections:
            refusals = _refusals(_inject_into_reachable(injected, into=owner))
            if expr not in refusals:
                reopened.append((injected, expr))
        expected = [(i, e) for i, _, e in gate_injections]
        assert sorted(reopened) == sorted(expected), (
            f"neutralizing the gate did not re-open every X8-caught injection, "
            f"so those controls are not discriminating: still refused "
            f"{sorted(set(expected) - set(reopened))}")
    finally:
        monkeypatch.undo()
    _assert_closed_world(_engine_source())


def test_l_n_a_refusal_names_the_rule_and_both_identities():
    """L.N (section 4.15) A refusal must be adjudicable without the source.

    Required: owner, normalized expression, coordinate, the failed rule, and
    the EXPECTED and OBSERVED provenance identity. "This site was refused" is
    not enough to tell an unreviewed call from an edited owner.
    """
    claimed = REVIEWED_OWNER_DIGESTS["_approved_roots"]
    weakened = _inject_into_reachable("roots = attacker",
                                      into="_approved_roots")
    refusals = _refusals(weakened)
    hit = refusals["roots.append"]
    row = hit.as_row()
    for required in ("_approved_roots", "roots.append",
                     claimed[:16], "source context changed"):
        assert required in hit.reason or required in row, (
            f"the diagnostic omits {required!r}: {row}")
    assert hit.lineno > 0, row
    # The OBSERVED digest is named too, so expected and observed are both
    # present and an operator can see that the owner changed.
    observed = _audit_context(ast.parse(weakened))["digests"]
    assert observed["_approved_roots"] != claimed, (
        "the owner digest did not change, so this control no longer "
        "exercises the digest rule")
    assert observed["_approved_roots"][:16] in hit.reason, (
        f"the refusal does not name the observed provenance identity: "
        f"{hit.reason}")

    # The unreviewed-site case is a DIFFERENT diagnostic, not the same text.
    other = _refusals(_inject_into_reachable("roots.extend(payload)"))
    assert other["roots.extend"].reason != hit.reason
    assert "REVIEWED_RECEIVER_METHODS" in other["roots.extend"].reason

    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    assert "roots.append" in str(excinfo.value)


def test_l_o_the_x8_totals_are_measured_and_stable():
    """L.O (section 4) The reported totals, asserted rather than narrated.

    Every number the X8 evidence claims is computed here, so a drift fails the
    suite instead of silently making the evidence wrong -- the failure mode
    X5 exhibited and X6 corrected.
    """
    closure, sites = _assert_closed_world(_engine_source())
    granted = [s for s in sites if s.classification != CLASS_UNKNOWN]
    observed = {}
    for site in granted:
        key = (site.owner, site.expression)
        observed[key] = observed.get(key, 0) + 1

    context = _audit_context(ast.parse(_engine_source()))
    mismatches = [s for s in granted
                  if _site_authority(s.owner, s.expression, context)
                  is not None]
    measured = {
        "closure_functions": len(closure),
        "reachable_call_sites": len(sites),
        "exact_site_manifest": len(EXACT_SITE_MANIFEST),
        "owner_digests": len(REVIEWED_OWNER_DIGESTS),
        "duplicate_site_identities":
            len([s.identity for s in sites])
            - len({s.identity for s in sites}),
        "missing_manifest_entries": len(set(observed) -
                                       set(EXACT_SITE_MANIFEST)),
        "surplus_manifest_entries": len(set(EXACT_SITE_MANIFEST) -
                                       set(observed)),
        "provenance_mismatches": len(mismatches),
        "read_only": sum(1 for s in sites
                         if s.classification == CLASS_READ_ONLY),
        "internal": sum(1 for s in sites
                        if s.classification == CLASS_INTERNAL),
        "mutation": sum(1 for s in sites
                        if s.classification == CLASS_MUTATION),
        "unknown": len(_unknown_sites(sites)),
    }
    assert measured == X8_TOTALS, (
        "the X8 totals drifted from the recorded evidence: "
        + str({k: (measured[k], X8_TOTALS[k]) for k in X8_TOTALS
               if measured[k] != X8_TOTALS[k]}))
    assert len(EXACT_SITE_MANIFEST) == len(observed), (
        "manifest entries and distinct granted sites disagree")
    assert max(EXACT_SITE_MANIFEST.values()) == 7, (
        "the largest reviewed occurrence count moved; re-derive the evidence")
    assert sorted(_reachable_mutation_channels(sites)) == ["open", "os.open"]


# --------------------------------------------------------------------- #
# X7X: receiver BINDING provenance -- tuple, walrus, comprehension, lambda
# --------------------------------------------------------------------- #
#
# The question this section answers is two questions wearing one coat:
#   (1) can a receiver that IS a tuple / walrus / comprehension / lambda be
#       admitted?  -> K.A, and the answer is no;
#   (2) can one of those shapes, used as the BINDING that produces a reviewed
#       receiver NAME, inherit the review? -> K.B..K.F, and at df19763a3 the
#       answer was YES for all of them. K.G..K.M then show the repair did not
#       cost the real engine anything, and record what is still open.
#
# Every injection preserves the target function's NAME, so an anchor-only
# drift check cannot notice (the X5 blind spot).

_SHAPE_RECEIVERS = (
    # (label, injected source, normalized expression the refusal must name)
    ("tuple", "(a, b).replace(dst)", "tuple.replace"),
    ("tuple starred", "(*a, b).replace(dst)", "tuple.replace"),
    ("walrus", "(x := f()).replace(dst)", "ast.NamedExpr.replace"),
    ("list comprehension", "[f(i) for i in xs].append(v)",
     "ast.ListComp.append"),
    ("set comprehension", "{f(i) for i in xs}.append(v)",
     "ast.SetComp.append"),
    ("dict comprehension", "{k: v for k, v in xs}.update(v)",
     "ast.DictComp.update"),
    ("generator expression", "(f(i) for i in xs).append(v)",
     "ast.GeneratorExp.append"),
    ("lambda call", "(lambda: obj)().replace(dst)",
     "ast.Lambda(...).replace"),
)

# (label, owner, injected source, normalized expression, rule that must catch it)
#
# Every row is injected into an owner that DID review that exact triple, so the
# owner-scoping rule cannot mask the binding-form rule (which is what K.K and
# K.L need in order to discriminate them independently). The one row marked
# "site" is the exception and exists precisely because it is caught by the
# OTHER rule -- see K.F.
_BINDING_FORGERIES = (
    ("comprehension target", "_classify_record_for_shell",
     "[record.get(k) for record in externals]", "record.get", "form"),
    ("comprehension set target", "_assert_selector_authority_names",
     "{entry.stat() for entry in scanned}", "entry.stat", "form"),
    ("comprehension tuple target", "_approved_roots",
     "[part.strip() for part, other in pairs]", "part.strip", "form"),
    ("comprehension over unpacked name", "_assert_record_authority_names",
     "[name.startswith(x) for name, other in pairs]", "name.startswith",
     "form"),
    ("walrus target", "_classify_record_for_shell",
     "if (record := attacker): record.get('x')", "record.get", "form"),
    ("lambda parameter", "_bound_operation",
     "sorted(xs, key=lambda record: record.get('x'))", "record.get", "form"),
    ("for target", "_classify_record_for_shell",
     "for record in attacker: record.get('x')", "record.get", "form"),
    ("with target", "_classify_rollback_for_shell",
     "with attacker as promote: promote.get('x')", "promote.get", "form"),
    ("augmented assignment", "_thaw",
     "value += externals[0]; value.items()", "value.items", "form"),
    ("tuple unpack target", "_load_transition_record",
     "record, sink = unpacked(a); record.get('x')", "record.get", "site"),
)


def _measured_binding_forms():
    """Every binding form the closure actually uses. For the K.K loosening."""
    tree = ast.parse(_engine_source())
    funcs, closure = _authority_closure(tree)
    forms = set()
    for owner_bindings in _receiver_binding_forms(funcs, closure).values():
        for names in owner_bindings.values():
            forms |= set(names)
    return forms


def test_k_a_tuple_walrus_comprehension_and_lambda_receivers_fail_closed():
    """K.A A receiver that IS one of those four shapes is never admitted.

    Each shape normalizes to a spelling that is absent from every reviewed
    registry, so the receiver itself cannot buy authority. The expression the
    refusal MUST name is asserted, because a refusal for some unrelated reason
    (a refused helper, say) would not prove the receiver was checked.
    """
    for label, injected, expected in _SHAPE_RECEIVERS:
        weakened = _inject_into_reachable(injected)
        refusals = _refusals(weakened)
        assert expected in refusals, (
            f"{label} receiver {injected!r} was not refused as {expected!r}; "
            f"refused instead: {sorted(refusals)}")
        hit = refusals[expected]
        assert hit.owner == "_load_transition_record", hit.as_row()
        assert hit.classification == CLASS_UNKNOWN
        with pytest.raises(AssertionError):
            _assert_closed_world(weakened)


def test_k_b_the_named_shapes_are_absent_as_receivers_in_the_real_closure():
    """K.B Measured, not assumed: the real closure uses none of them.

    So K.A guards a shape the engine does not currently contain. That makes
    these controls NECESSARY rather than decorative -- a future comprehension
    receiver would otherwise be unproven -- and it is stated so nobody reads
    the green suite as coverage the engine actually exercises today.
    """
    tree = ast.parse(_engine_source())
    funcs, closure = _authority_closure(tree)
    banned = (ast.Tuple, ast.NamedExpr, ast.ListComp, ast.SetComp,
              ast.DictComp, ast.GeneratorExp, ast.Lambda)
    found = []
    for owner in sorted(closure):
        for call in ast.walk(funcs[owner]):
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Attribute):
                continue
            if isinstance(call.func.value, banned):
                found.append((owner, call.lineno,
                              type(call.func.value).__name__))
    assert not found, (
        f"a tuple/walrus/comprehension/lambda receiver now exists in the "
        f"closure and must be reviewed explicitly: {found!r}")


def test_k_c_a_comprehension_target_cannot_forge_a_reviewed_receiver():
    """K.C `[record.get(k) for record in externals]` was ADMITTED at X7.

    X7 bound the method to the receiver NAME and never to the VALUE, so a
    comprehension target that happens to spell a reviewed receiver inherits
    the whole review. The binding FORM is now part of the rule.
    """
    weakened = _inject_into_reachable(
        "[record.get(k) for record in externals]",
        into="_classify_record_for_shell")
    refusals = _refusals(weakened)
    assert "record.get" in refusals, (
        f"a comprehension target still forges the reviewed receiver; "
        f"refused: {sorted(refusals)}")
    reason = refusals["record.get"].reason
    assert "comprehension" in reason, (
        "the refusal does not name the binding form that forged the "
        f"receiver: {reason}")
    assert "_classify_record_for_shell" in reason, reason
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_k_d_a_walrus_target_cannot_forge_a_reviewed_receiver():
    """K.D `if (record := attacker): record.get(..)` was ADMITTED at X7."""
    weakened = _inject_into_reachable(
        "if (record := attacker): record.get('x')",
        into="_classify_record_for_shell")
    refusals = _refusals(weakened)
    assert "record.get" in refusals, (
        f"a walrus target still forges the reviewed receiver; refused: "
        f"{sorted(refusals)}")
    assert "walrus" in refusals["record.get"].reason, (
        refusals["record.get"].reason)
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_k_e_a_lambda_parameter_cannot_forge_a_reviewed_receiver():
    """K.E A lambda parameter is NOT a function parameter.

    `record` is legitimately a function parameter in the closure, so a rule
    that merely allowed `param` would admit `key=lambda record: record.get`.
    The lambda's own scope is invisible to the caller, which is why it is a
    separate form.
    """
    weakened = _inject_into_reachable(
        "sorted(xs, key=lambda record: record.get('x'))",
        into="_bound_operation")
    refusals = _refusals(weakened)
    assert "record.get" in refusals, (
        f"a lambda parameter still forges the reviewed receiver; refused: "
        f"{sorted(refusals)}")
    assert "lambda-param" in refusals["record.get"].reason, (
        refusals["record.get"].reason)
    index = _binding_form_index(ast.parse("f = lambda record: record"))
    assert index.get("record") == {"lambda-param"}, index
    index = _binding_form_index(ast.parse("def f(record): return record"))
    assert index.get("record") == {"param"}, index
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_k_f_tuple_unpacking_is_caught_by_the_site_rule_not_the_form_rule():
    """K.F Ordering fact, proven rather than assumed.

    `record` legitimately uses assign-unpack SOMEWHERE in the closure, so the
    form rule alone CANNOT catch `record, sink = unpacked(a)`. It is caught
    because that owner never reviewed `record.get`. If the reason here ever
    names the form rule instead, the proof has gone quiet on the real cause.
    """
    assert "assign-unpack" in REVIEWED_RECEIVER_BINDINGS["record"], (
        "this control assumes `record` tolerates assign-unpack; if that "
        "changed, re-derive which rule does the work")
    weakened = _inject_into_reachable(
        "record, sink = unpacked(a); record.get('x')")
    refusals = _refusals(weakened)
    assert "record.get" in refusals, (
        f"tuple-unpack target forging is no longer refused; refused: "
        f"{sorted(refusals)}")
    reason = refusals["record.get"].reason
    assert "REVIEWED_RECEIVER_SITES" in reason, (
        f"the refusal did not come from owner-scoping, so this control no "
        f"longer exercises what it claims: {reason}")
    assert "_load_transition_record" in reason, reason
    with pytest.raises(AssertionError):
        _assert_closed_world(weakened)


def test_k_g_for_with_and_augmented_targets_cannot_forge_a_receiver():
    """K.G Every binding form, refused, and by the RIGHT rule.

    Driven from the shared table, so each row also asserts which rule fired. A
    row silently caught by the other rule would still be green here, which is
    exactly the ordering mistake K.F is about.
    """
    for label, owner, injected, expr, rule in _BINDING_FORGERIES:
        weakened = _inject_into_reachable(injected, into=owner)
        refusals = _refusals(weakened)
        assert expr in refusals, (
            f"{label} forging is no longer refused as {expr!r}; refused: "
            f"{sorted(refusals)}")
        reason = refusals[expr].reason
        assert owner in reason, (
            f"{label}: the refusal does not name the owning function: "
            f"{reason}")
        if rule == "form":
            assert "unreviewed binding form" in reason, (
                f"{label} was expected to be caught by the binding-form "
                f"rule, not: {reason}")
        else:
            assert "REVIEWED_RECEIVER_SITES" in reason, (
                f"{label} was expected to be caught by owner-scoping, "
                f"not: {reason}")
        with pytest.raises(AssertionError):
            _assert_closed_world(weakened)


def test_k_h_an_except_handler_name_cannot_forge_a_reviewed_receiver():
    """K.H `except E as record:` binds `record`, and is measured as `except`."""
    index = _binding_form_index(ast.parse(
        "try:\n    pass\nexcept OSError as record:\n    record.get('x')\n"))
    assert index.get("record") == {"except"}, index
    assert "except" not in REVIEWED_RECEIVER_BINDINGS["record"], (
        "the except form is allowed for `record`, so this control no longer "
        "discriminates anything")


def test_k_i_every_real_reviewed_receiver_is_still_admitted():
    """K.I The repair must not make the policy too strict for real code.

    The mirror of J.E/J.F: a proof that refuses everything would also be
    closed-world. All 27 measured triples and all 40 sites behind them must
    still classify, through the reviewed rule.
    """
    _, sites = _assert_closed_world(_engine_source())
    assert not _unknown_sites(sites), (
        f"{len(_unknown_sites(sites))} reachable call site(s) became "
        "UNKNOWN; the X7X repair is too strict for the real engine")
    by_reason = {}
    for site in sites:
        by_reason.setdefault(site.reason, []).append(site)
    triple_sites = [s for r, group in by_reason.items() if "triple" in r
                    for s in group]
    assert len(triple_sites) == 40, (
        f"expected 40 sites admitted by the owner-scoped rule, got "
        f"{len(triple_sites)}; reasons: "
        + str({k: len(v) for k, v in sorted(by_reason.items())}))
    measured = {(s.owner, s.expression.split(".", 1)[0],
                 s.expression.rsplit(".", 1)[1]) for s in triple_sites}
    assert measured == set(REVIEWED_RECEIVER_SITES), (
        "the admitted triples drifted from the reviewed registry: "
        f"only-measured={sorted(measured - set(REVIEWED_RECEIVER_SITES))} "
        f"only-reviewed={sorted(set(REVIEWED_RECEIVER_SITES) - measured)}")


def test_k_j_the_reviewed_binding_forms_are_measured_not_invented():
    """K.J No dead tolerance: every allowed form is one the engine uses.

    A registry that grants a form nobody exercises is latent permission. Both
    directions are asserted: no allowed form is unused, and no measured form
    is missing from the registry (that would have made K.C..K.G vacuous).
    """
    tree = ast.parse(_engine_source())
    funcs, closure = _authority_closure(tree)
    bindings = _receiver_binding_forms(funcs, closure)
    measured = {}
    for owner in closure:
        for name, forms in bindings[owner].items():
            measured.setdefault(name, set()).update(forms)

    for receiver, allowed in sorted(REVIEWED_RECEIVER_BINDINGS.items()):
        assert any(receiver == r for _, r, _ in REVIEWED_RECEIVER_SITES), (
            f"{receiver!r} has binding forms reviewed but no reviewed "
            f"triple; the form registry is dead permission")
        got = measured.get(receiver, set())
        assert got == set(allowed), (
            f"binding-form registry drifted for {receiver!r}: measured="
            f"{sorted(got)} reviewed={sorted(allowed)}")
    assert set(measured) >= set(REVIEWED_RECEIVER_BINDINGS) - {
        "OPERATION_ID_RE", "_STATE_DISPATCH"}, (
        "a reviewed receiver name was not found in the closure at all")

    # Every form the walker can emit must be a label the module knows about,
    # or the K.K loosening would silently permit less than it claims.
    used = _measured_binding_forms()
    assert used <= ALL_BINDING_FORMS, (
        f"the closure emits binding form(s) outside ALL_BINDING_FORMS: "
        f"{sorted(used - ALL_BINDING_FORMS)}")
    # And every forgery must actually BIND something, or it discriminates
    # nothing no matter how the registry is loosened.
    for label, _owner, injected, _expr, _rule in _BINDING_FORGERIES:
        forged = set()
        for names in _binding_form_index(ast.parse(injected)).values():
            forged |= set(names)
        assert forged, (
            f"the {label!r} forgery binds no name, so it cannot discriminate")
        assert forged <= ALL_BINDING_FORMS, (
            f"the {label!r} forgery produced binding form(s) outside "
            f"ALL_BINDING_FORMS: {sorted(forged - ALL_BINDING_FORMS)}")


def test_k_k_dropping_the_binding_form_rule_reopens_the_hole(monkeypatch):
    """K.K The binding-form rule is load-bearing, not decorative.

    Same shape as J.J: loosen the form registry and the forging injections --
    each injected into an owner that DID review the triple, so owner-scoping
    cannot mask the result -- must become ADMITTED again. Then restore the
    registry and the proof must go green.

    X8 NOTE. Loosening the form registry alone is no longer sufficient to
    re-open the hole, because the exact-site gate refuses these injections on
    its own. That is not this control going vacuous -- it is a SECOND rule
    covering the same ground. So the exact-site gate is neutralized for the
    duration, which is what isolates the form rule and keeps this control
    discriminating. K.X (section L) proves the reverse isolation.
    """
    saved_bindings = dict(REVIEWED_RECEIVER_BINDINGS)
    saved_gate = _site_authority
    loosened = {name: frozenset(ALL_BINDING_FORMS) for name in saved_bindings}
    assert loosened["record"] != saved_bindings["record"], (
        "the loosening is a no-op; this control would be vacuous")
    monkeypatch.setattr(
        sys.modules[__name__], "REVIEWED_RECEIVER_BINDINGS", loosened)
    monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                        lambda *a, **k: None)
    try:
        reopened = []
        for label, owner, injected, expr, rule in _BINDING_FORGERIES:
            if rule != "form":
                continue  # caught by owner-scoping, not by the form rule
            refusals = _refusals(_inject_into_reachable(injected, into=owner))
            if expr not in refusals:
                reopened.append(label)
        assert sorted(reopened) == sorted(
            label for label, _, _, _, rule in _BINDING_FORGERIES
            if rule == "form"), (
            f"loosening the binding-form rule did NOT re-open every form-rule "
            f"forgery; still refused: "
            f"{sorted(set(label for label, _, _, _, r in _BINDING_FORGERIES if r == 'form') - set(reopened))}")
    finally:
        monkeypatch.setattr(sys.modules[__name__],
                            "REVIEWED_RECEIVER_BINDINGS", saved_bindings)
        monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                            saved_gate)
    _assert_closed_world(_engine_source())


def test_k_l_dropping_the_site_rule_reopens_cross_function_forging(
        monkeypatch):
    """K.L Owner-scoping is load-bearing too, and separately so.

    Loosening only the FORM registry must not admit `record.get` in a
    function that never reviewed it -- that is what K.F relies on.
    """
    saved = dict(REVIEWED_RECEIVER_BINDINGS)
    every_form = ALL_BINDING_FORMS
    loosened = {name: frozenset(every_form) for name in saved}
    monkeypatch.setattr(
        sys.modules[__name__], "REVIEWED_RECEIVER_BINDINGS", loosened)
    try:
        refusals = _refusals(_inject_into_reachable(
            "record = externals[0]; record.get('x')"))
        assert "record.get" in refusals, (
            "owner-scoping failed to refuse record.get in "
            "_load_transition_record; K.F is no longer discriminated by the "
            "site rule")
        assert "REVIEWED_RECEIVER_SITES" in refusals["record.get"].reason
    finally:
        monkeypatch.setattr(sys.modules[__name__],
                            "REVIEWED_RECEIVER_BINDINGS", saved)
    _assert_closed_world(_engine_source())


def test_k_m_the_x7x_value_provenance_residual_is_now_closed(monkeypatch):
    """K.M X7X recorded an OPEN residual here. X8 CLOSES it.

    X7X refused a reviewed receiver name bound by a form the review does not
    cover. It could not follow the VALUE, so a receiver rebound by a form the
    review DOES cover, inside a function that DID review that pair, was still
    admitted:

      * `record = externals[0]; record.get('x')` in `_classify_record_for_shell`
        -- `assign` is a reviewed form for `record` there;
      * `for entry in attacker: entry.stat()` in
        `_assert_selector_authority_names` -- `for` is already a reviewed form
        for `entry` there, so a second for-binding added no NEW form.

    K.M previously ASSERTED these were still open, and instructed that if one
    ever closed the evidence must be rewritten rather than the control deleted.
    One has closed, so this control is rewritten -- not removed -- and it keeps
    the same job: it fails if the boundary ever moves again in either
    direction.

    The closure is attributed, not just observed: neutralizing the exact-site
    gate must make both injections ADMITTED again, which proves X8 is what
    closed them and that the X7X rules alone never could.
    """
    residuals = (
        ("assign in a reviewed owner",
         "record = externals[0]; record.get('x')",
         "_classify_record_for_shell", "record.get"),
        ("repeat for-binding of a reviewed receiver",
         "for entry in attacker: entry.stat()",
         "_assert_selector_authority_names", "entry.stat"),
    )
    for label, injected, owner, expr in residuals:
        weakened = _inject_into_reachable(injected, into=owner)
        refusals = _refusals(weakened)
        assert expr in refusals, (
            f"the X7X value-provenance residual {label!r} is OPEN again, so "
            f"the X8 exact-site gate is not holding it closed; refused: "
            f"{sorted(refusals)}")
        reason = refusals[expr].reason
        assert "source context changed" in reason or "manifest" in reason, (
            f"{label}: the residual is refused, but not by the X8 exact-site "
            f"rule, so the attribution is wrong: {reason}")
        with pytest.raises(AssertionError):
            _assert_closed_world(weakened)

    # Attribution, and the negative control section 2 requires: with the new
    # gate neutralized, the SAME injections are admitted, so they were open at
    # X7X and X8 is the thing that closed them.
    saved_gate = _site_authority
    monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                        lambda *a, **k: None)
    try:
        for label, injected, owner, expr in residuals:
            refusals = _refusals(_inject_into_reachable(injected, into=owner))
            assert expr not in refusals, (
                f"{label} is refused even with the X8 gate neutralized, so "
                f"this control no longer demonstrates what it claims")
    finally:
        monkeypatch.setattr(sys.modules[__name__], "_site_authority",
                            saved_gate)
    _assert_closed_world(_engine_source())


def test_k_n_a_refusal_names_the_owner_expression_form_and_coordinate():
    """K.X An operator must be able to adjudicate a refusal without the source.

    X7 required owner + normalized expression + coordinate + reason. X7X adds
    the binding form, because "record.get is refused" without "because
    `record` is walrus-bound here" does not say what to fix.
    """
    weakened = _inject_into_reachable(
        "if (record := attacker): record.get('x')",
        into="_classify_record_for_shell")
    refusals = _refusals(weakened)
    hit = refusals["record.get"]
    for required in ("_classify_record_for_shell", "record.get", "walrus",
                     "reviewed forms"):
        assert required in hit.reason or required in hit.as_row(), (
            f"the diagnostic omits {required!r}: {hit.as_row()}")
    with pytest.raises(AssertionError) as excinfo:
        _assert_closed_world(weakened)
    message = str(excinfo.value)
    for required in ("_classify_record_for_shell", "record.get", "walrus"):
        assert required in message, (
            f"the failure message omits {required!r}: {message}")


RECORD_SIZE_ANCHORS = (
    ("        if first.st_size > _RECORD_MAX_BYTES:",
     "        if False and first.st_size > _RECORD_MAX_BYTES:"),
    ("            if total > _RECORD_MAX_BYTES:",
     "            if False and total > _RECORD_MAX_BYTES:"),
)


def _unbounded_record_engine(tmp_path):
    """A copy of the engine with the record size bound removed."""
    source = CLI.read_text(encoding="utf-8")
    for old, new in RECORD_SIZE_ANCHORS:
        assert source.count(old) == 1, (
            f"the record size anchor is stale or ambiguous: {old!r} occurs "
            f"{source.count(old)} times")
        source = source.replace(old, new)
    path = Path(tmp_path) / "unbounded-record-pg-recovery.py"
    path.write_text(source, encoding="utf-8")
    compile(source, str(path), "exec")
    return path


def _oversized_record(transitions, record):
    """Publish a CANONICAL record above `_RECORD_MAX_BYTES`.

    Valid JSON on purpose. A record that is merely invalid JSON would be
    refused by the parser, and the refusal would prove nothing about the
    size bound.
    """
    padded = dict(record)
    padded["_oversize_padding"] = "x" * (pgrec._RECORD_MAX_BYTES + 4096)
    path = transitions / f"{OPID}.json"
    path.write_bytes(_bytes(padded))
    os.chmod(path, 0o600)
    return path


def test_g_an_oversized_record_denial_is_inert(tmp_path):
    """G.3 An actually oversized record is refused, and nothing moves.

    This test used to build a NORMAL record, call acquisition, and assert
    only that the census was unchanged -- so acquisition SUCCEEDED, the
    oversized case was never exercised, and a rename of the test would have
    kept passing. The name described an event that did not occur.
    """
    transitions, record, promote, receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = _oversized_record(transitions, record)
    assert path.stat().st_size > pgrec._RECORD_MAX_BYTES, (
        "the fixture is not actually oversized")
    # The governed coordinate and the required permissions are preserved, so
    # the ONLY thing wrong with this record is its size.
    assert path.name == f"{OPID}.json"
    if os.name != "nt":
        assert (path.stat().st_mode & 0o777) == 0o600

    census_before = _census(pgrec._transitions_dir())
    outside_before = _census(receipt.parent)

    with _MutationTripwire(pgrec) as trip:
        bundle = pgrec._acquire_recovery_authority(OPID, promote)
        # The public classification routes must fail closed too, and must not
        # reach a decision from the bytes that were on disk.
        direct = pgrec._classify_record_for_shell(record, promote)
        shell = pgrec._classify_rollback_for_shell(str(receipt))

    # The oversized record is refused, whole.
    assert bundle.record is None, "an oversized record was admitted"
    assert bundle.record_snapshot.present is False
    assert bundle.record_digest is None
    # No truncated record is admitted: the refusal is RECORDED on the
    # snapshot, and no digest binds the bytes that were on disk.
    assert bundle.record_snapshot.read_error, (
        "the oversized record was not recorded as refused: "
        f"{bundle.record_snapshot}")
    # No downstream decision uses partial bytes.
    assert direct == 4, f"the direct route decided on an oversized record: {direct}"
    assert shell == 4, f"the shell route decided on an oversized record: {shell}"
    # And the engine wrote nothing to make any of that true.
    assert trip.mutations == [], f"the denial mutated authority: {trip.mutations!r}"

    # Every governed artifact -- record, claim, receipt, any temporary --
    # byte-identical. Nothing created, removed, replaced or rewritten.
    assert _census(pgrec._transitions_dir()) == census_before
    assert _census(receipt.parent) == outside_before


def test_g_an_oversized_control_becomes_reachable_without_the_bound(
        tmp_path):
    """G.4 Without the size bound, the oversized record IS admitted.

    The denial proof in G.3 is only meaningful if the bound is what refuses
    the record. This control removes both size comparisons from a copy of
    the shipped engine and requires the same record to become observably
    reachable, so a green G.3 means "the bound held", not "the test setup
    happened to be refused for some other reason".
    """
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = _oversized_record(transitions, record)
    assert path.stat().st_size > pgrec._RECORD_MAX_BYTES

    weak = _import(_unbounded_record_engine(tmp_path), "r48r3_g_oversized_weak")
    weak._bind_test_recovery_root(str(transitions.parents[0]))

    bundle = weak._acquire_recovery_authority(OPID, promote)
    assert bundle.record is not None, (
        "removing the record size bound did not make the oversized record "
        "reachable, so the denial proof discriminates nothing")
    assert bundle.record.get("_oversize_padding"), (
        "the admitted record is not the oversized one")
    assert bundle.record_snapshot.present is True
    assert bundle.record_digest, "an admitted record must bind a digest"


# --------------------------------------------------------------------- #
# M: the owner digest must be a function of the SOURCE, not the INTERPRETER
# --------------------------------------------------------------------- #
#
# X8's baseline is reviewed evidence only if its value depends on the source
# alone. The first implementation used `ast.dump`, which depends on the source
# AND the interpreter: CPython 3.12 appended `type_params` to
# `FunctionDef._fields`, so all 35 frozen digests moved on the Linux runner
# while all 35 stayed green on a 3.11 developer machine. Identical source,
# identical coordinates, identical 312 reachable call sites, identical
# manifest -- only the serialisation differed.
#
# The consequence was not cosmetic. Every grant in every owner was withdrawn,
# the closure reported 313 UNKNOWN_OR_DYNAMIC sites against a baseline that
# was correct, and b1 went 33-red. A baseline whose value depends on WHERE the
# proof runs is a second, hidden baseline, and no reviewed artifact may have
# one.
#
# X9 CORRECTION. X8's repair then made the digest stable by DROPPING the
# interpreter-added field, and by emitting fields in the interpreter's own
# order. Both made the baseline blind: `type_params` carries PEP 695 lexical
# bindings, and permuting `_fields` -- same values, same source -- moved the
# digest. M.A..M.F now prove the corrected law in both directions: the schema
# is ENUMERATED from the real source with NO exceptions (M.A), the digest is
# sensitive to every meaning-bearing edit including type parameters (M.B),
# coordinate-neutral (M.C), normalises a missing 3.11 `type_params` to the
# same canonical value as 3.12's empty list while a NON-empty one moves the
# digest (M.D), fails CLOSED when the schema drops a field instead of
# silently ignoring it (M.E), and the frozen literals validate under the
# 3.12 AST shape (M.F). The N section adds the type-parameter authority
# proofs and the real PEP 695 syntax controls.


# X9 REMOVED `_INTERPRETER_FIELD_ADDITIONS`. Its one entry, `type_params`, is
# now a REAL part of the canonical schema, and there is no exception set any
# more: a field the schema does not name makes the serializer raise
# `_UnreviewedAstFieldError`, so an interpreter-added field is a RED proof and
# an operator review decision -- never a silent exclusion.


def _digest_of_snippet(source):
    """Digest the first module-level function of a source snippet."""
    module = ast.parse(source)
    func = next(node for node in module.body
                if isinstance(node, ast.FunctionDef))
    return _owner_ast_digest(func)


def _synthetic_type_var(name, bound=None):
    """The 3.12 AST shape of one type parameter, without the 3.12 parser.

    CPython 3.12 documents `TypeVar(identifier name, expr? bound)`. A dynamic
    stand-in with the same kind name and the same fields lets the 3.11 suite
    exercise the CONSUMER side of the defect faithfully; the 3.12 runner
    additionally parses real `def f[os](): ...` syntax and compares the two
    shapes (`test_n_d_*`), so the simulation is not merely asserted to be
    equivalent -- it is measured against the real thing on the real runner.
    """
    cls = type("TypeVar", (ast.AST,), {"_fields": ("name", "bound")})
    node = cls()
    node.name = name
    node.bound = bound
    return node


def _digest_with_type_params(source, params):
    """The snippet's digest with `params` PRESENTED as `type_params`.

    Presentation is native on 3.12 and synthetic on 3.11 (see
    `_present_type_params`); either way the field is serialised, so a
    non-empty parameter must move the digest on BOTH interpreters.
    """
    func = ast.parse(source).body[0]
    saved = _present_type_params(func, list(params))
    try:
        return _owner_ast_digest(func)
    finally:
        _restore_type_params(func, saved)


def test_m_a_the_frozen_vocabulary_drops_no_meaning_bearing_field():
    """M.A Every real field is in the vocabulary, or a named addition.

    The vocabulary was first assembled by READING it, and reading missed
    `id`. That made every identifier in the owner invisible to the digest, so
    a rename or a rebound receiver could not withdraw anything -- the exact
    sensitivity X8 exists to provide, absent, and completely invisible to
    inspection. This control ENUMERATES the fields of the real closure and
    fails on any dropped name that is not a documented interpreter addition.
    """
    funcs, closure = _authority_closure(ast.parse(_engine_source()))
    dropped = {}
    for owner in closure:
        for node in ast.walk(funcs[owner]):
            for field in node._fields:
                if field not in _STABLE_AST_FIELDS:
                    dropped.setdefault(field, set()).add(type(node).__name__)
    assert not dropped, (
        "the frozen schema drops field(s) that carry meaning: "
        + repr({name: sorted(dropped[name])
                for name in sorted(dropped)}))
    for required in ("id", "type_params"):
        assert required in _STABLE_AST_FIELDS, (
            f"{required!r} is missing from the canonical schema; its absence "
            "was already one recorded defect -- a bare rename, and a PEP 695 "
            "lexical binding, respectively")
    # There is no exception set left for a future addition to hide behind.
    assert "_INTERPRETER_FIELD_ADDITIONS" not in globals(), (
        "an interpreter-field exception set is back in the proof; an "
        "unreviewed field must be RED, not excused")


def test_m_b_the_digest_moves_on_every_condition_the_mission_requires():
    """M.B Rebinding, shadowing, duplication, addition and reordering move it.

    A digest that cannot move is a digest that cannot withdraw a grant. These
    are the five edits X8 section 3 requires it to detect, plus a bare rename,
    which the original vocabulary could not see at all.
    """
    base = _digest_of_snippet("def _f():\n    values.append(item)\n")
    for label, source in (
        ("a receiver rebound",
         "def _f():\n    values = attacker\n    values.append(item)\n"),
        ("a module shadowed",
         "def _f():\n    os = attacker\n    os.stat(path)\n"),
        ("a call duplicated",
         "def _f():\n    values.append(item)\n    values.append(item)\n"),
        ("a call added",
         "def _f():\n    values.append(item)\n    roots.append(item)\n"),
        ("statements reordered",
         "def _f():\n    item = 1\n    values.append(item)\n"),
        ("a bare rename",
         "def _f():\n    values.append(other)\n"),
        ("a receiver renamed",
         "def _f():\n    externals.append(item)\n"),
    ):
        assert _digest_of_snippet(source) != base, (
            f"the digest is INSENSITIVE to {label}, so that edit would not "
            "withdraw a grant")
    # X9: a NON-EMPTY type parameter is the edit the first normalisation
    # repair dropped. It must move the digest whether it shadows a reviewed
    # name (`os`, `hashlib`) or is harmless (`T`), because either way it is a
    # lexical binding that a reviewer must decide about.
    plain = "def _f():\n    os.stat(path)\n"
    plain_digest = _digest_of_snippet(plain)
    for name in ("T", "os", "hashlib"):
        moved = _digest_with_type_params(plain, [_synthetic_type_var(name)])
        assert moved != plain_digest, (
            f"a type parameter [{name}] did NOT move the digest, so a PEP 695 "
            "lexical binding could change name resolution and withdraw "
            "nothing")
    # ...and an EMPTY presentation is the version-normalisation case: it must
    # NOT move it, or every 3.11/3.12 ordinary definition would red the proof.
    assert _digest_with_type_params(plain, []) == plain_digest, (
        "an empty type_params moved the digest, so ordinary definitions are "
        "not version-normalised")


def test_m_c_the_digest_ignores_coordinates_and_indentation():
    """M.C Stable under shifts, so re-indenting cannot satisfy the baseline.

    Section 3 requires coordinates to stay diagnostic. If the digest moved on
    a line shift, every legitimate reformat would red the proof and the
    baseline would be unusable; if it did NOT move on a semantic edit, it
    would authorise nothing. Both halves are asserted together on purpose.
    """
    source = "def _f():\n    values.append(item)\n"
    base = _digest_of_snippet(source)
    assert _digest_of_snippet("\n\n\n\n" + source) == base, (
        "a line shift moved the digest")
    assert _digest_of_snippet(source.replace("\n    ", "\n        ")) == base, (
        "re-indenting moved the digest")
    assert _digest_of_snippet(source) != \
        _digest_of_snippet(source.replace("item", "other")), (
        "a rename did NOT move the digest while a shift did not either, so "
        "this control discriminates nothing")


def _present_type_params(node, value):
    """Make `type_params` present the way THIS interpreter would carry it.

    On 3.12 and later the field is NATIVE. On 3.11 it has to be simulated by
    appending it to the node CLASS's `_fields`, which is the MECHANISM: 3.12
    appended the field to `_fields`, and the canonical serializer checks
    exactly that vocabulary (and normalises a missing field's value to the
    empty list, so the two worlds agree). Returns
    `(saved_fields, synthetic, prior)`.
    """
    cls = type(node)
    original = cls._fields
    synthetic = "type_params" not in original
    prior = (hasattr(node, "type_params"),
             getattr(node, "type_params", None))
    if synthetic:
        cls._fields = original + ("type_params",)
    node.type_params = value
    return (original, synthetic, prior)


def _restore_type_params(node, saved):
    """Undo `_present_type_params` exactly, native case included.

    Returning the class to its own `_fields` is not enough where the field is
    NATIVE: the test's value would stay on the shared node. The prior attribute
    state is restored too, so no control can observe another's residue.
    """
    cls = type(node)
    original, synthetic, (had, prior) = saved
    cls._fields = original
    if synthetic or not had:
        if hasattr(node, "type_params"):
            del node.type_params
    else:
        node.type_params = prior


def test_m_d_missing_type_params_normalise_to_the_empty_list():
    """M.D The version boundary is normalised on the VALUE, not by dropping.

    X8's M.D asserted the digest was UNMOVABLE by `type_params`. That
    assertion is now inverted, because it WAS the defect: the first
    version-normalisation repair discarded a meaning-bearing field. The law
    X9 requires has two directions, both asserted here:

      * an interpreter whose nodes lack `type_params` (3.11) and an
        interpreter that carries it natively (3.12+) produce the SAME
        canonical value for a NON-generic definition -- the empty list;
      * a NON-empty type parameter MOVES the digest on either interpreter.

    The negative control keeps the simulation honest: `ast.dump` must move
    when the presented field changes, so a dead simulation cannot satisfy
    the second assertion.
    """
    funcs, _closure = _authority_closure(ast.parse(_engine_source()))
    node = funcs["_acquire_recovery_authority"]
    clean = _owner_ast_digest(node)          # 3.11: no type_params at all
    param = _synthetic_type_var("T")
    saved = _present_type_params(node, [])
    try:
        empty_digest = _owner_ast_digest(node)
        empty_dump = ast.dump(node, annotate_fields=True,
                              include_attributes=False)
        node.type_params = [param]
        filled_digest = _owner_ast_digest(node)
        filled_dump = ast.dump(node, annotate_fields=True,
                               include_attributes=False)
    finally:
        _restore_type_params(node, saved)
    # Version normalisation: an ABSENT field and an EMPTY list are one value.
    assert empty_digest == clean, (
        "presenting an empty type_params moved the digest, so the 3.11/3.12 "
        "normalisation is not value-level")
    # The meaning-bearing direction: a non-empty parameter MUST move it.
    assert filled_digest != clean, (
        "a non-empty type parameter did NOT move the reviewed digest, so a "
        "PEP 695 lexical binding can change name resolution without "
        "withdrawing any grant")
    # Negative control: the mechanism is live.
    assert filled_dump != empty_dump, (
        "changing the version field did not change `ast.dump`, so this "
        "control does not reproduce the shape it claims to")
    # And nothing leaked into the tree the other controls share.
    assert _owner_ast_digest(node) == clean, "the control leaked a mutation"


def test_m_e_dropping_a_schema_field_fails_closed(monkeypatch):
    """M.E The schema is load-bearing: removing a field is RED, not quiet.

    The mutation this control is written against is exactly the X8 defect -- a
    meaning-bearing field silently dropped from the vocabulary. With the
    canonical serializer, dropping `type_params` (or any of the names whose
    absence was already a recorded defect) must make the digest RAISE and name
    the node type and the field, never return a digest computed without it.
    The negative control is the other direction: with the shipped schema, the
    same trees digest normally.
    """
    module = sys.modules[__name__]
    schema = _STABLE_AST_FIELDS
    snippets = {
        "id": "def _f():\n    return x\n",
        "name": "def _f():\n    pass\n",
        "body": "def _f():\n    pass\n",
        "args": "def _f(a):\n    pass\n",
        "func": "def _f():\n    g()\n",
        "value": "def _f():\n    return 1\n",
        "type_params": "def _f():\n    pass\n",
    }
    for dropped, source in snippets.items():
        func = ast.parse(source).body[0]
        saved = None
        if dropped == "type_params":
            saved = _present_type_params(func, [_synthetic_type_var("T")])
        try:
            # Negative control: with the shipped schema the snippet digests.
            assert _owner_ast_digest(func), "the snippet did not digest"
            monkeypatch.setattr(module, "_STABLE_AST_FIELDS",
                                schema - {dropped})
            with pytest.raises(_UnreviewedAstFieldError) as caught:
                _owner_ast_digest(func)
            message = str(caught.value)
            assert f".{dropped}:" in message, (
                f"dropping {dropped!r} from the canonical schema did not name "
                f"it in the failure: {message}")
            monkeypatch.setattr(module, "_STABLE_AST_FIELDS", schema)
        finally:
            if saved is not None:
                _restore_type_params(func, saved)


def test_m_f_the_frozen_digests_validate_under_the_3_12_ast_shape():
    """M.F The frozen literals must hold on the interpreter b1 actually uses.

    Every frozen digest was GENERATED on 3.11.9. b1 runs 3.12.14. A literal
    that validates only where it was made is not evidence, and this module has
    already been red once for exactly that reason.

    So this control puts the running interpreter into the 3.12 shape -- where
    `type_params` is present on FunctionDef, AsyncFunctionDef and ClassDef --
    and then re-runs the comparison that FAILED on the runner: every frozen
    owner digest, and the whole closed-world audit, against the shipped
    engine.

    Stated boundary, because it matters: this faithfully reproduces the one
    documented 3.12 AST change that caused the failure. It cannot prove there
    are no OTHER 3.12 AST differences, and it does not claim to. The authority
    for that is the b1 run on 3.12 itself.
    """
    saved_fields = [(cls, cls._fields) for cls in
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)]
    try:
        for cls, fields in saved_fields:
            # On 3.12 the field is already native and this is a no-op, which
            # is the point: the SAME frozen literals must validate under the
            # real shape there and under the simulated shape on 3.11.
            if "type_params" not in fields:
                cls._fields = fields + ("type_params",)
        source = _engine_source()
        tree = ast.parse(source)
        funcs, closure = _authority_closure(tree)
        mismatched = sorted(
            owner for owner in closure
            if _owner_ast_digest(funcs[owner])
            != REVIEWED_OWNER_DIGESTS.get(owner))
        assert not mismatched, (
            "frozen digests are interpreter-dependent; these owners moved "
            "under the 3.12 AST shape: " + repr(mismatched))
        _assert_closed_world(source, label="engine under the 3.12 AST shape")
    finally:
        for cls, fields in saved_fields:
            cls._fields = fields
    # The simulation left nothing behind: the real 3.11 shape still validates.
    _assert_closed_world(_engine_source())


# --------------------------------------------------------------------- #
# N: PEP 695 TYPE PARAMETERS ARE REAL AUTHORITY-RELEVANT BINDINGS (X9)
# --------------------------------------------------------------------- #
#
# The X8 blind spot, reproduced before this repair (the measured probe is
# recorded next to `_STABLE_AST_FIELDS`): `_INTERPRETER_FIELD_ADDITIONS`
# excluded `type_params` as "merely interpreter metadata", so
# `def f[os](): os.stat(path)` kept the reviewed digest, the binding walker
# did not report `os`, the manifest and occurrence count were unchanged, and
# the site still took PROVEN_READ_ONLY_OR_PURE. A PEP 695 type parameter
# creates a lexical scope visible inside the generic body, so name resolution
# really changed while every string-matching rule kept matching.
#
# N.A..N.G prove the repair against the REAL engine source, so the manifest,
# occurrence counts and frozen digests all apply as they do in production.
# The type-parameter refusal is deliberately INDEPENDENT of the owner digest:
# N.B neutralises the exact-site gate and shows the binding rule alone still
# refuses, naming the binding form `type-param` and the shadowed name. N.D and
# N.E are the REAL PEP 695 syntax controls, gated to CPython 3.12+ -- the
# interpreter b1 runs. On 3.11 they SKIP and the synthetic-shape controls run
# instead; the boundary claim is exactly "validated on CPython 3.11 and 3.12",
# never arbitrary future-version independence.
PEP695_SYNTAX = sys.version_info >= (3, 12)


def _snippet_binding_context(node, owner="f"):
    """A minimal context for auditing a SNIPPET that is not in the closure.

    Only the measured binding data is real. The manifest/digest maps are
    deliberately empty: these controls prove the BINDING-side refusal, which
    must fire BEFORE any site authority is consulted, so a snippet that has
    no reviewed manifest entry can still be refused for the right reason.
    """
    index = _binding_form_index(node)
    return {
        "definitions": set(),
        "bindings": {owner: {n: frozenset(f) for n, f in index.items()}},
        "type_params": {owner: frozenset(
            n for n, f in index.items() if "type-param" in f)},
        "digests": {},
        "counts": {},
        "funcs": {},
        "closure": set(),
    }


def _shadowed_owner_call(owner, expr, params):
    """The engine tree with `owner` carrying `params`, plus the named call.

    Returns `(tree, node, call, saved)`; the caller restores `saved` in a
    finally block. The tree is the REAL engine source, so the manifest, the
    occurrence count and the frozen digest all apply exactly as they do in
    production.
    """
    tree = ast.parse(_engine_source())
    funcs, _closure = _authority_closure(tree)
    node = funcs[owner]
    call = next(c for c in ast.walk(node)
                if isinstance(c, ast.Call)
                and _normalized_call_expression(c) == expr)
    saved = _present_type_params(node, list(params))
    return tree, node, call, saved


def test_n_a_a_type_parameter_is_reported_as_a_real_binding():
    """N.A The walker reports every type-parameter name with form `type-param`.

    The refusal is computed from this walker, so it is tested directly, with
    a negative control: with no type parameters the name is NOT bound; with
    one presented it IS -- on whichever interpreter is running (native 3.12
    shape or the exact 3.11 simulation). ClassDef is covered too, because
    the language permits type parameters there as well.
    """
    assert "type-param" in ALL_BINDING_FORMS
    for reviewed in REVIEWED_RECEIVER_BINDINGS.values():
        assert "type-param" not in reviewed, (
            "a type parameter must never be a REVIEWED form; it is a refusal "
            "form, not an admissible one")
    tree = ast.parse(_engine_source())
    funcs, closure = _authority_closure(tree)
    owner = "_admit_record_descriptor"
    node = funcs[owner]
    assert _type_param_bindings(funcs, closure)[owner] == frozenset()
    saved = _present_type_params(node, [_synthetic_type_var("os")])
    try:
        funcs, closure = _authority_closure(tree)
        assert _type_param_bindings(funcs, closure)[owner] == frozenset({"os"}), (
            "the type parameter was not reported as a binding")
        index = _binding_form_index(node)
        assert "type-param" in index["os"], index
        forms = _receiver_binding_forms(funcs, closure)
        assert forms[owner]["os"] == frozenset({"type-param"}), forms[owner]
    finally:
        _restore_type_params(node, saved)
    # The binding proof went back to the shipped state.
    funcs, closure = _authority_closure(ast.parse(_engine_source()))
    assert _type_param_bindings(funcs, closure)[owner] == frozenset()
    # ClassDef definitions bind their type parameters the same way.
    class_node = ast.parse("class _C:\n    pass\n").body[0]
    class_saved = _present_type_params(class_node, [_synthetic_type_var("os")])
    try:
        assert "type-param" in _binding_form_index(class_node).get("os", set())
    finally:
        _restore_type_params(class_node, class_saved)


@pytest.mark.parametrize("owner,expr,shadow", [
    ("_admit_record_descriptor", "os.stat", "os"),
    ("_receipt_digest", "hashlib.sha256", "hashlib"),
    ("_read_record_snapshot_admitted", "RecordSnapshot", "RecordSnapshot"),
    ("_derive_claim_coordinate", "_transitions_dir", "_transitions_dir"),
])
def test_n_b_a_type_parameter_cannot_shadow_a_reviewed_name(owner, expr, shadow):
    """N.B A type parameter shadowing a reviewed name is refused, BY NAME.

    The four cases are the ones the mission names: a qualified module head
    (`os`), a second qualified module (`hashlib`), a reviewed constructor and
    a module-level engine definition. Three independent facts are asserted:

      * the owner digest moved (the field is serialised);
      * with the exact-site gate AVAILABLE the site is refused;
      * with the gate NEUTRALISED -- so the digest cannot refuse -- the
        binding rule ALONE still refuses, naming `type-param` and the
        shadowed name. That is the proof the refusal does not depend only on
        the owner digest.

    The negative control runs first: the same call without the type parameter
    is granted, so the refusal is caused by the shadow.
    """
    tree = ast.parse(_engine_source())
    funcs, _closure = _authority_closure(tree)
    plain = _classify_call(owner, next(
        c for c in ast.walk(funcs[owner])
        if isinstance(c, ast.Call)
        and _normalized_call_expression(c) == expr), _audit_context(tree))
    assert plain.classification != CLASS_UNKNOWN, plain.as_row()

    tree, node, call, saved = _shadowed_owner_call(
        owner, expr, [_synthetic_type_var(shadow)])
    try:
        context = _audit_context(tree)
        assert shadow in context["type_params"][owner]
        assert context["digests"][owner] != REVIEWED_OWNER_DIGESTS[owner], (
            "the type parameter did not move the owner digest")
        refused = _classify_call(owner, call, context)
        assert refused.classification == CLASS_UNKNOWN, refused.as_row()
        saved_gate = _site_authority
        try:
            sys.modules[__name__]._site_authority = _gate_off()
            bound_only = _classify_call(owner, call, context)
        finally:
            sys.modules[__name__]._site_authority = saved_gate
        assert bound_only.classification == CLASS_UNKNOWN, (
            "with the exact-site gate neutralised, a type parameter "
            f"shadowing {shadow!r} was ADMITTED by the spelling rule: "
            f"{bound_only.as_row()}")
        assert "type-param" in bound_only.reason, bound_only.reason
        assert shadow in bound_only.reason, bound_only.reason
    finally:
        _restore_type_params(node, saved)


def test_n_c_a_harmless_type_parameter_still_requires_a_review_decision():
    """N.C A type parameter with a NON-reviewed name still withdraws authority.

    `def f[T]()` does not shadow a reviewed name, so the binding rule has
    nothing to refuse -- but the definition is still generic, so the digest
    must move and the exact-site gate must withdraw every grant in the owner
    until an operator reviews the new syntax. This is the review-decision
    direction: X9 requires the change to be VISIBLE, not refused by the
    type-param rule.
    """
    owner = "_admit_record_descriptor"
    plain_tree = ast.parse(_engine_source())
    funcs, _closure = _authority_closure(plain_tree)
    before = _classify_call(owner, next(
        c for c in ast.walk(funcs[owner])
        if isinstance(c, ast.Call)
        and _normalized_call_expression(c) == "os.stat"),
        _audit_context(plain_tree))
    assert before.classification != CLASS_UNKNOWN, before.as_row()
    assert before.reason == "reviewed dotted module call", before.reason

    tree, node, call, saved = _shadowed_owner_call(
        owner, "os.stat", [_synthetic_type_var("T")])
    try:
        context = _audit_context(tree)
        after = _classify_call(owner, call, context)
        assert after.classification == CLASS_UNKNOWN, after.as_row()
        assert "source context changed" in after.reason, after.reason
        assert REVIEWED_OWNER_DIGESTS[owner][:16] in after.reason
        # And the binding rule itself does NOT fire: `T` shadows nothing.
        assert _type_param_shadow(owner, call, context) is None
    finally:
        _restore_type_params(node, saved)


def test_n_d_interpreter_field_order_cannot_move_the_digest():
    """N.D Permuting `_fields` -- same values, same source -- is a no-op.

    The shipped X8 serializer emitted fields in `ast.iter_fields` order, so
    swapping two entries of `FunctionDef._fields` moved the digest of every
    owner while every field VALUE stayed identical (measured before the
    repair: c649a4c9df70b303... -> 4953c178717f43fe...). The canonical schema
    emits in the proof's sorted order, so this control requires equality --
    and the negative control requires the values to have really been
    identical, so "no change" cannot be satisfied by a no-op permutation.
    """
    funcs, _closure = _authority_closure(ast.parse(_engine_source()))
    node = funcs["_admit_record_descriptor"]
    before = _owner_ast_digest(node)
    values_before = {f: _canonical_field_value(node, f) for f in node._fields}
    original = ast.FunctionDef._fields
    permuted = list(original)
    permuted[0], permuted[1] = permuted[1], permuted[0]
    ast.FunctionDef._fields = tuple(permuted)
    try:
        after = _owner_ast_digest(node)
        values_after = {f: _canonical_field_value(node, f)
                        for f in node._fields}
    finally:
        ast.FunctionDef._fields = original
    assert values_before == values_after, (
        "the permutation changed a field VALUE, so this control is not "
        "isolating field ORDER")
    assert after == before, (
        "permuting `_fields` moved the digest despite identical values, so "
        "the serialization still consumes interpreter-provided field order")
    # A nested ClassDef is covered too, so the rule is not FunctionDef-only.
    snippet = "def _f():\n    class Local:\n        pass\n"
    class_before = _digest_of_snippet(snippet)
    class_original = ast.ClassDef._fields
    class_permuted = list(class_original)
    class_permuted[0], class_permuted[1] = class_permuted[1], class_permuted[0]
    ast.ClassDef._fields = tuple(class_permuted)
    try:
        class_after = _digest_of_snippet(snippet)
    finally:
        ast.ClassDef._fields = class_original
    assert class_after == class_before, (
        "permuting ClassDef._fields moved the digest")


def test_n_e_an_unknown_ast_field_fails_closed_with_kind_and_name():
    """N.E A field outside the schema is RED, and the diagnostic names it.

    Measured against the shipped X8 serializer before the repair: an unknown
    meaning-bearing field on `Call` left the digest IDENTICAL for two
    different values while `ast.dump` moved -- silently blind. The canonical
    serializer must instead raise, naming the node type and the field, so a
    future interpreter's addition forces an operator review; the negative
    control proves the injected field was observable at all.
    """
    funcs, _closure = _authority_closure(ast.parse(_engine_source()))
    node = funcs["_admit_record_descriptor"]
    call = next(c for c in ast.walk(node) if isinstance(c, ast.Call))
    original = ast.Call._fields
    try:
        ast.Call._fields = original + ("default_value",)
        call.default_value = "attacker-controlled-1"
        with pytest.raises(_UnreviewedAstFieldError) as caught:
            _owner_ast_digest(node)
        assert "Call.default_value" in str(caught.value), str(caught.value)
        dump_a = ast.dump(node, annotate_fields=True,
                          include_attributes=False)
        call.default_value = "attacker-controlled-2"
        dump_b = ast.dump(node, annotate_fields=True,
                          include_attributes=False)
        assert dump_a != dump_b, (
            "the injected field was not observable even by `ast.dump`, so "
            "the control does not reproduce a real field")
        # A second kind, so the check is not `Call`-specific.
        func_original = ast.FunctionDef._fields
        try:
            ast.FunctionDef._fields = func_original + ("default_value",)
            with pytest.raises(_UnreviewedAstFieldError) as caught_func:
                _owner_ast_digest(node)
            assert "FunctionDef.default_value" in str(caught_func.value), \
                str(caught_func.value)
        finally:
            ast.FunctionDef._fields = func_original
    finally:
        ast.Call._fields = original
        if hasattr(call, "default_value"):
            del call.default_value
    # The shipped shape still digests to the frozen value.
    assert _owner_ast_digest(node) == REVIEWED_OWNER_DIGESTS[
        "_admit_record_descriptor"]


def test_n_f_the_repaired_source_authority_keeps_every_x8_guarantee():
    """N.F X9 preserves X8: exact sites, exact counts, full coverage.

    The repair changes the serializer and the binding walker; it must not
    change WHAT is authorized. The measured totals are asserted to be the
    same as X8's (`X8_TOTALS`), the manifest is exact in both directions, the
    two reachable mutation channels keep their observers, and every READ_ONLY
    grant carries a reason.
    """
    closure, sites = _assert_closed_world(_engine_source())
    counts = {}
    for site in sites:
        counts[site.classification] = counts.get(site.classification, 0) + 1
    assert len(closure) == X8_TOTALS["closure_functions"]
    assert len(sites) == X8_TOTALS["reachable_call_sites"]
    assert counts.get(CLASS_READ_ONLY, 0) == X8_TOTALS["read_only"]
    assert counts.get(CLASS_INTERNAL, 0) == X8_TOTALS["internal"]
    assert counts.get(CLASS_MUTATION, 0) == X8_TOTALS["mutation"]
    assert counts.get(CLASS_UNKNOWN, 0) == X8_TOTALS["unknown"]
    observed = {}
    for site in sites:
        if site.classification != CLASS_UNKNOWN:
            key = (site.owner, site.expression)
            observed[key] = observed.get(key, 0) + 1
    assert observed == EXACT_SITE_MANIFEST, (
        "the manifest is no longer an exact record of the granted surface")
    assert _reachable_mutation_channels(sites) == {"os.open", "open"}
    assert len(_globally_instrumented_channels()) == 33
    for site in sites:
        if site.classification == CLASS_READ_ONLY:
            assert site.reason, f"{site.identity} has no stated reason"


@pytest.mark.skipif(not PEP695_SYNTAX,
                    reason="real PEP 695 syntax requires CPython 3.12+")
@pytest.mark.parametrize("shadow,callee", [
    ("os", "os.stat(path)"),
    ("hashlib", "hashlib.sha256(b'x')"),
    ("RecordSnapshot", "RecordSnapshot(record)"),
    ("_transitions_dir", "_transitions_dir()"),
])
def test_n_g_real_pep695_syntax_is_refused_for_every_reviewed_shape(
        shadow, callee):
    """N.G REAL 3.12 generic syntax, parsed and refused on the 3.12 runner.

    The 3.11 simulation is compared against the real parser in N.H; this is
    the end-to-end control on the interpreter b1 uses: an ACTUAL generic
    function definition is parsed by CPython 3.12, its type parameter is
    measured as a `type-param` binding, and the reviewed call under it is
    refused by the binding rule, naming the shadow. The negative control is
    the same source without the type parameter.
    """
    generic = ast.parse(f"def f[{shadow}]():\n    {callee}\n").body[0]
    assert generic.type_params, "the real parser produced no type parameter"
    call = next(c for c in ast.walk(generic) if isinstance(c, ast.Call))
    context = _snippet_binding_context(generic)
    verdict = _classify_call("f", call, context)
    assert verdict.classification == CLASS_UNKNOWN, verdict.as_row()
    assert "type-param" in verdict.reason, verdict.reason
    assert shadow in verdict.reason, verdict.reason
    # Negative control: the same call without the type parameter is NOT
    # refused by the binding rule.
    plain = ast.parse(f"def f():\n    {callee}\n").body[0]
    plain_call = next(c for c in ast.walk(plain) if isinstance(c, ast.Call))
    plain_context = _snippet_binding_context(plain)
    assert _type_param_shadow("f", plain_call, plain_context) is None


@pytest.mark.skipif(not PEP695_SYNTAX,
                    reason="real PEP 695 syntax requires CPython 3.12+")
def test_n_h_real_pep695_syntax_against_the_real_engine_source():
    """N.H A real generic DEF LINE in the engine itself is refused by name.

    This is the strongest form of the reproduction: the engine source is
    rewritten to carry real PEP 695 syntax on a real reviewed owner and
    re-audited end to end, so the manifest, the occurrence count and the
    frozen digest all apply. The refusal must name `type-param` and the
    shadowed name, and `_assert_closed_world` must go RED.
    """
    source = _engine_source()
    # Negative control: the untouched engine audits green.
    _assert_closed_world(source)
    for owner, expr, shadow in (
            ("_admit_record_descriptor", "os.stat", "os"),
            ("_receipt_digest", "hashlib.sha256", "hashlib"),
            ("_read_record_snapshot_admitted", "RecordSnapshot",
             "RecordSnapshot"),
            ("_derive_claim_coordinate", "_transitions_dir",
             "_transitions_dir"),
    ):
        rewritten = source.replace(f"def {owner}(",
                                   f"def {owner}[{shadow}](", 1)
        assert rewritten != source, owner
        _closure, sites = _audit_source(rewritten)
        hits = [s for s in sites
                if s.owner == owner and s.expression == expr]
        assert hits, f"{expr} vanished from {owner}"
        assert all(s.classification == CLASS_UNKNOWN for s in hits), (
            f"a real generic definition still authorized {expr} in {owner}: "
            + "; ".join(s.as_row() for s in hits))
        assert all("type-param" in s.reason and shadow in s.reason
                   for s in hits), "; ".join(s.reason for s in hits)
        with pytest.raises(AssertionError) as caught:
            _assert_closed_world(rewritten)
        assert "type-param" in str(caught.value)
    # The harmless-parameter case: real syntax, reviewed name untouched, and
    # the DIGEST withdraws the grant (a review decision, not a shadow).
    rewritten = source.replace("def _admit_record_descriptor(",
                               "def _admit_record_descriptor[T](", 1)
    _closure, sites = _audit_source(rewritten)
    hits = [s for s in sites if s.owner == "_admit_record_descriptor"
            and s.expression == "os.stat"]
    assert hits and all(s.classification == CLASS_UNKNOWN for s in hits)
    assert any("source context changed" in s.reason for s in hits), \
        "; ".join(s.reason for s in hits)


@pytest.mark.skipif(not PEP695_SYNTAX,
                    reason="real PEP 695 syntax requires CPython 3.12+")
def test_n_i_real_syntax_matches_the_simulated_shape_and_the_normalisation():
    """N.I The 3.11 simulation is COMPARED against real 3.12 parsing.

    X8's lesson was that a shape assertion made on one interpreter can be
    false on the other, so the simulation may not be ASSUMED equivalent. On
    the runner that can parse real generic syntax, the real tree is measured
    and compared field by field with `_synthetic_type_var`; the real digest
    moves; a plain 3.12 definition carries `type_params == []`; and deleting
    that native attribute normalises to the SAME digest, which is the 3.11
    direction of the version boundary exercised on 3.12 itself.
    """
    real = ast.parse("def f[os]():\n    os.stat(path)\n").body[0]
    assert isinstance(real.type_params, list) and len(real.type_params) == 1
    real_param = real.type_params[0]
    synthetic = _synthetic_type_var("os")
    assert tuple(real_param._fields) == tuple(synthetic._fields), (
        (real_param._fields, synthetic._fields))
    assert _type_parameter_name(real_param) == "os"
    assert getattr(real_param, "bound", None) is None
    for field in synthetic._fields:
        assert _canonical_field_value(real_param, field) == \
            _canonical_field_value(synthetic, field), field
    plain = ast.parse("def f():\n    os.stat(path)\n").body[0]
    assert plain.type_params == []
    assert _owner_ast_digest(real) != _owner_ast_digest(plain)
    # Deleting the NATIVE attribute still normalises to the empty list, so
    # the 3.11 absence and the 3.12 empty list are one canonical value here
    # too, not only in the simulation.
    native = ast.parse("def f():\n    os.stat(path)\n").body[0]
    natural = _owner_ast_digest(native)
    del native.type_params
    assert _owner_ast_digest(native) == natural, (
        "a missing type_params did not normalise to the empty list on 3.12")
