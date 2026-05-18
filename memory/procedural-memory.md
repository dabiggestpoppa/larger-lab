---
created: 2026-05-17
updated: 2026-05-17
tags: [memory, procedural, workflows, sop, how-to]
importance: 5
---

# Procedural Memory

> How-to knowledge, workflows, standard operating procedures.

## Session Startup Procedure

1. Run: `python tools/terminal_cleanup.py --force` (kill stale processes)
2. Read: `shared-conversations/team-chat.md` (latest team context)
3. Read: `workspace-state.md` (system state)
4. Read: `progress/{agent}-progress.md` (own progress)

## Delegation Workflow

1. MAD gives directive to OWL
2. OWL identifies required work
3. OWL creates task specification (file path + description)
4. OWL spawns sub-agent with explicit:
   - Task definition
   - Success criteria
   - File paths to work in
   - Time/scope bounds
5. Sub-agent works → writes output files
6. OWL reads output files → reports to MAD
7. OWL updates workspace-state.md if needed

## Error Handling SOP

1. If error occurs → read error log from LAST action (not health check)
2. If stuck >2 attempts → log to `error-db.json` + `team-chat.md`
3. If stuck >30 min → stop guessing, read the log file
4. If service won't start → check config schema validation FIRST
5. If behavior ≠ config → check for override files

## Code Change SOP

1. Read existing code
2. Make minimal change
3. Run tests: `python -m pytest` or language-specific test
4. Update progress file
5. Push to workspace-state.md (every 5 edits)
6. Post summary to team-chat.md (every 5 edits)
7. If architecture change: `python tools/arch-commit.py --agent <TAG> --file "<path>" --change "<description>"`

## Memory Update SOP

1. After EVERY code edit → update own progress file + memory file
2. After every 5 code edits → post summary to team-chat.md
3. Before each work session → read team-chat.md + workspace-state.md
4. Compress memory if file exceeds 200 lines

## Terminal Cleanup SOP

1. After EVERY task → kill spawned terminals
2. Check: test runners, dev servers, background watchers
3. Run `python tools/terminal_cleanup.py --force` at session start
4. Stale terminals cause port conflicts — don't leave them

## Phase Gate SOP

1. All tests for current phase must pass
2. Run: `python tools/phase-gate.py --check`
3. CC approves phase transition
4. Update `.phase-state.json`
5. Update AGENTS.md phase status table

## OC2 Restart Procedure

1. `openclaw gateway stop`
2. `openclaw gateway run --port 18790`
3. Wait 5s
4. Test: `openclaw gateway probe`
5. Do NOT debug code first — 90% of issues fixed by restart
