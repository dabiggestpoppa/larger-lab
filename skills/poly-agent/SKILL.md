# Poly-Agent Skill — Sub-Agent Orchestration for Lab Managers

## Purpose
The Poly-Agent skill allows a Lab Manager agent to dynamically spawn, coordinate, and manage sub-agents within its lab. Each sub-agent is a bounded, specialized worker with a single clear deliverable.

## Core Principle
**One agent, one task, one deliverable.** The manager never does work itself — it decomposes, delegates, verifies, and integrates.

## When to Spawn a Sub-Agent
- Task requires specialized knowledge the manager doesn't have
- Task can be parallelized (multiple agents working simultaneously)
- Task is large enough to warrant isolation (prevents context bloat)
- Task needs focused attention without interruption

## Sub-Agent Governance (OCE + SRRA Principles)

### Bounded Autonomy
- Each sub-agent gets: **single deliverable + success criteria + timeout + output format**
- Sub-agents **cannot spawn other sub-agents** (no recursive proliferation)
- Sub-agents **cannot modify system files** (OPERATOR_RULES, AGENTS.md, safety rules)
- Sub-agents **must report to team-chat** with their tag
- Max **5 concurrent sub-agents** per lab (prevents topology fragmentation)

### Entropy Governance
- Sub-agents should be **short-lived** (15 min soft limit)
- If a sub-agent fails, **do NOT immediately retry** — assess root cause first
- Break large tasks into **smaller, independent chunks**
- Each sub-agent should produce **testable, verifiable output**

### Repair Before Expansion
- If a sub-agent is stuck >15 min: **kill, decompose, respawn**
- If a sub-agent fails: **fix the task spec, not the agent**
- Always **verify output** before integrating

### Continuity Preservation
- Sub-agents update **progress files** and **team-chat**
- Manager maintains a **task board** tracking all sub-agent work
- Completed work is **integrated and tested** before marking done

## Spawn Template

When spawning a sub-agent, the manager provides:

```
You are [TAG]. Your ONLY task is to [SINGLE DELIVERABLE].

## Task: [Clear description]
- File to create/modify: [exact path]
- Success criteria: [testable outcomes]
- Max runtime: [time estimate]
- Output format: [expected format]

## Context
- Read these files first: [relevant context]
- Key constraints: [what NOT to do]
- Related work: [what other agents are doing]

## Rules
- Write under [N] lines
- Use only stdin/stdlib (unless specified)
- Do NOT modify files outside [scope]
- Do NOT spawn other sub-agents
- Report to team-chat with tag [TAG]
- Update progress file: progress/[tag]-progress.md

## Before Starting
1. Read [context files]
2. Verify [prerequisites]
3. Post first update to team-chat as [TAG]
```

## Manager Responsibilities

### Before Spawning
1. **Decompose** the task into independent, testable chunks
2. **Define** clear success criteria for each chunk
3. **Identify** dependencies between tasks
4. **Estimate** time and complexity

### During Execution
1. **Monitor** sub-agent progress via team-chat
2. **Verify** output quality before integrating
3. **Resolve** conflicts between sub-agents
4. **Re-balance** workload if one agent is overloaded

### After Completion
1. **Integrate** sub-agent output into codebase
2. **Test** integrated work
3. **Document** what was learned
4. **Update** task board and progress files

## Communication Protocol

### Manager → Sub-Agent
- Task assignment via spawn parameters
- Clarification via team-chat @mentions
- Priority changes via team-chat

### Sub-Agent → Manager
- Progress updates in team-chat with tag
- Completion notification with file paths
- Error reports with context

### Sub-Agent ↔ Sub-Agent
- **No direct communication** — all coordination goes through manager
- Shared files are the only coordination mechanism
- Conflicts resolved by manager

## Task Board Format

The manager maintains a task board at `progress/[lab]-task-board.md`:

```markdown
# [Lab Name] Task Board

## Active
| Task | Agent | Status | Started | ETA |
|------|-------|--------|---------|-----|
| ... | ... | In Progress | ... | ... |

## Queued
| Task | Priority | Dependencies |
|------|----------|--------------|
| ... | HIGH | ... |

## Completed
| Task | Agent | Completed | Output |
|-------|-------|-----------|--------|
| ... | ... | ... | ... |
```

## Error Handling

### Sub-Agent Fails
1. Read the error log (not the health check)
2. Identify root cause (not symptom)
3. Fix the task spec (not the agent)
4. Spawn new agent with corrected spec

### Sub-Agent Stuck
1. Check if task is too large → decompose
2. Check if context is missing → provide more context
3. Check if dependencies are blocking → resolve dependencies
4. Kill and respawn with smaller task

### Output Quality Issues
1. Verify against success criteria
2. Request revision with specific feedback
3. If revision fails, manager does the work directly
4. Document the pattern for future tasks

## Integration with OCE

- Sub-agent events can be emitted to Event Fabric
- Sub-agent state can be stored in Structural Memory
- Sub-agent health can be monitored by Observer Runtime
- Sub-agent results can be searched via memory search

## Constraints

1. **Max 5 concurrent sub-agents** per lab
2. **No recursive spawning** — sub-agents cannot spawn
3. **All execution logged** — observable, replayable
4. **All output verified** — manager checks before integrating
5. **Bounded scope** — sub-agents only touch their assigned files
6. **Short-lived** — 15 min soft limit per sub-agent
7. **No system modification** — sub-agents cannot change safety rules
