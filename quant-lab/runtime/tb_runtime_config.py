#!/usr/bin/env python3
"""
TB-R6.1 — RUNTIME CONFIGURATION
===============================

Single source of truth for the persistent local demo runtime.

Deployment profiles:
    local_windows   (implemented; this machine with MT5)
    windows_vps     (schema/config template ONLY — no remote deployment)

All engineering gates are pre-registered and frozen; they are never tuned
against strategy PnL.
"""

from __future__ import annotations

import os
from pathlib import Path

# ─── PATHS ────────────────────────────────────────────────────────────────
QUANT_LAB = Path(__file__).resolve().parent.parent          # quant-lab/
REPO_ROOT = QUANT_LAB.parent
STATE_DIR = QUANT_LAB / "state"
LOGS_DIR = QUANT_LAB / "logs"
RUNTIME_DIR = QUANT_LAB / "runtime"

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_DB = STATE_DIR / "tb_runtime.db"
CONTROL_LEDGER = STATE_DIR / "tb_control.db"

SUPERVISOR_PID_FILE = STATE_DIR / "tb_supervisor.pid"
WORKER_PID_FILE = STATE_DIR / "tb_worker.pid"
WATCHER_PID_FILE = STATE_DIR / "tb_basket_watch.pid"    # owned by tb_basket_watcher.py
DASHBOARD_PID_FILE = STATE_DIR / "tb_dashboard.pid"     # owned by tb_dashboard.py
DESIRED_STATE_FILE = STATE_DIR / "tb_desired_state"     # RUNNING | STOPPED_BY_USER

SUPERVISOR_LOG = LOGS_DIR / "tb_supervisor.log"
WORKER_LOG = LOGS_DIR / "tb_runtime.log"
WATCHER_LOG = LOGS_DIR / "tb_basket_watch.log"          # owned by tb_basket_watcher.py
DASHBOARD_LOG = LOGS_DIR / "tb_dashboard.log"

# ─── DEPLOYMENT PROFILE ──────────────────────────────────────────────────
DEPLOYMENT_PROFILE = os.environ.get("TB_DEPLOYMENT_PROFILE", "local_windows")
PROFILES = ("local_windows", "windows_vps")
if DEPLOYMENT_PROFILE not in PROFILES:
    raise RuntimeError(f"unknown deployment profile {DEPLOYMENT_PROFILE!r}")

# ─── SUPERVISOR ──────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL_S = 10          # worker writes a heartbeat every 10 s
HEARTBEAT_GREEN_MAX_S = 30         # <= 30 s => ONLINE
HEARTBEAT_YELLOW_MAX_S = 90        # 30-90 s => DEGRADED; > 90 s => OFFLINE
RESTART_BACKOFF_S = (5, 15, 30, 60)   # bounded exponential backoff (max 60 s)
STALE_HEARTBEAT_RESTART_S = 300    # worker alive but dead heartbeat for 5 min
MT5_RETRY_INTERVAL_S = 30          # WAITING_FOR_MT5 bounded retry
MARKET_CLOSED_INTERVAL_S = 60      # stale-bar poll cadence while market closed

# ─── DASHBOARD ───────────────────────────────────────────────────────────
DASHBOARD_HOST = "127.0.0.1"       # localhost ONLY — never public
DASHBOARD_PORT = 8765

# ─── IDENTITY GATE (approved DEMO environment) ───────────────────────────
REQUIRED_COMPANY = "Ox Securities"
REQUIRED_SERVER = "OxSecurities-Demo"
REQUIRED_TRADE_MODE = 0            # 0 = DEMO (1 = contest, 2 = real)
REQUIRED_CURRENCY = "USD"

CANONICAL = ("GBPAUD", "GBPNZD", "AUDNZD")
BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")
CANON_TO_BROKER = dict(zip(CANONICAL, BROKER_SYMBOLS))

CONTROL_STRATEGY_ID = "TB-FROZEN-CONTROL"
PRIMARY_STRATEGY_ID = "TB-FWD-V1"
CONTROL_MAGIC = 31082026
PRIMARY_MAGIC = 31082026
TEST_MAGIC = 31082027          # TB-DEMO-EXEC-TEST harness only

# ─── EXECUTION GATES (frozen; never tuned on PnL) ────────────────────────
MAX_QUOTE_AGE_MS = 2000
MAX_CROSS_LEG_SKEW_MS = 1000
SPREAD_MAX_PTS = 100
GATE_K_MAX_RESIDUAL_PCT = 10.0
BASKET_NOTIONAL_USD = 5000.0

# Frozen research conversion rates (account currency USD) — R3 contract.
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}

# ─── DISK SAFETY ─────────────────────────────────────────────────────────
MIN_FREE_DISK_GB = 0.5
# ─── LOG ROTATION ────────────────────────────────────────────────────────
LOG_MAX_BYTES = 5 * 1024 * 1024    # 5 MB
LOG_BACKUP_COUNT = 5

# ─── DESIRED STATE ───────────────────────────────────────────────────────
RUNNING = "RUNNING"
STOPPED_BY_USER = "STOPPED_BY_USER"


def read_desired_state() -> str:
    try:
        v = DESIRED_STATE_FILE.read_text(encoding="utf-8").strip().upper()
        if v in (RUNNING, STOPPED_BY_USER):
            return v
    except FileNotFoundError:
        pass
    return RUNNING                      # default: running (safe? no — see note)


def write_desired_state(state: str) -> None:
    if state not in (RUNNING, STOPPED_BY_USER):
        raise ValueError(state)
    DESIRED_STATE_FILE.write_text(state, encoding="utf-8")
