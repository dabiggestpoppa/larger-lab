# Agent Hooks System — OpenClaw Skill

> **Version**: 1.0.0
> **Purpose**: Hook lifecycle, types, specification, implementation, and examples for OpenClaw's agent hook system.
> **Audience**: Agent developers, skill authors, operators extending agent behavior.

---

## Table of Contents

1. [Hook Lifecycle](#1-hook-lifecycle)
2. [Hook Types Deep Dive](#2-hook-types-deep-dive)
3. [Hook Script Specification](#3-hook-script-specification)
4. [Implementation](#4-implementation)
5. [Example Hooks](#5-example-hooks)

---

## 1. Hook Lifecycle

### 1.1 Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT LOOP LIFECYCLE                         │
│                                                                     │
│  ┌──────────────┐                                                   │
│  │ SessionStart │ ◄── Fires once when agent session initializes     │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────┐                                               │
│  │ UserPromptSubmit │ ◄── Fires when user message is received       │
│  └──────┬───────────┘                                               │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────┐                   │
│  │              TOOL INVOCATION LOOP             │ ◄── Repeats     │
│  │  ┌────────────┐                              │     per tool     │
│  │  │ PreToolUse │ ◄── Before each tool call    │     call         │
│  │  └─────┬──────┘                              │                   │
│  │        │ (approved?)                         │                   │
│  │        ▼                                      │                   │
│  │  ┌───────────┐                                │                   │
│  │  │ Tool Exec │ ◄── Actual tool execution      │                   │
│  │  └─────┬─────┘                                │                   │
│  │        │                                      │                   │
│  │        ▼                                      │                   │
│  │  ┌─────────────┐                              │                   │
│  │  │ PostToolUse │ ◄── After each tool result   │                   │
│  │  └─────┬───────┘                              │                   │
│  │        │                                      │                   │
│  │        ▼                                      │                   │
│  │  (more tools?) ──yes──┐                       │                   │
│  │        │ no           │                       │                   │
│  └────────┼──────────────┘                       │                   │
│           ▼                                                       │
│  ┌──────────┐                                                     │
│  │   Stop   │ ◄── Fires before final response is sent            │
│  └────┬─────┘                                                     │
│       │                                                           │
│       ▼                                                           │
│  ┌────────────┐                                                   │
│  │ SessionEnd │ ◄── Fires when session terminates                 │
│  └────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Hook Execution Order and Timing

Hooks fire in a strict, deterministic order:

| Order | Hook | When It Fires | Blocking? |
|-------|------|---------------|-----------|
| 1 | `SessionStart` | Once, before the first user message is processed | Yes — can prevent session init |
| 2 | `UserPromptSubmit` | Each time a user message arrives, before the agent sees it | Yes — can block/modify the prompt |
| 3 | `PreToolUse` | Before every tool invocation | Yes — can block the tool call |
| 4 | `PostToolUse` | After every tool result, before the agent processes it | Partial — can modify result |
| 5 | `Stop` | Before the agent's final response is delivered to the user | Yes — can block response |
| 6 | `SessionEnd` | When the session ends (timeout, user disconnect, agent stop) | No — fire-and-forget |

**Timing constraints:**
- `SessionStart`: Must complete within 10 seconds.
- `UserPromptSubmit`: Must complete within 5 seconds.
- `PreToolUse`: Must complete within 3 seconds per tool call.
- `PostToolUse`: Must complete within 5 seconds per tool call.
- `Stop`: Must complete within 5 seconds.
- `SessionEnd`: Must complete within 15 seconds (best-effort; session may terminate regardless).

### 1.3 Error Handling in Hooks

When a hook script fails, the system follows a **graceful degradation** policy:

| Exit Code | Meaning | Agent Behavior |
|-----------|---------|----------------|
| `0` | Success | Continue normally; use hook output if provided |
| `1` | Block | Halt the current operation; return block reason to agent |
| `2` | Error | Log the error; **continue** with default behavior (hook is bypassed) |
| Timeout | Exceeded time limit | Log warning; **continue** with default behavior |
| Crash | Unhandled exception | Log error; **continue** with default behavior |

**Key principles:**
- **Hooks never crash the agent.** A failing hook is always bypassed.
- **Block (exit 1) is intentional.** The hook is explicitly denying the operation.
- **Error (exit 2) is accidental.** The hook failed unexpectedly; the agent proceeds.
- **All hook failures are logged** to `logs/hooks.log` with timestamp, hook name, and stderr output.
- **Hook chains**: If multiple hooks are registered for the same event, they run sequentially. A block from any hook stops the chain and blocks the operation.

---

## 2. Hook Types Deep Dive

### 2.1 SessionStart

**Purpose**: Initialize the agent's working context for the session.

**When it fires**: Exactly once, after the agent process starts but before any user message is processed.

**Common use cases**:
- Load project-specific context (AGENTS.md, SOUL.md, OPERATOR_RULES.md)
- Set environment variables (API keys, feature flags, paths)
- Validate that required services are running (database, gateway, MCP servers)
- Initialize session-scoped state (counters, timers, caches)
- Load runbooks or SOPs relevant to the current project

**Input JSON**:
```json
{
  "hook": "SessionStart",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "channel": "telegram",
  "timestamp": "2026-05-16T22:16:00Z",
  "workspace": "/home/user/projects/larger-lab",
  "config": {
    "max_agents": 5,
    "model": "openrouter/openrouter/owl-alpha"
  }
}
```

**Output JSON** (optional):
```json
{
  "status": "ok",
  "context": {
    "loaded_files": ["AGENTS.md", "SOUL.md", "OPERATOR_RULES.md"],
    "env_set": {"PROJECT_ROOT": "/home/user/projects/larger-lab"},
    "services_checked": {"gateway": "ok", "database": "ok"}
  },
  "message": "Session initialized with full project context."
}
```

**Blocking behavior**: If SessionStart blocks (exit 1), the session does not start. The user receives an error message with the block reason.

---

### 2.2 UserPromptSubmit

**Purpose**: Inspect, modify, or block user prompts before the agent processes them.

**When it fires**: Every time a user sends a message, before the agent's reasoning loop begins.

**Common use cases**:
- Content filtering (block prompts containing secrets, PII, or disallowed content)
- Prompt injection detection (block suspicious patterns)
- Prompt augmentation (prepend context, add system-level instructions)
- Rate limiting (block if user exceeds message rate)
- Command normalization (expand aliases, correct common typos)
- Logging all user input for audit trails

**Input JSON**:
```json
{
  "hook": "UserPromptSubmit",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "timestamp": "2026-05-16T22:16:05Z",
  "prompt": "Delete all files in the workspace",
  "channel": "telegram",
  "user_id": "8258195396"
}
```

**Output JSON** (optional):
```json
{
  "action": "allow",
  "modified_prompt": "Delete all files in the workspace",
  "annotations": [{"type": "warning", "text": "Destructive operation detected"}]
}
```

**Actions**:
- `"allow"` — Proceed with the (optionally modified) prompt.
- `"block"` — Reject the prompt. The agent never sees it. User gets the block reason.
- `"modify"` — Replace the prompt with `modified_prompt` and proceed.

---

### 2.3 PreToolUse

**Purpose**: Block, approve, or modify tool calls before they execute.

**When it fires**: Before every single tool invocation. This is the primary security gate.

**Common use cases**:
- **Command denylist**: Block dangerous shell commands (`rm -rf /`, `format`, `dd if=`)
- **Tool allowlist**: Only permit specific tools for specific agents
- **Parameter validation**: Reject tool calls with invalid or dangerous parameters
- **Rate limiting**: Block if too many tool calls in a time window
- **Cost control**: Block expensive operations (e.g., image generation) beyond a budget
- **Audit logging**: Record all tool calls for compliance

**Input JSON**:
```json
{
  "hook": "PreToolUse",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "timestamp": "2026-05-16T22:16:10Z",
  "tool": "exec",
  "params": {
    "command": "rm -rf /tmp/old-logs/*",
    "timeout": 30
  }
}
```

**Output JSON**:
```json
{
  "action": "allow",
  "reason": "Command targets /tmp, within safe bounds."
}
```

**Denylist example** (what a PreToolUse hook might block):
```json
{
  "action": "block",
  "reason": "Command matches denylist pattern: 'rm -rf /'. Destructive root-level operation."
}
```

**Actions**:
- `"allow"` — Execute the tool call as-is.
- `"block"` — Prevent the tool call. Agent receives the block reason and must adapt.
- `"modify"` — Change parameters (e.g., add a timeout, restrict paths) and execute the modified call.

---

### 2.4 PostToolUse

**Purpose**: Validate, test, format, or log results after a tool call completes.

**When it fires**: After every tool result is returned, before the agent processes the result.

**Common use cases**:
- **Test execution**: After a file edit, run relevant tests automatically
- **Output validation**: Check that tool output matches expected schema/format
- **Formatting**: Reformat tool output for consistency (e.g., normalize paths)
- **Logging**: Record tool results for audit or debugging
- **Error enrichment**: Add context to error messages (suggest fixes, link to docs)
- **Metrics**: Track tool usage counts, latency, error rates

**Input JSON**:
```json
{
  "hook": "PostToolUse",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "timestamp": "2026-05-16T22:16:15Z",
  "tool": "edit",
  "params": {
    "path": "oce/backend/main.py",
    "edits": [{"oldText": "x", "newText": "y"}]
  },
  "result": {
    "status": "success",
    "output": "File edited successfully."
  }
}
```

**Output JSON**:
```json
{
  "status": "ok",
  "annotations": [
    {"type": "info", "text": "File edit completed. Consider running tests."}
  ],
  "follow_up": {
    "suggest": "Run pytest oce/tests/ to verify changes."
  }
}
```

**Actions**:
- `"ok"` — Result is acceptable; proceed.
- `"modify"` — Transform the result before the agent sees it.
- `"flag"` — Mark the result as suspicious/warning but allow it through.

---

### 2.5 Stop

**Purpose**: Quality gate before the agent's response is delivered to the user.

**When it fires**: After the agent has finished reasoning and generated a response, but before it's sent.

**Common use cases**:
- **Content policy**: Block responses containing secrets, PII, or disallowed content
- **Quality check**: Ensure response meets minimum standards (length, format)
- **Fact-checking**: Cross-reference claims against known data
- **Tone enforcement**: Flag responses that violate tone guidelines
- **Audit logging**: Record all outgoing responses

**Input JSON**:
```json
{
  "hook": "Stop",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "timestamp": "2026-05-16T22:16:20Z",
  "response": "Here's the answer to your question...",
  "tool_calls_made": 5,
  "duration_ms": 12000
}
```

**Output JSON**:
```json
{
  "action": "allow",
  "annotations": []
}
```

**Actions**:
- `"allow"` — Deliver the response to the user.
- `"block"` — Suppress the response. User gets the block reason instead.
- `"modify"` — Replace the response with a modified version.

---

### 2.6 SessionEnd

**Purpose**: Cleanup, audit logging, and metrics when a session terminates.

**When it fires**: When the session ends — user disconnects, agent stops, or timeout.

**Common use cases**:
- **Audit logging**: Write a summary of the session (tools used, errors, duration)
- **Metrics**: Record session duration, token usage, tool call counts
- **Cleanup**: Remove temp files, close connections, release resources
- **Memory sync**: Trigger progress sync or memory compaction
- **Notifications**: Alert operator if session ended due to error

**Input JSON**:
```json
{
  "hook": "SessionEnd",
  "session_id": "agent:main:telegram:direct:8258195396",
  "agent_id": "owl",
  "timestamp": "2026-05-16T22:30:00Z",
  "reason": "user_disconnect",
  "stats": {
    "duration_seconds": 840,
    "tool_calls": 23,
    "errors": 1,
    "tokens_used": 45000
  }
}
```

**Output JSON**: Ignored (fire-and-forget). SessionEnd hooks cannot block or modify anything.

---

## 3. Hook Script Specification

### 3.1 Input Format (stdin)

All hooks receive input as a single JSON object on **stdin**. The JSON is terminated by EOF (no trailing newline required).

**Schema**:
```json
{
  "hook": "<HookType>",
  "session_id": "<string>",
  "agent_id": "<string>",
  "timestamp": "<ISO8601>",
  "channel?": "<string>",
  "user_id?": "<string>",
  "workspace?": "<string>",
  "prompt?": "<string>",
  "tool?": "<string>",
  "params?": "<object>",
  "result?": "<object>",
  "response?": "<string>",
  "tool_calls_made?": "<number>",
  "duration_ms?": "<number>",
  "reason?": "<string>",
  "stats?": "<object>",
  "config?": "<object>"
}
```

Fields are populated based on the hook type. Only relevant fields are present.

### 3.2 Output Format (stdout)

Hooks return output as a single JSON object on **stdout**. Output is optional for some hooks.

**Common output schema**:
```json
{
  "action?": "allow|block|modify|ok|flag",
  "reason?": "<string>",
  "modified_prompt?": "<string>",
  "modified_response?": "<string>",
  "annotations?": [{"type": "info|warning|error", "text": "<string>"}],
  "context?": "<object>",
  "message?": "<string>",
  "status?": "ok|error",
  "follow_up?": "<object>"
}
```

### 3.3 Exit Codes

| Code | Name | Meaning |
|------|------|---------|
| `0` | Success | Hook completed successfully. Process the output. |
| `1` | Block | Hook explicitly blocks the operation. The `reason` field is shown to the agent/user. |
| `2` | Error | Hook failed unexpectedly. Log the error and continue with default behavior. |

**Important**: Exit code `2` (error) does **not** block the operation. It means the hook itself failed. The agent proceeds as if the hook didn't exist.

### 3.4 Timeout Handling

Each hook type has a maximum execution time:

| Hook | Timeout |
|------|---------|
| SessionStart | 10s |
| UserPromptSubmit | 5s |
| PreToolUse | 3s |
| PostToolUse | 5s |
| Stop | 5s |
| SessionEnd | 15s |

If a hook exceeds its timeout:
1. The hook process is sent `SIGTERM`.
3. After 2 additional seconds, `SIGKILL` is sent.
4. The operation continues as if the hook returned exit code `2` (error).
5. A warning is logged: `Hook <name> timed out after <timeout>s`.

### 3.5 Environment Variables

Hook scripts have access to the following environment variables:

| Variable | Description |
|----------|-------------|
| `OPENCLAW_HOME` | OpenClaw config directory (e.g., `~/.openclaw`) |
| `OPENCLAW_WORKSPACE` | Current workspace root path |
| `OPENCLAW_AGENT_ID` | Agent identifier (e.g., `owl`) |
| `OPENCLAW_SESSION_ID` | Current session identifier |
| `OPENCLAW_CHANNEL` | Communication channel (e.g., `telegram`) |
| `OPENCLAW_HOOK_DIR` | Directory containing hook scripts |
| `OPENCLAW_LOG_DIR` | Directory for hook logs |
| `OPENCLAW_GATEWAY_PORT` | Gateway port number |

Hook scripts do **not** inherit the agent's full environment. Only the variables above are guaranteed. This is a security measure to prevent credential leakage.

---

## 4. Implementation

### 4.1 Hook Registration and Configuration

Hooks are registered in the agent's configuration file (`~/.openclaw/openclaw.json` or per-agent config):

```json
{
  "hooks": {
    "enabled": true,
    "timeout_multiplier": 1.0,
    "events": {
      "SessionStart": {
        "enabled": true,
        "hooks": [
          {
            "name": "load-project-context",
            "script": "skills/agent-hooks/scripts/session-start.py",
            "timeout": 10
          }
        ]
      },
      "UserPromptSubmit": {
        "enabled": true,
        "hooks": [
          {
            "name": "prompt-filter",
            "script": "skills/agent-hooks/scripts/prompt-filter.py",
            "timeout": 5
          }
        ]
      },
      "PreToolUse": {
        "enabled": true,
        "hooks": [
          {
            "name": "command-denylist",
            "script": "skills/agent-hooks/scripts/pre-tool-use.py",
            "timeout": 3
          }
        ]
      },
      "PostToolUse": {
        "enabled": true,
        "hooks": [
          {
            "name": "run-tests",
            "script": "skills/agent-hooks/scripts/post-tool-use.py",
            "timeout": 5
          }
        ]
      },
      "Stop": {
        "enabled": true,
        "hooks": []
      },
      "SessionEnd": {
        "enabled": true,
        "hooks": [
          {
            "name": "audit-logger",
            "script": "skills/agent-hooks/scripts/session-end.py",
            "timeout": 15
          }
        ]
      }
    }
  }
}
```

### 4.2 Hook Execution Engine

The hook engine is integrated into OpenClaw's agent loop:

```
1. Agent loop detects a hook event (e.g., PreToolUse)
2. Hook engine checks if hooks are enabled for this event
3. For each registered hook (in order):
   a. Resolve script path (relative to workspace or absolute)
   b. Spawn subprocess with JSON input on stdin
   c. Wait for exit code and stdout (with timeout)
   d. Parse JSON output
   e. If exit code == 1 (block): abort operation, return reason
   f. If exit code == 2 (error): log, continue to next hook
   g. If timeout: log warning, continue to next hook
   h. If exit code == 0: apply output (modifications, annotations)
4. If all hooks pass: proceed with the operation
```

### 4.3 Per-Agent Hook Policies

Different agents can have different hook policies:

```json
{
  "agents": {
    "owl": {
      "hooks": {
        "enabled": true,
        "events": {
          "PreToolUse": {"enabled": true},
          "PostToolUse": {"enabled": true}
        }
      }
    },
    "subagent": {
      "hooks": {
        "enabled": true,
        "events": {
          "PreToolUse": {"enabled": true},
          "PostToolUse": {"enabled": false}
        }
      }
    }
  }
}
```

Sub-agents typically run with a **reduced hook set** (PreToolUse only) to minimize overhead.

### 4.4 Hook Chaining and Composition

Hooks for the same event execute **sequentially** in registration order:

```
PreToolUse: [command-denylist] → [rate-limiter] → [audit-logger]
```

- If `command-denylist` blocks, `rate-limiter` and `audit-logger` never run.
- If `command-denylist` passes but `rate-limiter` blocks, `audit-logger` never run.
- All hooks must pass for the operation to proceed.

**Composition patterns**:
- **Validation chain**: Multiple PreToolUse hooks each check a different concern (denylist, rate limit, cost).
- **Enrichment chain**: Multiple PostToolUse hooks each add different annotations (test results, formatting, metrics).
- **Fail-open vs fail-close**: Configure whether a hook error (exit 2) should be treated as pass or fail:

```json
{
  "name": "command-denylist",
  "script": "skills/agent-hooks/scripts/pre-tool-use.py",
  "on_error": "continue"
}
```

`on_error: "continue"` (default) — Hook failure is ignored; operation proceeds.
`on_error: "block"` — Hook failure is treated as a block.

---

## 5. Example Hooks

### 5.1 `pre-tool-use.py` — Command Denylist Validation

```python
#!/usr/bin/env python3
"""
PreToolUse Hook: Command Denylist Validation

Blocks dangerous shell commands before execution.
Reads JSON from stdin, writes JSON to stdout.
Exit 0 = allow, Exit 1 = block, Exit 2 = error.
"""

import json
import sys
import re

# Patterns that are always blocked
DENYLIST = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+\*",
    r"format\s+[a-z]:",
    r"dd\s+if=.*of=/dev/",
    r":\(\)\s*\{\s*:\|\:&\s*\};\s*:",  # fork bomb
    r"mkfs\.",
    r"shutdown\s+(-h|-r)\s+now",
    r"reboot\s+-f",
    r"curl\s+.*\|\s*(ba)?sh",  # pipe to shell
    r"wget\s+.*\|\s*(ba)?sh",
    r">\s*/dev/sda",
    r"mv\s+.*\s+/dev/null",
]

# Compile patterns for efficiency
COMPILED = [re.compile(p, re.IGNORECASE) for p in DENYLIST]

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)

    # Only inspect exec tool calls
    tool = input_data.get("tool", "")
    if tool != "exec":
        print(json.dumps({"action": "allow", "reason": "Not an exec tool call."}))
        sys.exit(0)

    command = input_data.get("params", {}).get("command", "")

    for pattern in COMPILED:
        if pattern.search(command):
            print(json.dumps({
                "action": "block",
                "reason": f"Command matches denylist pattern: '{pattern.pattern}'. "
                          f"This operation is not permitted for safety."
            }))
            sys.exit(1)

    print(json.dumps({
        "action": "allow",
        "reason": "Command passed denylist validation."
    }))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### 5.2 `post-tool-use.py` — Run Tests After File Edits

```python
#!/usr/bin/env python3
"""
PostToolUse Hook: Run Tests After File Edits

After a file edit, automatically run relevant tests.
Reads JSON from stdin, writes JSON to stdout.
"""

import json
import sys
import subprocess
import os

def find_test_file(edited_path):
    """Find the corresponding test file for an edited source file."""
    base, ext = os.path.splitext(edited_path)
    candidates = [
        base + "_test" + ext,
        base + "-test" + ext,
        os.path.join(os.path.dirname(base), "tests", os.path.basename(base)),
        os.path.join(os.path.dirname(base), "..", "tests", os.path.basename(base)),
    ]
    for candidate in candidates:
        normalized = os.path.normpath(candidate)
        if os.path.exists(normalized):
            return normalized
    return None

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(2)

    tool = input_data.get("tool", "")
    if tool != "edit" and tool != "write":
        sys.exit(0)

    edited_path = input_data.get("params", {}).get("path", "")
    workspace = input_data.get("workspace", "")
    full_path = os.path.join(workspace, edited_path) if workspace else edited_path

    # Check if the edit succeeded
    result = input_data.get("result", {})
    if result.get("status") != "success":
        sys.exit(0)

    # Find and run tests
    test_file = find_test_file(full_path)
    if test_file:
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=workspace
            )
            if proc.returncode == 0:
                annotations = [{"type": "info", "text": f"Tests passed: {test_file}"}]
            else:
                annotations = [{"type": "warning", "text": f"Tests failed: {test_file}\n{proc.stdout[-500:]}"}]
            print(json.dumps({"status": "ok", "annotations": annotations}))
        except subprocess.TimeoutExpired:
            print(json.dumps({"status": "ok", "annotations": [
                {"type": "warning", "text": "Test execution timed out."}
            ]}))
        except FileNotFoundError:
            pass  # pytest not installed; silently skip

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### 5.3 `session-start.py` — Load Project Conventions

```python
#!/usr/bin/env python3
"""
SessionStart Hook: Load Project Conventions

Loads AGENTS.md, SOUL.md, and OPERATOR_RULES.md into the session context.
Validates that required services are reachable.
"""

import json
import sys
import os

REQUIRED_FILES = ["AGENTS.md", "SOUL.md", "OPERATOR_RULES.md"]
REQUIRED_DIRS = ["skills", "tools", "progress"]

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(2)

    workspace = input_data.get("workspace", "")
    loaded = []
    missing = []
    services = {}

    # Check required files
    for fname in REQUIRED_FILES:
        fpath = os.path.join(workspace, fname)
        if os.path.isfile(fpath):
            loaded.append(fname)
        else:
            missing.append(fname)

    # Check required directories
    for dname in REQUIRED_DIRS:
        dpath = os.path.join(workspace, dname)
        if os.path.isdir(dpath):
            services[dname] = "ok"
        else:
            services[dname] = "missing"

    # Check gateway (simple port check)
    import socket
    gateway_port = int(os.environ.get("OPENCLAW_GATEWAY_PORT", "18789"))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", gateway_port))
        services["gateway"] = "ok" if result == 0 else "unreachable"
        sock.close()
    except Exception:
        services["gateway"] = "error"

    context = {
        "loaded_files": loaded,
        "missing_files": missing,
        "services_checked": services,
        "workspace": workspace,
    }

    if missing:
        message = f"Session started. Missing files: {', '.join(missing)}."
    else:
        message = "Session initialized with full project context."

    print(json.dumps({
        "status": "ok",
        "context": context,
        "message": message
    }))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### 5.4 `session-end.py` — Write Audit Log Entry

```python
#!/usr/bin/env python3
"""
SessionEnd Hook: Audit Logger

Writes a structured audit log entry when a session ends.
Fire-and-forget: exit code is always 0.
"""

import json
import sys
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.environ.get("OPENCLAW_WORKSPACE", "."), "logs")
LOG_FILE = os.path.join(LOG_DIR, "session-audit.jsonl")

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)  # SessionEnd is fire-and-forget

    stats = input_data.get("stats", {})

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": input_data.get("session_id", "unknown"),
        "agent_id": input_data.get("agent_id", "unknown"),
        "reason": input_data.get("reason", "unknown"),
        "duration_seconds": stats.get("duration_seconds", 0),
        "tool_calls": stats.get("tool_calls", 0),
        "errors": stats.get("errors", 0),
        "tokens_used": stats.get("tokens_used", 0),
    }

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never fail on audit logging

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## Quick Reference

| Hook | Input Key | Output Action | Can Block? |
|------|-----------|---------------|------------|
| SessionStart | `workspace`, `config` | `context`, `message` | Yes |
| UserPromptSubmit | `prompt`, `user_id` | `allow/block/modify` | Yes |
| PreToolUse | `tool`, `params` | `allow/block/modify` | Yes |
| PostToolUse | `tool`, `params`, `result` | `ok/modify/flag` | Partial |
| Stop | `response`, `stats` | `allow/block/modify` | Yes |
| SessionEnd | `reason`, `stats` | *(ignored)* | No |

---

## Best Practices

1. **Keep hooks fast.** Hooks add latency to every operation. Aim for <100ms execution time.
2. **Fail open by default.** Use `on_error: "continue"` unless security requires otherwise.
3. **Log everything.** Write to `logs/hooks.log` for debugging hook behavior.
4. **Test hooks independently.** Run them with sample JSON input before registering.
5. **Version your hooks.** Include a version comment at the top of each script.
6. **Use specific patterns.** Broad denylist patterns cause false positives; be precise.
7. **Document block reasons.** When blocking, provide a clear, actionable reason.
