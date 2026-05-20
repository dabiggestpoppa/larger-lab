# 📏 Code Quality Standards — Larger-Lab

> **Last Updated:** 2026-05-20
> **Python Version:** 3.11+ | **Package Manager:** uv
> **Contract:** [CLAUDE.md](../CLAUDE.md) — 12-Rule Behavioral Contract

---

## Table of Contents

1. [Python Version & Environment](#1-python-version--environment)
2. [Package Management](#2-package-management)
3. [Code Style](#3-code-style)
4. [Windows Execution Rules](#4-windows-execution-rules)
5. [Architecture Rules](#5-architecture-rules)
6. [Testing Requirements](#6-testing-testing-requirements)
7. [Documentation Requirements](#7-documentation-requirements)
8. [Git Workflow](#8-git-workflow)

---

## 1. Python Version & Environment

- **Python:** 3.11+ (see `.python-version`)
- **Virtual Environment:** `.venv/` managed by `uv`
- **Activation:** `.venv\Scripts\Activate.ps1` (PowerShell)

```powershell
# Check Python version
python --version

# Create virtual environment
uv venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1
```

---

## 2. Package Management

All dependencies are managed via `uv` and declared in `pyproject.toml`.

### Common Commands

```powershell
# Install all dependencies
uv sync

# Install a package
uv pip install <package>

# Install dev dependency
uv pip install --dev <package>

# List installed packages
uv pip list

# Update dependencies
uv lock --upgrade

# Run command in venv
uv run python script.py
```

### pyproject.toml Structure

```toml
[project]
name = "quant-lab"
requires-python = ">=3.12"

dependencies = [
    "nautilus_trader>=1.226.0",
    "numpy>=2.4.4",
    "pandas>=2.3.3,<3.0.0",
    # ...
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "jupyterlab>=4.0.0",
    "ipywidgets>=8.0.0",
]
```

### Rules

- **Never use `pip` directly** — always use `uv`
- **Pin major versions** for critical dependencies
- **Use dependency groups** for dev-only packages
- **Run `uv lock`** after adding dependencies

---

## 3. Code Style

### PEP 8 Compliance

Follow [PEP 8](https://peps.python.org/pep-0000/) with these project-specific additions:

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module | snake_case | `signal_packet.py` |
| Class | PascalCase | `SignalPacket` |
| Function | snake_case | `measure_resonance()` |
| Variable | snake_case | `coherence_score` |
| Constant | UPPER_SNAKE | `MAX_ENTROPY = 1.0` |
| Private | _leading_underscore | `_internal_state` |
| Test class | TestPascalCase | `TestSignalPacket` |
| Test method | test_snake_case | `test_signal_creation()` |

### Type Hints

Use type hints for all function signatures:

```python
def measure_resonance(
    source: str,
    target: str,
    source_energy: float,
    target_energy: float,
    source_entropy: float,
    target_entropy: float,
) -> ResonanceState:
    """Measure resonance between two field points."""
    ...
```

### Imports

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

# Third-party
import pytest
import numpy as np

# Local
from oce.backend.resonance.signal_packet import SignalPacket
from srrs_opc.observer_runtime import ObserverRuntime
```

### Line Length

- **Maximum:** 100 characters (soft limit)
- **Docstrings:** 88 characters (Black-compatible)

### Docstrings

Use Google-style docstrings:

```python
def compute_coherence(field: FieldState, window: int = 10) -> CoherenceSnapshot:
    """Compute coherence metrics for a field state snapshot.

    Measures phase alignment, entropy gradient, energy distribution,
    and resonance bandwidth over the specified window.

    Args:
        field: The field state to analyze.
        window: Number of historical states to include. Defaults to 10.

    Returns:
        CoherenceSnapshot with 6 metrics and overall health score.

    Raises:
        ValueError: If window is less than 1.
        FieldStateError: If field has no historical data.
    """
    ...
```

---

## 4. Windows Execution Rules

### PowerShell First

**ALWAYS use PowerShell for Windows operations.** Never use `cmd.exe` or `subprocess.run(..., shell=True)`.

```python
# BAD
subprocess.run("dir", shell=True)

# GOOD
subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-ChildItem'])
```

### Process Management

```python
# BAD
os.system("taskkill /PID 1234")

# GOOD
subprocess.run(['powershell', '-NoProfile', '-Command', 'Stop-Process -Id 1234 -Force'])
```

### File Operations

```python
# BAD
os.remove("file.txt")

# GOOD (Python stdlib is fine for simple operations)
from pathlib import Path
Path("file.txt").unlink()

# GOOD (PowerShell for complex operations)
subprocess.run(['powershell', '-NoProfile', '-Command', 'Remove-Item -Path "C:\path with spaces\file.txt" -Force'])
```

### CREATE_NO_WINDOW Flag

When spawning background processes on Windows, use `CREATE_NO_WINDOW` to prevent console popup:

```python
import subprocess

CREATE_NO_WINDOW = 0x08000000
process = subprocess.Popen(
    ['python', 'script.py'],
    creationflags=CREATE_NO_WINDOW
)
```

### PID Tracking

Always track spawned process PIDs for cleanup:

```python
import subprocess
import atexit

processes = []

def spawn_worker(script: str) -> subprocess.Popen:
    """Spawn a background worker process."""
    CREATE_NO_WINDOW = 0x08000000
    proc = subprocess.Popen(
        ['python', script],
        creationflags=CREATE_NO_WINDOW
    )
    processes.append(proc.pid)
    return proc

def cleanup():
    """Kill all spawned processes on exit."""
    for pid in processes:
        try:
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', f'Stop-Process -Id {pid} -Force'],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

atexit.register(cleanup)
```

---

## 5. Architecture Rules

### No Global State

Every node must self-stabilize. No module-level mutable state.

```python
# BAD
_state = {}  # Global mutable state

def get_state():
    return _state

# GOOD
class FieldStateManager:
    def __init__(self):
        self._state = {}  # Instance-level state
```

### Repair Before Scale

Never optimize throughput before stabilization.

```python
# BAD — optimizing before it works
@lru_cache(maxsize=1024)
@profile
def process_signal(signal):
    ...  # 50 lines of untested code

# GOOD — make it work first
def process_signal(signal):
    ...  # Simple, testable code

# THEN optimize after tests pass and profiling shows bottleneck
```

### Memory Must Compress

Linear memory growth is failure. Implement compression:

```python
# BAD — unbounded growth
history = []
def record(event):
    history.append(event)  # Grows forever

# GOOD — bounded with compression
from collections import deque
history = deque(maxlen=1000)
def record(event):
    history.append(event)  # Auto-evicts old entries
```

### Consensus Must Emergence

Never hardcode truth authority. Let consensus emerge from multiple observers.

```python
# BAD
def get_field_state():
    return primary_sensor.read()  # Single source of truth

# GOOD
def get_field_state():
    readings = [sensor.read() for sensor in self.sensors]
    return self._consensus_merge(readings)  # Emergent truth
```

---

## 6. Testing Requirements

### All Code Must Have Tests

Before advancing any phase, all new code must have corresponding tests.

```powershell
# Run tests for the phase you're working on
python -m pytest oce/backend/<phase>/tests/ -v

# Run SRRA-OPH tests
python -m pytest srrs_opc/tests/ -v
```

### Test Intent (Rule 9)

Every test must encode **WHY** the behavior matters:

```python
# BAD
def test_get_value():
    assert get_value() == 42

# GOOD
def test_field_coherence_drops_when_entropy_exceeds_limit():
    """When entropy exceeds the field's capacity, coherence must drop
    to prevent false resonance signals from propagating."""
    field = FieldState(entropy_limit=0.5)
    field.inject_entropy(0.8)
    assert field.coherence < field.COHERENCE_THRESHOLD
```

### Floating Point Comparisons

```python
# BAD
assert result == 0.3

# GOOD
assert result == pytest.approx(0.3, abs=1e-6)
```

---

## 7. Documentation Requirements

### Module-Level Docstrings

Every module must have a docstring:

```python
"""
Signal Packet Module
====================
Defines SignalPacket and SignalField — the core signal objects
that carry field state through the cognitive field.

Part of Phase 1: Resonant Signal Substrate.
"""
```

### Function Docstrings

All public functions must have Google-style docstrings with Args, Returns, and Raises.

### Architecture Docs

After any code change affecting architecture:

```powershell
python tools/arch-commit.py --agent <TAG> --file "<path>" --change "<description>"
```

### Progress Files

After every code edit:
1. Update your progress file (`progress/<agent>-progress.md`)
2. Update your memory file (`progress/<agent>-memory.md`)
3. After every 5 edits: Post summary to `shared-conversations/team-chat.md`

---

## 8. Git Workflow

### Branch Strategy

- **Default branch:** `master`
- **Feature branches:** `<agent>/<description>` (e.g., `pm/error-doc-update`)
- **Direct commits to master:** Allowed for documentation and tooling changes

### Commit Messages

```
<Agent>: <description>

Examples:
  PM: Fix variable reference in pressure_tracker.py
  PM: Add docs/TESTING.md — comprehensive testing guide
  PM: GitHub docs revamp — code quality, debugging, testing, GitHub config
  CC: Add Phase 10 recursive field computation modules
  AS: Update API reference for OCE backend
```

### Arch Commit

After any code change affecting architecture:

```powershell
python tools/arch-commit.py --agent PM --file "oce/backend/field_core/resonance_engine.py" --change "Added resonance measurement"
```

This:
1. Verifies the file exists
2. Checks alignment between claimed change and actual code
3. Updates architecture diagrams
4. Logs the change to `system-arch/arch-changes.jsonl`

### Git Discipline

```powershell
# After fixes
git add <files>
git commit -m "PM: <description>"
git push origin master
```

### Progress Sync

```powershell
# After completing significant work
python tools/progress-sync.py --force
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Run tests | `python -m pytest srrs_opc/tests/ -v` |
| Check style | `python -m pytest --co -q` |
| Install package | `uv pip install <package>` |
| Arch commit | `python tools/arch-commit.py --agent PM --file "<f>" --change "<d>"` |
| Progress sync | `python tools/progress-sync.py --force` |
| Terminal cleanup | `python tools/terminal_cleanup.py --force` |
| Self heal | `python tools/self_heal.py` |
