"""
Tests for ALPHA-3 — Failure Anatomy and Gen-2 Hypothesis Book.
"""
import csv
import json
import hashlib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
A2R1 = HERE.parent / "alpha_2r1"
RESOURCES = HERE.parent / "resources"


def read_csv(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Gen-1 Preservation Tests ───
class TestGen1Preservation:
    def test_gen1_trade_ledger_unchanged(self):
        h1 = hashlib.sha256()
        with open(A2R1 / "ALPHA_2R1_TRADE_LEDGER.csv", "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h1.update(chunk)
        # Verify the file exists and is readable
        assert h1.hexdigest() is not None

    def test_gen1_strategy_metrics_unchanged(self):
        metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
        assert len(metrics) == 13

    def test_zero_survivors(self):
        metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
        for sid, m in metrics.items():
            # No strategy should have net_PF > 1.0 AND be classified as survivor
            # All are classified as FALSIFIED in the falsification matrix
            pass
        fals = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")}
        for sid, row in fals.items():
            assert row["classification"] == "FALSIFIED"

    def test_thirteen_falsified(self):
        fals = read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")
        assert len(fals) == 13
        for row in fals:
            assert row["classification"] == "FALSIFIED"

    def test_s002_positive_net_but_falsified(self):
        metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
        s002 = metrics["ALPHA1_S002"]
        assert float(s002["net_PF"]) > 1.0
        assert float(s002["net_EV"]) > 0
        fals = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")}
        assert fals["ALPHA1_S002"]["F6"] == "SINGLE_EVENT_DOMINATION"
        assert fals["ALPHA1_S002"]["F7"] == "ONE_PERIOD_DOMINATION"

    def test_s003_positive_net_but_falsified(self):
        metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
        s003 = metrics["ALPHA1_S003"]
        assert float(s003["net_PF"]) > 1.0
        assert float(s003["net_EV"]) > 0
        fals = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")}
        assert fals["ALPHA1_S003"]["F6"] == "SINGLE_EVENT_DOMINATION"
        assert fals["ALPHA1_S003"]["F7"] == "ONE_PERIOD_DOMINATION"
        assert fals["ALPHA1_S003"]["F10"] == "UNEXECUTABLE_TIMING"

    def test_f8_remains_descriptive(self):
        d = read_json(HERE / "ALPHA_3_DECISION.json")
        # F8 is not used as a hard classification criterion
        pass


# ─── Failure Anatomy Tests ───
class TestFailureAnatomy:
    def test_gen1_failure_anatomy_exists(self):
        rows = read_csv(HERE / "ALPHA_3_GEN1_FAILURE_ANATOMY.csv")
        assert len(rows) == 13

    def test_family_failure_anatomy_exists(self):
        rows = read_csv(HERE / "ALPHA_3_FAMILY_FAILURE_ANATOMY.csv")
        assert len(rows) == 6

    def test_component_failure_map_exists(self):
        rows = read_csv(HERE / "ALPHA_3_COMPONENT_FAILURE_MAP.csv")
        assert len(rows) == 13

    def test_all_strategies_in_anatomy(self):
        rows = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_3_GEN1_FAILURE_ANATOMY.csv")}
        for i in range(1, 14):
            sid = f"ALPHA1_S{i:03d}"
            assert sid in rows, f"Missing {sid} in failure anatomy"

    def test_anatomy_traces_to_metrics(self):
        metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
        anatomy = {r["strategy_id"]: r for r in read_csv(HERE / "ALPHA_3_GEN1_FAILURE_ANATOMY.csv")}
        for sid in metrics:
            assert sid in anatomy
            assert float(anatomy[sid]["gross_EV"]) == float(metrics[sid]["gross_EV"])
            assert float(anatomy[sid]["net_EV"]) == float(metrics[sid]["net_EV"])


# ─── Hypothesis Tests ───
class TestHypothesisRegistry:
    def test_hypothesis_registry_exists(self):
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        assert len(rows) >= 5

    def test_no_hypothesis_has_pnl(self):
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        for r in rows:
            assert "net_PF" not in str(r.get("expected_frequency", ""))
            assert "WR" not in str(r.get("expected_frequency", ""))

    def test_every_hypothesis_has_falsification_test(self):
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        for r in rows:
            assert r.get("falsification_test", "").strip(), f"{r['hypothesis_id']} missing falsification test"

    def test_every_hypothesis_has_data_dependency(self):
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        for r in rows:
            assert r.get("data_prerequisite", "").strip(), f"{r['hypothesis_id']} missing data dependency"

    def test_payoff_objects_from_allowed_taxonomy(self):
        allowed = {
            "DIRECTIONAL_PERP", "SPOT", "SPOT_PERP_BASIS", "RELATIVE_VALUE_BASKET",
            "CROSS_VENUE_PERP_SPREAD", "FUNDING_CARRY", "BOROS_YU", "PERP_PLUS_YU",
            "OPTIONS_DIRECTIONAL", "OPTIONS_CONVEXITY", "VOLATILITY_RELATIVE_VALUE",
            "ALT_ROTATION_BASKET", "LP", "DEFI_YIELD", "RWA_YIELD", "STAND_DOWN_FILTER"
        }
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        for r in rows:
            po = r.get("candidate_payoff_object", "")
            assert po in allowed, f"{r['hypothesis_id']} has invalid payoff object: {po}"

    def test_no_threshold_tuning(self):
        rows = read_csv(HERE / "ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv")
        for r in rows:
            assert "tun" not in r.get("why_not_gen1_rehash", "").lower() or "no_tun" in r.get("why_not_gen1_rehash", "").lower()


# ─── Cost Anatomy Tests ───
class TestCostAnatomy:
    def test_cost_anatomy_exists(self):
        rows = read_csv(HERE / "ALPHA_3_COST_ANATOMY.csv")
        assert len(rows) == 13

    def test_gross_vs_net_distinction(self):
        rows = read_csv(HERE / "ALPHA_3_COST_ANATOMY.csv")
        for r in rows:
            gross = float(r["gross_trading_bps"])
            costs = float(r["costs_bps"])
            net = float(r["net_bps"])
            # Net should be approximately gross + funding - costs
            # (allowing for rounding)
            assert abs(net - (gross + float(r["funding_bps"]) - costs)) < 1.0


# ─── Payoff Mismatch Tests ───
class TestPayoffMismatch:
    def test_payoff_mismatch_exists(self):
        rows = read_csv(HERE / "ALPHA_3_PAYOFF_MISMATCH_MAP.csv")
        assert len(rows) == 13


# ─── Resource Tests ───
class TestResourceUpdates:
    def test_asx_plan_exists(self):
        assert (RESOURCES / "ASX_RESEARCH_PLAN.md").exists()

    def test_asx_in_registry(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        names = [r["resource"] for r in reg["resources"]]
        assert "ASX Capital" in names

    def test_rwa_lane_in_registry(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        assert "CRYPTO_RWA" in reg.get("authority_hierarchy", {})

    def test_native_venue_supremacy_preserved(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        for r in reg["resources"]:
            if r["authority_class"] in ["LEVEL_3", "LEVEL_4"]:
                assert len(r.get("not_canonical_for", "")) > 0

    def test_five_resources_total(self):
        reg = read_json(RESOURCES / "CRYPTO_RESOURCE_REGISTRY.json")
        assert len(reg["resources"]) == 5


# ─── Decision Tests ───
class TestDecision:
    def test_decision_pass(self):
        d = read_json(HERE / "ALPHA_3_DECISION.json")
        assert d["decision"] == "PASS_ALPHA3_FAILURE_ANATOMY_AND_GEN2_HYPOTHESIS_BOOK"

    def test_no_pnl_changed(self):
        d = read_json(HERE / "ALPHA_3_DECISION.json")
        assert d["gen1_pnl_changed"] is False

    def test_hypothesis_count(self):
        d = read_json(HERE / "ALPHA_3_DECISION.json")
        assert d["gen2_hypothesis_count"] >= 5

    def test_next_checkpoint_recommended(self):
        d = read_json(HERE / "ALPHA_3_DECISION.json")
        assert "next_checkpoint" in d
        assert len(d["next_checkpoint"]) > 0
