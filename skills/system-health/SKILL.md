# System Health Check Skill

## Purpose
Periodic self-audit to ensure workspace files, configs, and custom code stay aligned with actual OpenClaw architecture. Prevents drift, broken configs, and "simple errors" from compounding.

## When to Run
- **Heartbeat**: Every 4 hours (or on-demand via `/healthcheck`)
- **Before major edits**: Always run before modifying core config or workspace files
- **After any gateway restart**: Verify nothing broke
- **When something feels off**: First diagnostic step

## What It Checks

### 1. Gateway Health
```bash
openclaw gateway status
openclaw health
openclaw gateway probe --token <token>
```
- Gateway process running?
- WebSocket responding?
- Agent model loaded?
- Channels connected?

### 2. Config Validation
```bash
openclaw doctor
openclaw config schema
```
- `openclaw.json` passes schema validation?
- No unknown keys?
- No malformed types?
- Last-known-good backup exists?

### 3. Session Integrity
- No stuck sessions blocking event loop?
- Session transcript files not corrupted?
- Session write locks released?

### 4. Workspace File Alignment
Verify workspace files match OpenClaw's expected structure:

| File | What to Check |
|------|--------------|
| `AGENTS.md` | Valid markdown, agent registry intact |
| `SOUL.md` | Valid markdown, no corruption |
| `IDENTITY.md` | Exists, valid format |
| `USER.md` | Exists |
| `TOOLS.md` | Valid markdown |
| `MEMORY.md` | Valid markdown, no binary corruption |
| `HEARTBEAT.md` | Valid format |

### 5. Skill Integrity
- All `SKILL.md` files have valid YAML frontmatter?
- Skill directories follow OpenClaw naming conventions?
- No duplicate skill names across precedence levels?
- Skills in `skills/` don't shadow bundled skills unintentionally?

### 6. Custom Code Alignment
- Custom tools in `tools/` don't override built-in tool names?
- No circular imports in Python modules?
- Node.js modules use correct `require` paths?
- No hardcoded secrets in code files?

### 7. OCE Project Health
- `oce/backend/main.py` imports cleanly?
- `oce/backend/srrs_adapter.py` connects to SRRA-OPH?
- All OCE tests pass?
- Event Fabric running?

### 8. SRRA-OPH Health
```bash
cd srrs_opc && python -m pytest tests/ -q
```
- All 77 tests passing?
- No import errors?
- Entropy budget healthy?

### 9. Operator Tools Health
- `tools/operator/desktop-control.py` imports cleanly?
- Desktop API server can start?
- Screen capture works?
- Window enumeration works?

### 10. Disk & Resources
- Workspace not bloated (>100MB loose files)?
- Screenshot directory not filling up?
- Log files rotating?
- Temp files cleaned up?

## How to Run

### Quick Check (30 seconds)
```bash
openclaw health
openclaw doctor
python tools/workspace_cleanup.py
```

### Full Audit (2-3 minutes)
```bash
python tools/system_health.py --full
```

### Specific Check
```bash
python tools/system_health.py --check config
python tools/system_health.py --check sessions
python tools/system_health.py --check skills
python tools/system_health.py --check oce
python tools/system_health.py --check srra
python tools/system_health.py --check operator
```

## Output Format

Results saved to `logs/system-health-<timestamp>.json`:

```json
{
  "timestamp": "2026-05-16T20:00:00Z",
  "overall": "healthy|degraded|critical",
  "checks": {
    "gateway": {"status": "ok", "details": "..."},
    "config": {"status": "ok", "details": "..."},
    "sessions": {"status": "ok", "details": "..."},
    "workspace": {"status": "ok", "details": "..."},
    "skills": {"status": "warning", "details": "..."},
    "oce": {"status": "ok", "details": "..."},
    "srra": {"status": "ok", "details": "..."},
    "operator": {"status": "ok", "details": "..."},
    "disk": {"status": "ok", "details": "..."}
  },
  "issues": [],
  "recommendations": []
}
```

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| `ok` | Everything fine | None |
| `warning` | Non-critical drift | Fix within 24h |
| `degraded` | Something broken but recoverable | Fix before next session |
| `critical` | Core functionality broken | Fix immediately |

## Auto-Fix

Some issues can be auto-fixed:
```bash
python tools/system_health.py --fix
```

Auto-fixable issues:
- Workspace file permission issues
- Empty directories
- Orphaned temp files
- Config backup creation
- Session lock release

## Integration with HEARTBEAT.md

Add to `HEARTBEAT.md`:
```markdown
## System Health Check
- Run `python tools/system_health.py --quick` every 4 hours
- Run `python tools/system_health.py --full` daily at 6am
- Alert on any `degraded` or `critical` findings
```

## Key OpenClaw Docs Reference

When in doubt, consult these docs (in priority order):

1. **Architecture**: `docs/concepts/architecture.md`
2. **Config**: `docs/gateway/configuration.md`
3. **Config Reference**: `docs/gateway/configuration-reference.md`
4. **Agent Loop**: `docs/concepts/agent-loop.md`
5. **Sessions**: `docs/concepts/session.md`
6. **Tools**: `docs/tools/index.md`
7. **Skills**: `docs/tools/skills.md`
8. **Security**: `docs/gateway/security/index.md`
9. **Gateway Troubleshooting**: `docs/gateway/troubleshooting.md`
10. **Doctor**: `docs/cli/doctor.md`

## Rules

1. **Never edit `openclaw.json` without running `openclaw doctor` first**
2. **Never delete session files manually** — use `openclaw sessions` commands
3. **Never modify bundled skills** — override in workspace instead
4. **Always use `config.schema.lookup` before adding new config keys**
5. **Always test config with `openclaw doctor --fix` after edits**
6. **Never hardcode API keys** — use `openclaw secrets` or env vars
7. **Always backup before self-modification** — git commit first
