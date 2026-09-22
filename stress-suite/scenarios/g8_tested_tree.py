"""G8 — the tested tree: ONE owner (STRESS-G8ARCH3).

Three layers used to answer "which tree is this package tested against?" privately.
The emitter derived it, the pytest harness stamped its own with a different
fallback, and the audit entry point used live HEAD. At an archive commit those
answers disagree -- live HEAD IS the archive commit, while the derived tree is the
last code/test commit -- so `python scenarios/g8_run_audit.py <artifact>` refused
its own package at exactly the commit a reviewer is meant to run it at.

The rule itself is declared once, in `engine.g8_test_evidence`:

  * `TESTED_TREE_PATHS`   -- the code/test tree the baseline certifies;
  * `TESTED_TREE_GIT_ARGS` -- the Git query that resolves it.

This module is its only implementation. It lives outside the engine because the
engine may not shell out (`tests/test_no_mutation_surface.py`), and asking Git is
the whole point of the rule.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

from engine.g8_test_evidence import (TESTED_TREE_GIT_ARGS, TESTED_TREE_PATHS,
                                     UnverifiableTestEvidence)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_DIR.parent


def _git(args: Sequence[str], repo_root: Path) -> str:
    """A read-only Git query, run in the tree it describes."""
    proc = subprocess.run(["git", *args], cwd=str(repo_root),
                          capture_output=True, text=True, check=False)
    return proc.stdout.strip()


def derived_tested_tree(repo_root: Path = REPO_ROOT, *,
                        require_clean: bool = False) -> str:
    """The tree this package is tested against: the newest commit that changed code
    or tests.

    Because the rule names the CODE tree, a later commit that touches only docs or
    evidence does not move it, so a package stays re-derivable from any such commit
    rather than only from the one that happened to be HEAD.

    A pending change is not part of any commit, so `require_clean` refuses instead of
    publishing: a package must never claim a tree that is not the tree that was
    tested. The cited artifact is deliberately NOT part of that cleanliness rule --
    it is regenerated immediately before emission, and its bytes are bound by the
    citation check instead.

    A repository with no commit touching the code paths yet falls back to HEAD. That
    fallback lives here, once: the previous revision had two derivations with
    different fallbacks, which is how the ledger and the harness could disagree.
    """
    derived = _git(TESTED_TREE_GIT_ARGS, repo_root)
    if not derived:
        derived = _git(("rev-parse", "HEAD"), repo_root)
    if not require_clean:
        return derived
    if not derived:
        raise UnverifiableTestEvidence(
            "the tested tree cannot be derived: no commit touching "
            f"{list(TESTED_TREE_PATHS)} resolves in {repo_root}")
    dirty = _git(("status", "--porcelain", "--", *TESTED_TREE_PATHS), repo_root)
    if dirty:
        raise UnverifiableTestEvidence(
            "refusing to publish a package for a dirty tree: the code or tests "
            "have uncommitted changes, so the tree being archived is not the tree "
            f"that was tested\n{dirty}")
    return derived
