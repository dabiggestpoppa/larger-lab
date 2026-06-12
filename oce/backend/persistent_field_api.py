"""
O-7 Persistent Field API Endpoints
===================================

Exposes persistent field functionality via FastAPI.
"""

from fastapi import FastAPI, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger("oce.persistent_field_api")


def register_persistent_field_endpoints(app: FastAPI) -> None:
    """Register all O-7 persistent field endpoints."""

    @app.get("/api/persistent-field/status")
    async def get_persistent_field_status():
        """Get overall persistent field status."""
        try:
            from core.persistent_field.persistent_runtime import PersistentRuntime
            rt = PersistentRuntime.get_instance()
            return rt.get_status()
        except Exception as e:
            logger.error(f"Persistent field status error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/heartbeat")
    async def get_heartbeat():
        """Get current runtime heartbeat."""
        try:
            from core.persistent_field.runtime_heartbeat import RuntimeHeartbeat
            hb = RuntimeHeartbeat()
            return hb.get_current()
        except Exception as e:
            logger.error(f"Persistent field heartbeat error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.post("/api/persistent-field/heartbeat")
    async def pulse_heartbeat():
        """Pulse the runtime heartbeat."""
        try:
            from core.persistent_field.runtime_heartbeat import RuntimeHeartbeat
            hb = RuntimeHeartbeat()
            return hb.pulse()
        except Exception as e:
            logger.error(f"Persistent field heartbeat pulse error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/dormant-state")
    async def get_dormant_state():
        """Get current dormant state."""
        try:
            from core.persistent_field.dormant_state_manager import DormantStateManager
            mgr = DormantStateManager()
            return mgr.get_summary()
        except Exception as e:
            logger.error(f"Persistent field dormant state error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.post("/api/persistent-field/dormant-state/transition")
    async def transition_dormant_state(state: str, reason: str = ""):
        """Transition dormant state."""
        try:
            from core.persistent_field.dormant_state_manager import DormantStateManager, DormantState
            mgr = DormantStateManager()
            new_state = DormantState(state)
            success = mgr.transition(new_state, reason)
            return {"success": success, "state": mgr.get_state()}
        except Exception as e:
            logger.error(f"Persistent field dormant transition error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/environment")
    async def get_environment():
        """Get environmental monitor status."""
        try:
            from core.persistent_field.environmental_monitor import EnvironmentalMonitor
            mon = EnvironmentalMonitor()
            return mon.check_environment()
        except Exception as e:
            logger.error(f"Persistent field environment error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/repair")
    async def get_repair_status():
        """Get autonomous repair status."""
        try:
            from core.persistent_field.autonomous_repair import AutonomousRepair
            repair = AutonomousRepair()
            return repair.get_status()
        except Exception as e:
            logger.error(f"Persistent field repair status error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.post("/api/persistent-field/repair")
    async def trigger_repair(action: str, target: str):
        """Trigger a repair action."""
        try:
            from core.persistent_field.autonomous_repair import AutonomousRepair, RepairAction
            repair = AutonomousRepair()
            result = repair.repair(RepairAction(action), target)
            return {
                "event_id": result.event_id,
                "action": result.action,
                "target": result.target,
                "status": result.status,
                "duration_seconds": result.duration_seconds,
            }
        except Exception as e:
            logger.error(f"Persistent field repair trigger error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/drift")
    async def get_drift_report():
        """Get operational drift report."""
        try:
            from core.persistent_field.operational_drift_detect import OperationalDriftDetector
            detector = OperationalDriftDetector()
            return detector.get_drift_report()
        except Exception as e:
            logger.error(f"Persistent field drift report error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/scheduler")
    async def get_scheduler_status():
        """Get persistent scheduler status."""
        try:
            from core.persistent_field.persistent_scheduler import PersistentScheduler
            scheduler = PersistentScheduler()
            return scheduler.get_status()
        except Exception as e:
            logger.error(f"Persistent field scheduler error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/continuity")
    async def get_continuity():
        """Get continuity preservation status."""
        try:
            from core.persistent_field.continuity_preserver import ContinuityPreserver
            preserver = ContinuityPreserver()
            return preserver.get_summary()
        except Exception as e:
            logger.error(f"Persistent field continuity error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.get("/api/persistent-field/recovery")
    async def get_recovery_status():
        """Get recovery persistence status."""
        try:
            from core.persistent_field.recovery_persistence import RecoveryPersistence
            recovery = RecoveryPersistence()
            return recovery.get_recovery_status()
        except Exception as e:
            logger.error(f"Persistent field recovery error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.post("/api/persistent-field/snapshot")
    async def create_snapshot(components: list[str], data: dict = None):
        """Create a recovery snapshot."""
        try:
            from core.persistent_field.recovery_persistence import RecoveryPersistence
            recovery = RecoveryPersistence()
            snapshot = recovery.create_snapshot(components, data or {})
            return {
                "snapshot_id": snapshot.snapshot_id,
                "timestamp": snapshot.timestamp,
                "components": snapshot.components,
            }
        except Exception as e:
            logger.error(f"Persistent field snapshot error: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    logger.info("O-7 Persistent Field endpoints registered")
