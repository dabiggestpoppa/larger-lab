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
import dataclasses
import json
import os
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

    On top of the syscall surface, the engine's own durable-write helpers
    are wrapped, because a write performed entirely through `os.fdopen`
    would otherwise be visible only as a helper call.
    """

    MUTATORS = frozenset({
        "unlink", "remove", "rmdir", "removedirs", "truncate", "chmod",
        "chown", "link", "symlink", "rename", "replace", "mkdir",
        "makedirs", "rmtree", "write", "fsync",
    })

    WRITE_HELPERS = (
        "_write_transition_record", "_record_transition", "_commit_receipt",
        "_exclusive_copy", "_publish_no_replace", "_fsync_dir",
    )

    def __init__(self, engine):
        self.engine = engine
        self.real_os = engine.os
        self.real_helpers = {}
        self.mutations = []

    def __enter__(self):
        tripwire = self

        class _OsProxy:
            """Forwards everything; intercepts only the mutating names."""

            def __getattr__(self, name):
                if name in tripwire.MUTATORS:
                    def intercepted(*args, **kwargs):
                        tripwire.mutations.append(
                            ("os." + name, [str(a) for a in args[:2]]))
                        return getattr(tripwire.real_os, name)(*args, **kwargs)
                    return intercepted
                return getattr(tripwire.real_os, name)

        self.engine.os = _OsProxy()
        for name in self.WRITE_HELPERS:
            real = getattr(self.engine, name, None)
            if real is None:
                continue
            self.real_helpers[name] = real

            def make(name=name, real=real):
                def intercepted(*args, **kwargs):
                    tripwire.mutations.append(
                        (name, [str(a) for a in args[:2]]))
                    return real(*args, **kwargs)
                return intercepted

            setattr(self.engine, name, make())
        return self

    def __exit__(self, *exc_info):
        self.engine.os = self.real_os
        for name, real in self.real_helpers.items():
            setattr(self.engine, name, real)
        return False

    def kinds(self):
        return [kind for kind, _args in self.mutations]


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


# The size bound the denial proof depends on. Both the BEFORE-read and the
# DURING-read comparison are anchored, each asserted to occur exactly once,
# so a drifted engine makes the control fail loudly instead of quietly
# rebuilding the shipped engine and proving nothing.
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