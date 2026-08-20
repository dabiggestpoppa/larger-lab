#!/usr/bin/env python3
"""CTBT T4 — static artifact generator (frozen values, no runtime state)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
T3 = HERE.parent / "t3_forward_prereg"

BASE = "44379e416c1c49dd055f0d818f10bafccefec131"
HASHES = {
    "EUR_GBP_USD": "aad0a8e64c6964952eb9129ac2cdebd34d308e6df87ebf45e4584c351044b1a7",
    "GBP_NZD_USD": "5538d63a8acb29883b117fc23c76b1fe389db47ed89009ab3cd258b864f62485",
}
VERSIONS = {"EUR_GBP_USD": "CTBT-EUR-GBP-USD-v1", "GBP_NZD_USD": "CTBT-GBP-NZD-USD-v1"}
SYM = {"EURGBP": "EURGBP.PRO", "EURUSD": "EURUSD.PRO", "GBPUSD": "GBPUSD.PRO",
       "GBPNZD": "GBPNZD.PRO", "NZDUSD": "NZDUSD.PRO"}


def jwrite(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


# ── T3 seal ───────────────────────────────────────────────────────────────
t3d = json.loads((T3 / "CTBT_T3_DECISION.json").read_text(encoding="utf-8"))
jwrite("CTBT_T4_T3_SEAL.json", {
    "t3_commit": BASE,
    "t3_status": t3d["status"],
    "t3_verified": True,
    "sealed_candidates": [{"triangle": c, "version": VERSIONS[c], "hash": HASHES[c]}
                          for c in ["EUR_GBP_USD", "GBP_NZD_USD"]],
})

# ── runtime config ────────────────────────────────────────────────────────
jwrite("CTBT_T4_RUNTIME_CONFIG.json", {
    "checkpoint": "SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION",
    "runtime_version": "ctbt-runtime-0.1.0",
    "mode": "READ_ONLY_FORWARD_SHADOW",
    "provider": {"name": "Ox Securities MetaTrader 5", "server": "OxSecurities-Demo",
                 "role": "READ_ONLY_MARKET_DATA_SOURCE", "orders": "PROHIBITED"},
    "feed": {"timeframe": "M5", "poll_interval_seconds": 60, "warmup_bars": 200,
             "sync_rule": "all legs must share the exact same closed M5 timestamp; forming bars never evaluated"},
    "engine": {"source": "sealed T1.1 lifecycle (verified 405/405 + 194/194)",
               "entry": "strict |z| > 3.0", "weight": "W2 exact-neutral",
               "exit": "E1 +-0.25", "stop": "|z| > 6", "session": "London 03:00-12:00 EST",
               "min_runway_minutes": 120, "hard_exit": "noon", "concurrency": 1,
               "reentry": "canonical deterministic"},
    "ledgers": {"format": "append-only JSONL", "dir": "state/"},
    "order_prevention": "fail-closed ReadOnlyMT5Proxy; write capabilities unreachable by construction; automated tests",
})

# ── strategy registry ─────────────────────────────────────────────────────
jwrite("CTBT_T4_STRATEGY_REGISTRY.json", {
    "entries": [
        {"strategy": "EUR_GBP_USD", "version_id": VERSIONS["EUR_GBP_USD"],
         "strategy_hash": HASHES["EUR_GBP_USD"],
         "status": "FORWARD_SHADOW_ONLY",
         "input_symbols": ["EURGBP.PRO", "EURUSD.PRO", "GBPUSD.PRO"],
         "runtime_slot": "separate from canonical AUD_GBP_NZD"},
        {"strategy": "GBP_NZD_USD", "version_id": VERSIONS["GBP_NZD_USD"],
         "strategy_hash": HASHES["GBP_NZD_USD"],
         "status": "FORWARD_SHADOW_ONLY",
         "input_symbols": ["GBPNZD.PRO", "GBPUSD.PRO", "NZDUSD.PRO"],
         "runtime_slot": "separate from canonical AUD_GBP_NZD"},
    ],
    "status_meaning": {
        "FORWARD_SHADOW_ONLY": "observe + record only; NOT LIVE, NOT PRODUCTION, NOT CAPITAL_ELIGIBLE"
    },
})

# ── symbol mapping ────────────────────────────────────────────────────────
jwrite("CTBT_T4_SYMBOL_MAPPING.json", {
    "rule": "explicit deterministic mapping; no silent runtime inference",
    "broker": "Ox Securities MetaTrader 5 (OxSecurities-Demo), terminal build 6090",
    "mapping": SYM,
    "candidates": {
        "EUR_GBP_USD": {"legs": ["EURGBP", "EURUSD", "GBPUSD"],
                         "broker_symbols": ["EURGBP.PRO", "EURUSD.PRO", "GBPUSD.PRO"]},
        "GBP_NZD_USD": {"legs": ["GBPNZD", "GBPUSD", "NZDUSD"],
                        "broker_symbols": ["GBPNZD.PRO", "GBPUSD.PRO", "NZDUSD.PRO"]},
    },
    "verified_live": True,
})

# ── provider status (from the read-only activation probe) ─────────────────
jwrite("CTBT_T4_PROVIDER_STATUS.json", {
    "provider_connected": True,
    "account": {"login": 1114712, "server": "OxSecurities-Demo", "trade_mode": 0,
                "trade_mode_label": "DEMO", "currency": "USD"},
    "terminal": {"company": "Ox Securities Pty Ltd", "build": 6090, "connected": True},
    "symbols_mapped": True,
    "symbols_verified": list(SYM.values()),
    "m5_rates_available": True,
    "m5_history_30d_per_leg": {"EURGBP.PRO": 6320, "EURUSD.PRO": 6320, "GBPUSD.PRO": 6320,
                               "GBPNZD.PRO": 6320, "NZDUSD.PRO": 6320},
    "observed_spread_points": {"EURGBP.PRO": 2, "EURUSD.PRO": 1, "GBPUSD.PRO": 2,
                               "GBPNZD.PRO": 11, "NZDUSD.PRO": 1},
    "leg_sync_at_probe": {"EUR_GBP_USD": True, "GBP_NZD_USD": True},
    "role": "READ_ONLY_MARKET_DATA_SOURCE — no orders, no account mutation",
    "probe_ts_utc": "2026-08-20T15:55:00Z",
})

# ── shadow event schema ───────────────────────────────────────────────────
jwrite("CTBT_T4_SHADOW_EVENT_SCHEMA.json", {
    "fields": [
        "strategy_version", "strategy_hash", "event_id", "provider", "environment",
        "decision_bar_timestamp", "signal_timestamp", "triangle", "direction",
        "entry_z", "basis", "leg_symbols", "leg_directions", "w2_model_weights",
        "bid", "ask", "mid", "spread_per_leg", "modeled_cost_bps",
        "observed_quote_crossing_cost_bps", "observed_model_cost_multiple",
        "theoretical_entry_state", "exit_timestamp", "exit_z", "exit_reason",
        "gross_bps", "net_modeled_bps", "net_observed_cost_bps", "mae_bps",
        "mfe_bps", "hold_minutes", "completeness_classification",
        "quote_freshness", "cross_leg_skew_seconds", "missing_leg",
        "stale_quote", "spread_anomaly", "data_validity",
    ],
    "note": "mae/mfe filled when the theoretical basket would be live; completeness set by the independent auditor; slippage = NOT_OBSERVED until demo fills exist",
})

# ── cost capture schema ───────────────────────────────────────────────────
jwrite("CTBT_T4_COST_CAPTURE_SCHEMA.json", {
    "per_leg_at_signal": ["bid", "ask", "mid", "spread", "quote_timestamp"],
    "quote_quality": ["quote_freshness", "cross_leg_timestamp_skew_seconds",
                      "missing_leg", "stale_quote_status", "spread_anomaly", "data_validity"],
    "quote_quality_note": "where true tick age/skew cannot be measured -> NOT_AVAILABLE; no invented precision",
    "basket": {"modeled_cost_bps": "frozen T1.1 conservative contract",
               "observed_quote_crossing_cost_bps": "computed from captured quotes",
               "observed_model_cost_multiple": "observed / modeled"},
    "slippage": "NOT_OBSERVED until actual demo fills exist",
    "separation": "historical modeled cost remains separate from observed shadow quote-crossing cost",
})

# ── demo canary review contract ───────────────────────────────────────────
jwrite("CTBT_T4_DEMO_CANARY_REVIEW_CONTRACT.json", {
    "eligibility": "DEMO_CANARY_REVIEW_ELIGIBLE only if BOTH: >=10 clean natural forward shadow events AND >=28 elapsed calendar days since T4 activation",
    "not_equal_to": ["FORWARD_VALIDATED", "PRODUCTION_READY", "CAPITAL_READY"],
    "gates": {
        "A_min_10_events": ">=10 completed natural shadow events",
        "B_min_28_days": ">=28 calendar days elapsed",
        "C_100pct_recognition": "100% expected signal recognition",
        "D_no_unexplained_missed": "zero unexplained MISSED_SIGNAL",
        "E_no_unexplained_runtime_only": "zero unexplained RUNTIME_ONLY_SIGNAL",
        "F_no_causality_failure": "no causality failure",
        "G_no_config_drift": "no strategy-hash/config drift",
        "H_no_persistent_divergence": "no persistent data divergence",
        "I_cost_compatibility": "observed provider crossing costs economically compatible with historical gross edge",
        "J_no_mechanism_inversion": "forward gross mechanism has not clearly inverted",
        "K_no_runtime_defect": "no severe runtime/reconciliation defect",
    },
    "if_any_fails": "candidate remains SHADOW ONLY",
    "independent_promotion": "EUR_GBP_USD and GBP_NZD_USD promote independently",
    "orders": "DEMO_CANARY_REVIEW_ELIGIBLE does NOT authorize orders; demo execution requires SW-CTBT-T5 with human authorization",
})

# ── forward evidence contract ─────────────────────────────────────────────
jwrite("CTBT_T4_FORWARD_EVIDENCE_CONTRACT.json", {
    "forward_starts": "strictly after activation seal; no earlier bar relabeled",
    "horizons": {"early_diagnostic": 15, "minimum_useful": 30, "preferred": 50,
                 "note": "15 is diagnostic only, never validation; thresholds unchanged from T3"},
    "expectancy_states": ["INSUFFICIENT_EVENTS", "MECHANISM_ALIGNED", "MECHANISM_WEAKENED",
                          "MECHANISM_BROKEN", "COST_MARGIN_HEALTHY", "COST_MARGIN_TIGHT",
                          "COST_MARGIN_BROKEN"],
    "states_do_not_authorize_trading": True,
    "early_scientific_stop": {
        "permitted_only_for": ["causality failure", "strategy/runtime mismatch",
                               "gross mechanism inversion", "severe cost impossibility",
                               "invalid data"],
        "not_permitted_for": "ordinary drawdown or losing streak",
    },
    "metrics_per_candidate": ["signals", "completed_events", "events_per_week", "gross_ev",
                              "net_modeled_ev", "net_observed_cost_ev", "wr", "median_ev",
                              "pf", "payoff_ratio", "max_dd", "p5", "worst_event",
                              "losing_streak", "mae", "mfe", "hold_distribution",
                              "z6_rate", "hard_exit_rate",
                              "signal_time_cost_median_p75_p90_p95", "observed_model_cost_multiple"],
    "monthly_engineering_audit": ["runtime_uptime", "missing_bars", "data_divergences",
                                  "signal_classifications", "provider_costs",
                                  "event_count", "hash_integrity"],
    "no_strategy_changes": True,
})

# ── canonical noninterference ─────────────────────────────────────────────
jwrite("CTBT_T4_CANONICAL_NONINTERFERENCE.json", {
    "canonical_aud_gbp_nzd": {
        "may_share": ["provider", "market-data process", "runtime infrastructure"],
        "must_not_share": ["strategy state", "event ledger", "completeness ledger",
                           "evidence count", "candidate metrics"],
        "continues_independently": True,
        "priority": "canonical TB forward takes precedence",
    },
    "ctbt_ledgers": ["state/ledger_EUR_GBP_USD.jsonl", "state/ledger_GBP_NZD_USD.jsonl",
                     "state/ledger_EUR_GBP_USD.audit.jsonl", "state/ledger_GBP_NZD_USD.audit.jsonl"],
})

# ── nonregression ─────────────────────────────────────────────────────────
jwrite("CTBT_T4_NONREGRESSION.json", {
    "t1_t11_t2_t3_artifacts_unchanged": True,
    "canonical_405_194_anchors_unchanged": True,
    "sealed_hashes_unchanged": HASHES,
    "no_historical_optimization": True,
    "no_2026_historical_research": True,
    "engine_source": "run_t11_screen.py reused verbatim; runtime parity proven by tests/test_sealed_engine.py (146 + 81 events identical to T2 ledger)",
    "activation_after_t3": True,
    "forward_evidence_only_after_activation": True,
})

# ── activation seal / forward clock: PENDING templates (stamped post-commit)
jwrite("CTBT_T4_ACTIVATION_SEAL.json", {
    "status": "PENDING_ACTIVATION",
    "note": "Stamped by ctbt_runtime/activate.py after the T4 commit exists (seal contains its own commit SHA).",
    "activation_commit": None,
    "activation_timestamp_utc": None,
    "first_eligible_m5_bar": None,
})
jwrite("CTBT_T4_FORWARD_CLOCK.json", {
    "status": "PENDING_ACTIVATION",
    "authoritative": False,
})

print("T4 static artifacts written.")
