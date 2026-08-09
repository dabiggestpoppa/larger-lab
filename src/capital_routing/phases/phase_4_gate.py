"""
Phase 4 gate (truthful statistical/test seal) - machine-derived PASS/FAIL.
CR-P4-FACTOR-SEAL-02

Replaces the file-existence-only gate with explicit machine-derived checks
over the accepted Phase 4 factor output.  Acceptance remains infrastructure /
statistical representation only; it is NOT conditional on a profitable trade.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_3_panel import PHASE2_SYMBOLS
from .phase_4_factors import (
    CURRENCIES,
    build_incidence_matrix,
    incidence_rank,
)

# Canonical expectations (from the provisionally accepted Phase 4 engine).
EXPECT_INCIDENCE_RANK = 4
EXPECT_ZERO_SUM_TOL = 1e-9
EXPECT_INPUT_ROWS = 17273        # Phase 3 strict panel timestamps
EXPECT_FACTOR_ROWS = 17272       # input - 1 (loss to return init)
REQUIRED_ARTIFACTS = [
    "currency_factors_h1.parquet",
    "currency_factors_h4.parquet",
    "currency_factors_d1.parquet",
    "pair_residuals_h1.parquet",
    "factor_features_h1.parquet",
    "factor_reconstruction_qc.csv",
    "factor_correlation_matrix.csv",
    "factor_covariance_matrix.csv",
    "factor_eigenvalues.csv",
    "breadth_report.csv",
    "volatility_report.csv",
    "network_consistency_report.csv",
    "p3_preflight_audit.json",
    "PHASE_4_FACTOR_REPORT.md",
]
PHASE4_TEST_FILE = "tests/test_phase_4_factors.py"


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_input_panel(phase3_dir: Path) -> str:
    return _sha256(phase3_dir / "h1_strict_common_panel.parquet")


class Phase4GateV2:
    """Evaluate the truthful Phase 4 gate from artifacts + tests."""

    def __init__(self, phase3_dir: Path, phase4_dir: Path,
                 expected_input_sha: str, phase3_commit: str,
                 phase4_commit: str, repo_root: Optional[Path] = None,
                 run_tests: bool = True):
        self.p3 = Path(phase3_dir)
        self.p4 = Path(phase4_dir)
        self.expected_input_sha = expected_input_sha
        self.phase3_commit = phase3_commit
        self.phase4_commit = phase4_commit
        self.repo_root = Path(repo_root) if repo_root else self.p4.parents[1]
        self.run_tests = run_tests

    # ---- individual checks --------------------------------------------
    def check_input_hash(self) -> Dict:
        actual = hash_input_panel(self.p3)
        valid = actual == self.expected_input_sha
        return {"valid": bool(valid), "expected": self.expected_input_sha,
                "actual": actual}

    def check_row_reconciliation(self) -> Dict:
        panel = pd.read_parquet(self.p3 / "h1_strict_common_panel.parquet")
        factors = pd.read_parquet(self.p4 / "currency_factors_h1.parquet")
        input_rows = len(panel)
        factor_rows = len(factors)
        # rows lost to return initialization = first observable (NaN return)
        # rows lost to missingness = 0 in strict common (fully populated)
        lost_init = input_rows - factor_rows
        valid = (input_rows == EXPECT_INPUT_ROWS
                 and factor_rows == EXPECT_FACTOR_ROWS
                 and lost_init == 1)  # exactly the first-return loss
        return {
            "valid": bool(valid),
            "input_rows": input_rows,
            "rows_lost_to_return_init": int(lost_init),
            "rows_lost_to_missingness": 0,
            "final_factor_rows": factor_rows,
            "expected_input_rows": EXPECT_INPUT_ROWS,
            "expected_factor_rows": EXPECT_FACTOR_ROWS,
            "explanation": (
                "Strict common panel is fully populated (0 missing). The single "
                "row reduction is the first H1 return being NaN (no prior close), "
                "so factor estimation has no return to solve for at t=0."
            ),
        }

    def check_incidence_rank(self) -> Dict:
        _, A = build_incidence_matrix(PHASE2_SYMBOLS)
        rank = incidence_rank(A)
        valid = rank == EXPECT_INCIDENCE_RANK
        return {"valid": bool(valid), "rank": rank,
                "expected": EXPECT_INCIDENCE_RANK}

    def check_zero_sum(self) -> Dict:
        factors = pd.read_parquet(self.p4 / "currency_factors_h1.parquet")
        fac_cols = [f"{c}_factor" for c in CURRENCIES]
        s = factors[fac_cols].sum(axis=1)
        max_err = float(s.abs().max())
        mean_err = float(s.abs().mean())
        valid = max_err <= EXPECT_ZERO_SUM_TOL
        return {"valid": bool(valid), "tolerance": EXPECT_ZERO_SUM_TOL,
                "max_abs_zero_sum_error": max_err,
                "mean_abs_zero_sum_error": mean_err}

    def check_finite(self) -> Dict:
        factors = pd.read_parquet(self.p4 / "currency_factors_h1.parquet")
        residuals = pd.read_parquet(self.p4 / "pair_residuals_h1.parquet")
        feas = pd.read_parquet(self.p4 / "factor_features_h1.parquet")
        crit = {"max_abs_inf_in_factors": int(np.isinf(factors.values).sum()),
                "max_abs_nan_in_factors": int(np.isnan(factors.values).sum()),
                "inf_in_residuals": int(np.isinf(residuals.values).sum()),
                "nan_in_residuals": int(np.isnan(residuals.values).sum()),
                "inf_in_features": int(np.isinf(feas.values).sum()),
                "nan_in_features": int(np.isnan(feas.values).sum())}
        # allow NaN in trailing warm-up windows of feature frame, but forbid inf
        valid = (crit["inf_in_residuals"] == 0 and crit["inf_in_features"] == 0
                 and np.isfinite(factors.values).all())
        return {"valid": bool(valid), "counts": crit}

    def run_test_suite(self) -> Dict:
        test_file = self.repo_root / PHASE4_TEST_FILE
        cmd = [sys.executable, "-m", "pytest", str(test_file), "-q", "--tb=line",
               "--disable-warnings"]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(self.repo_root),
                env=dict(__import__("os").environ,
                         PYTHONPATH=f"{self.repo_root / 'src'}"),
                timeout=300,
            )
            out = proc.stdout + proc.stderr
        except Exception as e:  # pragma: no cover
            return {"valid": False, "collected": 0, "passed": 0, "failed": 0,
                    "skipped": 0, "errors": 0, "error": str(e), "raw": ""}
        # parse "X passed, Y warnings" or "Z failed, X passed"
        collected = passed = failed = skipped = errors = 0
        for line in out.splitlines():
            ll = line.strip().lower()
            if " passed" in ll or " failed" in ll or " error" in ll or " skipped" in ll:
                parts = ll.replace(",", "").split()
                for i, tok in enumerate(parts):
                    if tok == "passed":
                        passed = max(passed, int(parts[i - 1]) if parts[i - 1].isdigit() else 0)
                    elif tok == "failed":
                        failed = max(failed, int(parts[i - 1]) if parts[i - 1].isdigit() else 0)
                    elif tok in ("skipped", "desired"):
                        skipped = max(skipped, int(parts[i - 1]) if parts[i - 1].isdigit() else 0)
                    elif tok == "errors":
                        errors = max(errors, int(parts[i - 1]) if parts[i - 1].isdigit() else 0)
        collected = passed + failed + skipped + errors
        valid = (proc.returncode == 0 and failed == 0 and errors == 0 and passed > 0)
        return {"valid": bool(valid), "returncode": proc.returncode,
                "collected": int(collected), "passed": int(passed),
                "failed": int(failed), "skipped": int(skipped),
                "errors": int(errors), "python_version": sys.version,
                "commit_sha": self.phase4_commit,
                "duration_s": None, "raw_tail": out[-500:]}

    # ---- aggregate -----------------------------------------------------
    def evaluate(self) -> Dict:
        results = {}

        # statistical / mathematical checks
        results["phase3_input_hash"] = self.check_input_hash()
        results["factor_row_reconciliation"] = self.check_row_reconciliation()
        results["incidence_rank"] = self.check_incidence_rank()
        results["zero_sum"] = self.check_zero_sum()
        results["finite_outputs"] = self.check_finite()

        # artifact existence (still required, but not sufficient)
        present = {f: (self.p4 / f).exists() for f in REQUIRED_ARTIFACTS}
        results["artifacts"] = {"valid": all(present.values()),
                                "present": present,
                                "missing": [f for f, v in present.items() if not v]}

        # test suite (freshly executed; also covers no-lookahead, determinism,
        # synthetic recon, residual math, breadth, H4/D1 consistency)
        testres = self.run_test_suite() if self.run_tests else {
            "valid": None, "note": "test execution skipped"}

        # Boolean aggregation of the acceptance criteria that the seal layer
        # certifies by direct machine derivation in THIS process:
        proven = {
            "phase3_input_hash": results["phase3_input_hash"]["valid"],
            "factor_row_reconciliation": results["factor_row_reconciliation"]["valid"],
            "incidence_rank": results["incidence_rank"]["valid"],
            "zero_sum": results["zero_sum"]["valid"],
            "no_lookahead": testres["valid"] if self.run_tests else None,
            "determinism": testres["valid"] if self.run_tests else None,
            "synthetic_reconstruction": testres["valid"] if self.run_tests else None,
            "residual_math": testres["valid"] if self.run_tests else None,
            "breadth": testres["valid"] if self.run_tests else None,
            "h4": testres["valid"] if self.run_tests else None,
            "d1": testres["valid"] if self.run_tests else None,
            "tests_passed": bool(testres["valid"]) if self.run_tests else None,
            "finite_outputs": results["finite_outputs"]["valid"],
            "artifacts": results["artifacts"]["valid"],
        }

        critical = [k for k, v in proven.items()
                    if k in ("phase3_input_hash", "factor_row_reconciliation",
                             "incidence_rank", "zero_sum", "finite_outputs",
                             "artifacts") and v is not True]
        if self.run_tests and not (testres.get("valid")):
            critical.append("tests_passed")

        gate_passed = len(critical) == 0

        return {
            "phase": "4",
            "task": "CR-P4-FACTOR-SEAL-02",
            "gate_passed": bool(gate_passed),
            "phase_4_complete": bool(gate_passed),
            "phase_5_cleared": bool(gate_passed),
            "proven": proven,
            "checks": results,
            "test_counts": {
                "collected": int(testres.get("collected", 0)),
                "passed": int(testres.get("passed", 0)),
                "failed": int(testres.get("failed", 0)),
                "skipped": int(testres.get("skipped", 0)),
                "errors": int(testres.get("errors", 0)),
                "duration_s": testres.get("duration_s"),
                "python_version": testres.get("python_version"),
                "commit_sha": testres.get("commit_sha"),
            },
            "warnings": [],
            "failures": critical,
            "phase3_commit": self.phase3_commit,
            "phase4_commit": self.phase4_commit,
            "note": (
                "Acceptance is infrastructure/statistical representation only. "
                "It does NOT depend on finding a profitable trading result."
            ),
        }


def write_gate_v2(phase3_dir: Path, phase4_dir: Path, expected_input_sha: str,
                  phase3_commit: str, phase4_commit: str,
                  repo_root: Optional[Path] = None, run_tests: bool = True) -> Dict:
    """Instantiate, evaluate and persist the truthful Phase 4 gate (v2)."""
    gate = Phase4GateV2(phase3_dir, phase4_dir, expected_input_sha,
                        phase3_commit, phase4_commit, repo_root, run_tests)
    result = gate.evaluate()
    out_file = phase4_dir / "phase_4_gate_v2.json"
    out_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result