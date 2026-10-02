#!/usr/bin/env python3
"""B4-CXR7U9R47S1 - the `docker cp` operand boundary is checked BEFORE use.

Sonar's "Command Argument Injection via faulty LLM-supplied CLI arguments"
finding on `pg-recovery.py` names the `docker cp` call. The mechanism it
describes is real even though no exploit was demonstrated:

    subprocess.run(["docker", "cp", archive_path, f"{container}:{remote}"])

`docker cp` reads its two operands POSITIONALLY. docker's own CLI parses a
leading '-' on an operand as a FLAG. So an operand that arrives from a command
line can change what the command DOES, not only which file it names. Before
this repair the container reference reached the argv with no check at all, and
an admitted archive path was checked for root containment but not for the flag
shape.

These proofs establish the repaired contract:

  * a container reference that docker would read as a flag is refused, and the
    refusal happens BEFORE the container is contacted at all;
  * an admitted archive path that docker would read as a flag is refused the
    same way;
  * ordinary references and paths still produce exactly the same command, and
    the destination directory is still created by the container first.

The suite deliberately asserts the *absence of subprocess calls*, because the
defect is not "the wrong argument is passed" -- it is "the argument is
interpreted as something other than an operand".
"""
import pytest

from recovery_cli import CLI, load_engine

pgrec = load_engine()

CONTAINER = pgrec.CONTAINER


class _Done:
    def __init__(self, rc=0, out=b"", err=b""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


@pytest.fixture()
def spy(monkeypatch):
    """Record every exec/run the engine attempts; never touch a container."""
    calls = []

    def fake_exec(container, cmd, *a, **kw):
        calls.append(("exec", container, list(cmd)))
        return _Done(out=b"/tmp/tmp.private123\n")

    def fake_run(cmd, *a, **kw):
        calls.append(("run", list(cmd)))
        return _Done()

    monkeypatch.setattr(pgrec, "docker_exec", fake_exec)
    monkeypatch.setattr(pgrec.subprocess, "run", fake_run)
    return calls


@pytest.mark.parametrize("hostile", [
    "--help",
    "-v",
    "--version",
    "-",
    "",
    "oce pg",
    "oce/pg",
    None,
    7,
])
def test_container_reference_that_docker_could_read_as_a_flag_is_refused(
        hostile, spy):
    """The reference is refused, and NOTHING is asked of the container."""
    with pytest.raises(RuntimeError, match="container reference"):
        pgrec.clone_archive_into_container(hostile, "backup.dump")
    assert spy == [], (
        "a refused container reference must not reach the container or a "
        "command line; observed calls: %r" % (spy,))


@pytest.mark.parametrize("hostile", [
    "-backup.dump",
    "--output=/tmp/elsewhere",
    "-",
    "",
    None,
])
def test_archive_operand_that_docker_could_read_as_a_flag_is_refused(
        hostile, spy):
    """Containment approval does not make a flag-shaped path an operand."""
    with pytest.raises(RuntimeError, match="could be read as a flag"):
        pgrec.clone_archive_into_container(CONTAINER, hostile)
    assert spy == [], (
        "a refused path must not reach the container or a command line; "
        "observed calls: %r" % (spy,))


def test_ordinary_reference_and_path_produce_the_same_command(spy):
    """Positive control: the repair does not change legitimate behaviour."""
    remote = pgrec.clone_archive_into_container(CONTAINER, "backup.dump")

    assert remote == "/tmp/tmp.private123/archive.dump", remote
    assert spy[0] == ("exec", CONTAINER, ["mktemp", "-d"]), (
        "the container still creates the destination directory itself, first")
    assert ("run", ["docker", "cp", "backup.dump",
                    CONTAINER + ":/tmp/tmp.private123/archive.dump"]) in spy, spy


def test_a_dotted_or_underscored_reference_is_still_accepted(spy):
    """The token shape is the one docker itself accepts, not a narrower one."""
    assert pgrec._validated_container_ref("a") == "a"
    assert pgrec._validated_container_ref("oce-pg_1.2") == "oce-pg_1.2"
    pgrec.clone_archive_into_container("oce-pg_1.2", "/var/backups/b.dump")
    assert ("run", ["docker", "cp", "/var/backups/b.dump",
                    "oce-pg_1.2:/tmp/tmp.private123/archive.dump"]) in spy


def test_validators_are_the_only_door_before_the_subprocess(spy):
    """A source-level proof of ordering, not just of the observable calls.

    The refusal must be structural: the validation calls have to appear before
    the first `docker_exec`/`subprocess.run` in the function body, so a later
    edit cannot reintroduce a pre-validation call without this failing.
    """
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(
        pgrec.clone_archive_into_container))
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name)
             and n.func.id in ("_validated_container_ref",
                               "_validated_cp_operand",
                               "docker_exec")]
    order = [n.func.id for n in calls]
    assert order[:2] == ["_validated_container_ref", "_validated_cp_operand"], order
    assert "docker_exec" in order[2:], order


def test_the_engine_under_test_is_the_shipped_engine():
    """No weakened copy: this proof runs against the file CI ships."""
    import os
    assert os.path.realpath(pgrec.__file__) == os.path.realpath(str(CLI))


def test_the_choke_point_itself_refuses_a_flag_shaped_reference(monkeypatch):
    """`docker_exec` is where every container command passes through, so the
    repair belongs there too -- not only at one call site."""
    seen = []

    def fake_run(cmd, *a, **kw):
        seen.append(list(cmd))
        return _Done()

    monkeypatch.setattr(pgrec.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="container reference"):
        pgrec.docker_exec("--help", ["mktemp", "-d"])
    assert seen == [], (
        "no argv may be built from a refused reference; observed: %r" % (seen,))

    pgrec.docker_exec(CONTAINER, ["true"])
    assert seen == [["docker", "exec", "-i", CONTAINER, "true"]], seen


def test_every_docker_argv_in_the_module_is_built_where_it_is_validated():
    """A completeness proof: the module builds docker argv in exactly two
    places, and each of them validates its operands first. A third unguarded
    construction would fail here."""
    import ast

    source = ast.parse(open(str(CLI), encoding="utf-8").read())
    builders = {}
    for node in ast.walk(source):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"
                and node.args
                and isinstance(node.args[0], (ast.List, ast.BinOp))):
            argv = ast.unparse(node.args[0])
            if "docker" not in argv:
                continue
            enclosing = None
            for fn in ast.walk(source):
                if (isinstance(fn, ast.FunctionDef)
                        and fn.lineno <= node.lineno <= fn.end_lineno):
                    enclosing = fn.name
            builders.setdefault(enclosing, []).append(node.lineno)

    assert set(builders) == {"docker_exec", "clone_archive_into_container"}, builders
    for name in builders:
        fn = next(n for n in ast.walk(source)
                  if isinstance(n, ast.FunctionDef) and n.name == name)
        validated = {c.func.id for c in ast.walk(fn)
                     if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Name)
                     and c.func.id in ("_validated_container_ref",
                                       "_validated_cp_operand")}
        assert validated, (
            "%s builds a docker argv but validates no operand" % name)
