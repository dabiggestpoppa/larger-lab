# 🔧 Agent Harness SOP — Standard Operating Procedure

> Adapted from CLI-Anything's HARNESS.md and VILA-Lab's Claude Code analysis.
> This is the definitive guide for building agent-native tools in our workspace.

---

## Core Philosophy

**The agent loop is simple. The harness around it is where the real engineering lives.**

- 98.4% of agent infrastructure is deterministic: permission gates, tool routing, context compaction, recovery logic
- 1.6% is AI decision logic
- The model reasons. The harness enforces.

---

## 7-Phase Tool Building Pipeline

### Phase 1: Codebase Analysis
1. **Identify the backend engine** — Find the core library/framework
2. **Map GUI actions to API calls** — Every action = a function call
3. **Identify the data model** — File formats, project state representation
4. **Find existing CLI tools** — These are building blocks
5. **Catalog the command/undo system** — Command pattern = CLI operations

### Phase 2: CLI Architecture Design
1. **Choose interaction model:**
   - Stateful REPL for interactive sessions
   - Subcommand CLI for one-shot operations
   - **Both** (recommended)
2. **Define command groups** matching logical domains
3. **Design the state model** — What persists between commands?
4. **Plan output format:**
   - Human-readable (tables, colors) for interactive use
   - Machine-readable (`--json`) for agent consumption

### Phase 3: Implementation
1. Start with the data layer
2. Add probe/info commands first
3. Add mutation commands
4. Add backend integration
5. Add rendering/export
6. Add session management (undo/redo)
7. Add REPL with unified skin

### Phase 4: Test Planning
1. Unit tests for every core function
2. E2E tests with real files and software
3. CLI subprocess verification
4. Edge cases and error handling

### Phase 5: Test Writing
1. `test_core.py` — unit tests with synthetic data
2. `test_e2e.py` — real software invocation + output verification
3. `test_cli.py` — installed command via subprocess

### Phase 6: Documentation
1. `SKILL.md` — agent skill discovery (YAML frontmatter + usage)
2. `TEST.md` — test plan and results
3. Architecture SOP specific to the tool

### Phase 7: Publishing
1. `setup.py` for pip install
2. Install to PATH
3. Register in skill registry

---

## 5-Layer Context Compaction

Before every model call, run these layers cheapest first:

| Layer | Strategy | Trigger |
|-------|----------|---------|
| 1 | Budget Reduction — per-message caps | Always active |
| 2 | Snip — trim older history | Feature-gated |
| 3 | Microcompact — cache-aware compression | Always (time-based) |
| 4 | Context Collapse — virtual projection | Feature-gated |
| 5 | Auto-Compact — full model summary | Last resort |

See `tools/context_compaction.py` for implementation.

---

## 7 Safety Layers

A request must pass through **all** applicable layers:

1. **Tool pre-filtering** — Blanket-denied tools removed from model's view
2. **Deny-first rule evaluation** — Deny always overrides allow
3. **Permission mode constraints** — Active mode determines baseline
4. **Auto-mode classifier** — Separate safety evaluation
5. **Shell sandboxing** — Filesystem + network isolation
6. **Non-restoration on resume** — Permissions never persist across sessions
7. **Hook-based interception** — Pre-tool-use hooks can block actions

---

## 4 Extension Mechanisms (Ordered by Context Cost)

| Mechanism | Cost | Use Case |
|-----------|------|----------|
| **Hooks** | Zero | Event interception, logging |
| **Skills** | Low | Task-specific capabilities |
| **Plugins** | Medium | Feature extensions |
| **MCP** | High | External tool integration |

---

## Subagent Pattern

**Key principle:** Subagents return ONLY summary text to the parent.
Full transcripts live in sidechain files.

```
progress/sidechains/
  HR_20260516_1430_a1b2c3d4.jsonl
  PM_20260516_1435_e5f6g7h8.jsonl
```

Each sidechain file is JSONL with:
- `header` — run metadata
- `turn` — each model call + tool result
- `result` — final summary

See `tools/subagent_manager.py` for implementation.

---

## Tool Output Standard

Every tool command MUST support `--json` flag:

```bash
# Human-readable (default)
python tool.py command --option value

# Machine-readable (for agents)
python tool.py command --option value --json
```

JSON output format:
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "duration_ms": 123,
    "tokens_used": 456
  }
}
```

---

## Session Management

All stateful tools use JSON session files with exclusive locking:

```python
import fcntl

def _locked_save_json(path, data):
    with open(path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        f.truncate()
        json.dump(data, f)
        fcntl.flock(f, fcntl.LOCK_UN)
```

---

## Critical Lessons

1. **Use the real software** — No toy implementations. Call actual backends.
2. **Verify output** — Never trust exit code 0. Check magic bytes, structure, content.
3. **Timecode precision** — Use `round()` not `int()` for frame rates.
4. **Filter translation** — Watch for duplicate merging, parameter space differences.
5. **Session locking** — Prevent concurrent write corruption.
6. **Graceful degradation** — If backend missing, fail with clear install instructions.
