#!/usr/bin/env python3
"""B4-CXR7U9R46X1 - authoritative Linux proofs for the selector durable-name
law that replaces the withdrawn total-link-count law.

Authoritative Linux CI (b1 run 36759645882, implementation head 0a9157ffa)
refused six R44 crash-recovery proofs. Every one of them failed for ONE
reason: POSIX publication is ``os.link(tmp, "<opid>.claim")`` followed by
``os.unlink(tmp)``, so a publisher that dies in that window - which is
exactly the boundary the R44 law simulates - leaves the durably published
claim carrying TWO names. R46R1 read that residue as a foreign hard link and
refused it, which converted a recoverable crash into a permanent authority
lockout and contradicted R44's own law that such a claim stays resumable.

This suite proves the corrected law is both NECESSARY and NON-VACUOUS:

* x1/x2 - a claim published through the engine's OWN primitives with the
  post-publication unlink omitted (the exact R44 death window) is ADMITTED by
  one FD-bound snapshot and still GOVERNS the decision: the rollback branch
  it selected is honoured (exit 6), and a residue whose payload binds
  nothing fails closed (exit 4);
* x3 - a foreign durable name INSIDE the governed directory is refused;
* x4 - a foreign durable name OUTSIDE the governed directory is refused, and
  is refused by the descriptor-relative count cross-check, so an
  out-of-directory name can never hide behind an in-directory census;
* x5 - the withdrawn ``st_nlink == 1`` law, restored verbatim, REFUSES that
  same legitimate residue: the repair is necessary, not cosmetic;
* x6 - every denial leaves the governed tree byte-identical and creates,
  deletes and rewrites nothing.

Every proof is deterministic: the residue is produced by the shipped
primitives with the unlink withheld, never by a sleep or a race. The
residue-shaped proofs are POSIX-only because Windows publication consumes the
temporary name atomically (os.rename), so the state under test cannot exist
there; every other proof runs on both platforms.
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

OPID = "a" * 32
FOREIGN = "b" * 64
EXACT = "c" * 64

posix_only = pytest.mark.skipif(
    os.name == "nt",
    reason="the POSIX publication window (link then unlink) has no Windows "
           "counterpart: os.rename consumes the temporary name atomically")


def _load_engine(path):
    spec = importlib.util.spec_from_file_location(
        "pg_recovery_r46x1_under_test", str(path))
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
    transitions = tmp_path / "governed-recovery" / "transitions"
    transitions.mkdir(parents=True, exist_ok=True)
    record = {
        "format": pgrec.TRANSITION_FORMAT,
        "state": state,
        "operation_id": OPID,
        "selected_transition": "rollback" if state == "PROMOTED" else None,
        "receipt_sha256": record_digest,
    }
    (transitions / f"{OPID}.json").write_bytes(_bytes(record))
    os.chmod(transitions / f"{OPID}.json", 0o600)
    # B4-CXR7U9R47R2: the engine now derives its governed transition root from
    # its own identity -- no parameter is left to pass a directory through --
    # so every tree built here binds that root in process through the explicit
    # test seam. A proof that builds a second tree rebinds to it, which is
    # exactly why two trees can never share an authority root.
    pgrec._bind_test_recovery_root(str(tmp_path / "governed-recovery"))
    return transitions, record


def _publish(transitions, payload):
    claim = transitions / f"{OPID}.claim"
    claim.write_bytes(payload)
    os.chmod(claim, 0o600)
    return claim


def _publisher_crash_residue(transitions, payload):
    """The engine's OWN POSIX publication, with the post-publication unlink
    withheld: exactly the R44 'after_canonical_claim_publication' death.

    The temporary is created by ``_open_claim_temporary`` (so its name, mode
    and lock discipline are the shipped ones), the payload is written and
    fsynced, and ``_publish_no_replace`` links it into the canonical
    coordinate. The publisher then dies instead of retiring the temporary.
    """
    fd, tmp, lockfd = pgrec._open_claim_temporary(OPID, str(transitions))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, 0o600)
        claim = transitions / f"{OPID}.claim"
        pgrec._publish_no_replace(tmp, str(claim))
    finally:
        os.close(lockfd)
    residue = Path(tmp)
    # the residue really is a second durable name of the SAME inode
    claim_info = os.stat(claim)
    residue_info = os.stat(residue)
    assert claim_info.st_nlink == 2
    assert (claim_info.st_dev, claim_info.st_ino) == \
        (residue_info.st_dev, residue_info.st_ino)
    assert residue.name.startswith(pgrec._claim_temp_prefix(OPID))
    return claim, residue


# --------------------------------------------------------------------- #
# x1 / x2: the legitimate crash residue is admitted AND governs
# --------------------------------------------------------------------- #

@posix_only
def test_x1_publisher_crash_residue_is_admitted_by_one_snapshot(tmp_path):
    """x1: a claim the engine itself published and died holding is readable."""
    transitions, _record = _governed(tmp_path)
    promote = {"operation_phase": "promote", "exit_status": 0,
               "operation_id": OPID}
    claim, residue = _publisher_crash_residue(
        transitions, _bytes({**CLAIM,
                             "receipt_sha256":
                             pgrec._receipt_digest(promote)}))
    snapshot = pgrec._read_selector_snapshot(OPID)
    assert snapshot.present is True
    assert snapshot.link_count == 2
    assert (snapshot.device, snapshot.inode) == \
        (os.stat(claim).st_dev, os.stat(claim).st_ino)
    assert snapshot.read_error is None
    assert snapshot.claim["transition"] == "rollback"
    assert snapshot.canonical_path == str(claim)
    assert pgrec._load_claim(OPID) == snapshot.claim
    # the residue is untouched by the read: the engine never repairs, deletes
    # or rewrites a selector it admitted
    assert os.stat(residue).st_nlink == 2


@posix_only
def test_x2_crash_residue_still_governs_the_branch_selection(tmp_path):
    """x2: admissibility is not a weakened decision: the selected branch is
    honoured (6), and a residue bound to nothing fails closed (4)."""
    transitions, record = _governed(tmp_path)
    promote = {"operation_phase": "promote", "exit_status": 0,
               "operation_id": OPID}
    _claim, _residue = _publisher_crash_residue(
        transitions, _bytes({**CLAIM,
                             "receipt_sha256":
                             pgrec._receipt_digest(promote)}))
    # B4-CXR7U9R47R1: the branch decision consumes ONE complete authority
    # snapshot -- there is no directory parameter left to pass.
    authority = pgrec._acquire_recovery_authority(OPID, promote)
    assert pgrec._valid_transition_claim(
        OPID, "rollback", promote, authority=authority) is True
    assert pgrec._valid_transition_claim(
        OPID, "finalize", promote, authority=authority) is False
    assert pgrec._classify_record_for_shell(record, promote) == 6

    # the same residue whose payload binds a FOREIGN well-formed digest is
    # different authority and is refused, not honoured
    transitions_b, record_b = _governed(tmp_path / "second")
    _publisher_crash_residue(
        transitions_b, _bytes({**CLAIM, "receipt_sha256": FOREIGN}))
    assert pgrec._classify_record_for_shell(
        record_b, promote) == 4


# --------------------------------------------------------------------- #
# x3 / x4: every OTHER durable name is refused
# --------------------------------------------------------------------- #

def test_x3_foreign_name_inside_the_governed_directory_is_refused(tmp_path):
    """x3: a second in-directory durable name is not a publisher residue."""
    transitions, _record = _governed(tmp_path)
    claim = _publish(transitions, _bytes(CLAIM))
    second = transitions / f"{OPID}.second"
    try:
        os.link(claim, second)
    except (OSError, NotImplementedError):
        pytest.skip("hard links unavailable on this platform")
    before = _census(transitions)
    try:
        with pytest.raises(pgrec._ExecutionAuthorityConflict):
            pgrec._read_selector_snapshot(OPID)
        assert _census(transitions) == before
    finally:
        second.unlink()
    assert pgrec._read_selector_snapshot(OPID).present


def test_x4_foreign_link_outside_the_governed_directory_is_refused(tmp_path):
    """x4: a durable name the governed directory cannot even see is refused by
    the count cross-check, so it can never hide behind the census."""
    transitions, _record = _governed(tmp_path)
    claim = _publish(transitions, _bytes(CLAIM))
    outside = tmp_path / "outside-the-governed-directory"
    try:
        os.link(claim, outside)
    except (OSError, NotImplementedError):
        pytest.skip("hard links unavailable on this platform")
    census = {p.name for p in transitions.iterdir()}
    assert outside.name not in census, (
        "the out-of-directory link must be invisible to the census, or this "
        "proof would be proving nothing")
    before = _census(transitions)
    try:
        with pytest.raises(pgrec._ExecutionAuthorityConflict) as refusal:
            pgrec._read_selector_snapshot(OPID)
        if os.name != "nt":
            # POSIX refuses it for the exact, provable reason: the link count
            # and the in-directory census disagree.
            assert "unaccounted durable name" in str(refusal.value)
        assert _census(transitions) == before
        assert outside.is_file()
    finally:
        outside.unlink()
    assert pgrec._read_selector_snapshot(OPID).present


# --------------------------------------------------------------------- #
# x5: the withdrawn law, restored verbatim, breaks the R44 crash law
# --------------------------------------------------------------------- #

@posix_only
def test_x5_withdrawn_total_link_count_law_refuses_the_legal_residue(
        tmp_path, monkeypatch):
    """x5: the withdrawn R46R1 form is the defect, proven by execution.

    The R46R1 law is restored verbatim on the admitted descriptor and the
    engine's OWN crash residue is refused by it. That refusal is what made
    six R44 crash-recovery proofs fail in authoritative Linux CI, so the
    corrected law is necessary rather than cosmetic.
    """
    transitions, _record = _governed(tmp_path)
    _claim, _residue = _publisher_crash_residue(transitions, _bytes(CLAIM))

    def withdrawn_law(info, dir_fd, canonical_name, operation_id):
        if info.st_nlink != 1:
            raise pgrec._selector_conflict(
                operation_id,
                f"the canonical claim has {info.st_nlink} durable links; the "
                "published selector is one single durable name")

    monkeypatch.setattr(pgrec, "_assert_selector_authority_names",
                        withdrawn_law)
    with pytest.raises(pgrec._ExecutionAuthorityConflict) as refusal:
        pgrec._read_selector_snapshot(OPID)
    assert "one single durable name" in str(refusal.value)


# --------------------------------------------------------------------- #
# x6: every denial has zero authority-side effects
# --------------------------------------------------------------------- #

@posix_only
def test_x6_every_denial_leaves_the_governed_tree_byte_identical(tmp_path):
    """x6: an admitted read and a REFUSED read both leave the governed tree
    byte-identical. A selector is never repaired, deleted, rewritten or
    quietly tidied - not even when the engine itself left a residue name
    beside it."""
    promote = {"operation_phase": "promote", "exit_status": 0,
               "operation_id": OPID}
    bound = _bytes({**CLAIM, "receipt_sha256": pgrec._receipt_digest(promote)})
    shapes = ("residue_admitted", "foreign_name_refused",
              "outside_link_refused")
    for shape in shapes:
        root = tmp_path / shape
        transitions, _record = _governed(root)
        claim, residue = _publisher_crash_residue(transitions, bound)
        extra = None
        if shape == "foreign_name_refused":
            extra = transitions / f"{OPID}.second"
            os.link(claim, extra)
        elif shape == "outside_link_refused":
            extra = root / "outside"
            os.link(claim, extra)
        before = _census(transitions)
        try:
            if extra is None:
                snapshot = pgrec._read_selector_snapshot(OPID)
                assert snapshot.present is True
                # the exact branch is decided by ONE admitted snapshot
                authority = pgrec._acquire_recovery_authority(OPID, promote)
                assert pgrec._valid_transition_claim(
                    OPID, "rollback", promote,
                    authority=authority) is True
                assert pgrec._valid_transition_claim(
                    OPID, "finalize", promote,
                    authority=authority) is False
            else:
                with pytest.raises(pgrec._ExecutionAuthorityConflict):
                    pgrec._read_selector_snapshot(OPID)
                # and the decision law fails closed instead of guessing
                assert pgrec._valid_transition_claim(
                    OPID, "rollback", promote) is False
            # the governed tree, the claim bytes, the residue and the foreign
            # name all survive the decision exactly as they were
            assert _census(transitions) == before
            assert claim.read_bytes() == bound
            assert residue.is_file()
            if extra is not None:
                assert extra.is_file()
        finally:
            if extra is not None:
                extra.unlink()
