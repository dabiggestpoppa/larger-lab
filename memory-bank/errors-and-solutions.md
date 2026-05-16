# Errors & Solutions — Workspace Knowledge Base

> **Purpose:** Structured log of every significant error encountered and its solution.
> **Sync:** Auto-synced to repo memory every 7 updates via `tools/memory_sync_daemon.py`
> **Format:** Each entry follows the same structure for fast scanning.
> **Rule:** Keep entries concise. If solution > 10 lines, link to a doc instead.

---

## Entry #1 — OC2 Gateway "Live" But Not Processing Messages

| Field | Value |
|-------|-------|
| **Date** | 2026-05-16 |
| **Severity** | CRITICAL — 8 hours of downtime |
| **Service** | OC2 (OpenClaw 2 Gateway) |
| **Symptom** | Health endpoint said "live", Telegram connected, but no response to messages |

### Root Cause
Two config issues:
1. **Invalid config keys** in `openclaw.json`: `contextLimit` and `hardThresholdTokens` don't exist in OpenClaw's schema. Gateway started HTTP server but agent model never initialized.
2. **Wrong API key** in agent `models.json`: Had literal string `OPENROUTER_API_KEY` instead of actual key. Agent fell back to `openai/gpt-5.5` which had no key.

### Solution
1. Remove invalid config keys from `.openclaw-2/.openclaw/openclaw.json`
2. Fix `~/.openclaw/agents/main/agent/models.json` with correct API key
3. Restart with correct `OPENCLAW_HOME`

### Diagnostic Pattern (Soft Logic)
- **Read logs first** — `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log`
- Health endpoint only checks HTTP server, NOT agent model
- When behavior ≠ config, check for **agent-level config overrides**
- When service won't start, check **config schema validation** first

### Prevention
- `tools/oc2-start.cmd` — validates config + API key before starting
- `tools/oc2-doctor.cmd` — full 6-layer diagnostic
- Never add config keys without checking schema first

---

## Entry #2 — OC2 Session Stuck in "Running" State

| Field | Value |
|-------|-------|
| **Date** | 2026-05-16 |
| **Severity** | HIGH — session unresponsive |
| **Service** | OC2 Telegram DM session |
| **Symptom** | Session status = "running" forever, contextTokens = 1,048,756 |

### Root Cause
Session context bloated to 1M+ tokens. OWL Alpha model couldn't process new messages because the context window was exhausted.

### Solution
1. Kill OC2 process
2. Remove stuck session from `sessions.json`
3. Delete bloated `.jsonl` session files
4. Restart OC2 fresh
5. Add context limits to config (800K max, compaction at 750K)

### Diagnostic Pattern
- Check `contextTokens` in sessions.json — if > 600K, warn user
- If session status = "running" for > 5 minutes, it's stuck
- High context = session can't process new messages

### Prevention
- `tools/oc2-context-monitor.py` — alerts at 75%/90%/95% context usage
- Context monitor skill in OC2 skills directory
- Auto-compaction at 95%

---

## Entry #3 — PowerShell Multi-Line Command Failures

| Field | Value |
|-------|-------|
| **Date** | 2026-05-16 |
| **Severity** | MEDIUM — wasted time, failed operations |
| **Tool** | PowerShell terminal |
| **Symptom** | Multi-line commands with `;` or `|` silently fail or produce no output |

### Root Cause
PowerShell handles multi-line commands differently than bash. Semicolons don't always chain properly, especially with comments (`REM`) or complex pipes.

### Solution
- Use **one command per line** in PowerShell
- For complex scripts, write a `.cmd` or `.py` file and execute that
- Use `python -c "..."` for complex logic instead of inline PowerShell

### Prevention
- Prefer `.cmd` scripts for multi-step operations
- Test complex commands in isolation before chaining

---

## Entry #4 — OpenClaw Config Write Rejections

| Field | Value |
|-------|-------|
| **Date** | 2026-05-16 |
| **Severity** | MEDIUM — config changes silently rejected |
| **Service** | OpenClaw config system |
| **Symptom** | `CONFIG_WRITE_REJECTED` in config-audit.jsonl |

### Root Cause
OpenClaw validates config writes. If the new config is smaller than the previous version (size-drop), it rejects it as suspicious. Also rejects unknown keys.

### Solution
- Only use keys documented in OpenClaw's schema
- When removing keys, also remove the `.bak` file
- Check `config-audit.jsonl` after config changes

### Prevention
- Check schema before adding keys
- Use `openclaw doctor --fix` to validate config

---

## Template for New Entries

```
## Entry #N — [Short Title]

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Severity** | CRITICAL / HIGH / MEDIUM / LOW |
| **Service** | Which service/tool |
| **Symptom** | What the user sees |

### Root Cause
What actually caused it.

### Solution
How to fix it.

### Diagnostic Pattern
What to check next time (soft logic, not hard rules).

### Prevention
Tools/patterns to prevent recurrence.
```
