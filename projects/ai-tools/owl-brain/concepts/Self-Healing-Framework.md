# Self-Healing Framework

> OWL's ability to detect, classify, and repair issues in itself and the workspace.

## Components

### 1. Error Database (`db/owl_health.db`)
- SQLite with 4 tables: errors, bug_annotations, startup_checks, self_healing_actions
- Tracks: severity, category, occurrence count, resolution status, timestamps

### 2. Self-Heal Engine (`tools/self_heal.py`)
- Scans gateway logs on startup
- 12 error pattern matchers (symlink, timeout, stall, performance, recovery, tool)
- Deduplicates, logs to DB, creates bug markdown files
- Auto-fixes known patterns
- Generates health reports

### 3. Bug Annotations (`bugs/open/` and `bugs/resolved/`)
- Markdown files for each unique error
- Fields: severity, category, root cause, suggested fix, status, priority
- Auto-created on first detection

### 4. Self-Surgery Module (`tools/self_surgery.py`)
- Safe internal editing: backup → edit → validate → log
- Can modify any workspace file (SOUL.md, MEMORY.md, skills, tools, etc.)
- Never touches gateway config, node_modules, or .git
- Full backup/restore system in `.surgery-backups/`

## First Scan Results (2026-05-16)
- 509 raw log lines → 12 unique errors → 12 bug files → 1 auto-fixed
- **Chronic issues**:
  - Event loop delays: 169 occurrences (gateway under load)
  - Agent stalls: 51 occurrences (subagents getting stuck)
  - Network fetch timeouts: 34 occurrences (Telegram API)
  - Symlink EPERM: 198 occurrences (known Windows limitation — auto-resolved)

## Integration
- Runs on every 4th heartbeat or first heartbeat after gateway restart
- Results logged to DB and bug files
- Critical errors trigger Telegram notification to MAD

## Related
- [[Self-Surgery]] — The editing capability
- [[Error DB]] — The data store
- [[HEARTBEAT]] — The trigger mechanism
