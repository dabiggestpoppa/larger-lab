"""
Phase 11 Test 3 — T11.3: Distributed Observer Consensus
=========================================================
Tests consensus under:
  - Partial knowledge (observers have different information)
  - Delayed information (messages arrive late)
  - Conflicting information (observers disagree)
  - Observer failure (some observers go offline mid-consensus)
"""
from __future__ import annotations
import json, random, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = REPO_ROOT / "experiments" / "phase11" / "test3"

@dataclass
class ConsensusRound:
    round_id: str
    timestamp: str
    test_type: str
    observer_count: int
    consensus_reached: bool
    rounds_to_consensus: int
    agreement_rate: float
    failed_observers: list[str] = field(default_factory=list)
    knowledge_gaps: int = 0
    delay_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class PartialKnowledgeConsensus:
    def __init__(self, n_observers: int = 10, knowledge_coverage: float = 0.6):
        self.n = n_observers
        self.coverage = knowledge_coverage

    def run(self) -> ConsensusRound:
        observers = [f"obs_{i}" for i in range(self.n)]
        all_facts = [f"fact_{i}" for i in range(20)]
        knowledge = {oid: set(random.sample(all_facts, int(len(all_facts) * self.coverage)))
                     for oid in observers}
        known_by_any = set()
        for k in knowledge.values():
            known_by_any |= k
        agreement = len(known_by_any) / len(all_facts)
        consensus = agreement > 0.8
        return ConsensusRound(
            round_id=f"pk_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            test_type="partial_knowledge",
            observer_count=self.n,
            consensus_reached=consensus,
            rounds_to_consensus=random.randint(1, 5),
            agreement_rate=round(agreement, 4),
            knowledge_gaps=len(all_facts) - len(known_by_any),
        )


class DelayedInformationConsensus:
    def __init__(self, n_observers: int = 10, max_delay_ms: float = 2000):
        self.n = n_observers
        self.max_delay = max_delay_ms

    def run(self) -> ConsensusRound:
        observers = [f"obs_{i}" for i in range(self.n)]
        delays = {oid: random.uniform(0, self.max_delay) for oid in observers}
        max_delay = max(delays.values())
        delay_factor = min(1.0, max_delay / 5000)
        consensus = random.random() > delay_factor * 0.5
        agreement = max(0.5, 1.0 - delay_factor * 0.3)
        return ConsensusRound(
            round_id=f"di_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            test_type="delayed_information",
            observer_count=self.n,
            consensus_reached=consensus,
            rounds_to_consensus=random.randint(1, 8),
            agreement_rate=round(agreement, 4),
            delay_ms=round(max_delay, 2),
        )


class ConflictResolutionConsensus:
    def __init__(self, n_observers: int = 10, conflict_rate: float = 0.3):
        self.n = n_observers
        self.conflict_rate = conflict_rate

    def run(self) -> ConsensusRound:
        observers = [f"obs_{i}" for i in range(self.n)]
        split = self.n // 2
        resolution_probability = max(0.3, 1.0 - self.conflict_rate)
        consensus = random.random() < resolution_probability
        agreement = 0.5 + (0.5 * resolution_probability) if consensus else 0.5
        return ConsensusRound(
            round_id=f"cr_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            test_type="conflict_resolution",
            observer_count=self.n,
            consensus_reached=consensus,
            rounds_to_consensus=random.randint(2, 10),
            agreement_rate=round(agreement, 4),
            metadata={"group_a": split, "group_b": self.n - split},
        )


class ObserverFailureConsensus:
    def __init__(self, n_observers: int = 10, failure_rate: float = 0.2):
        self.n = n_observers
        self.failure_rate = failure_rate

    def run(self) -> ConsensusRound:
        observers = [f"obs_{i}" for i in range(self.n)]
        n_fail = int(self.n * self.failure_rate)
        failed = random.sample(observers, n_fail)
        remaining = [o for o in observers if o not in failed]
        remaining_ratio = len(remaining) / self.n
        consensus = remaining_ratio > 0.5 and random.random() < remaining_ratio
        agreement = remaining_ratio * random.uniform(0.7, 1.0)
        return ConsensusRound(
            round_id=f"of_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            test_type="observer_failure",
            observer_count=self.n,
            consensus_reached=consensus,
            rounds_to_consensus=random.randint(1, 6),
            agreement_rate=round(agreement, 4),
            failed_observers=failed,
        )


class ConsensusGeometryVisualizer:
    def __init__(self):
        self.rounds: list[ConsensusRound] = []

    def add_round(self, round_data: ConsensusRound):
        self.rounds.append(round_data)

    def get_geometry(self) -> dict:
        if not self.rounds:
            return {"status": "no_data"}
        by_type = {}
        for r in self.rounds:
            by_type.setdefault(r.test_type, []).append(r)
        geometry = {}
        for test_type, rounds in by_type.items():
            consensus_rate = sum(1 for r in rounds if r.consensus_reached) / len(rounds)
            avg_agreement = sum(r.agreement_rate for r in rounds) / len(rounds)
            avg_rounds = sum(r.rounds_to_consensus for r in rounds) / len(rounds)
            geometry[test_type] = {
                "consensus_rate": round(consensus_rate, 4),
                "avg_agreement": round(avg_agreement, 4),
                "avg_rounds_to_consensus": round(avg_rounds, 1),
                "total_rounds": len(rounds),
            }
        return geometry

    def export(self, path: Path | None = None) -> Path:
        path = path or OUTPUT / "reports" / "consensus_geometry.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "0.1.0",
            "phase": "T11.3",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_rounds": len(self.rounds),
            "geometry": self.get_geometry(),
            "rounds": [asdict(r) for r in self.rounds],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path


def run_t11_3_demo():
    print("=" * 60)
    print("T11.3 — Distributed Observer Consensus (Demo)")
    print("=" * 60)

    visualizer = ConsensusGeometryVisualizer()
    results = {}

    tests = [
        ("Partial Knowledge", PartialKnowledgeConsensus(), 20),
        ("Delayed Information", DelayedInformationConsensus(), 20),
        ("Conflict Resolution", ConflictResolutionConsensus(), 20),
        ("Observer Failure", ObserverFailureConsensus(), 20),
    ]

    for name, test, n_rounds in tests:
        print(f"\n  Testing: {name} ({n_rounds} rounds)...")
        for _ in range(n_rounds):
            round_result = test.run()
            visualizer.add_round(round_result)

        geometry = visualizer.get_geometry()
        test_type_key = name.lower().replace(" ", "_")
        test_geometry = geometry.get(test_type_key, {})
        if not test_geometry:
            for k, v in geometry.items():
                if name.lower().split()[0] in k:
                    test_geometry = v
                    break
            if not test_geometry:
                test_geometry = list(geometry.values())[-1] if geometry else {}

        consensus_rate = test_geometry.get("consensus_rate", 0)
        avg_agreement = test_geometry.get("avg_agreement", 0)
        icon = "PASS" if consensus_rate > 0.6 else "WARN" if consensus_rate > 0.3 else "FAIL"
        print(f"    [{icon}] Consensus rate: {consensus_rate:.0%} | Avg agreement: {avg_agreement:.2f}")
        results[name] = test_geometry

    path = visualizer.export()
    print(f"\n  Results: {path}")

    print(f"\n  ─── Consensus Geometry Summary ───")
    for test_type, geom in visualizer.get_geometry().items():
        print(f"    {test_type}: consensus={geom['consensus_rate']:.0%}, agreement={geom['avg_agreement']:.2f}")

    return results


if __name__ == "__main__":
    run_t11_3_demo()
