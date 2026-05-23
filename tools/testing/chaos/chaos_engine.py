"""
Phase 11.2 — Chaos Engine v2
Injects failures to test system resilience and recovery.
Amplification scales duration, severity, and breadth of chaos.
"""

import time
import random
import threading
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from datetime import datetime


class ChaosType(Enum):
    OBSERVER_KILL = "observer_kill"
    EVENT_FLOOD = "event_flood"
    MEMORY_CORRUPT = "memory_corrupt"
    ROUTER_FAILURE = "router_failure"
    WEBSOCKET_LOSS = "websocket_loss"
    TOKEN_STARVE = "token_starve"
    RECURSIVE_STORM = "recursive_storm"
    TWIN_DESYNC = "twin_desync"


@dataclass
class ChaosEvent:
    """A chaos injection event."""
    event_id: str
    chaos_type: ChaosType
    timestamp: float
    duration_seconds: float
    target: str
    severity: float  # 0.0 to 1.0
    recovered: bool = False
    amplification: float = 1.0


class ChaosEngine:
    """
    Injects controlled failures into the system.
    Tests recovery, continuity, and stability under stress.
    Amplification parameter scales all chaos parameters.
    """

    # Base durations (seconds) — these get multiplied by amplification
    BASE_DURATIONS = {
        ChaosType.OBSERVER_KILL: 30,
        ChaosType.EVENT_FLOOD: 120,
        ChaosType.MEMORY_CORRUPT: 60,
        ChaosType.ROUTER_FAILURE: 45,
        ChaosType.WEBSOCKET_LOSS: 30,
        ChaosType.TOKEN_STARVE: 180,
        ChaosType.RECURSIVE_STORM: 60,
        ChaosType.TWIN_DESYNC: 120,
    }

    # Base severities — these get multiplied by amplification (capped at 1.0)
    BASE_SEVERITIES = {
        ChaosType.OBSERVER_KILL: 0.5,
        ChaosType.EVENT_FLOOD: 0.5,
        ChaosType.MEMORY_CORRUPT: 0.3,
        ChaosType.ROUTER_FAILURE: 0.7,
        ChaosType.WEBSOCKET_LOSS: 0.5,
        ChaosType.TOKEN_STARVE: 0.5,
        ChaosType.RECURSIVE_STORM: 0.6,
        ChaosType.TWIN_DESYNC: 0.7,
    }

    def __init__(self):
        self.active_events: List[ChaosEvent] = []
        self.event_history: List[ChaosEvent] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _scaled_duration(self, chaos_type: ChaosType, amplification: float) -> float:
        """Scale duration by amplification. Higher amp = longer chaos."""
        base = self.BASE_DURATIONS.get(chaos_type, 60)
        scaled = base * amplification
        return min(scaled, 600)  # Cap at 10 minutes per event

    def _scaled_severity(self, chaos_type: ChaosType, amplification: float) -> float:
        """Scale severity by amplification, capped at 1.0."""
        base = self.BASE_SEVERITIES.get(chaos_type, 0.5)
        return min(base * amplification, 1.0)

    def inject_chaos(self, chaos_type: ChaosType, target: str,
                     duration: float = 60, severity: float = 0.5,
                     amplification: float = 1.0) -> ChaosEvent:
        """Inject a chaos event into the system."""
        event = ChaosEvent(
            event_id=f"chaos_{int(time.time()*1000)}",
            chaos_type=chaos_type,
            timestamp=time.time(),
            duration_seconds=duration,
            target=target,
            severity=severity,
            amplification=amplification
        )

        self.active_events.append(event)
        print(f"[CHAOS] Injected {chaos_type.value} on {target} for {duration:.0f}s (amp={amplification:.2f}x, sev={severity:.2f})")

        def recover():
            time.sleep(duration)
            event.recovered = True
            if event in self.active_events:
                self.active_events.remove(event)
            self.event_history.append(event)
            print(f"[CHAOS] Recovered from {chaos_type.value} on {target}")

        thread = threading.Thread(target=recover, daemon=True)
        thread.start()
        return event

    def observer_kill(self, observer_id: str, amplification: float = 1.0):
        """Kill an observer. Duration scales with amplification."""
        duration = self._scaled_duration(ChaosType.OBSERVER_KILL, amplification)
        severity = self._scaled_severity(ChaosType.OBSERVER_KILL, amplification)
        return self.inject_chaos(ChaosType.OBSERVER_KILL, observer_id,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def event_flood(self, target: str = "event_fabric", amplification: float = 1.0):
        """Flood event fabric. Duration and rate scale with amplification."""
        duration = self._scaled_duration(ChaosType.EVENT_FLOOD, amplification)
        rate_multiplier = 10 * amplification
        severity = min(rate_multiplier / 10, 1.0)
        return self.inject_chaos(ChaosType.EVENT_FLOOD, target,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def memory_corrupt(self, memory_id: str, amplification: float = 1.0):
        """Inject false/conflicting memories. Duration and corruption scale."""
        duration = self._scaled_duration(ChaosType.MEMORY_CORRUPT, amplification)
        corruption_rate = min(0.1 * amplification, 1.0)
        return self.inject_chaos(ChaosType.MEMORY_CORRUPT, memory_id,
                                   duration=duration, severity=corruption_rate,
                                   amplification=amplification)

    def router_failure(self, router_id: str, amplification: float = 1.0):
        """Simulate router failure. Duration scales with amplification."""
        duration = self._scaled_duration(ChaosType.ROUTER_FAILURE, amplification)
        severity = self._scaled_severity(ChaosType.ROUTER_FAILURE, amplification)
        return self.inject_chaos(ChaosType.ROUTER_FAILURE, router_id,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def websocket_loss(self, connection_id: str, amplification: float = 1.0):
        """Simulate websocket disconnection. Duration scales."""
        duration = self._scaled_duration(ChaosType.WEBSOCKET_LOSS, amplification)
        severity = self._scaled_severity(ChaosType.WEBSOCKET_LOSS, amplification)
        return self.inject_chaos(ChaosType.WEBSOCKET_LOSS, connection_id,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def token_starve(self, observer_id: str, amplification: float = 1.0):
        """Starve observer of tokens. Duration and severity scale."""
        duration = self._scaled_duration(ChaosType.TOKEN_STARVE, amplification)
        severity = self._scaled_severity(ChaosType.TOKEN_STARVE, amplification)
        return self.inject_chaos(ChaosType.TOKEN_STARVE, observer_id,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def recursive_storm(self, target: str = "orchestration", amplification: float = 1.0):
        """Trigger recursive delegation storm. Duration scales."""
        duration = self._scaled_duration(ChaosType.RECURSIVE_STORM, amplification)
        severity = self._scaled_severity(ChaosType.RECURSIVE_STORM, amplification)
        return self.inject_chaos(ChaosType.RECURSIVE_STORM, target,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def twin_desync(self, twin_id: str = "oc2_oc3", amplification: float = 1.0):
        """Desync twin claws. Duration scales."""
        duration = self._scaled_duration(ChaosType.TWIN_DESYNC, amplification)
        severity = self._scaled_severity(ChaosType.TWIN_DESYNC, amplification)
        return self.inject_chaos(ChaosType.TWIN_DESYNC, twin_id,
                                   duration=duration, severity=severity,
                                   amplification=amplification)

    def get_active_chaos(self) -> List[Dict]:
        """Get list of currently active chaos events."""
        return [
            {
                "event_id": e.event_id,
                "type": e.chaos_type.value,
                "target": e.target,
                "severity": e.severity,
                "amplification": e.amplification,
                "remaining": max(0, e.duration_seconds - (time.time() - e.timestamp))
            }
            for e in self.active_events
        ]

    def run_chaos_scenario(self, scenario_name: str, amplification: float = 1.0) -> Dict:
        """
        Run a predefined chaos scenario with amplification scaling.
        """
        scenarios = self._build_scenarios(amplification)
        scenario = scenarios.get(scenario_name, [])
        results = []

        for injection in scenario:
            event = injection()
            results.append(event.event_id)
            stagger = max(2, 5 / amplification)
            time.sleep(stagger)

        return {
            "scenario": scenario_name,
            "events_injected": len(results),
            "event_ids": results,
            "amplification": amplification
        }

    def _build_scenarios(self, amplification: float) -> Dict[str, List[Callable]]:
        """Build scenario injection lists, scaling with amplification."""

        # Observer death: more observers killed at higher amp
        observer_targets = ["trading_observer", "repair_observer"]
        if amplification >= 1.5:
            observer_targets.append("planner_observer")
        if amplification >= 2.0:
            observer_targets.append("memory_observer")
        if amplification >= 3.0:
            observer_targets.append("gateway_observer")
        if amplification >= 5.0:
            observer_targets.extend(["security_observer", "health_observer"])

        observer_death = [
            lambda t=t: self.observer_kill(t, amplification)
            for t in observer_targets
        ]

        # Event flood: more targets at higher amp
        event_flood = [lambda: self.event_flood("event_fabric", amplification)]
        if amplification >= 3.0:
            event_flood.append(lambda: self.event_flood("command_bus", amplification))
        if amplification >= 5.0:
            event_flood.append(lambda: self.event_flood("signal_router", amplification))

        # Memory poison: more memory targets at higher amp
        memory_targets = [("memory_bank", amplification)]
        if amplification >= 2.0:
            memory_targets.append(("structural_memory", amplification))
        if amplification >= 4.0:
            memory_targets.append(("cache_layer", amplification))
        if amplification >= 6.0:
            memory_targets.append(("persistent_store", amplification))

        memory_poison = [
            lambda t=t, a=a: self.memory_corrupt(t, a)
            for t, a in memory_targets
        ]

        # Full chaos: combines everything, scales with amp
        full_chaos = [
            lambda: self.observer_kill("planner_observer", amplification),
            lambda: self.event_flood("event_fabric", amplification),
            lambda: self.memory_corrupt("structural_memory", amplification),
            lambda: self.websocket_loss("hermes_mcp", amplification),
        ]
        if amplification >= 2.0:
            full_chaos.append(lambda: self.router_failure("main_router", amplification))
        if amplification >= 3.0:
            full_chaos.append(lambda: self.token_starve("trading_observer", amplification))
        if amplification >= 5.0:
            full_chaos.append(lambda: self.recursive_storm("orchestration", amplification))
        if amplification >= 8.0:
            full_chaos.append(lambda: self.twin_desync("oc2_oc3", amplification))

        # Extreme chaos: only at very high amplification
        extreme_chaos = []
        if amplification >= 10.0:
            extreme_chaos = [
                lambda: self.observer_kill("trading_observer", amplification),
                lambda: self.observer_kill("repair_observer", amplification),
                lambda: self.observer_kill("planner_observer", amplification),
                lambda: self.observer_kill("memory_observer", amplification),
                lambda: self.event_flood("event_fabric", amplification),
                lambda: self.event_flood("command_bus", amplification),
                lambda: self.memory_corrupt("memory_bank", amplification),
                lambda: self.memory_corrupt("structural_memory", amplification),
                lambda: self.memory_corrupt("cache_layer", amplification),
                lambda: self.websocket_loss("hermes_mcp", amplification),
                lambda: self.router_failure("main_router", amplification),
                lambda: self.token_starve("trading_observer", amplification),
                lambda: self.recursive_storm("orchestration", amplification),
                lambda: self.twin_desync("oc2_oc3", amplification),
            ]

        result = {
            "observer_death": observer_death,
            "event_flood": event_flood,
            "memory_poison": memory_poison,
            "full_chaos": full_chaos,
        }
        if extreme_chaos:
            result["extreme_chaos"] = extreme_chaos

        return result


if __name__ == "__main__":
    engine = ChaosEngine()

    print("=== Test at 1.0x amplification ===")
    result = engine.run_chaos_scenario("observer_death", amplification=1.0)
    print(f"Result: {result}")
    time.sleep(2)

    print("\n=== Test at 5.0x amplification ===")
    result = engine.run_chaos_scenario("full_chaos", amplification=5.0)
    print(f"Result: {result}")

    print("\nActive chaos:")
    for event in engine.get_active_chaos():
        print(f"  - {event}")
