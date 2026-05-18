# AGENT STABILITY PROTOCOL v2.0
> MAD Directive 2026-05-17: Agents were causing cascading failures. This protocol prevents ripple effects.

## SESSION MANAGEMENT

### Before ANY agent action:
1. Check if target session already exists — don't duplicate
2. Verify no stale locks: `openclaw sessions list`
3. If stale lock found → run `openclaw doctor --fix` before proceeding

### Sub-agent spawning rules:
- **Max 2 concurrent** (reduced from 5 until stability proven)
- **Hard timeout: 5 minutes** — no exceptions
- **No recursive spawning** — sub-agents CANNOT spawn sub-agents
- **Must write to team-chat** before starting work
- **Must report completion or failure** within timeout

### On stall detection:
- If agent session stalls 3+ times in 10 minutes → **kill and do NOT retry**
- Log the stall pattern, investigate root cause before retrying
- Never restart the same failed task more than twice

## TOOL CALL DISCIPLINE

### File operations:
- ALWAYS check file exists before reading
- Use absolute paths, never relative
- If ENOENT → stop, report, don't retry same path

### Subprocess calls:
- ALL subprocess calls MUST use `CREATE_NO_WINDOW` on Windows
- ALL background processes MUST have PID tracking
- Kill stale processes before spawning new ones
- Use `pythonw` for daemon scripts

### Network calls:
- Check connectivity before API calls
- On timeout → wait 30s, retry once, then fail gracefully
- Never hammer an endpoint that's returning errors

## ERROR CONTAINMENT

### If an error occurs:
1. Log it immediately to `memory-bank/error-log.jsonl`
2. Assess: is this isolated or systemic?
3. If systemic → STOP all agent work, alert MAD
4. If isolated → fix, document, continue

### Forbidden patterns:
- Retrying the same failed operation >2 times without changing approach
- Spawning new sub-agents to "fix" a failed sub-agent's work
- Modifying system files without MAD approval
- Running unbounded loops or recursive operations

## GATEWAY PROTECTION

### Agents must NEVER:
- Restart the gateway
- Modify `openclaw.json` directly
- Kill processes they didn't spawn
- Fill the log with repetitive error messages

### If gateway shows stress (event loop delay):
- Reduce agent activity immediately
- Kill non-essential sub-agents
- Report to MAD before continuing

---
_This protocol is mandatory for all agents. Violation = immediate suspension._
