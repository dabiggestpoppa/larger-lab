#!/usr/bin/env python3
"""B4-CXR7U9R35-R37 — recovery AUTHORITY proofs.

Filesystem containment (test_b4_cxr7u9r7_path_authority.py) proves WHERE
recovery inputs came from. It cannot prove WHAT they are allowed to order, and
that gap was a real defect: a promote receipt is JSON sitting in an approved
backup root, and its `quarantine_database` used to be trusted verbatim, so a
contained forgery naming the canonical database could direct finalize to drop
it. These proofs cover the authority that containment does not:

* RECOVERY TRANSITION AUTHORITY (R36): a promote receipt is validated as
  content — format, phase, exit status, promoted, complete phase sequence,
  governed database/user/container identity, stamp-bound quarantine and
  staging names, archive identity, inventory identity, run identity — before
  any docker or catalog call, so forged, replayed, substituted or incomplete
  receipts cannot mutate database state;
* GOVERNED TARGETS (R37): the destructive destination is the governed local
  identity; alternate --db/--user/--container values are refused;
* RECEIPT-WRITE AUTHORITY (R37): --receipt-out can only name a file inside the
  engine's own recovery-state directory;
* ONE ARCHIVE IDENTITY (R35): admission happens once and the container copy is
  hash-bound to the admitted bytes before any staging or canonical mutation.

Every denial is proven with a deterministic container/catalog bridge that
records all calls, so "no mutation" means the engine made no call to make one.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
CLI = SCRIPTS / "pg-recovery.py"

INVENTORY_DOC = ('{"format": "oce-pg-inventory-v1", "database": "oce_local",'
                 ' "table_count": 1, "tables": [{"name": "public.widgets",'
                 ' "row_count": 3, "fingerprint": "deadbeef"}]}')


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(SCRIPTS / filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pgrec = _load("u9r35_pgrec", "pg-recovery.py")


class _Done:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class _Bridge:
    """Deterministic stand-in for every container/catalog surface the three
    phases walk. It records each call, so a refusal can be proven to have made
    none, and it walks a genuine promote/finalize/rollback to completion so the
    receipts under test are the ones the engine actually emits."""

    def __init__(self):
        self.docker = []
        self.dropped = []
        self.renamed = []
        self.staged = []
        self.terminated = []
        self.copied = []
        self.dbs = {"postgres", pgrec.DB}
        self.remote_sha = None

    def docker_exec(self, container, cmd, stdin_bytes=None, timeout=600):
        self.docker.append(list(cmd))
        return _Done(0, b"")

    def clone(self, container, archive_path):
        self.copied.append(archive_path)
        return "/tmp/oce-probe/archive.dump"

    def validate(self, container, remote):
        return "archive listing"

    def remote_hash(self, container, remote):
        return self.remote_sha

    def catalog(self, container, user):
        return set(self.dbs)

    def create_staging(self, container, user, base_db, stamp):
        name = pgrec.STAGING_PREFIX + stamp
        self.staged.append(name)
        self.dbs.add(name)
        return name

    def drop(self, container, user, name):
        self.dropped.append(name)
        self.dbs.discard(name)

    def rename(self, container, user, from_name, to_name):
        self.renamed.append((from_name, to_name))
        self.dbs.discard(from_name)
        self.dbs.add(to_name)

    def terminate(self, container, user, *dbs):
        self.terminated.extend(dbs)

    def verify(self, container, db, user, inventory, probe):
        return True, [], {"public.widgets": 3}, {"public.widgets": "deadbeef"}

    def psql(self, container, db, user, sql, stdin_bytes=None):
        return _Done(0, b"16.2\n")

    def reset(self):
        """Forget the genuine promotion's calls: a denial must be judged on
        what the refused invocation itself did."""
        self.docker.clear()
        self.dropped.clear()
        self.renamed.clear()
        self.staged.clear()
        self.terminated.clear()

    def install(self, monkeypatch):
        for name, fn in (("clone_archive_into_container", self.clone),
                         ("validate_archive", self.validate),
                         ("sha256_remote_file", self.remote_hash),
                         ("create_staging_db", self.create_staging),
                         ("drop_db", self.drop),
                         ("rename_db", self.rename),
                         ("terminate_local_connections", self.terminate),
                         ("_verify_db", self.verify),
                         ("_catalog_names", self.catalog),
                         ("psql", self.psql),
                         ("docker_exec", self.docker_exec)):
            monkeypatch.setattr(pgrec, name, fn)


def _write_inputs(tmp_path, monkeypatch):
    """Approved backup-root content: inventory + its SHA + an archive. Every
    recovery input - and every receipt under test - lives inside this one
    approved root, so these proofs exercise CONTENT authority rather than
    re-testing containment."""
    roots = tmp_path / "roots"
    roots.mkdir()
    inv = roots / "inventory.json"
    inv.write_text(INVENTORY_DOC, encoding="utf-8")
    sha = roots / "inventory.sha256"
    sha.write_text(hashlib.sha256(INVENTORY_DOC.encode()).hexdigest(), encoding="utf-8")
    archive = roots / "archive.dump"
    archive.write_bytes(b"PGDMP")
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
    return inv, sha, archive


@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _promote_receipt(bridge, inv, sha, archive, name="promote-receipt.json"):
    """The genuine article: a complete promote receipt produced by the shipped
    phase code, written where the receipt read path may read it."""
    receipt = pgrec.phase_promote(str(archive), str(inv), str(sha), pgrec.DB,
                                  pgrec.USER, pgrec.CONTAINER, None)
    assert receipt["exit_status"] == 0, receipt
    path = archive.parent / name
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return receipt, path


def _mutated(receipt, mutate, where, name="forged.json"):
    forged = json.loads(json.dumps(receipt))
    mutate(forged)
    path = Path(where).parent / name
    path.write_text(json.dumps(forged), encoding="utf-8")
    return path


def _transition(bridge, phase, path, inv, sha):
    fn = pgrec.phase_finalize if phase == "finalize" else pgrec.phase_rollback
    return fn(str(path), str(inv), str(sha), pgrec.DB, pgrec.USER, pgrec.CONTAINER, None)


def _assert_no_transition_mutation(bridge, receipt, needle):
    assert receipt["exit_status"] == 1, receipt
    assert "refusing recovery transition authority" in receipt["error"], receipt
    assert needle in receipt["error"], receipt["error"]
    assert bridge.dropped == [], bridge.dropped
    assert bridge.renamed == [], bridge.renamed
    assert bridge.staged == [], bridge.staged
    assert bridge.docker == [], bridge.docker
    assert not receipt.get("promoted"), receipt


# --------------------------------------------------------------------- #
# positive controls: the genuine receipts these rules must NOT block
# --------------------------------------------------------------------- #

def test_genuine_promote_receipt_carries_governed_identity(bridge, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, _ = _promote_receipt(bridge, inv, sha, archive)
    assert receipt["user"] == pgrec.USER, receipt
    assert receipt["container"] == pgrec.CONTAINER, receipt
    assert receipt["database"] == receipt["source_database"] == receipt["target_database"]
    assert receipt["phases"] == pgrec.PHASES_PROMOTE
    assert receipt["quarantine_database"] == pgrec.QUARANTINE_PREFIX + receipt["stamp"]
    assert receipt["staging_database"] == pgrec.STAGING_PREFIX + receipt["stamp"]
    # the receipt records the admitted canonical inventory, not the CLI string
    assert receipt["inventory_path"] == pgrec._validated_open_path(str(inv))
    # and the container copy was hash-bound to the admitted bytes
    assert receipt["remote_archive_sha256"] == receipt["source_archive_sha256"]


def test_genuine_lifecycle_finalize_and_rollback_are_accepted(bridge, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    promoted, path = _promote_receipt(bridge, inv, sha, archive, "p1.json")
    final = _transition(bridge, "finalize", path, inv, sha)
    assert final["exit_status"] == 0, final
    assert final["quarantine_dropped"] is True
    assert bridge.dropped == [promoted["quarantine_database"]], bridge.dropped
    # a second, independent promotion can still be rolled back explicitly
    promoted2, path2 = _promote_receipt(bridge, inv, sha, archive, "p2.json")
    rollback = _transition(bridge, "rollback", path2, inv, sha)
    assert rollback["exit_status"] == 0, rollback
    assert rollback["quarantine_database"] == promoted2["quarantine_database"]
    assert (promoted2["quarantine_database"], pgrec.DB) in bridge.renamed, bridge.renamed


# --------------------------------------------------------------------- #
# R36: receipt CONTENT is transition authority
# --------------------------------------------------------------------- #

def _cases():
    return [
        ("format", lambda r: r.__setitem__("format", "oce-something-else"),
         "receipt format is not"),
        ("not-a-promote", lambda r: r.__setitem__("operation_phase", "finalize"),
         "is not a promote receipt"),
        ("failed-exit-status", lambda r: r.__setitem__("exit_status", 1),
         "records a failed promote"),
        ("not-promoted", lambda r: r.__setitem__("promoted", False),
         "does not record a completed promotion"),
        ("stamp-missing", lambda r: r.pop("stamp"), "stamp"),
        ("stamp-malformed", lambda r: r.__setitem__("stamp", "zzzz-not-hex"),
         "stamp"),
        ("quarantine-unbound", lambda r: r.__setitem__(
            "quarantine_database", pgrec.QUARANTINE_PREFIX + "0123456789ab"),
         "quarantine"),
        ("staging-unbound", lambda r: r.__setitem__(
            "staging_database", pgrec.STAGING_PREFIX + "0123456789ab"),
         "staging"),
        ("quarantine-is-canonical", lambda r: r.__setitem__(
            "quarantine_database", pgrec.DB), "quarantine"),
        ("staging-is-canonical", lambda r: r.__setitem__(
            "staging_database", pgrec.DB), "staging"),
        ("wrong-database", lambda r: r.__setitem__("database", "postgres"),
         "database"),
        ("inconsistent-source", lambda r: r.__setitem__(
            "source_database", "another_db"), "source_database"),
        ("inconsistent-target", lambda r: r.__setitem__(
            "target_database", "another_db"), "target_database"),
        ("wrong-user", lambda r: r.__setitem__("user", "postgres"), "user"),
        ("wrong-container", lambda r: r.__setitem__("container", "other-pg"),
         "container"),
        ("incomplete-phases", lambda r: r.__setitem__("phases", ["inventory_validated"]),
         "phase sequence"),
        ("reordered-phases", lambda r: r.__setitem__(
            "phases", list(reversed(r["phases"]))), "phase sequence"),
        ("invented-phase", lambda r: r.__setitem__(
            "phases", r["phases"][:-1] + ["promoted_again"]), "phase sequence"),
        ("no-archive-identity", lambda r: r.pop("source_archive_sha256"),
         "archive identity"),
        ("other-inventory", lambda r: r.__setitem__(
            "inventory_path", os.path.join(os.sep, "tmp", "elsewhere.json")),
         "inventory"),
        ("other-inventory-sha", lambda r: r.__setitem__("inventory_sha256", "b" * 64),
         "inventory SHA"),
    ]


@pytest.mark.parametrize("name,mutate,needle", _cases(), ids=[c[0] for c in _cases()])
def test_forged_or_incomplete_receipt_cannot_order_a_transition(
        bridge, tmp_path, monkeypatch, name, mutate, needle):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    monkeypatch.setenv("OCE_RUN_ID", "feedface1234")
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive)
    forged = _mutated(receipt, mutate, path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_no_transition_mutation(bridge, out, needle)


def test_receipt_from_a_different_run_is_refused(bridge, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    monkeypatch.setenv("OCE_RUN_ID", "feedface1234")
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive)
    forged = _mutated(receipt, lambda r: r.__setitem__("run_id", "deadbeef4321"), path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_no_transition_mutation(bridge, out, "different recovery run")


def test_forged_finalize_receipt_cannot_drop_the_canonical_database(
        bridge, tmp_path, monkeypatch):
    """The defect this gate exists for: a contained receipt that claims a
    successful promotion and names the CANONICAL database as its quarantine.
    Before R36 this reached DROP DATABASE on live truth."""
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive)
    forged = _mutated(receipt, lambda r: r.update({
        "promoted": True, "exit_status": 0,
        "quarantine_database": pgrec.DB}), path)
    bridge.reset()
    out = _transition(bridge, "finalize", forged, inv, sha)
    _assert_no_transition_mutation(bridge, out, "quarantine")
    assert pgrec.DB not in bridge.dropped and pgrec.DB not in bridge.renamed


@pytest.mark.parametrize("selection,needle", [
    ("canonical", "quarantine"),
    ("arbitrary", "quarantine"),
    ("other-stamps", "quarantine"),
])
def test_forged_rollback_receipt_cannot_redirect_a_restore(
        bridge, tmp_path, monkeypatch, selection, needle):
    """rollback forwards the receipt's quarantine into rename/drop recovery
    logic, so it must be refused for the canonical name, for an arbitrary
    database, and for a valid-looking quarantine belonging to another stamp."""
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive)
    names = {"canonical": pgrec.DB,
             "arbitrary": "some_other_database",
             "other-stamps": pgrec.QUARANTINE_PREFIX + "0123456789ab"}
    forged = _mutated(receipt,
                      lambda r: r.__setitem__("quarantine_database", names[selection]),
                      path)
    bridge.reset()
    out = _transition(bridge, "rollback", forged, inv, sha)
    assert out["exit_status"] == 1, out
    assert "refusing recovery transition authority" in out["error"], out
    assert needle in out["error"], out["error"]
    assert bridge.dropped == [], bridge.dropped
    assert bridge.renamed == [], bridge.renamed
    assert bridge.docker == [], bridge.docker


def test_malformed_receipt_json_is_refused_before_any_call(bridge, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    broken = archive.parent / "broken.json"
    broken.write_text("{not json at all", encoding="utf-8")
    out = _transition(bridge, "finalize", broken, inv, sha)
    _assert_no_transition_mutation(bridge, out, "refusing recovery transition authority")


def test_receipt_refusal_writes_no_audit_side_effect_but_records_itself(
        bridge, tmp_path, monkeypatch):
    """A refusal is evidence, not silence: the caller still gets a receipt, and
    the recovery state it refused to touch is untouched."""
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive)
    forged = _mutated(receipt, lambda r: r.__setitem__("promoted", False), path)
    before = set(bridge.dbs)
    out = _transition(bridge, "finalize", forged, inv, sha)
    assert set(bridge.dbs) == before
    assert "error" in out and out["finished_at"]
