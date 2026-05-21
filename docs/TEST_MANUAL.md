# 🧪 LARGER-LAB TEST MANUAL

> **Version:** 1.0 | **Last Updated:** May 21, 2026 | **Phase:** V3 P11.1 Active

---

## 📋 TABLE OF CONTENTS

1. [Test Philosophy](#test-philosophy)
2. [Test Categories](#test-categories)
3. [Phase 11.1 Long-Horizon Tests](#phase-111-long-horizon-tests)
4. [Chaos Engine Tests](#chaos-engine-tests)
5. [OCE/SRRA-OPH Tests](#ocesrra-oph-tests)
6. [System Capability Tests](#system-capability-tests)
7. [Running Tests](#running-tests)
8. [Interpreting Results](#interpreting-results)

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

### 1. Phase 11.1 Long-Horizon Continuity Tests

**Purpose:** Validate system can run autonomously for 24-72 hours without degradation.

**Current Status:** ✅ **RUNNING** (PID 1628, 10 observers)

| Test | What It Does | Scale | Duration |
|------|-------------|-------|----------|
| Observer Stress Test | 10 tasks/minute per observer | 100 tasks/minute total | 24 hours |
| Runtime Monitor | Collects CPU, memory, uptime metrics | Every 60 seconds | Continuous |
| Continuity Checksum | SHA256 hashes of state | Every 5 minutes | Continuous |
| Stability Runner | Orchestrates all tests | Daemon mode | 24 hours |

### 2. Chaos Engine Tests

**Purpose:** Inject failures to test resilience and recovery.

| Test | What It Simulates | Duration | Recovery Target |
|------|-------------------|----------|-----------------|
| Observer Kill | Process death | 30s | 30s |
| Event Flood | Event fabric overload | 120s | 60s |
| Memory Corrupt | False/conflicting memories | 60s | 30s |
| Token Starve | Resource starvation | 180s | 60s |
| Recursive Storm | Delegation explosion | 60s | 30s |
| Full Chaos | All failures combined | Varies | 120s |

### 3. OCE/SRRA-OPH Tests

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

## 🕐 PHASE 11.1 LONG-HORIZON TESTS

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

## 🌪️ CHAOS ENGINE TESTS

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
| Phase 11.1 Observer Stress | 🔄 Running | 10 observers | N/A |
| Chaos Engine | ⏸️ Ready | 8 scenarios | N/A |
| OCE/SRRA-OPH | ✅ Complete | 1460 | 100% |
| System Capabilities | ✅ Complete | 11 | 100% |

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