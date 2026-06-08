"""
4.3 Adaptive Profiler — Sovereign Instrumentation
===================================================
Profiles field module performance and adapts sampling rate based on load.

When load is high → sample less frequently.
When low → sample more for accuracy.

Tracks per-module: call_count, total_time, avg, p95, p99.
"""

import logging
import threading
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.adaptive_profiler")


class ProfileEntry(BaseModel):
    module_name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    current_sample_rate: float = 1.0
    recent_durations: List[float] = Field(default_factory=list)


class AdaptiveProfilerConfig(BaseModel):
    """Configuration for AdaptiveProfiler."""
    enabled: bool = True
    base_sample_rate: float = 1.0
    min_sample_rate: float = 0.1
    max_sample_rate: float = 1.0
    window_size: int = 100


class AdaptiveProfilerModule:
    """Adaptive performance profiler for field modules."""

    def __init__(self):
        self.config = AdaptiveProfilerConfig()
        self.running = False
        self._lock = threading.Lock()
        self._profiles: Dict[str, ProfileEntry] = {}
        self._windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.window_size))
        self._call_counts: Dict[str, int] = defaultdict(int)

    def start(self) -> None:
        """Start the profiler."""
        self.running = True
        logger.info("AdaptiveProfiler started")

    def stop(self) -> None:
        """Stop the profiler."""
        self.running = False
        logger.info("AdaptiveProfiler stopped")

    def record_call(self, module_name: str, duration_ms: float) -> None:
        """Record a function call duration for a module.

        Args:
            module_name: Name of the module being profiled.
            duration_ms: Duration of the call in milliseconds.
        """
        if not self.config.enabled or not self.running:
            return

        with self._lock:
            self._call_counts[module_name] += 1

            # Adaptive sampling: decide whether to record this call
            sample_rate = self._compute_sample_rate(module_name)
            if module_name in self._profiles:
                self._profiles[module_name].current_sample_rate = sample_rate

            # Record with probability = sample_rate
            import random
            if random.random() > sample_rate:
                return

            window = self._windows[module_name]
            window.append(duration_ms)

            # Compute percentiles from window
            sorted_durations = sorted(window)
            n = len(sorted_durations)
            p95_idx = min(int(n * 0.95), n - 1)
            p99_idx = min(int(n * 0.99), n - 1)

            total = sum(sorted_durations)
            avg = total / n if n > 0 else 0.0

            if module_name not in self._profiles:
                self._profiles[module_name] = ProfileEntry(module_name=module_name)

            profile = self._profiles[module_name]
            profile.call_count = self._call_counts[module_name]
            profile.total_time_ms += duration_ms
            profile.avg_time_ms = round(avg, 4)
            profile.p95_time_ms = round(sorted_durations[p95_idx], 4)
            profile.p99_time_ms = round(sorted_durations[p99_idx], 4)
            profile.recent_durations = list(window)[-20:]

    def _compute_sample_rate(self, module_name: str) -> float:
        """Compute adaptive sample rate based on call frequency."""
        count = self._call_counts.get(module_name, 0)
        if count < 10:
            return self.config.max_sample_rate
        # Decay sample rate as call count grows
        import math
        rate = self.config.base_sample_rate / (1 + math.log10(max(count / 10, 1)))
        return max(self.config.min_sample_rate, min(self.config.max_sample_rate, rate))

    def get_profile(self, module_name: str) -> Optional[ProfileEntry]:
        """Get profile for a specific module."""
        with self._lock:
            return self._profiles.get(module_name)

    def get_all_profiles(self) -> Dict[str, ProfileEntry]:
        """Get all module profiles."""
        with self._lock:
            return dict(self._profiles)

    def get_hotspots(self, n: int = 10) -> List[ProfileEntry]:
        """Get the top N slowest modules by average time.

        Args:
            n: Number of hotspots to return.

        Returns:
            List of ProfileEntry sorted by avg_time_ms descending.
        """
        with self._lock:
            profiles = sorted(self._profiles.values(), key=lambda p: p.avg_time_ms, reverse=True)
            return profiles[:n]
