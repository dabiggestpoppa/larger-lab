"""OCE Book 4 — B4-CXR7U7/U8 security-test integrity gate.

Three layers:

1. ANTI-VACUITY GATE (static): every mandatory security test module is parsed
   with AST and checked for demonstrably vacuous assertions
   (``assert ... or True``, ``assert True``, ``assert x not in ""`` —
   constant/empty-container noise) and for unconditional early returns that
   skip the security decision. The gate fails if any security test module
   carries them.

2. NEGATIVE CONTROLS with ISOLATED MUTATION (behavioral, B4-CXR7U8-01/02):
   removing a security property from the runtime MUST make the pinned suite
   fail — and a mutation proof passes ONLY when the failure is attributable
   to the removed defense. The canonical checkout is NEVER modified:

   * the minimum runnable control-plane tree (src/, scripts/, tests/ Python
     sources) is materialized under tmp_path;
   * every mutation is applied ONLY inside that isolated tree;
   * the canonical checkout is hashed before and after EVERY control (also
     on mutation-function exception, subprocess timeout, subprocess
     termination, invalid mutant, and collection failure) and proven
     byte-identical;
   * detection requires: baseline (unmutated copy) collects each pinned node
     exactly once and passes it exactly once with exit code 0; the mutant is
     applied exactly once (pattern verified) and changes the isolated file
     digest; the mutant run exits 1 (tests failed, NOT a collection/import/
     usage/internal/timeout error) and JUnit proves the EXPECTED node was
     collected and failed.

3. FALSE-POSITIVE NEGATIVE CONTROLS (B4-CXR7U8-02): a missing node ID, a
   collection error, a syntax-error mutant, a subprocess timeout or
   termination, an unrelated failing test, and an absent replacement pattern
   are NOT accepted as mutation proof.

Canonical statements live in B4-THREAT-MODEL.md.
"""
from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "src"
SCRIPTS = BASE / "scripts"
TESTS = BASE / "tests"

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
    # constant/empty-container comparisons: `assert x not in ""` (or an empty
    # list/dict/set/tuple) is ALWAYS True regardless of x — pure noise.
    if isinstance(test, ast.Compare):
        for op, comparator in zip(test.ops, test.comparators):
            if isinstance(op, ast.NotIn) and isinstance(comparator, ast.Constant):
                if isinstance(comparator.value, (str, list, dict, set, tuple)) \
                        and len(comparator.value) == 0:
                    return "assert ... not in <empty literal>"
    return None


def _constant_false_ternary_in_test(module_path: Path) -> str | None:
    """Detect `X if False else Y` expression statements inside test bodies —
    the False branch makes the ternary constant-selected and the test's
    advertised path unreachable (B4-CXR7U8-03)."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test_"):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.IfExp) and isinstance(node.test, ast.Constant):
                if node.test.value is False:
                    return (f"{module_path.name}:{fn.name}: constant-false "
                            f"ternary at line {node.lineno}")
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
        if len(body) >= 2 and isinstance(body[0], ast.Return) and \
                body[0].value is None:
            return f"{module_path.name}:{fn.name}: unconditional first-statement return"
    return None


class TestAntiVacuityGate:
    """Static AST gate: no mandatory security test may pass vacuously."""

    @pytest.mark.parametrize("module", SECURITY_TEST_MODULES)
    def test_no_vacuous_assertions_in_security_tests(self, module):
        path = TESTS / module
        assert path.exists(), module
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            v = _vacuous_assert(node)
            assert v is None, f"{module}: {v} at line {node.lineno}"

    @pytest.mark.parametrize("module", SECURITY_TEST_MODULES)
    def test_no_unconditional_early_return_in_security_tests(self, module):
        path = TESTS / module
        offense = _unconditional_early_return_after_advertised_path(path)
        assert offense is None, offense

    @pytest.mark.parametrize("module", SECURITY_TEST_MODULES)
    def test_no_constant_false_ternary_in_security_tests(self, module):
        # `X if False else Y` makes the advertised path unreachable — the
        # constant-selected branch is vacuous noise (B4-CXR7U8-03)
        path = TESTS / module
        offense = _constant_false_ternary_in_test(path)
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
            path = TESTS / module
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") and "zero side effects" in stripped:
                    window = "\n".join(text.splitlines()[i:i + 30])
                    if "_state_snapshot" not in window and "digest" not in window \
                            and "before ==" not in window and "== before" not in window \
                            and "_store_digests" not in window:
                        offenders.append(f"{module}:{i}")
        assert offenders == []


# --------------------------------------------------------------------------- #
# Isolated mutation-control machinery (B4-CXR7U8-01/02)
# --------------------------------------------------------------------------- #

class MutationControlError(Exception):
    """The mutation-control PROTOCOL itself failed (never counts as proof)."""


def _canonical_hash() -> str:
    """SHA-256 over every tracked canonical Python source under src/,
    scripts/ and the pinned test modules. The canonical checkout must be
    byte-identical before and after every mutation control."""
    h = hashlib.sha256()
    roots = [(SRC, "src"), (SCRIPTS, "scripts"), (TESTS, "tests")]
    rels = set()
    for root, prefix in roots:
        for p in sorted(root.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            rels.add(f"{prefix}/{p.relative_to(root).as_posix()}")
    for rel in sorted(rels):
        path = BASE / rel
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            continue  # only files that exist in the canonical checkout
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(data)
        h.update(b"\x00")
    return h.hexdigest()


def _build_isolated_tree(tmp_path: Path) -> Path:
    """Materialize the minimum runnable control-plane tree (all Python
    sources under src/, scripts/, tests/) inside *tmp_path*. Nothing outside
    this tree is ever read or written by the mutation runs."""
    iso = tmp_path / "iso"
    for sub, dest in ((SRC, iso / "src"),
                      (SCRIPTS, iso / "scripts"),
                      (TESTS, iso / "tests")):
        for p in sub.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            rel = p.relative_to(sub)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
    # compose.yml is read STATICALLY by configure()'s loopback preflight
    # (published_ports_from_compose) — the isolated tree needs it to behave
    # exactly like the canonical checkout.
    compose_yml = BASE / "compose" / "compose.yml"
    if compose_yml.exists():
        (iso / "compose").mkdir(parents=True, exist_ok=True)
        shutil.copy2(compose_yml, iso / "compose" / "compose.yml")
    return iso


def _run_pytest_isolated(iso: Path, node_ids: list[str],
                         junit: Path, timeout_s: float):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(iso), str(iso / "src"), str(iso / "scripts"), str(iso / "tests"),
         env.get("PYTHONPATH", "")])
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--no-header", "-q",
         "-p", "no:cacheprovider", "--junitxml", str(junit),
         "--rootdir", str(iso), *node_ids],
        cwd=str(iso), env=env, capture_output=True, text=True,
        timeout=timeout_s, errors="replace")


def _junit_summary(xml_path: Path) -> dict:
    """Parse a pytest JUnit file into {tests, errors, failures, cases} where
    cases maps classname->{name: status}."""
    if not xml_path.exists():
        return {}
    tree = ET.parse(xml_path)
    suite = tree.getroot()
    out = {"tests": int(suite.get("tests", 0)),
           "errors": int(suite.get("errors", 0)),
           "failures": int(suite.get("failures", 0)),
           "cases": []}
    for case in suite.iter("testcase"):
        status = "passed"
        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        out["cases"].append({
            "classname": case.get("classname", ""),
            "name": case.get("name", ""),
            "status": status,
        })
    return out


def _node_parts(node_id: str) -> tuple[str, str | None, str]:
    parts = node_id.split("::")
    file_part = parts[0]
    name = parts[-1]
    classname = parts[1] if len(parts) >= 3 else None
    return file_part, classname, name


def _expected_node_ran(summary: dict, node_id: str) -> tuple[bool, str]:
    """Exactly one run of the expected node; return (ran, verdict)."""
    file_part, classname, name = _node_parts(node_id)
    hits = [c for c in summary.get("cases", [])
            if (c["name"] == name or c["name"].startswith(name + "["))
            and (classname is None or c["classname"].endswith(classname))]
    if len(hits) != 1:
        return False, f"expected node collected {len(hits)} times (need exactly 1)"
    return True, hits[0]["status"]


def mutation_detected(node_id: str, mutations: list[dict], tmp_path: Path,
                      *, timeout_s: float = 600.0,
                      extra_nodes: list[str] | None = None) -> bool:
    """Run the FULL mutation-control protocol against an ISOLATED copy of the
    runtime under *tmp_path*. The canonical checkout is never touched: its
    hash is captured before the tree is built and verified byte-identical
    when the protocol finishes (normal detection, mutant failure,
    mutation-function exception, timeout, termination, invalid mutant, and
    collection failure all leave it untouched).

    Baseline: EVERY pinned node (node_id + extra_nodes) must collect exactly
    once and pass exactly once on the unmutated isolated copy (rc 0).

    Returns True ONLY when the applied mutant made the EXPECTED node
    (node_id) fail attributably (JUnit-proven, clean run) — a random nonzero
    exit is never mutation proof (B4-CXR7U8-02). A mutant that only breaks
    an UNRELATED node (extra_nodes) or nothing at all returns False.
    """
    before_hash = _canonical_hash()
    if not mutations:
        raise MutationControlError("mutation control has no apply steps")
    node_ids = [node_id] + list(extra_nodes or [])
    iso = _build_isolated_tree(tmp_path)
    junit = iso / "junit.xml"
    try:
        # 1. baseline: every pinned node must collect+pass exactly once on
        #    the UNMUTATED isolated copy (rc 0).
        base = _run_pytest_isolated(iso, node_ids, junit, timeout_s)
        if base.returncode != 0:
            raise MutationControlError(
                "baseline (unmutated isolated copy) must pass — an unrelated "
                f"failing test is NOT mutation proof (rc={base.returncode})")
        base_sum = _junit_summary(junit)
        for nid in node_ids:
            ran, verdict = _expected_node_ran(base_sum, nid)
            if not ran or verdict != "passed":
                raise MutationControlError(
                    f"baseline must collect+pass pinned node {nid} exactly "
                    f"once (ran={ran}, verdict={verdict})")

        # 2. verify each replacement pattern exists EXACTLY once in the
        #    isolated target, then apply the mutant; the isolated file digest
        #    must change (the mutation is real, not a no-op).
        for spec in mutations:
            target = iso / spec["path"]
            source = target.read_text(encoding="utf-8")
            count = source.count(spec["pattern"])
            if count != 1:
                raise MutationControlError(
                    f"replacement pattern appears {count} times in "
                    f"{spec['path']} (must be exactly 1): "
                    f"{spec['pattern'][:80]!r}")
            mutated = spec["mutate"](source)
            if hashlib.sha256(mutated.encode()).hexdigest() == \
                    hashlib.sha256(source.encode()).hexdigest():
                raise MutationControlError(
                    f"mutation did not change {spec['path']} — invalid mutant")
            target.write_text(mutated, encoding="utf-8")

        # 3. mutant run: rc 1 (tests failed), no collection/import/internal
        #    error, and the EXPECTED node failed in JUnit.
        try:
            mut = _run_pytest_isolated(iso, node_ids, junit, timeout_s)
        except subprocess.TimeoutExpired:
            return False  # a hanging mutant is a timeout, never proof
        if mut.returncode != 1:
            return False  # rc 0 (no detection), rc 2 (collection/usage), rc 3+
        text = (mut.stdout or "") + "\n" + (mut.stderr or "")
        for marker in ("INTERNALERROR", "errors during collection",
                       "ImportError while", "usage: "):
            if marker in text:
                return False  # collection/import/internal/usage — NOT proof
        sum_ = _junit_summary(junit)
        if sum_.get("errors", 0):
            return False
        ran, verdict = _expected_node_ran(sum_, node_id)
        if not ran:
            return False  # expected node was not even collected
        if verdict != "failed":
            return False  # expected node passed — not attributable proof
        return True
    finally:
        # 4. canonical checkout byte-invariance — always.
        if _canonical_hash() != before_hash:
            raise MutationControlError(
                "canonical checkout was modified by a mutation control — "
                "controls must never touch the real checkout")
        try:
            junit.unlink(missing_ok=True)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Negative controls: removing a defense must fail the pinned suite
# --------------------------------------------------------------------------- #
def _cs() -> str:
    return "src/oce_control/config_startup.py"


def _ls() -> str:
    return "src/oce_control/local_secrets.py"


# (mutation anchor strings are kept as plain literals so the isolated copy is
#  the only thing that changes — these strings must exist EXACTLY once in the
#  canonical source, verified per control run.)
MUTATION_CONTROLS = [
    {
        "name": "parent_child_type_separation",
        "node": "tests/test_b4_cxr6_activation_capability.py::"
                "TestCXR6R1AuthenticatedActivationCapability::"
                "test_child_cannot_reissue_capability",
        "mutations": [{
            "path": _cs(),
            "pattern": "return VerifiedChildContext(",
            "mutate": lambda t: t.replace(
                "return VerifiedChildContext(", "return ParentActivationContext(", 1),
        }],
    },
    {
        "name": "role_audience_validation",
        "node": "tests/test_b4_cxr6_activation_capability.py::"
                "TestCXR6R1AuthenticatedActivationCapability::"
                "test_l_capability_without_declared_role_rejected",
        "mutations": [{
            "path": _cs(),
            "pattern": "if role is None:",
            "mutate": lambda t: t.replace(
                "if role is None:", "if False and role is None:", 1),
        }],
    },
    {
        "name": "atomic_nonce_consumption",
        "node": "tests/test_b4_cxr7_atomic_consumption.py::"
                "TestConsumeHandoffOnce::test_sequential_replay_denied",
        "mutations": [{
            "path": _ls(),
            "pattern": "def consume_handoff_once(nonce: str, metadata: dict | None = None) -> bool:",
            "mutate": lambda t: t.replace(
                "def consume_handoff_once(nonce: str, metadata: dict | None = None) -> bool:",
                "def consume_handoff_once(nonce: str, metadata: dict | None = None) -> bool:\n"
                "    return True  # MUTANT: never records consumption", 1),
        }],
    },
    {
        "name": "corrupt_ledger_refusal",
        "node": "tests/test_b4_cxr7_atomic_consumption.py::"
                "TestFailClosedLedger::test_corrupt_json_denied_without_rewrite",
        "mutations": [{
            "path": _ls(),
            "pattern": 'raise LedgerCorrupt(\n            f"consumed-handoff '
                       'ledger is corrupt JSON — fail closed, no "\n'
                       '            f"rewrite (B4-CXR7U4): {exc}") from exc',
            "mutate": lambda t: t.replace(
                'raise LedgerCorrupt(\n            f"consumed-handoff '
                'ledger is corrupt JSON — fail closed, no "\n'
                '            f"rewrite (B4-CXR7U4): {exc}") from exc',
                "return {}  # MUTANT: corrupt ledger treated as empty", 1),
        }],
    },
    {
        "name": "audit_canonicalization",
        "node": "tests/test_b4_config_spine.py::"
                "TestCXR7U5CanonicalAuditValue::test_canonical_values",
        "mutations": [{
            "path": "src/oce_control/audit_sink.py",
            "pattern": "if isinstance(value, bool):\n        return "
                       '"true" if value else "false"',
            "mutate": lambda t: t.replace(
                "if isinstance(value, bool):\n        return "
                '"true" if value else "false"',
                "if isinstance(value, bool):\n        return str(value)  # MUTANT", 1),
        }],
    },
    {
        "name": "configure_rollback_recovery",
        "node": "tests/test_b4_cxr7_configure_atomic.py::"
                "TestCompleteOrNothingConfigure::"
                "test_failure_on_first_configure_leaves_no_state",
        "mutations": [{
            "path": "src/oce_control/local_lifecycle.py",
            # the 16-space-call site is configure()'s exception-rollback
            # path (the pinned test injects a projection failure and
            # asserts NO state); the recover() helper site is 4-space
            "pattern": "                _configure_restore(snapshot)",
            "mutate": lambda t: t.replace(
                "                _configure_restore(snapshot)",
                "                pass  # MUTANT: rollback removed", 1),
        }],
    },
    {
        "name": "trusted_program_allowlisting",
        "node": "tests/test_b4_cxr7_trusted_program.py::"
                "TestTrustedProgramRegistry::test_unknown_job_type_fails_closed",
        "mutations": [{
            "path": "src/oce_control/representative_jobs.py",
            "pattern": "def program_for(job_type: str) -> str:\n"
                       "    if job_type not in _PROGRAMS:\n"
                       "        raise KeyError(f\"unsupported task type '{job_type}' — fail closed\")\n"
                       "    return _PROGRAMS[job_type]",
            "mutate": lambda t: t.replace(
                "def program_for(job_type: str) -> str:\n"
                "    if job_type not in _PROGRAMS:\n"
                "        raise KeyError(f\"unsupported task type '{job_type}' — fail closed\")\n"
                "    return _PROGRAMS[job_type]",
                "def program_for(job_type: str) -> str:\n"
                "    return _PROGRAMS.get(job_type, \"import os\\nprint('MUTANT-EXEC')\")", 1),
        }],
    },
    {
        "name": "truthful_isolation_reporting",
        "node": "tests/test_b4_cxr7_trusted_program.py::"
                "TestTruthfulIsolationReporting::"
                "test_resource_enforcement_report_states_the_three_truths",
        "mutations": [{
            "path": "src/oce_control/execution_runtime.py",
            "pattern": '"os_network_enforcement": "not implemented",',
            "mutate": lambda t: t.replace(
                '"os_network_enforcement": "not implemented",',
                '"os_network_enforcement": "enforced by rlimits",', 1),
        }],
    },
]


class TestNegativeControlsIsolated:
    """Removing a security property must make the pinned tests fail on an
    ISOLATED copy — with a byte-identical canonical checkout before/after
    (B4-CXR7U8-01) and an attributable failure (B4-CXR7U8-02)."""

    @pytest.mark.parametrize("control", MUTATION_CONTROLS,
                             ids=[c["name"] for c in MUTATION_CONTROLS])
    def test_defense_removal_detected(self, control, tmp_path):
        before_hash = _canonical_hash()
        assert mutation_detected(control["node"], control["mutations"],
                                 tmp_path), \
            f"suite failed to detect removal of {control['name']}"
        assert _canonical_hash() == before_hash, \
            "canonical checkout changed across an isolated mutation control"

    # ---- false positives are NOT mutation proof (B4-CXR7U8-02) ----------
    def test_missing_node_id_is_not_detection(self, tmp_path):
        # baseline with a misspelled node id fails collection -> rc 2: the
        # protocol must refuse (MutationControlError), never report detection
        with pytest.raises(MutationControlError):
            mutation_detected(
                "tests/test_b4_cxr7_trusted_program.py::"
                "TestTrustedProgramRegistry::test_unknown_job_type_FAILS_"
                "closed_typo", MUTATION_CONTROLS[6]["mutations"], tmp_path)

    def test_collection_error_is_not_detection(self, tmp_path):
        # a mutant that breaks collection (syntax error) exits rc 2 and must
        # NOT be accepted as proof — returns False (with a clean checkout)
        control = dict(MUTATION_CONTROLS[6])
        syntax_mutant = {
            "path": "src/oce_control/representative_jobs.py",
            "pattern": "def program_for(job_type: str) -> str:",
            "mutate": lambda t: t.replace(
                "def program_for(job_type: str) -> str:\n    if job_type not in _PROGRAMS:",
                "def program_for(job_type: str) -> str:\n    if job_type not in _PROGRAMS  # syntax",
                1),
        }
        control["mutations"] = [syntax_mutant]
        before_hash = _canonical_hash()
        assert mutation_detected(control["node"], control["mutations"],
                                 tmp_path) is False
        assert _canonical_hash() == before_hash

    def test_syntax_error_mutant_is_not_detection(self, tmp_path):
        # invalid Python from a malformed mutation must never count
        iso = _build_isolated_tree(tmp_path)
        target = iso / "src/oce_control/representative_jobs.py"
        src = target.read_text(encoding="utf-8")
        target.write_text(src.replace("def program_for(job_type: str) -> str:",
                                      "def program_for(job_type: str -> :"), "utf-8")
        base = _run_pytest_isolated(
            iso, ["tests/test_b4_cxr7_trusted_program.py::"
                  "TestTrustedProgramRegistry::test_unknown_job_type_fails_closed"],
            iso / "junit.xml", 120)
                # a syntax error can surface as rc 2 (collection), rc 3 (internal)
        # or rc 4/5 (no tests) — the ONLY forbidden outcomes are 0 (all
        # passed) and 1 (ordinary test failure), which would look like proof
        assert base.returncode not in (0, 1)

    def test_replacement_pattern_absent_is_not_detection(self, tmp_path):
        # a pattern that does not exist exactly once must fail the protocol
        bad = [{"path": "src/oce_control/config_startup.py",
                "pattern": "def this_function_does_not_exist_anywhere():",
                "mutate": lambda t: t + "\n",
                }]
        before_hash = _canonical_hash()
        with pytest.raises(MutationControlError):
            mutation_detected(
                "tests/test_b4_cxr6_activation_capability.py::"
                "TestCXR6R1AuthenticatedActivationCapability::"
                "test_child_cannot_reissue_capability", bad, tmp_path)
        assert _canonical_hash() == before_hash

    def test_unrelated_failing_test_is_not_detection(self, tmp_path):
        # a mutant that only breaks an UNRELATED pinned node (while the
        # EXPECTED node still passes) exits rc 1 but is NOT attributable to
        # the removed defense — the protocol must return False. Here the
        # expected allowlisting node keeps failing closed, while adding a
        # rogue job type breaks the unrelated fixed-allowlist test.
        allowlist_control = MUTATION_CONTROLS[6]
        expected_node = allowlist_control["node"]
        unrelated_node = (
            "tests/test_b4_cxr7_trusted_program.py::"
            "TestTrustedProgramRegistry::test_supported_job_types_are_fixed_allowlist")
        rogue_mutant = {
            "path": "src/oce_control/representative_jobs.py",
            "pattern": "def supported_job_types() -> list[str]:\n    return list(_PROGRAMS)",
            "mutate": lambda t: t.replace(
                "def supported_job_types() -> list[str]:\n    return list(_PROGRAMS)",
                "def supported_job_types() -> list[str]:\n    return list(_PROGRAMS) + [\"b3.injected-rogue-type\"]  # MUTANT", 1),
        }
        before_hash = _canonical_hash()
        assert mutation_detected(
            expected_node, [rogue_mutant], tmp_path,
            extra_nodes=[unrelated_node]) is False
        assert _canonical_hash() == before_hash

    def test_subprocess_timeout_is_not_detection(self, tmp_path):
        # a mutant that hangs the pinned test must surface as TimeoutExpired
        # (never as proof) with a byte-identical canonical checkout
        control = dict(MUTATION_CONTROLS[6])
        hang_mutant = {
            "path": "src/oce_control/representative_jobs.py",
            "pattern": "def program_for(job_type: str) -> str:",
            "mutate": lambda t: t.replace(
                "def program_for(job_type: str) -> str:",
                "def program_for(job_type: str) -> str:\n"
                "    import time; time.sleep(500)  # MUTANT hang", 1),
        }
        control["mutations"] = [hang_mutant]
        before_hash = _canonical_hash()
        assert mutation_detected(control["node"], control["mutations"],
                                 tmp_path, timeout_s=20) is False
        assert _canonical_hash() == before_hash

    def test_subprocess_termination_is_not_detection(self, tmp_path):
        # a mutant that kills its own interpreter mid-run exits with a signal/
        # nonzero code that is NOT an attributable test failure -> False
        control = dict(MUTATION_CONTROLS[6])
        exit_mutant = {
            "path": "src/oce_control/representative_jobs.py",
            "pattern": "def program_for(job_type: str) -> str:",
            "mutate": lambda t: t.replace(
                "def program_for(job_type: str) -> str:",
                "def program_for(job_type: str) -> str:\n"
                "    import os; os._exit(7)  # MUTANT termination", 1),
        }
        control["mutations"] = [exit_mutant]
        before_hash = _canonical_hash()
        assert mutation_detected(control["node"], control["mutations"],
                                 tmp_path) is False
        assert _canonical_hash() == before_hash
