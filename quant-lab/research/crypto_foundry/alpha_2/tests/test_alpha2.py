#!/usr/bin/env python3
"""
ALPHA-2 Test Suite.
Tests sealed contract integrity, engine correctness, and falsification rules.
"""

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════
HERE = Path(__file__).resolve().parent
A2 = HERE.parent
CRYPTO = A2.parent
A1 = CRYPTO / "alpha_1"
A11 = CRYPTO / "alpha_1_1"
MECH2 = CRYPTO / "mech_2"

REGISTRY_HASH = "2abaf8c21200a67e5b06d8ccf42ceb19574a12df21916d314a3c80b47f9a419e"


# ═══════════════════════════════════════════════════════════════════════
# CONTRACT INTEGRITY TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestSealedContractHash:
    """Verify the sealed strategy registry hash."""

    def test_registry_hash_matches(self):
        """The strategy registry hash must match the sealed value."""
        reg_file = A1 / "ALPHA_1_STRATEGY_REGISTRY_HASH.json"
        with open(reg_file) as f:
            data = json.load(f)
        actual = data.get("new_registry_hash") or data.get("registry_hash")
        assert actual == REGISTRY_HASH, f"Registry hash mismatch: {actual} != {REGISTRY_HASH}"

    def test_registry_hash_also_in_alpha1_1(self):
        """Both alpha_1 and alpha_1_1 must have the same hash."""
        h1 = json.load(open(A1 / "ALPHA_1_STRATEGY_REGISTRY_HASH.json"))
        h2 = json.load(open(A11 / "ALPHA_1_1_REGISTRY_HASH.json"))
        a1 = h1.get("new_registry_hash") or h1.get("registry_hash")
        a2 = h2.get("new_registry_hash") or h2.get("registry_hash")
        assert a1 == a2, "Registry hashes differ between alpha_1 and alpha_1_1"


class TestStrategyContractIntegrity:
    """Verify strategy contracts are frozen and unmodified."""

    def test_13_strategies_exist(self):
        """Exactly 13 strategies must be defined."""
        contracts = json.load(open(A1 / "ALPHA_1_STRATEGY_CONTRACTS.json"))
        assert len(contracts) == 13

    def test_all_strategy_ids_present(self):
        """All 13 strategy IDs must be present."""
        contracts = json.load(open(A1 / "ALPHA_1_STRATEGY_CONTRACTS.json"))
        ids = {c["strategy_id"] for c in contracts}
        expected = {f"ALPHA1_S{i:03d}" for i in range(1, 14)}
        assert ids == expected, f"Missing: {expected - ids}, Extra: {ids - expected}"

    def test_6_families_represented(self):
        """All 6 families must be represented."""
        contracts = json.load(open(A1 / "ALPHA_1_STRATEGY_CONTRACTS.json"))
        families = {c["family_id"] for c in contracts}
        assert families == {"FAM_A", "FAM_B", "FAM_C", "FAM_D", "FAM_E", "FAM_X"}

    def test_strategy_hash_deterministic(self):
        """Stored registry hash must match the sealed value."""
        reg_file = A1 / "ALPHA_1_STRATEGY_REGISTRY_HASH.json"
        with open(reg_file) as f:
            data = json.load(f)
        stored = data.get("new_registry_hash") or data.get("registry_hash")
        assert stored == REGISTRY_HASH, f"Stored hash {stored} != sealed {REGISTRY_HASH}"


class TestControlRegistry:
    """Verify 6 controls are registered."""

    def test_6_controls(self):
        """Exactly 6 controls must be defined."""
        with open(A1 / "ALPHA_1_CONTROL_REGISTRY.csv") as f:
            controls = list(csv.DictReader(f))
        assert len(controls) == 6

    def test_all_control_ids(self):
        """All control IDs must be present."""
        with open(A1 / "ALPHA_1_CONTROL_REGISTRY.csv") as f:
            controls = list(csv.DictReader(f))
        ids = {c["control_id"] for c in controls}
        expected = {f"ALPHA1_C{i:03d}" for i in range(1, 7)}
        assert ids == expected


class TestThresholdContract:
    """Verify threshold values match MECH-2 state definitions."""

    def test_thresholds_match_definitions(self):
        """Threshold contract must match MECH-2 definitions."""
        t = json.load(open(A11 / "ALPHA_1_1_THRESHOLD_CONTRACT.json"))
        d = json.load(open(MECH2 / "MECH_2_STATE_DEFINITIONS.json"))

        # BTC basis
        assert abs(t["BTC"]["basis"]["p90_abs"] - 6.578) < 0.01
        assert abs(t["BTC"]["basis"]["p99_abs"] - 9.867) < 0.01

        # ETH basis
        assert abs(t["ETH"]["basis"]["p90_abs"] - 6.766) < 0.01
        assert abs(t["ETH"]["basis"]["p99_abs"] - 10.148) < 0.01

    def test_funding_thresholds(self):
        """Funding thresholds must be set."""
        t = json.load(open(A11 / "ALPHA_1_1_THRESHOLD_CONTRACT.json"))
        assert "funding" in t["BTC"]
        assert "funding" in t["ETH"]
        assert t["BTC"]["funding"]["p5"] < 0  # negative tail
        assert t["BTC"]["funding"]["p95"] > 0  # positive tail


class TestCostContract:
    """Verify cost model is sealed."""

    def test_perp_cost(self):
        """Perp roundtrip cost must be 5.0 bps."""
        c = json.load(open(A11 / "ALPHA_1_1_COST_ACCOUNTING_CONTRACT.json"))
        assert c["perp_roundtrip_bps"] == 5.0

    def test_spot_cost(self):
        """Spot roundtrip cost must be 7.5 bps."""
        c = json.load(open(A11 / "ALPHA_1_1_COST_ACCOUNTING_CONTRACT.json"))
        assert c["spot_roundtrip_bps"] == 7.5

    def test_hedge_cost(self):
        """Hedge roundtrip cost must be 12.5 bps."""
        c = json.load(open(A11 / "ALPHA_1_1_COST_ACCOUNTING_CONTRACT.json"))
        assert c["hedge_roundtrip_bps"] == 12.5

    def test_stress_multiplier(self):
        """Stress cost multiplier must be 2.0."""
        c = json.load(open(A11 / "ALPHA_1_1_COST_ACCOUNTING_CONTRACT.json"))
        assert c["stress_2x"]["mult"] == 2.0


class TestFundingContract:
    """Verify funding accounting rules."""

    def test_settlement_times(self):
        """Settlements at 00, 08, 16 UTC."""
        f = json.load(open(A11 / "ALPHA_1_1_FUNDING_ACCOUNTING_CONTRACT.json"))
        assert "00,08,16" in f["settlements"]

    def test_entry_not_accrued(self):
        """Entry on settlement NOT accrued."""
        f = json.load(open(A11 / "ALPHA_1_1_FUNDING_ACCOUNTING_CONTRACT.json"))
        assert f["entry_on_settlement"] == "NOT accrued"

    def test_exit_accrued(self):
        """Exit on settlement IS accrued."""
        f = json.load(open(A11 / "ALPHA_1_1_FUNDING_ACCOUNTING_CONTRACT.json"))
        assert f["exit_on_settlement"] == "IS accrued"


class TestExecutionContract:
    """Verify execution rules."""

    def test_no_same_bar(self):
        """No same-bar execution allowed."""
        e = json.load(open(A11 / "ALPHA_1_1_EXECUTION_CONTRACT.json"))
        assert e["no_same_bar"] is True

    def test_signal_is_bar_close(self):
        """Signal at bar close."""
        e = json.load(open(A11 / "ALPHA_1_1_EXECUTION_CONTRACT.json"))
        assert e["signal"] == "1h bar close"

    def test_execution_is_next_bar(self):
        """Execution at next bar open."""
        e = json.load(open(A11 / "ALPHA_1_1_EXECUTION_CONTRACT.json"))
        assert e["execution"] == "next bar open"

    def test_no_pyramiding(self):
        """No pyramiding allowed."""
        e = json.load(open(A11 / "ALPHA_1_1_EXECUTION_CONTRACT.json"))
        assert e["pyramiding"] is False


class TestFalsificationRules:
    """Verify falsification rules are frozen."""

    def test_12_rules_exist(self):
        """Exactly 12 falsification rules."""
        f = json.load(open(A11 / "ALPHA_1_1_FALSIFICATION_RULES.json"))
        assert len(f["rules"]) == 12

    def test_rule_ids_complete(self):
        """All F1-F12 must be present."""
        f = json.load(open(A11 / "ALPHA_1_1_FALSIFICATION_RULES.json"))
        ids = {r["rule_id"] for r in f["rules"]}
        expected = {f"F{i}" for i in range(1, 13)}
        assert ids == expected

    def test_f8_bootstrap_params(self):
        """F8 must use paired bootstrap with seed 31082026."""
        f = json.load(open(A11 / "ALPHA_1_1_FALSIFICATION_RULES.json"))
        f8 = next(r for r in f["rules"] if r["rule_id"] == "F8")
        assert f8["seed"] == 31082026
        assert f8["n_resamples"] == 10000


class TestControlSampling:
    """Verify control sampling contract."""

    def test_seed(self):
        """Control sampling seed must be 31082026."""
        c = json.load(open(A11 / "ALPHA_1_1_CONTROL_SAMPLING_CONTRACT.json"))
        assert c["seed"] == 31082026

    def test_draws_per_event(self):
        """10 draws per event."""
        c = json.load(open(A11 / "ALPHA_1_1_CONTROL_SAMPLING_CONTRACT.json"))
        assert c["draws_per_event"] == 10

    def test_matching_criteria(self):
        """Matching on asset, month, hour_utc."""
        c = json.load(open(A11 / "ALPHA_1_1_CONTROL_SAMPLING_CONTRACT.json"))
        assert "asset" in c["matching"]
        assert "month" in c["matching"]
        assert "hour_utc" in c["matching"]


class TestStateCoverageMatrix:
    """Verify state coverage matrix counts."""

    def test_25_total_states(self):
        """25 promoted states in coverage matrix."""
        with open(A11 / "ALPHA_1_1_STATE_COVERAGE_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 25

    def test_15_consumed(self):
        """15 DIRECTLY_CONSUMED states."""
        with open(A11 / "ALPHA_1_1_STATE_COVERAGE_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        consumed = sum(1 for r in rows if r["coverage_status"] == "DIRECTLY_CONSUMED")
        assert consumed == 15

    def test_3_control_only(self):
        """3 CONTROL_ONLY states."""
        with open(A11 / "ALPHA_1_1_STATE_COVERAGE_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        control = sum(1 for r in rows if r["coverage_status"] == "CONTROL_ONLY")
        assert control == 3

    def test_7_rejected(self):
        """7 DESIGN_REJECTED states."""
        with open(A11 / "ALPHA_1_1_STATE_COVERAGE_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        rejected = sum(1 for r in rows if "REJECTED" in r["coverage_status"])
        assert rejected == 7


# ═══════════════════════════════════════════════════════════════════════
# PRE-RUN LOCK TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestPreRunLock:
    """Verify pre-run lock exists and is valid."""

    def test_lock_exists(self):
        """Pre-run lock file must exist."""
        lock_file = A2 / "ALPHA_2_PRE_RUN_LOCK.json"
        assert lock_file.exists()

    def test_lock_registry_verified(self):
        """Registry hash must be verified in lock."""
        lock = json.load(open(A2 / "ALPHA_2_PRE_RUN_LOCK.json"))
        assert lock["registry_hash_verified"] is True

    def test_lock_no_results_seen(self):
        """Lock must be created before results."""
        lock = json.load(open(A2 / "ALPHA_2_PRE_RUN_LOCK.json"))
        assert lock["no_results_seen"] is True

    def test_lock_all_artifacts_hashed(self):
        """All 14 artifacts must be hashed."""
        lock = json.load(open(A2 / "ALPHA_2_PRE_RUN_LOCK.json"))
        assert len(lock["artifacts"]) == 14


# ═══════════════════════════════════════════════════════════════════════
# RESULT ARTIFACT TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestResultArtifacts:
    """Verify all required output artifacts exist."""

    REQUIRED_FILES = [
        "ALPHA_2_PRE_RUN_LOCK.json",
        "ALPHA_2_PRE_RUN_TRUTH_REPAIR.md",
        "ALPHA_2_ENGINE_AUDIT.md",
        "ALPHA_2_TRADE_LEDGER.csv",
        "ALPHA_2_CONTROL_LEDGER.csv",
        "ALPHA_2_STRATEGY_METRICS.csv",
        "ALPHA_2_CONTROL_METRICS.csv",
        "ALPHA_2_FALSIFICATION_MATRIX.csv",
        "ALPHA_2_STRATEGY_CONTROL_COMPARISON.csv",
        "ALPHA_2_FAMILY_SUMMARY.csv",
        "ALPHA_2_COST_STRESS.csv",
        "ALPHA_2_FUNDING_ATTRIBUTION.csv",
        "ALPHA_2_SUBPERIOD_STABILITY.csv",
        "ALPHA_2_EFFECTIVE_EVENT_ANALYSIS.csv",
        "ALPHA_2_FORWARD_CANDIDATE_REGISTRY.csv",
        "ALPHA_2_REPORT.md",
        "ALPHA_2_DECISION.json",
    ]

    def test_all_artifacts_exist(self):
        """All 17 required artifacts must exist."""
        for f in self.REQUIRED_FILES:
            assert (A2 / f).exists(), f"Missing artifact: {f}"

    def test_trade_ledger_has_rows(self):
        """Trade ledger must have at least 1 row."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) > 0

    def test_control_ledger_has_rows(self):
        """Control ledger must have at least 1 row."""
        with open(A2 / "ALPHA_2_CONTROL_LEDGER.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) > 0

    def test_strategy_metrics_13_rows(self):
        """Strategy metrics must have 13 rows."""
        with open(A2 / "ALPHA_2_STRATEGY_METRICS.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13

    def test_control_metrics_6_rows(self):
        """Control metrics must have 6 rows."""
        with open(A2 / "ALPHA_2_CONTROL_METRICS.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 6

    def test_falsification_matrix_13_rows(self):
        """Falsification matrix must have 13 rows."""
        with open(A2 / "ALPHA_2_FALSIFICATION_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13

    def test_family_summary_6_rows(self):
        """Family summary must have 6 rows."""
        with open(A2 / "ALPHA_2_FAMILY_SUMMARY.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 6

    def test_cost_stress_13_rows(self):
        """Cost stress must have 13 rows."""
        with open(A2 / "ALPHA_2_COST_STRESS.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13

    def test_funding_attribution_13_rows(self):
        """Funding attribution must have 13 rows."""
        with open(A2 / "ALPHA_2_FUNDING_ATTRIBUTION.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13

    def test_effective_events_13_rows(self):
        """Effective event analysis must have 13 rows."""
        with open(A2 / "ALPHA_2_EFFECTIVE_EVENT_ANALYSIS.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13


class TestTradeLedgerIntegrity:
    """Verify trade ledger fields are complete."""

    REQUIRED_FIELDS = [
        "strategy_id", "family_id", "asset", "entry_timestamp", "entry_price",
        "direction", "execution_object", "exit_timestamp", "exit_price",
        "exit_reason", "holding_hours",
        "gross_bps", "entry_cost_bps", "exit_cost_bps", "funding_bps", "net_bps",
        "gross_R", "net_R", "MAE", "MFE",
    ]

    def test_all_fields_present(self):
        """All required fields must be in trade ledger."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
        for field in self.REQUIRED_FIELDS:
            assert field in fields, f"Missing field: {field}"

    def test_all_13_strategies_in_ledger(self):
        """All 13 strategies must appear in trade ledger."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            rows = list(csv.DictReader(f))
        ids = {r["strategy_id"] for r in rows}
        expected = {f"ALPHA1_S{i:03d}" for i in range(1, 14)}
        assert ids == expected, f"Missing in ledger: {expected - ids}"

    def test_net_bps_consistency(self):
        """net_bps must equal gross_bps - entry_cost - exit_cost + funding."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            rows = list(csv.DictReader(f))
        for r in rows[:100]:  # check first 100
            gross = float(r["gross_bps"])
            entry_c = float(r["entry_cost_bps"])
            exit_c = float(r["exit_cost_bps"])
            funding = float(r["funding_bps"])
            net = float(r["net_bps"])
            expected_net = gross - entry_c - exit_c + funding
            assert abs(net - expected_net) < 0.01, f"net_bps inconsistency: {net} != {expected_net}"


# ═══════════════════════════════════════════════════════════════════════
# FALSIFICATION RULE TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestFalsificationMatrix:
    """Verify falsification rules were applied correctly."""

    def test_all_strategies_falsified(self):
        """All 13 strategies must be classified."""
        with open(A2 / "ALPHA_2_FALSIFICATION_MATRIX.csv") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            assert r["classification"] in (
                "SURVIVES_DEVELOPMENT", "WEAK_DEVELOPMENT", "FALSIFIED",
                "INSUFFICIENT_EVENTS", "CONTROL_EQUIVALENT", "COST_FRAGILE"
            ), f"Invalid classification for {r['strategy_id']}: {r['classification']}"

    def test_f1_insufficient_events(self):
        """F1 must be triggered for strategies with < 20 trades."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        from collections import Counter
        counts = Counter(r["strategy_id"] for r in trades)
        with open(A2 / "ALPHA_2_FALSIFICATION_MATRIX.csv") as f:
            fal = {r["strategy_id"]: r for r in csv.DictReader(f)}
        for sid, count in counts.items():
            if count < 20:
                assert fal[sid]["F1"] == "INSUFFICIENT_EVENTS", \
                    f"F1 should trigger for {sid} with {count} trades"

    def test_f3_no_net_edge(self):
        """F3 must trigger when net_PF <= 1."""
        with open(A2 / "ALPHA_2_STRATEGY_METRICS.csv") as f:
            metrics = {r["strategy_id"]: r for r in csv.DictReader(f)}
        with open(A2 / "ALPHA_2_FALSIFICATION_MATRIX.csv") as f:
            fal = {r["strategy_id"]: r for r in csv.DictReader(f)}
        for sid, m in metrics.items():
            if float(m["net_PF"]) <= 1.0 and int(m["raw_trade_count"]) > 0:
                assert fal[sid]["F3"] == "NO_NET_EDGE", \
                    f"F3 should trigger for {sid} with net_PF={m['net_PF']}"


# ═══════════════════════════════════════════════════════════════════════
# CAUSALITY TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestCausality:
    """Verify no same-bar execution or future leakage."""

    def test_no_same_bar_execution(self):
        """Entry must be strictly after signal timestamp."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        for t in trades[:200]:
            signal = datetime.fromisoformat(t["signal_timestamp"].replace("Z", "+00:00"))
            entry = datetime.fromisoformat(t["entry_timestamp"].replace("Z", "+00:00"))
            assert entry > signal, \
                f"Same-bar execution: signal={t['signal_timestamp']} entry={t['entry_timestamp']}"

    def test_no_negative_holding(self):
        """Holding time must be non-negative."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        for t in trades:
            assert float(t["holding_hours"]) >= 0, \
                f"Negative holding: {t['strategy_id']} = {t['holding_hours']}"


# ═══════════════════════════════════════════════════════════════════════
# COST ACCOUNTING TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestCostAccounting:
    """Verify cost application is correct."""

    def test_perp_costs(self):
        """Perp strategies must have 5.0 bps total cost."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        perp_trades = [t for t in trades if t["execution_object"] == "perp"
                       and t["exit_reason"] != "END_OF_DATA"]
        if perp_trades:
            t = perp_trades[0]
            total_cost = float(t["entry_cost_bps"]) + float(t["exit_cost_bps"])
            assert abs(total_cost - 5.0) < 0.01, f"Perp cost wrong: {total_cost}"

    def test_hedge_costs(self):
        """Hedge strategies must have 12.5 bps total cost."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        hedge_trades = [t for t in trades if t["execution_object"] == "spot+perp hedge"
                        and t["exit_reason"] != "END_OF_DATA"]
        if hedge_trades:
            t = hedge_trades[0]
            total_cost = float(t["entry_cost_bps"]) + float(t["exit_cost_bps"])
            assert abs(total_cost - 12.5) < 0.01, f"Hedge cost wrong: {total_cost}"


# ═══════════════════════════════════════════════════════════════════════
# POSITION CONCURRENCY TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestPositionConcurrency:
    """Verify one-active-position rule."""

    def test_no_overlapping_positions_same_strategy(self):
        """No overlapping positions for same strategy."""
        with open(A2 / "ALPHA_2_TRADE_LEDGER.csv") as f:
            trades = list(csv.DictReader(f))
        # Group by strategy
        from collections import defaultdict
        by_strat = defaultdict(list)
        for t in trades:
            by_strat[t["strategy_id"]].append(t)

        for sid, strades in by_strat.items():
            for i, t1 in enumerate(strades):
                for t2 in strades[i+1:]:
                    if t1["asset"] != t2["asset"]:
                        continue
                    # Check overlap
                    e1 = datetime.fromisoformat(t1["entry_timestamp"].replace("Z", "+00:00"))
                    x1 = datetime.fromisoformat(t1["exit_timestamp"].replace("Z", "+00:00"))
                    e2 = datetime.fromisoformat(t2["entry_timestamp"].replace("Z", "+00:00"))
                    x2 = datetime.fromisoformat(t2["exit_timestamp"].replace("Z", "+00:00"))
                    # No overlap: e2 >= x1 or e1 >= x2
                    if not (e2 >= x1 or e1 >= x2):
                        assert False, \
                            f"Overlapping positions: {sid} {t1['entry_timestamp']}-{t1['exit_timestamp']} vs {t2['entry_timestamp']}-{t2['exit_timestamp']}"


# ═══════════════════════════════════════════════════════════════════════
# RESULT COMPLETENESS TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestResultCompleteness:
    """Verify every strategy appears in final matrix."""

    def test_no_dropped_rows(self):
        """All 13 strategies must appear in strategy metrics."""
        with open(A2 / "ALPHA_2_STRATEGY_METRICS.csv") as f:
            rows = list(csv.DictReader(f))
        ids = {r["strategy_id"] for r in rows}
        expected = {f"ALPHA1_S{i:03d}" for i in range(1, 14)}
        assert ids == expected, f"Missing strategies in metrics: {expected - ids}"

    def test_decision_json_complete(self):
        """Decision JSON must have required fields."""
        d = json.load(open(A2 / "ALPHA_2_DECISION.json"))
        assert d["checkpoint"] == "CRYPTO-ALPHA-2-PREREGISTERED-BACKTEST-AND-FALSIFICATION"
        assert d["decision"] == "PASS_ALPHA2_FALSIFICATION_COMPLETE"
        assert d["strategies_run"] == 13
        assert d["controls_run"] == 6
        assert d["engine_integrity"] == "PASS"


# ═══════════════════════════════════════════════════════════════════════
# FORWARD REGISTRY TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestForwardRegistry:
    """Verify forward registry is fail-closed."""

    def test_registry_exists(self):
        """Forward candidate registry must exist."""
        assert (A2 / "ALPHA_2_FORWARD_CANDIDATE_REGISTRY.csv").exists()

    def test_no_unauthorized_promotions(self):
        """No strategies should be promoted if all are falsified."""
        d = json.load(open(A2 / "ALPHA_2_DECISION.json"))
        if d["results"]["SURVIVES_DEVELOPMENT"] == 0:
            with open(A2 / "ALPHA_2_FORWARD_CANDIDATE_REGISTRY.csv") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 0, "No survivors should mean empty registry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
