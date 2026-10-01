#!/usr/bin/env python3
"""B4-CXR7U9R47R1 - ONE COMPLETE recovery-authority snapshot per decision.

R46's evidence recorded "one decision consumes one snapshot" for the shell
classifier. That was true of `_valid_transition_claim` in isolation and FALSE
of the complete classifier, which called `_claim_state()` -- a helper with no
snapshot parameter at all, so it always re-read the coordinate itself -- and
then read the coordinate a SECOND time to select the branch. On a PROMOTED
record with an exact promote receipt that was 2 selector reads per decision,
and a replacement landing between them was legal.

These proofs drive the COMPLETE classifier and count reads at the boundary:

1. a PROMOTED rollback decision and a PROMOTED finalize decision each consume
   exactly ONE transition-record read and exactly ONE selector read;
2. every state on the ladder performs no hidden re-read;
3. the deterministic mixed-generation replay -- read 1 = rollback, attempted
   read 2 = finalize -- is never performed at all by the repaired engine;
4. an executable weakened control that restores the two-read classifier DOES
   consume the swapped generation, so proof 3 is non-vacuous;
5. a record replaced between record admission and selector classification
   stays pinned to the admitted record: generations are never combined.

Every proof is deterministic. The generation swap is an explicit post-admission
replay of a parsed snapshot, never a thread and never a timing race.
"""
import dataclasses
import importlib.util
import json
import os
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "pg-recovery.py"

OPID = "a" * 32
FOREIGN = "b" * 64
STATES = ["CREATED", "STAGED", "PROMOTED", "FINALIZING", "ROLLING_BACK",
          "ROLLED_BACK", "FAILED", "COMMIT_INTENT_RECORDED",
          "COMMIT_POINT_REACHED", "FINALIZED"]


def _load_engine(path=None):
    spec = importlib.util.spec_from_file_location(
        "pg_recovery_r47r1", str(path or CLI))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pgrec = _load_engine()


@pytest.fixture(autouse=True)
def _approved_root(tmp_path, monkeypatch):
    """The promote receipt is DATA and must sit inside an approved root
    (`_approved_roots`: program identity, or the operator-declared
    OCE_BACKUP_ROOTS list). Point that list at this test's disposable tree
    -- the same channel restore.sh uses -- so the receipts these proofs
    read are readable, and nothing else about authority changes."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))


def _bytes(doc):
    return json.dumps(doc).encode("utf-8")


def _census(root):
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = (
                path.stat().st_size, pgrec.sha256_file(str(path)))
    return out


def _promote_receipt():
    return {
        "format": pgrec.RECEIPT_FORMAT,
        "operation_phase": "promote",
        "exit_status": 0,
        "promoted": True,
        "operation_id": OPID,
        "database": pgrec.DB,
        "user": pgrec.USER,
        "container": pgrec.CONTAINER,
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "run_id": "0123456789abcdef",
        "stamp": "0123456789ab",
        "quarantine_database": pgrec.QUARANTINE_PREFIX + "0123456789ab",
        "staging_database": pgrec.STAGING_PREFIX + "0123456789ab",
        "source_archive_sha256": "c" * 64,
        "inventory_sha256": "d" * 64,
    }


def _record(promote, state="PROMOTED", digest=None, transition=None):
    record = {
        "format": pgrec.TRANSITION_FORMAT,
        "state": state,
        "operation_id": OPID,
        "selected_transition": transition,
        "receipt_sha256": (digest if digest is not None
                           else pgrec._receipt_digest(promote)),
    }
    for key in ("database", "user", "container", "source_commit", "source_tree",
                "run_id", "stamp", "quarantine_database", "staging_database",
                "source_archive_sha256", "inventory_sha256"):
        record[key] = promote[key]
    if state == "FINALIZING":
        record["selected_transition"] = "finalize"
    if state in ("ROLLING_BACK", "ROLLED_BACK"):
        record["selected_transition"] = "rollback"
    if state == "COMMIT_INTENT_RECORDED":
        record["commit_intent"] = {
            "marker": "forward_commit", "operation_id": OPID,
            "receipt_sha256": record["receipt_sha256"],
            "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER,
            "quarantine_database": record["quarantine_database"],
            "at": "2026-09-24T00:00:00Z",
        }
    if state in ("COMMIT_POINT_REACHED", "FINALIZED"):
        record["commit_point"] = {"marker": "quarantine_dropped",
                                  "at": "2026-09-24T00:00:01Z"}
    return record


def _publish(transitions, doc):
    path = transitions / f"{OPID}.claim"
    path.write_bytes(_bytes(doc))
    os.chmod(path, 0o600)
    return path


def _claim_doc(promote, transition):
    return {"format": pgrec._CLAIM_FORMAT, "operation_id": OPID,
            "transition": transition,
            "receipt_sha256": pgrec._receipt_digest(promote),
            "claimed_at": "2026-09-24T00:00:00Z"}


def _build(tmp_path, state="PROMOTED", transition=None, digest=None):
    """A genuine, complete operation tree; binds the engine to it in process.

    B4-CXR7U9R47R2: the engine derives its governed transition root from its own
    identity. There is no parameter left to pass a directory through, so the
    disposable root reaches the engine only through the explicit test seam.
    """
    root = tmp_path / "governed-recovery"
    root.mkdir(parents=True, exist_ok=True)
    transitions = root / "transitions"
    transitions.mkdir(exist_ok=True)
    promote = _promote_receipt()
    record = _record(promote, state, digest, transition)
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    receipt = root / "promote-receipt.json"
    receipt.write_bytes(_bytes(promote))
    os.chmod(receipt, 0o600)
    if transition:
        _publish(transitions, _claim_doc(promote, transition))
    pgrec._bind_test_recovery_root(str(root))
    return transitions, record, promote, receipt


def _counts(engine):
    """Count reads at the two boundary functions a decision must not repeat."""
    tally = {"record": 0, "selector": 0}
    real_record = engine._load_transition_record
    # The counted boundary is the ADMITTED selector read itself, not its
    # convenience wrapper: `_read_selector_snapshot` only derives the
    # coordinate and admits the directory before delegating here, so wrapping
    # the wrapper would miss a decision that re-acquires a snapshot through
    # `_acquire_recovery_authority` directly.
    real_selector = engine._read_selector_snapshot_admitted

    def counted_record(operation_id):
        tally["record"] += 1
        return real_record(operation_id)

    def counted_selector(operation_id, governed, name, dir_fd, identity):
        tally["selector"] += 1
        return real_selector(operation_id, governed, name, dir_fd, identity)

    engine._load_transition_record = counted_record
    engine._read_selector_snapshot_admitted = counted_selector
    return tally


class _GenerationReplay:
    """Deterministic post-admission generation swap -- no threads, no timing.

    The first admitted snapshot replays generation 1, every later read replays
    generation 2. The admitted IDENTITY is deliberately preserved (only the
    parsed content changes), so this models a generation swap that already got
    past admission, which is exactly the window R46 left open.
    """

    def __init__(self, engine, generations):
        self.generations = generations
        self.reads = 0
        self.real = engine._read_selector_snapshot_admitted

    def __call__(self, operation_id, governed, name, dir_fd, identity):
        snap = self.real(operation_id, governed, name, dir_fd, identity)
        if not snap.present:
            return snap
        index = min(self.reads, len(self.generations) - 1)
        self.reads += 1
        return dataclasses.replace(snap, claim=self.generations[index])


def _weakened_engine(tmp_path):
    """Restore the R46 two-read PROMOTED leg in a copy of the real engine."""
    source = CLI.read_text(encoding="utf-8")
    assert TWO_READ_OLD in source, "the shipped classifier changed shape"
    changed = source.replace(TWO_READ_OLD, TWO_READ_TWO_READ)
    assert changed != source
    path = tmp_path / "weakened-pg-recovery.py"
    path.write_text(changed, encoding="utf-8")
    return path


TWO_READ_OLD = '''        if promote is not None and authority is not None:
            if _valid_transition_claim(operation_id, "rollback", promote,
                                       transition_dir=transition_dir,
                                       authority=authority):
                return 6
            if _valid_transition_claim(operation_id, "finalize", promote,
                                       transition_dir=transition_dir,
                                       authority=authority):
                return 5
'''

TWO_READ_TWO_READ = '''        if promote is not None and authority is not None:
            # B4-CXR7U9R47R1 NEGATIVE CONTROL: the R46 shape, verbatim in
            # effect. Classify from the admitted snapshot, then RE-ACQUIRE a
            # second one to select the branch. The second read is the window in
            # which the swapped generation lands.
            _claim_state(operation_id, authority=authority)
            second = _acquire_recovery_authority(operation_id, promote,
                                                 record=record)
            if _valid_transition_claim(operation_id, "rollback", promote,
                                       authority=second):
                return 6
            if _valid_transition_claim(operation_id, "finalize", promote,
                                       authority=second):
                return 5
'''


# --------------------------------------------------------------------- #
# proofs 1-2: the COMPLETE production route, read counts at the boundary
# --------------------------------------------------------------------- #

def test_promoted_rollback_decision_is_one_record_and_one_selector_read(
        tmp_path):
    """Proof 1: the COMPLETE rollback-legality decision -- receipt load, record
    binding, selector admission, binding, branch and freshness -- reads the
    durable record once and the canonical selector once."""
    _transitions, _record, _promote, receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    tally = _counts(pgrec)
    verdict = pgrec._classify_rollback_for_shell(str(receipt))
    assert verdict == 6, verdict
    assert tally["record"] == 1, ("the record must be read exactly once", tally)
    assert tally["selector"] == 1, (
        "the selector must be read exactly once", tally)


def test_promoted_finalize_decision_is_one_record_and_one_selector_read(
        tmp_path):
    """Proof 2: the same complete decision on the OTHER branch."""
    _transitions, _record, _promote, receipt = _build(
        tmp_path, "PROMOTED", "finalize")
    tally = _counts(pgrec)
    verdict = pgrec._classify_rollback_for_shell(str(receipt))
    assert verdict == 5, verdict
    assert tally["record"] == 1, tally
    assert tally["selector"] == 1, tally


@pytest.mark.parametrize("state", STATES)
def test_every_ladder_state_performs_no_hidden_reread(tmp_path, state):
    """Proof 3: no state on the ladder spends a second selector read, and none
    of them re-reads a record the caller already admitted."""
    transition = {"PROMOTED": "rollback", "FINALIZING": "finalize",
                  "ROLLING_BACK": "rollback",
                  "ROLLED_BACK": "rollback"}.get(state)
    _transitions, record, promote, _receipt = _build(
        tmp_path, state, transition)
    tally = _counts(pgrec)
    pgrec._classify_record_for_shell(record, promote)
    assert tally["selector"] == 1, (state, tally)
    assert tally["record"] == 0, (state, tally)


# --------------------------------------------------------------------- #
# proofs 4-5: the deterministic mixed-generation replay, and its control
# --------------------------------------------------------------------- #

def test_mixed_generation_second_read_is_never_performed(tmp_path):
    """Proof 4: present the classifier with generation 1 = exact rollback
    selector and generation 2 = exact finalize selector. The shipped engine
    must not perform the second read AT ALL, so the swapped generation is never
    observed and the verdict comes from generation 1."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    generations = [_claim_doc(promote, "rollback"),
                   _claim_doc(promote, "finalize")]
    replay = _GenerationReplay(pgrec, generations)
    real = pgrec._read_selector_snapshot_admitted
    pgrec._read_selector_snapshot_admitted = replay
    try:
        verdict = pgrec._classify_record_for_shell(record, promote)
    finally:
        pgrec._read_selector_snapshot_admitted = real
    assert verdict == 6, verdict
    assert replay.reads == 1, (
        "the complete decision must perform exactly one selector read; the "
        "second generation must never be read")
    assert generations[1]["transition"] == "finalize"


def test_weakened_two_read_classifier_consumes_the_mixed_generation(tmp_path):
    """Proof 5: the executable negative control. Restoring the R46 two-read
    PROMOTED leg makes the swapped generation land and the classifier ACCEPT
    the finalize branch. This is what proof 4 is protecting against, so proof
    4 is not vacuous."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    generations = [_claim_doc(promote, "rollback"),
                   _claim_doc(promote, "finalize")]
    weak = _load_engine(_weakened_engine(tmp_path))
    weak._bind_test_recovery_root(str(tmp_path / "governed-recovery"))
    replay = _GenerationReplay(weak, generations)
    weak._read_selector_snapshot_admitted = replay
    verdict = weak._classify_record_for_shell(record, promote)
    assert replay.reads == 2, ("the weakened control must perform the second "
                               "read the shipped engine refuses to perform")
    assert verdict == 5, ("the weakened control must ACCEPT the swapped "
                          "finalize generation")
    # the shipped engine, on the identical durable world, does not
    pgrec._bind_test_recovery_root(str(tmp_path / "governed-recovery"))
    assert pgrec._classify_record_for_shell(record, promote) == 6


# --------------------------------------------------------------------- #
# proof 6: the record and the selector can never come from two generations
# --------------------------------------------------------------------- #

def test_record_replaced_after_admission_stays_pinned_to_that_record(
        tmp_path):
    """Proof 6: replace the durable record AFTER it has been admitted but
    BEFORE the selector is classified. The decision must stay pinned to the
    admitted record -- never silently combine the admitted record with the
    selector read against the replacement."""
    # NOTE: the unpacked record is deliberately NOT named `_record`:
    # the module-level `_record()` helper builds replacement records, and
    # shadowing it with the unpacked dict would make the closure below
    # call a dict.
    transitions, admitted_record, promote, receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    assert admitted_record["state"] == "PROMOTED"
    path = transitions / f"{OPID}.json"
    real_load = pgrec._load_transition_record

    def load_then_swap(operation_id):
        admitted = real_load(operation_id)
        # the attacker replaces the durable record the instant it was admitted
        path.write_bytes(_bytes(_record(promote, "ROLLED_BACK",
                                        digest=FOREIGN)))
        return admitted

    pgrec._load_transition_record = load_then_swap
    try:
        verdict = pgrec._classify_rollback_for_shell(str(receipt))
    finally:
        pgrec._load_transition_record = real_load
    # the replacement really landed on disk during the decision ...
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == \
        "ROLLED_BACK"
    # ... and the decision still came from the ADMITTED record
    assert verdict == 6, verdict
    # a LATER decision does see the replacement: the pin is per-decision, not
    # a stale cache, and the replacement is different authority (4, not 6)
    assert pgrec._classify_rollback_for_shell(str(receipt)) == 4


# --------------------------------------------------------------------- #
# the pure classifier really is pure
# --------------------------------------------------------------------- #

def test_the_pure_classifier_performs_no_filesystem_access(monkeypatch,
                                                           tmp_path):
    """Once the authority snapshot exists, the classifier must decide from it
    alone. Prove that by making every reader raise, then classifying."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    authority = pgrec._acquire_recovery_authority(OPID, promote, record=record)
    expected = pgrec._receipt_digest(promote)

    def boom(*_a, **_k):
        raise AssertionError("the pure classifier must not touch the filesystem")

    for name in ("_read_selector_snapshot", "_read_selector_snapshot_admitted",
                 "_load_transition_record", "_load_claim"):
        monkeypatch.setattr(pgrec, name, boom)
    assert pgrec._classify_claim_content(
        OPID, authority.selector, expected_receipt_sha256=expected) \
        == "bound_complete"
    assert pgrec._valid_transition_claim(OPID, "rollback", promote,
                                         authority=authority) is True
    assert pgrec._valid_transition_claim(OPID, "finalize", promote,
                                         authority=authority) is False
    assert pgrec._selector_agrees_with_finalizing(OPID, promote,
                                                   authority=authority) is False
    assert pgrec._claim_state(OPID, authority=authority,
                              expected_receipt_sha256=expected) \
        == "bound_complete"


def test_authority_snapshot_carries_the_admitted_governed_directory_identity(
        tmp_path):
    """The snapshot is pinned to one directory INODE, admitted with
    O_NOFOLLOW -- not to a pathname a redirection could re-point."""
    transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    authority = pgrec._acquire_recovery_authority(OPID, promote, record=record)
    info = os.stat(transitions)
    assert authority.governed_device == info.st_dev
    assert authority.governed_inode == info.st_ino
    assert authority.selector.governed_inode == info.st_ino
    assert authority.record is record
    assert authority.record_digest == pgrec._receipt_digest(record)
    assert authority.expected_receipt_sha256 == pgrec._receipt_digest(promote)
    # and it is immutable: a decision may not rewrite its own evidence
    with pytest.raises(Exception):
        authority.expected_receipt_sha256 = "b" * 64
