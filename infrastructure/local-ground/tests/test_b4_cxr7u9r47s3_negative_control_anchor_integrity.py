"""B4-CXR7U9R47S3: the negative controls must keep weakening something.

Failure mechanism this suite exists to prevent
-----------------------------------------------
Several proof suites in this tree build a deliberately weakened copy of the
recovery engine by rewriting its *text*: a control replaces an anchor in the
shipped source and runs the result. That coupling is invisible in review and
catastrophic when it drifts. `str.replace` returns the subject unchanged when
the anchor no longer matches, so an engine edit that reformats a line silently
converts a negative control into a run of the SHIPPED engine -- the control
still "passes", and now proves nothing at all.

That is not hypothetical: R47S2 restated `_ExecutionLock.__exit__` with a
guarded release, moving `os.close(self.fd)` from twelve spaces to sixteen. The
R43 post-unlock unlink control anchored on exactly that text and became a
no-op; the only symptom was a barrier timeout in a POSIX-only test, on Linux
CI, several rungs later.

Two defences are asserted here, both platform-independent:

1. Every text anchor used anywhere in this tree still addresses the file it
   was written for. Drift is caught on every platform, not only where the
   gated control happens to execute.
2. A stale anchor raises. The rewrite must fail at the anchor rather than
   quietly produce an unmodified engine.

The R43 control itself stays platform-gated: proving a unlink race needs
POSIX. What is proven here is that the control is still wired to weaken the
engine at all.
"""

import ast
import os
import py_compile

import pytest

TESTS = os.path.dirname(os.path.abspath(__file__))
LOCAL_GROUND = os.path.dirname(TESTS)
SCRIPTS = os.path.join(LOCAL_GROUND, "scripts")
ENGINE = os.path.join(SCRIPTS, "pg-recovery.py")

# Sources a negative control may legitimately rewrite. Anchored on the SHELL
# scripts too: those suites weaken a bridge or a script, not the engine.
_TARGET_RELATIVE = (
    "scripts/pg-recovery.py",
    "scripts/restore.sh",
    "scripts/backup.sh",
    "scripts/run-validation.sh",
)


def _engine_source():
    with open(ENGINE, encoding="utf-8") as stream:
        return stream.read()


def _target_texts():
    texts = {}
    for rel in _TARGET_RELATIVE:
        path = os.path.join(LOCAL_GROUND, *rel.split("/"))
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as stream:
                texts[rel] = stream.read()
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(TESTS, name)
        with open(path, encoding="utf-8") as stream:
            source = stream.read()
        texts["tests/" + name] = source
        # Bridge engines are assembled into module-level `*_SOURCE` constants;
        # a control that rewrites a bridge anchors against that value.
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if "SOURCE" not in target.id.upper():
                    continue
                if (isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)):
                    texts["const:%s:%s" % (name, target.id)] = node.value.value
    return texts


def _string_anchors():
    """Every text anchor a negative control rewrites against.

    Two shapes count, and the second one is not optional. Anchors written
    inline as the subject of a `.replace(...)` are easy to see; anchors hoisted
    into a named module constant are better style and *invisible* to a scan that
    only looks at call arguments. R47S3 hoisted the R43 anchor into
    `_POST_UNLOCK_ANCHOR`, which at first made this scan blind to the very
    control it exists to protect. Both shapes are collected.
    """
    found = []
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(TESTS, name)
        with open(path, encoding="utf-8") as stream:
            tree = ast.parse(stream.read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "replace"):
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            subject = node.args[0].value
            if isinstance(subject, str) and len(subject) >= 12:
                found.append((name, node.lineno, subject, "inline"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if "ANCHOR" not in target.id.upper():
                    continue
                if (isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                        and len(node.value.value) >= 12):
                    found.append((name, node.lineno, node.value.value, "named"))
    return found


def test_the_suite_actually_contains_text_anchored_negative_controls():
    """Guard the guard: an empty scan would make the next proof vacuous."""
    anchors = _string_anchors()
    assert len(anchors) >= 15, anchors
    engine = _engine_source()
    # At least one control must really be rewriting the shipped engine, or the
    # integrity scan below is only ever exercising the shell/bridge targets.
    engine_anchored = [a for a in anchors if a[2] in engine]
    assert engine_anchored, anchors
    # And the R43 control's anchor must be reachable by name, not only inline.
    named = [a for a in anchors if a[3] == "named"]
    assert any("self.fd" in a[2] for a in named), named


def test_every_negative_control_anchor_still_addresses_its_target():
    """No control may be silently weakened into a copy of the shipped code."""
    texts = _target_texts()
    assert len(texts) >= 10, sorted(texts)
    unresolved = []
    for name, lineno, anchor, kind in _string_anchors():
        if not any(anchor in text for text in texts.values()):
            unresolved.append("%s:%d (%s) %r" % (name, lineno, kind,
                                                 anchor[:70]))
    assert not unresolved, (
        "negative-control anchors that no longer match any source they may "
        "rewrite -- these controls now run unmodified code:\n  "
        + "\n  ".join(unresolved))


def test_a_stale_anchor_raises_instead_of_producing_an_unweakened_engine():
    """The failure mechanism itself: `replace` alone is silent, so guard it."""
    import test_b4_cxr7u9r43_lock_inode_rollback_resume as r43

    stale = "import tempfile\n\n\ndef unrelated():\n    pass\n"
    # Before S3 this returned `stale` unchanged -- the silent no-op. The whole
    # point of the guard is that the refusal is now loud and names the cause.
    with pytest.raises(AssertionError) as caught:
        r43._post_unlock_unlink_transform(stale)
    assert "no longer matches the engine text" in str(caught.value)


def test_the_post_unlock_control_still_weakens_the_shipped_engine():
    """The R43 control must rewrite the engine, and the rewrite must be valid."""
    import test_b4_cxr7u9r43_lock_inode_rollback_resume as r43

    source = _engine_source()
    assert r43._POST_UNLOCK_ANCHOR in source, (
        "the post-unlink control's anchor has drifted from the engine")

    weakened = r43._post_unlock_unlink_transform(source)
    assert weakened != source
    assert "import time" in weakened
    # The weakening is a post-unlock, post-close unlink of the coordinate.
    assert weakened.count("R43_WEAK_COORDINATE") == 1
    assert weakened.count("os.unlink(self.path)") == 1
    body = weakened.split("def __exit__", 1)[1][:1400]
    assert body.find("os.close(self.fd)") < body.find("R43_WEAK_COORDINATE")
    assert body.find("R43_WEAK_COORDINATE") < body.find("os.unlink(self.path)")
    assert body.find("os.unlink(self.path)") < body.find("return False")

    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as raw:
        target = Path(raw) / "weakened-pg-recovery.py"
        target.write_text(weakened, encoding="utf-8")
        py_compile.compile(str(target), cfile=str(Path(raw) / "w.pyc"),
                           doraise=True)


def test_execution_lock_exit_returns_false_on_every_path():
    """The invariant S2 restated, pinned independently of its shape."""
    fn = next(
        node for node in ast.walk(ast.parse(_engine_source()))
        if isinstance(node, ast.FunctionDef)
        and node.name == "__exit__"
        and getattr(node, "lineno", 0) > 2000)
    returns = [node for node in ast.walk(fn) if isinstance(node, ast.Return)]
    assert len(returns) == 1, ast.unparse(fn)
    assert isinstance(returns[0].value, ast.Constant)
    assert returns[0].value.value is False, ast.unparse(fn)


def test_the_engine_still_refuses_a_container_reference_that_is_a_flag():
    """S1's repair, pinned so a later refactor cannot reopen the channel."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("r47s3_engine", ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    for hostile in ("--help", "-i", "--privileged"):
        with pytest.raises(RuntimeError):
            engine._validated_container_ref(hostile)
    for legitimate in ("oce-pg", "postgres_1", "pg.recovery-2"):
        assert engine._validated_container_ref(legitimate) == legitimate