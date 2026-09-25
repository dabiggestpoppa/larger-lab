#!/usr/bin/env python3
"""B4-CXR7U9R39-R3 — durable, single-use recovery TRANSITION authority.

R36 validated a promote receipt's CONTENT, but the receipt itself remained the
authority to finalize or roll back, so the same receipt could be presented
repeatedly, a structurally plausible substitution was indistinguishable from a
genuine one, and nothing bound a transition to the operation that produced it.

These proofs cover the durable operation record that now owns that authority:
one high-entropy operation id per promotion, a state machine
(CREATED -> STAGED -> PROMOTED -> FINALIZED | ROLLED_BACK, or FAILED), a
content digest binding the receipt to the record, and a one-time claim taken
BEFORE any docker or catalog call. Every denial is judged against the
deterministic bridge (no call, no catalog change, no authority-store change).

The bridge and the genuine promote/deny helpers are the ones proven in
test_b4_cxr7u9r35_recovery_authority.py; this suite imports them rather than
growing a second copy.
"""
import hashlib
import json
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _mutated, _promote_receipt, production_recovery_identity, pgrec)

TRANSITION_FORMAT = pgrec.TRANSITION_FORMAT


@pytest.fixture
def bridge(monkeypatch):
    """The deterministic engine bridge proven in the R35 suite, reused here:
    every denial must be judged on the calls the refused invocation made."""
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _tree_state(root):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def _record(operation_id):
    return pgrec._load_transition_record(operation_id)


def _transition(bridge, phase, path, inv, sha):
    fn = pgrec.phase_finalize if phase == "finalize" else pgrec.phase_rollback
    try:
        return fn(str(path), str(inv), str(sha), pgrec.DB, pgrec.USER,
                  pgrec.CONTAINER, None)
    except pgrec._ExecutionAuthorityConflict as exc:
        # B4-CXR7U9R44R2: a receipt that is not bound to a governed durable
        # operation is now refused BEFORE a lock coordinate can be
        # provisioned, so the refusal raises instead of returning a phase
        # receipt. It is strictly stronger than before: no coordinate, no
        # metadata, no claim, and no receipt of its own.
        return {"exit_status": 1, "error": str(exc), "operation_phase": phase,
                "refused_before_authority": True}


def _inputs(tmp_path, monkeypatch):
    """This test's approved backup root: inventory + its SHA + an archive.
    Reusable within one test, so several promotions can be driven."""
    roots = tmp_path / "roots"
    roots.mkdir(exist_ok=True)
    inv = roots / "inventory.json"
    inv.write_text(json.dumps({"format": "oce-pg-inventory-v1", "database": "oce_local",
                               "table_count": 1,
                               "tables": [{"name": "public.widgets", "row_count": 3,
                                           "fingerprint": "deadbeef"}]}), encoding="utf-8")
    sha = roots / "inventory.sha256"
    sha.write_text(hashlib.sha256(inv.read_text(encoding="utf-8").encode()).hexdigest(),
                   encoding="utf-8")
    archive = roots / "archive.dump"
    archive.write_bytes(b"PGDMP")
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
    return inv, sha, archive


def _promoted(bridge, tmp_path, monkeypatch, name="promote.json"):
    """One genuine promotion, with the receipt written under `name`."""
    inv, sha, archive = _inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive, name)
    return receipt, path, inv, sha


def _assert_refused_without_mutation(bridge, out, needle):
    assert out["exit_status"] == 1, out
    assert "refusing recovery transition authority" in out["error"] \
        or "refusing to enter execution authority" in out["error"], out
    assert needle in out["error"], out["error"]
    assert bridge.docker == [], bridge.docker
    assert bridge.dropped == [] and bridge.renamed == [] and bridge.staged == []


def _identity_refusal(path, inv, sha, needle):
    """The receipt's own identity rules are unchanged: prove the specific
    reason is still named even though R44 refuses earlier and more cheaply."""
    with pytest.raises(RuntimeError) as refused:
        pgrec._validated_promote_receipt(str(path), pgrec.DB, pgrec.USER,
                                         pgrec.CONTAINER, str(inv), str(sha))
    assert needle in str(refused.value), str(refused.value)


# --------------------------------------------------------------------- #
# the durable record and its state machine
# --------------------------------------------------------------------- #

def test_promotion_mints_one_durable_operation_in_the_governed_boundary(
        bridge, tmp_path, monkeypatch):
    receipt, _, _, _ = _promoted(bridge, tmp_path, monkeypatch)
    operation_id = receipt["operation_id"]
    assert pgrec.OPERATION_ID_RE.match(operation_id), operation_id
    record = _record(operation_id)
    assert record["format"] == TRANSITION_FORMAT
    assert record["state"] == pgrec.TRANSITION_STATE_PROMOTED
    assert record["permitted_next"] == ["finalize", "rollback"]
    assert record["receipt_sha256"] == pgrec._receipt_digest(receipt)
    # the record binds the identity and the snapshot the receipt names
    for label in ("database", "user", "container", "source_commit", "source_tree",
                  "run_id", "stamp", "quarantine_database", "staging_database",
                  "source_archive_sha256", "inventory_sha256"):
        assert record[label] == receipt[label], label
    assert record["created_at"] and record["updated_at"]
    # it lives under the governed recovery boundary, and nothing is claimed yet
    governed = pgrec._recovery_state_dir()
    assert str(Path(pgrec._transition_record_path(operation_id)).parent).startswith(governed)
    assert not list(Path(governed).rglob("*.claim"))


def test_operation_state_is_durable_across_engine_instances(bridge, tmp_path, monkeypatch):
    """The authority is on disk, not in the process that minted it: a second
    engine instance reading the same governed boundary sees the same state."""
    receipt, _, _, _ = _promoted(bridge, tmp_path, monkeypatch)
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(
        "r3_second_engine", str(Path(pgrec.__file__)))
    second = importlib.util.module_from_spec(spec)
    sys.modules["r3_second_engine"] = second
    spec.loader.exec_module(second)
    second._bind_test_recovery_root(pgrec._recovery_state_dir())
    try:
        assert second._load_transition_record(receipt["operation_id"])["state"] == \
            pgrec.TRANSITION_STATE_PROMOTED
    finally:
        second._unbind_test_recovery_root()


@pytest.mark.parametrize("phase,terminal", [("finalize", "FINALIZED"),
                                            ("rollback", "ROLLED_BACK")])
def test_a_transition_consumes_the_promoted_authority_exactly_once(
        bridge, tmp_path, monkeypatch, phase, terminal):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    first = _transition(bridge, phase, path, inv, sha)
    assert first["exit_status"] == 0, first
    assert _record(receipt["operation_id"])["state"] == terminal
    assert _record(receipt["operation_id"])["permitted_next"] == []
    bridge.reset()
    before = _tree_state(tmp_path)
    second = _transition(bridge, phase, path, inv, sha)
    _assert_refused_without_mutation(bridge, second, "no longer available")
    assert _tree_state(tmp_path) == before, "a denial wrote durable state"
    assert _record(receipt["operation_id"])["state"] == terminal


@pytest.mark.parametrize("first,second", [("finalize", "rollback"),
                                          ("rollback", "finalize")])
def test_a_terminal_operation_refuses_the_other_transition(
        bridge, tmp_path, monkeypatch, first, second):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    assert _transition(bridge, first, path, inv, sha)["exit_status"] == 0
    bridge.reset()
    out = _transition(bridge, second, path, inv, sha)
    _assert_refused_without_mutation(bridge, out, "no longer available")


def test_replaying_a_transition_with_the_same_receipt_is_denied_before_any_call(
        bridge, tmp_path, monkeypatch):
    """Finalize replay: the exact receipt that finalized is presented again."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    assert _transition(bridge, "finalize", path, inv, sha)["exit_status"] == 0
    bridge.reset()
    out = _transition(bridge, "finalize", path, inv, sha)
    _assert_refused_without_mutation(bridge, out, "no longer available")


def test_finalize_after_rollback_is_denied(bridge, tmp_path, monkeypatch):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    assert _transition(bridge, "rollback", path, inv, sha)["exit_status"] == 0
    bridge.reset()
    _assert_refused_without_mutation(bridge, _transition(bridge, "finalize", path, inv, sha),
                                     "no longer available")


# --------------------------------------------------------------------- #
# substitution, registration and identity
# --------------------------------------------------------------------- #

def test_structurally_valid_substitution_is_denied_by_the_content_binding(
        bridge, tmp_path, monkeypatch):
    """Every identity field stays consistent with the record; only the receipt's
    CONTENT differs, which the digest is there to catch."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    forged = _mutated(receipt, lambda r: r.__setitem__("finished_at", "2001-01-01T00:00:00Z"),
                      path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_refused_without_mutation(bridge, out, "does not match its durable operation record")


def test_unregistered_receipt_is_denied(bridge, tmp_path, monkeypatch):
    """A receipt whose identity is otherwise perfect but which no operation
    record ever registered is not authority."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    forged = _mutated(receipt, lambda r: r.__setitem__("operation_id", "f" * 32), path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_refused_without_mutation(bridge, out, "no durable recovery operation record")


def test_cross_operation_receipt_is_denied(bridge, tmp_path, monkeypatch):
    """Two independent operations: consuming one leaves the other's authority
    intact, and the consumed operation's receipt is refused."""
    first, path_a, inv, sha = _promoted(bridge, tmp_path, monkeypatch, "a.json")
    second, path_b, _, _ = _promoted(bridge, tmp_path, monkeypatch, "b.json")
    assert first["operation_id"] != second["operation_id"]
    assert _transition(bridge, "finalize", path_a, inv, sha)["exit_status"] == 0
    bridge.reset()
    _assert_refused_without_mutation(bridge, _transition(bridge, "finalize", path_a, inv, sha),
                                     "no longer available")
    other = _transition(bridge, "rollback", path_b, inv, sha)
    assert other["exit_status"] == 0, other
    assert _record(second["operation_id"])["state"] == "ROLLED_BACK"


@pytest.mark.parametrize("label,value,needle", [
    ("source_commit", "unknown", "not a known revision"),
    ("source_tree", "not-set", "not a known revision"),
    ("source_commit", "", "not a known revision"),
    ("run_id", "unknown", "no authoritative run identity"),
    ("run_id", "not-set", "no authoritative run identity"),
])
def test_unknown_identity_is_not_transition_authority(
        bridge, tmp_path, monkeypatch, label, value, needle):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    forged = _mutated(receipt, lambda r: r.__setitem__(label, value), path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_refused_without_mutation(
        bridge, out, "does not match its durable operation record")
    _identity_refusal(forged, inv, sha, needle)


def test_a_receipt_from_another_run_is_denied(bridge, tmp_path, monkeypatch):
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    forged = _mutated(receipt, lambda r: r.__setitem__("run_id", "ffffffffffffffff"), path)
    bridge.reset()
    _assert_refused_without_mutation(
        bridge, _transition(bridge, "finalize", forged, inv, sha),
        "does not match its durable operation record")
    _identity_refusal(forged, inv, sha, "different recovery run")


def test_a_preflight_refusal_opens_no_operation_state_at_all(
        bridge, tmp_path, monkeypatch):
    """A promotion refused BEFORE it touches recovery-durable state is not an
    operation: its receipt names an operation id, but no record exists, so it
    holds no transition authority and leaves the governed store empty."""
    inv, sha, _archive = _inputs(tmp_path, monkeypatch)
    governed = Path(pgrec._recovery_state_dir())
    out = pgrec.phase_promote(str(tmp_path / "outside.dump"), str(inv), str(sha),
                              pgrec.DB, pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1, out
    assert pgrec.OPERATION_ID_RE.match(out["operation_id"])
    assert not (governed / "transitions").exists(), \
        sorted(str(p) for p in governed.rglob("*"))
    path = tmp_path / "roots" / "refused-promote.json"
    path.write_text(json.dumps(out), encoding="utf-8")
    bridge.reset()
    # it is refused as a failed promotion, and nothing durable is touched
    _assert_refused_without_mutation(
        bridge, _transition(bridge, "finalize", path, inv, sha),
        "no governed recovery transition directory")
    assert not list((governed / "transitions").glob("*.json"))
    assert not list((governed / "transitions").glob("*.claim"))


def test_a_promotion_that_fails_after_staging_records_a_terminal_failure(
        bridge, tmp_path, monkeypatch):
    """Once the promotion has begun, a failure is a FAILED operation: the
    record offers no transition, and its receipt is refused by content too."""
    inv, sha, archive = _inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    monkeypatch.setattr(pgrec, "_verify_db",
                        lambda *a, **k: (False, ["staging truth broken"], {}, None))
    out = pgrec.phase_promote(str(archive), str(inv), str(sha), pgrec.DB,
                              pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1, out
    assert "staging verification FAILED" in out["error"], out["error"]
    record = _record(out["operation_id"])
    assert record["state"] == "FAILED"
    assert record["permitted_next"] == []
    path = tmp_path / "roots" / "failed-promote.json"
    path.write_text(json.dumps(out), encoding="utf-8")
    bridge.reset()
    # the receipt is still refused as a failed promotion, and nothing mutates
    _assert_refused_without_mutation(bridge, _transition(bridge, "finalize", path, inv, sha),
                                     "failed promote")


# --------------------------------------------------------------------- #
# crash safety and durability of the flow
# --------------------------------------------------------------------- #

def test_an_interrupted_transition_leaves_the_authority_spent(
        bridge, tmp_path, monkeypatch):
    """A claim is taken BEFORE the work, so an interruption (the claim exists,
    the work never finished) truthfully means the authority is already spent -
    it can never be replayed to repeat a destructive step. The operation-wide
    claim durably names the selected transition and moves the record to the
    matching in-flight state, so the interruption is ATTRIBUTABLE."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    bridge.reset()
    out = _transition(bridge, "finalize", path, inv, sha)
    _assert_refused_without_mutation(bridge, out, "its finalize authority is "
                                     "no longer available")
    # the claim durably named the selection; the record is FINALIZING, never
    # re-opened as PROMOTED authority
    claim = pgrec._load_claim(receipt["operation_id"])
    assert claim["transition"] == "finalize"
    assert claim["receipt_sha256"] == pgrec._receipt_digest(receipt)
    assert _record(receipt["operation_id"])["state"] == pgrec.TRANSITION_STATE_FINALIZING


def test_a_transition_survives_a_receipt_json_round_trip(bridge, tmp_path, monkeypatch):
    """The durable hand-off IS a file: re-serializing the promote receipt (as
    restore.sh and every operator does) must not invalidate its authority."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    rewritten = Path(path).parent / "reserialized.json"
    rewritten.write_text(json.dumps(json.loads(Path(path).read_text(encoding="utf-8")),
                                    indent=4), encoding="utf-8")
    out = _transition(bridge, "finalize", rewritten, inv, sha)
    assert out["exit_status"] == 0, out
    assert _record(receipt["operation_id"])["state"] == "FINALIZED"
