"""P0-C01 — Book V 15.1 topology smoke evidence.

Asserts the frozen canon package topology exists on disk, is importable, and
that the QCAE package exposes version metadata.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import qcae

QCAE_DIR = Path(__file__).resolve().parents[2]

CANON_TOPLEVEL = [
    "core",
    "orchestration",
    "discovery",
    "intelligence",
    "audit",
    "proving",
    "quant",
    "acquisition",
    "evidence",
    "registry",
    "monitoring",
    "governance",
    "infrastructure",
    "interfaces",
]

CANON_SECOND_LEVEL = {
    "core": ["contracts", "capabilities", "lifecycle", "relationships", "decisions", "policies"],
    "orchestration": ["orchestrator", "jobs", "workers", "context", "handoffs"],
    "discovery": ["planning", "github", "curated", "ecosystems", "research", "internal"],
    "intelligence": ["repository", "comprehension", "dependencies", "archaeology", "forensics"],
    "audit": ["license", "supply_chain", "secrets", "egress"],
    "proving": ["sandbox", "build", "tests", "adversarial", "benchmarks", "reproducibility"],
    "quant": ["reconstruction", "data", "backtest", "robustness", "execution", "cerebus"],
    "acquisition": ["decisions", "adapters", "extraction", "vendoring", "forks", "reimplementation"],
    "evidence": ["artifacts", "receipts", "provenance", "hashing"],
    "registry": ["capabilities", "repositories", "relationships"],
    "monitoring": ["upstream", "drift", "revalidation"],
    "governance": ["interfaces", "standalone", "oce"],
    "infrastructure": ["persistence", "queue", "secrets", "sandbox_backends"],
    "interfaces": ["cli", "api"],
}


def test_qcae_package_metadata() -> None:
    assert qcae.__version__
    assert qcae.CANON_VERSION == "0.1"


@pytest.mark.parametrize("name", CANON_TOPLEVEL)
def test_toplevel_package_exists_and_imports(name: str) -> None:
    pkg_dir = QCAE_DIR / name
    assert pkg_dir.is_dir(), f"missing canon toplevel package: {name}"
    module = importlib.import_module(f"qcae.{name}")
    assert module.__doc__, f"canon package {name} lacks a responsibility docstring"


@pytest.mark.parametrize(
    ("parent", "child"),
    [(p, c) for p, children in CANON_SECOND_LEVEL.items() for c in children],
)
def test_second_level_package_exists_and_imports(parent: str, child: str) -> None:
    pkg_dir = QCAE_DIR / parent / child
    assert pkg_dir.is_dir(), f"missing canon subpackage: {parent}/{child}"
    module = importlib.import_module(f"qcae.{parent}.{child}")
    assert module.__doc__, f"canon subpackage {parent}.{child} lacks a responsibility docstring"
