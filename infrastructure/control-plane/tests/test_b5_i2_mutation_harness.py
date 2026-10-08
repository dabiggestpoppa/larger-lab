"""B5-I2 reproducibility-harness integrity tests (harness has teeth).

AUTHORIZED_STAGE=B5-I2-POST-MERGE-REPRODUCIBILITY-REPAIR.

Prove the governed mutation harness
(``infrastructure/control-plane/scripts/b5_i2_mutation_battery.py``) is
itself trustworthy:

- the registry is exactly the frozen 11 unique mutations M1..M9
  (M7a/M7b/M7c), each with a declared expected discriminator;
- every patch anchor occurs exactly once in the frozen source it targets
  (fail-closed preconditions for schema operations too);
- absent / duplicated / no-op anchors are refused without touching files;
- an unexpected-green mutation fails the harness (real isolated pytest run);
- a failing clean control fails the harness (real isolated pytest run);
- a wrong (non-frozen) inventory and a skipped control fail closed;
- canonical JSON is byte-deterministic and free of machine-specific paths,
  host names, user names or timestamps;
- executing a real battery against the real repository tree cannot alter the
  caller's tracked worktree (byte-hashes + git status snapshots).

These tests use real isolated temporary trees and real pytest subprocess
invocations; source-string assertions alone are not sufficient.
"""
from __future__ import annotations

import getpass
import hashlib
import importlib.util
import json
import os
import socket
from pathlib import Path

import pytest

_HARNESS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "b5_i2_mutation_battery.py"
_spec = importlib.util.spec_from_file_location("b5_i2_mutation_battery", _HARNESS_PATH)
hb = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hb)

_MINI_OK = (
    "def test_alpha():\n"
    "    assert 1 + 1 == 2\n"
    "\n"
    "def test_beta():\n"
    '    assert "x" in "xyz"\n'
)


def _mini_source(tmp_path: Path, tests_src: str) -> Path:
    root = tmp_path / "src"
    (root / "mini" / "tests").mkdir(parents=True)
    (root / "mini" / "tests" / "test_mini.py").write_text(tests_src, encoding="utf-8")
    (root / "mini" / "the_mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    return root


def _mini_mutations() -> list[dict]:
    return [{
        "id": "X1",
        "name": "X1-mini-weakened-assertion",
        "target": "mini/tests/test_mini.py",
        "kind": "text",
        "description": "mini assertion weakened; must discriminate",
        "anchor": "assert 1 + 1 == 2",
        "replacement": "assert 1 + 1 == 3",
        "expected": ["mini/tests/test_mini.py::test_alpha"],
        "output_pattern": None,
    }]


def _run_mini(src: Path, *, expected: int, mutations: list[dict]) -> dict:
    return hb.execute_battery(
        source_root=src,
        copy_paths=["mini"],
        test_relpath="mini/tests/test_mini.py",
        expected_node_count=expected,
        mutations=mutations,
        timeout=180,
    )


# ---------------------------------------------------------------------------
# Registry and frozen-source anchor proofs
# ---------------------------------------------------------------------------


def test_registry_is_exactly_the_frozen_eleven_unique_mutations():
    ids = [m["id"] for m in hb.MUTATIONS]
    assert len(ids) == 11
    assert len(set(ids)) == 11
    assert set(ids) == {"M1", "M2", "M3", "M4", "M5", "M6",
                        "M7a", "M7b", "M7c", "M8", "M9"}
    names = [m["name"] for m in hb.MUTATIONS]
    assert len(set(names)) == 11
    assert {m["target"] for m in hb.MUTATIONS} <= {hb.PACK, hb.MODULE, hb.SCHEMA}


def test_every_mutation_declares_an_expected_discriminator():
    for m in hb.MUTATIONS:
        assert m["expected"], f"{m['id']} has no expected discriminator"
        for node in m["expected"]:
            assert node.startswith(hb.TEST_FILE + "::"), (m["id"], node)
            assert node.count("::") == 2, (m["id"], node)
        if m["kind"] == "text":
            assert m["anchor"], m["id"]
            assert m["replacement"] != m["anchor"], f"{m['id']} is a no-op by construction"
        elif m["kind"] == "schema":
            assert m["op"]["op"] in {"add_prop", "remove_prop", "rename_prop"}, m["id"]
        else:
            pytest.fail(f"{m['id']}: unknown mutation kind {m['kind']!r}")


def test_every_patch_anchor_occurs_exactly_once_in_the_frozen_source():
    root = hb.resolve_repo_root()
    for m in hb.MUTATIONS:
        target = root / m["target"]
        assert target.is_file(), f"frozen target missing: {m['target']}"
        if m["kind"] == "text":
            text, _ = hb._read_norm(target)
            assert text.count(m["anchor"]) == 1, (
                f"{m['id']}: anchor occurs {text.count(m['anchor'])}x "
                f"in {m['target']} (must be exactly 1)")
        else:
            doc = json.loads(target.read_text(encoding="utf-8"))
            props = doc["properties"]
            op = m["op"]
            if op["op"] == "add_prop":
                assert op["key"] not in props, m["id"]
                assert m["anchor"] == op["key"]
            elif op["op"] == "remove_prop":
                assert op["key"] in props, m["id"]
                assert m["anchor"] == op["key"]
            else:
                assert op["old"] in props and op["new"] not in props, m["id"]
                assert m["anchor"] == op["old"]


def test_repo_root_resolution_is_deterministic_from_the_harness_location():
    root = hb.resolve_repo_root()
    assert (root / ".git").exists()
    assert (root / hb.CONTROL_PLANE_DIR).is_dir()
    assert hb.resolve_repo_root() == root


# ---------------------------------------------------------------------------
# Fail-closed application on isolated temporary trees (no pytest needed)
# ---------------------------------------------------------------------------


def test_absent_anchor_fails_closed(tmp_path):
    tree = tmp_path / "t"
    tree.mkdir()
    target = tree / "mod.py"
    original = "value = 1\n"
    target.write_text(original, encoding="utf-8")
    mutation = {"id": "X", "kind": "text", "target": "mod.py",
                "anchor": "not-present-anywhere", "replacement": "something"}
    with pytest.raises(hb.MutationError, match="anchor occurs 0x"):
        hb.apply_mutation(tree, mutation)
    assert target.read_text(encoding="utf-8") == original


def test_duplicated_anchor_fails_closed(tmp_path):
    tree = tmp_path / "t"
    tree.mkdir()
    target = tree / "mod.py"
    original = "value = 1\nvalue = 1\n"
    target.write_text(original, encoding="utf-8")
    mutation = {"id": "X", "kind": "text", "target": "mod.py",
                "anchor": "value = 1", "replacement": "value = 2"}
    with pytest.raises(hb.MutationError, match="anchor occurs 2x"):
        hb.apply_mutation(tree, mutation)
    assert target.read_text(encoding="utf-8") == original


def test_mutation_that_changes_nothing_is_refused(tmp_path):
    tree = tmp_path / "t"
    tree.mkdir()
    target = tree / "mod.py"
    original = "value = 1\n"
    target.write_text(original, encoding="utf-8")
    # a) replacement identical to anchor
    with pytest.raises(hb.MutationError, match="no-op"):
        hb.apply_mutation(tree, {"id": "X", "kind": "text", "target": "mod.py",
                                 "anchor": "value = 1", "replacement": "value = 1"})
    # b) schema operation that would leave the document unchanged
    schema = tree / "s.json"
    schema.write_text(json.dumps({"properties": {"lease": {"type": "object"}}}),
                      encoding="utf-8")
    with pytest.raises(hb.MutationError, match="already present"):
        hb.apply_mutation(tree, {"id": "Y", "kind": "schema", "target": "s.json",
                                 "op": {"op": "add_prop", "key": "lease"},
                                 "anchor": "lease"})
    assert schema.read_text(encoding="utf-8").endswith("}")


def test_missing_target_fails_closed(tmp_path):
    tree = tmp_path / "t"
    tree.mkdir()
    with pytest.raises(hb.MutationError, match="target missing"):
        hb.apply_mutation(tree, {"id": "X", "kind": "text", "target": "ghost.py",
                                 "anchor": "a", "replacement": "b"})


# ---------------------------------------------------------------------------
# Real isolated pytest batteries: the harness fails when it must
# ---------------------------------------------------------------------------


def test_unexpected_green_mutation_fails_the_harness(tmp_path):
    src = _mini_source(tmp_path, _MINI_OK)
    mutations = [{
        "id": "G1", "name": "G1-mini-still-green", "target": "mini/tests/test_mini.py",
        "kind": "text", "description": "changes content but tests still pass",
        "anchor": 'assert "x" in "xyz"', "replacement": 'assert "xy" in "xyz"',
        "expected": ["mini/tests/test_mini.py::test_beta"], "output_pattern": None,
    }]
    with pytest.raises(hb.HarnessError, match="did not discriminate"):
        _run_mini(src, expected=2, mutations=mutations)


def test_failing_clean_control_fails_the_harness(tmp_path):
    src = _mini_source(
        tmp_path,
        "def test_alpha():\n    assert False\n\n"
        "def test_beta():\n    assert True\n",
    )
    with pytest.raises(hb.HarnessError, match="control proof"):
        _run_mini(src, expected=2, mutations=_mini_mutations())


def test_wrong_inventory_fails_closed_before_execution(tmp_path):
    src = _mini_source(tmp_path, _MINI_OK + "\ndef test_gamma():\n    assert True\n")
    with pytest.raises(hb.HarnessError, match="inventory"):
        _run_mini(src, expected=2, mutations=_mini_mutations())


def test_skipped_control_fails_the_zero_skip_law(tmp_path):
    src = _mini_source(
        tmp_path,
        "import pytest\n\n"
        "def test_alpha():\n    assert True\n\n"
        "@pytest.mark.skip(reason='must not pass the control gate')\n"
        "def test_beta():\n    assert False\n",
    )
    with pytest.raises(hb.HarnessError, match="skipped"):
        _run_mini(src, expected=2, mutations=_mini_mutations())


# ---------------------------------------------------------------------------
# Canonical JSON: deterministic, machine-free; isolation of temp state
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mini_battery(tmp_path_factory):
    """One real, successful mini battery shared by serialization tests."""
    tmp = tmp_path_factory.mktemp("b5i2-mini")
    src = _mini_source(tmp, _MINI_OK)
    target = src / "mini" / "tests" / "test_mini.py"
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    core = _run_mini(src, expected=2, mutations=_mini_mutations())
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    return {"src": src, "before": before, "after": after, "core": core}


def test_mini_battery_discriminates_and_restores_source_bytes(mini_battery):
    core = mini_battery["core"]
    assert mini_battery["before"] == mini_battery["after"]
    assert len(core["baseline_nodes"]) == 2
    assert core["baseline_nodes"] == sorted(core["baseline_nodes"])
    outcomes = core["outcomes"]
    assert len(outcomes) == 1
    assert outcomes[0]["outcome"] == "DISCRIMINATED"
    assert outcomes[0]["matched_by"] == "node"


def test_canonical_json_is_deterministic_and_machine_free(mini_battery):
    core = mini_battery["core"]
    doc = {
        "schema": hb.SCHEMA_ID,
        "schema_version": hb.SCHEMA_VERSION,
        "baseline": {"nodes": core["baseline_nodes"]},
        "mutations": [
            {k: o[k] for k in ("id", "name", "target", "description", "outcome")}
            for o in core["outcomes"]
        ],
    }
    text_a = hb.canonical_json(doc)
    # Re-serialize a dict built with a DIFFERENT key insertion order:
    reordered = dict(reversed(list(doc.items())))
    text_b = hb.canonical_json(reordered)
    assert text_a == text_b
    assert text_a == hb.canonical_json(doc)
    assert text_a.endswith("\n")
    assert json.loads(text_a) == doc

    # No machine-specific or nondeterministic data may ever be serialized.
    strays = [str(mini_battery["src"].parent),  # the temp dir root
              "b5i2-repro-",
              "C:\\", "C:/", "/home/", "/tmp/",
              str(Path.home()),
              os.environ.get("USERPROFILE", "\x00"),
              os.environ.get("HOME", "\x00"),
              socket.gethostname(),
              getpass.getuser()]
    for stray in strays:
        if stray:
            assert stray not in text_a, f"machine-specific data serialized: {stray!r}"
    assert not any(k in json.loads(text_a) for k in
                   ("timestamp", "duration", "hostname", "started_at", "finished_at"))


def test_harness_source_declares_no_machine_specific_paths():
    source = _HARNESS_PATH.read_text(encoding="utf-8")
    for stray in ("C:\\", "/home/", str(Path.home()), "/c/tmp", "C:/tmp",
                  os.environ.get("USERPROFILE", "\x00")):
        if stray:
            assert stray not in source, f"machine-specific path in harness source: {stray!r}"


# ---------------------------------------------------------------------------
# The real battery cannot alter the caller's tracked worktree
# ---------------------------------------------------------------------------


def test_real_battery_cannot_alter_the_tracked_worktree():
    root = hb.resolve_repo_root()
    targets = [root / hb.PACK, root / hb.MODULE, root / hb.SCHEMA, root / hb.TEST_FILE]
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in targets}
    core = hb.execute_battery(
        source_root=root,
        copy_paths=[hb.CONTROL_PLANE_DIR],
        test_relpath=hb.TEST_FILE,
        expected_node_count=hb.FROZEN_NODE_FLOOR,
        mutations=[hb.MUTATIONS[0]],  # M1: pack-only byte change, fast discriminator
        timeout=600,
    )
    after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in targets}
    assert before == after, "battery mutated the real tracked sources"
    assert core["caller_tracked_worktree_unmodified"] is True
    assert len(core["baseline_nodes"]) == hb.FROZEN_NODE_FLOOR
    assert core["outcomes"][0]["outcome"] == "DISCRIMINATED"
