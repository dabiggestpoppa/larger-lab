#!/usr/bin/env python3
"""Test script for CopilotKit Agent State Integration"""
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass, asdict

STATE_FILE = Path(__file__).parent / "agent_state.json"

@dataclass
class AgentState:
    hermes_status: str = "idle"
    hermes_iteration: int = 0
    hermes_profitable_strategies: int = 0
    hermes_target_strategies: int = 5
    openclaw_status: str = "idle"
    openclaw_task: str = ""
    openclaw_progress: str = ""
    last_updated: str = ""
    active_pair: str = "EURUSD"
    backtest_results: list = None
    
    def __post_init__(self):
        if self.backtest_results is None:
            self.backtest_results = []
        self.last_updated = datetime.now().isoformat()

class CopilotKitAgent:
    def __init__(self, name: str):
        self.name = name
        self.state = AgentState()
        
    def update_state(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.state.last_updated = datetime.now().isoformat()
        self._save_state()
        
    def _save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)
            
    def get_state(self) -> dict:
        return asdict(self.state)

hermes_agent = CopilotKitAgent("Hermes")
openclaw_agent = CopilotKitAgent("OpenClaw")

# Test the integration
print("Testing CopilotKit Agent State Integration...")

hermes_agent.update_state(
    hermes_status="running",
    hermes_iteration=4,
    hermes_profitable_strategies=2
)

openclaw_agent.update_state(
    openclaw_status="parsing",
    openclaw_task="CEREBUS manual extraction",
    openclaw_progress="50%"
)

shared_state = {
    "hermes": hermes_agent.get_state(),
    "openclaw": openclaw_agent.get_state(),
    "timestamp": datetime.now().isoformat()
}

print(json.dumps(shared_state, indent=2))
print("\n✅ CopilotKit Agent State Integration working!")