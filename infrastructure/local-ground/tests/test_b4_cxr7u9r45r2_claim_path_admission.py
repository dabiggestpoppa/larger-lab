#!/usr/bin/env python3
"""B4-CXR7U9R45R2 — canonical claim PATH and TYPE admission, and the exact
receipt binding that decides every selector verdict.

R44 proved the PUBLICATION of the canonical claim is crash-atomic. R45 proves
the consumption of an already-published claim is equally hard:

* FRESH AUTHORITY EXISTS ONLY WHEN THE CANONICAL CLAIM PATHNAME IS ABSENT
  (R45-01). A claim that exists but is unbound, wrongly bound, malformed or
  coordinate-inadmissible is spent authority — never fresh, never repaired,
  never deleted (R45R1 law, exercised through BOTH the shell classifier and
  the reconciliation engine);
* the claim pathname must pass the same class of admission as the governed
  lock coordinate (R45-02): engine-derived name, realpath containment in the
  governed transitions directory, regular-file type, symlink refusal (even to
  a target inside the approved root), POSIX privacy, replacement detection;
* every refusal proves ZERO mutation of the durable record, the receipt
  catalog, the existing claim and the container bridge (no dropped database,
  no rename, no staging, no docker call);
* the executable weakened control reproduces the pre-R45R1 false-fresh
  behavior at runtime and the shipped engine kills it (the R45-03 negative
  control for the selector law), while the exact-bound positives are proven
  byte-identical on both engines.

The in-process harness reuses the R35 authority proofs: the promote receipts
under test are the genuine article produced by the shipped phase code. Every
binding is computed from the receipt exactly as the engine binds it — the
canonical JSON digest of the RECEIPT ON DISK.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import recovery_cli
from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)

CLI = Path(pgrec.__file__)


# --------------------------------------------------------------------- #
# harness: a genuine promoted operation and its governed coordinates
# --------------------------------------------------------------------- #

@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _promoted(bridge, tmp_path, monkeypatch, name="p.json"):
    """A genuine promote: returns (disk_receipt, receipt_path, inv, sha).

    Each call gets its OWN approved backup root, so one test may promote
    several independent operations without colliding on r35's fixed root."""
    from test_b4_cxr7u9r35_recovery_authority import INVENTORY_DOC
    # ONE shared approved root for every promote in this test: the receipt
    # read path only opens receipts inside OCE_BACKUP_ROOTS, and a later
    # child process must still be able to read an earlier receipt.
    roots = tmp_path / "roots"
    roots.mkdir(exist_ok=True)
    inv = roots / "inventory.json"
    inv.write_text(INVENTORY_DOC, encoding="utf-8")
    sha = roots / "inventory.sha256"
    sha.write_text(hashlib.sha256(INVENTORY_DOC.encode()).hexdigest(),
                   encoding="utf-8")
    archive = roots / "archive.dump"
    archive.write_bytes(b"PGDMP")
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive, name)
    return json.loads(path.read_text(encoding="utf-8")), path, inv, sha


def _transitions():
    return Path(pgrec._recovery_state_dir()) / "transitions"


def _record_path(opid):
    return _transitions() / f"{opid}.json"


def _claim_path(opid):
    return _transitions() / f"{opid}.claim"


def _load_record(opid):
    return json.loads(_record_path(opid).read_text(encoding="utf-8"))


def _digest(receipt):
    return pgrec._receipt_digest(receipt)


def _write_claim(opid, claim):
    """Hand-publish a canonical claim the way the engine's payload is
    published: private (0600), regular, in place. The CONTENT under test is
    written verbatim by each refusal case."""
    path = _claim_path(opid)
    path.write_text(json.dumps(claim), encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def _bound_claim(receipt, transition):
    return {
        "format": pgrec._CLAIM_FORMAT,
        "operation_id": receipt["operation_id"],
        "transition": transition,
        "receipt_sha256": _digest(receipt),
        "claimed_at": "2026-09-24T00:00:00Z",
    }


def _census(root):
    """Byte-exact census of a tree: relative name -> (size, sha256). A denial
    that leaves this unchanged durably did nothing."""
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = (
                path.stat().st_size,
                hashlib.sha256(path.read_bytes()).hexdigest())
    return out


# --------------------------------------------------------------------- #
# the two shell surfaces under test
# --------------------------------------------------------------------- #

def _shell_state(record_path):
    return subprocess.run(
        [sys.executable, str(CLI), "--phase", "reconcile",
         "--classify-state", str(record_path)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=60).returncode


def _shell_receipt(receipt_path):
    return subprocess.run(
        [sys.executable, str(CLI), "--phase", "reconcile",
         "--classify-rollback", str(receipt_path),
         "--transition-dir", str(_transitions())],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=60).returncode


def _reconcile_argv(receipt_path, output):
    return ["--phase", "reconcile", "--receipt-in", str(receipt_path),
            "--inventory", str(Path(pgrec._recovery_state_dir()).parent),
            "--inventory-sha", str(Path(pgrec._recovery_state_dir()).parent),
            "--receipt-out", str(output)]


# --------------------------------------------------------------------- #
# R45-02: coordinate admission refusals — zero mutation each
# --------------------------------------------------------------------- #

def _symlink_or_skip(target, link):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError) as e:
        pytest.skip(f"symlink creation is unavailable on this platform: {e}")


def test_symlink_claim_is_refused_even_to_a_valid_target(
        bridge, tmp_path, monkeypatch):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    # a COMPLETE, exactly-bound engine-shaped claim, published elsewhere in
    # the governed tree, reached through a symlink at the canonical name
    valid = _transitions() / f"{opid}.valid-claim"
    valid.write_text(json.dumps(_bound_claim(receipt, "rollback")),
                     encoding="utf-8")
    os.chmod(valid, 0o600)
    _symlink_or_skip(valid, _claim_path(opid))

    before = _census(_transitions())
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _shell_receipt(path) == 4
    assert _census(_transitions()) == before


def test_symlink_claim_pointing_outside_the_governed_root_is_refused(
        bridge, tmp_path, monkeypatch):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    external = tmp_path / "external.claim"
    external.write_text(json.dumps(_bound_claim(receipt, "rollback")),
                        encoding="utf-8")
    _symlink_or_skip(external, _claim_path(opid))

    before = _census(_transitions())
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _census(_transitions()) == before


def test_directory_at_the_claim_pathname_is_refused(bridge, tmp_path,
                                                    monkeypatch):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _claim_path(opid).mkdir()

    before = _census(_transitions())
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _shell_receipt(path) == 4
    assert _census(_transitions()) == before
    assert _claim_path(opid).is_dir(), "the engine must not delete the object"


@pytest.mark.skipif(os.name == "nt",
                    reason="POSIX group/other permission bits only")
def test_widened_claim_permissions_are_refused(bridge, tmp_path, monkeypatch):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    path = _write_claim(opid, _bound_claim(receipt, "rollback"))
    os.chmod(path, 0o644)

    before = _census(_transitions())
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _census(_transitions()) == before


# --------------------------------------------------------------------- #
# R45-01/R45-02: binding refusals — a claim that exists is NEVER fresh
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("content,why", [
    pytest.param(
        lambda r: {k: v for k, v in _bound_claim(r, "rollback").items()
                   if k != "receipt_sha256"}, "missing digest",
        id="missing-digest"),
    pytest.param(
        lambda r: {**_bound_claim(r, "rollback"),
                   "receipt_sha256": "not-a-digest"}, "malformed digest",
        id="malformed-digest"),
    pytest.param(
        lambda r: {**_bound_claim(r, "rollback"),
                   "receipt_sha256": "a" * 64}, "correct-length foreign digest",
        id="foreign-digest"),
])
def test_unbindable_digests_are_never_fresh(bridge, tmp_path, monkeypatch,
                                            content, why):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, content(receipt))

    before = _census(tmp_path)
    # the shell route with the receipt binds the expectation and must refuse
    assert _shell_receipt(path) == 4, why
    # the shell route WITHOUT a receipt can never call a present claim fresh
    assert _shell_state(_record_path(opid)) == 4, why
    # the semantic law reports the spent shape, never fresh
    assert pgrec._claim_state(opid) == "unbound_or_mismatched", why
    assert _census(tmp_path) == before, why


@pytest.mark.parametrize("transition", ["rollback", "finalize"])
def test_a_well_formed_claim_bound_to_a_different_promote_is_never_fresh(
        bridge, tmp_path, monkeypatch, transition):
    """A structurally perfect claim whose digest binds ANOTHER genuine
    promote receipt of another operation: well-formed, exactly typed, and
    still never fresh for THIS operation's authority."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    other, _other_path, _i2, _s2 = _promoted(bridge, tmp_path, monkeypatch,
                                             name="other.json")
    opid = receipt["operation_id"]
    assert _digest(other) != _digest(receipt)
    # THIS operation's id, a permitted transition, a perfectly shaped digest —
    # but the digest binds the OTHER receipt, not this operation's authority
    _write_claim(opid, {**_bound_claim(receipt, transition),
                        "receipt_sha256": _digest(other)})

    before = _census(tmp_path)
    assert pgrec._claim_state(
        opid, expected_receipt_sha256=_digest(receipt)) == "unbound_or_mismatched"
    assert _shell_receipt(path) == 4
    assert _shell_state(_record_path(opid)) == 4
    assert _census(tmp_path) == before
    # the durable record was never touched
    assert _load_record(opid)["state"] == "PROMOTED"
    assert len(list(_transitions().glob("*.claim"))) == 1


def test_wrong_operation_id_claim_is_never_fresh(bridge, tmp_path,
                                                 monkeypatch):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    forged = _bound_claim(receipt, "rollback")
    forged["operation_id"] = "f" * 32
    _write_claim(opid, forged)

    before = _census(tmp_path)
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _shell_receipt(path) == 4
    assert _census(tmp_path) == before


@pytest.mark.parametrize("selector", ["rollback", "foreign_digest"])
def test_state_claim_transition_disagreement_fails_closed(
        bridge, tmp_path, monkeypatch, selector):
    """State/claim transition disagreement (R45-03): the durable record
    selected finalize; a rollback selector — or a finalize selector bound to
    foreign authority — must never re-open governed abort authority over it.
    An exact-bound finalize selector AGREES with the record and keeps the
    governed preintent abort (the positive, parametrized in
    test_exactly_bound_claims_resume_their_branch)."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    record = _load_record(opid)
    record["state"] = pgrec.TRANSITION_STATE_FINALIZING
    record["selected_transition"] = "finalize"
    _record_path(opid).write_text(json.dumps(record), encoding="utf-8")
    if selector == "rollback":
        # complete, well-shaped, but the WRONG branch for this record
        _write_claim(opid, _bound_claim(receipt, "rollback"))
    else:
        # the RIGHT branch name, bound to foreign authority
        _write_claim(opid, {**_bound_claim(receipt, "finalize"),
                            "receipt_sha256": "a" * 64})

    before = _census(tmp_path)
    # BOTH surfaces fail closed. The receipted route binds the digest
    # expectation and refuses (4). The receiptless state route resolves the
    # branch NAME agreement: a complete claim naming rollback under a
    # durably finalize-selected record is detectable disagreement (4); a
    # finalize-naming claim with a foreign digest cannot be bound receiptlessly
    # and falls back to the fail-safe preintent verdict (5) — never fresh (0)
    # in either case.
    assert _shell_receipt(path) == 4
    if selector == "rollback":
        assert _shell_state(_record_path(opid)) == 4
    else:
        assert _shell_state(_record_path(opid)) == 5
    assert _census(tmp_path) == before


def test_exactly_bound_finalize_selector_under_finalizing_record_agrees(
        bridge, tmp_path, monkeypatch):
    """The positive disagreement control: an exact-bound finalize selector
    under a FINALIZING record is the one agreeing shape, and both surfaces
    return the governed preintent abort (5) for it."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    record = _load_record(opid)
    record["state"] = pgrec.TRANSITION_STATE_FINALIZING
    record["selected_transition"] = "finalize"
    _record_path(opid).write_text(json.dumps(record), encoding="utf-8")
    _write_claim(opid, _bound_claim(receipt, "finalize"))

    before = _census(tmp_path)
    assert _shell_state(_record_path(opid)) == 5
    assert _shell_receipt(path) == 5
    assert _census(tmp_path) == before


def test_foreign_structure_claim_is_malformed_and_never_fresh(
        bridge, tmp_path, monkeypatch):
    """A canonical claim NAME holding a structurally valid JSON object that is
    not an engine-published claim (a foreign write): malformed, fail-closed,
    never fresh — through every consumer."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, {"format": pgrec._CLAIM_FORMAT,
                        "note": "hand-written, no binding fields"})

    before = _census(tmp_path)
    assert pgrec._claim_state(opid) == "malformed"
    assert _shell_state(_record_path(opid)) == 4
    assert _shell_receipt(path) == 4
    assert _census(tmp_path) == before


# --------------------------------------------------------------------- #
# R45-01: the exact-bound positives and ABSENCE stay intact
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("transition", ["rollback", "finalize"])
def test_exactly_bound_claims_resume_their_branch(bridge, tmp_path,
                                                  monkeypatch, transition):
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, _bound_claim(receipt, transition))
    assert pgrec._claim_state(opid, expected_receipt_sha256=_digest(receipt)) \
        == "bound_complete"

    # the exact-bound selector resumes ITS branch (6 rollback / 5 finalize),
    # never fresh (0)
    assert _shell_receipt(path) == (6 if transition == "rollback" else 5)

    # removing the selector is the ONLY thing that restores fresh authority
    _claim_path(opid).unlink()
    assert pgrec._claim_state(opid) == "absent"
    assert _shell_state(_record_path(opid)) == 0
    assert _shell_receipt(path) == 0


def test_engine_published_claim_passes_its_own_admission(bridge, tmp_path,
                                                         monkeypatch):
    """A claim published by the REAL engine is admitted by the REAL engine:
    the engine's own publication (temporary, chmod, no-replace rename) is the
    exact coordinate shape the admission demands."""
    receipt, rpath, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    out = pgrec.phase_rollback(str(rpath), str(inv), str(sha), pgrec.DB,
                               pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 0, out
    claim = _claim_path(opid)
    assert claim.is_file()
    import stat
    assert stat.S_ISREG(claim.lstat().st_mode)
    if os.name != "nt":
        assert stat.S_IMODE(claim.lstat().st_mode) & 0o077 == 0
    assert pgrec._claim_state(opid, expected_receipt_sha256=_digest(receipt)) \
        == "bound_complete"
    assert pgrec._claim_state(opid) == "unbound_or_mismatched"


def test_receiptless_promoted_with_present_claim_is_never_fresh(
        bridge, tmp_path, monkeypatch):
    """PROMOTED + present claim + NO receipt to bind: --classify-state must
    fail closed, while the truly absent selector stays fresh (0)."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, _bound_claim(receipt, "rollback"))
    assert _shell_state(_record_path(opid)) == 4
    _claim_path(opid).unlink()
    assert _shell_state(_record_path(opid)) == 0


# --------------------------------------------------------------------- #
# R45-03: the executable weakened control — false-fresh reproduced, killed
# --------------------------------------------------------------------- #

# ONE targeted transform: delete exactly the receiptless spent-selector veto
# the R45R1 law added. Every other veto (malformed, unbound-with-expectation)
# stays — so the weakened engine fails ONLY on the row the law is about, and
# the positives prove the weakening is surgical, not a general disarm.
_WEAKENED_TRANSFORM = ('''        elif isinstance(operation_id, str) \\
                and OPERATION_ID_RE.match(operation_id) \\
                and _claim_state(operation_id, transition_dir) != "absent":
            # PROMOTED with an existing canonical claim and NO receipt to bind:
            # the selector name exists, so the one-time authority is spent —
            # never fresh (B4-CXR7U9R45R1).
            return 4
        return 0
''', '''        return 0
''')


def _weakened_engine(tmp_path):
    source = CLI.read_text(encoding="utf-8")
    old, new = _WEAKENED_TRANSFORM
    assert old in source, "the R45R1 selector law changed shape"
    source = source.replace(old, new)
    assert source != CLI.read_text(encoding="utf-8")
    path = tmp_path / "weakened-pg-recovery.py"
    path.write_text(source, encoding="utf-8")
    return path


def _run_engine(engine_path, argv):
    return subprocess.run(
        [sys.executable, str(engine_path), *map(str, argv)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=60).returncode


@pytest.mark.parametrize("poison", ["missing_digest", "foreign_digest"])
def test_weakened_classifier_reproduces_false_fresh_and_the_shipped_engine_kills_it(
        bridge, tmp_path, monkeypatch, poison):
    """Executable negative control. The weakened engine copy drops the R45R1
    receiptless spent-selector veto and MUST re-report a spent selector as
    fresh rollback (0) via --classify-state. The shipped engine MUST refuse
    it. Both engines stay byte-identical on the exact-bound positive."""
    receipt, path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    if poison == "missing_digest":
        _write_claim(opid, {k: v for k, v in
                            _bound_claim(receipt, "rollback").items()
                            if k != "receipt_sha256"})
    elif poison == "foreign_digest":
        _write_claim(opid, {**_bound_claim(receipt, "rollback"),
                            "receipt_sha256": "a" * 64})
    else:
        _write_claim(opid, {"format": pgrec._CLAIM_FORMAT,
                            "note": "foreign"})

    state_argv = ["--phase", "reconcile", "--classify-state",
                  str(_record_path(opid))]
    weak = _weakened_engine(tmp_path)

    # the defect, observed at runtime on the weakened copy
    assert _run_engine(weak, state_argv) == 0, (
        "the weakened control no longer reproduces false-fresh")
    # the shipped engine refuses it, deterministically
    assert _run_engine(CLI, state_argv) == 4
    # the durable world is unchanged by either classification
    assert _load_record(opid)["state"] == "PROMOTED"
    assert len(list(_transitions().glob("*.claim"))) == 1


def test_weakened_and_shipped_engines_agree_on_every_positive_row(
        bridge, tmp_path, monkeypatch):
    """The negative control weakens ONLY the receiptless spent-selector veto:
    every exact-bound positive and the absent-selector fresh row classify
    identically on both engines (0 fresh / 5 preintent / 6 resume)."""
    weak = _weakened_engine(tmp_path)
    rows = []
    for transition in ("rollback", "finalize"):
        receipt, rpath, _inv, _sha = _promoted(
            bridge, tmp_path, monkeypatch, name=f"pos-{transition}.json")
        _write_claim(receipt["operation_id"], _bound_claim(receipt, transition))
        rows.append(("exact-bound " + transition, rpath))
    _r3, rpath3, _i, _s = _promoted(bridge, tmp_path, monkeypatch,
                                    name="pos-absent.json")
    rows.append(("absent", rpath3))

    for name, rpath in rows:
        argv = ["--phase", "reconcile", "--classify-rollback", str(rpath),
                "--transition-dir", str(_transitions())]
        assert _run_engine(weak, argv) == _run_engine(CLI, argv), (
            f"positive row {name} diverged")
    # the absent row is fresh on BOTH engines
    assert _run_engine(CLI, [
        "--phase", "reconcile", "--classify-rollback", str(rows[-1][1]),
        "--transition-dir", str(_transitions())]) == 0


# --------------------------------------------------------------------- #
# R45: reconciliation agrees with the shell classification
# --------------------------------------------------------------------- #

def test_reconcile_reports_unreconciled_for_a_spent_selector(
        bridge, tmp_path, monkeypatch):
    receipt, rpath, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, {**_bound_claim(receipt, "rollback"),
                        "receipt_sha256": "a" * 64})

    bridge.reset()
    before = _census(tmp_path)
    out = tmp_path / "governed-recovery" / "reconcile.json"
    result = recovery_cli.run_cli(
        ["--phase", "reconcile", "--receipt-in", str(rpath),
         "--inventory", str(inv), "--inventory-sha", str(sha),
         "--db", pgrec.DB, "--user", pgrec.USER,
         "--container", pgrec.CONTAINER, "--receipt-out", str(out)],
        write_root=str(tmp_path / "governed-recovery"),
        env_extra={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=60)
    assert result.returncode == 1, result.stderr
    decision = json.loads(out.read_text(encoding="utf-8"))
    assert decision["verdict"] == "unreconciled"
    assert decision["claim_state"] == "unbound_or_mismatched"
    assert "never be reported as fresh" in decision["error"]
    # reconciliation never mutates the durable selector world; its only
    # artifact is its own decision receipt
    after = _census(tmp_path)
    assert after.pop(str(out.relative_to(tmp_path))) is not None
    assert after == before
    assert bridge.dropped == [] and bridge.renamed == []
    assert bridge.staged == [] and bridge.docker == []


def test_denied_fresh_cli_execution_leaves_zero_durable_side_effects(
        bridge, tmp_path, monkeypatch):
    """A denied classification consumes nothing: the real CLI refuses the
    fresh-retry execution, no container surface is touched, and the durable
    record, receipts and existing claim are byte-identical."""
    receipt, receipt_path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    _write_claim(opid, {**_bound_claim(receipt, "rollback"),
                        "receipt_sha256": "a" * 64})

    bridge.reset()
    before = _census(tmp_path)
    out = tmp_path / "governed-recovery" / "denied.json"
    result = recovery_cli.run_cli(
        ["--phase", "rollback", "--receipt-in", str(receipt_path),
         "--inventory", str(inv), "--inventory-sha", str(sha),
         "--db", pgrec.DB, "--user", pgrec.USER,
         "--container", pgrec.CONTAINER, "--receipt-out", str(out)],
        write_root=str(tmp_path / "governed-recovery"),
        env_extra={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=60)
    assert result.returncode == 1, result.stderr
    assert "already claimed" in result.stderr
    assert bridge.dropped == [] and bridge.renamed == []
    assert bridge.staged == [] and bridge.docker == []
    after = _census(tmp_path)
    assert after.pop(str(out.relative_to(tmp_path))) is not None, (
        "the refusal receipt is the only permitted artifact")
    assert after == before
    assert _load_record(opid)["state"] == "PROMOTED"
    assert len(list(_transitions().glob("*.claim"))) == 1
