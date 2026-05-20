"""
Phase 11.2 — Chaos Engine
Injects failures to test system resilience and recovery.
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


class ChaosEngine:
    """
    Injects controlled failures into the system.
    Tests recovery, continuity, and stability under stress.
    """
    
    def __init__(self):
        self.active_events: List[ChaosEvent] = []
        self.event_history: List[ChaosEvent] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def inject_chaos(self, chaos_type: ChaosType, target: str, 
                     duration: float = 60, severity: float = 0.5) -> ChaosEvent:
        """Inject a chaos event into the system."""
        event = ChaosEvent(
            event_id=f"chaos_{int(time.time()*1000)}",
            chaos_type=chaos_type,
            timestamp=time.time(),
            duration_seconds=duration,
            target=target,
            severity=severity
        )
        
        self.active_events.append(event)
        print(f"[CHAOS] Injected {chaos_type.value} on {target} for {duration}s")
        
        # Schedule recovery
        def recover():
            time.sleep(duration)
            event.recovered = True
            self.active_events.remove(event)
            self.event_history.append(event)
            print(f"[CHAOS] Recovered from {chaos_type.value} on {target}")
            
        thread = threading.Thread(target=recover, daemon=True)
        thread.start()
        
        return event
    
    def observer_kill(self, observer_id: str, severity: float = 1.0):
        """Kill an observer to test recovery."""
        return self.inject_chaos(ChaosType.OBSERVER_KILL, observer_id, 
                                   duration=30, severity=severity)
    
    def event_flood(self, target: str = "event_fabric", rate_multiplier: float = 10):
        """Flood event fabric with events."""
        return self.inject_chaos(ChaosType.EVENT_FLOOD, target,
                                  duration=120, severity=rate_multiplier/10)
    
    def memory_corrupt(self, memory_id: str, corruption_rate: float = 0.1):
        """Inject false/conflicting memories."""
        return self.inject_chaos(ChaosType.MEMORY_CORRUPT, memory_id,
                                  duration=60, severity=corruption_rate)
    
    def router_failure(self, router_id: str):
        """Simulate router failure."""
        return self.inject_chaos(ChaosType.ROUTER_FAILURE, router_id,
                                  duration=45, severity=1.0)
    
    def websocket_loss(self, connection_id: str):
        """Simulate websocket disconnection."""
        return self.inject_chaos(ChaosType.WEBSOCKET_LOSS, connection_id,
                                  duration=30, severity=1.0)
    
    def token_starve(self, observer_id: str, reduction: float = 0.9):
        """Starve observer of tokens."""
        return self.inject_chaos(ChaosType.TOKEN_STARVE, observer_id,
                                  duration=180, severity=reduction)
    
    def recursive_storm(self, target: str = "orchestration"):
        """Trigger recursive delegation storm."""
        return self.inject_chaos(ChaosType.RECURSIVE_STORM, target,
                                  duration=60, severity=0.8)
    
    def twin_desync(self, twin_id: str = "oc2_oc3"):
        """Desync twin claws."""
        return self.inject_chaos(ChaosType.TWIN_DESYNC, twin_id,
                                  duration=120, severity=1.0)
    
    def get_active_chaos(self) -> List[Dict]:
        """Get list of currently active chaos events."""
        return [
            {
                "event_id": e.event_id,
                "type": e.chaos_type.value,
                "target": e.target,
                "severity": e.severity,
                "remaining": e.duration_seconds - (time.time() - e.timestamp)
            }
            for e in self.active_events
        ]
    
    def run_chaos_scenario(self, scenario_name: str) -> Dict:
        """Run a predefined chaos scenario."""
        scenarios = {
            "observer_death": [
                lambda: self.observer_kill("trading_observer"),
                lambda: self.observer_kill("repair_observer"),
            ],
            "event_flood": [
                lambda: self.event_flood("event_fabric", 20),
            ],
            "memory_poison": [
                lambda: self.memory_corrupt("memory_bank", 0.3),
            ],
            "full_chaos": [
                lambda: self.observer_kill("planner_observer"),
                lambda: self.event_flood("event_fabric", 15),
                lambda: self.memory_corrupt("structural_memory", 0.2),
                lambda: self.websocket_loss("hermes_mcp"),
            ]
        }
        
        scenario = scenarios.get(scenario_name, [])
        results = []
        
        for injection in scenario:
            event = injection()
            results.append(event.event_id)
            time.sleep(5)  # Stagger injections
            
        return {
            "scenario": scenario_name,
            "events_injected": len(results),
            "event_ids": results
        }


if __name__ == "__main__":
    engine = ChaosEngine()
    
    # Run a quick test
    print("Running observer death scenario...")
    result = engine.run_chaos_scenario("observer_death")
    print(f"Result: {result}")
    
    print("\nActive chaos:")
    for event in engine.get_active_chaos():
        print(f"  - {event}")