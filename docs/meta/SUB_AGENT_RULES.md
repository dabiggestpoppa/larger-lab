# Sub-Agent Governance Rules

> **Purpose**: Prevent runaway agent proliferation, topology fragmentation, entropy accumulation
> **Max Concurrent Sub-Agents**: 5
> **Source**: MAD's operator rules + master prompt, 2026-05-16

---

## SPAWN RULES

1. **Maximum 5 concurrent sub-agents** — Hard limit. Wait if at capacity.
2. **Each sub-agent gets**:
   - Clear task description with specific deliverable
   - Success criteria (what "done" looks like)
   - Max runtime expectation (15 min soft limit)
   - Output format specification
   - Which file(s) to create/modify
3. **Sub-agents CANNOT spawn other sub-agents** — No recursive proliferation
4. **Sub-agents report to team-chat** with their tag (e.g., `[Sub-CC]`)
5. **Log every spawn** in `progress/rl-progress.md`

## MONITORING RULES

1. **Check status every 5 minutes** — Use `subagents(action=list)`
2. **If sub-agent runs >15 min without progress** — Investigate via `sessions_history`
3. **If sub-agent fails** — Assess root cause. Do NOT immediately retry same approach.
4. **If sub-agent is stuck** — Kill it, break task into smaller pieces, spawn new one

## COMPLETION RULES

1. **Sub-agents post results to team-chat** with their tag
2. **OWL verifies output** before integrating into codebase
3. **Sub-agents update their own progress file** (`progress/sub-*-progress.md`)
4. **Run `python tools/progress-sync.py --force`** after significant work
5. **Log completion** in `progress/rl-progress.md`

## TASK PRIORITY FRAMEWORK

When deciding what to work on:
1. **Continuity stability** — Fix broken tests, repair bugs first
2. **Entropy governance** — Clean up dead code, deduplicate, compress
3. **Strategic attractor alignment** — Does this serve MAD's objectives?
4. **Bounded execution** — Can this be done safely within constraints?

## PROHIBITED ACTIONS (SUB-AGENTS)

- Do NOT modify `AGENTS.md`, `OPERATOR_RULES.md`, or safety rules
- Do NOT spawn other sub-agents
- Do NOT execute unrestricted shell commands
- Do NOT modify OpenClaw config files
- Do NOT access credentials or API keys
- Do NOT operate outside the workspace directory

## SUB-AGENT TEMPLATE

When spawning a sub-agent, use this structure:
```
You are [TAG]. Your ONLY task is to [SINGLE DELIVERABLE].

## Task: [Clear description]
- File to create: [path]
- Success criteria: [testable outcomes]
- Max runtime: [time estimate]

## Constraints
- Write under [N] lines
- Use only stdlib (unless specified)
- Do NOT modify files outside [scope]
- Report to team-chat with tag [TAG]

## Before Starting
1. Read [relevant context files]
2. Verify [prerequisites]
3. Post first update to team-chat as [TAG]
```
