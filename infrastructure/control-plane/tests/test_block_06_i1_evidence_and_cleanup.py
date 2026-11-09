"""B6-I1 evidence proofs: inventory equality, uniqueness, manifest and cleanup."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I1_"
TESTS = ROOT / "infrastructure/control-plane/tests"


def load(name: str) -> dict:
    return json.loads((DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def collected() -> list[str]:
    modules = sorted(TESTS.glob("test_block_06_i1_*.py"))
    proc = subprocess.run([sys.executable, "-m", "pytest", *map(str, modules),
                           "--collect-only", "-q", "-p", "no:cacheprovider"],
                          capture_output=True, text=True, cwd=str(ROOT))
    return [line.strip() for line in proc.stdout.splitlines()
            if line.startswith("infrastructure/") and "::" in line]


def test_inventory_equals_collection() -> None:
    registry = load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    nodes = collected()
    assert len(nodes) == registry["inventory"]["expected_nodes"] == 42
    modules = {node.split("::")[0] for node in nodes}
    assert modules == set(registry["inventory"]["modules"])


def test_node_names_unique_and_orphan_free() -> None:
    nodes = collected()
    assert len(nodes) == len(set(nodes))
    registry = load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    for row in registry["requirements"]:
        assert (TESTS / row["proved_by"]).exists(), row["proved_by"]


def test_manifest_hashes_recompute() -> None:
    manifest = load("MANIFEST_v1.0.json")
    assert manifest["totals"]["artifacts"] == len(manifest["artifacts"]) >= 6
    for row in manifest["artifacts"] + manifest["code"]:
        data = (ROOT / row["path"]).read_bytes()
        assert row["sha256"] == hashlib.sha256(data).hexdigest(), row["path"]
        assert row["bytes"] == len(data)


def test_cleanup_no_scratch_residue() -> None:
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain",
                             "--untracked-files=all"], capture_output=True, text=True).stdout
    assert status.strip() == ""
    assert list(ROOT.glob(".b6i1-*")) == []
