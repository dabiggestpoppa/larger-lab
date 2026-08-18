"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 tests.

Locks the position-scaling / account-boundary truth repair:

- 1R definition unchanged (24.49489742783178 bps; NOT a hard stop).
- pos = TARGET_VOL/rv reconstruction on all 890 events.
- Corrected notional INCLUDES pos: N = E x f x pos x 1e4/RISK.
- Removing pos breaks parity (old fixed formula rejected).
- One-R underlying price move is event-specific: RISK/pos.
- USDJPY pip conversion fixtures.
- Account-impact units: % = r x admitted_f_pct (A worst -2.5588%, B worst
  -0.9939%), signed, never "maximum possible loss".
- H1 parity: 826 accepted / 64 rejected; rejected events -> zero exposure.
- Gross parity across every accepted event (machine precision).
- Account currency / broker product truth: research vs executable split,
  both unresolved until account binding.
- No broker calls; no science changes; TB Forward as engineering reference;
  handoff schema complete.
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

import run_exec_translation_planning_r1 as r1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"

RISK_UNIT_BPS = 24.49489742783178
FACTOR = 1e4 / RISK_UNIT_BPS

ARTIFACTS = [
    "CR_EXEC_R1_PROTOCOL.md", "CR_EXEC_R1_DEFECT_AUDIT.md",
    "CR_EXEC_R1_SOURCE_SHA_MANIFEST.json", "CR_EXEC_R1_POSITION_SCALING_DERIVATION.md",
    "CR_EXEC_R1_POSITION_DISTRIBUTION.csv", "CR_EXEC_R1_ONE_R_PRICE_MOVE_FIXTURES.csv",
    "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv", "CR_EXEC_R1_ACCOUNT_SIZE_MATRIX.csv",
    "CR_EXEC_R1_ACCOUNT_IMPACT_UNIT_REPAIR.csv", "CR_EXEC_R1_ACCOUNT_CURRENCY_TRUTH.md",
    "CR_EXEC_R1_PRODUCT_IDENTITY_TRUTH.md", "CR_EXEC_R1_COST_SCALING_AUDIT.md",
    "CR_EXEC_R1_GROSS_PARITY_890.json", "CR_EXEC_R1_NET_PARITY_890.json",
    "CR_EXEC_R1_H1_PARITY.json", "CR_EXEC_R1_ACCOUNT_CONTROL_PLANE_BOUNDARY.md",
    "CR_EXEC_R1_CROSS_BRANCH_EXECUTION_INVENTORY.csv",
    "CR_EXEC_R1_EXECUTION_FOUNDATION_HANDOFF_SCHEMA.json",
    "CR_EXEC_R1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json",
    "CR_EXEC_R1_COMPONENT_STATUS.csv", "CR_EXEC_R1_TEST_AUDIT.json",
    "CR_EXEC_R1_REPORT.md", "CR_EXEC_R1_DECISION.json",
]

DECISION_FIELDS = [
    "checkpoint", "status", "base_commit", "scale_science_unchanged", "n_events",
    "n_accepted", "n_rejected", "risk_unit_bps", "risk_unit_is_hard_stop",
    "position_scaling_required", "position_scaling_derivation_pass",
    "old_fixed_notional_formula_valid", "old_fixed_notional_formula_rejected",
    "one_r_price_move_is_event_specific", "pip_semantics_repaired",
    "account_impact_units_repaired", "research_reporting_currency",
    "executable_account_currency_resolved", "account_currency_contract_defined",
    "research_instrument", "broker_instrument_resolved",
    "broker_product_type_resolved", "cost_scaling_resolved",
    "gross_890_translation_parity_pass", "net_890_translation_parity_pass",
    "net_parity_broker_dependency", "h1_parity_pass",
    "account_control_plane_boundary_defined", "portfolio_master_requirement_defined",
    "tb_forward_cross_branch_audited", "execution_runtime_foundation_audited",
    "capital_routing_execution_boundary_defined", "broker_execution_performed",
    "implementation_ready", "implementation_authorized", "production_authorized",
    "human_review_required", "next_checkpoint_recommended",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_EXEC_R1_DECISION.json").read_text(encoding="utf-8"))


def _facts() -> dict:
    return r1.compute_facts()


# --------------------------------------------------------------------------
# 1-8: risk unit, pos, gross reconstruction, corrected notional, one-R move
# --------------------------------------------------------------------------

def test_1_risk_unit_definition_unchanged():
    d = _decision()
    assert d["risk_unit_bps"] == RISK_UNIT_BPS
    assert d["risk_unit_is_hard_stop"] is False
    assert abs(RISK_UNIT_BPS - 10.0 * np.sqrt(6.0)) < 1e-12


def test_2_pos_reconstruction_all_890():
    # pos = TARGET_VOL / rv, with the documented clamp "pos >= 1.0 when rv
    # missing" (8 rows have NaN rv_bps_per_h and pos = 1.0 exactly)
    ld = pd.read_csv(LEDGER)
    rv = ld["rv_bps_per_h"].to_numpy(dtype=float)
    pos_rec = np.where(np.isfinite(rv), 10.0 / rv, 1.0)
    assert np.allclose(pos_rec, ld["pos"].to_numpy(), rtol=1e-9, atol=1e-12)
    assert (ld["rv_bps_per_h"].isna() == (ld["pos"] == 1.0)).all()


def test_3_gross_pnl_reconstruction_all_890():
    ld = pd.read_csv(LEDGER)
    price_ret = (np.log(ld["exit_price"]) - np.log(ld["entry_price"])) * 1e4
    gross = ld["dir"] * ld["pos"] * price_ret
    pd.testing.assert_series_equal(gross.round(9), ld["gross_pnl_bps"].round(9),
                                   check_names=False)


def test_4_corrected_notional_includes_pos():
    f = _facts()
    fr = f["frames"]
    for i in np.where(fr["accepted"])[0][:5]:
        f_dec = 0.007 if fr["fam"][i] == "A" else 0.003
        expect = f_dec * fr["pos"][i] * FACTOR
        assert abs(fr["n_e"][i] - expect) < 1e-9


def test_5_removing_pos_causes_parity_failure():
    f = _facts()
    assert f["risks"]["old_formula_max_err"] > 1e-3  # materially wrong
    assert f["risks"]["old_formula_zero_error_only_pos_eq_1"]


def test_6_one_r_underlying_price_move_is_R_over_pos():
    ld = pd.read_csv(LEDGER)
    move = RISK_UNIT_BPS / ld["pos"]
    assert np.allclose(move, ld["risk_unit_bps"] / ld["pos"])  # identity by def
    # and it is NOT the fixed RISK value except when pos == 1
    assert not np.allclose(move, RISK_UNIT_BPS)


def test_7_event_specific_one_r_moves_vary():
    f = _facts()
    p = f["one_R_move_percentiles_accepted"]
    assert p["p0"] < p["p50"] < p["p100"]
    assert p["p100"] / p["p0"] > 10  # wide spread => event-specific


def test_8_usdjpy_pip_conversion_fixture():
    # 1R at pos=1.0 on USDJPY 150: 24.4949 bps -> 0.3674 JPY -> 36.74 pips (0.01)
    for pos_v, expect_pips in [(1.0, 36.74), (5.0, 7.35), (0.5, 73.49)]:
        bps = RISK_UNIT_BPS / pos_v
        raw_quote = 150.0 * bps / 1e4
        pips = raw_quote / 0.01
        assert abs(pips - expect_pips) < 0.02
    fx = pd.read_csv(OUT / "CR_EXEC_R1_ONE_R_PRICE_MOVE_FIXTURES.csv")
    assert len(fx) >= 9
    assert (fx["one_R_price_move_bps"] > 0).all()


# --------------------------------------------------------------------------
# 9-10: account impact units
# --------------------------------------------------------------------------

def test_9_worst_A_account_impact_units():
    ld = pd.read_csv(LEDGER)
    w = float(ld.loc[ld["family"] == "A", "r_multiple"].min())
    impact_pct = w * 0.70  # r x admitted_f_pct
    assert abs(impact_pct - (-2.5588)) < 1e-3
    assert abs(impact_pct - r1.compute_facts()["worst_account_impact_A_pct"]) < 1e-9
    # repaired CSV carries the signed percent, not 255.88
    rep = pd.read_csv(OUT / "CR_EXEC_R1_ACCOUNT_IMPACT_UNIT_REPAIR.csv")
    a = rep[rep["family"] == "A"]
    assert float(a["historical_observed_account_impact_pct"].min()) < -2.5


def test_10_worst_B_account_impact_units():
    ld = pd.read_csv(LEDGER)
    w = float(ld.loc[ld["family"] == "B", "r_multiple"].min())
    impact_pct = w * 0.30
    assert abs(impact_pct - (-0.9939)) < 1e-3


# --------------------------------------------------------------------------
# 11-14: H1 admission parity
# --------------------------------------------------------------------------

def test_11_rejected_h1_event_zero_exposure():
    f = _facts()
    fr = f["frames"]
    assert (fr["n_e"][~fr["accepted"]] == 0.0).all()
    df = pd.read_csv(OUT / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv")
    rej = df[df["status"] == "REJECT_HEAT_CAP"]
    assert len(rej) == 64
    assert (rej["notional_multiple_equity"] == 0.0).all()


def test_12_accepted_A_requested_f_070():
    f = _facts()
    assert f["requested_f_A"] == 0.70


def test_13_accepted_B_requested_f_030():
    f = _facts()
    assert f["requested_f_B"] == 0.30


def test_14_826_64_admission_preserved():
    f = _facts()
    assert f["n_accepted"] == 826
    assert f["n_rejected"] == 64
    assert f["accepted_A"] == 371
    assert f["accepted_B"] == 455
    h = json.loads((OUT / "CR_EXEC_R1_H1_PARITY.json").read_text(encoding="utf-8"))
    assert h["n_accepted"] == 826 and h["n_rejected"] == 64
    assert h["rejected_zero_exposure"] is True


# --------------------------------------------------------------------------
# 15-18: parity + fixtures
# --------------------------------------------------------------------------

def test_15_corrected_gross_parity_every_accepted_event():
    f = _facts()
    assert f["risks"]["gross_parity_pass"] is True
    assert f["risks"]["gross_parity_max_err"] < 1e-12
    g = json.loads((OUT / "CR_EXEC_R1_GROSS_PARITY_890.json").read_text(encoding="utf-8"))
    assert g["pass"] is True and len(g["events"]) == 890
    acc = [e for e in g["events"] if e["accepted"]]
    assert len(acc) == 826
    assert max(e["abs_error"] for e in acc) < 1e-12


def test_16_long_and_short_parity():
    f = _facts()
    fr = f["frames"]
    pos_ok = fr["accepted"] & (fr["fam"] == "A")
    neg_ok = fr["accepted"] & (fr["fam"] == "B")
    assert fr["gross_err"][pos_ok].max() < 1e-12
    assert fr["gross_err"][neg_ok].max() < 1e-12


def test_17_low_pos_fixture():
    ld = pd.read_csv(LEDGER)
    low = ld.loc[ld["pos"].idxmin()]
    move = RISK_UNIT_BPS / low["pos"]
    assert move > 200  # low pos -> large one-R price move (up to ~222 bps)


def test_18_high_pos_fixture():
    ld = pd.read_csv(LEDGER)
    high = ld.loc[ld["pos"].idxmax()]
    move = RISK_UNIT_BPS / high["pos"]
    assert move < 1.4  # high pos -> tiny one-R price move (~1.35 bps)


# --------------------------------------------------------------------------
# 19-22: currency / product truth
# --------------------------------------------------------------------------

def test_19_account_currency_unresolved_until_binding():
    d = _decision()
    assert d["executable_account_currency_resolved"] is False


def test_20_research_reporting_currency_distinct():
    d = _decision()
    assert d["research_reporting_currency"] == "USD"
    assert d["account_currency_contract_defined"] is True


def test_21_broker_symbol_unresolved():
    d = _decision()
    assert d["broker_instrument_resolved"] is False
    inv = pd.read_csv(OUT / "CR_EXEC_R1_CROSS_BRANCH_EXECUTION_INVENTORY.csv")
    assert len(inv) >= 5


def test_22_broker_product_type_unresolved():
    d = _decision()
    assert d["broker_product_type_resolved"] is False
    assert d["research_instrument"] == "USDJPY"


# --------------------------------------------------------------------------
# 23-28: no broker calls, no science change, cross-branch, schemas
# --------------------------------------------------------------------------

def test_23_no_broker_calls():
    d = _decision()
    assert d["broker_execution_performed"] is False
    # no execution-capable API calls in the R1 runner (TradeLocker / MT5 appear
    # only in boundary DOCS as things Capital Routing must NOT own)
    src = Path(r1.__file__).read_text(encoding="utf-8")
    for bad in ["order_send(", "place_order(", "order_submit(", "tradeocker.",
                "mt5.initialize", "broker_api.", "create_order("]:
        assert bad.lower() not in src.lower()


def test_24_no_strategy_science_changes():
    d = _decision()
    assert d["scale_science_unchanged"] is True
    assert d["n_events"] == 890 and d["n_accepted"] == 826 and d["n_rejected"] == 64


def test_25_no_cr_math_changes_except_translation():
    # 1R / pos / gross_pnl still reconstruct from the SEALED ledger untouched
    test_1_risk_unit_definition_unchanged()
    test_2_pos_reconstruction_all_890()
    test_3_gross_pnl_reconstruction_all_890()


def test_26_tb_forward_included_as_engineering_reference():
    inv = pd.read_csv(OUT / "CR_EXEC_R1_CROSS_BRANCH_EXECUTION_INVENTORY.csv")
    tb = inv[inv["resource"].str.contains("tb-forward-engine")].iloc[0]
    assert "PROVEN ENGINEERING REFERENCE" in tb["classification"]
    assert tb["reusable_for_cr_execution"] != "YES"
    d = _decision()
    assert d["tb_forward_cross_branch_audited"] is True


def test_27_no_tb_import():
    # Capital Routing must not import TB strategy/runtime code. The word
    # "tb_forward" appears only as audit-field names, never as an import.
    import ast
    src = Path(r1.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any("tb" in i.lower().split(".")[0] for i in imports)
    d = _decision()
    assert d["execution_runtime_foundation_audited"] is True


def test_28_execution_foundation_handoff_schema_complete():
    h = json.loads((OUT / "CR_EXEC_R1_EXECUTION_FOUNDATION_HANDOFF_SCHEMA.json")
                   .read_text(encoding="utf-8"))
    for key in ["translation_request_id", "event_id", "family", "portfolio_group_id",
                "account_id", "side", "admitted_f_pct", "pos_t",
                "target_notional_account_ccy", "account_currency",
                "one_R_price_move_bps", "model_heat_before", "model_heat_after",
                "policy_id", "configuration_hash", "ownership_tag",
                "decision_timestamp", "expiration_timestamp", "exit_contract"]:
        assert key in h["fields"], f"missing handoff field {key}"
    req = json.loads((OUT / "CR_EXEC_R1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    assert req["input_from_capital_router"]["risk_unit_bps"] == RISK_UNIT_BPS


# --------------------------------------------------------------------------
# Artifacts + decision completeness
# --------------------------------------------------------------------------

def test_all_r1_artifacts_exist():
    missing = [f for f in ARTIFACTS if not (OUT / f).exists()]
    assert missing == [], f"missing R1 artifacts: {missing}"


def test_decision_fields_and_expected_truth():
    d = _decision()
    missing = [k for k in DECISION_FIELDS if k not in d]
    assert missing == [], f"missing decision fields: {missing}"
    assert d["checkpoint"] == r1.CHECKPOINT
    assert d["base_commit"] == r1.BASE_COMMIT
    assert d["status"] == "PASS"
    assert d["position_scaling_required"] is True
    assert d["position_scaling_derivation_pass"] is True
    assert d["old_fixed_notional_formula_valid"] is False
    assert d["old_fixed_notional_formula_rejected"] is True
    assert d["one_r_price_move_is_event_specific"] is True
    assert d["pip_semantics_repaired"] is True
    assert d["account_impact_units_repaired"] is True
    assert d["gross_890_translation_parity_pass"] is True
    assert d["h1_parity_pass"] is True
    assert d["implementation_ready"] is True
    assert d["implementation_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0"


def test_account_size_matrix_rebuilt_event_level():
    m = pd.read_csv(OUT / "CR_EXEC_R1_ACCOUNT_SIZE_MATRIX.csv")
    assert len(m) == 10  # 5 account sizes x 2 families
    row = m[(m["equity_usd"] == 10000) & (m["family"] == "A")].iloc[0]
    assert row["one_R_budget_usd"] == 70.0
    # max notional at $10k A = 10000 x max(accepted-A notional/equity),
    # derived from the sealed ledger + admission (not a hardcoded pos)
    mult = pd.read_csv(OUT / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv")
    a = mult[(mult["family"] == "A") & (mult["status"] == "ACCEPT_FULL")]
    assert abs(row["max_target_notional_usd"]
               - 10000 * a["notional_multiple_equity"].max()) < 1.0
    assert row["historical_worst_observed_account_impact_pct"] < -2.5
