#!/usr/bin/env python3
"""
Fix field directory naming (digits are invalid Python identifiers),
complete the health monitor, fix all __init__.py exports, and rebuild.
"""
import os
import sys
import shutil
import re

BASE = os.path.join(os.path.dirname(__file__), "..", "field")

# Map broken names -> valid names
PHASE_MAP = {
    "4_instrumentation": "phase4_instrumentation",
    "5_continuity":       "phase5_continuity",
    "6_resonance":        "phase6_resonance",
    "7_multiscale":       "phase7_multiscale",
    "8_coevolution":      "phase8_coevolution",
    "9_emergence":        "phase9_emergence",
}

PHASES = {
    "phase4_instrumentation": [
        "instrumentation_bus", "adaptive_profiler", "field_state_snapshot",
        "consensus_observer", "resource_orchestrator", "sovereign_dashboard",
    ],
    "phase5_continuity": [
        "long_term_memory", "memory_consolidation", "temporal_reasoner",
        "pattern_librarian", "continuity_guardian", "session_bridger",
        "knowledge_graph", "dream_state_engine",
    ],
    "phase6_resonance": [
        "resonance_bus", "cognitive_harmony", "collective_reasoning",
        "belief_propagation", "emergent_insight_detector",
    ],
    "phase7_multiscale": [
        "scale_router", "tick_engine", "bar_engine", "session_engine",
        "daily_engine", "weekly_engine", "scale_bridge",
    ],
    "phase8_coevolution": [
        "operator_profiles", "feedback_collector", "field_adaptation",
        "coevolution_tracker", "suggestion_engine", "trust_calibration",
        "autonomy_manager",
    ],
    "phase9_emergence": [
        "field_consciousness", "self_model", "goal_formation",
        "priority_arbiter", "field_drift_correction", "emergence_monitor",
    ],
}

# ── Step 1: Rename digit-prefixed directories ──────────────────────
print("=" * 60)
print("STEP 1: Renaming directories...")
for old, new in PHASE_MAP.items():
    old_path = os.path.join(BASE, old)
    new_path = os.path.join(BASE, new)
    if os.path.exists(old_path):
        if os.path.exists(new_path):
            print(f"  Merging {old} -> {new} (target exists, copying files)")
            for item in os.listdir(old_path):
                src = os.path.join(old_path, item)
                dst = os.path.join(new_path, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            shutil.rmtree(old_path)
        else:
            print(f"  Rename: {old} -> {new}")
            shutil.move(old_path, new_path)
    else:
        print(f"  Skip (no dir): {old}")

# ── Step 2: Fix all test imports ───────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Fixing test imports...")

for phase_dir, modules in PHASES.items():
    tests_dir = os.path.join(BASE, phase_dir, "tests")
    if not os.path.exists(tests_dir):
        continue
    for f in os.listdir(tests_dir):
        if not f.startswith("test_") or not f.endswith(".py"):
            continue
        fpath = os.path.join(tests_dir, f)
        with open(fpath, "r") as fh:
            content = fh.read()
        # Fix imports like: from field.9_emergence.X import Y
        # -> from field.phase9_emergence.X import Y
        new_content = content
        for old_prefix, new_prefix in PHASE_MAP.items():
            pattern = rf'from field\.{re.escape(old_prefix)}\.'
            replacement = f'from field.{new_prefix}.'
            new_content = re.sub(pattern, replacement, new_content)
        if new_content != content:
            with open(fpath, "w") as fh:
                fh.write(new_content)
            print(f"  Fixed: {fpath}")

# ── Step 3: Fix all module __init__.py imports ─────────────────────
print("\n" + "=" * 60)
print("STEP 3: Fixing __init__.py imports...")

for phase_dir, modules in PHASES.items():
    init_path = os.path.join(BASE, phase_dir, "__init__.py")
    # Build import lines for all modules in this phase
    imports = []
    all_exports = []
    for m in modules:
        class_name = m.title().replace("_", "") + "Module"
        imports.append(f"from .{m} import {class_name}")
        all_exports.append(f'"{class_name}"')
    if imports and os.path.exists(os.path.dirname(init_path)):
        content = "\n".join(imports) + "\n\n__all__ = [" + ", ".join(all_exports) + "]\n"
        with open(init_path, "w") as fh:
            fh.write(content)
        print(f"  Rewrote: {init_path}")

# ── Step 4: Fix field/__init__.py ──────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Fixing field/__init__.py...")

field_init = os.path.join(BASE, "__init__.py")
field_init_content = '''"""Sovereign Field System — Phases 4–9
=====================================
The field: self-aware, self-healing, multi-scale cognitive infrastructure.

Phases:
  4 - Sovereign Instrumentation  (8 modules)  — field observes itself
  5 - Long-Horizon Continuity    (8 modules)  — field remembers across time
  6 - Resonant Cognition         (5 modules)  — agents think together
  7 - Multi-Scale Fields         (7 modules)  — multi-timeframe processing
  8 - Operator Coevolution       (7 modules)  — operators + field evolve together
  9 - Sovereign Field Emergence  (6 modules)  — field becomes autonomous entity

Total: 41 modules across 6 phases
"""

__version__ = "4.0.0"
__phases__ = [4, 5, 6, 7, 8, 9]
__total_modules__ = 41

# Import all phase modules
from field.phase4_instrumentation import *  # noqa: F401,F403
from field.phase5_continuity import *       # noqa: F401,F403
from field.phase6_resonance import *        # noqa: F401,F403
from field.phase7_multiscale import *       # noqa: F401,F403
from field.phase8_coevolution import *     # noqa: F401,F403
from field.phase9_emergence import *       # noqa: F401,F403
'''
with open(field_init, "w") as fh:
    fh.write(field_init_content)
print(f"  Rewrote: {field_init}")

# ── Step 5: Complete the health monitor ────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Completing sovereign_health_monitor.py...")

health_monitor_path = os.path.join(BASE, "sovereign_health_monitor.py")
# Check if truncated (missing reset_module and more)
with open(health_monitor_path, "r") as fh:
    content = fh.read()

if "def reset_module" not in content:
    # Find the end of the class and add missing methods
    # The file is truncated after "enabled:"
    full_content = '''"""
4.2 Sovereign Health Monitor — Sovereign Instrumentation
==========================================================
Health dashboard — latency, throughput, error rates, drift metrics.

Aggregates health signals from all field modules into a unified
health report with configurable alerting thresholds.

Singleton pattern consistent with OCE backend modules.
"""

import sqlite3
import json
import logging
import os
import psutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional
from time import monotonic

from pydantic import BaseModel, Field

logger = logging.getLogger("field.health")

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "health.db"


# ── Pydantic Models ──────────────────────────────────────────────

class HealthMetrics(BaseModel):
    module_name: str
    latency_ms: float = 0.0
    throughput_events_per_sec: float = 0.0
    error_rate_pct: float = 0.0
    queue_depth: int = 0
    memory_mb: float = 0.0
    cpu_pct: float = 0.0
    uptime_seconds: int = 0
    status: str = "unknown"  # healthy, degraded, critical, unknown
    last_update: str = ""


class HealthAlert(BaseModel):
    alert_id: str
    module_name: str
    severity: str  # "warning", "critical"
    metric: str
    value: float
    threshold: float
    message: str
    timestamp: str
    resolved: bool = False


class HealthReport(BaseModel):
    timestamp: str
    overall_status: str  # "green", "yellow", "red"
    total_modules: int
    healthy_count: int
    degraded_count: int
    critical_count: int
    avg_latency_ms: float
    total_throughput: float
    overall_error_rate: float
    alerts: List[HealthAlert] = Field(default_factory=list)
    module_metrics: List[HealthMetrics] = Field(default_factory=list)


class HealthConfig(BaseModel):
    """Configuration for the Sovereign Health Monitor."""

    enabled: bool = True
    check_interval_seconds: float = 5.0
    alert_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "latency_ms": 500.0,
        "error_rate_pct": 5.0,
        "memory_mb": 512.0,
        "cpu_pct": 80.0,
    })
    retention_hours: int = 24


# ── Health Monitor Engine ─────────────────────────────────────────

class SovereignHealthMonitor:
    """Singleton health monitor for the sovereign field system.

    Tracks all registered modules, collects metrics, generates alerts,
    and produces periodic health reports. Uses an in-memory dict backed
    by SQLite for persistence.
    """

    _instance: Optional["SovereignHealthMonitor"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "SovereignHealthMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.config = HealthConfig()
        self._modules: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[HealthAlert] = []
        self._history: List[HealthReport] = []
        self._running: bool = False
        self._monitor_thread: Optional[Thread] = None
        self._last_report_time: float = 0.0
        self._init_db()
        self._initialized = True

    def _init_db(self) -> None:
        """Initialize SQLite database for metric persistence."""
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                module_name TEXT NOT NULL,
                status TEXT,
                latency_ms REAL,
                throughput REAL,
                error_rate REAL,
                memory_mb REAL,
                cpu_pct REAL,
                queue_depth INTEGER
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT,
                module_name TEXT,
                severity TEXT,
                metric TEXT,
                value REAL,
                threshold REAL,
                message TEXT,
                timestamp TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    # ── Module Registration ──────────────────────────────────────

    def register_module(self, module_name: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Register a field module for health tracking.

        Args:
            module_name: Unique identifier for the module.
            meta: Optional metadata (version, description, etc.).
        """
        self._modules[module_name] = {
            "status": "unknown",
            "latency_ms": 0.0,
            "throughput": 0.0,
            "error_rate": 0.0,
            "memory_mb": 0.0,
            "cpu_pct": 0.0,
            "queue_depth": 0,
            "uptime_seconds": 0,
            "last_update": datetime.now(timezone.utc).isoformat(),
            "alert_count": 0,
            "meta": meta or {},
        }
        logger.info(f"Registered module: {module_name}")

    def deregister_module(self, module_name: str) -> None:
        """Remove a module from health tracking."""
        if module_name in self._modules:
            del self._modules[module_name]
            logger.info(f"Deregistered module: {module_name}")

    def reset_module(self, module_name: str) -> None:
        """Reset a module's health metrics to defaults."""
        if module_name in self._modules:
            self._modules[module_name] = {
                "status": "unknown",
                "latency_ms": 0.0,
                "throughput": 0.0,
                "error_rate": 0.0,
                "memory_mb": 0.0,
                "cpu_pct": 0.0,
                "queue_depth": 0,
                "uptime_seconds": 0,
                "last_update": datetime.now(timezone.utc).isoformat(),
                "alert_count": 0,
            }
            logger.info(f"Reset module: {module_name}")

    # ── Metric Updates ───────────────────────────────────────────

    def update_metrics(self, module_name: str, metrics: Dict[str, Any]) -> None:
        """Update health metrics for a registered module.

        Args:
            module_name: Name of the module to update.
            metrics: Dict of metric key-value pairs.
        """
        if module_name not in self._modules:
            logger.warning(f"Attempted to update metrics for unregistered module: {module_name}")
            return

        record = self._modules[module_name]
        updatable = ["latency_ms", "throughput", "error_rate", "memory_mb",
                      "cpu_pct", "queue_depth", "status"]
        for key in updatable:
            if key in metrics:
                record[key] = metrics[key]

        record["uptime_seconds"] = record.get("uptime_seconds", 0) + self.config.check_interval_seconds
        record["last_update"] = datetime.now(timezone.utc).isoformat()

        # Check thresholds and generate alerts
        self._check_thresholds(module_name, record)

    def _check_thresholds(self, module_name: str, record: Dict[str, Any]) -> None:
        """Check metrics against configured thresholds and fire alerts."""
        thresholds = self.config.alert_thresholds
        checks = {
            "latency_ms": record.get("latency_ms", 0),
            "error_rate": record.get("error_rate", 0),
            "memory_mb": record.get("memory_mb", 0),
            "cpu_pct": record.get("cpu_pct", 0),
        }
        metric_display = {
            "latency_ms": "latency_ms",
            "error_rate": "error_rate_pct",
            "memory_mb": "memory_mb",
            "cpu_pct": "cpu_pct",
        }

        for metric_key, value in checks.items():
            threshold = thresholds.get(metric_key)
            if threshold is not None and value > threshold:
                severity = "critical" if value > threshold * 2 else "warning"
                alert = HealthAlert(
                    alert_id=f"alert_{module_name}_{metric_key}_{int(monotonic())}",
                    module_name=module_name,
                    severity=severity,
                    metric=metric_display.get(metric_key,