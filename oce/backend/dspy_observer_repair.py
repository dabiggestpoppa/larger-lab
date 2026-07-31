"""
DSPy Observer Repair Pipeline — OCE Phase 3
=============================================
Auto-diagnoses observer failures and suggests repair actions.

Uses DSPy signatures to classify failures and recommend repairs.
Falls back to rule-based diagnosis when DSPy is not installed.

Task: OCE-3.20
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from srrs_opc import (
    RepairPatch,
    DriftDetector,
    EntropyBudgetManager,
    AdaptiveCompressionEngine,
    RecoverabilityEconomics,
)

logger = logging.getLogger("oce.dspy.observer_repair")

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None


# ─── Error Classification ─────────────────────────────────────────────────────

ERROR_CATEGORIES = {
    "entropy_exhausted": {
        "patterns": ["entropy", "budget", "exhausted", "depleted"],
        "severity": "high",
        "repair": "suspend_and_replenish",
    },
    "drift_detected": {
        "patterns": ["drift", "diverge", "inconsistent", "stale"],
        "severity": "medium",
        "repair": "trigger_self_check",
    },
    "memory_overflow": {
        "patterns": ["memory", "overflow", "oom", "allocation"],
        "severity": "high",
        "repair": "compress_state",
    },
    "event_loop_stall": {
        "patterns": ["timeout", "stall", "hang", "blocked", "deadlock"],
        "severity": "critical",
        "repair": "restart_observer",
    },
    "telegram_error": {
        "patterns": ["telegram", "api", "network", "connection", "fetch"],
        "severity": "medium",
        "repair": "check_network_restart",
    },
    "config_error": {
        "patterns": ["config", "schema", "validation", "invalid", "missing"],
        "severity": "high",
        "repair": "reset_config",
    },
    "session_stuck": {
        "patterns": ["session", "stuck", "zombie", "orphaned"],
        "severity": "medium",
        "repair": "clean_sessions",
    },
    "unknown": {
        "patterns": [],
        "severity": "low",
        "repair": "log_and_monitor",
    },
}


def classify_error(error_log: str) -> Dict[str, Any]:
    """Classify an error log into a known category."""
    error_lower = error_log.lower()
    for category, info in ERROR_CATEGORIES.items():
        if category == "unknown":
            continue
        for pattern in info["patterns"]:
            if pattern in error_lower:
                return {
                    "category": category,
                    "severity": info["severity"],
                    "repair": info["repair"],
                }
    return {
        "category": "unknown",
        "severity": "low",
        "repair": "log_and_monitor",
    }


# ─── Repair Actions ───────────────────────────────────────────────────────────

REPAIR_ACTIONS = {
    "suspend_and_replenish": {
        "description": "Suspend observer and request entropy budget replenishment",
        "steps": [
            "Set observer state to SUSPENDED",
            "Request budget replenishment from EntropyBudgetManager",
            "Wait for budget > 20%",
            "Resume observer",
        ],
        "estimated_seconds": 30,
    },
    "trigger_self_check": {
        "description": "Trigger RepairPatch self-check cycle",
        "steps": [
            "Run RepairPatch.self_check()",
            "If inconsistent, run RepairPatch.repair()",
            "Verify consistency after repair",
        ],
        "estimated_seconds": 10,
    },
    "compress_state": {
        "description": "Compress observer state via AdaptiveCompressionEngine",
        "steps": [
            "Snapshot current state",
            "Run AdaptiveCompressionEngine.compress()",
            "Verify recoverability > 0.9",
            "Resume with compressed state",
        ],
        "estimated_seconds": 15,
    },
    "restart_observer": {
        "description": "Full observer restart",
        "steps": [
            "Destroy current observer instance",
            "Clear observer state",
            "Create new observer with same config",
            "Activate observer",
        ],
        "estimated_seconds": 20,
    },
    "check_network_restart": {
        "description": "Check network connectivity and restart if needed",
        "steps": [
            "Ping Telegram API",
            "If unreachable, wait 30s and retry",
            "If still unreachable, restart observer",
        ],
        "estimated_seconds": 45,
    },
    "reset_config": {
        "description": "Reset observer configuration to defaults",
        "steps": [
            "Load default config for observer type",
            "Validate config schema",
            "Apply config",
            "Restart observer",
        ],
        "estimated_seconds": 15,
    },
    "clean_sessions": {
        "description": "Clean stuck/orphaned sessions",
        "steps": [
            "List all sessions",
            "Identify sessions older than threshold",
            "Remove stale sessions",
            "Verify session count < max",
        ],
        "estimated_seconds": 5,
    },
    "log_and_monitor": {
        "description": "Log error and continue monitoring",
        "steps": [
            "Log error to monitor log",
            "Increment error counter",
            "If error count > threshold, escalate",
        ],
        "estimated_seconds": 1,
    },
}


# ─── Heuristic Diagnosis ──────────────────────────────────────────────────────

class ObserverRepairHeuristic:
    """Rule-based observer repair diagnosis (no DSPy required)."""

    def __init__(self):
        self._repair_patch = RepairPatch()
        self._drift_detector = DriftDetector()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._compression = AdaptiveCompressionEngine()
        self._recoverability = RecoverabilityEconomics()

    def diagnose(
        self,
        error_log: str,
        health_metrics: Dict[str, Any],
        recent_events: List[Dict],
    ) -> Dict[str, Any]:
        """Diagnose observer failure and recommend repair."""
        # Classify the error
        classification = classify_error(error_log)
        repair_action = REPAIR_ACTIONS[classification["repair"]]

        # Enhance diagnosis with health metrics
        diagnosis = classification["category"]
        severity = classification["severity"]

        # Check entropy
        entropy_used = health_metrics.get("entropy_consumed", 0)
        entropy_budget = health_metrics.get("entropy_budget", 500)
        if entropy_budget > 0 and entropy_used / entropy_budget > 0.9:
            diagnosis = "entropy_exhausted"
            severity = "critical"
            repair_action = REPAIR_ACTIONS["suspend_and_replenish"]

        # Check drift
        drift_signals = health_metrics.get("drift_signals", 0)
        if drift_signals > 3:
            diagnosis = "drift_detected"
            severity = max(severity, "medium")
            repair_action = REPAIR_ACTIONS["trigger_self_check"]

        # Check memory
        memory_mb = health_metrics.get("memory_mb", 0)
        if memory_mb > 500:
            diagnosis = "memory_overflow"
            severity = "high"
            repair_action = REPAIR_ACTIONS["compress_state"]

        # Check error rate
        error_rate = health_metrics.get("error_rate", 0)
        if error_rate > 0.25:
            severity = "critical"
            repair_action = REPAIR_ACTIONS["restart_observer"]

        return {
            "diagnosis": diagnosis,
            "severity": severity,
            "repair_action": repair_action["description"],
            "repair_steps": repair_action["steps"],
            "estimated_recovery_time": repair_action["estimated_seconds"],
            "method": "heuristic",
        }


# ─── DSPy Diagnosis ───────────────────────────────────────────────────────────

if DSPY_AVAILABLE:
    class ObserverRepairSignature(dspy.Signature):
        """Diagnose observer failures and recommend repair actions."""
        error_log = dspy.InputField(desc="Recent error messages from observer")
        health_metrics = dspy.InputField(desc="Entropy, drift, memory usage, event throughput (JSON)")
        recent_events = dspy.InputField(desc="Last 20 events processed (JSON)")

        diagnosis = dspy.OutputField(desc="Root cause classification (e.g., entropy_exhausted, drift_detected)")
        severity = dspy.OutputField(desc="low/medium/high/critical")
        repair_action = dspy.OutputField(desc="Specific repair action to take")
        estimated_recovery_time = dspy.OutputField(desc="Estimated seconds to recover (integer)")


    class DSPyObserverRepairDiagnoser(dspy.Module):
        """DSPy module for diagnosing observer failures."""

        def __init__(self):
            self.diagnose = dspy.ChainOfThought(ObserverRepairSignature)

        def forward(
            self,
            error_log: str,
            health_metrics: Dict[str, Any],
            recent_events: List[Dict],
        ) -> Dict[str, Any]:
            result = self.diagnose(
                error_log=error_log,
                health_metrics=str(health_metrics),
                recent_events=str(recent_events[-20:]),
            )
            return {
                "diagnosis": result.diagnosis,
                "severity": result.severity,
                "repair_action": result.repair_action,
                "estimated_recovery_time": int(result.estimated_recovery_time),
                "method": "dspy",
            }


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class ObserverRepairPipeline:
    """
    Observer repair pipeline.
    Uses DSPy when available, falls back to heuristics.
    """

    def __init__(self, lm: Optional[Any] = None):
        self._dspy_available = DSPY_AVAILABLE
        self._heuristic = ObserverRepairHeuristic()
        self._diagnoser = None
        if self._dspy_available:
            try:
                self._diagnoser = DSPyObserverRepairDiagnoser()
                if lm:
                    dspy.configure(lm=lm)
            except Exception as e:
                logger.warning(f"DSPy diagnoser init failed, using heuristics: {e}")
                self._dspy_available = False

    def diagnose(
        self,
        error_log: str,
        health_metrics: Dict[str, Any],
        recent_events: List[Dict],
    ) -> Dict[str, Any]:
        """Diagnose observer failure and recommend repair."""
        if self._dspy_available and self._diagnoser:
            try:
                return self._diagnoser(error_log, health_metrics, recent_events)
            except Exception as e:
                logger.warning(f"DSPy diagnosis failed, using heuristics: {e}")

        return self._heuristic.diagnose(error_log, health_metrics, recent_events)

    def execute_repair(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a repair action based on diagnosis."""
        repair_name = diagnosis.get("repair_action", "").lower()
        result = {
            "diagnosis": diagnosis,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "steps_completed": [],
        }

        try:
            if "suspend" in repair_name or "entropy" in repair_name:
                # Suspend and replenish
                self._entropy_budget.replenish(amount=100.0)
                result["steps_completed"].append("entropy_replenished")
                result["success"] = True

            elif "compress" in repair_name or "memory" in repair_name:
                # Compress state
                self._compression.compress(layer="state", ratio=0.5)
                result["steps_completed"].append("state_compressed")
                result["success"] = True

            elif "drift" in repair_name or "self_check" in repair_name:
                # Trigger self-check
                check_result = self._repair_patch.self_check()
                result["steps_completed"].append(f"self_check:{check_result}")
                result["success"] = True

            elif "restart" in repair_name:
                result["steps_completed"].append("restart_requested")
                result["success"] = True  # Actual restart handled by ObserverRuntime

            elif "session" in repair_name:
                result["steps_completed"].append("session_cleanup_requested")
                result["success"] = True

            else:
                result["steps_completed"].append("logged_for_monitoring")
                result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Repair execution failed: {e}")

        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "dspy_available": self._dspy_available,
            "method": "dspy" if self._dspy_available else "heuristic",
            "error_categories": list(ERROR_CATEGORIES.keys()),
            "repair_actions": list(REPAIR_ACTIONS.keys()),
        }
