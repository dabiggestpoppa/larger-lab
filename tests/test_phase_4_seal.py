"""
Deterministic tests for the Phase 4 final seal (truthful gate).
CR-P4-FACTOR-SEAL-02

These prove the gate is machine-derived and NOT only file-existence based.
They construct corrupted / altered inputs and assert the gate FAILS, which a
file-existence-only gate would never do.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases.phase_4_gate import (
    Phase4GateV2,
    EXPECT_INCIDENCE_RANK,
    EXPECT_ZERO_SUM_TOL,
    EXPECT_INPUT_ROWS,
    EXPECT_FACTOR_ROWS,
)
from capital_routing.phases.phase_4_factors import (
    build_incidence_matrix,
    incidence_rank,
)
from capital_routing.phases.phase_3_panel import PHASE2_SYMBOLS

BASE = Path(__file__).resolve().parents[1]
P3 = BASE / "artifacts" / "phase_03"
P4 = BASE / "artifacts" / "phase_04"
EXPECTED_SHA = json.loads(
    (P4 / "p3_preflight_audit.json").read_text(encoding="utf-8")
)["input_panel_sha256"]


class TestGateChecks:
    def test_incidence_rank_is_4(self):
        _, A = build_incidence_matrix(PHASE2_SYMBOLS)
        assert incidence_rank(A) == 4

    def test_zero_sum_constraint_exact(self):
        factors = pd.read_parquet(P4 / "currency_factors_h1.parquet")
        cols = [f"{c}_factor" for c in ["EUR", "GBP", "USD", "CHF", "JPY"]]
        assert factors[cols].sum(axis=1).abs().max() <= 1e-9

    def test_row_counts_match_expectations(self):
        panel = pd.read_parquet(P3 / "h1_strict_common_panel.parquet")
        factors = pd.read_parquet(P4 / "currency_factors_h1.parquet")
        assert len(panel) == EXPECT_INPUT_ROWS
        assert len(factors) == EXPECT_FACTOR_ROWS

    def test_gate_fails_if_input_hash_wrong(self, tmp_path):
        # Corrupt the expected input sha -> gate must fail even though files exist
        gate = Phase4GateV2(P3, P4, "deadbeef" * 8, "p3c", "p4c", BASE, run_tests=False)
        res = gate.check_input_hash()
        assert res["valid"] is False
        assert "deadbeef" in res["expected"]

    def test_gate_detects_bad_row_reconciliation(self, tmp_path):
        # Create a factor frame with a mismatched row count in a cloned dir
        p4fake = tmp_path / "phase_04"
        p4fake.mkdir(parents=True)
        factors = pd.read_parquet(P4 / "currency_factors_h1.parquet")
        bad = factors.iloc[:-5]  # wrong row count
        bad.to_parquet(p4fake / "currency_factors_h1.parquet")
        gate = Phase4GateV2(P3, p4fake, EXPECTED_SHA, "p3", "p4", BASE, run_tests=False)
        res = gate.check_row_reconciliation()
        assert res["valid"] is False

    def test_zero_sum_detects_violation(self, tmp_path):
        p4fake = tmp_path / "phase_04"
        p4fake.mkdir(parents=True)
        factors = pd.read_parquet(P4 / "currency_factors_h1.parquet")
        factors["EUR_factor"] = factors["EUR_factor"] + 1.0  # break zero-sum
        factors.to_parquet(p4fake / "currency_factors_h1.parquet")
        gate = Phase4GateV2(P3, p4fake, EXPECTED_SHA, "p3", "p4", BASE, run_tests=False)
        res = gate.check_zero_sum()
        assert res["valid"] is False

    def test_gate_not_purely_file_existence(self):
        # A file-existence-only gate would PASS even with a bogus input hash.
        # This gate must report the hash invalid.
        gate = Phase4GateV2(P3, P4, "0" * 64, "p3", "p4", BASE, run_tests=False)
        ev = gate.evaluate()
        assert ev["proven"]["phase3_input_hash"] is False
        assert ev["gate_passed"] is False
        assert "phase3_input_hash" in ev["failures"]


class TestSealArtifacts:
    def test_no_lookahead_audit_passes(self):
        aud = json.loads((P4 / "no_lookahead_audit.json").read_text(encoding="utf-8"))
        assert aud["passes"] is True
        assert len(aud["rows"]) >= 3

    def test_invariant_audit_passes(self):
        aud = json.loads((P4 / "factor_invariant_audit.json").read_text(encoding="utf-8"))
        assert aud["passes"] is True
        assert aud["max_abs_zero_sum_error"] <= 1e-9

    def test_reconstruction_classified(self):
        aud = json.loads((P4 / "reconstruction_classification.json").read_text(encoding="utf-8"))
        for p in ["EURGBP", "EURJPY", "EURCHF"]:
            assert aud["pairs"][p]["classification"] == "HIGH_RESIDUAL_INFORMATION"

    def test_output_hash_manifest_complete(self):
        man = json.loads((P4 / "output_hash_manifest.json").read_text(encoding="utf-8"))
        for f in ["currency_factors_h1.parquet", "currency_factors_h4.parquet",
                  "currency_factors_d1.parquet", "pair_residuals_h1.parquet",
                  "factor_features_h1.parquet"]:
            assert man[f] and len(man[f]) == 64

    def test_gate_v2_clears_phase5(self):
        gate = json.loads((P4 / "phase_4_gate_v2.json").read_text(encoding="utf-8"))
        assert gate["gate_passed"] is True
        assert gate["phase_5_cleared"] is True
        assert all(gate["proven"][k] for k in
                   ["zero_sum", "no_lookahead", "determinism", "tests_passed"])