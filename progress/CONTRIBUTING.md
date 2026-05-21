# 🤝 Contributing to Larger-Lab

> **Last Updated:** 2026-05-18
> **Maintainer:** dabiggestpoppa | **Branch:** master

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [How to Add a New V3 Module](#how-to-add-a-new-v3-module)
4. [How to Add Tests](#how-to-add-tests)
5. [Code Review Process](#code-review-process)
6. [Agent Onboarding](#agent-onboarding)
7. [Communication Protocol](#communication-protocol)
8. [Architecture Rules](#architecture-rules)

---

## Getting Started

### Clone and Install
```bash
git clone https://github.com/dabiggestpoppa/larger-lab.git
cd larger-lab

# Create virtual environment
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Run Tests
```bash
# Full test suite (1460 tests)
python -m pytest oce/backend/ srrs_opc/ -q

# Specific phase
python -m pytest oce/backend/resonance/tests/ -v

# With coverage
python -m pytest oce/backend/ --cov=oce.backend --cov-report=html
```

### Start the Backend
```bash
cd oce/backend
python main.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs (Swagger UI)
```

---

## Project Structure

```
larger-lab/
├── oce/                          # Operator Continuity Engine
│   ├── backend/                  # FastAPI backend
│   │   ├── resonance/            # Phase 1: Resonant Signal Substrate
│   │   ├── reconstruction/       # Phase 2: Reconstructive Continuity
│   │   ├── topology/             # Phase 3: Resonant Topology & BSP
│   │   ├── sovereign/            # Phase 4: Sovereign Instrumentation
│   │   ├── temporal/             # Phase 5: Long-Horizon Continuity
│   │   ├── introspection/        # Phase 6: Recursive Introspection
│   │   ├── multiscale/           # Phase 7: Multi-Scale Cognitive Fields
│   │   ├── coevolution/          # Phase 8: Operator Coevolution
│   │   ├── field_core/           # Phase 9: Sovereign Field Emergence
│   │   ├── phase10/              # Phase 10: Recursive Field Computation
│   │   ├── tests/                # OCE core tests
│   │   └── main.py               # FastAPI entry point
│   ├── V3_PHASE*_TASKS.md        # Phase plans
│   └── docs/                     # Documentation
├── srrs_opc/                     # SRRA-OPH substrate
│   ├── tests/                    # SRRA-OPH tests (57 tests)
│   └── *.py                      # Core modules
├── docs/                         # Project documentation
│   ├── API_REFERENCE.md          # API endpoint reference
│   ├── MODULE_GUIDE.md           # Per-phase module guide
│   └── QUALITY_REVIEW.md         # Codebase quality assessment
├── tools/                        # Operator tools and CLIs
├── shared-conversations/         # Team coordination
│   └── team-chat.md              # Team chat
├── progress/                     # Agent progress files
├── memory-bank/                  # Error database and solutions
├── AGENTS.md                     # Agent team manifest
├── CLAUDE.md                     # 12-rule behavioral contract
├── ARCHITECTURE.md               # System architecture guide
├── PRINCIPLES.md                 # Core design principles
├── CODEMAP.md                    # Code navigation map
└── README.md                     # Project overview
```

---

## How to Add a New V3 Module

### Step 1: Create the Module File
```python
"""
V3 Phase X — [Module Name]
[Brief description of what this module does and why it exists.]
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MyModuleClass:
    """Docstring explaining the class."""
    # Implementation

class MyModuleEngine:
    """
    Main engine class.
    
    [Detailed description of the engine's responsibility.]
    """
    def __init__(self):
        pass
    
    def my_method(self) -> ResultType:
        """Method docstring."""
        pass
```

### Step 2: Add to `__init__.py`
```python
# In the phase's __init__.py
from .my_module import MyModuleClass, MyModuleEngine

__all__.extend(["MyModuleClass", "MyModuleEngine"])
```

### Step 3: Register API Endpoints (if applicable)
```python
# In the phase's API file (e.g., resonance_api.py)
def register_my_endpoints(app: FastAPI) -> None:
    @app.get("/my-endpoint")
    async def get_my_data():
        return {"data": "value"}
```

### Step 4: Add Tests
```python
# In tests/test_my_module.py
import pytest
from oce.backend.phasex.my_module import MyModuleClass, MyModuleEngine

class TestMyModuleClass:
    def test_creation(self):
        obj = MyModuleClass()
        assert obj is not None
    
    def test_behavior(self):
        obj = MyModuleClass()
        result = obj.my_method()
        assert result.expected == True
```

### Step 5: Update Documentation
- Add entry to `docs/MODULE_GUIDE.md`
- Add API endpoints to `docs/API_REFERENCE.md`
- Update `CODEMAP.md` with new module path

---

## How to Add Tests

### Testing Philosophy
Tests verify **intent**, not just behavior. Every test must encode WHY the behavior matters.

### Test Structure
```python
class TestFeatureName:
    """Tests for [feature] — [what invariant it verifies]."""
    
    def test_basic_creation(self):
        """Object should initialize with sensible defaults."""
        obj = MyClass()
        assert obj.default_value == expected_default
    
    def test_behavior_under_condition(self):
        """When [condition], should [expected behavior]."""
        obj = MyClass()
        result = obj.method(condition)
        assert result.meets_invariant()
    
    def test_stability_under_perturbation(self):
        """System should recover from [perturbation]."""
        obj = MyClass()
        obj.perturb()
        assert obj.is_stable() or obj.repairs()
```

### Running Tests
```bash
# All tests
python -m pytest oce/backend/ srrs_opc/ -q

# Specific module
python -m pytest oce/backend/resonance/tests/test_signal_packet.py -v

# With coverage
python -m pytest --cov=oce.backend --cov-report=term-missing
```

### Test Naming Convention
- `test_<feature>_<condition>` — e.g., `test_signal_packet_high_entropy`
- Test classes: `Test<ClassName>` — e.g., `TestSignalPacket`
- Test files: `test_<module_name>.py` — e.g., `test_signal_packet.py`

---

## Code Review Process

### For Human Contributors
1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes, add tests, run full suite
3. Create PR against `master`
4. CC (Claude Code) reviews architecture
5. AS (Assistant Manager) reviews quality and test coverage
6. PM (Polymorph) reviews debug tool compatibility
7. Merge after all approvals

### For AI Agents
1. Post intended changes to `shared-conversations/team-chat.md`
2. CC approves the plan
3. Implement changes
4. Run tests, update progress file
5. Post completion summary to team-chat
6. CC reviews and merges

### Review Checklist
- [ ] Code follows CLAUDE.md 12-rule contract
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes and methods
- [ ] Tests cover happy path, edge cases, and error cases
- [ ] No global state (every node self-stabilizes)
- [ ] Repair before expansion (fix bugs before adding features)
- [ ] Bounded sovereignty (no observer needs full global state)

---

## Agent Onboarding

New agents joining the team should:

1. **Read the manifest files** (in order):
   - `AGENTS.md` — Team roster and rules
   - `CLAUDE.md` — 12-rule behavioral contract
   - `ARCHITECTURE.md` — System architecture
   - `PRINCIPLES.md` — Core design principles

2. **Read your role's progress file:**
   - `progress/assistant-progress.md` (AS)
   - `progress/polymorph-progress.md` (PM)
   - `progress/rl-progress.md` (RL)

3. **Read the team chat:**
   - `shared-conversations/team-chat.md` — Latest coordination

4. **Read the memory bank:**
   - `memory-bank/errors-and-solutions.md` — Known issues
   - `memory-bank/error-db.json` — Error database

5. **Introduce yourself** in team-chat.md with:
   - Your role and capabilities
   - Your first task assignment
   - Any blockers or questions

---

## Communication Protocol

### Team Chat (`shared-conversations/team-chat.md`)
- All agents post here for coordination
- Use format: `[TAG] Date — Message`
- Tags: `[CC]`, `[AS]`, `[PM]`, `[RL]`, `[OC2]`
- Keep entries concise and actionable

### Progress Files (`progress/*.md`)
- Each agent maintains their own progress file
- Update after every significant edit
- Format: Date, task, status, blockers

### Memory Sync
- `memory-bank/errors-and-solutions.md` — Log errors and fixes
- `memory-bank/error-db.json` — Structured error database
- `workspace-state.md` — Cross-agent state relay

### Error Handling
- Errors >2 attempts → log to `memory-bank/error-db.json`
- Post summary to `team-chat.md`
- Never stall silently — always log what happened

---

## Architecture Rules

### Core Principles (from PRINCIPLES.md)
1. **Field over events** — The cognitive field is primary; events are perturbations
2. **Resonance over instruction** — Computation emerges from field dynamics
3. **Topology over hierarchy** — Structure emerges from interaction patterns
4. **Repair over replacement** — Self-healing before external intervention
5. **Bounded sovereignty** — No observer needs full global state
6. **Continuity over output** — Sustained operation > isolated brilliance

### Coding Standards
- **Python 3.11+** (see `.python-version`)
- **snake_case** for functions/variables, **PascalCase** for classes
- **Type hints** on all public methods
- **Dataclasses** preferred over dicts for structured data
- **No global state** — every node self-stabilizes
- **Repair before expansion** — fix bugs before adding features
- **Test everything** — all code must have tests before advancing phases

### Forbidden Patterns
- ❌ Global mutable state
- ❌ Circular imports between phases
- ❌ Hardcoded model names (use ModelRouter)
- ❌ Emotional dependency vectors (anti-manipulation safeguard)
- ❌ Unbounded recursion (always set max_iterations)
- ❌ Silent error swallowing (always log)

### Required Patterns
- ✅ Dataclasses with `field(default_factory=...)` for mutable defaults
- ✅ `Optional[type]` for nullable fields
- ✅ `HTTPException` for API errors with proper status codes
- ✅ `logger.error()` for unexpected errors
- ✅ `@property` for computed attributes
- ✅ `__all__` in `__init__.py` for explicit exports

---

## Quick Reference

### Key Commands
```bash
# Run all tests
python -m pytest oce/backend/ srrs_opc/ -q

# Start backend
python oce/backend/main.py

# Check OC2 status
openclaw gateway probe

# View OC2 logs
Get-Content "$env:LOCALAPPDATA\Temp\openclaw\openclaw-2026-05-18.log" -Tail 20 -Wait
```

### Key Files
| File | Purpose |
|------|---------|
| `AGENTS.md` | Team manifest |
| `CLAUDE.md` | Behavioral contract |
| `ARCHITECTURE.md` | System architecture |
| `PRINCIPLES.md` | Design principles |
| `CODEMAP.md` | Code navigation |
| `docs/API_REFERENCE.md` | API endpoint reference |
| `docs/MODULE_GUIDE.md` | Per-phase module guide |
| `docs/QUALITY_REVIEW.md` | Codebase quality assessment |

---

*Last updated: 2026-05-18 | V3 All 10 Phases Complete | 1460 tests passing*
