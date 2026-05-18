"""
V3 Phase 6 — Meta-Consensus
Consensus about the consensus process itself.

The patches/observers agree on HOW they agree. This is the meta-level
that ensures the consensus process itself is coherent and trustworthy.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConsensusProcess:
    """A record of a consensus process."""
    process_id: str
    topic: str
    participants: list[str] = field(default_factory=list)
    outcome: str = ""
    agreement_level: float = 0.0   # 0-1, how much participants agreed
    duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


class MetaConsensus:
    """
    Consensus about the consensus process itself.
    
    Ensures that:
    - The consensus mechanism is itself coherent
    - Patches agree on how they agree
    - The process is observable and improvable
    """

    def __init__(self):
        self._processes: list[ConsensusProcess] = []

    def record_consensus(
        self, topic: str, participants: list[str],
        outcome: str, agreement_level: float, duration: float,
    ) -> ConsensusProcess:
        """Record a consensus process."""
        process = ConsensusProcess(
            process_id=f"consensus_{int(time.time())}",
            topic=topic,
            participants=participants,
            outcome=outcome,
            agreement_level=agreement_level,
            duration_seconds=duration,
        )
        self._processes.append(process)
        return process

    def evaluate_process(self, process_id: str) -> dict:
        """Evaluate the quality of a consensus process."""
        for p in self._processes:
            if p.process_id == process_id:
                quality = 1.0
                quality *= p.agreement_level
                quality *= min(1.0, len(p.participants) / 3.0)  # Need at least 3 participants
                quality *= min(1.0, p.duration_seconds / 60.0)  # Should take at least 1 min

                return {
                    "process_id": process_id,
                    "topic": p.topic,
                    "quality": round(quality, 4),
                    "agreement": p.agreement_level,
                    "participants": len(p.participants),
                    "is_healthy": quality > 0.5,
                }
        return {"status": "not_found"}

    def get_meta_analysis(self) -> dict:
        """Analyze the consensus process itself."""
        if not self._processes:
            return {"status": "no_data"}

        avg_agreement = sum(p.agreement_level for p in self._processes) / len(self._processes)
        avg_duration = sum(p.duration_seconds for p in self._processes) / len(self._processes)

        return {
            "total_processes": len(self._processes),
            "avg_agreement": round(avg_agreement, 4),
            "avg_duration_sec": round(avg_duration, 2),
            "healthy_processes": sum(1 for p in self._processes if p.agreement_level > 0.5),
        }

    @property
    def stats(self) -> dict:
        return self.get_meta_analysis()
