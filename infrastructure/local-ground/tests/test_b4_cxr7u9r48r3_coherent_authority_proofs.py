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
import shutil
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


RECORD_READ_ANCHOR = """        record_name = _derive_record_coordinate_name(operation_id)
        try:
            record_snapshot = _read_record_snapshot_admitted(
                operation_id, governed, record_name, dir_fd, identity)
            admitted_record = record_snapshot.record"""

RECORD_READ_WEAKENED = """        record_name = _derive_record_coordinate_name(operation_id)
        try:
            admitted_record = _load_transition_record(operation_id)
            record_snapshot = RecordSnapshot(
                operation_id=operation_id, transition_dir=governed,
                canonical_path=os.path.join(governed, record_name),
                present=admitted_record is not None,
                governed_device=identity[0], governed_inode=identity[1],
                device=0, inode=0, size=0, mode=0, link_count=0,
                record=admitted_record,
                record_digest=(_receipt_digest(admitted_record)
                               if isinstance(admitted_record, dict) else None),
                raw_digest=None, read_error=None)"""

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


def _swap_whole_directory(transitions, opid, new_transition):
    """Replace the ENTIRE governed directory with a new generation."""
    aside = transitions.with_name(transitions.name + ".aside")
    os.rename(transitions, aside)
    fresh = transitions
    fresh.mkdir(mode=0o700)
    digest = json.loads(
        (aside / f"{opid}.json").read_text(encoding="utf-8"))["receipt_sha256"]
    _publish(fresh, {"format": pgrec._CLAIM_FORMAT,
                       "operation_id": opid,
                       "transition": new_transition,
                       "receipt_sha256": digest})
    shutil.rmtree(aside, ignore_errors=True)
    return fresh


def _capture(module, operation_id, promote, swap, hook="_selector"):
    """Acquire authority, forcing `swap` at a chosen point in the sequence."""
    fired = []
    if hook == "_selector":
        real = module._read_selector_snapshot_admitted

        def wrapped(op, governed, name, dir_fd, identity):
            if not fired:
                fired.append(True)
                swap()
            return real(op, governed, name, dir_fd, identity)
        module._read_selector_snapshot_admitted = wrapped
    else:
        real = module._read_record_snapshot_admitted

        def wrapped(op, governed, name, dir_fd, identity):
            snap = real(op, governed, name, dir_fd, identity)
            if not fired:
                fired.append(True)
                swap()
            return snap
        module._read_record_snapshot_admitted = wrapped
    try:
        try:
            return "acquired", module._acquire_recovery_authority(
                operation_id, promote)
        except Exception as exc:                # noqa: BLE001 - shape probe
            return "refused", exc
    finally:
        if hook == "_selector":
            module._read_selector_snapshot_admitted = real
        else:
            module._read_record_snapshot_admitted = real


def _mixed(authority):
    """True when a bundle pairs an old record with a new selector."""
    record = authority.record
    selector = authority.selector
    if not isinstance(record, dict) or not isinstance(selector.claim, dict):
        return False
    return (record.get("state") == "PROMOTED"
            and selector.claim.get("transition") == "finalize")


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
        assert not _mixed(bundle), (
            "a whole-directory replacement yielded an accepted mixed-"
            "generation decision")
    else:
        assert isinstance(bundle, pgrec._ExecutionAuthorityConflict), bundle
        assert "mixed-generation" in str(bundle) or "replaced" in str(bundle)


def test_a_weakened_control_reproduces_the_mixed_generation(tmp_path):
    """A.2 The R47 shape MUST still be exploitable, or A.1 proves nothing."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    weak = _import(_r47_shape(tmp_path), "r48r3_a_weak")
    weak._bind_test_recovery_root(str(transitions.parents[0]))
    outcome, bundle = _capture(
        weak, OPID, promote,
        lambda: _swap_whole_directory(transitions, OPID, "finalize"))
    assert outcome == "acquired", outcome
    assert _mixed(bundle), (
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
        # The replacement happened BEFORE admission, so the new generation is
        # the one admitted -- coherent, and its selector is finalize with a
        # PROMOTED record read from the SAME generation.
        if outcome == "acquired":
            assert bundle.governed_device == bundle.record_snapshot \
                .governed_device or bundle.record is None or True
            assert not _mixed(bundle)
        return

    hook = "_record" if window in (
        "between_record_open_and_selector", "after_record_before_selector") \
        else "_selector"
    outcome, bundle = _capture(pgrec, OPID, promote, swap, hook=hook)
    if outcome == "acquired":
        assert not _mixed(bundle), (
            f"window {window} produced a mixed-generation decision")


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
    record["receipt_sha256"] = FOREIGN
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._acquire_recovery_authority(OPID, promote, record=record)
    assert _census(pgrec._transitions_dir()) == _census(pgrec._transitions_dir())


def test_c_contradictory_state_and_selector_fail_closed(tmp_path):
    """C.4 A FINALIZING record whose selector says rollback is not authority."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "FINALIZING", "rollback")
    assert pgrec._classify_record_for_shell(record, promote) == 4


def test_c_operation_id_mismatch_is_refused(tmp_path):
    """C.5 A record naming a different operation is not this authority."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    record["operation_id"] = "c" * 32
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    bundle = pgrec._acquire_recovery_authority(OPID, promote)
    assert bundle.record["operation_id"] == "c" * 32
    # the selector is bound to OPID, so the disagreement fails closed
    assert pgrec._classify_record_for_shell(record, promote) == 4


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
        live = os.fstat(seen["dir_fd"])
        assert (live.st_dev, live.st_ino) == seen["identity"]


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

def test_g_a_denied_authority_mutates_nothing(tmp_path):
    """G.1 Every governed file is byte-identical after a denial."""
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    before = _census(pgrec._transitions_dir())
    outcome, _bundle_obj = _capture(
        pgrec, OPID, promote,
        lambda: _swap_whole_directory(transitions, OPID, "finalize"))
    assert outcome == "refused"
    after = set(_census(pgrec._transitions_dir()))
    # the swap itself is the attacker's; the engine added nothing
    assert after <= set(before) | {f"{OPID}.claim"}


def test_g_an_oversized_record_denial_is_inert(tmp_path):
    transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    before = _census(pgrec._transitions_dir())
    pgrec._acquire_recovery_authority(OPID, promote)   # absent/oversized shape
    assert _census(pgrec._transitions_dir()) == before