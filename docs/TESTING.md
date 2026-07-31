# 🧪 Testing Guide — Larger-Lab

> **Last Updated:** 2026-05-20
> **Total Tests:** 1460+ passing (1403 OCE + 56 SRRA-OPH)
> **Test Framework:** pytest 8.x+

---

## Table of Contents

1. [Test Structure Overview](#1-test-structure-overview)
2. [How to Run Tests](#2-how-to-run-tests)
3. [Test Categories](#3-test-categories)
4. [Test Counts by Phase](#4-test-counts-by-phase)
5. [Writing New Tests](#5-writing-new-tests)
6. [Debugging Failing Tests](#6-debugging-failing-tests)
7. [System Capability Tests](#7-system-capability-tests)
8. [CI/CD Integration](#8-cicd-integration)

---

## 1. Test Structure Overview

Tests are organized into two main subsystems:

### OCE (Operator Continuity Engine)

```
oce/backend/
├── tests/                          # Core OCE tests (22 test files)
│   ├── test_adaptive_compression.py
│   ├── test_alerting_engine.py
│   ├── test_coevolution_protocol.py
│   ├── test_consensus_engine.py
│   ├── test_drift_detector.py
│   ├── test_dspy_execution.py
│   ├── test_dspy_resonance.py
│   ├── test_economics_engine.py
│   ├── test_event_fabric.py
│   ├── test_execution_engine.py
│   ├── test_governance_engine.py
│   ├── test_metrics_collector.py
│   ├── test_observer_runtime.py
│   ├── test_resonance_integration.py
│   ├── test_self_healing.py
│   ├── test_structural_memory.py
│   ├── test_sync_cost_optimizer.py
│   ├── test_system_capabilities.py    # 11 integration tests
│   ├── test_topology_routing.py
│   └── test_tracing_engine.py
├── cognition/tests/                # Phase 6 tests
├── coevolution/tests/              # Phase 8 tests
├── field_core/tests/               # Phase 9 tests
├── introspection/tests/            # Phase 6 tests
├── multiscale/tests/               # Phase 7 tests
├── phase10/tests/                  # Phase 10 tests
├── production/tests/               # Production readiness tests
├── reconstruction/tests/           # Phase 2 tests
├── resonance/tests/                # Phase 1 tests
├── sovereign/tests/                # Phase 4 tests
├── temporal/tests/                 # Phase 5 tests
└── topology/tests/                 # Phase 3 tests
```

### SRRA-OPH (Substrate)

```
srrs_opc/
├── tests/
│   ├── test_phase2_e2e.py
│   ├── test_phase3_book2.py
│   ├── test_phase3_e2e.py
│   ├── test_phase4_e2e.py
│   ├── test_phase5_e2e.py
│   ├── test_phase6_e2e.py
│   ├── test_phase7_e2e.py
│   ├── test_phase8_e2e.py
│   └── test_phase9_e2e.py
```

---

## 2. How to Run Tests

### Full Suite

```powershell
# Run all SRRA-OPH tests
python -m pytest srrs_opc/tests/ -v

# Run all OCE core tests
python -m pytest oce/backend/tests/ -v

# Run everything (from workspace root)
python -m pytest srrs_opc/tests/ oce/backend/tests/ -v
```

### Specific Phase (SRRA-OPH)

```powershell
python -m pytest srrs_opc/tests/test_phase3_e2e.py -v
python -m pytest srrs_opc/tests/test_phase7_e2e.py -v
```

### Specific Module (OCE)

```powershell
python -m pytest oce/backend/tests/test_event_fabric.py -v
python -m pytest oce/backend/resonance/tests/ -v
python -m pytest oce/backend/phase10/tests/ -v
```

### Specific Test Class or Method

```powershell
python -m pytest oce/backend/tests/test_system_capabilities.py::TestSystemIntegration::test_field_coherence_chain -v
```

### Useful Flags

| Flag | Purpose |
|------|---------|
| `-v` | Verbose output (shows each test name) |
| `-q` | Quiet output (summary only) |
| `-x` | Stop on first failure |
| `--tb=short` | Short traceback on failure |
| `--tb=long` | Full traceback on failure |
| `-k "pattern"` | Run tests matching pattern string |
| `--co` | Collect tests without running (dry run) |
| `-p no:warnings` | Suppress warning output |

### Examples

```powershell
# Run only tests matching "resonance" in the name
python -m pytest oce/backend/resonance/tests/ -k "resonance" -v

# Stop on first failure with short traceback
python -m pytest srrs_opc/tests/ -x --tb=short

# Collect all tests to see what would run
python -m pytest oce/backend/tests/ --co -q
```

---

## 3. Test Categories

### Unit Tests

Test individual functions and classes in isolation. Fast, deterministic, no external dependencies.

```python
# Example: Testing a single function
def test_signal_packet_creation():
    packet = SignalPacket(id="sig-01", energy=0.8, coherence=0.9)
    assert packet.id == "sig-01"
    assert packet.energy == 0.8
    assert packet.is_valid
```

**Location:** Most `test_*.py` files in `oce/backend/<phase>/tests/`

### Integration Tests

Test that multiple components work together correctly. These validate data flow between modules.

```python
# Example: Testing field coherence chain
def test_field_coherence_chain():
    engine = ResonanceEngine()
    state = engine.measure_resonance("a", "b", 0.9, 0.9, 0.1, 0.1)
    assert state.is_resonant

    registry = FieldNodeRegistry()
    node = registry.register("test_node", local_state={"value": 1.0})
    assert registry.get("test_node") is not None
```

**Location:** `oce/backend/tests/test_system_capabilities.py`, `test_resonance_integration.py`

### End-to-End (E2E) Tests

Test complete phase workflows from input to output. These validate that all modules in a phase work together.

```python
# Example: Phase 3 E2E test
def test_phase3_full_pipeline():
    # Setup topology → BSP projection → resonance routing
    topology = CollarField()
    projection = BSPProjection()
    router = ResonanceRouter()
    # ... full pipeline execution
    assert pipeline_result.is_valid
```

**Location:** `srrs_opc/tests/test_phase*_e2e.py`

### System Capability Tests

Validate end-to-end system behavior for deployment readiness. These are NOT unit tests — they test the real system.

**Location:** `oce/backend/tests/test_system_capabilities.py` (11 tests)

---

## 4. Test Counts by Phase

### OCE V3 Phases

| Phase | Directory | Focus | Test Files |
|-------|-----------|-------|------------|
| Phase 1 | `resonance/tests/` | Resonant Signal Substrate | 7 |
| Phase 2 | `reconstruction/tests/` | Reconstructive Continuity Manifold | 6 |
| Phase 3 | `topology/tests/` | Resonant Topology & BSP Emergence | 7 |
| Phase 4 | `sovereign/tests/` | Sovereign Instrumentation | 8 |
| Phase 5 | `temporal/tests/` | Long-Horizon Continuity | 7 |
| Phase 6 | `cognition/tests/` + `introspection/tests/` | Recursive Topology Introspection | 11 |
| Phase 7 | `multiscale/tests/` | Multi-Scale Cognitive Fields | 7 |
| Phase 8 | `coevolution/tests/` | Operator Coevolution | 1 |
| Phase 9 | `field_core/tests/` | Sovereign Field Emergence | 7 |
| Phase 10 | `phase10/tests/` | Recursive Field Computation | 1 |
| Core | `tests/` | System-wide capabilities | 22 |

### SRRA-OPH Phases

| Phase | Test File | Tests |
|-------|-----------|-------|
| Phase 2 | `test_phase2_e2e.py` | E2E substrate |
| Phase 3 | `test_phase3_book2.py` + `test_phase3_e2e.py` | Book + E2E |
| Phase 4 | `test_phase4_e2e.py` | E2E |
| Phase 5 | `test_phase5_e2e.py` | E2E |
| Phase 6 | `test_phase6_e2e.py` | E2E |
| Phase 7 | `test_phase7_e2e.py` | E2E |
| Phase 8 | `test_phase8_e2e.py` | E2E |
| Phase 9 | `test_phase9_e2e.py` | E2E |
| **Total** | | **56 passing** |

---

## 5. Writing New Tests

### Conventions

1. **File naming:** `test_<module_name>.py` — always prefix with `test_`
2. **Class naming:** `Test<FeatureName>` — PascalCase with `Test` prefix
3. **Method naming:** `test_<what_it_tests>` — descriptive snake_case
4. **Location:** Mirror the source structure — `oce/backend/<phase>/tests/` for phase modules

### Basic Template

```python
"""Tests for <module_name>."""

import pytest
import sys
import os

# Add workspace root to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from oce.backend.<phase>.<module> import ClassName


class TestFeatureName:
    """Tests for <FeatureName> behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.instance = ClassName()

    def teardown_method(self):
        """Clean up after test."""
        pass

    def test_basic_behavior(self):
        """Test that <expected behavior>."""
        result = self.instance.method()
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case: <description>."""
        with pytest.raises(ExpectedException):
            self.instance.method(invalid_input)
```

### Fixtures

Use `conftest.py` for shared fixtures:

```python
# oce/backend/<phase>/tests/conftest.py
import pytest
from oce.backend.<phase>.<module> import ClassName

@pytest.fixture
def instance():
    """Provide a fresh ClassName instance."""
    return ClassName()

@pytest.fixture
def configured_instance():
    """Provide a pre-configured instance."""
    inst = ClassName()
    inst.configure(param="value")
    return inst
```

### Test Intent (Rule 9)

Every test must encode **WHY** the behavior matters, not just **WHAT** it does.

```python
# BAD — tests what, not why
def test_get_value():
    assert get_value() == 42

# GOOD — tests intent
def test_field_coherence_drops_below_threshold_when_entropy_exceeds_limit():
    """When entropy exceeds the field's capacity, coherence must drop
    to prevent false resonance signals from propagating."""
    field = FieldState(entropy_limit=0.5)
    field.inject_entropy(0.8)
    assert field.coherence < field.COHERENCE_THRESHOLD
```

---

## 6. Debugging Failing Tests

### Step 1: Read the Error

```powershell
python -m pytest path/to/test.py::TestClass::test_method -v --tb=long
```

Read the **bottom** of the traceback first — that's where the actual error is.

### Step 2: Classify the Error

| Error Type | Symptom | Fix |
|------------|---------|-----|
| `ImportError` / `ModuleNotFoundError` | Module not found | Check `sys.path`, verify module exists |
| `AttributeError` | Method/attribute doesn't exist | Check class definition, check for typos |
| `AssertionError` | Test assertion failed | Check expected vs actual values |
| `NameError` | Variable not defined | Check variable scope, check for typos |
| `TypeError` | Wrong argument type | Check function signature |
| `FloatingPointError` | Precision mismatch | Use `pytest.approx()` for float comparisons |
| Collection error | `ERROR` during import | Check imports in the test file itself |

### Step 3: Common Patterns

**Floating point precision:**
```python
# BAD
assert result == 0.3

# GOOD
assert result == pytest.approx(0.3, abs=1e-6)
```

**Windows subprocess issues:**
```python
# BAD
subprocess.run("command", shell=True)

# GOOD
subprocess.run(['powershell', '-NoProfile', '-Command', 'command'])
```

**API version mismatches:**
```python
# Check the actual API signature
import inspect
print(inspect.signature(SomeClass.method))
```

### Step 4: Isolate the Failure

```powershell
# Run only the failing test
python -m pytest path/to/test.py::TestClass::test_method -xvs

# Run with debugger
python -m pytest path/to/test.py::TestClass::test_method -xvs --pdb
```

### Step 5: Verify the Fix

```powershell
# Run the specific test
python -m pytest path/to/test.py::TestClass::test_method -v

# Run the full file to check for regressions
python -m pytest path/to/test.py -v

# Run the full phase to check for cascading issues
python -m pytest oce/backend/<phase>/tests/ -v
```

---

## 7. System Capability Tests

The 11 system capability tests in `oce/backend/tests/test_system_capabilities.py` validate end-to-end system behavior for deployment readiness. They are **not** unit tests — they test the real system.

| # | Test | What It Validates |
|---|------|-------------------|
| 1 | `test_field_coherence_chain` | Full chain: resonance → field nodes → attractor mapper |
| 2 | `test_recursive_compute_integration` | Phase 10 RCG integrates with Phase 9 field_core |
| 3 | `test_positional_reference_integration` | PRS integrates with field topology |
| 4 | `test_resonance_propagation_integration` | RPE propagates through field correctly |
| 5 | `test_constraint_topology_integration` | DCT maintains constraints across field |
| 6 | `test_attractor_compute_integration` | ACE computes attractor states correctly |
| 7 | `test_drift_governance_integration` | Drift governor detects and corrects field drift |
| 8 | `test_reconstruction_integration` | Reconstruction core rebuilds field state |
| 9 | `test_continuity_identity_integration` | Identity engine preserves continuity across sessions |
| 10 | `test_self_healing_integration` | Self-healing detects and repairs field damage |
| 11 | `test_governance_integration` | Governance engine enforces operational constraints |

**Key principle:** These tests validate that the system works as a whole, not just that individual modules work in isolation.

---

## 8. CI/CD Integration

### Local Pre-Commit Testing

Before committing, always run the relevant tests:

```powershell
# Quick check — SRRA-OPH (fast)
python -m pytest srrs_opc/tests/ -q --tb=short

# Full check — OCE core
python -m pytest oce/backend/tests/ -q --tb=short
```

### Phase Gate Testing

Each phase must pass all tests before advancing:

```powershell
# Phase gate check
python -m pytest oce/backend/<phase>/tests/ -v --tb=short
```

### Test Automation

The workspace includes several test-related tools:

| Tool | Path | Purpose |
|------|------|---------|
| Phase Gate | `tools/phase-gate.py` | Phase transition manager — validates all tests pass before phase advance |
| Validation Gate | `tools/validation-gate.py` | Pre-deployment validation |
| Self Heal | `tools/self_heal.py` | Log scanner, error classifier, auto-fixer |
| Arch Commit | `tools/arch-commit.py` | Post-change alignment review |

### GitHub Actions (Planned)

```yaml
# .github/workflows/tests.yml (planned)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: python -m pytest srrs_opc/tests/ -v --tb=short
      - run: python -m pytest oce/backend/tests/ -v --tb=short
```

---

## Quick Reference

```powershell
# Run everything
python -m pytest srrs_opc/tests/ oce/backend/tests/ -v

# Run with coverage (if pytest-cov installed)
python -m pytest srrs_opc/tests/ --cov=srrs_opc --cov-report=term-missing

# Run only failed tests from last run
python -m pytest --lf -v

# Run tests in parallel (if pytest-xdist installed)
python -m pytest srrs_opc/tests/ -n auto
```
