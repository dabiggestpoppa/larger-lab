"""
V3 Phase 7 — Multi-Scale Cognitive Fields
Simultaneous cognition across local/regional/global scales.
"""

from .local_fields import LocalObserverField, LocalFieldRegistry
from .regional_clusters import RegionalCluster, ClusterRegistry
from .global_attractor import GlobalAttractor, GlobalAttractorLayer, AttractorState
from .hierarchical_sync import SyncManager, SyncFrequency, SyncRecord
from .nested_repair import NestedRepairSystem, RepairEscalation, RepairRequest
from .scale_routing import ScaleAdaptiveRouter, ScaleLevel, RoutedMessage
from .entropy_containment import EntropyContainmentSystem, ContainmentBoundary

__all__ = [
    "LocalObserverField", "LocalFieldRegistry",
    "RegionalCluster", "ClusterRegistry",
    "GlobalAttractor", "GlobalAttractorLayer", "AttractorState",
    "SyncManager", "SyncFrequency", "SyncRecord",
    "NestedRepairSystem", "RepairEscalation", "RepairRequest",
    "ScaleAdaptiveRouter", "ScaleLevel", "RoutedMessage",
    "EntropyContainmentSystem", "ContainmentBoundary",
]
