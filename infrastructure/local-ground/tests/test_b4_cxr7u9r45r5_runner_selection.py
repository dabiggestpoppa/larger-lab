#!/usr/bin/env python3
"""B4-CXR7U9R45R5 — authoritative-runner selection proofs for the R45 modules.

The mandatory runner must select ALL new R45 proof modules; the collected
node ids must be unique; every skip these modules can produce must be
declared (symlink creation on Windows, POSIX permission bits), so the Linux
mandatory run has ZERO unexplained skips (mission 7); and every suite
argument on the pytest selection line must be an expanded shell variable.
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

R45_MODULES = {
    "R45R2_CLAIM_PATH_ADMISSION_TEST": "test_b4_cxr7u9r45r2_claim_path_admission.py",
    "R45R3_SELECTOR_CLASSIFICATION_LAW_TEST":
        "test_b4_cxr7u9r45r3_selector_classification_law.py",
    "R45R5_RUNNER_SELECTION_TEST":
        "test_b4_cxr7u9r45r5_runner_selection.py",
}

# every skip these modules can emit, with the reason it is platform-gated
PLATFORM_GATED = {
    "test_b4_cxr7u9r45r2_claim_path_admission.py": (
        2, "symlink creation may be privilege-gated on Windows"),
    "test_b4_cxr7u9r45r3_selector_classification_law.py": (0, None),
    "test_b4_cxr7u9r45r5_runner_selection.py": (0, None),
}


@pytest.mark.parametrize("var,module", sorted(R45_MODULES.items()))
def test_runner_selects_the_r45_module(var, module):
    source = RUNNER.read_text(encoding="utf-8")
    assert f"{var}=" in source, f"runner must define {var}"
    assert module in source, (
        f"runner must select {module} in its pytest invocation")
    # every earlier mandatory suite stays selected
    for retained in ("R44_ATOMIC_CLAIM_PUBLICATION_TEST",
                     "R44X2_CLAIM_TEMPORARY_LIVENESS_TEST",
                     "R43_LOCK_ROLLBACK_RESUME_TEST",
                     "CRASH_COHERENCE_TEST"):
        assert retained in source, retained


@pytest.mark.parametrize("module", sorted(R45_MODULES.values()))
def test_r45_module_collects_unique_node_ids(module):
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


@pytest.mark.parametrize("module", sorted(R45_MODULES.values()))
def test_r45_module_declares_every_platform_gate_it_uses(module):
    """A skip that exists in the module must be a DECLARED symlink/POSIX
    gate, so Linux CI runs everything with zero unexplained skips."""
    limit, _reason = PLATFORM_GATED[module]
    source = (TESTS / module).read_text(encoding="utf-8")
    # split literals so this module's own scan code cannot self-match when
    # it is the module under scan
    skips = source.count("pytest." + "skip(") + source.count(
        "pytest." + "mark.skipif(")
    assert skips <= limit, (
        f"{module}: {skips} skip sites exceed the {limit} declared gates")


def test_pytest_selection_expands_every_suite_variable():
    """Every suite argument on the authoritative pytest invocation line must
    be a shell variable expansion inside quotes; a bare unexpanded token
    would silently hand pytest a nonexistent filename (regression class
    caught pre-push: a suite variable missing its dollar prefix)."""
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
