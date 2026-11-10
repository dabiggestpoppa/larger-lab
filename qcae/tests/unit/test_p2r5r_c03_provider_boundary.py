"""P2-R5R-C03 — provider-neutral admission + a single request resolver.

Architecture laws proven by AST (never a string grep):

1. No module under ``qcae/orchestration/**`` imports
   ``qcae.governance.standalone`` at ANY level — statically, dynamically
   (``__import__`` / ``importlib.import_module`` with a literal), or inside a
   function (deferred import). The orchestrator depends only on the
   provider-neutral ``ApprovalAdmissionProvider`` port.
2. ``latest_for_step`` exists in exactly ONE place: the resolver. Neither the
   engine nor the runtime service re-implements request lookup.
3. Both execution-time admission (engine) and grant-release verification
   (runtime service) hold a resolver instance.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from qcae.infrastructure.persistence.sqlite_approval_registry import (
    SqliteApprovalRegistry,
)
from qcae.orchestration.authority_gate import (
    ApprovalAdmissionProvider,
    ApprovalRequestResolver,
)
from qcae.orchestration.jobs.runtime import JobEventType

QCAE_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATION_ROOT = QCAE_ROOT / "orchestration"
FORBIDDEN_ROOT = "qcae.governance.standalone"


def _py_files() -> list:
    return sorted(p for p in ORCHESTRATION_ROOT.rglob("*.py"))


def _violations(path: Path) -> list:
    """Every governance-standalone import/reference in one module's AST."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_ROOT):
                    found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(FORBIDDEN_ROOT):
                found.append((node.lineno, module))
            # ``from qcae.governance import standalone``
            if module == "qcae.governance" and any(
                a.name == "standalone" for a in node.names
            ):
                found.append((node.lineno, "qcae.governance.standalone"))
        elif isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name in ("__import__", "import_module"):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(
                        arg.value, str
                    ) and arg.value.startswith(FORBIDDEN_ROOT):
                        found.append((node.lineno, arg.value))
    return found


class TestProviderBoundaryArchitecture:
    def test_orchestration_has_no_governance_standalone_import(self) -> None:
        files = _py_files()
        assert files, "orchestration package missing"
        violations = {p: v for p in files if (v := _violations(p))}
        assert not violations, "\n".join(
            f"{p.relative_to(QCAE_ROOT)}:{line}: {mod}"
            for p, items in violations.items()
            for line, mod in items
        )

    def test_engine_depends_on_the_port_not_a_concrete_registry(self) -> None:
        engine = ORCHESTRATION_ROOT / "orchestrator" / "engine.py"
        source = engine.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
        assert "qcae.orchestration.authority_gate" in imported
        assert "sqlite_approval_registry" not in " ".join(imported)
        # The port is what the engine stores.
        assert "ApprovalAdmissionProvider" in source


class TestSingleRequestResolver:
    def test_latest_for_step_is_defined_in_exactly_one_module(self) -> None:
        owners = []
        for path in QCAE_ROOT.rglob("*.py"):
            if "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name in (
                    "latest_for_step", "_latest_authority_request",
                ):
                    owners.append(path.relative_to(QCAE_ROOT))
        assert owners == [Path("orchestration/authority_gate.py")], owners

    def test_both_admission_and_release_hold_a_resolver(self) -> None:
        engine = (ORCHESTRATION_ROOT / "orchestrator" / "engine.py").read_text(
            encoding="utf-8"
        )
        service = (
            QCAE_ROOT / "governance" / "standalone" / "runtime_service.py"
        ).read_text(encoding="utf-8")
        assert "ApprovalRequestResolver(self._store.events_for_job)" in engine
        assert "ApprovalRequestResolver(self._store.events_for_job)" in service
        assert "self._resolver.latest_for_step" in engine
        assert "self._resolver.latest_for_step" in service

    def test_resolver_returns_latest_request_for_step(self) -> None:
        events = [
            (1, _ev("APPROVAL_REQUESTED", "s-1"), '{"authority_request_id": "req-1"}'),
            (2, _ev("APPROVAL_REQUESTED", "s-1"), '{"authority_request_id": "req-2"}'),
            (3, _ev("STEP_SUCCEEDED", "s-1"), '{"reason": "done"}'),
        ]
        resolver = ApprovalRequestResolver(lambda job_id: events)
        assert resolver.latest_for_step("job-1", "s-1") == "req-2"

    def test_resolver_none_when_no_request__or_unsinked(self) -> None:
        assert ApprovalRequestResolver(lambda job_id: []).latest_for_step(
            "job-1", "s-1") is None
        events = [(1, _ev("APPROVAL_REQUESTED", "s-1"),
                   '{"authority_request_id": "unsinked"}')]
        assert ApprovalRequestResolver(lambda job_id: events).latest_for_step(
            "job-1", "s-1") is None


class TestRegistryImplementsPort:
    def test_registry_exposes_the_port_methods(self) -> None:
        for name in ("get_request", "effective_grant", "consume_grant"):
            assert hasattr(SqliteApprovalRegistry, name), name

    def test_port_is_runtime_checkable(self) -> None:
        assert getattr(ApprovalAdmissionProvider, "_is_runtime_protocol", False)


@dataclass
class _Ev:
    event_type: object
    event_id: str
    step_id: str


def _ev(event_type_name: str, step_id: str) -> _Ev:
    return _Ev(
        event_type=JobEventType[event_type_name],
        event_id="ev",
        step_id=step_id,
    )
