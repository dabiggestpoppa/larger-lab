"""
CTBT T4 — Frozen runtime configuration.

All values here are sealed at T3/T4.  A runtime that loads a strategy MUST
verify its hash against STRATEGY_HASHES before evaluating anything.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
T11_REPAIR = REPO / "research" / "shallow_well" / "canonical_tb_transfer" / "t11_repair"
T4_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = T4_DIR / "state"

# ── sealed strategy registry ──────────────────────────────────────────────
STRATEGY_HASHES = {
    "EUR_GBP_USD": "aad0a8e64c6964952eb9129ac2cdebd34d308e6df87ebf45e4584c351044b1a7",
    "GBP_NZD_USD": "5538d63a8acb29883b117fc23c76b1fe389db47ed89009ab3cd258b864f62485",
}
STRATEGY_VERSIONS = {
    "EUR_GBP_USD": "CTBT-EUR-GBP-USD-v1",
    "GBP_NZD_USD": "CTBT-GBP-NZD-USD-v1",
}

# triangle -> (A, B, C) basis legs (frozen orientation, T3 basis orientation)
BASIS_LEGS = {
    "EUR_GBP_USD": ("EURGBP", "EURUSD", "GBPUSD"),
    "GBP_NZD_USD": ("GBPNZD", "GBPUSD", "NZDUSD"),
}

# ── provider symbol mapping (explicit, recorded, no runtime guessing) ─────
# Broker: Ox Securities MetaTrader 5 (OxSecurities-Demo), terminal 6090.
SYMBOL_MAP = {
    "EURGBP": "EURGBP.PRO",
    "EURUSD": "EURUSD.PRO",
    "GBPUSD": "GBPUSD.PRO",
    "GBPNZD": "GBPNZD.PRO",
    "NZDUSD": "NZDUSD.PRO",
}
# Observed live spreads (points) at activation probe (read-only), 2026-08-20:
OBSERVED_SPREAD_POINTS = {
    "EURGBP.PRO": 2, "EURUSD.PRO": 1, "GBPUSD.PRO": 2,
    "GBPNZD.PRO": 11, "NZDUSD.PRO": 1,
}

# ── provider / environment ────────────────────────────────────────────────
PROVIDER = {
    "name": "Ox Securities MetaTrader 5",
    "server": "OxSecurities-Demo",
    "account": 1114712,
    "trade_mode": 0,          # 0 = demo
    "currency": "USD",
    "leverage": 500,
    "terminal_build": 6090,
    "role": "READ_ONLY_MARKET_DATA_SOURCE",
    "no_orders": True,
}

# ── feed / engine frozen contract (T3 seal) ───────────────────────────────
ENGINE = {
    "timeframe": "M5",
    "rolling_z_lookback": 200,
    "ddof": 0,
    "current_bar_excluded": True,
    "entry_primary": 3.0,
    "entry_control_descriptive": 2.5,
    "exit_e1": {"short_exit_z": -0.25, "long_exit_z": 0.25},
    "stop_z6": 6.0,
    "session": {"london_start_h_est": 3, "london_end_h_est": 12, "utc_offset": -5},
    "min_runway_minutes": 120,
    "hard_exit_h_est": 12,
    "concurrency": 1,
    "reentry": "canonical deterministic lifecycle",
    "cost_contract": "HISTORICAL_MODELED_COST_CONTRACT (T1.1 conservative: 1.5 pip floor + 1.4 pips/leg commission)",
}

# ── runtime behavior ──────────────────────────────────────────────────────
RUNTIME = {
    "poll_interval_seconds": 60,
    "max_bars_per_fetch": 5000,
    "warmup_bars": 200,
    "ledger_dir": STATE_DIR,
    "pid_file": STATE_DIR / ".ctbt_shadow.pid",
    "log_file": STATE_DIR / "ctbt_shadow.log",
    "activation_seal": T4_DIR / "CTBT_T4_ACTIVATION_SEAL.json",
    "forward_clock": T4_DIR / "CTBT_T4_FORWARD_CLOCK.json",
}

# forward evidence horizons (T3/T4 frozen)
HORIZONS = {
    "early_diagnostic_events": 15,
    "minimum_useful_events": 30,
    "preferred_events": 50,
}
DEMO_CANARY = {
    "min_events": 10,
    "min_days": 28,
}
