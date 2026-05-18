"""
V3 Phase 9 — Performance Benchmarks
Baseline performance metrics for the V3 cognitive field system.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    benchmark_id: str
    name: str
    value: float
    unit: str = ""
    baseline: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def improvement_pct(self) -> float:
        if self.baseline == 0:
            return 0.0
        return round((self.value - self.baseline) / self.baseline * 100, 2)

    @property
    def meets_baseline(self) -> bool:
        return self.value >= self.baseline if self.baseline > 0 else True


@dataclass
class BenchmarkSuite:
    """A collection of related benchmarks."""
    suite_id: str
    name: str
    description: str = ""
    results: list = field(default_factory=list)


class PerformanceBenchmarks:
    """
    Baseline performance metrics for V3 system.
    
    Tracks:
    - Field coherence latency
    - Response time
    - Repair latency
    - Sync efficiency
    - Memory usage
    - Throughput
    """

    def __init__(self):
        self._results: list[BenchmarkResult] = []
        self._suites: dict[str, BenchmarkSuite] = {}
        self._baselines: dict[str, float] = {}

    def set_baseline(self, name: str, value: float) -> None:
        """Set a baseline value for a benchmark."""
        self._baselines[name] = value

    def run_benchmark(self, name: str, value: float, unit: str = "") -> BenchmarkResult:
        """Record a benchmark result."""
        baseline = self._baselines.get(name, 0.0)
        result = BenchmarkResult(
            benchmark_id=f"bench_{int(time.time() * 1000)}",
            name=name, value=value, unit=unit,
            baseline=baseline,
        )
        self._results.append(result)
        return result

    def get_latest_result(self, name: str) -> Optional[BenchmarkResult]:
        """Get the most recent result for a benchmark."""
        for r in reversed(self._results):
            if r.name == name:
                return r
        return None

    def get_results_by_name(self, name: str) -> list[BenchmarkResult]:
        """Get all results for a benchmark name."""
        return [r for r in self._results if r.name == name]

    def create_suite(self, name: str, description: str = "") -> BenchmarkSuite:
        """Create a benchmark suite."""
        suite = BenchmarkSuite(
            suite_id=f"suite_{len(self._suites)}",
            name=name, description=description,
        )
        self._suites[suite.suite_id] = suite
        return suite

    def add_to_suite(self, suite_id: str, result: BenchmarkResult) -> bool:
        """Add a result to a suite."""
        suite = self._suites.get(suite_id)
        if suite is None:
            return False
        suite.results.append(result)
        return True

    def compare_to_baseline(self, name: str) -> Optional[dict]:
        """Compare latest result to baseline."""
        result = self.get_latest_result(name)
        if result is None:
            return None
        return {
            "name": name,
            "current": result.value,
            "baseline": result.baseline,
            "improvement_pct": result.improvement_pct,
            "meets_baseline": result.meets_baseline,
        }

    def get_all_comparisons(self) -> list[dict]:
        """Compare all benchmarks to their baselines."""
        names = set(r.name for r in self._results)
        return [
            self.compare_to_baseline(name)
            for name in names
            if self.compare_to_baseline(name) is not None
        ]

    @property
    def stats(self) -> dict:
        if not self._results:
            return {"total_benchmarks": 0, "unique_names": 0}

        names = set(r.name for r in self._results)
        meeting = sum(
            1 for n in names
            if (r := self.get_latest_result(n)) and r.meets_baseline
        )
        return {
            "total_benchmarks": len(self._results),
            "unique_names": len(names),
            "meeting_baseline": meeting,
            "below_baseline": len(names) - meeting,
            "total_suites": len(self._suites),
        }
