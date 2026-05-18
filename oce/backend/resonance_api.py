"""
V3 Phase 1 — Resonance API Endpoints
FastAPI routes for the Resonant Signal Substrate.

Provides endpoints for:
- Signal injection and querying
- Field state monitoring
- Coherence measurement
- Boundary mapping
- Resonance scoring
- Pressure tracking
"""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from resonance import (
    SignalPacket, SignalField,
    CoherenceEngine, CoherenceSnapshot,
    FieldStateManager, FieldState,
    BoundaryMapper, Boundary, PressureZone,
    ResonanceEngine, ResonanceScore, Constraint,
    PressureTracker, PressureAlert,
)

logger = logging.getLogger("oce.resonance")

# ─── Global Instances ────────────────────────────────────────────────────────

_signal_field = SignalField()
_field_manager = FieldStateManager()
_coherence_engine = CoherenceEngine()
_boundary_mapper = BoundaryMapper()
_resonance_engine = ResonanceEngine()
_pressure_tracker = PressureTracker()


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class InjectSignalRequest(BaseModel):
    source: str
    amplitude: float = 0.5
    coherence: float = 0.5
    phase: float = 0.0
    entropy_delta: float = 0.0
    boundary_tags: list[str] = []
    resonance_targets: list[str] = []
    metadata: dict = {}


class ScoreResonanceRequest(BaseModel):
    observer_id: str
    observer_phase: float = 0.0
    observer_coherence: float = 0.5
    signal_source: str = "api"
    amplitude: float = 0.5
    coherence: float = 0.5
    phase: float = 0.0
    entropy_delta: float = 0.0


class AddConstraintRequest(BaseModel):
    constraint_id: str
    constraint_type: str  # "goal", "system", "resource", "temporal"
    weight: float = 0.5
    phase: float = 0.0
    coherence: float = 0.5


class ObserverRegistration(BaseModel):
    observer_id: str
    phase: float = 0.0
    coherence: float = 0.5


# ─── Registration Function ───────────────────────────────────────────────────

def register_resonance_endpoints(app: FastAPI) -> None:
    """Register all resonance API endpoints on the given FastAPI app."""

    # ── Signal Endpoints ──────────────────────────────────────────────────

    @app.post("/resonance/signal")
    async def inject_signal(request: InjectSignalRequest):
        """Inject a signal into the cognitive field."""
        try:
            signal = SignalPacket(
                source=request.source,
                amplitude=request.amplitude,
                coherence=request.coherence,
                phase=request.phase,
                entropy_delta=request.entropy_delta,
                boundary_tags=request.boundary_tags,
                resonance_targets=request.resonance_targets,
                metadata=request.metadata,
            )
            _signal_field.inject(signal)
            _field_manager.inject_signal(signal)
            return {"status": "injected", "signal_id": signal.signal_id}
        except Exception as e:
            logger.error(f"Signal injection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/signals")
    async def get_signals(
        signal_type: Optional[str] = Query(None, description="resonant, entropic, all"),
        source: Optional[str] = None,
        limit: int = Query(50, ge=1, le=500),
    ):
        """Query signals from the field."""
        try:
            if signal_type == "resonant":
                signals = _signal_field.get_resonant_signals()[:limit]
            elif signal_type == "entropic":
                signals = _signal_field.get_entropic_signals()[:limit]
            elif source:
                signals = _signal_field.get_signals_by_source(source)[:limit]
            else:
                signals = _signal_field.signals[-limit:]
            return {"signals": [s.to_dict() for s in signals], "count": len(signals)}
        except Exception as e:
            logger.error(f"Signal query error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/resonance/signals")
    async def clear_signals():
        """Clear all signals from the field."""
        _signal_field.clear()
        return {"status": "cleared"}

    # ── Field State Endpoints ─────────────────────────────────────────────

    @app.get("/resonance/field")
    async def get_field_state():
        """Get current field state."""
        try:
            state = _field_manager.state
            coherence = _coherence_engine.measure(_signal_field)
            return {
                "field": state.to_dict(),
                "coherence": coherence.to_dict() if coherence else None,
                "signal_count": len(_signal_field.signals),
                "boundary_count": len(_boundary_mapper.boundaries),
            }
        except Exception as e:
            logger.error(f"Field state error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/field/decay")
    async def decay_field():
        """Apply one decay step to the field."""
        try:
            _signal_field.decay()
            _field_manager.decay_step()
            _boundary_mapper.decay()
            return {"status": "decayed"}
        except Exception as e:
            logger.error(f"Decay error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/field/repair")
    async def repair_field():
        """Trigger field repair."""
        try:
            _field_manager.repair()
            return {"status": "repaired", "field": _field_manager.state.to_dict()}
        except Exception as e:
            logger.error(f"Repair error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Coherence Endpoints ───────────────────────────────────────────────

    @app.get("/resonance/coherence")
    async def get_coherence():
        """Get current coherence snapshot."""
        try:
            snap = _coherence_engine.measure(_signal_field)
            if snap is None:
                return {"coherence": None, "message": "No signals in field"}
            return {"coherence": snap.to_dict()}
        except Exception as e:
            logger.error(f"Coherence error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/coherence/trend")
    async def get_coherence_trend(points: int = Query(10, ge=1, le=100)):
        """Get coherence trend over recent history."""
        try:
            trend = _coherence_engine.get_trend(points)
            return {"trend": [t.to_dict() for t in trend]}
        except Exception as e:
            logger.error(f"Coherence trend error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/observer")
    async def register_observer(request: ObserverRegistration):
        """Register an observer in the coherence engine."""
        try:
            _coherence_engine.update_observer(
                request.observer_id, request.phase, request.coherence
            )
            _field_manager.entrain_observer(request.observer_id)
            return {"status": "registered", "observer_id": request.observer_id}
        except Exception as e:
            logger.error(f"Observer registration error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/resonance/observer/{observer_id}")
    async def remove_observer(observer_id: str):
        """Remove an observer."""
        _coherence_engine.remove_observer(observer_id)
        _field_manager.remove_observer(observer_id)
        return {"status": "removed", "observer_id": observer_id}

    # ── Boundary Endpoints ────────────────────────────────────────────────

    @app.get("/resonance/boundaries")
    async def get_boundaries(
        critical_only: bool = Query(False),
    ):
        """Get all detected boundaries."""
        try:
            if critical_only:
                boundaries = _boundary_mapper.get_critical_boundaries()
            else:
                boundaries = list(_boundary_mapper.boundaries.values())
            return {"boundaries": [b.to_dict() for b in boundaries], "count": len(boundaries)}
        except Exception as e:
            logger.error(f"Boundary query error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/boundaries/detect")
    async def detect_boundaries():
        """Run boundary detection on current field."""
        try:
            new_boundaries = _boundary_mapper.detect_boundaries(_signal_field)
            zones = _boundary_mapper.map_pressure_zones()
            return {
                "new_boundaries": len(new_boundaries),
                "total_boundaries": len(_boundary_mapper.boundaries),
                "pressure_zones": len(zones),
            }
        except Exception as e:
            logger.error(f"Boundary detection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/pressure-zones")
    async def get_pressure_zones():
        """Get all pressure zones."""
        try:
            zones = list(_boundary_mapper.pressure_zones.values())
            return {"zones": [z.to_dict() for z in zones], "count": len(zones)}
        except Exception as e:
            logger.error(f"Pressure zone error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Resonance Engine Endpoints ────────────────────────────────────────

    @app.post("/resonance/score")
    async def score_resonance(request: ScoreResonanceRequest):
        """Score resonance between an observer and a signal."""
        try:
            signal = SignalPacket(
                source=request.signal_source,
                amplitude=request.amplitude,
                coherence=request.coherence,
                phase=request.phase,
                entropy_delta=request.entropy_delta,
            )
            score = _resonance_engine.score_resonance(
                request.observer_id, request.observer_phase,
                request.observer_coherence, signal,
            )
            return {"score": score.to_dict()}
        except Exception as e:
            logger.error(f"Resonance scoring error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/constraint")
    async def add_constraint(request: AddConstraintRequest):
        """Add a constraint to the resonance field."""
        try:
            constraint = Constraint(
                constraint_id=request.constraint_id,
                constraint_type=request.constraint_type,
                weight=request.weight,
                phase=request.phase,
                coherence=request.coherence,
            )
            _resonance_engine.add_constraint(constraint)
            return {"status": "added", "constraint_id": request.constraint_id}
        except Exception as e:
            logger.error(f"Constraint error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/constraints")
    async def get_constraints():
        """Get all constraints."""
        try:
            constraints = list(_resonance_engine._constraints.values())
            return {
                "constraints": [
                    {
                        "constraint_id": c.constraint_id,
                        "constraint_type": c.constraint_type,
                        "weight": c.weight,
                        "phase": c.phase,
                        "coherence": c.coherence,
                        "satisfied": c.satisfied,
                    }
                    for c in constraints
                ],
                "harmonization": _resonance_engine.harmonize_constraints(),
            }
        except Exception as e:
            logger.error(f"Constraints error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/action-path")
    async def get_action_path():
        """Get the current action path from constraint harmonization."""
        try:
            path = _resonance_engine.get_action_path()
            return {"action_path": path}
        except Exception as e:
            logger.error(f"Action path error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Pressure Tracker Endpoints ────────────────────────────────────────

    @app.post("/resonance/scan")
    async def scan_pressure():
        """Scan field for pressure anomalies."""
        try:
            alerts = _pressure_tracker.scan(_signal_field, _boundary_mapper)
            return {
                "alerts": [a.to_dict() for a in alerts],
                "alert_count": len(alerts),
            }
        except Exception as e:
            logger.error(f"Pressure scan error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/alerts")
    async def get_alerts(
        active_only: bool = Query(True),
    ):
        """Get pressure alerts."""
        try:
            if active_only:
                alerts = _pressure_tracker.get_active_alerts()
            else:
                alerts = _pressure_tracker._alerts
            return {"alerts": [a.to_dict() for a in alerts], "count": len(alerts)}
        except Exception as e:
            logger.error(f"Alerts error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/resonance/alerts/{alert_id}/resolve")
    async def resolve_alert(alert_id: str):
        """Resolve a pressure alert."""
        try:
            for alert in _pressure_tracker._alerts:
                if alert.alert_id == alert_id:
                    alert.resolve()
                    return {"status": "resolved", "alert_id": alert_id}
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Alert resolve error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/resonance/stats")
    async def get_stats():
        """Get comprehensive resonance subsystem stats."""
        try:
            return {
                "signals": _signal_field.stats(),
                "field": _field_manager.stats(),
                "resonance": _resonance_engine.stats(),
                "pressure": _pressure_tracker.stats(),
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("Resonance API endpoints registered (20 endpoints)")
