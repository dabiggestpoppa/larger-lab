"""OCE Book 4 — B4-CXR7U7 security-test integrity gate.

Two layers:

1. ANTI-VACUITY GATE (static): every mandatory security test module is parsed
   with AST and checked for demonstrably vacuous assertions
   (``assert ... or True``, ``assert True``, ``assert False or ...``) and for
   unconditional early returns that skip the security decision. The gate
   fails if any security test module carries them.

2. NEGATIVE CONTROLS (behavioral mutation probes): removing a security
   property from the runtime MUST make the pinned suite fail. Each control
   neutralizes one production defense on a throwaway module copy and proves
   the corresponding tests detect it:

   * parent/child type separation  -> U2 type tests fail
   * role/audience validation      -> U2/CXR6R1 role tests fail
   * atomic nonce consumption      -> U4 replay tests fail
   * corrupt-ledger refusal        -> U4 fail-closed tests fail
   * audit canonicalization        -> U5 canonical tests fail
   * configure rollback/recovery   -> U6 failure-injection tests fail
   * trusted-program allowlisting  -> U3 registry tests fail
   * truthful isolation reporting  -> U3 truth tests fail
"""
from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "src"

# Security-mandatory test modules covered by the anti-vacuity gate.
SECURITY_TEST_MODULES = [
    "test_b4_cxr6_activation_capability.py",
    "test_b4_cxr7_threat_model.py",
    "test_b4_cxr7_trusted_program.py",
    "test_b4_cxr7_atomic_consumption.py",
    "test_b4_cxr7_configure_atomic.py",
    "test_b4_startup_gate.py",
    "test_b4_config_spine.py",
]

# security-mandatory RUNTIME modules that must carry no vacuous assertions
SECURITY_RUNTIME_MODULES = [
    "oce_control/config_startup.py",
    "oce_control/local_secrets.py",
    "oce_control/local_lifecycle.py",
    "oce_control/audit_sink.py",
    "oce_control/execution_runtime.py",
    "oce_control/representative_jobs.py",
]


def _vacuous_assert(node: ast.AST) -> str | None:
    """Classify a demonstrably vacuous assert, or return None."""
    if not isinstance(node, ast.Assert):
        return None
    test = node.test
    if isinstance(test, ast.Constant) and test.value is True:
        return "assert True"
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        for value in test.values:
            if isinstance(value, ast.Constant) and value.value is True:
                return "assert ... or True"
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        for value in test.values:
            if isinstance(value, ast.Constant) and value.value is False:
                return "assert ... and False"
    return None


def _unconditional_early_return_after_advertised_path(module_path: Path) -> str | None:
    """Detect an unconditional early return as the FIRST statement of a test
    function (the security decision can never be reached)."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test_"):
            continue
        body = fn.body
        # a test whose body is only `return` / `assert True` then unreachable code
        if len(body) >= 2 and isinstance(body[0], ast.Return) and \
                body[0].value is None:
            return f"{module_path.name}:{fn.name}: unconditional first-statement return"
    return None


class TestAntiVacuityGate:
    """Static AST gate: no mandatory security test may pass vacuously."""

    @pytest.mark.parametrize("module", SECURITY_TEST_MODULES)
    def test_no_vacuous_assertions_in_security_tests(self, module):
        path = BASE / "tests" / module
        assert path.exists(), module
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            v = _vacuous_assert(node)
            assert v is None, f"{module}: {v} at line {node.lineno}"

    @pytest.mark.parametrize("module", SECURITY_TEST_MODULES)
    def test_no_unconditional_early_return_in_security_tests(self, module):
        path = BASE / "tests" / module
        offense = _unconditional_early_return_after_advertised_path(path)
        assert offense is None, offense

    @pytest.mark.parametrize("module", SECURITY_RUNTIME_MODULES)
    def test_no_vacuous_assertions_in_security_runtime(self, module):
        path = SRC / module
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            v = _vacuous_assert(node)
            assert v is None, f"{module}: {v} at line {node.lineno}"

    def test_comments_do_not_claim_unmeasured_side_effects(self):
        # the CXR7 blocker evidence documented a comment/claim mismatch;
        # security test files must not claim side-effect checks they never
        # perform: every comment naming a snapshot must be near snapshot use
        offenders = []
        for module in SECURITY_TEST_MODULES:
            path = BASE / "tests" / module
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") and "zero side effects" in stripped:
                    # the test function must actually take a snapshot nearby
                    window = "\n".join(text.splitlines()[i:i + 30])
                    if "_state_snapshot" not in window and "digest" not in window \
                            and "before ==" not in window and "== before" not in window \
                            and "_store_digests" not in window:
                        offenders.append(f"{module}:{i}")
        assert offenders == []


# --------------------------------------------------------------------------- #
# Negative controls: removing a defense must fail the pinned suite
# --------------------------------------------------------------------------- #

def _run_pinned(node_ids: list[str], mutation, tmp_path) -> bool:
    """Apply *mutation* to a COPY of the runtime on sys.path and run the
    pinned node ids against it. Returns True when the suite FAILS (defense
    removal is detected).

    The mutation receives (source_text) and returns mutated text; it is
    applied to the real module file for the subprocess lifetime only, and
    restored in a finally block. (Files are restored byte-for-byte; this is
    the one honest way to prove the suite detects removal without building a
    parallel fake runtime that could itself drift from production.)
    """
    targets = mutation["files"]
    saved = {str(p): p.read_bytes() for p in targets}
    try:
        for spec in mutation["apply"]:
            p = spec["path"]
            p.write_text(spec["mutate"](p.read_text(encoding="utf-8")),
                         encoding="utf-8")
        import subprocess
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(BASE), str(SRC), str(BASE / "scripts"), str(BASE / "tests"),
             env.get("PYTHONPATH", "")])
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-x",
             "--timeout-method=thread" if False else "-p", "no:cacheprovider",
             *node_ids],
            cwd=str(BASE), env=env, capture_output=True, text=True,
            timeout=600, errors="replace")
        return r.returncode != 0
    finally:
        for raw, data in saved.items():
            Path(raw).write_bytes(data)


import os  # noqa: E402  (used by _run_pinned)


def _cs() -> Path:
    return SRC / "oce_control" / "config_startup.py"


def _ls() -> Path:
    return SRC / "oce_control" / "local_secrets.py"


class TestNegativeControls:
    """Removing a security property must make the pinned tests fail."""

    def test_removal_of_parent_child_type_separation_detected(self, tmp_path):
        mutation = {
            "files": [_cs()],
            "apply": [{
                "path": _cs(),
                "mutate": lambda t: t.replace(
                    "return VerifiedChildContext(", "return ParentActivationContext("),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr6_activation_capability.py::"
             "TestCXR6R1AuthenticatedActivationCapability::"
             "test_child_cannot_reissue_capability"], mutation, tmp_path), \
            "suite failed to detect removal of parent/child type separation"

    def test_removal_of_role_audience_validation_detected(self, tmp_path):
        mutation = {
            "files": [_cs()],
            "apply": [{
                "path": _cs(),
                "mutate": lambda t: t.replace(
                    "if role != envelope.child_role:",
                    "if False and role != envelope.child_role:"),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr6_activation_capability.py::"
             "TestCXR6R1AuthenticatedActivationCapability::"
             "test_l_role_confusion_rejected"], mutation, tmp_path), \
            "suite failed to detect removal of role/audience validation"

    def test_removal_of_atomic_nonce_consumption_detected(self, tmp_path):
        mutation = {
            "files": [_ls()],
            "apply": [{
                "path": _ls(),
                "mutate": lambda t: t.replace(
                    "def consume_handoff_once(nonce: str, metadata: dict | None = None) -> bool:",
                    "def consume_handoff_once(nonce: str, metadata: dict | None = None) -> bool:\n"
                    "    return True  # MUTANT: never records consumption"),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr7_atomic_consumption.py::"
             "TestConsumeHandoffOnce::test_sequential_replay_denied"],
            mutation, tmp_path), \
            "suite failed to detect removal of atomic nonce consumption"

    def test_removal_of_corrupt_ledger_refusal_detected(self, tmp_path):
        mutation = {
            "files": [_ls()],
            "apply": [{
                "path": _ls(),
                "mutate": lambda t: t.replace(
                    "class LedgerCorrupt(RuntimeError):",
                    "class LedgerCorrupt(Exception):\n    pass\n\n\nclass _Unused(RuntimeError):"),
            }],
        }
        # a corrupt ledger must still fail closed: mutating the exception
        # base is a no-op probe; instead remove the strict loader refusal
        mutation = {
            "files": [_ls()],
            "apply": [{
                "path": _ls(),
                "mutate": lambda t: t.replace(
                    'raise LedgerCorrupt(\n            f"consumed-handoff ledger is corrupt JSON',
                    'return {}\n        _never = (\n            f"consumed-handoff ledger is corrupt JSON'),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr7_atomic_consumption.py::"
             "TestFailClosedLedger::test_corrupt_json_denied_without_rewrite"],
            mutation, tmp_path), \
            "suite failed to detect removal of corrupt-ledger refusal"

    def test_removal_of_audit_canonicalization_detected(self, tmp_path):
        target = SRC / "oce_control" / "audit_sink.py"
        mutation = {
            "files": [target],
            "apply": [{
                "path": target,
                "mutate": lambda t: t.replace(
                    "if isinstance(value, bool):\n        return \"true\" if value else \"false\"",
                    "if isinstance(value, bool):\n        return str(value)  # MUTANT: 'True'/'False'"),
            }],
        }
        # the UNIT canonical-value test runs everywhere (no container needed);
        # container CI additionally proves the same property through the real
        # PostgreSQL sink (boolean exact retry)
        assert _run_pinned(
            ["tests/test_b4_config_spine.py::"
             "TestCXR7U5CanonicalAuditValue::test_canonical_values"],
            mutation, tmp_path), \
            "suite failed to detect removal of audit canonicalization"

    def test_removal_of_configure_rollback_detected(self, tmp_path):
        target = SRC / "oce_control" / "local_lifecycle.py"
        mutation = {
            "files": [target],
            "apply": [{
                "path": target,
                "mutate": lambda t: t.replace(
                    "_configure_restore(snapshot)",
                    "pass  # MUTANT: rollback removed"),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr7_configure_atomic.py::"
             "TestCompleteOrNothingConfigure::"
             "test_failure_on_first_configure_leaves_no_state"],
            mutation, tmp_path), \
            "suite failed to detect removal of configure rollback/recovery"

    def test_removal_of_trusted_program_allowlisting_detected(self, tmp_path):
        target = SRC / "oce_control" / "representative_jobs.py"
        mutation = {
            "files": [target],
            "apply": [{
                "path": target,
                "mutate": lambda t: t.replace(
                    "def program_for(job_type: str) -> str:\n    if job_type not in _PROGRAMS:\n        raise KeyError(f\"unsupported task type '{job_type}' — fail closed\")\n    return _PROGRAMS[job_type]",
                    "def program_for(job_type: str) -> str:\n    return _PROGRAMS.get(job_type, \"import os\\nprint('MUTANT-EXEC')\")"),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr7_trusted_program.py::"
             "TestTrustedProgramRegistry::test_unknown_job_type_fails_closed"],
            mutation, tmp_path), \
            "suite failed to detect removal of trusted-program allowlisting"

    def test_removal_of_truthful_isolation_reporting_detected(self, tmp_path):
        target = SRC / "oce_control" / "execution_runtime.py"
        mutation = {
            "files": [target],
            "apply": [{
                "path": target,
                "mutate": lambda t: t.replace(
                    '"os_network_enforcement": "not implemented",',
                    '"os_network_enforcement": "enforced by rlimits",'),
            }],
        }
        assert _run_pinned(
            ["tests/test_b4_cxr7_trusted_program.py::"
             "TestTruthfulIsolationReporting::"
             "test_resource_enforcement_report_states_the_three_truths"],
            mutation, tmp_path), \
            "suite failed to detect removal of truthful isolation reporting"
