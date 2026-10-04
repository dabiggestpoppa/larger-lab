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
import builtins
import dataclasses
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


def _classify_call(owner, call, engine_definitions):
    """Assign exactly one classification to a single reachable call site.

    Matching order matters and is deliberate:
      1. no renderable callee            -> UNKNOWN (dynamic call)
      2. maps to a tripwire observer      -> MUTATION
      3. defined in this module           -> INTERNAL (the closure walk
                                            audits its own body separately)
      4. explicitly reviewed constructor  -> READ_ONLY
      5. reviewed READ_ONLY registry      -> READ_ONLY
      6. anything else                    -> UNKNOWN, which fails the proofX7: a METHOD call is no longer admitted on its attribute name alone. The
    receiver is normalized and the (receiver, method) PAIR must be reviewed, so
    `record.get` is admitted while `Path(src).replace(dst)` and
    `external.update(...)` are refused.
    """
    callee = _qualified_callee(call)
    expr = _normalized_call_expression(call)
    col = getattr(call, "col_offset", 0)

    def _ret(classification, reason="", observer=None):
        return _ClassifiedCall(owner, call.lineno, callee, classification,
                               observer, col=col, expression=expr,
                               reason=reason)

    if callee is None:
        return _ret(CLASS_UNKNOWN, "no renderable callee (dynamic call)")
    observer = _observer_for(callee)
    if observer is not None:
        return _ret(CLASS_MUTATION, "maps to a tripwire observer", observer)
    # X7 rule F: a reviewed constructor must be decidable on its own reviewed
    # merits. Previously engine_definitions was consulted first, so every name
    # in PURE_CONSTRUCTORS was unreachable and the policy was dead.
    if callee in PURE_CONSTRUCTORS:
        return _ret(CLASS_READ_ONLY, "reviewed pure constructor")
    head, _, attr = callee.rpartition(".")
    # X7: the receiver/method vs bare-name discriminator is the AST SHAPE, not
    # the rendered spelling. `hashlib.sha256(x).hexdigest()` renders as the
    # dotless "hexdigest" yet IS a method call on an expression receiver, so
    # routing on the dot would misclassify it as a bare local name.
    is_method = isinstance(call.func, ast.Attribute)
    if head in QUALIFIED_MODULES:
        # Known module: only the full dotted spelling may be admitted, so a
        # new module call cannot be absorbed by a bare-name registry entry.
        if callee in READ_ONLY_REGISTRY:
            return _ret(CLASS_READ_ONLY, "reviewed dotted module call")
        return _ret(CLASS_UNKNOWN,
                    f"module call {callee!r} is not in READ_ONLY_REGISTRY")
    if not is_method:
        # X7 rule E: the dispatch-table seam stays explicit and separately
        # proven by I.G.
        if callee in REVIEWED_DISPATCH_LOCALS:
            return _ret(CLASS_INTERNAL,
                        "engine dispatch table (proven by I.G)",
                        "engine dispatch table (proven by I.G)")
        # X7 rule D: only genuine MODULE-LEVEL engine functions and classes may
        # take INTERNAL_CALL from a bare name. Nested defs and class methods are
        # deliberately absent from engine_definitions, so `commit()` cannot be
        # mistaken for an engine function.
        if callee in engine_definitions:
            return _ret(CLASS_INTERNAL, "module-level engine definition")
        if callee in READ_ONLY_REGISTRY:
            return _ret(CLASS_READ_ONLY, "reviewed bare builtin")
        return _ret(CLASS_UNKNOWN,
                    f"bare name {callee!r} is neither a module-level engine "
                    f"definition nor a reviewed builtin")
    # X7 rules B and C: method call on a non-module receiver.
    receiver = call.func.value
    if _is_literal_receiver(receiver):
        if expr in LITERAL_RECEIVER_METHODS:
            return _ret(CLASS_READ_ONLY, "literal receiver cannot be rebound")
        return _ret(CLASS_UNKNOWN,
                    f"literal-receiver call {expr!r} is not reviewed")
    if isinstance(receiver, ast.Call):
        if expr in REVIEWED_EXPRESSION_RECEIVERS:
            return _ret(CLASS_READ_ONLY, "reviewed expression receiver")
        return _ret(CLASS_UNKNOWN,
                    f"expression receiver {expr!r} is not in "
                    f"REVIEWED_EXPRESSION_RECEIVERS")
    if expr in REVIEWED_RECEIVER_METHODS:
        return _ret(CLASS_READ_ONLY, "reviewed (receiver, method) pair")
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
    funcs, closure = _authority_closure(tree)
    engine_definitions = _engine_definitions(tree)
    sites = []
    for owner in sorted(closure):
        calls = [c for c in ast.walk(funcs[owner]) if isinstance(c, ast.Call)]
        for call in sorted(calls,
                           key=lambda c: (c.lineno, _qualified_callee(c) or "")):
            sites.append(_classify_call(owner, call, engine_definitions))
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
    assert _classify_call(
        "_probe", ast.parse("handler(record)").body[0].value,
        set()) .classification == CLASS_INTERNAL
    assert _classify_call(
        "_probe", ast.parse("rogue(value)").body[0].value,
        set()).classification == CLASS_UNKNOWN


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