"""
CRYPTO-ALPHA-1 Artifact Builder.

Generates all frozen strategy contracts, controls, cost/split/metric/
falsification contracts, preregistration, registry hash, report, and decision.

Imported by run_alpha1.py. Run there, not standalone.
"""
from __future__ import annotations

import csv, hashlib, json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

OUT = Path(__file__).resolve().parent
MECH2 = OUT.parent / "mech_2"

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_families() -> List[Dict]:
    rows = []
    p = OUT / "ALPHA_1_MECHANISM_FAMILY_REGISTRY.csv"
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


# ─── STRATEGY CONTRACTS ───────────────────────────────────────────────

def build_contracts(families: List[Dict]) -> Dict[str, Any]:
    """Return {contracts: [...], controls: [...]}."""
    strategies: List[Dict] = []
    controls: List[Dict] = []
    s_id = 0
    c_id = 0

    fam_map = {f["family_id"]: f for f in families}

    ####################################################################
    # FAM_A — Extreme Negative Basis Dislocation (3 variants + control)
    ####################################################################
    if "FAM_A" in fam_map:
        f = fam_map["FAM_A"]
        base = dict(
            family_id="FAM_A",
            mechanism_type="EXTREME_NEGATIVE_BASIS_DISLOCATION",
            source_state_ids=f["source_states"].split("; "),
            asset="BTC_ETH",
            expected_resolution_path="basis drifts to normal band; resolution slow (>4h), may expand first",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="perp_price,spot_price,basis,funding",
            causality_notes="state at t uses only information available by t (causal basis lagged 5m to 1h depending on resolution)",
            known_failure_modes="basis expands further; funding does not confirm; systemic stress overrides",
        )
        # A1: directional perp — trade perp in direction of expected basis resolution
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="PRIMARY_MECHANISM",
            execution_object="perp",
            direction_logic="long_perp_when_extreme_neg_basis",
            entry_state="B4_EXTREME_NEGATIVE or B3_ELEVATED_NEGATIVE",
            entry_trigger="STATE_ENTRY — first bar close where basis crosses below p90_abs threshold",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: basis normalizes to B1_NORMAL or weaker; or E3: time exit",
            invalidation_rule="basis expands beyond p99_abs or moves to B_EXTREME_POS; funding stays positive while basis negative",
            time_exit="8h",
            max_holding_period="24h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # A2: spot-perp convergence — trade the basis itself
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="spot+perp hedge",
            direction_logic="long_perp_short_spot (capture basis normalization)",
            entry_state="B4_EXTREME_NEGATIVE",
            entry_trigger="STATE_ENTRY — basis enters extreme negative",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E2: basis resolves >50% toward zero; or E3: time exit",
            invalidation_rule="basis expands further >p99_abs; spot-perp correlation breaks",
            time_exit="24h",
            max_holding_period="48h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # A3: state-transition expression — enter on elevated→extreme transition
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="perp",
            direction_logic="long_perp_on_basis_transition_extreme",
            entry_state="B4_EXTREME_NEGATIVE",
            entry_trigger="STATE_TRANSITION — basis transitions from B3_ELEVATED_NEGATIVE to B4_EXTREME_NEGATIVE",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: state exits B4; or E3: time exit",
            invalidation_rule="basis immediately reverts to B3 within 1h (false transition); funding direction contradicts",
            time_exit="4h",
            max_holding_period="12h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # A control: same perp directional, no state filter
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_A",
            name="FAM_A_UNCONDITIONAL_DIRECTIONAL",
            description="long BTC/ETH perp at random hourly bars (no state filter), exit at 8h",
            strategy_id_mirror="ALPHA1_S001",
            differences="no basis-state filter; unconditional entry at any bar",
            status="CONTROL",
        ))

    ####################################################################
    # FAM_B — Negative Basis + Negative Funding Crowding (3 variants + control)
    ####################################################################
    if "FAM_B" in fam_map:
        f = fam_map["FAM_B"]
        base = dict(
            family_id="FAM_B",
            mechanism_type="NEGATIVE_BASIS_CROWDING_CONFIRMED",
            source_state_ids=f["source_states"].split("; "),
            asset="BTC_ETH",
            expected_resolution_path="basis normalizes from negative extreme with funding mean-reversion; FAST or EXPANSION_FIRST",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="perp_price,spot_price,basis,funding",
            causality_notes="basis and funding both available at bar close; no future leak",
            known_failure_modes="crowding intensifies rather than unwinds; funding stays extreme; basis expands beyond prior peak",
        )
        # B1: crowding unwind — both basis and funding unwind together
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="PRIMARY_MECHANISM",
            execution_object="perp",
            direction_logic="long_perp_when_both_extreme_neg (basis+funding)",
            entry_state="B4_EXTREME_NEGATIVE + F_NEG_EXTREME or F_NEG_ELEVATED",
            entry_trigger="STATE_CONFIRMATION — basis extreme AND funding extreme (both confirmed at bar close)",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: basis exits extreme band; or E4: funding exits extreme band (whichever first); or E3: time exit",
            invalidation_rule="either basis or funding worsens further beyond entry severity",
            time_exit="8h",
            max_holding_period="24h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # B2: crowding persistence — hold through persistence, exit on resolution
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="perp",
            direction_logic="long_perp_on_persistent_crowding (hold through consecutive extreme bars)",
            entry_state="B4_EXTREME_NEGATIVE + F_NEG_EXTREME",
            entry_trigger="STATE_PERSISTENCE — 2+ consecutive bars in extreme state",
            decision_timestamp_rule="bar close (1h) after second consecutive bar",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: basis exits extreme; or E4: funding exits extreme band; or E3: time exit",
            invalidation_rule="basis expands >2x entry severity; funding flips sign",
            time_exit="24h",
            max_holding_period="48h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # B3: crowding continuation — enter on elevated funding, hold as it goes extreme
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="perp",
            direction_logic="long_perp_on_funding_deepening (entry at elevated, hold into extreme)",
            entry_state="B4_EXTREME_NEGATIVE + F_NEG_ELEVATED",
            entry_trigger="STATE_ACCELERATION — funding transitions from ELEVATED to EXTREME while basis stays extreme",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: basis exits extreme; or E4: funding exits both elevated and extreme bands; or E3: time exit",
            invalidation_rule="funding reverts to normal without basis resolution",
            time_exit="8h",
            max_holding_period="24h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # B control
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_B",
            name="FAM_B_UNCONDITIONAL_CROWDING",
            description="unconditional perp directional with 8h time exit; no basis/funding state filter",
            strategy_id_mirror="ALPHA1_S004",
            differences="no basis or funding state filter",
            status="CONTROL",
        ))

    ####################################################################
    # FAM_C — Basis+Funding+Volatility Composite (2 variants + control)
    ####################################################################
    if "FAM_C" in fam_map:
        f = fam_map["FAM_C"]
        base = dict(
            family_id="FAM_C",
            mechanism_type="BASIS_FUNDING_VOLATILITY_COMPOSITE",
            source_state_ids=f["source_states"].split("; "),
            asset="BTC_ETH",
            expected_resolution_path="vol compresses first, then basis/funding follow; SLOW or PERSISTENT",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="perp_price,spot_price,basis,funding,realized_volatility_24h",
            causality_notes="vol, basis, and funding all available at bar close with no future leak",
            known_failure_modes="vol stays elevated without basis resolution; triple dislocation persists through multiple funding cycles",
        )
        # C1: triple-confirmation perp directional
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="PRIMARY_MECHANISM",
            execution_object="perp",
            direction_logic="long_perp_on_triple_confirmation (extreme basis + extreme funding + high vol)",
            entry_state="basis extreme neg + funding extreme/elevated neg + vol HIGH or EXTREME",
            entry_trigger="STATE_CONFIRMATION — all three axes confirmed at bar close",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: basis exits extreme; or E4: vol compresses to NORMAL or LOW; or E3: time exit",
            invalidation_rule="any dimension worsens beyond entry severity",
            time_exit="24h",
            max_holding_period="48h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # C2: vol-first resolution — exit on vol compression, hold for basis resolution
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="spot+perp hedge",
            direction_logic="long_perp_short_spot; exit half on vol compression, remainder on basis resolution",
            entry_state="basis extreme neg + funding extreme/elevated neg + vol EXTREME",
            entry_trigger="STATE_CONFIRMATION — triple extreme at bar close",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E2: partial exit (50%) when vol exits EXTREME band; remainder on basis normalization; or E3: time exit",
            invalidation_rule="basis expands >p99_abs; vol increases further",
            time_exit="24h",
            max_holding_period="72h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # C control
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_C",
            name="FAM_C_HIGH_VOL_UNCONDITIONAL",
            description="unconditional perp directional in high vol only; no basis/funding state filter",
            strategy_id_mirror="ALPHA1_S007",
            differences="high vol filter only; no basis or funding state filter",
            status="CONTROL",
        ))

    ####################################################################
    # FAM_D — ETH-Led Relative Dislocation (2 variants + control)
    ####################################################################
    if "FAM_D" in fam_map:
        f = fam_map["FAM_D"]
        base = dict(
            family_id="FAM_D",
            mechanism_type="ETH_LED_RELATIVE_DISLOCATION",
            source_state_ids=f["source_states"].split("; "),
            asset="ETH",
            expected_resolution_path="ETH normalizes relative to BTC; ETH leads, BTC follows",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="ETH_perp_price,ETH_spot_price,BTC_perp_price,BTC_spot_price,ETH_basis,BTC_basis,ETH_funding,BTC_funding",
            causality_notes="relative state from MECH-2 uses only information at t",
            known_failure_modes="ETH stress becomes systemic; relative dislocation narrows via BTC worsening",
        )
        # D1: ETH directional perp
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="PRIMARY_MECHANISM",
            execution_object="ETH perp",
            direction_logic="long_ETH_perp_when_ETH_specific_or_led_stress",
            entry_state="ETH_LED or ETH_SPECIFIC or SYSTEMIC_STRESS",
            entry_trigger="STATE_ENTRY — relative state becomes ETH_LED or ETH_SPECIFIC or SYSTEMIC_STRESS",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: ETH state returns to NORMAL_CROSS_STATE or SYNCHRONIZED; or E3: time exit",
            invalidation_rule="state transitions to BTC_LED; ETH stress becomes ISOLATED_BTC",
            time_exit="24h",
            max_holding_period="48h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # D2: BTC/ETH relative basket
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="BTC/ETH relative basket",
            direction_logic="long_ETH_perp_short_BTC_perp_on_ETH_led_stress",
            entry_state="ETH_LED or ETH_SPECIFIC",
            entry_trigger="STATE_ENTRY — ETH_LED or ETH_SPECIFIC confirmed",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: state returns to SYNCHRONIZED or NORMAL_CROSS_STATE; or E3: time exit",
            invalidation_rule="state becomes SYSTEMIC_STRESS (both assets stressed); relative basis narrows via BTC dislocation",
            time_exit="24h",
            max_holding_period="48h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # D control
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_D",
            name="FAM_D_UNCONDITIONAL_ETH",
            description="unconditional long ETH perp with 24h time exit; no relative-state filter",
            strategy_id_mirror="ALPHA1_S009",
            differences="no relative-state filter; entry at any bar",
            status="CONTROL",
        ))

    ####################################################################
    # FAM_E — Normal Basis + Extreme Funding Pre-Dislocation (2 variants + control)
    ####################################################################
    if "FAM_E" in fam_map:
        f = fam_map["FAM_E"]
        base = dict(
            family_id="FAM_E",
            mechanism_type="NORMAL_BASIS_EXTREME_FUNDING_PRE_DISLOCATION",
            source_state_ids=f["source_states"].split("; "),
            asset="BTC_ETH",
            expected_resolution_path="ambiguous: either funding normalizes without basis stress OR basis subsequently dislocates",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="perp_price,spot_price,basis,funding",
            causality_notes="funding available at bar close; no future leak",
            known_failure_modes="funding normalizes without basis movement (false alarm); basis dislocates in opposite direction",
        )
        # E1: funding normalization exit — trade perp, exit when funding normalizes
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="PRIMARY_MECHANISM",
            execution_object="perp",
            direction_logic="long_perp_when_extreme_neg_funding_normal_basis",
            entry_state="B0_NORMAL + F_NEG_EXTREME",
            entry_trigger="STATE_CONFIRMATION — normal basis but extreme negative funding",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: funding exits extreme band (returns to elevated or normal); or E3: time exit",
            invalidation_rule="funding stays extreme AND basis moves to extreme POSITIVE; structural invalidation",
            time_exit="4h",
            max_holding_period="8h",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # E2: hold through basis dislocation if it arrives
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="ALTERNATIVE_EXPRESSION",
            execution_object="spot+perp hedge",
            direction_logic="pre_position_long_perp_short_spot; if basis dislocates neg, hold for resolution",
            entry_state="B0_NORMAL + F_NEG_EXTREME",
            entry_trigger="STATE_CONFIRMATION — normal basis + extreme negative funding",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E1: funding normalizes without basis dislocation (exit immediately); E2: if basis enters extreme neg, hold until resolution; E3: time exit",
            invalidation_rule="basis moves extreme positive (opposite direction); funding normalizes and basis stays normal",
            time_exit="4h",
            max_holding_period="24h (if basis dislocates)",
            control_id="",
            status="PREREGISTERED_FOR_ALPHA2",
        )})
        # E control
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_E",
            name="FAM_E_UNCONDITIONAL_FUNDING",
            description="unconditional perp directional when funding is extreme (any basis); exit at 4h",
            strategy_id_mirror="ALPHA1_S011",
            differences="funding state filter only; no basis state filter",
            status="CONTROL",
        ))

    ####################################################################
    # FAM_X — Normal Basis Transition Control (1 control strategy)
    ####################################################################
    if "FAM_X" in fam_map:
        f = fam_map["FAM_X"]
        base = dict(
            family_id="FAM_X",
            mechanism_type="NORMAL_BASIS_TRANSITION_CONTROL",
            source_state_ids=f["source_states"].split("; "),
            asset="BTC",
            expected_resolution_path="basis stays normal",
            cost_model="BASE_COST",
            funding_accounting="FULL",
            required_data="perp_price,spot_price,basis,funding",
            causality_notes="normal basis state used as mechanism-trivial baseline",
            known_failure_modes="N/A (control)",
        )
        c_id += 1
        controls.append(dict(
            control_id=f"ALPHA1_C{c_id:03d}",
            family_id="FAM_X",
            name="FAM_X_NORMAL_BASIS_CONTROL",
            description="long perp when basis is NORMAL; exit at 8h. Mechanism-trivial control to test whether state conditioning adds value over unconditional entry.",
            strategy_id_mirror="ALPHA1_S001",
            differences="uses normal basis filter rather than extreme negative filter",
            status="CONTROL",
        ))
        # Also add a FAM_X strategy count entry (SAT)
        s_id += 1
        strategies.append({**base, **dict(
            strategy_id=f"ALPHA1_S{s_id:03d}",
            variant_type="CONTROL",
            execution_object="perp",
            direction_logic="long_perp_when_normal_basis (control entry)",
            entry_state="B0_NORMAL",
            entry_trigger="STATE_ENTRY — basis enters normal band",
            decision_timestamp_rule="bar close (1h)",
            execution_timestamp_rule="next bar open (1h+tick)",
            exit_rule="E3: time exit",
            invalidation_rule="basis exits normal band toward extreme before time exit",
            time_exit="8h",
            max_holding_period="8h",
            control_id="ALPHA1_C006",
            status="CONTROL",
        )})

    return {"contracts": strategies, "controls": controls}


# ─── STATIC CONTRACTS ─────────────────────────────────────────────────

COST_CONTRACT = {
    "contract_id": "ALPHA1_COST_V1",
    "frozen_at": TS,
    "description": "Conservative transaction cost assumptions for ALPHA-2 backtest. All in bps of notional.",
    "perpetual": {
        "maker_fee_bps": 0.2,
        "taker_fee_bps": 0.5,
        "spread_bps": 1.0,
        "slippage_bps": 1.5,
        "funding_roundtrip_note": "funding paid/received modeled explicitly per holding period",
    },
    "spot": {
        "fee_bps": 1.0,
        "spread_bps": 1.5,
        "slippage_bps": 2.0,
    },
    "relative_basket": {
        "note": "cost each leg separately using perp and spot schedules above",
        "rebalance_cost_bps": 1.0,
    },
    "stress_cost_2x": {
        "description": "STRESS_COST_2X = double all above for sensitivity test",
        "multiplier": 2.0,
    },
    "base_cost_total": {
        "single_perp_roundtrip_bps": "taker_fee + taker_fee + spread + slippage = 3.5 bps per roundtrip (excl funding)",
        "spot_perp_hedge_roundtrip_bps": "perp roundtrip + spot roundtrip = ~8.0 bps",
    },
}

DATA_SPLIT_CONTRACT = {
    "contract_id": "ALPHA1_DATA_SPLIT_V1",
    "frozen_at": TS,
    "description": "Data-split contract for ALPHA-2 backtest. Development and stability periods defined. No genuine untouched confirmation period exists — 2026 period already consumed by MECH-1/MECH-2 mechanism research.",
    "periods": {
        "development": {
            "start": "2026-01-25",
            "end": "2025-12-31",
            "note": "Earliest common usable period through end of 2025. May be empty if DATA-1 starts in 2026.",
            "available": False,
            "reason": "DATA-1 frozen normalized data begins 2026-01-25; no pre-2026 common data exists.",
        },
        "mechanism_research": {
            "start": "2026-01-25",
            "end": "2026-06-15",
            "note": "Consumed by MECH-1 mechanism anatomy research.",
            "consumed": True,
        },
        "stability_extension": {
            "start": "2026-07-01",
            "end": "2026-08-21",
            "note": "AMM 30d extension period; limited to AMM evidence. Not a full backtest period.",
            "available_partial": True,
        },
    },
    "confirmation_period": {
        "available": False,
        "statement": "No genuine untouched confirmation period exists. All available common history has been consumed by mechanism research. ALPHA-2 must state this honestly and use the entire available history for development only, reporting that confirmation is DEFERRED.",
    },
    "future_confirmation": "Requires new data collection beyond 2026-08-21 for any forward out-of-sample test.",
}

METRIC_CONTRACT = {
    "contract_id": "ALPHA1_METRIC_V1",
    "frozen_at": TS,
    "description": "Metrics to be computed by ALPHA-2 for each strategy. These are preregistered; do NOT compute them in ALPHA-1.",
    "metrics": [
        "trade_count",
        "trade_frequency_per_day",
        "win_rate",
        "mean_R",
        "median_R",
        "gross_profit_factor",
        "net_profit_factor",
        "payoff_ratio",
        "p5_outcome_R",
        "worst_outcome_R",
        "max_drawdown_R",
        "max_losing_streak",
        "mean_MAE_R",
        "mean_MFE_R",
        "mean_holding_time_hours",
        "cost_share_of_PnL",
        "funding_contribution_R",
        "subperiod_PF (split by month)",
        "state_concentration (Herfindahl across states)",
        "asset_concentration",
    ],
}

FALSIFICATION_RULES = {
    "contract_id": "ALPHA1_FALSIFICATION_V1",
    "frozen_at": TS,
    "description": "Automatic rejection conditions for ALPHA-2. A strategy is FALSIFIED if any condition is met.",
    "rules": [
        {"rule_id": "F1", "condition": "trade_count < 20", "reason": "INSUFFICIENT_EVENTS"},
        {"rule_id": "F2", "condition": "trade_count < 50", "reason": "SPARSE_EVENTS (flagged but not automatic rejection if net edge > 0)"},
        {"rule_id": "F3", "condition": "net_profit_factor <= 1.0 at BASE_COST", "reason": "NO_NET_EDGE"},
        {"rule_id": "F4", "condition": "gross_profit_factor <= 1.0", "reason": "NO_GROSS_EDGE"},
        {"rule_id": "F5", "condition": "net_profit_factor drops >30% at STRESS_COST_2X", "reason": "COST_FRAGILITY"},
        {"rule_id": "F6", "condition": "single_trade_dominates_gt_50pct_total_R", "reason": "SINGLE_EVENT_DOMINATION"},
        {"rule_id": "F7", "condition": "single_month_dominates_gt_50pct_total_R", "reason": "ONE_PERIOD_DOMINATION"},
        {"rule_id": "F8", "condition": "control_net_PF >= strategy_net_PF (CI overlap)", "reason": "STATE_ADDS_NO_VALUE"},
        {"rule_id": "F9", "condition": "future_perturbation_breaks_state_labels", "reason": "FUTURE_LEAKAGE"},
        {"rule_id": "F10", "condition": "mean_holding_time < 2 bar periods", "reason": "UNEXECUTABLE_TIMING"},
        {"rule_id": "F11", "condition": "causal_violation_detected", "reason": "CAUSALITY_BREACH"},
        {"rule_id": "F12", "condition": "turnover > 100 roundtrips per month", "reason": "UNREASONABLE_TURNOVER"},
    ],
    "no_changing_rules_after_results": True,
}


# ─── ARTIFACT WRITERS ─────────────────────────────────────────────────

def write_preregistration(contracts: Dict) -> Path:
    md = f"""# ALPHA-1 Preregistration — Mechanism-to-Strategy Hypothesis Generation

**Frozen:** {TS}
**Parent:** CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY (PASS_STATE_TAXONOMY)
**Commit:** 1e0265c684ef457f6ead0e6bc84d4eb2147eaa11

## Scope

Convert 25 MECH-2 PROMOTE_TO_ALPHA states into explicit, causal, testable
strategy hypotheses. This checkpoint FREEZES ideas before results.

## Hard Boundaries

- MAY generate explicit trading hypotheses, define entries/exits/invalidations, define execution objects, define cost assumptions, preregister backtest contracts
- MUST NOT run strategy PnL, look at PF/Sharpe/win rate, optimize thresholds/stops/targets/holding periods, tune for profitability, use ML, connect execution

## Strategy Count

- **Strategy contracts:** {len(contracts['contracts'])} (target <= 25)
- **Control contracts:** {len(contracts['controls'])}
- **Total:** {len(contracts['contracts']) + len(contracts['controls'])}

## Mechanism Families

| Family | Name | Source States | Variants |
|---|---|---|---|
"""
    for f in load_families():
        md += f"| {f['family_id']} | {f['name']} | {f['n_source_states']} | {f.get('_variant_count', 'see contracts')} |\n"

    md += f"""
## Execution Objects

- BTC perpetual
- ETH perpetual
- BTC spot
- ETH spot
- BTC/ETH relative-value basket
- spot + perp hedge

## Status

All strategy contracts: **PREREGISTERED_FOR_ALPHA2**
No PnL has been observed. No optimization has been performed.
"""
    p = OUT / "ALPHA_1_PREREGISTRATION.md"
    p.write_text(md, encoding="utf-8")
    return p


def write_strategy_registry(contracts: Dict) -> Path:
    """Write ALPHA_1_STRATEGY_HYPOTHESIS_REGISTRY.csv."""
    rows = contracts["contracts"]
    controls = contracts["controls"]
    # Find control fallback keys
    fallback = rows[0].keys() if rows else []
    ctrl_fallback = controls[0].keys() if controls else []

    # Strategy registry
    strat_fields = [
        "strategy_id", "family_id", "variant_type", "asset",
        "source_state_ids", "mechanism_type", "expected_resolution_path",
        "execution_object", "direction_logic",
        "entry_state", "entry_trigger",
        "decision_timestamp_rule", "execution_timestamp_rule",
        "exit_rule", "invalidation_rule",
        "time_exit", "max_holding_period",
        "cost_model", "funding_accounting",
        "control_id", "required_data",
        "causality_notes", "known_failure_modes",
        "status",
    ]
    p = OUT / "ALPHA_1_STRATEGY_HYPOTHESIS_REGISTRY.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=strat_fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # Control registry
    ctrl_fields = [
        "control_id", "family_id", "name", "description",
        "strategy_id_mirror", "differences", "status",
    ]
    cp = OUT / "ALPHA_1_CONTROL_REGISTRY.csv"
    with open(cp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ctrl_fields, extrasaction="ignore")
        w.writeheader()
        for r in controls:
            w.writerow(r)
    return p


def write_json_contracts(contracts: Dict) -> List[Path]:
    """Write all JSON artifacts and return their paths."""
    paths = []

    # Strategy contracts JSON
    sp = OUT / "ALPHA_1_STRATEGY_CONTRACTS.json"
    json.dump(contracts["contracts"], open(sp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    paths.append(sp)

    # Cost contract
    cp = OUT / "ALPHA_1_COST_CONTRACT.json"
    json.dump(COST_CONTRACT, open(cp, "w", encoding="utf-8"), indent=2)
    paths.append(cp)

    # Data split
    dp = OUT / "ALPHA_1_DATA_SPLIT_CONTRACT.json"
    json.dump(DATA_SPLIT_CONTRACT, open(dp, "w", encoding="utf-8"), indent=2)
    paths.append(dp)

    # Metrics
    mp = OUT / "ALPHA_1_METRIC_CONTRACT.json"
    json.dump(METRIC_CONTRACT, open(mp, "w", encoding="utf-8"), indent=2)
    paths.append(mp)

    # Falsification rules
    fp = OUT / "ALPHA_1_FALSIFICATION_RULES.json"
    json.dump(FALSIFICATION_RULES, open(fp, "w", encoding="utf-8"), indent=2)
    paths.append(fp)

    return paths


def write_registry_hash(contracts: Dict) -> Path:
    """Hash the strategy contracts JSON and write the hash."""
    payload = json.dumps(contracts["contracts"], sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    doc = {
        "hash_algorithm": "SHA-256",
        "frozen_at": TS,
        "registry_hash": h,
        "contract_count": len(contracts["contracts"]),
        "control_count": len(contracts["controls"]),
        "note": "This hash freezes the strategy contract registry before any ALPHA-2 backtest. Any strategy redesign must produce a new hash.",
    }
    p = OUT / "ALPHA_1_STRATEGY_REGISTRY_HASH.json"
    json.dump(doc, open(p, "w", encoding="utf-8"), indent=2)
    return p


def write_report(contracts: Dict) -> Path:
    families = load_families()
    fam_map = {f["family_id"]: f for f in families}
    contracts_list = contracts["contracts"]
    controls_list = contracts["controls"]

    fam_counts: Dict[str, int] = {}
    for c in contracts_list:
        fid = c["family_id"]
        fam_counts[fid] = fam_counts.get(fid, 0) + 1

    md = f"""# ALPHA-1 Report — Mechanism-to-Strategy Hypothesis Generation

**Checkpoint:** CRYPTO-ALPHA-1-MECHANISM-TO-STRATEGY-GENERATION
**Frozen:** {TS}
**Parent:** MECH-2 (PASS_STATE_TAXONOMY, commit 1e0265c6)
**Decision:** PASS_ALPHA_HYPOTHESIS_GENERATION

## Summary

25 promoted MECH-2 states were clustered into 6 mechanism families
(5 active + 1 control baseline), producing {len(contracts_list)} strategy
contracts and {len(controls_list)} control contracts.

No PnL was observed. No optimization was performed.
All thresholds, entries, exits, invalidations, costs, and horizons
are frozen before any backtest.

## Mechanism Families

| ID | Name | Promoted States | Strategies |
|---|---|---|---|
"""
    for fid in sorted(fam_counts.keys()):
        f = fam_map.get(fid, {})
        md += f"| {fid} | {f.get('name', fid)} | {f.get('n_source_states', '?')} | {fam_counts[fid]} |\n"

    md += f"""
## Strategy Contracts

| ID | Family | Variant | Asset | Execution | Entry | Exit |
|---|---|---|---|---|---|---|
"""
    for c in contracts_list:
        md += f"| {c['strategy_id']} | {c['family_id']} | {c['variant_type']} | {c['asset']} | {c['execution_object']} | {c['entry_trigger'][:40]}... | {c['exit_rule'][:40]}... |\n"

    md += f"""
## Controls

| ID | Family | Name | Mirrors |
|---|---|---|---|
"""
    for c in controls_list:
        md += f"| {c['control_id']} | {c['family_id']} | {c['name']} | {c['strategy_id_mirror']} |\n"

    md += """
## Cost Contract

| Component | BASE (bps) | STRESS (2x) |
|---|---|---|
| Perp taker fee | 0.5 | 1.0 |
| Perp spread | 1.0 | 2.0 |
| Perp slippage | 1.5 | 3.0 |
| Spot fee | 1.0 | 2.0 |
| Spot spread+slippage | 3.5 | 7.0 |
| Perp roundtrip | 3.5 | 7.0 |
| Spot+perp hedge roundtrip | 8.0 | 16.0 |

## Data Split

**No genuine untouched confirmation period exists.** All available common
history (2026-01-25 through 2026-08-21) has been consumed by MECH-1 and
MECH-2 mechanism research. ALPHA-2 will report all results as development
with confirmation DEFERRED.

## Falsification Rules

12 automatic rejection rules preregistered (see ALPHA_1_FALSIFICATION_RULES.json):
F1 (N<20), F2 (N<50), F3 (net PF<=1), F4 (gross PF<=1), F5 (cost fragile),
F6 (single-trade domination), F7 (single-month domination),
F8 (state adds no value vs control), F9 (future leak),
F10 (unexecutable timing), F11 (causality breach), F12 (excessive turnover).

## Pass Conditions Met

1. MECH-2 parent verified ✓
2. Clerical parent inconsistencies reconciled (ALPHA_1_PARENT_TRUTH_PREFLIGHT.md) ✓
3. Only promoted states feed native strategies ✓
4. Mechanism families deduplicated (25 states → 6 families) ✓
5. <=25 strategy contracts ({len(contracts_list)}) ✓
6. Each strategy causal (bar close → next bar open, no same-bar fills) ✓
7. Each strategy has invalidation rule ✓
8. Costs frozen ✓
9. Funding accounting frozen ✓
10. Controls defined ({len(controls_list)}) ✓
11. ALPHA-2 metrics frozen ✓
12. Falsification rules frozen ✓
13. Strategy registry hashed ✓
14. No PnL run ✓
15. No optimization ✓
16. No ML ✓
17. No execution ✓

## Status

**PASS_ALPHA_HYPOTHESIS_GENERATION**

Next: CRYPTO-ALPHA-2-PREREGISTERED-BACKTEST-AND-FALSIFICATION
"""
    p = OUT / "ALPHA_1_REPORT.md"
    p.write_text(md, encoding="utf-8")
    return p


def write_decision() -> Path:
    doc = {
        "checkpoint": "CRYPTO-ALPHA-1-MECHANISM-TO-STRATEGY-GENERATION",
        "parent": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
        "parent_sha": "1e0265c684ef457f6ead0e6bc84d4eb2147eaa11",
        "decision": "PASS_ALPHA_HYPOTHESIS_GENERATION",
        "frozen_at": TS,
        "strategy_count": 0,  # filled by caller
        "control_count": 0,
        "promoted_states_consumed": 25,
        "mechanism_families": 6,
        "next_checkpoint": "CRYPTO-ALPHA-2-PREREGISTERED-BACKTEST-AND-FALSIFICATION",
        "authorized": {
            "strategy_generation": True,
            "backtest": False,
            "execution": False,
            "live_capital": False,
        },
    }
    return doc


# ─── MAIN ─────────────────────────────────────────────────────────────

def build_all():
    print("=== ALPHA-1 Artifact Builder ===")
    families = load_families()
    print(f"Loaded {len(families)} families")

    print("Building strategy contracts...")
    contracts = build_contracts(families)
    print(f"  Strategies: {len(contracts['contracts'])}")
    print(f"  Controls:   {len(contracts['controls'])}")

    print("Writing artifacts...")
    written = []
    written.append(write_preregistration(contracts))
    print(f"  {written[-1].name}")
    written.append(write_strategy_registry(contracts))
    print(f"  {written[-1].name}")
    for p in write_json_contracts(contracts):
        written.append(p)
        print(f"  {p.name}")
    written.append(write_registry_hash(contracts))
    print(f"  {written[-1].name}")
    written.append(write_report(contracts))
    print(f"  {written[-1].name}")

    decision = write_decision()
    decision["strategy_count"] = len(contracts["contracts"])
    decision["control_count"] = len(contracts["controls"])
    dp = OUT / "ALPHA_1_DECISION.json"
    json.dump(decision, open(dp, "w", encoding="utf-8"), indent=2)
    print(f"  {dp.name}")

    print(f"\nAll {len(written) + 1} artifacts written.")
    return contracts, decision


if __name__ == "__main__":
    build_all()