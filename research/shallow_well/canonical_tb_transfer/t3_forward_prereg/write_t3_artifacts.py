#!/usr/bin/env python3
"""
CTBT T3 — Transfer-candidate seal + forward-shadow preregistration artifacts.

Writes every T3 artifact from a single FROZEN_TRUTH dict.  Strategy hashes
are sha256 over the canonical, deterministically serialized strategy
specification (sorted keys, compact separators) — the immutable contract a
runtime must reproduce exactly.  No historical research, no parameters are
changed: this checkpoint seals what T1.1/T2 already proved.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

BASE = "d08502793fd0ca96eb65e78d12ed85eea6389073"

# ── canonical strategy specifications (frozen, immutable) ─────────────────
def strategy_spec(tri, legs, version, basis_note):
    return {
        "version_id": version,
        "family": "CANONICAL_TB_TRANSFER_FAMILY",
        "timeframe": "M5",
        "basis": {
            "formula": "b = ln(A) - ln(B) + ln(C)",
            "A": legs[0], "B": legs[1], "C": legs[2],
            "orientation_frozen": True,
            "note": basis_note,
        },
        "direction_rule": {
            "z_gt_3": "SHORT basket: short A, long B, short C (profits when basis declines)",
            "z_lt_-3": "LONG basket: long A, short B, long C (profits when basis rises)",
        },
        "rolling_z": {"lookback": 200, "ddof": 0, "population_std": True,
                      "current_bar_excluded": True, "causality": "closed bar only"},
        "entry_primary": {"strict": True, "threshold": 3.0},
        "weight": {"model": "W2 exact-neutral",
                   "note": "MODEL GEOMETRY only — not broker lots, not capital allocation, not leverage authorization"},
        "exit": {"family": "E1 canonical signed overshoot",
                 "short_exit_z": -0.25, "long_exit_z": 0.25},
        "structural_stop": {"z_abs_gt": 6.0},
        "session": {"name": "canonical London", "start_h_est": 3, "end_h_est": 12,
                    "utc_offset_hours": -5, "fixed_contract": True},
        "min_runway_minutes": 120,
        "hard_exit": {"h_est": 12, "checked_before_tp_sl": True},
        "concurrency": 1,
        "reentry": "canonical deterministic lifecycle; no cooldown",
        "cost_contract_reference": "HISTORICAL_MODELED_COST_CONTRACT",
        "triangle_id": tri,
    }

SPECS = {
    "EUR_GBP_USD": strategy_spec(
        "EUR_GBP_USD", ["EURGBP", "EURUSD", "GBPUSD"], "CTBT-EUR-GBP-USD-v1",
        "EURGBP * GBPUSD == EURUSD triangular identity; basis = ln(EURGBP) - ln(EURUSD) + ln(GBPUSD)"),
    "GBP_NZD_USD": strategy_spec(
        "GBP_NZD_USD", ["GBPNZD", "GBPUSD", "NZDUSD"], "CTBT-GBP-NZD-USD-v1",
        "GBPNZD * NZDUSD == GBPUSD triangular identity; basis = ln(GBPNZD) - ln(GBPUSD) + ln(NZDUSD)"),
}

def sh(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

HASHES = {tri: sh(spec) for tri, spec in SPECS.items()}

# ── frozen historical truth (sealed at T2, unchanged) ─────────────────────
TRUTH = {
    "EUR_GBP_USD": {
        "version_id": "CTBT-EUR-GBP-USD-v1",
        "development": {"window": ["2022-09-28 00:00:00", "2024-12-31 18:55:00"],
                        "events": 435, "net_ev_bps": 15.7393, "pf_net": 5.4152,
                        "win_rate_pct": 78.16, "edge_cost_ratio": 2.8828,
                        "monotonicity": "MONOTONIC_STRONG"},
        "confirmation_2025": {"window": ["2025-01-02 00:00:00", "2025-12-31 18:55:00"],
                              "events": 146, "net_ev_bps": 17.75497, "pf_net": 5.5231,
                              "win_rate_pct": 77.3973, "edge_cost_ratio": 3.2039,
                              "break_even_multiple": 3.2039,
                              "bootstrap_95_ci": [14.2525, 21.4659],
                              "bh_fdr": "significant",
                              "transport": "TRANSPORT_CONFIRMED"},
    },
    "GBP_NZD_USD": {
        "version_id": "CTBT-GBP-NZD-USD-v1",
        "development": {"window": ["2022-09-12 00:00:00", "2024-12-31 18:55:00"],
                        "events": 210, "net_ev_bps": 22.8374, "pf_net": 8.0184,
                        "win_rate_pct": 84.29, "edge_cost_ratio": 3.5557,
                        "monotonicity": "MONOTONIC_STRONG"},
        "confirmation_2025": {"window": ["2025-01-02 00:00:00", "2025-12-31 18:55:00"],
                              "events": 81, "net_ev_bps": 11.86815, "pf_net": 5.8179,
                              "win_rate_pct": 74.0741, "edge_cost_ratio": 2.3346,
                              "break_even_multiple": 2.3346,
                              "bootstrap_95_ci": [6.1569, 17.2246],
                              "bh_fdr": "significant",
                              "transport": "TRANSPORT_DECAYED_BUT_POSITIVE"},
    },
}

def jwrite(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")

# ── 1. T2 seal ────────────────────────────────────────────────────────────
jwrite("CTBT_T3_T2_SEAL.json", {
    "checkpoint": "SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION",
    "t2_commit": BASE,
    "t2_status": "FOCUSED_TRANSFER_FAMILY",
    "t2_verified": True,
    "confirmed_candidates": ["EUR_GBP_USD", "GBP_NZD_USD"],
    "sealed_truth": TRUTH,
})

# ── 2. strategy hashes ────────────────────────────────────────────────────
jwrite("CTBT_T3_STRATEGY_HASHES.json", {
    "hash_algorithm": "sha256",
    "canonicalization": "json.dumps(sort_keys=True, separators=(',',':')) over the strategy specification (strategy params, basis, leg sides, lifecycle, session, cost reference); historical metrics are NOT part of the hash",
    "strategies": {
        tri: {"version_id": SPECS[tri]["version_id"], "strategy_hash": HASHES[tri],
              "spec": SPECS[tri]}
        for tri in SPECS
    },
})

# ── 3. candidate seals ────────────────────────────────────────────────────
for tri in SPECS:
    jwrite(f"CTBT_T3_{tri}_CANDIDATE_SEAL.json", {
        "candidate": tri,
        "version_id": SPECS[tri]["version_id"],
        "strategy_hash": HASHES[tri],
        "strategy_spec": SPECS[tri],
        "historical_truth": TRUTH[tri],
        "state": "HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE",
        "evidence_consumed": "development 2020-2024 (effective 2022-09+) and 2025 confirmation; historical research CLOSED",
    })

# ── 4. family registry ────────────────────────────────────────────────────
family = {
    "family": "CANONICAL_TB_TRANSFER_FAMILY",
    "members": [
        {"strategy": "AUD_GBP_NZD", "version": "CANONICAL_TB (reference)", "role": "CANONICAL_REFERENCE",
         "note": "separate strategy version, separate evidence program, separate runtime slot, separate completeness audit"},
        {"strategy": "EUR_GBP_USD", "version": "CTBT-EUR-GBP-USD-v1", "role": "CONFIRMED_TRANSFER",
         "hash": HASHES["EUR_GBP_USD"]},
        {"strategy": "GBP_NZD_USD", "version": "CTBT-GBP-NZD-USD-v1", "role": "CONFIRMED_TRANSFER_DECAYED",
         "hash": HASHES["GBP_NZD_USD"]},
    ],
    "rules": {
        "no_pnl_pooling": True,
        "portfolio_correlation_capital_work": "LATER (after independent forward proof)",
        "members_promote_independently": True,
    },
}
family["family_hash"] = sh(family)
jwrite("CTBT_T3_FAMILY_REGISTRY.json", family)

# ── 5. basis orientation ──────────────────────────────────────────────────
jwrite("CTBT_T3_BASIS_ORIENTATION.json", {
    "note": "Exact log-basis orientations frozen from the T2 implementation. Runtime must NOT infer orientation dynamically.",
    "EUR_GBP_USD": {
        "basis": "b = ln(EURGBP) - ln(EURUSD) + ln(GBPUSD)",
        "identity": "EURGBP * GBPUSD == EURUSD",
        "z_gt_3": "SHORT basket (short EURGBP, long EURUSD, short GBPUSD)",
        "z_lt_-3": "LONG basket (long EURGBP, short EURUSD, long GBPUSD)",
        "gross_bps_SHORT": "+10000 * (b_entry - b_exit)",
        "gross_bps_LONG": "+10000 * (b_exit - b_entry)",
    },
    "GBP_NZD_USD": {
        "basis": "b = ln(GBPNZD) - ln(GBPUSD) + ln(NZDUSD)",
        "identity": "GBPNZD * NZDUSD == GBPUSD",
        "z_gt_3": "SHORT basket (short GBPNZD, long GBPUSD, short NZDUSD)",
        "z_lt_-3": "LONG basket (long GBPNZD, short GBPUSD, long NZDUSD)",
        "gross_bps_SHORT": "+10000 * (b_entry - b_exit)",
        "gross_bps_LONG": "+10000 * (b_exit - b_entry)",
    },
})

# ── 6. leg-side mapping ───────────────────────────────────────────────────
jwrite("CTBT_T3_LEG_SIDE_MAPPING.json", {
    "note": "Deterministic buy/sell orientation per basket. Symbol mapping follows the frozen data path (quant-lab/data CSVs; MT5 provider-neutral runtime symbols mapped at integration). Bid/ask side: model prices are mid; execution cost applied via frozen modeled cost contract; forward shadow observes real bid/ask.",
    "symbols": {
        "EURGBP": {"pair": "EUR/GBP", "pip": 0.0001},
        "EURUSD": {"pair": "EUR/USD", "pip": 0.0001},
        "GBPUSD": {"pair": "GBP/USD", "pip": 0.0001},
        "GBPNZD": {"pair": "GBP/NZD", "pip": 0.0001},
        "NZDUSD": {"pair": "NZD/USD", "pip": 0.0001},
    },
    "baskets": {
        "EUR_GBP_USD": {
            "SHORT": {"EURGBP": "SELL", "EURUSD": "BUY", "GBPUSD": "SELL"},
            "LONG": {"EURGBP": "BUY", "EURUSD": "SELL", "GBPUSD": "BUY"},
        },
        "GBP_NZD_USD": {
            "SHORT": {"GBPNZD": "SELL", "GBPUSD": "BUY", "NZDUSD": "SELL"},
            "LONG": {"GBPNZD": "BUY", "GBPUSD": "SELL", "NZDUSD": "BUY"},
        },
    },
})

# ── 7. W2 contract ────────────────────────────────────────────────────────
jwrite("CTBT_T3_W2_CONTRACT.json", {
    "model": "W2 exact-neutral",
    "definition": "Uniform unit-free log-weight per leg: each leg carries equal absolute log exposure, making the basket market-neutral in log space.",
    "status": "MODEL GEOMETRY — not broker lots, not capital allocation, not leverage authorization",
    "runtime_conversion": "separate concern (CapitalTranslationAdapter), NOT invoked in T3",
    "sealed_behavior": "identical to the T1.1 engine that produced 405/405 + 194/194 reference parity and the T2 confirmations",
})

# ── 8. cost contract ──────────────────────────────────────────────────────
jwrite("CTBT_T3_COST_CONTRACT.json", {
    "historical_contract": "HISTORICAL_MODELED_COST_CONTRACT",
    "method": "basket round-trip bps = sum over legs (spread_pips + commission_pips) * pip_size / median_close * 1e4",
    "spread_pips_floor": 1.5,
    "commission_pips_per_leg": 1.4,
    "evidence_class": "VERIFIED_STATIC_PROVIDER (documented OxSecurities MT5 spec; floor stricter than documented)",
    "canonical_reference_cost": "10.2 pips frozen (AUD_GBP_NZD)",
    "disclaimer": "Historical modeled cost does NOT equal realized forward execution cost.",
    "forward_requirement": "collect actual provider-side cost evidence per eligible signal (bid/ask/mid/spread, basket modeled vs observed quote-crossing cost, observed/model multiple)",
})

# ── 9. forward start ──────────────────────────────────────────────────────
jwrite("CTBT_T3_FORWARD_START.json", {
    "rule": "Forward evidence begins strictly AFTER the SW-CTBT-T3 commit timestamp. No historical event may be relabeled as forward evidence.",
    "forward_start_timestamp": "first causally complete M5 bar strictly after the T3 sealing commit (to be stamped by T4 runtime integration once the T3 commit SHA and its commit timestamp are known)",
    "t2_evidence_end": "2025-12-31 18:55:00",
    "seal_commit": "recorded in CTBT_T3_DECISION.json after commit",
})

# ── 10. event-count stopping ──────────────────────────────────────────────
jwrite("CTBT_T3_EVENT_COUNT_STOPPING.json", {
    "horizon": "EVENT COUNT is the primary evidence horizon; calendar time reported but not decisive",
    "early_diagnostic_events": 15,
    "minimum_useful_events": 30,
    "preferred_events": 50,
    "note_15": "15 events is DIAGNOSTIC ONLY — not validation",
    "time_review_points": ["monthly engineering audit", "quarterly scientific context review"],
    "no_parameter_changes_at_reviews": True,
})

# ── 11. forward scorecard schema ──────────────────────────────────────────
jwrite("CTBT_T3_FORWARD_SCORECARD_SCHEMA.json", {
    "per_strategy": ["signals", "completed_events", "events_per_week", "gross_ev_bps",
                     "net_modeled_ev_bps", "net_observed_cost_ev_bps", "win_rate_pct",
                     "median_ev_bps", "pf", "payoff_ratio", "max_dd_bps", "p5_bps",
                     "worst_bps", "longest_losing_streak", "mae", "mfe",
                     "hold_distribution_min", "z6_rate", "hard_exit_rate",
                     "signal_time_cost_distribution_bps", "provider_cost_multiple_distribution"],
    "historical_comparison": {
        "rule": "compare forward evidence SEPARATELY against development fingerprint and 2025 confirmation fingerprint",
        "no_pooling": "do not pool all periods into one headline"
    },
    "expectancy_states": ["INSUFFICIENT_EVENTS", "MECHANISM_ALIGNED", "MECHANISM_WEAKENED",
                          "MECHANISM_BROKEN", "COST_MARGIN_HEALTHY", "COST_MARGIN_TIGHT",
                          "COST_MARGIN_BROKEN"],
    "expectancy_note": "evidence labels only; they do not authorize trading",
})

# ── 12. historical reference bands ────────────────────────────────────────
jwrite("CTBT_T3_HISTORICAL_REFERENCE_BANDS.json", {
    "note": "Reference distributions, NOT quotas. Forward metrics are not required to equal these.",
    "EUR_GBP_USD": {
        "development_ev_bps": 15.74, "confirmation_ev_bps": 17.75,
        "confirmation_pf": 5.52, "confirmation_wr_pct": 77.4,
        "confirmation_cost_ratio": 3.20,
        "monitoring_emphasis": "mechanism continuity at or near confirmation quality",
    },
    "GBP_NZD_USD": {
        "development_ev_bps": 22.84, "confirmation_ev_bps": 11.87,
        "confirmation_pf": 5.82, "confirmation_wr_pct": 74.1,
        "confirmation_cost_ratio": 2.33,
        "monitoring_emphasis": "already showed material transport decay; compare primarily against 2025 confirmation, not development; do not auto-kill for forward EV below development",
    },
})

# ── 13. runtime mapping ───────────────────────────────────────────────────
jwrite("CTBT_T3_RUNTIME_MAPPING.json", {
    "architecture_rule": "Use existing Execution Runtime abstractions; do NOT build a parallel broker stack inside Shallow Well",
    "flow": ["FrozenTransferCandidate", "->", "StrategyAdapter", "->",
             "provider-neutral market data", "->", "shadow signal/event ledger"],
    "existing_abstractions": {
        "market_data": "quant-lab/data M5 CSV path (frozen engine source) + provider-neutral runtime feed at integration",
        "execution_contract": "quant-lab/engines/triangular_execution_contract.py (BrokerLegIntent, BasketExecutionIntent, model_weight_to_notional, notional_to_mt5_lots, assess_basket_neutrality)",
        "mt5_layer": "quant-lab/mt5/execution_layer.py (MT5ExecutionLayer) — NOT invoked in T3",
        "production_runtime": "quant-lab/mt5/production_runtime.py (ProductionRuntime, RuntimeConfig, StateStore, HealthMonitor) — shadow integration only, order path disabled",
        "provider_cost_config": "quant-lab/config/spread_commission_config.py (SPREAD_CONFIG, get_spread_pips, get_commission_pips)",
    },
    "shadow_ledger": "per-candidate shadow signal/event ledger (event_id, entry/exit ts, direction, entry/exit z, exit reason, hold, leg weights, gross bps, modeled cost bps, net bps, z6 state, session state, hard-exit flag, provider cost snapshot)",
    "no_order_path": True,
    "no_account_mutation": True,
})

# ── 14. provider cost schema ──────────────────────────────────────────────
jwrite("CTBT_T3_PROVIDER_COST_SCHEMA.json", {
    "per_eligible_signal": {
        "provider": None, "account_environment": None, "symbol_mapping": None,
        "decision_timestamp": None,
        "per_leg": {"bid": None, "ask": None, "mid": None, "spread": None},
        "basket_modeled_cost_bps": None,
        "basket_observed_quote_crossing_cost_bps": None,
        "observed_model_cost_multiple": None,
    },
    "if_demo_fills_exist": {"slippage": "measured separately", "commissions": "measured separately"},
    "provider_separation": {"rule": "providers remain separate in cost diagnostics; do NOT pool MT5 and TradeLocker observations blindly",
                            "primary": "existing MT5 provider-neutral runtime path",
                            "tradelocker": "may participate once its read-only provider layer is available"},
    "t3_places_no_orders": True,
})

# ── 15. promotion contract ────────────────────────────────────────────────
jwrite("CTBT_T3_PROMOTION_CONTRACT.json", {
    "purpose": "preregistered minimum candidate-level evidence BEFORE demo execution may even be considered",
    "minimum_consideration_gates": {
        "events": ">= 30 natural forward events",
        "net_ev": "positive forward net EV",
        "pf": "> 1.20",
        "mechanism": "no mechanism break",
        "cost_margin": "remains positive",
        "completeness": "signal completeness acceptable",
        "causality": "intact",
        "runtime_data_parity": "acceptable",
    },
    "preferred_events": 50,
    "not_automatic_authorization": True,
    "family_promotion": "candidates promote independently (EUR_GBP_USD may pass forward while GBP_NZD_USD fails)",
})

# ── 16. failure contract ──────────────────────────────────────────────────
jwrite("CTBT_T3_FAILURE_CONTRACT.json", {
    "forward_mechanism_failed": "marked if sufficient events show persistent negative EV, or clear mechanism-sign reversal, or transaction costs systematically dominate gross edge",
    "no_automatic_retuning": True,
    "failed_v1_is_sealed": True,
    "early_stop_before_30_events": {
        "permitted_only_for": ["causality failure", "strategy/runtime mismatch",
                               "gross mechanism inversion", "severe cost impossibility",
                               "data invalidity"],
        "not_permitted_for": "ordinary losing streak",
    },
})

# ── 17. canonical noninterference ─────────────────────────────────────────
jwrite("CTBT_T3_CANONICAL_NONINTERFERENCE.json", {
    "canonical_aud_gbp_nzd": {
        "separate_strategy_version": True, "separate_evidence_program": True,
        "separate_runtime_slot": True, "separate_completeness_audit": True,
        "may_share_infrastructure": True, "must_not_share_evidence_ledgers": True,
        "may_not_be_delayed_or_altered_by_candidates": True,
        "priority": "canonical TB forward takes precedence over clone research if engineering attention is required",
    },
    "reference_parity_anchors": {"control_z25": 405, "primary_z3": 194,
                                 "cost_contract_pips": 10.2},
})

# ── 18. nonregression ─────────────────────────────────────────────────────
jwrite("CTBT_T3_NONREGRESSION.json", {
    "t1_artifacts_unchanged": True, "t11_artifacts_unchanged": True,
    "t2_artifacts_unchanged": True,
    "t11_reference_parity_exact": True,
    "canonical_405_194_anchors": True,
    "t2_metrics_preserved": {"EUR_GBP_USD": TRUTH["EUR_GBP_USD"]["confirmation_2025"],
                             "GBP_NZD_USD": TRUTH["GBP_NZD_USD"]["confirmation_2025"]},
    "t2_focused_transfer_family": True,
    "historical_optimization_complete": True,
    "no_additional_historical_testing": True,
    "no_2026_historical_research": True,
})

# ── 19. DECISION ──────────────────────────────────────────────────────────
jwrite("CTBT_T3_DECISION.json", {
    "checkpoint": "SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION",
    "status": "PASS_TRANSFER_FAMILY_SEALED_FORWARD_PREREGISTERED",
    "base_commit": BASE,
    "t2_verified": {"status": "FOCUSED_TRANSFER_FAMILY", "commit": BASE},
    "family": "CANONICAL_TB_TRANSFER_FAMILY",
    "candidate_count": 2,
    "candidates": ["EUR_GBP_USD", "GBP_NZD_USD"],
    "historical_research_closed": True,
    "eur_gbp_usd_version": "CTBT-EUR-GBP-USD-v1",
    "eur_gbp_usd_hash": HASHES["EUR_GBP_USD"],
    "eur_gbp_usd_state": "HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE",
    "gbp_nzd_usd_version": "CTBT-GBP-NZD-USD-v1",
    "gbp_nzd_usd_hash": HASHES["GBP_NZD_USD"],
    "gbp_nzd_usd_state": "HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE",
    "forward_start_rule": "first causally complete M5 bar strictly after the T3 sealing commit timestamp",
    "early_diagnostic_events": 15,
    "minimum_useful_events": 30,
    "preferred_events": 50,
    "runtime_mapping_ready": True,
    "runtime_shadow_ready": False,
    "runtime_shadow_authorized": False,
    "demo_execution_ready": False,
    "demo_execution_authorized": False,
    "capital_routing_authorized": False,
    "canonical_tb_unchanged": True,
    "production_authorized": False,
    "human_review_required": True,
    "next_checkpoint_recommended": "SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION",
    "t4_scope": "engineering integration only; does NOT authorize demo execution, live execution, or strategy-science changes",
})

# ── 20. REPORT ────────────────────────────────────────────────────────────
report = f"""# CTBT T3 — Transfer-Candidate Seal & Forward-Shadow Preregistration

**Checkpoint:** `SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION`
**Base:** `{BASE}` (T2, FOCUSED_TRANSFER_FAMILY)
**Status:** **PASS_TRANSFER_FAMILY_SEALED_FORWARD_PREREGISTERED**

## 1. What this checkpoint is

Candidate **seal** + **forward-evidence contract** + **runtime-mapping
specification** for the two historically confirmed transfer candidates. It
performs **no** historical optimization, changes no parameters, opens no new
candidate baskets, places no orders, and authorizes no capital.

## 2. Sealed candidates

| Version ID | Strategy hash | T1.1 (dev) | 2025 confirmation | Transport |
|---|---|---|---|---|
| `CTBT-EUR-GBP-USD-v1` | `{HASHES['EUR_GBP_USD'][:16]}…` | N=435, EV +15.74, PF 5.42, WR 78.2%, ratio 2.88 | N=146, EV +17.75, PF 5.52, WR 77.4%, ratio 3.20 | TRANSPORT_CONFIRMED |
| `CTBT-GBP-NZD-USD-v1` | `{HASHES['GBP_NZD_USD'][:16]}…` | N=210, EV +22.84, PF 8.02, WR 84.3%, ratio 3.56 | N=81, EV +11.87, PF 5.82, WR 74.1%, ratio 2.33 | TRANSPORT_DECAYED_BUT_POSITIVE |

Full specs and hashes: `CTBT_T3_STRATEGY_HASHES.json` (sha256 over the
canonical, deterministically serialized strategy specification — the
immutable contract a runtime must reproduce exactly).

## 3. Frozen contract (both candidates)

M5 · rolling z 200 completed bars, population std ddof=0, current bar
excluded, closed-bar causal · strict |z| > 3.0 entry · W2 exact-neutral
(MODEL GEOMETRY only) · E1 signed overshoot ±0.25 · |z| > 6 structural
invalidation · canonical London 03:00–12:00 EST · 120 min minimum runway ·
canonical noon hard exit · concurrency 1 · canonical deterministic re-entry.
Cost: `HISTORICAL_MODELED_COST_CONTRACT` (frozen T1.1 conservative method) —
explicitly **not** claimed equal to realized forward execution cost.

Basis orientations and leg-side (buy/sell) mappings are frozen explicitly
(`CTBT_T3_BASIS_ORIENTATION.json`, `CTBT_T3_LEG_SIDE_MAPPING.json`) — no
dynamic orientation inference at runtime.

## 4. Forward-shadow program

- **Start:** strictly after the T3 commit timestamp; no historical event may
  be relabeled as forward evidence.
- **Horizon:** event-count driven — 15 early diagnostic, 30 minimum useful,
  50 preferred. 15 is diagnostic only, never validation.
- **Evidence states:** INSUFFICIENT_EVENTS / MECHANISM_ALIGNED /
  MECHANISM_WEAKENED / MECHANISM_BROKEN / COST_MARGIN_HEALTHY /
  COST_MARGIN_TIGHT / COST_MARGIN_BROKEN — labels only, no trading
  authorization.
- **Completeness:** independent signal-completeness auditor
  (`CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md`) reconstructs eligible signals
  independently from raw M5 data with the frozen engine (MATCHED_SHADOW /
  VALID_RUNTIME_BLOCK / MISSED_SIGNAL / RUNTIME_ONLY_SIGNAL /
  DATA_DIVERGENCE / NO_SIGNAL); 100% recognition target, misses are
  individual failures.
- **Costs:** per-signal provider cost snapshot (bid/ask/mid/spread per leg,
  modeled vs observed quote-crossing basket cost, observed/model multiple).
  Providers (MT5 vs TradeLocker) remain separate in diagnostics.
- **Comparison:** forward results compared separately against development and
  2025-confirmation fingerprints — never pooled.

## 5. Runtime architecture

`FrozenTransferCandidate → StrategyAdapter → provider-neutral market data →
shadow signal/event ledger`, reusing the existing execution abstractions
(`triangular_execution_contract.py`, `mt5/execution_layer.py`,
`mt5/production_runtime.py`, `config/spread_commission_config.py`). **No
order path, no account mutation, no capital routing, no sizing.** Registry
status: `HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE` (not LIVE, not
PRODUCTION, not CAPITAL_ELIGIBLE).

## 6. Family & independence

Family `CANONICAL_TB_TRANSFER_FAMILY`: AUD_GBP_NZD (CANONICAL_REFERENCE),
EUR_GBP_USD (CONFIRMED_TRANSFER), GBP_NZD_USD (CONFIRMED_TRANSFER_DECAYED).
No PnL pooling, no portfolio/correlation/capital work yet, no portfolio
optimization. Candidates promote independently — EUR_GBP_USD may pass forward
while GBP_NZD_USD fails. Canonical AUD_GBP_NZD is untouched and takes
priority. GBP_NZD_USD monitoring is weighted against its 2025 confirmation
(not development) given its recorded transport decay.

## 7. Promotion & failure

Demo consideration requires per candidate: ≥30 natural forward events,
positive net EV, PF > 1.20, no mechanism break, positive cost margin,
acceptable completeness, intact causality, acceptable runtime/data parity
(preferred ≥50). These are minimum *consideration* gates — not automatic
authorization. Failure: FORWARD_MECHANISM_FAILED with no automatic retuning;
a failed v1 is sealed. Early scientific stop (<30 events) only for
catastrophic evidence (causality failure, runtime mismatch, mechanism
inversion, cost impossibility, data invalidity).

## 8. Decision

`production_authorized = false` · `human_review_required = true` ·
`runtime_shadow_ready = false` · `demo_execution_authorized = false` ·
`capital_routing_authorized = false`. Next checkpoint (if authorized):
`SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION` — engineering
integration only, no demo/live execution, no strategy-science changes.
"""
(HERE / "CTBT_T3_REPORT.md").write_text(report, encoding="utf-8")

print("T3 artifacts written.")
print("HASHES:", {k: v[:16] for k, v in HASHES.items()})
