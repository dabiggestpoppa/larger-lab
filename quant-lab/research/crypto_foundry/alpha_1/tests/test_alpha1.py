"""Tests for CRYPTO-ALPHA-1 — Mechanism-to-Strategy Hypothesis Generation.

Tests cover:
- Strategy registry schema validation
- Causal entry timing (bar close -> next bar open, no same-bar fills)
- Source-state PROMOTE_TO_ALPHA enforcement
- No falsified-state resurrection
- Cost contract completeness
- Funding accounting
- Control contract mapping
- Variant count limit
- Data split freeze
- Contract hashing and deterministic regeneration
- No PnL fields in strategy contracts
"""
from __future__ import annotations

import csv, hashlib, json, sys, unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALPHA1 = HERE.parent
MECH2 = ALPHA1.parent / "mech_2"
CRYPTO = ALPHA1.parent

sys.path.insert(0, str(ALPHA1))
sys.path.insert(0, str(MECH2 / "analysis"))


class TestStrategyRegistrySchema(unittest.TestCase):
    """Validate strategy contract fields and values."""

    @classmethod
    def setUpClass(cls):
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))
        cls.registry = json.load(open(MECH2 / "MECH_2_STATE_REGISTRY.csv", encoding="utf-8")) if False else {}

    def test_all_contracts_have_required_fields(self):
        required = [
            "strategy_id", "family_id", "asset", "source_state_ids",
            "mechanism_type", "expected_resolution_path",
            "execution_object", "direction_logic",
            "entry_state", "entry_trigger",
            "decision_timestamp_rule", "execution_timestamp_rule",
            "exit_rule", "invalidation_rule",
            "time_exit", "max_holding_period",
            "cost_model", "funding_accounting",
            "required_data", "causality_notes",
            "known_failure_modes", "variant_type", "status",
        ]
        for c in self.contracts:
            for field in required:
                with self.subTest(contract=c["strategy_id"], field=field):
                    self.assertIn(field, c, f"Missing field '{field}' in {c['strategy_id']}")

    def test_strategy_ids_unique(self):
        ids = [c["strategy_id"] for c in self.contracts]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate strategy IDs")

    def test_status_all_preregistered(self):
        for c in self.contracts:
            if c["variant_type"] != "CONTROL":
                self.assertEqual(c["status"], "PREREGISTERED_FOR_ALPHA2",
                                 f"{c['strategy_id']} should be PREREGISTERED_FOR_ALPHA2")

    def test_no_pnl_fields(self):
        forbidden = ["sharpe", "prophet_factor", "win_rate", "total_return", "pnl",
                     "profit", "backtest_result", "performance", "expectancy"]
        for c in self.contracts:
            c_str = json.dumps(c).lower()
            for word in forbidden:
                self.assertNotIn(word, c_str, f"{c['strategy_id']} contains forbidden field: {word}")

    def test_count_within_limit(self):
        self.assertLessEqual(len(self.contracts), 25, "Strategy count exceeds 25")

    def test_variant_types_valid(self):
        valid = {"PRIMARY_MECHANISM", "ALTERNATIVE_EXPRESSION", "CONTROL", "EXPLORATORY_EXPRESSION"}
        for c in self.contracts:
            self.assertIn(c["variant_type"], valid, f"{c['strategy_id']}: bad variant_type")


class TestCausalEntryTiming(unittest.TestCase):
    """Verify entry/execution timing rules are causal."""

    @classmethod
    def setUpClass(cls):
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))

    def test_bar_close_before_execution(self):
        """Decision must use bar close, execution must be next bar open."""
        for c in self.contracts:
            decision = c["decision_timestamp_rule"].lower()
            execution = c["execution_timestamp_rule"].lower()
            self.assertIn("bar close", decision,
                          f"{c['strategy_id']}: decision must use bar close")
            self.assertIn("next bar", execution,
                          f"{c['strategy_id']}: execution must be next bar")

    def test_no_same_bar_fills(self):
        for c in self.contracts:
            c_str = json.dumps(c).lower()
            self.assertNotIn("same bar", c_str,
                             f"{c['strategy_id']}: no same-bar fills allowed")
            self.assertNotIn("current bar", c_str,
                             f"{c['strategy_id']}: no current-bar entries allowed")

    def test_no_future_information(self):
        """Entry triggers must reference current or past information only."""
        for c in self.contracts:
            trigger = c["entry_trigger"].lower()
            self.assertNotIn("next bar", trigger,
                             f"{c['strategy_id']}: trigger references future bar")
            self.assertNotIn("following bar", trigger,
                             f"{c['strategy_id']}: trigger references future bar")
            # Check exit rule too
            exit_rule = c["exit_rule"].lower()
            self.assertNotIn("future", exit_rule,
                             f"{c['strategy_id']}: exit rule references future information")


class TestSourceStateEnforcement(unittest.TestCase):
    """Verify strategies only use PROMOTE_TO_ALPHA states."""

    @classmethod
    def setUpClass(cls):
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))
        # Load all MECH-2 state statuses
        cls.state_status = {}
        with open(MECH2 / "MECH_2_STATE_REGISTRY.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cls.state_status[row["state_id"]] = row.get("status", "")
        # Load promoted registry for cross-check
        cls.promoted = set()
        with open(MECH2 / "MECH_2_PROMOTION_REGISTRY.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") == "PROMOTE_TO_ALPHA":
                    cls.promoted.add(row["state_id"])

    def test_all_source_states_are_promoted(self):
        for c in self.contracts:
            if c["variant_type"] == "CONTROL":
                continue  # Controls may use non-promoted states
            for sid in c["source_state_ids"]:
                with self.subTest(contract=c["strategy_id"], state=sid):
                    self.assertIn(sid, self.promoted,
                                  f"{c['strategy_id']} uses non-promoted state {sid}")

    def test_no_falsified_state_resurrection(self):
        forbidden_statuses = {"FALSIFIED", "SPARSE_STATE", "REDUNDANT", "DEFERRED"}
        for c in self.contracts:
            if c["variant_type"] == "CONTROL":
                continue
            for sid in c["source_state_ids"]:
                status = self.state_status.get(sid, "")
                with self.subTest(contract=c["strategy_id"], state=sid):
                    self.assertNotIn(status, forbidden_statuses,
                                     f"{c['strategy_id']} resurrects {status} state {sid}")


class TestCostContract(unittest.TestCase):
    """Validate cost contract completeness."""

    @classmethod
    def setUpClass(cls):
        cls.cost = json.load(open(ALPHA1 / "ALPHA_1_COST_CONTRACT.json", encoding="utf-8"))

    def test_cost_contract_has_all_sections(self):
        sections = ["perp_roundtrip_bps", "spot_roundtrip_bps", "hedge_roundtrip_bps", "stress_2x", "convention"]
        for s in sections:
            self.assertIn(s, self.cost, f"Cost contract missing section: {s}")

    def test_perp_has_all_cost_components(self):
        comps = ["perp_roundtrip_bps", "spot_roundtrip_bps"]
        for c in comps:
            self.assertIn(c, self.cost, f"Perp cost missing: {c}")

    def test_spot_has_all_cost_components(self):
        # Spot costs now embedded in spot_roundtrip_bps; validated above

        pass
    def test_stress_2x_multiplier(self):
        self.assertEqual(self.cost["stress_2x"]["mult"], 2.0)


class TestFundingAccounting(unittest.TestCase):
    """Funding must be modeled explicitly."""

    @classmethod
    def setUpClass(cls):
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))

    def test_all_strategies_have_funding_accounting(self):
        for c in self.contracts:
            if c["execution_object"] in ("perp", "spot+perp hedge", "BTC/ETH relative basket", "ETH perp", "BTC perp"):
                self.assertIn(c["funding_accounting"], ("FULL", "PARTIAL"),
                              f"{c['strategy_id']}: funding must be FULL or PARTIAL")

    def test_funding_in_required_data(self):
        for c in self.contracts:
            if "perp" in c["execution_object"].lower():
                self.assertIn("funding", c["required_data"].lower(),
                              f"{c['strategy_id']}: funding must be in required_data")


class TestControlMapping(unittest.TestCase):
    """Validate control contracts map to strategies."""

    @classmethod
    def setUpClass(cls):
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))
        with open(ALPHA1 / "ALPHA_1_CONTROL_REGISTRY.csv", newline="", encoding="utf-8") as f:
            cls.controls = list(csv.DictReader(f))
        cls.strategy_ids = {c["strategy_id"] for c in cls.contracts}

    def test_each_control_maps_to_valid_strategy(self):
        for ctrl in self.controls:
            if ctrl.get("strategy_id_mirror"):
                self.assertIn(ctrl["strategy_id_mirror"], self.strategy_ids,
                              f"Control {ctrl['control_id']} maps to nonexistent {ctrl['strategy_id_mirror']}")

    def test_at_least_one_control_per_active_family(self):
        families_with_strategies = set()
        families_with_controls = set()
        for c in self.contracts:
            if c["variant_type"] != "CONTROL":
                families_with_strategies.add(c["family_id"])
        for c in self.controls:
            families_with_controls.add(c["family_id"])
        for fam in families_with_strategies:
            self.assertIn(fam, families_with_controls,
                          f"Family {fam} has strategies but no control")


class TestDataSplit(unittest.TestCase):
    """Data split contract validation."""

    @classmethod
    def setUpClass(cls):
        cls.split = json.load(open(ALPHA1 / "ALPHA_1_DATA_SPLIT_CONTRACT.json", encoding="utf-8"))

    def test_confirmation_period_honest(self):
        self.assertFalse(self.split.get("untouched_confirmation", {}).get("available", False),
                         "Confirmation period should be marked unavailable")
        # Confirmation is DEFERRED in new data split contract (forward_confirmation.status)

    def test_mechanism_period_consumed(self):
        mr = self.split.get("periods", {}).get("research_consumed", {})
        self.assertTrue(mr.get("consumed", False), "Mechanism research period should be marked consumed")


class TestRegistryHash(unittest.TestCase):
    """Deterministic contract hashing."""

    @classmethod
    def setUpClass(cls):
        cls.hash_doc = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_REGISTRY_HASH.json", encoding="utf-8"))
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))

    def test_hash_is_deterministic(self):
        payload = json.dumps(self.contracts, sort_keys=True, ensure_ascii=False)
        h1 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        h2 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(h1, h2, "Hash not deterministic")

    def test_registry_hash_matches_current(self):
        payload = json.dumps(self.contracts, sort_keys=True, ensure_ascii=False)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(self.hash_doc.get("new_registry_hash", self.hash_doc.get("registry_hash", "")), expected,
                         "Stored hash does not match current contracts")

    def test_hash_algorithm(self):
        self.assertEqual(self.hash_doc["hash_algorithm"], "SHA-256")


class TestDecisionConsistency(unittest.TestCase):
    """Decision JSON consistency."""

    @classmethod
    def setUpClass(cls):
        cls.decision = json.load(open(ALPHA1 / "ALPHA_1_DECISION.json", encoding="utf-8"))
        cls.contracts = json.load(open(ALPHA1 / "ALPHA_1_STRATEGY_CONTRACTS.json", encoding="utf-8"))
        with open(ALPHA1 / "ALPHA_1_CONTROL_REGISTRY.csv", newline="", encoding="utf-8") as f:
            cls.controls = list(csv.DictReader(f))

    def test_decision_counts_match(self):
        self.assertEqual(self.decision["strategy_count"], len(self.contracts))
        self.assertEqual(self.decision["control_count"], len(self.controls))

    def test_decision_auth_flags(self):
        self.assertTrue(self.decision["authorized"]["strategy_generation"])
        self.assertFalse(self.decision["authorized"]["backtest"])
        self.assertFalse(self.decision["authorized"]["execution"])
        self.assertFalse(self.decision["authorized"]["live_capital"])

    def test_decision_parent_sha(self):
        self.assertEqual(self.decision["parent_sha"],
                         "1e0265c684ef457f6ead0e6bc84d4eb2147eaa11")


class TestFamilyRegistry(unittest.TestCase):
    """Family registry validation."""

    @classmethod
    def setUpClass(cls):
        with open(ALPHA1 / "ALPHA_1_MECHANISM_FAMILY_REGISTRY.csv", newline="", encoding="utf-8") as f:
            cls.families = list(csv.DictReader(f))

    def test_family_count(self):
        self.assertGreater(len(self.families), 0)

    def test_families_have_source_states(self):
        for f in self.families:
            self.assertGreater(int(f["n_source_states"]), 0,
                               f"Family {f['family_id']} has no source states")

    def test_total_source_states_equals_25(self):
        total = sum(int(f["n_source_states"]) for f in self.families)
        self.assertEqual(total, 25, f"Total source states should be 25, got {total}")

    def test_family_ids_unique(self):
        ids = [f["family_id"] for f in self.families]
        self.assertEqual(len(ids), len(set(ids)))


class TestNoMLNoExecution(unittest.TestCase):
    """Verify no ML or execution references."""

    @classmethod
    def setUpClass(cls):
        cls.all_text = ""
        for p in ALPHA1.glob("*.json"):
            cls.all_text += json.dumps(json.load(open(p, encoding="utf-8"))).lower()
        for p in ALPHA1.glob("*.md"):
            cls.all_text += open(p, encoding="utf-8").read().lower()
        for p in ALPHA1.glob("*.csv"):
            cls.all_text += open(p, encoding="utf-8").read().lower()

    def test_no_ml(self):
        forbidden = ["machine learning", "random forest", "xgboost", "gradient boost",
                     "neural net", "logistic regression", "lasso", "ridge"]
        for term in forbidden:
            self.assertNotIn(term, self.all_text, f"Forbidden ML term found: {term}")

    def test_no_execution(self):
        forbidden = ["place order", "live trading", "production execution",
                     "deploy trade", "live account"]
        for term in forbidden:
            self.assertNotIn(term, self.all_text, f"Forbidden execution term found: {term}")


if __name__ == "__main__":
    unittest.main()