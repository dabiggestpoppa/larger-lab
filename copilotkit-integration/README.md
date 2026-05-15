# CopilotKit Integration for Hermes + OpenClaw

## Overview
Python-based CopilotKit agent state management for the larger-lab agent team.

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
    hermes_iteration=4,
    hermes_profitable_strategies=2
)

# Update OpenClaw state
openclaw_agent.update_state(
    openclaw_status="parsing",
    openclaw_task="CEREBUS manual extraction"
)

# Get shared state
state = get_shared_state()
```

## Test Results
✅ Agent state management working
✅ JSON persistence working
✅ Shared state accessible