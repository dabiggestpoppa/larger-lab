"""P0-T01 — architecture/dependency guards (canon Book V 15.2).

Enforces the hard dependency line around QCAE core:

- core imports only stdlib and qcae.core (provider-neutral domain, ADR-0001);
- core cannot import higher layers (orchestration, discovery, ... interfaces);
- nothing outside governance.oce imports OCE adapter code (14.8 isolation);
- database engines are denied even when packaged in stdlib (sqlite3).

The scanner is itself tested against a synthetic violating tree so a silent
scanner regression cannot fake a green architecture.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

QCAE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = QCAE_DIR.parent
CORE_DIR = QCAE_DIR / "core"

CORE_PACKAGE = "qcae.core"
OCE_ADAPTER_PACKAGE = "qcae.governance.oce"

#: A-001 §7: QCAE must not rebuild or import Research Mesh implementation.
#: Research Mesh enters core through interface contracts only.
RESEARCH_MESH_IMPLEMENT_FRAGMENTS = frozenset(
    {"research_mesh", "researchmesh", "research-mesh"}
)

#: Higher layers that core must never depend on (canon 15.2 dependency direction).
HIGHER_LAYERS = frozenset(
    {
        "orchestration", "discovery", "intelligence", "audit", "proving",
        "quant", "acquisition", "evidence", "registry", "monitoring",
        "governance", "infrastructure", "interfaces",
    }
)

#: Explicit denials beyond the stdlib-only rule (canon 15.2 forbidden list).
DENIED_ROOTS = frozenset({"sqlite3"})


@dataclass(frozen=True)
class ImportViolation:
    file: Path
    lineno: int
    module: str
    reason: str

    def __str__(self) -> str:  # pragma: no cover - test output formatting
        return f"{self.file}:{self.lineno}: imports '{self.module}' — {self.reason}"


def _resolve_import(py_file: Path, tree_root: Path, node: ast.ImportFrom) -> str:
    """Resolve an import (absolute or relative) to its dotted package path."""
    if node.level == 0:
        return node.module or ""
    package_parts = list(py_file.resolve().parent.relative_to(tree_root).parts)
    # level=1 means current package, level=2 means parent, etc.
    for _ in range(node.level - 1):
        if package_parts:
            package_parts.pop()
    if node.module:
        return ".".join(package_parts + node.module.split("."))
    return ".".join(package_parts)


def _iter_imports(py_file: Path):
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno, node
        elif isinstance(node, ast.ImportFrom):
            yield "__importfrom__", node.lineno, node
        elif isinstance(node, ast.Call):
            # Catch dynamic __import__("x") usage too.
            func = node.func
            if isinstance(func, ast.Name) and func.id == "__import__" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    yield arg.value, node.lineno, node


def _module_exists_in_tree(tree_root: Path, module: str) -> bool:
    base = tree_root.joinpath(*module.split("."))
    return (base.with_suffix(".py").is_file()
            or (base / "__init__.py").is_file())


def scan_directory(directory: Path, tree_root: Path, *, is_core: bool) -> list:
    """Scan .py files under ``directory`` for dependency-rule violations.

    ``tree_root`` is the directory containing the top-level ``qcae`` package
    (the real repository root, or a synthetic tmp tree mirroring the layout).
    """
    violations = []
    for py_file in sorted(directory.rglob("*.py")):
        rel_posix = py_file.resolve().relative_to(tree_root).as_posix()
        for module, lineno, node in _iter_imports(py_file):
            if module == "__importfrom__":
                module = _resolve_import(py_file, tree_root, node)
            root = module.split(".")[0] if module else ""

            if root in DENIED_ROOTS:
                violations.append(ImportViolation(py_file, lineno, module,
                                                  "denied root (canon 15.2)"))
                continue

            if is_core:
                if module == CORE_PACKAGE or module.startswith(CORE_PACKAGE + "."):
                    continue  # internal core import
                if root == "qcae":
                    violations.append(ImportViolation(
                        py_file, lineno, module,
                        "core must not import higher layers (canon 15.2)"))
                elif not _module_exists_in_tree(tree_root, module) and root \
                        and root not in sys.stdlib_module_names:
                    violations.append(ImportViolation(
                        py_file, lineno, module,
                        "core must be stdlib-only (ADR-0001, canon 15.2)"))
            else:
                if module == OCE_ADAPTER_PACKAGE or module.startswith(
                    OCE_ADAPTER_PACKAGE + "."
                ):
                    in_oce = rel_posix.startswith(
                        OCE_ADAPTER_PACKAGE.replace(".", "/"))
                    if not in_oce:
                        violations.append(ImportViolation(
                            py_file, lineno, module,
                            "only governance/oce adapters may import OCE code "
                            "(canon 14.8, master prompt §21)"))
    return violations


class TestCoreDependencyRules:
    def test_core_is_stdlib_only(self) -> None:
        violations = scan_directory(CORE_DIR, REPO_ROOT, is_core=True)
        assert not violations, "\n" + "\n".join(str(v) for v in violations)

    def test_core_does_not_import_providers_or_frameworks(self) -> None:
        """Belt-and-braces scan for canon 15.2's named forbidden categories."""
        forbidden_fragments = (
            "github", "deepwiki", "openai", "anthropic", "docker", "kubernetes",
            "k8s", "boto", "requests", "httpx", "sqlalchemy", "psycopg", "duckdb",
            "fastapi", "flask", "django", "backtrader", "zipline", "nautilus",
            "pandas", "numpy", "pydantic",
        )
        for py_file in sorted(CORE_DIR.rglob("*.py")):
            for module, _lineno, _node in _iter_imports(py_file):
                if module == "__importfrom__":
                    module = _resolve_import(py_file, REPO_ROOT, _node)
                for fragment in forbidden_fragments:
                    assert fragment not in module.lower(), (
                        f"{py_file}: core imports '{module}' "
                        f"(matches forbidden provider fragment '{fragment}')"
                    )

    def test_core_imports_only_from_qcae_core(self) -> None:
        for py_file in sorted(CORE_DIR.rglob("*.py")):
            for module, _lineno, _node in _iter_imports(py_file):
                if module == "__importfrom__":
                    module = _resolve_import(py_file, REPO_ROOT, _node)
                if module.startswith("qcae"):
                    assert module == CORE_PACKAGE or module.startswith(
                        CORE_PACKAGE + "."
                    ), f"{py_file}: core imports '{module}' outside qcae.core"

    def test_core_has_no_third_party_runtime(self) -> None:
        """Every import in core resolves to stdlib or qcae — checked exhaustively."""
        for py_file in sorted(CORE_DIR.rglob("*.py")):
            for module, _lineno, _node in _iter_imports(py_file):
                if module == "__importfrom__":
                    module = _resolve_import(py_file, REPO_ROOT, _node)
                root = module.split(".")[0] if module else ""
                if module == CORE_PACKAGE or module.startswith(CORE_PACKAGE + "."):
                    continue
                assert not root or root in sys.stdlib_module_names, (
                    f"{py_file}: non-stdlib import '{module}'"
                )


class TestOceIsolation:
    def test_no_qcae_module_imports_oce_adapters(self) -> None:
        violations = scan_directory(QCAE_DIR, REPO_ROOT, is_core=False)
        assert not violations, "\n" + "\n".join(str(v) for v in violations)

    def test_core_rejects_research_mesh_implementation_import(self, tmp_path: Path) -> None:
        """A-001 §7 / reconciliation §13: a direct Research Mesh implementation
        import into qcae/core must be flagged as a stdlib/layer violation."""
        pkg_dir = tmp_path / "qcae" / "core"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        (pkg_dir / "leak.py").write_text(
            "import research_mesh.institution\n"
            "from researchmesh.consensus import engine\n"
            "from qcae.research_mesh.adapter import x\n",
            encoding="utf-8",
        )
        violations = scan_directory(pkg_dir, tmp_path, is_core=True)
        modules = {v.module for v in violations}
        assert "research_mesh.institution" in modules
        assert "researchmesh.consensus" in modules
        assert "qcae.research_mesh.adapter" in modules

    def test_core_contains_no_research_mesh_import(self) -> None:
        """The real core tree imports no Research Mesh implementation."""
        for py_file in sorted(CORE_DIR.rglob("*.py")):
            for module, _lineno, _node in _iter_imports(py_file):
                if module == "__importfrom__":
                    module = _resolve_import(py_file, REPO_ROOT, _node)
                lowered = module.lower()
                for fragment in RESEARCH_MESH_IMPLEMENT_FRAGMENTS:
                    assert fragment not in lowered, (
                        f"{py_file}: core imports '{module}' — Research Mesh "
                        "implementation must not leak into core (A-001 §7)"
                    )

    def test_oce_adapter_package_is_empty_placeholder(self) -> None:
        """P0 ships the boundary, not the implementation (canon 18.1 P12)."""
        oce_dir = QCAE_DIR / "governance" / "oce"
        assert oce_dir.is_dir()
        py_files = [p for p in oce_dir.rglob("*.py") if p.name != "__init__.py"]
        assert py_files == [], (
            "OCE adapter implementation must not exist before P12"
        )


class TestScannerSelfVerification:
    """The guard must be able to catch violations — a broken guard is a hazard."""

    def _make_tree(self, tmp_path: Path, relpath: str, code: str) -> Path:
        """Create a synthetic package mirroring production layout: <root>/qcae/..."""
        pkg_dir = tmp_path / "qcae" / relpath
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        target = pkg_dir / "module.py"
        target.write_text(code, encoding="utf-8")
        return target

    def _scan(self, tmp_path: Path, subdir: str, *, is_core: bool) -> list:
        return scan_directory(tmp_path / "qcae" / subdir, tmp_path, is_core=is_core)

    def test_scanner_flags_third_party_import_in_core(self, tmp_path: Path) -> None:
        self._make_tree(tmp_path, "core", "import requests\n")
        violations = self._scan(tmp_path, "core", is_core=True)
        assert any("stdlib-only" in v.reason for v in violations)

    def test_scanner_flags_higher_layer_import_in_core(self, tmp_path: Path) -> None:
        self._make_tree(
            tmp_path, "core", "from qcae.discovery.github import adapter\n"
        )
        violations = self._scan(tmp_path, "core", is_core=True)
        assert any("higher layers" in v.reason for v in violations)

    def test_scanner_flags_sqlite_in_core(self, tmp_path: Path) -> None:
        self._make_tree(tmp_path, "core", "import sqlite3\n")
        violations = self._scan(tmp_path, "core", is_core=True)
        assert any("denied root" in v.reason for v in violations)

    def test_scanner_flags_relative_escape_from_core(self, tmp_path: Path) -> None:
        target = self._make_tree(
            tmp_path, "core/contracts", "from ...discovery import x\n"
        )
        violations = self._scan(tmp_path, "core", is_core=True)
        assert any(
            v.file == target and "higher layers" in v.reason for v in violations
        )

    def test_scanner_allows_internal_core_relative_import(self, tmp_path: Path) -> None:
        self._make_tree(
            tmp_path, "core/contracts", "from ..errors import QcaeError\n"
        )
        assert self._scan(tmp_path, "core", is_core=True) == []

    def test_scanner_flags_oce_import_outside_adapter(self, tmp_path: Path) -> None:
        self._make_tree(
            tmp_path, "orchestration", "from qcae.governance.oce.client import x\n"
        )
        violations = self._scan(tmp_path, "orchestration", is_core=False)
        assert any("OCE" in v.reason for v in violations)

    def test_scanner_accepts_oce_import_inside_adapter(self, tmp_path: Path) -> None:
        self._make_tree(
            tmp_path, "governance/oce", "from qcae.governance.oce.client import x\n"
        )
        assert self._scan(tmp_path, "governance", is_core=False) == []

    def test_scanner_accepts_stdlib_and_core_imports(self, tmp_path: Path) -> None:
        self._make_tree(
            tmp_path,
            "core/contracts",
            "import json\nimport hashlib\nfrom dataclasses import dataclass\n"
            "from qcae.core.errors import QcaeError\nfrom . import sibling\n",
        )
        assert self._scan(tmp_path, "core", is_core=True) == []

    def test_scanner_flags_dynamic_import(self, tmp_path: Path) -> None:
        self._make_tree(tmp_path, "core", 'mod = __import__("pandas")\n')
        violations = self._scan(tmp_path, "core", is_core=True)
        assert any("pandas" in v.module for v in violations)
