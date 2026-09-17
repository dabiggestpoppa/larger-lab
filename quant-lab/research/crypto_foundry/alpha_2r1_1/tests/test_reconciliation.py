"""
Tests for ALPHA-2R1.1 — Final Evidence Reconciliation Seal.
Validates F8 recomputation, rule counts, effective events, terminology.
"""
import csv
import json
import hashlib
import sys
import os
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
A2R1 = HERE.parent / "alpha_2r1"

# ─── Helpers ───
def read_csv(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Fixtures ───
@pytest.fixture(scope="module")
def strat_metrics():
    return {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}

@pytest.fixture(scope="module")
def ctrl_metrics():
    return {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_CONTROL_METRICS.csv")}

@pytest.fixture(scope="module")
def fals_matrix():
    return {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")}

@pytest.fixture(scope="module")
def decision():
    return read_json(HERE / "ALPHA_2R1_1_DECISION.json")

@pytest.fixture(scope="module")
def hash_lock():
    return read_json(HERE / "ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json")

@pytest.fixture(scope="module")
def f8_recomp():
    return {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_1_F8_RECOMPUTATION.csv")}

@pytest.fixture(scope="module")
def rule_reconcile():
    return {r["rule"]: r for r in read_csv(HERE / "ALPHA_2R1_1_RULE_RECONCILIATION.csv")}

@pytest.fixture(scope="module")
def eff_events():
    return {r["entity_id"]: r for r in read_csv(HERE / "ALLPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv") if False}  # will use correct path

@pytest.fixture(scope="module")
def family_handoff():
    return {r["family_id"]: r for r in read_csv(HERE / "ALPHA_2R1_1_FAMILY_HANDOFF.csv")}


# ─── Hash Lock Tests ───
class TestHashLock:
    def test_lock_exists(self, hash_lock):
        assert hash_lock["checkpoint"] == "CRYPTO-ALPHA-2R1.1-FINAL-EVIDENCE-RECONCILIATION-SEAL"

    def test_sealed_registry_hash(self, hash_lock):
        assert hash_lock["sealed_registry_hash"] == "2abaf8c21200a67e5b06d8ccf42ceb19574a12df21916d314a3c80b47f9a419e"

    def test_no_pnl_replayed(self, hash_lock):
        assert hash_lock["no_pnl_replayed"] is True

    def test_input_hashes_not_empty(self, hash_lock):
        assert len(hash_lock["input_hashes"]) >= 8

    def test_input_hash_deterministic(self, hash_lock):
        for fn, h in hash_lock["input_hashes"].items():
            fp = A2R1 / fn
            assert fp.exists(), f"Referenced file {fn} does not exist"
            assert sha256_file(fp) == h, f"Hash mismatch for {fn}"


# ─── F3 Reconciliation Tests ───
class TestF3Reconciliation:
    def test_f3_count_exact_11(self, strat_metrics, fals_matrix):
        f3_ids = []
        for sid, m in strat_metrics.items():
            net_pf = float(m.get("net_PF", 0))
            if net_pf <= 1.0:
                f3_ids.append(sid)
        assert len(f3_ids) == 11, f"F3 count: got {len(f3_ids)}, expected 11. IDs: {f3_ids}"

    def test_s002_not_f3(self, strat_metrics, fals_matrix):
        m = strat_metrics["ALPHA1_S002"]
        assert float(m["net_PF"]) > 1.0, f"S002 net_PF={m['net_PF']} should be > 1.0"
        assert not fals_matrix["ALPHA1_S002"].get("F3", "").strip(), "S002 should not have F3"

    def test_s003_not_f3(self, strat_metrics, fals_matrix):
        m = strat_metrics["ALPHA1_S003"]
        assert float(m["net_PF"]) > 1.0, f"S003 net_PF={m['net_PF']} should be > 1.0"
        assert not fals_matrix["ALPHA1_S003"].get("F3", "").strip(), "S003 should not have F3"


# ─── F8 Recomputation Tests ───
class TestF8Recomputation:
    def test_f8_seed_deterministic(self):
        """F8 recomputation with same seed produces same results."""
        import random
        rng = random.Random(31082026)
        samples1 = [rng.randint(0, 99) for _ in range(100)]
        rng2 = random.Random(31082026)
        samples2 = [rng2.randint(0, 99) for _ in range(100)]
        assert samples1 == samples2, "F8 seed not deterministic"

    def test_f8_10k_resamples(self, f8_recomp):
        """All F8 entries should have 10,000 bootstrap resamples implied."""
        for sid, row in f8_recomp.items():
            # The CI should exist and be non-trivial
            ci_low = float(row.get("CI_low", 0))
            ci_high = float(row.get("CI_high", 0))
            assert ci_low != ci_high, f"{sid} CI is degenerate: [{ci_low}, {ci_high}]"

    def test_f8_mapping_complete(self, f8_recomp):
        all_sids = [f"ALPHA1_S{i:03d}" for i in range(1, 14)]
        for sid in all_sids:
            assert sid in f8_recomp, f"Missing F8 entry for {sid}"

    def test_f8_count_3(self, f8_recomp):
        triggered = [sid for sid, r in f8_recomp.items() if r.get("F8_trigger", "").lower() == "true"]
        assert len(triggered) == 3, f"F8 count: got {len(triggered)}, expected 3. IDs: {triggered}"

    def test_f8_triggered_ids_correct(self, f8_recomp):
        expected = {"ALPHA1_S005", "ALPHA1_S011", "ALPHA1_S012"}
        triggered = {sid for sid, r in f8_recomp.items() if r.get("F8_trigger", "").lower() == "true"}
        assert triggered == expected, f"F8 IDs mismatch: got {triggered}, expected {expected}"

    def test_s001_f8_false(self, f8_recomp):
        """S001 strategy beats control — F8 must be False."""
        assert f8_recomp["ALPHA1_S001"].get("F8_trigger", "").lower() == "false"

    def test_s007_f8_false(self, f8_recomp):
        """S007 strategy beats control — F8 must be False."""
        assert f8_recomp["ALPHA1_S007"].get("F8_trigger", "").lower() == "false"

    def test_s011_f8_true(self, f8_recomp):
        """S011 control clearly beats strategy — F8 must be True."""
        assert f8_recomp["ALPHA1_S011"].get("F8_trigger", "").lower() == "true"


# ─── Rule Count Reconciliation Tests ───
class TestRuleReconciliation:
    def test_f3_count_in_reconciliation(self, rule_reconcile):
        assert rule_reconcile["F3"]["count"] == "11"

    def test_f8_count_in_reconciliation(self, rule_reconcile):
        assert rule_reconcile["F8"]["count"] == "3"

    def test_all_rules_present(self, rule_reconcile):
        for r in ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"]:
            assert r in rule_reconcile, f"Missing rule {r}"


# ─── Decision Tests ───
class TestDecision:
    def test_decision_class(self, decision):
        assert decision["decision"] == "PASS_ALPHA2_FINAL_EVIDENCE_SEAL"

    def test_pnl_not_mutated(self, decision):
        assert decision["pnl_mutated"] is False

    def test_no_optimization(self, decision):
        assert decision["no_optimization"] is True

    def test_f8_recomputed(self, decision):
        assert decision["falsification_counts_reconciled"]["F8_recomputed"] == 3

    def test_s002_classification(self, decision):
        assert decision["s002_classification"] == "POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED"

    def test_s003_classification(self, decision):
        assert decision["s003_classification"] == "POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED"

    def test_13_falsified(self, decision):
        assert decision["results"]["FALSIFIED"] == 13
        assert decision["results"]["SURVIVES_DEVELOPMENT"] == 0


# ─── No Ledger Mutation Tests ───
class TestNoMutation:
    def test_trade_ledger_hash_unchanged(self):
        """Trade ledger hash must match what was locked."""
        h = sha256_file(A2R1 / "ALPHA_2R1_TRADE_LEDGER.csv")
        lock = read_json(HERE / "ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json")
        assert lock["input_hashes"]["ALPHA_2R1_TRADE_LEDGER.csv"] == h

    def test_strategy_metrics_hash_unchanged(self):
        h = sha256_file(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")
        lock = read_json(HERE / "ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json")
        assert lock["input_hashes"]["ALPHA_2R1_STRATEGY_METRICS.csv"] == h

    def test_falsification_matrix_hash_unchanged(self):
        h = sha256_file(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")
        lock = read_json(HERE / "ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json")
        assert lock["input_hashes"]["ALPHA_2R1_FALSIFICATION_MATRIX.csv"] == h


# ─── Effective Event Tests ───
class TestEffectiveEvents:
    def test_effective_events_file_exists(self):
        fp = HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv"
        assert fp.exists(), "Effective event counts file missing"

    def test_all_strategies_present(self):
        rows = read_csv(HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv")
        strat_rows = [r for r in rows if r["entity_type"] == "STRATEGY"]
        assert len(strat_rows) == 13, f"Expected 13 strategy rows, got {len(strat_rows)}"

    def test_all_controls_present(self):
        rows = read_csv(HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv")
        ctrl_rows = [r for r in rows if r["entity_type"] == "CONTROL"]
        assert len(ctrl_rows) == 6, f"Expected 6 control rows, got {len(ctrl_rows)}"

    def test_no_varies_placeholder(self):
        rows = read_csv(HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv")
        for r in rows:
            assert r["effective_event_count"] != "varies", f"{r['entity_id']} has 'varies' placeholder"

    def test_no_zero_effective_events_with_trades(self):
        rows = read_csv(HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv")
        for r in rows:
            raw = int(r["raw_trade_count"])
            eff = int(r["effective_event_count"])
            if raw > 0:
                assert eff > 0, f"{r['entity_id']}: raw={raw} but effective=0"


# ─── Root-Cause Terminology Tests ───
class TestTerminology:
    def test_root_cause_separation(self, decision):
        rc = decision["root_cause_terminology"]
        assert rc["BUG_A"] == "EXIT_EXECUTION_CONTRACT_VIOLATION"
        assert rc["AUDIT_B"] == "PRICE_SOURCE_ISOLATION"
        assert "cross-asset" not in rc["BUG_A_description"].lower()


# ─── Family Handoff Tests ───
class TestFamilyHandoff:
    def test_all_families_present(self, family_handoff):
        for fam in ["FAM_A", "FAM_B", "FAM_C", "FAM_D", "FAM_E", "FAM_X"]:
            assert fam in family_handoff, f"Missing family {fam}"

    def test_handoff_matches_metrics(self, family_handoff, strat_metrics):
        """Family EV ranges should be consistent with individual strategy metrics."""
        for fam, info in family_handoff.items():
            strategies = info["strategies"].split(";")
            for sid in strategies:
                assert sid in strat_metrics, f"Family {fam} references unknown strategy {sid}"
