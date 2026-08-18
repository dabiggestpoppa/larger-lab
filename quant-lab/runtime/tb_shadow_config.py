#!/usr/bin/env python3
"""QL-EXEC-R4.2 — TB generic shadow configuration (isolated paths + frozen budget).

Every mutable shadow artifact lives under ``quant-lab/shadow_state/
tb-generic-shadow-g1/`` — NEVER any active TB path. The shadow's desired state,
PID lock, SQLite store, logs, and telemetry are all separate from tbctl / the
active supervisor/worker/dashboard.
"""
from __future__ import annotations

import os
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent  # quant-lab/

# ─── ISOLATED SHADOW STATE ────────────────────────────────────────────────
RUNTIME_ID = "tb-generic-shadow-g1"
DEPLOYMENT_GENERATION = "TB-GENERIC-SHADOW-G1"

# Env override keeps shadowctl / process / tests isolated (QL_SHADOW_STATE_DIR
# points at a temp directory under test). Production default is the dedicated
# shadow_state dir under quant-lab — never an active TB path.
_env_state = os.environ.get("QL_SHADOW_STATE_DIR")
SHADOW_STATE_DIR = (
    Path(_env_state) if _env_state else QUANT_LAB / "shadow_state" / RUNTIME_ID
)
SHADOW_STATE_DIR.mkdir(parents=True, exist_ok=True)

SHADOW_DB = SHADOW_STATE_DIR / "runtime.sqlite"
SHADOW_PID_FILE = SHADOW_STATE_DIR / "shadow.pid"
SHADOW_DESIRED_STATE_FILE = SHADOW_STATE_DIR / "shadow_desired_state"
SHADOW_LOG = SHADOW_STATE_DIR / "logs" / "shadow.log"
HEARTBEAT_JSON = SHADOW_STATE_DIR / "heartbeat.json"
TELEMETRY_JSON = SHADOW_STATE_DIR / "telemetry.json"
PARITY_JSONL = SHADOW_STATE_DIR / "parity.jsonl"
MISMATCH_JSONL = SHADOW_STATE_DIR / "mismatches.jsonl"

# Legacy worker writes this append-only export; the shadow ONLY reads it.
LEGACY_EXPORT_FILE = SHADOW_STATE_DIR / "legacy_export.jsonl"

# ─── FROZEN IDENTITY ──────────────────────────────────────────────────────
LEGACY_AUTHORITY_SHA = "b48fd35255b41865026a3cba333ae2a2a0d6a004"
R4_AUTHORITY_SHA = "750a14bf20bf0869f452d8df20138e58bbb091e5"
SHADOW_PROFILE_HASH = "tb-generic-shadow-g1-profile-hash"   # frozen at deploy
PARITY_SCHEMA_VERSION = 1
TOLERANCE_VERSION = "r4_1_v1"

# ─── DESIRED STATE ────────────────────────────────────────────────────────
RUNNING = "RUNNING"
STOPPED_BY_USER = "STOPPED_BY_USER"


# ─── RESOURCE BUDGET (frozen; measured, never tuned on PnL) ───────────────
MAX_CPU_PCT = 5.0            # sustained % of one core over 60 s
MAX_MEM_RSS_BYTES = 256 * 1024 * 1024
MAX_DISK_GROWTH_BYTES_H = 10 * 1024 * 1024
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5
HEARTBEAT_INTERVAL_S = 10

# ─── PROCESS / BOOT ───────────────────────────────────────────────────────
# G1 starts manually; Task Scheduler / logon autostart is FUTURE work only.
AUTO_START_ENABLED = False
