"""Shared read-only helpers for the B6-I0 suites.

Not a test module: it holds loading, scratch-copy and git helpers so each governed node stays
short. Nothing here mutates the repository.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "oce-golden-system"
SCRIPTS = ROOT / "infrastructure" / "control-plane" / "scripts"
EVIDENCE = ROOT / "infrastructure" / "control-plane" / "evidence"
TESTS = ROOT / "infrastructure" / "control-plane" / "tests"

sys.path.insert(0, str(SCRIPTS))
import block_06_i0_validate as V  # noqa: E402  (path-based import of the validator)

BASE_SHA = "5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6"
P0_SHA = "e2aa8ac71dc9f0de4287fbcaa8a17ff127d5356f"
I0_MODULES = (
    "test_block_06_i0_stage_contract.py",
    "test_block_06_i0_decisions_and_api.py",
    "test_block_06_i0_compat_and_failures.py",
    "test_block_06_i0_authority_and_boundary.py",
    "test_block_06_i0_book5_regression.py",
    "test_block_06_i0_reproducibility_and_ci.py",
)
SCRIPTS_I0 = (
    "block_06_i0_generate.py",
    "block_06_i0_validate.py",
    "block_06_i0_mutation_battery.py",
    "block_06_i0_gate.py",
)


def load(name: str):
    return json.loads((DOCS / f"OCE_BLOCK_06_I0_{name}_v1.0.json").read_text(encoding="utf-8"))


def p0(name: str):
    return json.loads((DOCS / f"OCE_BLOCK_06_P0_{name}").read_text(encoding="utf-8"))


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def validate(root=None) -> dict:
    return V.run(pathlib.Path(root) if root else ROOT)


def failed_checks(root=None) -> set[str]:
    return {f["check"] for f in validate(root)["failure_detail"]}


def normalize(root: pathlib.Path) -> pathlib.Path:
    """Reconstruct canonical LF bytes: a Windows checkout materialises CRLF, a Linux one does not."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".md", ".txt"}:
            raw = path.read_bytes()
            if b"\r\n" in raw:
                path.write_bytes(raw.replace(b"\r\n", b"\n"))
    return root


def scratch_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A self-contained copy the validator can read without touching the repository."""
    root = tmp_path / "scratch"
    shutil.copytree(DOCS, root / "docs" / "oce-golden-system")
    shutil.copytree(EVIDENCE, root / "infrastructure" / "control-plane" / "evidence")
    shutil.copytree(TESTS, root / "infrastructure" / "control-plane" / "tests")
    return normalize(root)


def artifact_path(name: str) -> pathlib.Path:
    return DOCS / f"OCE_BLOCK_06_I0_{name}_v1.0.json"


def write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def changed_since(base: str) -> list[str]:
    proc = git("diff", "--name-only", base)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def pytest_paths() -> list[str]:
    return [str(TESTS / name) for name in I0_MODULES]


def stage_mode() -> str:
    """Resolved stage mode: "later" when a committed B6-I1 identity is present, else "i0"."""
    try:
        return V.stage_scope.resolve(ROOT, "auto")["mode"]
    except Exception:
        return "i0"


def stage_scope_identity() -> dict:
    return V.stage_scope.resolve(ROOT, "auto")
