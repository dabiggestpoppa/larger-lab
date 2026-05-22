# 🧪 LARGER-LAB TEST MANUAL

> **Version:** 1.1 | **Last Updated:** May 21, 2026 | **Phase:** V3 P11 Active (11.1 Running)

---

## 📋 TABLE OF CONTENTS

1. [Test Philosophy](#test-philosophy)
2. [Test Categories](#test-categories)
3. [Phase 11.1 Runtime Stability](#phase-111-runtime-stability-24h)
4. [Phase 11.2 Chaos Engineering](#phase-112-chaos-engineering)
5. [Phase 11.3 Continuity Stability](#phase-113-continuity-stability-72h)
6. [Phase 11.4 Memory Stability](#phase-114-memory-stability-7d)
7. [Phase 11.5 Orchestration Stability](#phase-115-orchestration-stability-7d)
8. [Phase 11.6 Resource Stability](#phase-116-resource-stability-7d)
9. [Phase 11.7 Recovery Stability](#phase-117-recovery-stability-cycles)
10. [OCE/SRRA-OPH Tests](#ocesrra-oph-tests)
11. [System Capability Tests](#system-capability-tests)
12. [Running Tests](#running-tests)
13. [Interpreting Results](#interpreting-results)

---

## 🎯 TEST PHILOSOPHY

### What We Test

| Category | Purpose | Real-World Equivalent |
|----------|---------|----------------------|
| **Long-Horizon** | 24-72 hour continuous operation | Production deployment |
| **Chaos** | Failure injection & recovery | Real-world outages |
| **Integration** | Component interaction | Live system behavior |
| **Capability** | Actual system performance | Deployment readiness |

### Success Criteria

- **99.5% uptime** for observer survival
- **Zero observer deaths** during chaos
- **Full recovery** within 30 seconds
- **Memory integrity** preserved
- **No drift** in continuity checksums

---

## 📚 TEST CATEGORIES

### Phase 11 — Operational Validation Overview

| Sub-Phase | Duration | Target | Pass Criteria | Status |
|-----------|----------|--------|---------------|--------|
| **11.1 Runtime Stability** | 24h | No observer death | >99.5% uptime | 🔄 Running |
| **11.2 Chaos Engineering** | Varies | Recovery | Auto-restart | ⏸️ Ready |
| **11.3 Continuity Stability** | 72h | Identity continuity | ≥95% integrity | ⏸️ Pending |
| **11.4 Memory Stability** | 7d | No poisoning | <2% contradiction | ⏸️ Pending |
| **11.5 Orchestration Stability** | 7d | No collapse | Stable | ⏸️ Pending |
| **11.6 Resource Stability** | 7d | Bounded entropy | Bounded | ⏸️ Pending |
| **11.7 Recovery Stability** | Cycles | Identity preserved | <60s recovery | ⏸️ Pending |

---

### 1. Phase 11.1 Runtime Stability (24h)

**Purpose:** Validate system can run autonomously for 24 hours without observer death.

**Current Status:** ✅ **RUNNING** (PID 1628, 10 observers)

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Observer Stress Test | 10 tasks/minute per observer | 100 tasks/minute total | 24 hours |
| Runtime Monitor | Collects CPU, memory, uptime metrics | Every 60 seconds | Continuous |
| Continuity Checksum | SHA256 hashes of state | Every 5 minutes | Continuous |
| Stability Runner | Orchestrates all tests | Daemon mode | 24 hours |

### 2. Phase 11.2 Chaos Engineering

**Purpose:** Inject failures to test resilience and recovery.

| Test | What It Simulates | Duration | Recovery Target |
|------|-------------------|----------|-----------------|
| Observer Kill | Process death | 30s | 30s |
| Event Flood | Event fabric overload | 120s | 60s |
| Memory Corrupt | False/conflicting memories | 60s | 30s |
| Token Starve | Resource starvation | 180s | 60s |
| Recursive Storm | Delegation explosion | 60s | 30s |
| Full Chaos | All failures combined | Varies | 120s |

### 3. Phase 11.3 Continuity Stability (72h)

**Purpose:** Validate identity continuity over 72 hours.

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Continuity Probe | Periodic state sampling | Every 5 minutes | 72 hours |
| Drift Tracker | Monitors state drift | Continuous | 72 hours |
| Restart Validator | Validates post-restart state | On restart | 72 hours |
| Continuity Checksum | SHA256 integrity checks | Every 5 minutes | 72 hours |

### 4. Phase 11.4 Memory Stability (7d)

**Purpose:** Validate memory integrity over 7 days.

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Memory Integrity | Checks for poisoning/drift | Every 60s | 7 days |
| Contradiction Detector | Finds conflicting memories | Continuous | 7 days |
| Memory Decay | Validates decay curves | Daily | 7 days |
| Poisoning Resistance | Tests false memory rejection | Continuous | 7 days |

### 5. Phase 11.5 Orchestration Stability (7d)

**Purpose:** Validate orchestration doesn't collapse.

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Orchestration Monitor | Tracks delegation chains | Continuous | 7 days |
| Collapse Detector | Detects runaway recursion | Continuous | 7 days |
| Stability Runner | Orchestrates all tests | Daemon mode | 7 days |
| Entropy Monitor | Tracks system entropy | Every 60s | 7 days |

### 6. Phase 11.6 Resource Stability (7d)

**Purpose:** Validate bounded entropy growth.

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Entropy Monitor | Tracks entropy growth | Every 60s | 7 days |
| Resource Tracker | CPU, memory, disk | Every 60s | 7 days |
| Budget Enforcer | Enforces entropy limits | Continuous | 7 days |
| Stability Runner | Orchestrates all tests | Daemon mode | 7 days |

### 7. Phase 11.7 Recovery Stability (Cycles)

**Purpose:** Validate identity preservation across restarts.

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Restart Validator | Captures pre/post state | On restart | Cycles |
| Recovery Timer | Measures recovery time | On restart | Cycles |
| Identity Checker | Validates identity preserved | On restart | Cycles |
| Continuity Reconstructor | Rebuilds state | On restart | Cycles |

---

### 8. OCE/SRRA-OPH Tests

**Purpose:** Validate all 10 V3 phases work together.

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 1-10 | 1403 OCE + 57 SRRA-OPH tests | ✅ Complete |
| Integration | End-to-end workflows | ✅ Complete |
| Adapter | SRRSAdapter functionality | ✅ Complete |

### 4. System Capability Tests

**Purpose:** Real system validation for deployment readiness.

| Test | What It Validates | Scale |
|------|-------------------|-------|
| Field Coherence Chain | Resonance → Nodes → Attractor | 3 components |
| Recursive Compute | Phase 10 RCG integration | 100 nodes |
| Memory Efficiency | GC under load | 100 nodes |
| Concurrent Operations | Thread safety | 5 threads |
| Error Recovery | Graceful failure handling | N/A |

---

## 🕐 PHASE 11.1 RUNTIME STABILITY (24H)

### Observer Stress Test

**File:** `tools/testing/long_horizon/observer_stress.py`

#### What It Does
- Registers 10 observers (observer_0 through observer_9)
- Each observer processes 10 tasks per minute
- Simulates 1% random error rate
- Checks health every 60 seconds
- Detects degraded/dead observers

#### How It Works
```python
# Observer state tracking
@dataclass
class ObserverState:
    observer_id: str
    status: str  # alive, degraded, dead
    last_heartbeat: float
    tasks_completed: int
    errors: int
    uptime_seconds: float

# Health check logic
if now - obs.last_heartbeat > 300:  # 5 minutes
    obs.status = "dead"
```

#### Test Scale
| Metric | Value |
|--------|-------|
| **Tasks/minute** | 100 (10 observers × 10) |
| **Tasks/hour** | 6,000 |
| **Tasks/24h** | 144,000 |
| **Error injection** | 1% (1,440 simulated errors) |
| **Health checks** | 1,440 (every minute) |

#### Pass/Fail Criteria
- **PASS:** 99.5% uptime, zero observer deaths
- **FAIL:** Any observer dies (heartbeat > 5 min)

#### Current Status
```
Process: PID 1628
Observers: 10 registered
Status: Running (11 threads, 1.7MB working set)
```

### Runtime Monitor

**File:** `tools/testing/long_horizon/runtime_monitor.py`

#### What It Does
- Collects CPU, memory, disk metrics
- Tracks uptime and process count
- Stores in SQLite database
- Runs every 60 seconds

#### Metrics Collected
| Metric | Description |
|--------|-------------|
| cpu_percent | CPU usage percentage |
| memory_mb | Memory in MB |
| disk_percent | Disk usage |
| uptime_seconds | Process uptime |
| process_count | Active Python processes |

### Continuity Checksum Engine

**File:** `tools/testing/long_horizon/continuity_checksum.py`

#### What It Does
- Generates SHA256 hashes of system state
- Tracks identity, trajectory, goals, memory
- Detects drift between checkpoints
- Validates continuity integrity

#### Checksum Components
```python
state = {
    "identity": "observer_0",
    "trajectory": ["task1", "task2", ...],
    "goals": ["goal1", "goal2"],
    "memory": [{"id": "mem1", "content": "..."}]
}
checksum = sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
```

#### Drift Detection
- **No drift:** Checksums match
- **Drift detected:** Checksums differ
- **Severity:** % difference in state

---

## 🌪️ PHASE 11.2 CHAOS ENGINEERING

### Chaos Types

| Type | Description | Real-World Equivalent |
|------|-------------|----------------------|
| OBSERVER_KILL | Kills an observer process | Server crash |
| EVENT_FLOOD | Floods event fabric | DDoS attack |
| MEMORY_CORRUPT | Injects false memories | Data corruption |
| ROUTER_FAILURE | Simulates router down | Network outage |
| WEBSOCKET_LOSS | Disconnects websocket | Connection drop |
| TOKEN_STARVE | Reduces token budget | Rate limiting |
| RECURSIVE_STORM | Triggers delegation storm | Infinite loop |
| TWIN_DESYNC | Desyncs twin claws | Data inconsistency |

### Chaos Scenarios

#### Observer Death Scenario
```python
engine.run_chaos_scenario("observer_death")
# Kills: trading_observer, repair_observer
# Duration: 30s each
# Recovery: Auto-restart
```

#### Full Chaos Scenario
```python
engine.run_chaos_scenario("full_chaos")
# Kills: planner_observer
# Floods: event_fabric (15x rate)
# Corrupts: structural_memory (20%)
# Disconnects: hermes_mcp websocket
```

### Heavy Compute Test: Recursive Storm

**This is the heavy compute equivalent for AI systems.**

#### What It Simulates
- **Exponential delegation growth** (1 → 10 → 100 → 1000...)
- **Memory explosion** from nested contexts
- **Stack overflow prevention**
- **Recovery from runaway recursion**

#### Why This Matters
Current AI systems fail when they enter recursive loops:
- "Let me think step by step" repeated infinitely
- Context window explosion
- Memory exhaustion
- No recovery mechanism

#### Test Parameters
```python
engine.recursive_storm("orchestration")
# Duration: 60 seconds
# Severity: 0.8
# Expected: Recovery within 30 seconds
```

---

## 🔗 PHASE 11.3 CONTINUITY STABILITY (72H)

### Continuity Probe

**File:** `tools/testing/long_horizon/continuity_probe.py`

#### What It Does
- Samples system state every 5 minutes
- Records identity, trajectory, goals, memory
- Stores snapshots for drift analysis
- Runs for 72 hours continuously

#### How It Works
```python
# Probe state
@dataclass
class ContinuityProbe:
    probe_id: str
    timestamp: float
    identity: str
    trajectory: List[str]
    goals: List[str]
    memory_checksum: str
```

#### Pass/Fail Criteria
- **PASS:** ≥95% integrity over 72 hours
- **FAIL:** <95% integrity or any discontinuity

---

## 🧠 PHASE 11.4 MEMORY STABILITY (7D)

### Memory Integrity Checker

**File:** `tools/testing/long_horizon/memory_integrity.py`

#### What It Does
- Scans memory for contradictions
- Detects poisoned/false memories
- Validates memory decay curves
- Runs for 7 days continuously

#### Test Scale
| Metric | Value |
|--------|-------|
| **Scan frequency** | Every 60 seconds |
| **Duration** | 7 days |
| **Contradiction threshold** | <2% |
| **Poisoning detection** | >90% |

#### Pass/Fail Criteria
- **PASS:** <2% contradiction rate
- **FAIL:** ≥2% contradiction or poisoning detected

---

## ⚙️ PHASE 11.5 ORCHESTRATION STABILITY (7D)

### Orchestration Monitor

**File:** `tools/testing/long_horizon/stability_runner.py`

#### What It Does
- Tracks delegation chains
- Detects runaway recursion
- Monitors orchestration health
- Runs for 7 days continuously

#### Key Metrics
| Metric | Target |
|--------|--------|
| **Collapse events** | 0 |
| **Recursion depth** | Bounded |
| **Delegation chains** | Stable |

---

## 📊 PHASE 11.6 RESOURCE STABILITY (7D)

### Entropy Monitor

**File:** `tools/testing/long_horizon/entropy_monitor.py`

#### What It Does
- Tracks system entropy growth
- Enforces entropy budgets
- Monitors resource usage
- Runs for 7 days continuously

#### Key Metrics
| Metric | Target |
|--------|--------|
| **Entropy growth** | Bounded |
| **CPU usage** | <80% |
| **Memory growth** | Linear |

---

## 🔄 PHASE 11.7 RECOVERY STABILITY (CYCLES)

### Restart Validator

**File:** `tools/testing/long_horizon/restart_validator.py`

#### What It Does
- Captures pre-restart state
- Validates post-restart state
- Measures recovery time
- Verifies identity preservation

#### Pass/Fail Criteria
- **PASS:** Recovery <60s, identity preserved
- **FAIL:** Recovery >60s or identity lost

---

## 🔗 OCE/SRRA-OPH TESTS

### Chaos Types

| Type | Description | Real-World Equivalent |
|------|-------------|----------------------|
| OBSERVER_KILL | Kills an observer process | Server crash |
| EVENT_FLOOD | Floods event fabric | DDoS attack |
| MEMORY_CORRUPT | Injects false memories | Data corruption |
| ROUTER_FAILURE | Simulates router down | Network outage |
| WEBSOCKET_LOSS | Disconnects websocket | Connection drop |
| TOKEN_STARVE | Reduces token budget | Rate limiting |
| RECURSIVE_STORM | Triggers delegation storm | Infinite loop |
| TWIN_DESYNC | Desyncs twin claws | Data inconsistency |

### Chaos Scenarios

#### Observer Death Scenario
```python
engine.run_chaos_scenario("observer_death")
# Kills: trading_observer, repair_observer
# Duration: 30s each
# Recovery: Auto-restart
```

#### Full Chaos Scenario
```python
engine.run_chaos_scenario("full_chaos")
# Kills: planner_observer
# Floods: event_fabric (15x rate)
# Corrupts: structural_memory (20%)
# Disconnects: hermes_mcp websocket
```

### Heavy Compute Test: Recursive Storm

**This is the heavy compute equivalent for AI systems.**

#### What It Simulates
- **Exponential delegation growth** (1 → 10 → 100 → 1000...)
- **Memory explosion** from nested contexts
- **Stack overflow prevention**
- **Recovery from runaway recursion**

#### Why This Matters
Current AI systems fail when they enter recursive loops:
- "Let me think step by step" repeated infinitely
- Context window explosion
- Memory exhaustion
- No recovery mechanism

#### Test Parameters
```python
engine.recursive_storm("orchestration")
# Duration: 60 seconds
# Severity: 0.8
# Expected: Recovery within 30 seconds
```

---

## 🔗 OCE/SRRA-OPH TESTS

### Test Structure

| Phase | Files | Tests | Status |
|-------|-------|-------|--------|
| Phase 1 | test_phase2_e2e.py | 23 | ✅ |
| Phase 2 | test_phase2_e2e.py | 23 | ✅ |
| Phase 3 | test_phase3_e2e.py | 24 | ✅ |
| Phase 4 | test_phase4_e2e.py | 104 | ✅ |
| Phase 5 | test_phase5_e2e.py | 24 | ✅ |
| Phase 6 | test_phase6_e2e.py | 24 | ✅ |
| Phase 7 | test_phase7_e2e.py | 24 | ✅ |
| Phase 8 | test_phase8_e2e.py | 76 | ✅ |
| Phase 9 | test_oce_adapter.py | 25 | ✅ |
| Phase 10 | test_phase10.py | 23 | ✅ |

### OCE Adapter Tests

**File:** `oce/tests/test_oce_adapter.py`

#### What It Tests
- Adapter initialization
- Observer status retrieval
- Health checks
- Entropy economics metrics
- Attractor state
- Memory access
- Event emission
- Prediction contracts

#### Key Tests
```python
# Initialization
test_initialize_creates_patches()  # Creates 4 observer patches
test_initialize_creates_entropy_components()  # Phase 9 components

# Observer Status
test_get_observer_status_returns_all()  # Returns all 4 observers
test_observers_are_active()  # Verifies observers are alive

# Health
test_health_returns_healthy()  # Overall health check
test_health_patches_are_healthy()  # Individual patch health
```

---

## ⚙️ SYSTEM CAPABILITY TESTS

### File: `oce/backend/tests/test_system_capabilities.py`

#### Test: Field Coherence Chain
```python
def test_field_coherence_chain(self):
    """Test full field coherence chain: resonance → nodes → attractor."""
    engine = ResonanceEngine()
    state = engine.measure_resonance("a", "b", 0.9, 0.9, 0.1, 0.1)
    assert state.is_resonant
    
    registry = FieldNodeRegistry()
    node = registry.register("test_node", local_state={"value": 1.0})
    
    mapper = AttractorMapper()
    attractor = mapper.register_attractor("test_attractor")
```

#### Test: Memory Efficiency
```python
def test_memory_efficiency(self):
    """Test system handles memory efficiently under load."""
    graph = RecursiveComputeGraph("memory_test")
    for i in range(100):
        node = ComputeNode(node_id=f"node_{i}", ...)
        graph.add_node(node)
    results = graph.compute()
    assert len(results) == 100
```

#### Test: Concurrent Operations
```python
def test_concurrent_operations(self):
    """Test system handles concurrent operations."""
    threads = [threading.Thread(target=create_graph, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results["count"] == 5
```

---

## ▶️ RUNNING TESTS

### Quick Start

```bash
# Run Phase 11.1 observer stress test
python tools/testing/long_horizon/observer_stress.py

# Run chaos engine test
python tools/testing/chaos/chaos_engine.py

# Run OCE adapter tests
pytest oce/tests/test_oce_adapter.py -v

# Run system capability tests
pytest oce/backend/tests/test_system_capabilities.py -v

# Run all SRRA-OPH tests
pytest srrs_opc/tests/ -v
```

### Current Running Test

```bash
# Check status
python tools/memory_sync_daemon.py --status

# Output:
# 🧠 Daemon running (PID 14088)
#    Scans: 5 | Syncs: 0
```

---

## 📊 INTERPRETING RESULTS

### Observer Stress Test Results

| Result | Meaning | Action |
|--------|---------|--------|
| `uptime_percent >= 99.5` | PASS | System stable |
| `uptime_percent < 99.5` | FAIL | Investigate degradation |
| `dead > 0` | FAIL | Observer died |
| `degraded > 0` | WARNING | Monitor closely |

### Chaos Test Results

| Result | Meaning | Action |
|--------|---------|--------|
| `recovered == True` | PASS | Recovery worked |
| `recovered == False` | FAIL | Fix recovery logic |
| `recovery_time < 30s` | PASS | Fast recovery |
| `recovery_time > 30s` | WARNING | Optimize recovery |

### Continuity Checksum Results

| Result | Meaning | Action |
|--------|---------|--------|
| `drift == 0` | PASS | No state drift |
| `drift > 0` | WARNING | Check memory integrity |
| `checksum_match == True` | PASS | State preserved |
| `checksum_match == False` | FAIL | Investigate drift |

---

## 📈 CURRENT STATUS

### Test Summary

| Test Suite | Status | Tests | Pass Rate |
|------------|--------|-------|-----------|
| Phase 11.1 Observer Stress | 🔄 Running | 10 observers | 100% (16h) |
| Chaos Engine | 🔄 Ready | 4 scenarios | N/A |
| OCE/SRRA-OPH | ✅ Complete | 1460 | 100% |
| System Capabilities | ✅ Complete | 11 | 100% |

### Phase 11.1 Progress (16 Hours)

| Time | Alive | Degraded | Dead | Status |
|------|-------|----------|------|--------|
| 0.0h | 10 | 0 | 0 | ✅ Started |
| 5.0h | 10 | 0 | 0 | ✅ Exceeds previous 5.7h failure point |
| 10.0h | 10 | 0 | 0 | ✅ 10-hour milestone |
| 15.0h | 10 | 0 | 0 | ✅ 15-hour milestone |
| 16.0h | 10 | 0 | 0 | ✅ 16-hour milestone |

### Phase 11.2 Chaos Scenarios Ready

| Scenario | Description | Duration | Status |
|----------|-------------|----------|--------|
| observer_death | Kill trading_observer + repair_observer | 30s | 🔄 Ready |
| event_flood | Flood event_fabric at 20x rate | 120s | 🔄 Ready |
| memory_poison | Inject false memories at 30% rate | 60s | 🔄 Ready |
| full_chaos | Combined: kill + flood + corrupt + websocket loss | 120s | 🔄 Ready |

### Active Processes

| Process | PID | Command |
|---------|-----|---------|
| Observer Stress Test | 1628 | 10 observers, 24h test |
| Memory Sync Daemon | 14088 | Scanning every 60s |
| OCE Backend | 10572 | uvicorn port 8000 |
| SRRA API | 23760 | uvicorn port 8001 |
| DMR Dashboard | 19320 | uvicorn port 8002 |

---

## 📝 NOTES

- **Phase 11.1** is the final validation before production
- **Chaos tests** should be run after observer stress completes
- **All tests** are automated and logged to `stability/` directory
- **Results** are stored in SQLite databases for analysis