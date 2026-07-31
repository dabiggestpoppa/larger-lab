"""
V3 Phase 1 — Signal Packet Ontology
Core signal object for the Resonant Signal Substrate (RSS).

Every event in the cognitive field is represented as a SignalPacket containing
energetic state, coherence state, phase state, and entropy potential.

This replaces raw event handling with field-state propagation.
"""

from __future__ import annotations
import uuid
import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SignalPacket:
    """
    Core signal object for the resonance substrate.
    
    Signals are NOT events. Events are discrete occurrences.
    Signals carry energetic, coherence, phase, and entropy state —
    they propagate through the field and interact with observers.
    """
    source: str
    amplitude: float = 0.5          # Signal strength (0.0 - 1.0)
    coherence: float = 0.5          # Coherence with field (0.0 - 1.0)
    phase: float = 0.0              # Phase angle (0 - 2π)
    entropy_delta: float = 0.0      # Entropy change caused by this signal
    boundary_tags: list[str] = field(default_factory=list)
    resonance_targets: list[str] = field(default_factory=list)
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate and clamp values."""
        self.amplitude = max(0.0, min(1.0, self.amplitude))
        self.coherence = max(0.0, min(1.0, self.coherence))
        self.phase = self.phase % (2 * math.pi)
        if self.entropy_delta < 0:
            self.entropy_delta = 0.0

    @property
    def is_resonant(self) -> bool:
        """A signal is resonant if coherence > 0.5 and amplitude > 0.3."""
        return self.coherence > 0.5 and self.amplitude > 0.3

    @property
    def is_entropic(self) -> bool:
        """A signal is entropic if it increases field entropy significantly."""
        return self.entropy_delta > 0.5

    @property
    def signal_pressure(self) -> float:
        """
        Signal pressure = amplitude × (1 - coherence) × entropy_delta.
        High pressure = strong signal that doesn't fit the field = instability.
        """
        return self.amplitude * (1.0 - self.coherence) * max(self.entropy_delta, 0.1)

    def resonance_score(self, observer_coherence: float, observer_phase: float) -> float:
        """
        Calculate resonance score between this signal and an observer.
        
        Score = coherence_alignment × amplitude × phase_proximity
        
        Args:
            observer_coherence: The observer's current coherence level
            observer_phase: The observer's current phase angle
            
        Returns:
            Resonance score (0.0 - 1.0)
        """
        coherence_alignment = 1.0 - abs(self.coherence - observer_coherence)
        phase_diff = abs(self.phase - observer_phase)
        phase_proximity = 1.0 - (phase_diff / (2 * math.pi))
        return coherence_alignment * self.amplitude * phase_proximity

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "signal_id": self.signal_id,
            "source": self.source,
            "amplitude": round(self.amplitude, 4),
            "coherence": round(self.coherence, 4),
            "phase": round(self.phase, 4),
            "entropy_delta": round(self.entropy_delta, 4),
            "boundary_tags": self.boundary_tags,
            "resonance_targets": self.resonance_targets,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SignalPacket:
        """Deserialize from dictionary."""
        return cls(
            source=data["source"],
            amplitude=data.get("amplitude", 0.5),
            coherence=data.get("coherence", 0.5),
            phase=data.get("phase", 0.0),
            entropy_delta=data.get("entropy_delta", 0.0),
            boundary_tags=data.get("boundary_tags", []),
            resonance_targets=data.get("resonance_targets", []),
            signal_id=data.get("signal_id", str(uuid.uuid4())[:8]),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def create_resonant(cls, source: str, target: str, amplitude: float = 0.8) -> SignalPacket:
        """Factory: Create a high-coherence resonant signal."""
        return cls(
            source=source,
            amplitude=amplitude,
            coherence=0.9,
            phase=0.0,
            entropy_delta=0.1,
            resonance_targets=[target],
            boundary_tags=["resonance"],
        )

    @classmethod
    def create_entropic(cls, source: str, entropy: float = 0.8) -> SignalPacket:
        """Factory: Create an entropy-increasing signal."""
        return cls(
            source=source,
            amplitude=0.7,
            coherence=0.2,
            entropy_delta=entropy,
            boundary_tags=["entropy"],
        )

    @classmethod
    def create_boundary(cls, source: str, boundary: str, amplitude: float = 0.6) -> SignalPacket:
        """Factory: Create a boundary pressure signal."""
        return cls(
            source=source,
            amplitude=amplitude,
            coherence=0.5,
            entropy_delta=0.3,
            boundary_tags=[boundary],
        )

    def __repr__(self) -> str:
        return (
            f"SignalPacket(id={self.signal_id}, src={self.source}, "
            f"amp={self.amplitude:.2f}, coh={self.coherence:.2f}, "
            f"phase={self.phase:.2f}, dS={self.entropy_delta:.2f})"
        )


class SignalField:
    """
    Container for signals propagating through the field.
    Manages signal lifecycle: injection, propagation, resonance, decay.
    """

    def __init__(self, max_size: int = 10000):
        self.signals: list[SignalPacket] = []
        self.max_size = max_size
        self._injection_count = 0
        self._resonance_count = 0

    def inject(self, signal: SignalPacket) -> None:
        """Inject a signal into the field."""
        self.signals.append(signal)
        self._injection_count += 1
        # Evict oldest if over capacity
        if len(self.signals) > self.max_size:
            self.signals = self.signals[-self.max_size:]

    def get_resonant_signals(self, min_coherence: float = 0.5) -> list[SignalPacket]:
        """Get all signals above coherence threshold."""
        return [s for s in self.signals if s.coherence >= min_coherence]

    def get_entropic_signals(self, min_entropy: float = 0.5) -> list[SignalPacket]:
        """Get all signals above entropy threshold."""
        return [s for s in self.signals if s.entropy_delta >= min_entropy]

    def get_signals_by_source(self, source: str) -> list[SignalPacket]:
        """Get all signals from a specific source."""
        return [s for s in self.signals if s.source == source]

    def get_signals_by_boundary(self, boundary: str) -> list[SignalPacket]:
        """Get all signals touching a specific boundary."""
        return [s for s in self.signals if boundary in s.boundary_tags]

    def get_pressure_map(self) -> dict[str, float]:
        """
        Calculate pressure per boundary tag.
        Pressure = sum of signal_pressure for all signals touching that boundary.
        """
        pressure: dict[str, float] = {}
        for signal in self.signals:
            for tag in signal.boundary_tags:
                pressure[tag] = pressure.get(tag, 0.0) + signal.signal_pressure
        return pressure

    def decay(self, factor: float = 0.9) -> None:
        """
        Decay all signal amplitudes. Simulates signal dissipation.
        Signals with amplitude < 0.01 are removed.
        """
        for signal in self.signals:
            signal.amplitude *= factor
        self.signals = [s for s in self.signals if s.amplitude >= 0.01]

    def clear(self) -> None:
        """Clear all signals from the field."""
        self.signals.clear()

    @property
    def field_coherence(self) -> float:
        """Average coherence of all signals in the field."""
        if not self.signals:
            return 1.0
        return sum(s.coherence for s in self.signals) / len(self.signals)

    @property
    def field_entropy(self) -> float:
        """Total entropy delta of all signals in the field."""
        return sum(s.entropy_delta for s in self.signals)

    @property
    def stats(self) -> dict:
        """Field statistics."""
        return {
            "total_signals": len(self.signals),
            "injections": self._injection_count,
            "resonances": self._resonance_count,
            "field_coherence": round(self.field_coherence, 4),
            "field_entropy": round(self.field_entropy, 4),
            "resonant_count": len(self.get_resonant_signals()),
            "entropic_count": len(self.get_entropic_signals()),
        }

    def __len__(self) -> int:
        return len(self.signals)

    def __repr__(self) -> str:
        return f"SignalField(signals={len(self.signals)}, coherence={self.field_coherence:.2f})"
