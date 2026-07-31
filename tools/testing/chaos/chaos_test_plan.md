# Phase 11.2 — Chaos Engine Test Plan

## Overview
After 16 hours of successful observer stress testing, preparing for Phase 11.2 Chaos Engine validation.

## Current Status
- **Phase 11.1**: 16 hours completed, all observers running strong
- **Next**: Phase 11.2 — Chaos Engine failure injection testing

## Chaos Scenarios

### 1. Observer Death Scenario
```python
engine.run_chaos_scenario("observer_death")
```
- Kill trading_observer
- Kill repair_observer
- Verify recovery within 30 seconds

### 2. Event Flood Scenario
```python
engine.run_chaos_scenario("event_flood")
```
- Flood event_fabric with 20x normal rate
- Duration: 120 seconds
- Monitor throughput degradation

### 3. Memory Poison Scenario
```python
engine.run_chaos_scenario("memory_poison")
```
- Inject false/conflicting memories
- Corruption rate: 30%
- Duration: 60 seconds

### 4. Full Chaos Scenario
```python
engine.run_chaos_scenario("full_chaos")
```
- Kill planner_observer
- Flood event_fabric (15x)
- Corrupt structural_memory (20%)
- Simulate websocket loss (hermes_mcp)

## Individual Chaos Types Available

| Type | Method | Duration | Purpose |
|------|--------|----------|---------|
| OBSERVER_KILL | `observer_kill(id)` | 30s | Test observer recovery |
| EVENT_FLOOD | `event_flood(target, rate)` | 120s | Test event fabric resilience |
| MEMORY_CORRUPT | `memory_corrupt(id, rate)` | 60s | Test memory integrity |
| ROUTER_FAILURE | `router_failure(id)` | 45s | Test routing recovery |
| WEBSOCKET_LOSS | `websocket_loss(id)` | 30s | Test connection recovery |
| TOKEN_STARVE | `token_starve(id, reduction)` | 180s | Test resource constraints |
| RECURSIVE_STORM | `recursive_storm(target)` | 60s | Test compute limits |
| TWIN_DESYNC | `twin_desync(id)` | 120s | Test twin synchronization |

## Test Execution Order

1. **Pre-test**: Capture baseline metrics
2. **Scenario 1**: observer_death (gentle start)
3. **Scenario 2**: event_flood (medium intensity)
4. **Scenario 3**: memory_poison (data integrity)
5. **Scenario 4**: full_chaos (maximum stress)
6. **Post-test**: Validate recovery and generate report

## Success Criteria
- All observers recover within 60 seconds
- No data loss during chaos events
- System returns to baseline within 5 minutes post-recovery
- Drift score remains < 0.1 throughout

## Running Tests
```bash
cd tools/testing/chaos
python chaos_engine.py
```

Or programmatically:
```python
from tools.testing.chaos.chaos_engine import ChaosEngine

engine = ChaosEngine()
result = engine.run_chaos_scenario("observer_death")
print(f"Events injected: {result['events_injected']}")
```