#!/usr/bin/env python3
"""
🔴 PM — Resonance Debug CLI
Debug tools for V3 Resonant Signal Substrate (RSS)
"""
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from oce.backend.dspy_resonance import (
    SignalPacket,
    SignalPhase,
    CoherenceMetrics,
    ResonanceOptimizer,
    SignalRouter,
    FieldStateManager,
)


def cmd_score(signal_id: str, amplitude: float, coherence: float, phase: str, entropy: float):
    """Score a signal's resonance."""
    phase_enum = SignalPhase(phase.lower())
    signal = SignalPacket(signal_id, "cli", amplitude, coherence, phase_enum, entropy)
    metrics = CoherenceMetrics(0.8, 0.1, 0.7, 0.2, 0.1, 0.9)
    optimizer = ResonanceOptimizer()
    score = optimizer.score_resonance(signal, metrics)
    print(f"Signal: {signal_id}")
    print(f"  Amplitude: {amplitude}")
    print(f"  Coherence: {coherence}")
    print(f"  Phase: {phase}")
    print(f"  Resonance Score: {score:.4f}")


def cmd_metrics(phase_align: float, entropy_grad: float, density: float, tension: float, drift: float, stability: float):
    """Compute coherence metrics."""
    metrics = CoherenceMetrics(phase_align, entropy_grad, density, tension, drift, stability)
    print(f"Coherence Metrics:")
    print(f"  Phase Alignment: {metrics.phase_alignment:.4f}")
    print(f"  Entropy Gradient: {metrics.entropy_gradient:.4f}")
    print(f"  Resonance Density: {metrics.resonance_density:.4f}")
    print(f"  Field Tension: {metrics.field_tension:.4f}")
    print(f"  Manifold Drift: {metrics.manifold_drift:.4f}")
    print(f"  Attractor Stability: {metrics.attractor_stability:.4f}")
    print(f"  Overall Coherence: {metrics.overall_coherence:.4f}")
    print(f"  Performance Index: {metrics.performance_index:.4f}")


def cmd_field(field_id: str, capacity: int):
    """Create and inspect a field state manager."""
    fsm = FieldStateManager(field_id, capacity)
    print(f"Field: {field_id}")
    print(f"  Capacity: {capacity}")
    print(f"  Current Signals: {len(fsm.signals)}")


def cmd_test():
    """Run quick resonance tests."""
    # Test SignalPacket
    s = SignalPacket("test-001", "cli", 0.8, 0.9, SignalPhase.COHERENCE, 0.1)
    assert abs(s.resonance_score - 0.72) < 0.001
    assert s.is_viable is True
    
    # Test CoherenceMetrics
    m = CoherenceMetrics(1.0, 0.0, 1.0, 0.0, 0.0, 1.0)
    assert m.overall_coherence == 1.0
    
    # Test ResonanceOptimizer
    optimizer = ResonanceOptimizer()
    score = optimizer.score_resonance(s, m)
    assert 0.0 <= score <= 1.0
    
    print("✅ All quick tests passed")


def print_usage():
    print("Resonance Debug CLI")
    print("Usage:")
    print("  score <id> <amplitude> <coherence> <phase> <entropy>  - Score a signal")
    print("  metrics <phase_align> <entropy_grad> <density> <tension> <drift> <stability>  - Compute metrics")
    print("  field <id> <capacity>  - Create field state manager")
    print("  test  - Run quick tests")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    cmd = sys.argv[1]
    
    if cmd == "score" and len(sys.argv) == 7:
        cmd_score(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], float(sys.argv[6]))
    elif cmd == "metrics" and len(sys.argv) == 8:
        cmd_metrics(float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), 
                   float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]))
    elif cmd == "field" and len(sys.argv) == 4:
        cmd_field(sys.argv[2], int(sys.argv[3]))
    elif cmd == "test":
        cmd_test()
    else:
        print_usage()


if __name__ == "__main__":
    main()