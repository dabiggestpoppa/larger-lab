"""
V3 Phase 1 — Boundary Mapper
Detects boundaries in the cognitive field and maps pressure zones.

Boundaries are regions where signal coherence changes sharply —
the edges of coherent structures in the field. Pressure accumulates
where signals conflict at boundaries.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from .signal_packet import SignalPacket, SignalField


@dataclass
class Boundary:
    """
    Represents a boundary in the cognitive field.
    
    A boundary is a region where signal properties change sharply.
    Boundaries can be:
    - coherence boundaries (where coherence drops sharply)
    - phase boundaries (where phase shifts abruptly)
    - entropy boundaries (where entropy accumulates)
    """
    boundary_id: str
    boundary_type: str  # "coherence", "phase", "entropy", "observer"
    position: float = 0.0       # Position in field (0-1 normalized)
    strength: float = 0.5       # Boundary strength (0-1)
    pressure: float = 0.0       # Accumulated pressure (0-1)
    signal_count: int = 0       # Number of signals touching this boundary
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    @property
    def is_critical(self) -> bool:
        """Boundary is critical if pressure > 0.7."""
        return self.pressure > 0.7

    @property
    def is_weakening(self) -> bool:
        """Boundary is weakening if strength < 0.2."""
        return self.strength < 0.2

    def add_pressure(self, amount: float) -> None:
        """Add pressure to this boundary."""
        self.pressure = min(1.0, self.pressure + amount)
        self.signal_count += 1
        self.last_updated = time.time()

    def decay(self, factor: float = 0.95) -> None:
        """Decay boundary pressure over time."""
        self.pressure *= factor
        self.strength *= factor

    def to_dict(self) -> dict:
        return {
            "boundary_id": self.boundary_id,
            "boundary_type": self.boundary_type,
            "position": round(self.position, 4),
            "strength": round(self.strength, 4),
            "pressure": round(self.pressure, 4),
            "signal_count": self.signal_count,
            "tags": self.tags,
            "is_critical": self.is_critical,
        }


@dataclass
class PressureZone:
    """
    A region of accumulated pressure in the field.
    Pressure zones form where multiple signals conflict at boundaries.
    """
    zone_id: str
    center: float = 0.0         # Center position (0-1)
    radius: float = 0.1         # Zone radius
    intensity: float = 0.0      # Pressure intensity (0-1)
    boundary_ids: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_critical(self) -> bool:
        return self.intensity > 0.8

    @property
    def is_resolved(self) -> bool:
        return self.intensity < 0.1

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "center": round(self.center, 4),
            "radius": round(self.radius, 4),
            "intensity": round(self.intensity, 4),
            "boundary_count": len(self.boundary_ids),
            "is_critical": self.is_critical,
        }


class BoundaryMapper:
    """
    Detects and tracks boundaries in the cognitive field.
    Maps pressure zones where boundaries interact.
    
    This is the BSP (Boundary Signal Processing) core:
    - Detects where coherence changes sharply
    - Maps pressure accumulation
    - Identifies critical boundaries needing repair
    """

    def __init__(self):
        self.boundaries: dict[str, Boundary] = {}
        self.pressure_zones: dict[str, PressureZone] = {}
        self._boundary_counter = 0
        self._zone_counter = 0

    def detect_boundaries(self, field: SignalField) -> list[Boundary]:
        """
        Scan the signal field for boundaries.
        
        Boundaries are detected where:
        1. Coherence changes sharply between adjacent signals
        2. Phase shifts abruptly
        3. Entropy accumulates in a region
        """
        signals = field.signals
        if len(signals) < 2:
            return []

        new_boundaries = []

        # Sort signals by phase for boundary detection
        sorted_signals = sorted(signals, key=lambda s: s.phase)

        for i in range(len(sorted_signals) - 1):
            s1 = sorted_signals[i]
            s2 = sorted_signals[i + 1]

            # Coherence boundary: sharp coherence change
            coherence_diff = abs(s1.coherence - s2.coherence)
            if coherence_diff > 0.3:
                b = self._get_or_create_boundary(
                    f"coh_{i}", "coherence",
                    position=(s1.phase + s2.phase) / 2,
                    strength=coherence_diff,
                )
                b.add_pressure(coherence_diff * s1.amplitude)
                new_boundaries.append(b)

            # Phase boundary: abrupt phase shift
            phase_diff = abs(s1.phase - s2.phase)
            if phase_diff > math.pi / 2:
                b = self._get_or_create_boundary(
                    f"phase_{i}", "phase",
                    position=(s1.phase + s2.phase) / 2,
                    strength=phase_diff / (2 * math.pi),
                )
                b.add_pressure(phase_diff / (2 * math.pi) * s1.amplitude)
                new_boundaries.append(b)

            # Entropy boundary: entropy accumulation
            if s1.entropy_delta > 0.3 and s2.entropy_delta > 0.3:
                b = self._get_or_create_boundary(
                    f"ent_{i}", "entropy",
                    position=(s1.phase + s2.phase) / 2,
                    strength=(s1.entropy_delta + s2.entropy_delta) / 2,
                )
                b.add_pressure((s1.entropy_delta + s2.entropy_delta) / 2)
                new_boundaries.append(b)

        return new_boundaries

    def map_pressure_zones(self) -> list[PressureZone]:
        """
        Identify pressure zones from boundary interactions.
        Pressure zones form where multiple boundaries are close together.
        """
        critical_boundaries = [b for b in self.boundaries.values() if b.pressure > 0.3]
        
        zones: list[PressureZone] = []
        used = set()

        for b1 in critical_boundaries:
            if b1.boundary_id in used:
                continue
            
            # Find nearby boundaries
            nearby = [b1]
            for b2 in critical_boundaries:
                if b2.boundary_id != b1.boundary_id and b2.boundary_id not in used:
                    if abs(b1.position - b2.position) < 0.3:
                        nearby.append(b2)
            
            if len(nearby) >= 2:
                zone_id = f"zone_{self._zone_counter}"
                self._zone_counter += 1
                
                center = sum(b.position for b in nearby) / len(nearby)
                max_dist = max(abs(b.position - center) for b in nearby)
                intensity = sum(b.pressure for b in nearby) / len(nearby)
                
                zone = PressureZone(
                    zone_id=zone_id,
                    center=center,
                    radius=max(max_dist, 0.1),
                    intensity=min(1.0, intensity),
                    boundary_ids=[b.boundary_id for b in nearby],
                )
                zones.append(zone)
                self.pressure_zones[zone_id] = zone
                used.update(b.boundary_id for b in nearby)

        return zones

    def _get_or_create_boundary(
        self, boundary_id: str, boundary_type: str,
        position: float, strength: float,
    ) -> Boundary:
        """Get existing boundary or create new one."""
        if boundary_id in self.boundaries:
            b = self.boundaries[boundary_id]
            b.strength = max(b.strength, strength)
            b.last_updated = time.time()
            return b
        
        self._boundary_counter += 1
        b = Boundary(
            boundary_id=boundary_id,
            boundary_type=boundary_type,
            position=position,
            strength=strength,
        )
        self.boundaries[boundary_id] = b
        return b

    def get_critical_boundaries(self) -> list[Boundary]:
        """Get all boundaries with critical pressure."""
        return [b for b in self.boundaries.values() if b.is_critical]

    def get_critical_zones(self) -> list[PressureZone]:
        """Get all critical pressure zones."""
        return [z for z in self.pressure_zones.values() if z.is_critical]

    def decay(self, factor: float = 0.95) -> None:
        """Decay all boundary pressures."""
        for b in self.boundaries.values():
            b.decay(factor)
        # Remove weak boundaries
        to_remove = [bid for bid, b in self.boundaries.items() if b.strength < 0.01]
        for bid in to_remove:
            del self.boundaries[bid]
        
        # Decay zones
        for z in self.pressure_zones.values():
            z.intensity *= factor
        to_remove_z = [zid for zid, z in self.pressure_zones.items() if z.is_resolved]
        for zid in to_remove_z:
            del self.pressure_zones[zid]

    def get_repair_targets(self) -> list[dict]:
        """
        Get boundaries that need repair, sorted by pressure (highest first).
        Used by the repair observer to prioritize fixes.
        """
        critical = self.get_critical_boundaries()
        return sorted(
            [b.to_dict() for b in critical],
            key=lambda x: x["pressure"],
            reverse=True,
        )

    @property
    def stats(self) -> dict:
        """Boundary mapper statistics."""
        return {
            "total_boundaries": len(self.boundaries),
            "critical_boundaries": len(self.get_critical_boundaries()),
            "total_zones": len(self.pressure_zones),
            "critical_zones": len(self.get_critical_zones()),
            "boundary_types": {
                btype: sum(1 for b in self.boundaries.values() if b.boundary_type == btype)
                for btype in set(b.boundary_type for b in self.boundaries.values())
            },
        }

    def __repr__(self) -> str:
        return (
            f"BoundaryMapper(boundaries={len(self.boundaries)}, "
            f"zones={len(self.pressure_zones)}, "
            f"critical={len(self.get_critical_boundaries())})"
        )
