# Errors & Solutions — Workspace Knowledge Base

> **Purpose:** Structured log of every significant error encountered and its solution.
> **Rule:** Keep entries concise. Log any error that persists >2 attempts.

---

## Entry #1 — Stale Terminals Accumulating

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | MEDIUM — wastes resources, causes port conflicts |
| **Pattern** | Agents spawn terminals for tests/servers but don't kill them after completion |
| **Symptom** | Multiple old python/node processes running for hours, consuming memory |
| **Solution** | After EVERY task, kill spawned terminals. Run `python tools/terminal_cleanup.py --force` at session start. |
| **Prevention** | AGENTS.md rule: Terminal Cleanup Rule (MANDATORY) |

---

## Entry #2 — Windows CMD Restrictions

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | MEDIUM — causes file operation failures, encoding issues |
| **Pattern** | Using `cmd.exe` or `subprocess.run(..., shell=True)` on Windows |
| **Symptom** | File operations fail, encoding errors, path issues |
| **Solution** | Always use PowerShell first. `subprocess.run(['powershell', '-NoProfile', '-Command', '...'])` |
| **Prevention** | AGENTS.md rule: Windows Execution Rule (MANDATORY) |

---

## Entry #3 — pressure_tracker Variable Name Bug

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | LOW — caught by tests immediately |
| **Pattern** | Used `signals` instead of `field.signals` in `_calc_field_pressure` |
| **Solution** | Changed `len(signals)` to `len(field.signals)` |
| **Prevention** | Run tests after every module creation |
