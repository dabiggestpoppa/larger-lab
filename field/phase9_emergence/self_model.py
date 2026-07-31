"""
9_emergence.self_model
=======================
Self-model of the field — maintains a representation of the field's
own state, capabilities, history, and boundaries.

The field's self-model is a structured representation the field maintains
about itself. It tracks:
- Capabilities: what the field can do right now
- State: current operational status of all modules
- History: key events and transitions
- Boundaries: operational limits and constraints
- Confidence: how well the self-model reflects reality

This enables the field to reason about its own state, detect when its
self-model diverges from reality (model drift), and communicate its
status to operators and other agents.

The self-model is updated continuously from module health checks,
coevolution scores, and emergence events. It serves as the field's
"self-awareness" layer.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.self_model")


class Capability(BaseModel):
    """A field capability with its current status."""
    name: str
    description: str = ""
    status: str = "unknown"  # active, degraded, inactive, unknown
    confidence: float = 0.5  # 0-1, how confident we are in this capability
    last_verified: str = ""
    dependencies: List[str] = Field(default_factory=list)


class ModelDrift(BaseModel):
    """A detected discrepancy between self-model and reality."""
    drift_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    aspect: str  # capability, state, boundary, history
    expected: str
    actual: str
    severity: float = 0.5  # 0=minor, 1=critical
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = False


class SelfModelSnapshot(BaseModel):
    """A snapshot of the self-model at a point in time."""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    total_capabilities: int = 0
    active_capabilities: int = 0
    degraded_capabilities: int = 0
    overall_health: float = 0.5
    model_confidence: float = 0.5
    drift_count: int = 0
    unresolved_drifts: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SelfModelConfig(BaseModel):
    """Configuration for self_model."""
    enabled: bool = True
    max_capabilities: int = 200
    max_drifts: int = 500
    max_snapshots: int = 1000
    drift_severity_threshold: float = 0.5
    model_update_interval: int = 30  # seconds between self-model updates
    confidence_decay: float = 0.99  # capability confidence decay when not verified


class SelfModelModule:
    """Self-model — the field's representation of itself."""

    def __init__(self):
        self.config = SelfModelConfig()
        self.running = False
        self._lock = Lock()
        self._capabilities: Dict[str, Capability] = {}
        self._drifts: List[ModelDrift] = []
        self._snapshots: List[SelfModelSnapshot] = []
        self._overall_health: float = 0.5
        self._model_confidence: float = 0.5
        self._module_states: Dict[str, str] = {}
        self._history: List[Dict[str, Any]] = []
        self._update_count: int = 0

    def start(self) -> None:
        """Start the self-model module."""
        self.running = True
        self._record_history("self_model_started", {})
        logger.info("SelfModel started")

    def stop(self) -> None:
        """Stop the self-model module."""
        self.running = False
        self._record_history("self_model_stopped", {
            "total_updates": self._update_count,
            "total_drifts": len(self._drifts),
        })
        logger.info("SelfModel stopped — %d updates, %d drifts detected",
                     self._update_count, len(self._drifts))

    # ── Capability Management ──────────────────────────────────────────

    def register_capability(self, name: str, description: str = "",
                            dependencies: Optional[List[str]] = None) -> Capability:
        """
        Register a new field capability.

        Args:
            name: Unique capability name.
            description: Human-readable description.
            dependencies: Other capabilities this depends on.

        Returns:
            The registered Capability.
        """
        with self._lock:
            if name in self._capabilities:
                cap = self._capabilities[name]
                cap.description = description or cap.description
                cap.dependencies = dependencies or cap.dependencies
                return cap

            if len(self._capabilities) >= self.config.max_capabilities:
                logger.warning("Max capabilities reached, cannot register '%s'", name)
                return Capability(name=name, description=description)

            cap = Capability(
                name=name,
                description=description,
                status="unknown",
                confidence=0.5,
                dependencies=dependencies or [],
            )
            self._capabilities[name] = cap
            self._record_history("capability_registered", {"name": name})
            logger.debug("Capability registered: %s", name)
            return cap

    def update_capability(self, name: str, status: Optional[str] = None,
                          confidence: Optional[float] = None) -> Optional[Capability]:
        """
        Update a capability's status and/or confidence.

        Args:
            name: Capability name.
            status: New status (active, degraded, inactive).
            confidence: New confidence score 0-1.

        Returns:
            Updated Capability, or None if not found.
        """
        with self._lock:
            if name not in self._capabilities:
                logger.warning("Capability '%s' not found", name)
                return None

            cap = self._capabilities[name]
            old_status = cap.status

            if status:
                cap.status = status
            if confidence is not None:
                cap.confidence = max(0.0, min(1.0, confidence))

            cap.last_verified = datetime.now(timezone.utc).isoformat()

            if status and status != old_status:
                self._record_history("capability_changed", {
                    "name": name, "old_status": old_status, "new_status": status,
                })

            return cap

    def get_capability(self, name: str) -> Optional[Dict]:
        """Get a capability by name."""
        with self._lock:
            cap = self._capabilities.get(name)
            return cap.model_dump() if cap else None

    def get_capabilities(self, status_filter: Optional[str] = None) -> List[Dict]:
        """
        Get all capabilities, optionally filtered by status.

        Args:
            status_filter: Filter by status (active, degraded, inactive, unknown).

        Returns:
            List of capability dicts.
        """
        with self._lock:
            caps = list(self._capabilities.values())
            if status_filter:
                caps = [c for c in caps if c.status == status_filter]
            return [c.model_dump() for c in caps]

    # ── Drift Detection ─────────────────────────────────────────────────

    def check_drift(self, aspect: str, expected: str, actual: str,
                    severity: float = 0.5) -> Optional[ModelDrift]:
        """
        Check for model drift — discrepancy between self-model and reality.

        Args:
            aspect: What aspect drifted (capability, state, boundary, history).
            expected: What the self-model expected.
            actual: What was observed.
            severity: How severe the drift is (0-1).

        Returns:
            ModelDrift if drift detected, None if expected matches actual.
        """
        if expected == actual:
            return None

        with self._lock:
            drift = ModelDrift(
                aspect=aspect,
                expected=expected,
                actual=actual,
                severity=round(max(0.0, min(1.0, severity)), 4),
            )
            self._drifts.append(drift)

            # Trim drifts
            if len(self._drifts) > self.config.max_drifts:
                self._drifts = self._drifts[-self.config.max_drifts:]

            # Reduce model confidence on drift
            self._model_confidence = max(0.0, self._model_confidence - 0.05 * drift.severity)

            if drift.severity >= self.config.drift_severity_threshold:
                logger.warning("Model drift detected: %s — expected='%s' actual='%s' severity=%.2f",
                               aspect, expected, actual, drift.severity)

            self._record_history("drift_detected", {
                "aspect": aspect, "severity": drift.severity,
            })
            return drift

    def resolve_drift(self, drift_id: str) -> bool:
        """Mark a drift as resolved."""
        with self._lock:
            for drift in self._drifts:
                if drift.drift_id == drift_id and not drift.resolved:
                    drift.resolved = True
                    self._model_confidence = min(1.0, self._model_confidence + 0.02)
                    logger.info("Drift resolved: %s", drift_id)
                    return True
        return False

    def get_drifts(self, unresolved_only: bool = False,
                   min_severity: float = 0.0) -> List[Dict]:
        """
        Get model drifts.

        Args:
            unresolved_only: Only return unresolved drifts.
            min_severity: Minimum severity threshold.

        Returns:
            List of drift dicts, most recent first.
        """
        with self._lock:
            drifts = list(reversed(self._drifts))
            if unresolved_only:
                drifts = [d for d in drifts if not d.resolved]
            drifts = [d for d in drifts if d.severity >= min_severity]
            return [d.model_dump() for d in drifts]

    # ── Self-Model Snapshot ─────────────────────────────────────────────

    def update_model(self) -> SelfModelSnapshot:
        """
        Recompute the self-model from current data.

        Updates overall health, model confidence, and takes a snapshot.
        Should be called periodically to keep the self-model fresh.

        Returns:
            The new SelfModelSnapshot.
        """
        with self._lock:
            self._update_count += 1

            # Decay unverified capabilities
            for cap in self._capabilities.values():
                if cap.last_verified:
                    cap.confidence = max(0.0, cap.confidence * self.config.confidence_decay)

            # Compute health from capabilities
            total = len(self._capabilities)
            active = sum(1 for c in self._capabilities.values() if c.status == "active")
            degraded = sum(1 for c in self._capabilities.values() if c.status == "degraded")

            if total > 0:
                self._overall_health = (active + 0.5 * degraded) / total
            else:
                self._overall_health = 0.5

            # Recover model confidence slowly
            self._model_confidence = min(1.0, self._model_confidence + 0.01)

            unresolved = sum(1 for d in self._drifts if not d.resolved)

            snapshot = SelfModelSnapshot(
                total_capabilities=total,
                active_capabilities=active,
                degraded_capabilities=degraded,
                overall_health=round(self._overall_health, 4),
                model_confidence=round(self._model_confidence, 4),
                drift_count=len(self._drifts),
                unresolved_drifts=unresolved,
            )

            self._snapshots.append(snapshot)
            if len(self._snapshots) > self.config.max_snapshots:
                self._snapshots = self._snapshots[-self.config.max_snapshots:]

            logger.debug("Self-model updated: health=%.3f confidence=%.3f",
                         self._overall_health, self._model_confidence)
            return snapshot

    def get_snapshot(self) -> Optional[Dict]:
        """Get the latest self-model snapshot."""
        with self._lock:
            if self._snapshots:
                return self._snapshots[-1].model_dump()
            return None

    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get self-model history events."""
        with self._lock:
            return list(reversed(self._history[-limit:]))

    # ── Internal ────────────────────────────────────────────────────────

    def _record_history(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a history event."""
        self._history.append({
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep history bounded
        if len(self._history) > 10000:
            self._history = self._history[-5000:]
