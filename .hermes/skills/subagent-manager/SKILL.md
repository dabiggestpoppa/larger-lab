---
name: subagent-manager
description: Subagent management with sidechain file pattern. Subagents return only summaries to parent; full transcripts go to sidechain files.
---

# Subagent Manager Skill

Manages subagent execution with sidechain file pattern to prevent parent context pollution.

## Usage

```python
from tools.subagent_manager import SubagentManager, run_subagent

# Method 1: Use the manager directly
mgr = SubagentManager(sidechain_dir="progress/sidechains")
result = mgr.run_subagent(task="Run Phase 2 tests", agent="HR")

# Method 2: Convenience function
result = run_subagent(task="Evaluate GitHub repo", agent="PM")

# Access results
print(result.summary)          # Short text for parent context
print(result.sidechain_path)   # Full transcript file path
```

## Sidechain File Pattern

- Subagents return ONLY summary text to the parent
- Full transcripts (every tool call, every response) go to sidechain files
- Sidechain files are JSONL format in `progress/sidechains/`

## File Format

```
progress/sidechains/
  HR_20260516_1430_a1b2c3d4.jsonl
  PM_20260516_1435_e5f6g7h8.jsonl
```

Each file contains:
- `header` — run metadata (agent, task, timestamp)
- `turn` — each model call + tool result
- `result` — final summary

## When to Use

- When delegating complex tasks to subagents
- When subagent output would pollute parent context
- When you need full audit trail of subagent actions
