#!/usr/bin/env python3
"""B4-CXR7U9R46R7 — authoritative-runner selection proofs for the R46 modules.

The mandatory runner must select ALL R46 proof modules while retaining every
earlier mandatory suite; the collected node ids must be unique; every skip the
R46 modules can produce must be a DECLARED platform gate (all of them are
Windows-only, so the Linux mandatory run executes every R46 proof with ZERO
skips); and every suite argument on the pytest selection line must be an
expanded shell variable.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import pgrec  # noqa: F401

CLI = Path(pgrec.__file__)
TESTS = CLI.parent.parent / "tests"
RUNNER = CLI.parent / "run-validation.sh"

R46_MODULES = {
    "R46R5_SELECTOR_REPLACEMENT_PROOFS_TEST":
        "test_b4_cxr7u9r46r5_selector_replacement_proofs.py",
    "R46R7_RUNNER_SELECTION_TEST":
        "test_b4_cxr7u9r46r7_runner_selection.py",
}

# every skip site in the R46 modules is a WINDOWS-only gate: on Linux every
# mandatory R46 proof executes (zero skips).
PLATFORM_GATED = {
    "test_b4_cxr7u9r46r5_selector_replacement_proofs.py": (
        3, "symlink creation, POSIX share-mode replacement and hard links "
           "are platform-gated; all three gates are Windows-only"),
    "test_b4_cxr7u9r46r7_runner_selection.py": (0, None),
}


@pytest.mark.parametrize("var,module", sorted(R46_MODULES.items()))
def test_runner_selects_the_r46_module(var, module):
    source = RUNNER.read_text(encoding="utf-8")
    assert f"{var}=" in source, f"runner must define {var}"
    assert module in source, (
        f"runner must select {module} in its pytest invocation")
    # every earlier mandatory suite stays selected (append-only runner law)
    for retained in ("R45R2_CLAIM_PATH_ADMISSION_TEST",
                     "R45R3_SELECTOR_CLASSIFICATION_LAW_TEST",
                     "R45R5_RUNNER_SELECTION_TEST",
                     "R44_ATOMIC_CLAIM_PUBLICATION_TEST",
                     "R44X2_CLAIM_TEMPORARY_LIVENESS_TEST",
                     "R43_LOCK_ROLLBACK_RESUME_TEST",
                     "CRASH_COHERENCE_TEST",
                     "SHELL_COMMIT_LAW_TEST",
                     "COMMIT_BOUNDARY_TEST",
                     "TRANSITION_AUTHORITY_TEST",
                     "RECOVERY_AUTHORITY_TEST"):
        assert retained in source, retained


@pytest.mark.parametrize("module", sorted(R46_MODULES.values()))
def test_r46_module_collects_unique_node_ids(module):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         str(TESTS / module)],
        cwd=str(CLI.parent.parent), env=env, capture_output=True, text=True,
        timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    nodeids = [line.strip() for line in result.stdout.splitlines()
               if "::" in line]
    assert nodeids, f"{module} collected nothing"
    assert len(nodeids) == len(set(nodeids)), f"{module}: duplicate node ids"


@pytest.mark.parametrize("module", sorted(R46_MODULES.values()))
def test_r46_module_declares_every_platform_gate_it_uses(module):
    """A skip that exists in the module must be a DECLARED platform gate, so
    Linux CI runs everything with zero unexplained skips."""
    limit, _reason = PLATFORM_GATED[module]
    source = (TESTS / module).read_text(encoding="utf-8")
    # split literals so this module's own scan code cannot self-match when
    # it is the module under scan
    skips = source.count("pytest." + "skip(") + source.count(
        "pytest." + "mark.skipif(")
    assert skips <= limit, (
        f"{module}: {skips} skip sites exceed the {limit} declared gates")


def test_r46_weakened_controls_are_selected_proofs_not_skips():
    """The executable weakened controls run on EVERY platform (child
    processes): they are never platform-gated, so the Linux mandatory run
    demonstrates the old reader accepting a replacement."""
    source = (TESTS /
              "test_b4_cxr7u9r46r5_selector_replacement_proofs.py"
              ).read_text(encoding="utf-8")
    for control in ("test_weakened_path_then_open_accepts_a_boundary_replacement",
                    "test_weakened_two_read_decision_accepts_a_branch_swap"):
        assert f"def {control}(" in source, control
        # no platform gate decorates the weakened controls
        idx = source.index(f"def {control}(")
        preceding = source[:idx].rstrip().splitlines()[-2:]
        for ln in preceding:
            assert "skipif" not in ln and "skip(" not in ln, (
                f"{control} must not be platform-gated: {ln!r}")


def test_pytest_selection_expands_every_suite_variable():
    """Every suite argument on the authoritative pytest invocation line must
    be a shell variable expansion inside quotes (R45R5 regression class)."""
    source = RUNNER.read_text(encoding="utf-8")
    pytest_lines = [ln for ln in source.splitlines()
                    if ln.lstrip().startswith("python3 -m pytest")]
    assert len(pytest_lines) == 1, "exactly one pytest invocation expected"
    inv = pytest_lines[0]
    backslash = chr(92)
    for token in inv.replace("python3 -m pytest", "").split():
        if token == backslash or token.startswith("-"):
            continue  # line-continuation backslash or pytest flag
        assert token.startswith('"$') and token.endswith('"'), (
            f"unexpanded pytest argument on the selection line: {token!r}")
