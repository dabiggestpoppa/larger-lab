"""
O-6: Runtime Inspector — Live Operational Conditions
====================================================

Inspect live operational conditions and telemetry.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("oce.substrate.runtime_inspector")


class RuntimeInspector:
    """
    Inspect live operational conditions.
    
    Tracks:
    - System load
    - Memory pressure
    - GPU state
    - Disk state
    - Runtime bottlenecks
    - Orchestration pressure
    """
    
    _instance: Optional["RuntimeInspector"] = None
    
    def __init__(self):
        self._metrics_history: List[Dict[str, Any]] = []
    
    def inspect(self) -> Dict[str, Any]:
        """Get current runtime telemetry."""
        import psutil
        
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_load": {
                "cpu": psutil.cpu_percent(interval=0.1),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage("/")._asdict(),
                "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0],
            },
            "bottlenecks": self._detect_bottlenecks(),
            "orchestration_pressure": self._calculate_orchestration_pressure(),
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    def _detect_bottlenecks(self) -> List[str]:
        """Detect runtime bottlenecks."""
        import psutil
        
        bottlenecks = []
        
        if psutil.cpu_percent() > 80:
            bottlenecks.append("high_cpu")
        
        if psutil.virtual_memory().percent > 80:
            bottlenecks.append("high_memory")
        
        if psutil.disk_usage("/").percent > 90:
            bottlenecks.append("low_disk")
        
        return bottlenecks
    
    def _calculate_orchestration_pressure(self) -> float:
        """Calculate orchestration pressure metric."""
        # Would integrate with spawn registry
        return 0.0
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metrics history."""
        return self._metrics_history[-limit:]


def get_runtime_inspector() -> RuntimeInspector:
    """Get singleton RuntimeInspector instance."""
    if RuntimeInspector._instance is None:
        RuntimeInspector._instance = RuntimeInspector()
    return RuntimeInspector._instance