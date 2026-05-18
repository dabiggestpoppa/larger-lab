"""
V3 Phase 6 — Projection Engine
Transforms events into field vectors, topology influence, resonance pressure.

NOT linear dispatch — dynamic projection like wave interference.
Events are projected into the bounded coherent structures of the field.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from resonance import SignalPacket, SignalField


@dataclass
class FieldVector:
    """A vector representing an event's projection into the field."""
    vector_id: str
    source_event: str
    amplitude: float = 0.5
    phase: float = 0.0
    coherence: float = 0.5
    topology_influence: float = 0.0   # How much this affects topology
    resonance_pressure: float = 0.0   # Pressure on observer resonance
    timestamp: float = field(default_factory=time.time)

    @property
    def intensity(self) -> float:
        return self.amplitude * self.coherence

    def interfere(self, other: FieldVector) -> float:
        """Calculate interference with another vector. Positive = constructive, negative = destructive."""
        phase_diff = abs(self.phase - other.phase)
        return self.amplitude * other.amplitude * math.cos(phase_diff)


class ProjectionEngine:
    """
    Projects events into the cognitive field as vectors.
    
    Instead of linear dispatch (event → handler), events are projected
    dynamically into the field, creating interference patterns that
    naturally route signals to the most resonant observers.
    """

    def __init__(self):
        self._vectors: list[FieldVector] = []
        self._max_vectors = 10000

    def project_event(
        self, event_type: str, source: str, amplitude: float = 0.5,
        coherence: float = 0.5, phase: float = 0.0,
    ) -> FieldVector:
        """
        Project an event into the field as a vector.
        
        The vector's properties determine how it interacts with:
        - Other vectors (interference)
        - Observers (resonance)
        - Topology (structural influence)
        """
        vec = FieldVector(
            vector_id=f"vec_{int(time.time())}_{hash(event_type) % 1000}",
            source_event=event_type,
            amplitude=amplitude,
            phase=phase,
            coherence=coherence,
            topology_influence=amplitude * 0.3,
            resonance_pressure=(1.0 - coherence) * amplitude,
        )

        self._vectors.append(vec)
        if len(self._vectors) > self._max_vectors:
            self._vectors = self._vectors[-self._max_vectors:]

        return vec

    def project_signal(self, signal: SignalPacket) -> FieldVector:
        """Project a SignalPacket into the field."""
        return self.project_event(
            event_type=signal.source,
            source=signal.source,
            amplitude=signal.amplitude,
            coherence=signal.coherence,
            phase=signal.phase,
        )

    def calculate_interference(self, vector_id: str) -> float:
        """Calculate total interference for a vector with all other vectors."""
        target = None
        for v in self._vectors:
            if v.vector_id == vector_id:
                target = v
                break

        if not target:
            return 0.0

        total = 0.0
        for v in self._vectors:
            if v.vector_id != vector_id:
                total += target.interfere(v)

        return total

    def get_field_state(self) -> dict:
        """Get the current state of the projected field."""
        if not self._vectors:
            return {"total_vectors": 0, "avg_amplitude": 0.0, "avg_coherence": 0.0}

        recent = self._vectors[-100:]  # Last 100 vectors
        return {
            "total_vectors": len(self._vectors),
            "recent_vectors": len(recent),
            "avg_amplitude": round(sum(v.amplitude for v in recent) / len(recent), 4),
            "avg_coherence": round(sum(v.coherence for v in recent) / len(recent), 4),
            "avg_pressure": round(sum(v.resonance_pressure for v in recent) / len(recent), 4),
        }

    def decay(self, factor: float = 0.9) -> None:
        """Decay all vector amplitudes."""
        for v in self._vectors:
            v.amplitude *= factor
        self._vectors = [v for v in self._vectors if v.amplitude >= 0.01]

    @property
    def stats(self) -> dict:
        return self.get_field_state()
