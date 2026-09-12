"""
Tests for ALPHA-2R1.2 — F8 Semantic Truth Repair + Resource Architecture Freeze.
"""
import csv
import json
import hashlib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
RESOURCES = HERE.parent / "resources"
A2R1 = HERE.parent / "alpha_2r1"


def read_csv(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Part A: F8 Truth Repair ───
class TestF8TruthRepair:
    def test_truth_table_exists(self):
        fp = HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv"
        assert fp.exists()

    def test_truth_table_13_rows(self):
        rows = read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")
        assert len(rows) == 13

    def test_s009_pf_condition_correct(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")}
        r = rows["ALPHA1_S009"]
        # strat_PF=0.7133, ctrl_PF=0.7433 → ctrl >= strat = True
        assert r["pf_condition_correct"] == "True", f"S009 PF condition should be True, got {r['pf_condition_correct']}"

    def test_s010_pf_condition_correct(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")}
        r = rows["ALPHA1_S010"]
        # strat_PF=0.7292, ctrl_PF=0.7433 → ctrl >= strat = True
        assert r["pf_condition_correct"] == "True", f"S010 PF condition should be True, got {r['pf_condition_correct']}"

    def test_s006_pf_condition_correct(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")}
        r = rows["ALPHA1_S006"]
        # strat_PF=0.5908, ctrl_PF=0.7986 → ctrl >= strat = True
        assert r["pf_condition_correct"] == "True"

    def test_s008_pf_condition_correct(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")}
        r = rows["ALPHA1_S008"]
        assert r["pf_condition_correct"] == "True"

    def test_s001_pf_condition_false(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")}
        r = rows["ALPHA1_S001"]
        # strat_PF=0.8023, ctrl_PF=0.7614 → strat > ctrl → False
        assert r["pf_condition_correct"] == "False"

    def test_old_script_bug_count(self):
        rows = read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")
        bugs = [r for r in rows if r["discrepancy"] == "BUG_MISSED_PF_TRIGGER"]
        assert len(bugs) == 4, f"Expected 4 bugs (S006,S008,S009,S010), got {len(bugs)}"

    def test_pf_true_count(self):
        rows = read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")
        true_count = sum(1 for r in rows if r["pf_condition_correct"] == "True")
        assert true_count == 7, f"Expected 7 PF-true, got {true_count}"

    def test_pf_false_count(self):
        rows = read_csv(HERE / "ALPHA_2R1_2_F8_TRUTH_TABLE.csv")
        false_count = sum(1 for r in rows if r["pf_condition_correct"] == "False")
        assert false_count == 6, f"Expected 6 PF-false, got {false_count}"


class TestF8Reconciliation:
    def test_reconciliation_exists(self):
        assert (HERE / "ALPHA_2R1_2_F8_RECONCILIATION.csv").exists()

    def test_all_13_present(self):
        rows = read_csv(HERE / "ALPHA_2R1_2_F8_RECONCILIATION.csv")
        assert len(rows) == 13

    def test_canonical_status_ambiguous(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_RECONCILIATION.csv")}
        for sid, r in rows.items():
            assert r["canonical_status"] == "AMBIGUOUS_NON_DECISIVE", f"{sid} should be AMBIGUOUS_NON_DECISIVE"

    def test_s009_reading1_trigger(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_RECONCILIATION.csv")}
        r = rows["ALPHA1_S009"]
        assert r["reading1_trigger"] == "STATE_ADDS_NO_VALUE"

    def test_s010_reading1_trigger(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_2R1_2_F8_RECONCILIATION.csv")}
        r = rows["ALPHA1_S010"]
        assert r["reading1_trigger"] == "STATE_ADDS_NO_VALUE"


class TestFinalRuleCounts:
    def test_rule_counts_exists(self):
        assert (HERE / "ALPHA_2R1_2_FINAL_RULE_COUNTS.csv").exists()

    def test_f8_is_ambiguous(self):
        rows = {r["rule"]: r for r in read_csv(HERE / "ALPHA_2R1_2_FINAL_RULE_COUNTS.csv")}
        assert rows["F8"]["status"] in ("AMBIGUOUS", "AMBIGUOUS_NON_DECISIVE")

    def test_f3_count_11(self):
        rows = {r["rule"]: r for r in read_csv(HERE / "ALPHA_2R1_2_FINAL_RULE_COUNTS.csv")}
        assert rows["F3"]["count"] == "11"


class TestDecision:
    def test_decision_exists(self):
        d = read_json(HERE / "ALPHA_2R1_2_DECISION.json")
        assert d["overall_decision"] == "PASS_ALPHA2_EVIDENCE_AND_RESOURCE_ARCHITECTURE_FREEZE"

    def test_pnl_not_mutated(self):
        d = read_json(HERE / "ALPHA_2R1_2_DECISION.json")
        assert d["pnl_mutated"] is False

    def test_f8_ambiguous(self):
        d = read_json(HERE / "ALPHA_2R1_2_DECISION.json")
        assert d["f8_semantic_audit"]["canonical_status"] == "AMBIGUOUS_NON_DECISIVE"

    def test_survivors_zero(self):
        d = read_json(HERE / "ALPHA_2R1_2_DECISION.json")
        assert d["gen1_survivors"] == 0
        assert d["gen1_falsified"] == 13


class TestHashLock:
    def test_hash_lock_exists(self):
        lock = read_json(HERE / "ALPHA_2R1_2_PRE_RUN_HASH_LOCK.json")
        assert lock["pnl_mutated"] is False

    def test_input_hashes_present(self):
        lock = read_json(HERE / "ALPHA_2R1_2_PRE_RUN_HASH_LOCK.json")
        assert len(lock["input_hashes"]) >= 8

    def test_hashes_match_files(self):
        lock = read_json(HERE / "ALPHA_2R1_2_PRE_RUN_HASH_LOCK.json")
        for fn, expected_h in lock["input_hashes"].items():
            fp = A2R1 / fn
            assert fp.exists(), f"Referenced file {fn} does not exist"
            h = hashlib.sha256()
            with open(fp, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            assert h.hexdigest() == expected_h, f"Hash mismatch for {fn}"


# ─── Part B: Resource Architecture ───
class TestResourceArchitecture:
    def test_authority_registry_exists(self):
        assert (RESOURCES / "CRYPTO_RESOURCE_AUTHORITY_REGISTRY.md").exists()

    def test_integration_roadmap_exists(self):
        assert (RESOURCES / "CRYPTO_RESOURCE_INTEGRATION_ROADMAP.md").exists()

    def test_payoff_router_exists(self):
        assert (RESOURCES / "CRYPTO_PAYOFF_ROUTER_RESEARCH_PLAN.md").exists()

    def test_resource_registry_json_exists(self):
        assert (RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json").exists()

    def test_registry_has_4_resources(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        assert len(reg["resources"]) == 4

    def test_defillama_documented(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        names = [r["resource"] for r in reg["resources"]]
        assert "DefiLlama" in names

    def test_boros_documented(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        names = [r["resource"] for r in reg["resources"]]
        assert "Boros by Pendle" in names

    def test_perpdexlist_documented(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        names = [r["resource"] for r in reg["resources"]]
        assert "PERPDEXLIST" in names

    def test_derivatives_monkey_documented(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        names = [r["resource"] for r in reg["resources"]]
        assert "Derivatives Monkey" in names

    def test_defillama_plan_exists(self):
        assert (RESOURCES / "DEFILLAMA_RESEARCH_PLAN.md").exists()

    def test_boros_plan_exists(self):
        assert (RESOURCES / "BOROS_RESEARCH_PLAN.md").exists()

    def test_perpdexlist_plan_exists(self):
        assert (RESOURCES / "PERPDEXLIST_RESEARCH_PLAN.md").exists()

    def test_derivatives_monkey_plan_exists(self):
        assert (RESOURCES / "DERIVATIVES_MONKEY_RESEARCH_PLAN.md").exists()

    def test_no_lower_overrides_higher(self):
        """Authority hierarchy: no Level 3+ source overrides Level 1."""
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        for r in reg["resources"]:
            if r["authority_class"] in ["LEVEL_3", "LEVEL_4"]:
                assert len(r.get("not_canonical_for", "")) > 0, \
                    f"{r['resource']} should specify what it's NOT canonical for"

    def test_future_lanes_defined(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        lanes = set(r["future_lane"] for r in reg["resources"])
        assert "CRYPTO_RATES" in lanes
        assert "CRYPTO_OPTIONS" in lanes
        assert "CRYPTO_CAPITAL_FLOW" in lanes
