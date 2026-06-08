"""
4_instrumentation.resource_orchestrator
========================================
Field resource management — CPU, memory, IO monitoring and allocation.

Tracks computational resources across all field modules with
real system metrics via psutil.

Thread-safe, production-ready.
"""

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional

import psutil
from pydantic import BaseModel, Field

logger = logging.getLogger("field.resource_orchestrator")


class ResourceAllocation(BaseModel):
    resource_name: str
    allocated: float = 0.0
    capacity: float = 100.0
    unit: str = "percent"


class ResourceStatus(BaseModel):
    name: str
    resource_type: str
    capacity: float
    allocated: float
    available: float
    utilization_pct: float
    unit: str
    is_overloaded: bool
    is_critical: bool
    last_check: str = ""


class ResourceOrchestratorConfig(BaseModel):
    enabled: bool = True
    check_interval_sec: float = 10.0
    overload_threshold_pct: float = 85.0
    critical_threshold_pct: float = 95.0


class ResourceOrchestratorModule:
    """Field resource orchestrator — manages and monitors system resources."""

    def __init__(self):
        self.config = ResourceOrchestratorConfig()
        self.running = False
        self._lock = Lock()
        self._resources: Dict[str, dict] = {}
        self._allocations: Dict[str, float] = defaultdict(float)
        self._history: List[Dict[str, Any]] = []
        self._check_count = 0

    def start(self) -> None:
        self.running = True
        # Auto-register system resources
        self._register_system_resources()
        logger.info("ResourceOrchestrator started")

    def stop(self) -> None:
        self.running = False
        logger.info("ResourceOrchestrator stopped")

    def _register_system_resources(self):
        """Auto-detect and register system resources."""
        mem = psutil.virtual_memory()
        self.register_resource("cpu", "compute", 100.0, "percent")
        self.register_resource("memory", "storage", float(mem.total / (1024 * 1024)), "MB")
        self.register_resource("disk_io", "io", 1000.0, "Mbps")

    def register_resource(self, name: str, resource_type: str, capacity: float, unit: str = "units") -> None:
        with self._lock:
            self._resources[name] = {
                "type": resource_type,
                "capacity": capacity,
                "unit": unit,
                "registered_at": time.time(),
            }
            logger.debug("Registered resource: %s (%s, %.1f %s)", name, resource_type, capacity, unit)

    def allocate(self, name: str, amount: float) -> bool:
        with self._lock:
            if name not in self._resources:
                logger.warning("Unknown resource: %s", name)
                return False
            available = self._resources[name]["capacity"] - self._allocations[name]
            if amount > available:
                logger.warning("Over-allocation for %s: requested %.1f, available %.1f", name, amount, available)
                return False
            self._allocations[name] += amount
            logger.debug("Allocated %.1f %s of %s", amount, self._resources[name]["unit"], name)
            return True

    def release(self, name: str, amount: float) -> None:
        with self._lock:
            self._allocations[name] = max(0, self._allocations.get(name, 0) - amount)
            logger.debug("Released %.1f from %s", amount, name)

    def get_utilization(self, name: str) -> Optional[ResourceStatus]:
        with self._lock:
            if name not in self._resources:
                return None
            res = self._resources[name]
            # Get real system metrics where available
            actual_used = self._get_actual_usage(name)
            allocated = self._allocations.get(name, 0)
            capacity = res["capacity"]
            util_pct = (actual_used / capacity * 100) if capacity > 0 else 0.0
            return ResourceStatus(
                name=name,
                resource_type=res["type"],
                capacity=capacity,
                allocated=allocated,
                available=capacity - actual_used,
                utilization_pct=round(util_pct, 2),
                unit=res["unit"],
                is_overloaded=util_pct >= self.config.overload_threshold_pct,
                is_critical=util_pct >= self.config.critical_threshold_pct,
                last_check=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

    def _get_actual_usage(self, name: str) -> float:
        """Get actual system usage via psutil."""
        try:
            if name == "cpu":
                return psutil.cpu_percent(interval=0.1)
            elif name == "memory":
                mem = psutil.virtual_memory()
                return float(mem.used / (1024 * 1024))
            elif name == "disk_io":
                disk = psutil.disk_io_counters()
                return float((disk.read_bytes + disk.write_bytes) / (1024 * 1024))
        except Exception:
            pass
        return self._allocations.get(name, 0.0)

    def get_all_utilization(self) -> List[ResourceStatus]:
        return [s for s in (self.get_utilization(n) for n in self._resources) if s is not None]

    def get_overloaded(self, threshold_pct: Optional[float] = None) -> List[ResourceStatus]:
        threshold = threshold_pct or self.config.overload_threshold_pct
        result = []
        for name in self._resources:
            status = self.get_utilization(name)
            if status and status.utilization_pct >= threshold:
                result.append(status)
        return result

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "resource_count": len(self._resources),
                "allocation_count": len(self._allocations),
                "check_count": self._check_count,
                "resources": {n: {"type": r["type"], "capacity": r["capacity"], "unit": r["unit"]}
                              for n, r in self._resources.items()},
            }
