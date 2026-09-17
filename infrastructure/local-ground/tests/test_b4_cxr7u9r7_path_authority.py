#!/usr/bin/env python3
"""B4-CXR7U9R7 - truthful filesystem path authority proofs.

Proves the authority model claimed for every path input:

* independent-gate.py _validated_subprocess_path enforces REAL
  containment inside the approved evidence root (traversal, absolute
  escape, symlink substitution, prefix collisions all rejected);
* pg-recovery.py's _validated_open_path enforces the containment
  discipline both engines use (pg-verify.py reuses it, and the suite
  proves they are the same function): no symlink indirection (realpath
  must equal abspath), the canonical path must sit inside an approved
  root, and the target must be an existing regular file; denial has
  zero durable side effects (pure predicates).
"""
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(SCRIPTS / filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load("u9r7_gate", "independent-gate.py")
pgrec = _load("u9r7_pgrec", "pg-recovery.py")
pgver = _load("u9r7_pgver", "pg-verify.py")


def _symlink_creatable() -> bool:
    """Probe once whether THIS platform/privilege set can create symlinks.

    Windows without SeCreateSymbolicLinkPrivilege (or Developer Mode)
    raises OSError WinError 1314; Linux CI (where these adversarial
    proofs are mandatory) always can. This is the project's only symlink
    capability probe: the control-plane suites call os.symlink at the
    point of use and skip on OSError. The skip is TRUTHFUL - it names the
    missing capability, never hides a failure of the code under test (the
    containment logic itself is exercised on every platform through the
    traversal/absolute/prefix-collision cases).
    """
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            target = os.path.join(td, "t")
            os.mkdir(target)
            link = os.path.join(td, "l")
            os.symlink(target, link)
            os.unlink(link)
        return True
    except (OSError, NotImplementedError):
        return False


SYMLINKS_OK = _symlink_creatable()
needs_symlink = pytest.mark.skipif(
    not SYMLINKS_OK,
    reason="symlink creation requires privilege on this platform "
           "(WinError 1314); mandatory in CI where symlinks work")


# --------------------------------------------------------------------- #
# independent-gate containment matrix
# --------------------------------------------------------------------- #

class TestGateOpsRootContainment:
    def test_exact_approved_root_accepted(self, tmp_path):
        ops = tmp_path / "operations"
        ops.mkdir()
        out = gate._validated_subprocess_path(str(ops), str(tmp_path))
        assert Path(out) == Path(os.path.realpath(str(ops)))

    def test_valid_descendant_accepted(self, tmp_path):
        sub = tmp_path / "operations" / "receipts"
        sub.mkdir(parents=True)
        out = gate._validated_subprocess_path(str(sub), str(tmp_path))
        assert os.path.realpath(str(sub)) == out

    def test_parent_traversal_escape_rejected(self, tmp_path):
        outside = tmp_path.parent / "outside-evidence"
        outside.mkdir(exist_ok=True)
        candidate = str(tmp_path / "operations" / ".." / ".." / "outside-evidence")
        with pytest.raises(RuntimeError, match="escapes approved root"):
            gate._validated_subprocess_path(candidate, str(tmp_path))

    def test_arbitrary_absolute_external_rejected(self, tmp_path):
        external = str(Path(os.environ.get("SYSTEMROOT", "/etc")))
        with pytest.raises(RuntimeError, match="escapes approved root"):
            gate._validated_subprocess_path(external, str(tmp_path))

    @needs_symlink
    def test_symlink_file_candidate_rejected(self, tmp_path):
        real_dir = tmp_path.parent / "real-ops-u9r7"
        real_dir.mkdir(exist_ok=True)
        link = tmp_path / "operations"
        os.symlink(str(real_dir), str(link))
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(str(link), str(tmp_path))
        finally:
            link.unlink()

    @needs_symlink
    def test_symlink_parent_directory_rejected(self, tmp_path):
        real_ev = tmp_path.parent / "real-ev-u9r7"
        real_ev.mkdir(exist_ok=True)
        (real_ev / "operations").mkdir(exist_ok=True)
        link_ev = tmp_path / "evil-link"
        os.symlink(str(real_ev), str(link_ev))
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(
                    str(link_ev / "operations"), str(tmp_path))
        finally:
            link_ev.unlink()

    def test_prefix_collision_rejected(self, tmp_path):
        evil = tmp_path.parent / (tmp_path.name + "-evil")
        evil.mkdir(exist_ok=True)
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(evil, str(tmp_path))
        finally:
            evil.rmdir()

    def test_nonexistent_path_rejected(self, tmp_path):
        with pytest.raises(RuntimeError, match="not a directory"):
            gate._validated_subprocess_path(
                str(tmp_path / "operations" / "missing"), str(tmp_path))

    def test_wrong_type_file_rejected(self, tmp_path):
        f = tmp_path / "operations-file"
        f.write_text("x")
        with pytest.raises(RuntimeError, match="not a directory"):
            gate._validated_subprocess_path(str(f), str(tmp_path))

    def test_missing_approved_root_rejected(self, tmp_path):
        with pytest.raises(RuntimeError, match="approved root"):
            gate._validated_subprocess_path(
                str(tmp_path / "operations"), str(tmp_path / "no-such-root"))

    def test_denial_has_zero_durable_side_effects(self, tmp_path):
        before = sorted(p.name for p in tmp_path.rglob("*"))
        with pytest.raises(RuntimeError):
            gate._validated_subprocess_path(
                str(tmp_path / ".." / "x"), str(tmp_path))
        after = sorted(p.name for p in tmp_path.rglob("*"))
        assert before == after


# --------------------------------------------------------------------- #
# pg-recovery / pg-verify APPROVED-ROOT CONTAINMENT (B4-CXR7U9R12)
# --------------------------------------------------------------------- #

class TestApprovedRootArtifactInputs:
    """Artifact paths are contained: the approved roots are the program
    identity (engine directory plus the engine's own var/recovery state
    directory) plus operator-declared OCE_BACKUP_ROOTS. A CLI argument
    can never approve its own containment root."""

    @pytest.fixture(autouse=True)
    def _approve_tmp_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
        self.root = tmp_path

    def test_containment_has_exactly_one_owner(self):
        """pg-verify exposes the policy it imported from pg-recovery instead of
        restating it, so the two engines cannot drift apart. (Each test load
        execs its own module object, so the check is against pg-verify's own
        import, not against this file's second load of pg-recovery.)"""
        for name in ("_approved_roots", "_validated_open_path",
                     "_validated_read_text"):
            assert getattr(pgver, name) is getattr(pgver._PG, name), (
                f"{name} must be pg-recovery's function, not a second copy")

    def test_regular_file_accepted_and_canonical(self, tmp_path):
        f = tmp_path / "inventory.json"
        f.write_text("{}")
        out = pgrec._validated_open_path(str(f))
        assert Path(out) == Path(os.path.realpath(str(f)))

    @needs_symlink
    def test_symlink_file_rejected(self, tmp_path):
        real = tmp_path.parent / "real-inv-u9r7.json"
        real.write_text("{}")
        link = tmp_path / "inventory.json"
        os.symlink(str(real), str(link))
        try:
            with pytest.raises(RuntimeError, match="symlink indirection"):
                pgrec._validated_open_path(str(link))
        finally:
            link.unlink()

    def test_missing_path_rejected(self, tmp_path):
        with pytest.raises(RuntimeError, match="not a regular file"):
            pgrec._validated_open_path(str(tmp_path / "nope.json"))

    def test_wrong_type_directory_rejected(self, tmp_path):
        d = tmp_path / "adir"
        d.mkdir()
        with pytest.raises(RuntimeError, match="not a regular file"):
            pgrec._validated_open_path(str(d))

    def test_path_outside_every_approved_root_rejected(self, tmp_path):
        f = tmp_path.parent / "outside-approved-roots.json"
        f.write_text("{}")
        try:
            with pytest.raises(RuntimeError, match="approved backup root"):
                pgrec._validated_open_path(str(f))
        finally:
            f.unlink()

    def test_empty_roots_reject_everything(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OCE_BACKUP_ROOTS", "")
        f = tmp_path / "inventory.json"
        f.write_text("{}")
        with pytest.raises(RuntimeError, match="approved backup root"):
            pgrec._validated_open_path(str(f))

    def test_cli_argument_cannot_approve_its_own_root(self, tmp_path, monkeypatch):
        # A root named in the artifact's own path (or any argv channel)
        # grants nothing: only the engine directory and OCE_BACKUP_ROOTS
        # are consulted. A rogue directory outside both is rejected even
        # when the artifact path "looks" absolute and canonical.
        rogue = tmp_path.parent / "rogue-u9r12"
        rogue.mkdir(exist_ok=True)
        f = rogue / "inventory.json"
        f.write_text("{}")
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
        with pytest.raises(RuntimeError, match="approved backup root"):
            pgrec._validated_open_path(str(f))


# --------------------------------------------------------------------- #
# pg-recovery promote: the guard that feeds the open() sink
# --------------------------------------------------------------------- #

CLI = SCRIPTS / "pg-recovery.py"
INVENTORY_DOC = ('{"format": "oce-pg-inventory-v1", "database": "oce_local",'
                 ' "table_count": 1, "tables": [{"name": "public.widgets",'
                 ' "row_count": 3, "fingerprint": "deadbeef"}]}')


class TestPromoteSinkRefusal:
    """Adjudication of the failure-level finding on `pg-recovery.py:584`
    ("Path Traversal via faulty LLM-supplied CLI arguments").

    The sink is `open(os.path.realpath(_validated_open_path(archive)), "rb")`
    in `phase_promote`, fed by the `--archive` CLI argument. These tests drive
    the SHIPPED surfaces (the real CLI, and `phase_promote` itself) rather than
    the validator alone, and prove the four conditions the disposition rests
    on: (1) approved-root authority cannot come from the artifact path, (2)
    the canonical path is contained, (3) symlink indirection is refused even
    when its target is inside an approved root, (4) denial is a pure refusal -
    no container call, no staging database, and the caller's receipt is the
    only file written anywhere.
    """

    def _inputs(self, tmp_path, monkeypatch):
        roots = tmp_path / "roots"
        roots.mkdir()
        inv = roots / "inventory.json"
        inv.write_text(INVENTORY_DOC, encoding="utf-8")
        sha = roots / "inventory.sha256"
        sha.write_text(hashlib.sha256(INVENTORY_DOC.encode()).hexdigest(),
                       encoding="utf-8")
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
        return roots, inv, sha

    def _cli(self, archive, inv, sha, receipt):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(CLI), "--phase", "promote",
             "--archive", str(archive), "--inventory", str(inv),
             "--inventory-sha", str(sha), "--receipt-out", str(receipt)],
            capture_output=True, text=True, env=env, timeout=300)

    @pytest.mark.parametrize("kind,needle", [
        ("outside-root", "outside every approved backup root"),
        ("dot-dot-traversal", "outside every approved backup root"),
        ("self-declared-root", "outside every approved backup root"),
        ("symlink-into-root", "symlink indirection"),
    ])
    def test_promote_cli_refuses_hostile_archive_without_side_effects(
            self, tmp_path, monkeypatch, kind, needle):
        roots, inv, sha = self._inputs(tmp_path, monkeypatch)
        if kind == "symlink-into-root":
            if not SYMLINKS_OK:
                pytest.skip("symlink creation requires privilege on this platform")
            target = roots / "real.dump"
            target.write_bytes(b"PGDMP")
            archive = roots / "link.dump"
            os.symlink(str(target), str(archive))
        elif kind == "outside-root":
            archive = tmp_path / "outside.dump"
            archive.write_bytes(b"PGDMP")
        elif kind == "dot-dot-traversal":
            (tmp_path / "outside.dump").write_bytes(b"PGDMP")
            archive = roots / ".." / "outside.dump"
        else:  # a directory named like a root does not become one
            rogue = tmp_path / "rogue-root"
            rogue.mkdir()
            archive = rogue / "outside.dump"
            archive.write_bytes(b"PGDMP")

        before = sorted(str(p) for p in tmp_path.rglob("*"))
        receipt = tmp_path / "promote-receipt.json"
        run = self._cli(archive, inv, sha, receipt)

        assert run.returncode == 1, (run.returncode, run.stdout, run.stderr)
        assert "BLOCKED:" in run.stderr
        assert needle in run.stderr, run.stderr
        # The refusal is recorded, and it stopped at the archive step: the
        # inventory was validated, nothing was staged, nothing was promoted.
        recorded = json.loads(receipt.read_text(encoding="utf-8"))
        assert recorded["exit_status"] == 1
        assert recorded["phases"] == ["inventory_validated"], recorded["phases"]
        assert recorded["promoted"] is False
        assert recorded["quarantine_dropped"] is False
        assert needle in recorded["error"]
        # Only the caller's receipt was written anywhere; approved content is
        # byte-identical and the refused path was never followed.
        after = sorted(str(p) for p in tmp_path.rglob("*"))
        assert set(after) - set(before) == {str(receipt)}
        link = roots / "link.dump"
        if kind == "symlink-into-root":
            assert os.path.islink(str(link))
            assert (roots / "real.dump").read_bytes() == b"PGDMP"

    def test_promote_sink_refusal_precedes_every_container_call(
            self, tmp_path, monkeypatch):
        """The same hostile archive, driven through `phase_promote` itself,
        with the container bridge instrumented: the guard must fire before any
        docker invocation exists to make."""
        roots, inv, sha = self._inputs(tmp_path, monkeypatch)
        archive = tmp_path / "outside.dump"
        archive.write_bytes(b"PGDMP")
        calls = []

        def probe(container, cmd, stdin_bytes=None, timeout=600):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(list(cmd), 3, b"", b"probe")

        monkeypatch.setattr(pgrec, "docker_exec", probe)
        monkeypatch.setattr(pgrec, "docker_exec_ok", probe)
        receipt = pgrec.phase_promote(str(archive), str(inv), str(sha),
                                     "oce_local", "oce_local_admin",
                                     "oce-local-postgresql", None)
        assert calls == [], calls
        assert receipt["exit_status"] == 1
        assert "outside every approved backup root" in receipt["error"]
        assert receipt["phases"] == ["inventory_validated"]

    def test_promote_reaches_the_container_step_for_an_approved_archive(
            self, tmp_path, monkeypatch):
        """Vacuity control for the test above: with an approved regular file in
        place of the hostile one, the same instrumentation DOES observe the
        container call, so "no call" there is a real observation."""
        roots, inv, sha = self._inputs(tmp_path, monkeypatch)
        archive = roots / "real.dump"
        archive.write_bytes(b"PGDMP")
        calls = []

        def probe(container, cmd, stdin_bytes=None, timeout=600):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(list(cmd), 3, b"", b"probe")

        monkeypatch.setattr(pgrec, "docker_exec", probe)
        monkeypatch.setattr(pgrec, "docker_exec_ok", probe)
        receipt = pgrec.phase_promote(str(archive), str(inv), str(sha),
                                     "oce_local", "oce_local_admin",
                                     "oce-local-postgresql", None)
        assert calls, "the container bridge was never reached for an approved archive"
        assert "approved backup root" not in receipt.get("error", "")
        assert "container temp directory" in receipt["error"]


class TestPromoteSinkInputsAreValidatorOutput:
    """The same finding anchors on different lines of this one flow depending
    on the window (the `open()` at :584, or `sha256_file`'s parameter sink at
    :294). Both are fed by the `--archive` argument, so the disposition rests
    on what each sink RECEIVES, not only on the guard preceding it. These
    tests observe those values during a real promote, and pin the property that
    makes the raw argument safe at the `docker cp` source as well: every
    spelling the guard admits resolves to the canonical file inside an
    approved root.
    """

    def _approved(self, tmp_path, monkeypatch):
        roots = tmp_path / "roots"
        (roots / "sub").mkdir(parents=True)
        inv = roots / "inventory.json"
        inv.write_text(INVENTORY_DOC, encoding="utf-8")
        sha = roots / "inventory.sha256"
        sha.write_text(hashlib.sha256(INVENTORY_DOC.encode()).hexdigest(),
                       encoding="utf-8")
        archive = roots / "real.dump"
        archive.write_bytes(b"PGDMP")
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
        return roots, inv, sha, archive

    def test_values_reaching_the_hash_and_copy_sinks_are_contained(
            self, tmp_path, monkeypatch):
        roots, inv, sha, archive = self._approved(tmp_path, monkeypatch)
        hashed, copied = [], []
        real_sha256 = pgrec.sha256_file

        def record_hash(path):
            hashed.append(path)
            return real_sha256(path)

        def record_copy(container, archive_path):
            copied.append(archive_path)
            return "/tmp/probe/archive.dump"

        monkeypatch.setattr(pgrec, "sha256_file", record_hash)
        monkeypatch.setattr(pgrec, "clone_archive_into_container", record_copy)
        monkeypatch.setattr(pgrec, "docker_exec",
                            lambda *a, **k: subprocess.CompletedProcess([], 3, b"", b"probe"))
        receipt = pgrec.phase_promote(str(archive), str(inv), str(sha),
                                      "oce_local", "oce_local_admin",
                                      "oce-local-postgresql", None)

        expected = os.path.realpath(str(archive))
        # sha256_file's parameter (Sonar's :294 anchor) receives the validator's
        # canonical path, never the raw CLI string.
        assert hashed == [expected], hashed
        # The `docker cp` source (:571) is the raw argument, so what matters is
        # that the guard admitted it: its realpath is the same contained file.
        assert copied, "the container copy sink was never reached"
        for value in copied:
            assert os.path.realpath(value) == expected
            assert os.path.commonpath([str(roots), os.path.realpath(value)]) == str(roots)
        assert receipt["source_archive_sha256"] == real_sha256(str(archive))

    def test_every_admitted_spelling_resolves_inside_an_approved_root(
            self, tmp_path, monkeypatch):
        roots, _, _, archive = self._approved(tmp_path, monkeypatch)
        for spelling in (str(archive), str(roots / "." / "real.dump"),
                         str(roots) + os.sep + "real.dump",
                         str(roots / "sub" / ".." / "real.dump")):
            resolved = pgrec._validated_open_path(spelling)
            assert os.path.commonpath([str(roots), resolved]) == str(roots)
            assert resolved == os.path.realpath(str(archive)), spelling
            assert os.path.samefile(resolved, str(archive)), spelling

    def test_prefix_sibling_outside_the_root_is_refused(self, tmp_path, monkeypatch):
        """The sharpest edge of canonical containment: a sibling whose name only
        shares the root's text prefix (`roots-evil` beside `roots`) is not
        contained. A startswith() containment check would admit it."""
        self._approved(tmp_path, monkeypatch)
        sibling = tmp_path / "roots-evil"
        sibling.mkdir()
        (sibling / "real.dump").write_bytes(b"PGDMP")
        with pytest.raises(RuntimeError, match="approved backup root"):
            pgrec._validated_open_path(str(sibling / "real.dump"))

    def test_sha256_file_parameter_sink_has_no_unvalidated_call_site(self):
        """`sha256_file(path)` constrains nothing by itself, so its safety is a
        property of its call sites: the engine's production call must hand it
        the validator's output. A future call site bypassing the validator
        fails here rather than silently widening the sink."""
        tree = ast.parse((SCRIPTS / "pg-recovery.py").read_text(encoding="utf-8"))
        sites = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "sha256_file"]
        assert sites, "expected at least one sha256_file call site"
        for call in sites:
            assert call.args, "sha256_file called without a path"
            inner = call.args[0]
            assert (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
                    and inner.func.id == "_validated_open_path"), ast.dump(inner)
