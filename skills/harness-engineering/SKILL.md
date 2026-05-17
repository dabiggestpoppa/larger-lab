---
name: harness-engineering
description: Comprehensive harness engineering skill — build closed-loop working systems for AI agents using hooks, rules, boundaries, and verification loops. Based on Anthropic/OpenAI/WalkingLabs research.
---

# Harness Engineering

> **Core Principle**: A harness establishes a closed-loop working system for the model. The model reasons; the harness enforces.

---

## 1. What Is a Harness

A harness is everything **around** the model — the infrastructure that transforms raw model output into reliable, verifiable, bounded agent behavior. It is NOT the model itself. It is NOT a prompt. It is the deterministic control layer that makes agent systems production-grade.

### The 98.4 / 1.6 Rule

Analysis of Claude Code and similar agent systems reveals:
- **98.4% of agent infrastructure is deterministic** — hooks, tools, rules, sandboxes, verification loops
- **1.6% is AI decision logic** — the model's actual reasoning and choice-making

This means the quality of an agent system is almost entirely determined by its harness, not by the model's intelligence. A mediocre model with a great harness outperforms a great model with a mediocre harness.

### Harness vs Prompt

| Aspect | Prompt | Harness |
|--------|--------|---------|
| Enforcement | Advisory | Mandatory |
| Execution | Model-dependent | Deterministic |
| Observability | Opaque | Logged, auditable |
| Verification | None | Built-in |
| Recovery | Manual | Automated |

### Core Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      HARNESS EVENT LIFECYCLE                        │
│                                                                     │
│  event ──▶ optional matcher/filter ──▶ handler ──▶ outcome          │
│                                                                     │
│  Examples:                                                          │
│  "user sends message" ──▶ intent filter ──▶ route to agent ──▶ reply│
│  "agent calls tool" ──▶ policy check ──▶ allow/block/modify ──▶ run │
│  "agent finishes turn" ──▶ quality gate ──▶ accept/retry ──▶ done   │
└─────────────────────────────────────────────────────────────────────┘
```

Every harness event follows this pattern:
1. **Event** — something happens (user input, tool call, session start, etc.)
2. **Matcher/Filter** — optional: does this event match a rule? Should it be intercepted?
3. **Handler** — deterministic logic that processes the event
4. **Outcome** — the result: allow, block, modify, log, retry, escalate

### What a Harness Provides

- **Constrained behavior** — explicit rules and boundaries the model cannot override
- **Context continuity** — state maintained across long-running, multi-session tasks
- **Premature completion prevention** — agents cannot declare victory without verification
- **Observable runtime** — every decision logged, auditable, replayable
- **Self-healing** — automatic retry, repair, and escalation on failure
- **Bounded autonomy** — agents operate freely within defined guardrails

---

## 2. Harness Patterns

### 2.1 SessionStart — Context Loading

**Purpose**: Initialize the agent's working context before it begins reasoning.

**When it fires**: At the beginning of every new session or session resume.

**What it does**:
- Loads project conventions (AGENTS.md, SOUL.md, project rules)
- Loads environment facts (OS, installed tools, available services)
- Loads relevant memory from previous sessions
- Loads runbooks for the current task domain
- Sets up working directories and temp space
- Validates that required tools and services are available

**Example logic**:
```
ON session_start:
  1. Read AGENTS.md → extract project rules
  2. Read progress files → build task state
  3. Check tool availability → fail fast if missing
  4. Load memory search results for current task
  5. Inject context summary into agent's system prompt
  6. Log session start with context fingerprint
```

**Why it matters**: Without SessionStart, every session begins from scratch. The agent wastes tokens re-discovering context, makes inconsistent decisions, and loses continuity with previous work.

---

### 2.2 UserPromptSubmit — Input Inspection & Routing

**Purpose**: Inspect, augment, and route user input before the model processes it.

**When it fires**: After the user submits a message, before the model sees it.

**What it does**:
- Inspects the raw prompt for intent classification
- Adds relevant context (project state, recent memory, environment facts)
- Routes to the correct agent or sub-agent based on intent
- Blocks or transforms unsafe/ambiguous prompts
- Injects task-specific instructions based on context

**Example logic**:
```
ON user_prompt_submit:
  1. Classify intent (task request, question, config change, etc.)
  2. If intent matches known task pattern → inject task template
  3. If prompt references a project → load project context
  4. If prompt is ambiguous → add clarification request to context
  5. If prompt contains unsafe instructions → block and explain
  6. Route to appropriate handler agent
```

**Why it matters**: Raw user prompts are often underspecified. UserPromptSubmit enriches them with context the user assumes the agent already knows, reducing misalignment and rework.

---

### 2.3 PreToolUse — Tool Call Policy Enforcement

**Purpose**: Inspect and control tool calls before they execute.

**When it fires**: After the model decides to call a tool, but before the tool actually runs.

**What it does**:
- Checks tool calls against a denylist (dangerous commands, off-limits paths)
- Checks tool calls against an allowlist (only approved tools for this task)
- Modifies tool parameters (e.g., add safety flags, constrain scope)
- Blocks tool calls that violate policy
- Logs all tool calls for audit
- Rate-limits expensive or dangerous operations

**Example logic**:
```
ON pre_tool_use(tool_name, params):
  1. If tool_name in denylist → BLOCK, return error message
  2. If params contain dangerous patterns (rm -rf, DROP TABLE, etc.) → BLOCK
  3. If tool is "exec" and command writes to protected path → BLOCK
  4. If tool is "exec" and command not in allowlist → REQUIRE_APPROVAL
  5. If rate limit exceeded for this tool → QUEUE or BLOCK
  6. Log: {agent, tool, params, decision, timestamp}
  7. If allowed → pass through unchanged
```

**Why it matters**: This is the primary safety layer. The model may hallucinate dangerous commands, misunderstand scope, or attempt operations that violate project policy. PreToolUse is the last line of defense before execution.

---

### 2.4 PostToolUse — Validation & Verification

**Purpose**: Run validation after successful tool calls.

**When it fires**: After a tool call completes successfully.

**What it does**:
- Runs tests after code changes (lint, unit tests, type checks)
- Scans output for secrets, credentials, or sensitive data
- Validates that the tool produced the expected output format
- Triggers downstream actions (e.g., run formatter after file write)
- Logs results for audit and learning
- Detects and flags unexpected side effects

**Example logic**:
```
ON post_tool_use(tool_name, params, result):
  1. If tool_name == "write" or "edit":
     a. Run linter on modified file
     b. Run related unit tests
     c. Check for syntax errors
     d. If tests fail → notify agent with error details
  2. If tool_name == "exec":
     a. Check exit code
     b. Scan stdout/stderr for error patterns
     c. If error detected → capture and relay to agent
  3. Log: {tool, params, result_summary, validation_status}
```

**Why it matters**: PostToolUse catches errors immediately, before the agent proceeds on a broken foundation. It turns every tool call into a verified step rather than a blind mutation.

---

### 2.5 Stop — Completion Gate

**Purpose**: Check whether the agent should be allowed to finish its turn.

**When it fires**: When the agent signals it is done (or about to exceed token/context limits).

**What it does**:
- Checks whether all success criteria have been met
- Verifies that required tests pass
- Checks for incomplete work (TODOs, placeholders, stubs)
- Prevents premature "done" declarations
- Forces the agent to self-reflect before finishing
- Can force a retry or continuation if quality gates fail

**Example logic**:
```
ON stop_requested:
  1. Check: Did the agent run required tests?
  2. Check: Are there remaining TODO/FIXME/placeholder items?
  3. Check: Does output match the requested format?
  4. Check: Were all sub-agents completed successfully?
  5. If any check fails → BLOCK stop, return agent to work with feedback
  6. If all checks pass → ALLOW stop, trigger SessionEnd
  7. Log: {checks_passed, checks_failed, final_decision}
```

**Why it matters**: Agents are eager to declare completion. Without a Stop gate, agents routinely claim tasks are done when tests fail, edge cases are unhandled, or the output doesn't match requirements.

---

### 2.6 SessionEnd — Audit & Cleanup

**Purpose**: Finalize session state, write logs, and clean up.

**When it fires**: After the agent's turn is complete and the Stop gate has passed.

**What it does**:
- Writes audit log of the full session (events, decisions, tool calls)
- Flushes metrics (token usage, tool call counts, error rates)
- Updates progress files with current state
- Summarizes session for memory compression
- Cleans up temp files and resources
- Triggers any downstream notifications or syncs

**Example logic**:
```
ON session_end:
  1. Write session audit log → logs/sessions/{session_id}.jsonl
  2. Update progress file → progress/{agent}-progress.md
  3. Compress session summary → memory/{agent}-memory.md
  4. Clean temp files → remove /tmp/agent-{session_id}/*
  5. Sync state → run progress-sync if threshold met
  6. Log: {session_id, duration, tokens_used, tools_called, outcome}
```

**Why it matters**: Without SessionEnd, sessions leave no trace. Debugging becomes impossible, progress is lost, and the system cannot learn from its own history.

---

## 3. Harness Design Principles

### Principle 1: Constrain with Explicit Rules

Never rely on the model to "do the right thing." Every boundary must be explicit, enforced, and auditable.

```yaml
# Good: Explicit, enforceable rules
denylist:
  - "rm -rf"
  - "DROP TABLE"
  - "git push --force"
protected_paths:
  - "/etc/"
  - ".env"
  - "secrets/"
max_file_size: "10MB"
max_execution_time: 300s

# Bad: Advisory language the model can ignore
guidelines:
  - "Be careful with destructive commands"
  - "Don't modify system files"
```

### Principle 2: Maintain Context Across Sessions

Agents wake up fresh each session. The harness must provide continuity:

- **Progress files** — current state, next steps, blockers
- **Memory search** — semantic recall of past decisions and context
- **Session summaries** — compressed history of what happened and why
- **Environment facts** — what's installed, what's running, what's broken

### Principle 3: Stop Premature Completion

The #1 failure mode in agent systems is the agent declaring victory too early. Countermeasures:

- **Stop hooks** that verify quality gates before allowing completion
- **PostToolUse hooks** that run tests after every code change
- **Explicit success criteria** defined before work begins
- **Self-reflection prompts** that force the agent to check its own work

### Principle 4: Verify with Full-Pipeline Tests

Unit tests alone are not enough. The harness should verify:

1. **Build** — code compiles/runs without errors
2. **Unit tests** — individual functions behave correctly
3. **Integration tests** — components work together
4. **Linting** — code meets style/format standards
5. **Manual inspection** — spot-check critical logic
6. **Regression tests** — existing functionality still works

### Principle 5: Make Runtime Observable

Every decision, tool call, and outcome must be logged:

```json
{
  "timestamp": "2026-05-16T22:00:00Z",
  "session_id": "abc123",
  "agent": "CC",
  "event": "tool_call",
  "tool": "exec",
  "params": {"command": "python -m pytest"},
  "outcome": "success",
  "duration_ms": 4500,
  "exit_code": 0
}
```

### Principle 6: Prompts for Guidance, Hooks for Enforcement

| Use Prompts For | Use Hooks For |
|----------------|---------------|
| Style preferences | "Always run tests before declaring done" |
| Domain knowledge | "Never execute rm -rf" |
| Approach suggestions | "Log every tool call" |
| Examples and patterns | "Block writes to /etc/" |
| Context and background | "Load project rules at session start" |

**Rule of thumb**: If the word in the rule is "always," "never," "block," "record," "run," or "verify" — it belongs in a hook, not a prompt.

---

## 4. Implementation Guide

### 4.1 Hooks in OpenClaw

OpenClaw supports hooks through the `tools/agent-hooks/` directory. Each hook is a Python script that receives JSON input and returns JSON output.

**Hook directory structure**:
```
tools/agent-hooks/
├── session_start/
│   └── load_context.py
├── pre_tool_use/
│   ├── command_denylist.py
│   └── path_protection.py
├── post_tool_use/
│   ├── run_tests.py
│   └── lint_check.py
├── stop/
│   └── quality_gate.py
└── session_end/
    └── audit_logger.py
```

### 4.2 Hook Script Template

Every hook follows the same pattern: read JSON from stdin, process, write JSON to stdout.

```python
#!/usr/bin/env python3
"""Hook: {hook_name}
Fires: {when}
Purpose: {what_it_does}
"""

import json
import sys

def main():
    # Read event data from stdin
    event = json.loads(sys.stdin.read())
    
    # Extract relevant fields
    session_id = event.get("session_id", "unknown")
    agent = event.get("agent", "unknown")
    tool_name = event.get("tool_name", "")
    params = event.get("params", {})
    
    # --- Hook logic goes here ---
    decision = "allow"  # allow | block | modify
    reason = ""
    modified_params = params
    
    if tool_name == "exec":
        command = params.get("command", "")
        denylist = ["rm -rf", "DROP TABLE", "git push --force"]
        for pattern in denylist:
            if pattern in command:
                decision = "block"
                reason = f"Command matches denylist pattern: {pattern}"
                break
    
    # Write result to stdout
    result = {
        "decision": decision,
        "reason": reason,
        "modified_params": modified_params if decision == "modify" else None,
        "log": {
            "hook": "command_denylist",
            "session_id": session_id,
            "agent": agent,
            "tool": tool_name,
            "decision": decision
        }
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### 4.3 Testing Hooks Locally

Test hooks in isolation before deploying:

```bash
# Test PreToolUse hook
echo '{"tool_name":"exec","params":{"command":"rm -rf /tmp/test"},"agent":"CC","session_id":"test-123"}' | python tools/agent-hooks/pre_tool_use/command_denylist.py

# Expected output:
# {"decision":"block","reason":"Command matches denylist pattern: rm -rf","modified_params":null,"log":{...}}

# Test with safe command
echo '{"tool_name":"exec","params":{"command":"python -m pytest"},"agent":"CC","session_id":"test-123"}' | python tools/agent-hooks/pre_tool_use/command_denylist.py

# Expected output:
# {"decision":"allow","reason":"","modified_params":null,"log":{...}}
```

### 4.4 Common Pitfalls and Anti-Patterns

| Pitfall | Why It's Bad | Fix |
|---------|-------------|-----|
| Hooks that are too permissive | Defeats the purpose — agent bypasses constraints | Start restrictive, relax only when needed |
| Hooks that are too restrictive | Agent can't get anything done | Log blocked actions, analyze patterns, tune |
| Hooks with no logging | Can't debug why something was blocked/allowed | Every hook must emit a log entry |
| Hooks that silently modify params | Agent doesn't know its request was changed | Always include `reason` in the response |
| Hooks with unbounded execution time | Slow hooks block the entire agent | Set timeouts on all hook operations |
| Hooks that depend on external services | Network failure = hook failure = agent stuck | Make hooks self-contained or fail open with logging |
| Putting business logic in prompts | Model can ignore prompts | Move enforcement to hooks |
| Not testing hooks in isolation | Hook bugs manifest as mysterious agent failures | Unit test every hook with allow/block/modify cases |

---

## 5. Templates

### 5.1 PreToolUse Hook — Command Denylist Validation

```python
#!/usr/bin/env python3
"""PreToolUse Hook: Command Denylist Validation
Blocks dangerous commands before execution.
"""

import json
import sys
import re

# Configure denylist: list of (pattern, description) tuples
DENYLIST = [
    (r"rm\s+-rf\s+/", "Recursive root deletion"),
    (r"rm\s+-rf\s+~\s", "Recursive home deletion"),
    (r"DROP\s+TABLE", "SQL table drop"),
    (r"git\s+push\s+--force", "Force push"),
    (r":\(\)\s*\{.*\}\s*;\s*:", "Fork bomb"),
    (r"mkfs\.", "Filesystem format"),
    (r"dd\s+if=.*of=/dev/", "Direct disk write"),
]

# Protected paths that cannot be written to
PROTECTED_PATHS = [
    "/etc/",
    "/sys/",
    "/proc/",
    "C:\\Windows\\System32",
]

def main():
    event = json.loads(sys.stdin.read())
    tool_name = event.get("tool_name", "")
    params = event.get("params", {})
    session_id = event.get("session_id", "unknown")
    agent = event.get("agent", "unknown")

    decision = "allow"
    reason = ""

    if tool_name == "exec":
        command = params.get("command", "")

        # Check command denylist
        for pattern, description in DENYLIST:
            if re.search(pattern, command, re.IGNORECASE):
                decision = "block"
                reason = f"BLOCKED: {description} (pattern: {pattern})"
                break

        # Check for shell injection patterns
        if decision == "allow":
            dangerous_chains = ["; rm", "&& rm", "| rm", "`rm", "$(rm"]
            for chain in dangerous_chains:
                if chain in command:
                    decision = "block"
                    reason = f"BLOCKED: Potential shell injection: {chain}"
                    break

    elif tool_name in ("write", "edit"):
        path = params.get("path", "")
        for protected in PROTECTED_PATHS:
            if path.startswith(protected):
                decision = "block"
                reason = f"BLOCKED: Write to protected path: {protected}"
                break

    result = {
        "decision": decision,
        "reason": reason,
        "log": {
            "hook": "command_denylist",
            "session_id": session_id,
            "agent": agent,
            "tool": tool_name,
            "decision": decision,
            "reason": reason
        }
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### 5.2 PostToolUse Hook — Test Runner

```python
#!/usr/bin/env python3
"""PostToolUse Hook: Test Runner
Runs relevant tests after file modifications.
"""

import json
import sys
import subprocess
import os

def main():
    event = json.loads(sys.stdin.read())
    tool_name = event.get("tool_name", "")
    params = event.get("params", {})
    result = event.get("result", {})
    session_id = event.get("session_id", "unknown")
    agent = event.get("agent", "unknown")

    validation_passed = True
    validation_output = ""
    tests_run = []

    if tool_name in ("write", "edit"):
        file_path = params.get("path", "")
        file_dir = os.path.dirname(file_path)
        file_ext = os.path.splitext(file_path)[1]

        # Python files: run pytest on related tests
        if file_ext == ".py":
            test_dir = os.path.join(file_dir, "tests")
            if os.path.exists(test_dir):
                try:
                    proc = subprocess.run(
                        ["python", "-m", "pytest", test_dir, "-v", "--tb=short"],
                        capture_output=True, text=True, timeout=60,
                        cwd=file_dir if file_dir else "."
                    )
                    tests_run.append(f"pytest {test_dir}")
                    validation_passed = proc.returncode == 0
                    validation_output = proc.stdout[-500:] + proc.stderr[-500:]
                except subprocess.TimeoutExpired:
                    validation_passed = False
                    validation_output = "Test execution timed out (60s)"
                except FileNotFoundError:
                    tests_run.append("pytest not found, skipped")

        # JavaScript/TypeScript: run npm test
        if file_ext in (".js", ".ts", ".jsx", ".tsx"):
            if os.path.exists(os.path.join(file_dir, "package.json")):
                try:
                    proc = subprocess.run(
                        ["npm", "test", "--", "--testPathPattern", file_path],
                        capture_output=True, text=True, timeout=60,
                        cwd=file_dir if file_dir else "."
                    )
                    tests_run.append(f"npm test")
                    validation_passed = proc.returncode == 0
                    validation_output = proc.stdout[-500:] + proc.stderr[-500:]
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    tests_run.append("npm test skipped")

    output = {
        "validation_passed": validation_passed,
        "tests_run": tests_run,
        "output": validation_output,
        "log": {
            "hook": "test_runner",
            "session_id": session_id,
            "agent": agent,
            "tool": tool_name,
            "file": params.get("path", ""),
            "passed": validation_passed
        }
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### 5.3 SessionStart Hook — Context Loader

```python
#!/usr/bin/env python3
"""SessionStart Hook: Context Loader
Loads project context, memory, and environment facts at session start.
"""

import json
import sys
import os
import glob

def load_file_if_exists(path, max_lines=100):
    """Load a file, returning its content truncated to max_lines."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[:max_lines]
            return "".join(lines)
    except (FileNotFoundError, PermissionError):
        return None

def main():
    event = json.loads(sys.stdin.read())
    session_id = event.get("session_id", "unknown")
    agent = event.get("agent", "unknown")
    workspace = event.get("workspace", ".")

    context_parts = []
    loaded_files = []
    warnings = []

    # Load core project files
    core_files = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md"]
    for fname in core_files:
        content = load_file_if_exists(os.path.join(workspace, fname))
        if content:
            context_parts.append(f"## {fname}\n{content}")
            loaded_files.append(fname)
        else:
            warnings.append(f"Missing: {fname}")

    # Load agent progress file
    progress_path = os.path.join(workspace, "progress", f"{agent}-progress.md")
    content = load_file_if_exists(progress_path, max_lines=50)
    if content:
        context_parts.append(f"## Current Progress\n{content}")
        loaded_files.append(f"progress/{agent}-progress.md")

    # Load recent team chat (last 20 lines)
    chat_path = os.path.join(workspace, "shared-conversations", "team-chat.md")
    content = load_file_if_exists(chat_path, max_lines=20)
    if content:
        context_parts.append(f"## Recent Team Chat\n{content}")
        loaded_files.append("shared-conversations/team-chat.md")

    # Environment facts
    env_facts = {
        "workspace": workspace,
        "os": os.name,
        "python_path": sys.executable,
        "cwd": os.getcwd(),
    }
    context_parts.append(f"## Environment\n```json\n{json.dumps(env_facts, indent=2)}\n```")

    output = {
        "context": "\n\n".join(context_parts),
        "loaded_files": loaded_files,
        "warnings": warnings,
        "log": {
            "hook": "context_loader",
            "session_id": session_id,
            "agent": agent,
            "files_loaded": len(loaded_files),
            "warnings": len(warnings)
        }
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### 5.4 SessionEnd Hook — Audit Logger

```python
#!/usr/bin/env python3
"""SessionEnd Hook: Audit Logger
Writes session audit log and updates progress files.
"""

import json
import sys
import os
from datetime import datetime, timezone

def main():
    event = json.loads(sys.stdin.read())
    session_id = event.get("session_id", "unknown")
    agent = event.get("agent", "unknown")
    workspace = event.get("workspace", ".")
    duration_seconds = event.get("duration_seconds", 0)
    tokens_used = event.get("tokens_used", 0)
    tool_calls = event.get("tool_calls", [])
    outcome = event.get("outcome", "unknown")
    summary = event.get("summary", "")

    # Build audit entry
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "agent": agent,
        "duration_seconds": duration_seconds,
        "tokens_used": tokens_used,
        "tool_call_count": len(tool_calls),
        "tools_used": list(set(tc.get("tool", "unknown") for tc in tool_calls)),
        "outcome": outcome,
        "summary": summary
    }

    # Write to session audit log
    log_dir = os.path.join(workspace, "logs", "sessions")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{session_id}.jsonl")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")

    # Append to agent's daily summary
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = os.path.join(workspace, "logs", f"daily-{today}.jsonl")
    with open(daily_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")

    output = {
        "logged": True,
        "log_path": log_path,
        "daily_path": daily_path,
        "log": {
            "hook": "audit_logger",
            "session_id": session_id,
            "agent": agent,
            "outcome": outcome,
            "tool_calls": len(tool_calls),
            "tokens": tokens_used
        }
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

---

## Quick Reference

| Hook | Fires When | Primary Purpose |
|------|-----------|-----------------|
| `SessionStart` | Session begins | Load context, validate environment |
| `UserPromptSubmit` | User sends message | Inspect, enrich, route input |
| `PreToolUse` | Model calls a tool | Enforce policy, block dangerous calls |
| `PostToolUse` | Tool call completes | Run tests, validate output |
| `Stop` | Agent wants to finish | Quality gates, prevent premature done |
| `SessionEnd` | Session completes | Audit log, cleanup, state sync |

## Related Skills

- `agent-harness-sop` — 7-phase tool building pipeline
- `context-compaction` — context management strategies
- `subagent-manager` — subagent orchestration
- `create-tool` — building agent-native tools
