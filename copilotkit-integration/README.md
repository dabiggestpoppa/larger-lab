# CopilotKit Integration for Hermes + OpenClaw

## Overview
Python-based CopilotKit agent state management for the larger-lab agent team.

## Current Status

### Hermes Autopilot v3
- **Status**: Running (iteration 17)
- **Goal**: 5 profitable strategies
- **Found**: 3 profitable strategies
  - P90_Base_Strategy: 0.11% return, 147 trades
  - RSI_Reversion: 0.33% return, 349 trades
  - Asian_Breakout: 0.06% return, 1270 trades

### Node.js Installation
- **Status**: ✅ Installed (v26.1.0)
- **npm**: 11.13.0

## Files
- `agent_state.py` - Core agent state management
- `run_test.py` - Test script
- `agent_state.json` - Current shared state

## Usage

```python
from agent_state import hermes_agent, openclaw_agent, get_shared_state

# Update Hermes state
hermes_agent.update_state(
    hermes_status="running",
    hermes_iteration=17,
    hermes_profitable_strategies=3
)
```