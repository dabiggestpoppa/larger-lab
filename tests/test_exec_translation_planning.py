"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING verification tests.

Locks the source-truth audit facts proven by the planning checkpoint:

- 1R = TARGET_VOL x sqrt(6h) = 24.49489742783178 bps; NOT a hard stop.
- pnl_bps construction: dir x pos x price_return - cost with pos = TARGET_VOL/rv,
  fixture-verified against the sealed ledger.
- 1R -> notional: N = E x f / (1R_bps/1e4); per-family multipliers under the
  preferred research default (A 0.70 -> 2.8577x, B 0.30 -> 1.2247x).
- H1-1.00-REJ @ A1_70_30 reproduces the sealed admission (826 accepted /
  64 rejected); requested_f A 0.70 / B 0.30.
- Sealed book facts: 890 events (A 432 / B 458), splits, worst R.
- All 26 planning artifacts exist; the decision carries every required field
  with the expected truth (no authorization).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
for _p in (_SRC, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

import run_exec_translation_planning as plan  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning"
TRADES = ROOT / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"

RISK_UNIT_BPS = 24.49489742783178

ARTIFACTS = [
    "CR_EXEC_TRANSLATION_PROTOCOL.md",
    "CR_EXEC_TRANSLATION_SOURCE_TRUTH_AUDIT.md",
    "CR_EXEC_TRANSLATION_EVENT_LINEAGE.json",
    "CR_EXEC_TRANSLATION_EVENT_SCHEMA.json",
    "CR_EXEC_TRANSLATION_RISK_UNIT_AUDIT.md",
    "CR_EXEC_TRANSLATION_PNL_BPS_AUDIT.md",
    "CR_EXEC_TRANSLATION_EQUITY_BASIS_CONTRACT.md",
    "CR_EXEC_TRANSLATION_INSTRUMENT_INVENTORY.csv",
    "CR_EXEC_TRANSLATION_BROKER_PATH_INVENTORY.csv",
    "CR_EXEC_TRANSLATION_PRODUCT_TYPE_MATRIX.csv",
    "CR_EXEC_TRANSLATION_QUANTITY_FORMULA_CONTRACT.md",
    "CR_EXEC_TRANSLATION_ROUNDING_CONTRACT.md",
    "CR_EXEC_TRANSLATION_MARGIN_BUYING_POWER_CONTRACT.md",
    "CR_EXEC_TRANSLATION_COST_PARITY_PLAN.md",
    "CR_EXEC_TRANSLATION_MODEL_VS_ACTUAL_HEAT_CONTRACT.md",
    "CR_EXEC_TRANSLATION_RESERVATION_STATE_MACHINE.md",
    "CR_EXEC_TRANSLATION_FAILURE_CATALOG.json",
    "CR_EXEC_TRANSLATION_OWNERSHIP_RECONCILIATION_PLAN.md",
    "CR_EXEC_TRANSLATION_RESTART_RECOVERY_PLAN.md",
    "CR_EXEC_TRANSLATION_PARITY_FIXTURE_PLAN.md",
    "CR_EXEC_TRANSLATION_ACCOUNT_SIZE_MATRIX.csv",
    "CR_EXEC_TRANSLATION_IMPLEMENTATION_BLOCK_PLAN.md",
    "CR_EXEC_TRANSLATION_TEST_PLAN.md",
    "CR_EXEC_TRANSLATION_COMPONENT_STATUS.csv",
    "CR_EXEC_TRANSLATION_REPORT.md",
    "CR_EXEC_TRANSLATION_DECISION.json",
]

DECISION_FIELDS = [
    "checkpoint", "status", "base_commit", "block3_scale_seal_verified",
    "risk_unit_bps", "risk_unit_semantics_verified", "risk_unit_is_hard_stop",
    "pnl_bps_semantics_resolved", "event_source_lineage_resolved",
    "instrument_universe_resolved", "product_types_resolved",
    "account_currency_resolved", "equity_basis_proposed",
    "one_r_to_notional_formula_resolved", "formula_proven_against_fixtures",
    "cost_scaling_resolved", "rounding_policy_resolved",
    "post_rounding_heat_contract_resolved", "margin_gate_design_resolved",
    "reservation_state_design_resolved", "ownership_design_resolved",
    "restart_reconciliation_design_resolved", "broker_path_inventory_complete",
    "historical_890_event_parity_plan_complete", "preferred_research_default",
    "production_scale_selected", "broker_selected",
    "broker_execution_authorized", "deployment_authorized", "mt5_authorized",
    "planning_pass", "implementation_ready", "implementation_authorized",
    "next_checkpoint_recommended", "human_review_required",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_EXEC_TRANSLATION_DECISION.json")
                      .read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Sealed book facts
# --------------------------------------------------------------------------

def test_sealed_book_counts():
    t = pd.read_csv(TRADES)
    assert len(t) == 890
    assert t["family"].value_counts().to_dict() == {"B": 458, "A": 432}
    assert (t["hold_h"] == 6.0).all()
    assert set(t["dir"].unique()) == {1.0, -1.0}


def test_1r_definition():
    assert abs(RISK_UNIT_BPS - 10.0 * np.sqrt(6.0)) < 1e-9
    d = _decision()
    assert d["risk_unit_bps"] == RISK_UNIT_BPS
    assert d["risk_unit_is_hard_stop"] is False


def test_worst_r_extremes_match_block1():
    ld = pd.read_csv(LEDGER)
    assert round(float(ld.loc[ld["family"] == "A", "r_multiple"].min()), 2) == -3.66
    assert round(float(ld.loc[ld["family"] == "B", "r_multiple"].min()), 2) == -3.31


# --------------------------------------------------------------------------
# pnl_bps construction (fixture-verified)
# --------------------------------------------------------------------------

def test_pnl_bps_fixture_reconstruction():
    """Reconstruct pnl_bps from entry/exit/dir/pos on the first ledger row."""
    ld = pd.read_csv(LEDGER)
    r0 = ld.iloc[0]
    price_ret = (np.log(r0["exit_price"]) - np.log(r0["entry_price"])) * 1e4
    gross = float(r0["dir"]) * float(r0["pos"]) * price_ret
    assert abs(gross - r0["gross_pnl_bps"]) < 1e-6
    net = gross - r0["cost_pnl_bps"]
    assert abs(net - r0["pnl_bps"]) < 1e-6
    r_mult = net / r0["risk_unit_bps"]
    assert abs(r_mult - r0["r_multiple"]) < 1e-9
    # pos = TARGET_VOL / rv
    assert abs(float(r0["pos"]) - 10.0 / r0["rv_bps_per_h"]) < 1e-6


def test_pnl_bps_all_rows_reconstruct():
    """Reconstruction must hold on EVERY sealed ledger row (not just row 1)."""
    ld = pd.read_csv(LEDGER)
    price_ret = (np.log(ld["exit_price"]) - np.log(ld["entry_price"])) * 1e4
    gross = ld["dir"] * ld["pos"] * price_ret
    pd.testing.assert_series_equal(gross.round(9),
                                   ld["gross_pnl_bps"].round(9),
                                   check_names=False)
    net = gross - ld["cost_pnl_bps"]
    pd.testing.assert_series_equal(net.round(9), ld["pnl_bps"].round(9),
                                   check_names=False)


# --------------------------------------------------------------------------
# 1R -> notional formula
# --------------------------------------------------------------------------

def test_one_r_to_notional_formula():
    factor = 1e4 / RISK_UNIT_BPS
    assert abs(factor - 408.24829) < 1e-3
    # A at 0.70%: N/E = 0.007 x factor
    assert abs(0.007 * factor - 2.8577) < 1e-3
    # B at 0.30%: N/E = 0.003 x factor
    assert abs(0.003 * factor - 1.2247) < 1e-3
    # dollar check at $10k: A 1R budget = $70 -> notional ~$28,577
    assert abs(10000 * 0.007 * factor - 28577.4) < 1.0


def test_1r_budget_dollar_meaning():
    """A +1R move on the translated notional produces exactly admitted_f x E."""
    E = 10000.0
    for fam, w, mult in [("A", 0.70, 2.8577), ("B", 0.30, 1.2247)]:
        budget = E * w / 100.0
        notional = budget * (1e4 / RISK_UNIT_BPS)
        pnl_at_1r = notional * RISK_UNIT_BPS / 1e4
        assert abs(pnl_at_1r - budget) < 1e-6  # 1R move == f x E dollars
        assert abs(notional / E - mult) < 1e-3


# --------------------------------------------------------------------------
# H1 admission examples (A1_70_30, H1-1.00-REJ)
# --------------------------------------------------------------------------

def test_h1_examples_heat_units():
    # A+A = 1.40 requested -> second A fails H1 (cap 1.00)
    assert 0.70 + 0.70 > 1.00
    # A+B = 1.00 exactly at cap
    assert abs(0.70 + 0.30 - 1.00) < 1e-12
    # B+B+B = 0.90 under cap
    assert 0.30 * 3 < 1.00


def test_h1_admission_reproduces_sealed_book():
    f = plan.compute_facts()
    adm = f["admission"]
    assert adm["n_events"] == 890
    assert adm["requested_f_A"] == 0.70
    assert adm["requested_f_B"] == 0.30
    assert adm["decisions"] == {"ACCEPT_FULL": 826, "REJECT_HEAT_CAP": 64}
    assert adm["n_accepted_A"] == 371
    assert adm["n_accepted_B"] == 455


# --------------------------------------------------------------------------
# Artifacts + decision
# --------------------------------------------------------------------------

def test_all_planning_artifacts_exist():
    missing = [f for f in ARTIFACTS if not (OUT / f).exists()]
    assert missing == [], f"missing planning artifacts: {missing}"


def test_decision_carries_every_required_field():
    d = _decision()
    missing = [f for f in DECISION_FIELDS if f not in d]
    assert missing == [], f"missing decision fields: {missing}"
    assert d["checkpoint"] == "CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING"
    assert d["base_commit"] == "40d237123ac2b709cc0ebce1d7f057bbfde25dab"


def test_expected_truth_values():
    d = _decision()
    assert d["status"] == "PASS"
    assert d["block3_scale_seal_verified"] is True
    assert d["planning_pass"] is True
    assert d["implementation_ready"] is True
    assert d["implementation_authorized"] is False
    assert d["broker_selected"] is False
    assert d["broker_execution_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False
    assert d["production_scale_selected"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == \
        "CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0"


def test_preferred_default():
    d = _decision()
    pref = d["preferred_research_default"]
    assert pref["allocation"] == "A1_70_30"
    assert pref["heat_architecture"] == "H1-1.00-REJ"
    assert pref["f_total_pct"] == 1.00
    assert pref["family_A_event_fraction_pct"] == 0.70
    assert pref["family_B_event_fraction_pct"] == 0.30
    assert "not production sizing" in pref["role"].lower()


def test_no_fabricated_broker_fields():
    inv = pd.read_csv(OUT / "CR_EXEC_TRANSLATION_INSTRUMENT_INVENTORY.csv")
    row = inv.iloc[0]
    assert row["research_symbol"] == "USDJPY"
    assert row["broker_symbol"] == "MISSING_EXECUTION_TRANSLATION_FIELD"
    assert row["margin_requirement"] == "MISSING_EXECUTION_TRANSLATION_FIELD"
    assert row["minimum_quantity"] == "MISSING_EXECUTION_TRANSLATION_FIELD"


def test_broker_path_inventory_no_reusable_execution():
    b = pd.read_csv(OUT / "CR_EXEC_TRANSLATION_BROKER_PATH_INVENTORY.csv")
    assert len(b) >= 7
    assert not b["reusable_for_execution"].isin(["YES"]).any()


def test_account_size_matrix_science_columns():
    m = pd.read_csv(OUT / "CR_EXEC_TRANSLATION_ACCOUNT_SIZE_MATRIX.csv")
    assert len(m) == 5
    row = m[m["equity_usd"] == 10000].iloc[0]
    assert abs(row["A_one_R_budget_usd"] - 70.0) < 1e-6
    assert abs(row["B_one_R_budget_usd"] - 30.0) < 1e-6
    assert abs(row["A_target_notional_usd"] - 28577.1) < 1.0
    assert abs(row["B_target_notional_usd"] - 12247.3) < 1.0
