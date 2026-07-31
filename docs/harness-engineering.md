# Harness Engineering Guide

> How to constrain agent behavior, maintain context, verify work, and make runtime observable.
> Version: 1.0 | Date: 2026-05-17

## Table of Contents

1. [What is a Harness?](#1-what-is-a-harness)
2. [Constraining Agent Behavior](#2-constraining-agent-behavior)
3. [Maintaining Context Across Sessions](#3-maintaining-context-across-sessions)
4. [Verifying Work](#4-verifying-work)
5. [Making Runtime Observable](#5-making-runtime-observable)
6. [Templates](#6-templates)

---

## 1. What is a Harness?

A **harness** is the complete set of constraints, instructions, and guardrails that shape an agent's behavior. It includes:

- **System prompt / SOUL.md** — Identity, values, operating principles
- **AGENTS.md** — Team structure, rules, phase gates
- **Skill files (SKILL.md)** — Domain-specific procedures
- **Agent hooks** — Pre/post tool use validation
- **Memory files** — Persistent context across sessions
- **Progress files** — Observable work tracking

The harness is the **boundary layer** between raw LLM capability and reliable, bounded operation.

### Harness Design Principles

1. **Explicit over implicit** — State rules clearly, don't rely on "the model should know"
2. **Constrain early** — Block bad behavior at the hook level, not after the fact
3. **Verify always** — Every code change gets tested, every session gets audited
4. **Compress memory** — Linear growth is failure; summarize aggressively
5. **Make it observable** — If you can't see what the agent did, you can't trust it

---

## 2. Constraining Agent Behavior

### 2.1 Explicit Rules

Rules must be **specific, testable, and enforceable**. Bad rules are vague.

❌ **Bad:** "Be careful with files"
✅ **Good:** "Do not edit files matching `config/*.json`, `.env`, `.phase-state.json`, or `AGENTS.md` without explicit MAD approval"

❌ **Bad:** "Test your code"
✅ **Good:** "After every Python file edit, run `python -m py_compile <file>`. After every JSON edit, validate with `json.load()`."

### 2.2 Pre-Tool-Use Hooks

Use `tools/agent-hooks/pre-tool-use-enhanced.py` to block dangerous operations:

```bash
echo '{"command": "rm -rf /", "tool_name": "exec"}' | python tools/agent-hooks/pre-tool-use-enhanced.py
# → {"allowed": false, "reason": "Command matches denylist pattern"}
```

**Protected file patterns** (require explicit approval):
- `.openclaw*.json` — Gateway config
- `config/*.{json,yaml,yml}` — Application config
- `.env` — Environment variables
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md` — Core identity files
- `*.generated.*` — Generated files
- `node_modules/`, `__pycache__/`, `.git/` — Dependencies/cache

### 2.3 Post-Tool-Use Hooks

Use `tools/agent-hooks/post-tool-use-enhanced.py` to verify changes:

```bash
echo '{"file_path": "srrs_opc/module.py", "tool_name": "edit"}' | python tools/agent-hooks/post-tool-use-enhanced.py
# → {"passed": true, "results": [...]}
```

**Automatic checks:**
- Python syntax validation (`py_compile`)
- JSON validation (`json.load`)
- YAML validation (`yaml.safe_load`)
- Markdown link check (empty links, YAML frontmatter)
- Tool call logging (all calls → `logs/tool-calls.jsonl`)

### 2.4 Stop Hooks

Use `tools/agent-hooks/stop-hook.py` to verify task completion before session end:

```bash
echo '{
  "stated_goals": ["Create memory files", "Update hooks"],
  "completed_goals": ["Create memory files", "Update hooks"],
  "files_modified": ["memory/working-memory.md", "tools/agent-hooks/pre-tool-use-enhanced.py"]
}' | python tools/agent-hooks/stop-hook.py
# → {"can_stop": true, "checks": {...}}
```

---

## 3. Maintaining Context Across Sessions

### 3.1 Memory Architecture

Use the PAI-inspired 5-file memory system:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `memory/working-memory.md` | Active tasks, in-flight state | Every session |
| `memory/episodic-memory.md` | Past events, decisions | After significant events |
| `memory/semantic-memory.md` | Facts, concepts, relationships | When new knowledge is gained |
| `memory/procedural-memory.md` | SOPs, workflows, how-to | When procedures change |
| `memory/identity-memory.md` | Identity, values, preferences | Rarely (only on MAD directive) |

### 3.2 Session Startup Protocol

Every agent session should:

1. Read `memory/working-memory.md` — What's currently happening?
2. Read last 3 entries of `memory/episodic-memory.md` — What happened recently?
3. Read `shared-conversations/team-chat.md` — What's the team doing?
4. Read own `progress/{agent}-progress.md` — What was I working on?

### 3.3 Progress Files

Each agent maintains a progress file at `progress/{agent}-progress.md`:

```markdown
# {Agent} Progress

## Current Task
- **Task:** [description]
- **Status:** 🟡 In Progress
- **Started:** YYYY-MM-DD HH:MM

## Recent Edits
| Time | File | Change |
|------|------|--------|
| HH:MM | path/to/file.py | Added function X |

## Blockers
- [Any blockers]

## Next Steps
- [What comes next]
```

### 3.4 YAML Frontmatter

All memory files use YAML frontmatter for metadata:

```yaml
---
created: 2026-05-17
updated: 2026-05-17
tags: [memory, working, active]
importance: 5
---
```

---

## 4. Verifying Work

### 4.1 Test-Driven Verification

All code must have tests before advancing phases:

```bash
# Python
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_module.py -v

# Syntax check (fast)
python -m py_compile path/to/file.py
```

### 4.2 Self-Reflection Checklist

Before marking a task complete, the agent should verify:

- [ ] All stated goals are met
- [ ] All modified files exist and are valid
- [ ] No critical errors remain
- [ ] Tests pass (if applicable)
- [ ] Progress file is updated
- [ ] Memory files are updated (if significant)
- [ ] No stale terminals left running

### 4.3 Phase Gates

Phase transitions require:

1. All tests for current phase pass
2. CC (Claude Code) approval
3. Update `.phase-state.json`
4. Update `AGENTS.md` phase status table

---

## 5. Making Runtime Observable

### 5.1 Logging

All tool calls are logged to `logs/tool-calls.jsonl`:
```json
{"timestamp": "...", "agent": "OC2", "tool_name": "edit", "file_path": "...", "success": true}
```

All session summaries are logged to `logs/session-summaries.jsonl`:
```json
{"timestamp": "...", "session_id": "...", "agent": "OC2", "stated_goals": [...], "completed_goals": [...]}
```

### 5.2 Audit Trail

The complete audit trail is:
1. `logs/tool-calls.jsonl` — Every tool call
2. `logs/session-summaries.jsonl` — Session-level summary
3. `logs/session-audit.jsonl` — Session start/end events
4. `progress/{agent}-progress.md` — Agent's own progress log
5. `shared-conversations/team-chat.md` — Team coordination

### 5.3 Monitoring

Key files to monitor:
- `logs/tool-calls.jsonl` — Look for repeated failures
- `logs/session-summaries.jsonl` — Look for incomplete sessions
- `progress/{agent}-progress.md` — Look for stale tasks
- `error-db.json` — Look for recurring errors

---

## 6. Templates

### 6.1 AGENTS.md Template

```markdown
# AGENTS.md — [Team Name]

## Team Roster
| Tag | Agent | Role |
|-----|-------|------|
| 🔵 CC | Claude Code | Overseer |

## Rules
1. Max [N] concurrent sub-agents
2. No unrestricted self-modification
3. Repair before expansion
4. All execution logged

## Memory
- Working: `memory/working-memory.md`
- Episodic: `memory/episodic-memory.md`
- Semantic: `memory/semantic-memory.md`
- Procedural: `memory/procedural-memory.md`
- Identity: `memory/identity-memory.md`
```

### 6.2 Feature List Template

```markdown
# Feature: [Name]

## Goals
- [ ] Goal 1
- [ ] Goal 2

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes
- Files: `path/to/file.py`
- Tests: `tests/test_file.py`
- Dependencies: `package-name`

## Progress
- [ ] Step 1
- [ ] Step 2
```

### 6.3 Progress File Template

```markdown
# {Agent} Progress

## Current Task
- **Task:** [description]
- **Status:** 🟡 In Progress
- **Started:** YYYY-MM-DD HH:MM

## Recent Edits
| Time | File | Change |
|------|------|--------|

## Blockers
- None

## Next Steps
- [Next action]
```

---

## References

- Agent hooks: `tools/agent-hooks/`
- Memory system: `memory/`
- Phase gates: `tools/phase-gate.py`
- Progress sync: `tools/progress-sync.py`
- Arch commits: `tools/arch-commit.py`
