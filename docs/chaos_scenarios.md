# Phase 11.2 — Chaos Scenarios

## Overview

This document defines failure scenarios for testing SRRA+OPH resilience.

## Scenario Matrix

| Scenario | Target | Expected Behavior | Recovery Path |
|----------|--------|-------------------|---------------|
| Observer Kill | Trading Observer | Auto-restart within 30s | Observer registry rebuild |
| Event Flood | Event Fabric | Backpressure activated | Queue prioritization |
| Memory Corruption | Structural Memory | Contradiction detection | Memory rollback |
| Router Failure | Topology Router | Rerouting | Alternative paths |
| WebSocket Loss | Hermes MCP | Reconnect | Session restore |
| Token Starvation | All Observers | Degraded mode | Token compression |
| Recursive Storm | Orchestration | Bounded depth | Depth limiting |
| Twin Desync | OC2/OC3 | Reconciliation | State sync |

## Detailed Scenarios

### 1. Observer Termination (TEST 11.2-A)

**Goal:** Verify observer death does not spread.

**Procedure:**
- Randomly kill Trading, Repair, Planner, Memory observers
- During active runtime
- Every 2 hours

**Validate:**
- Cascade failures = 0
- Recovery time < 30s
- Lost continuity < 5%
- Event recovery = automatic

**Required Behaviors:**
- Observer heartbeat timeout
- Automatic restart
- State restoration
- Continuity reconstruction
- Reroute pending tasks

### 2. Event Flood (TEST 11.2-B)

**Goal:** Verify Event Fabric stability under overload.

**Procedure:**
- Inject 10x normal event rate
- Malformed events
- Recursive event chains
- Duplicate events

**Measure:**
- Queue overflow = prevented
- Event loss < 1%
- Routing latency = bounded
- Entropy growth = bounded

**Required Systems:**
- Backpressure
- Priority queues
- Event compression
- Flood throttling

### 3. Memory Corruption (TEST 11.2-C)

**Goal:** Verify system detects poisoned continuity.

**Procedure:**
- Inject false memories
- Conflicting memories
- Timestamp corruption
- Recursive hallucinations
- Stale trajectories

**Validate:**
- Contradiction detection > 90%
- Poison propagation = prevented
- Reconstruction accuracy > 85%
- False continuity = 0

**Required Systems:**
- Confidence scoring
- Contradiction graph
- Memory decay
- Trajectory auditing
- Checksum validation

### 4. Token Starvation (TEST 11.2-D)

**Goal:** Verify system survives compute scarcity.

**Procedure:**
- Restrict context window
- Token budgets
- Model availability
- Response latency

**Validate:**
- Graceful degradation = yes
- Core continuity preserved = yes
- Observer survival > 95%
- Recursive collapse = 0

**Required Systems:**
- Degraded cognition mode
- Summary compression
- Entropy shedding
- Observer prioritization

### 5. Twin Claw Desync (TEST 11.2-E)

**Goal:** Verify OC2 and OC3 recover synchronization.

**Procedure:**
- Isolated memory writes
- Conflicting trajectories
- Delayed event sync
- Split-brain states

**Validate:**
- Sync recovery time < 60s
- Continuity loss < 5%
- Memory divergence < 10%
- Task consistency > 95%

## Running Scenarios

```bash
# Run single scenario
python -m tools.testing.chaos.chaos_engine --scenario observer_death

# Run all scenarios
python -m tools.testing.chaos.chaos_engine --all

# Run with custom parameters
python -m tools.testing.chaos.chaos_engine --scenario full_chaos --severity 0.8
```

## Monitoring

All chaos events are logged to:
- `stability/chaos_events` table
- WebSocket stream at `/ws/stability`
- API endpoint `/api/stability/chaos`

## Pass Criteria

| Metric | Target |
|--------|--------|
| Infinite loops | 0 |
| Orphan agents | 0 |
| Max recursion | bounded |
| Token runaway | prevented |
| Recovery time | < 60s |
| Continuity loss | < 5% |