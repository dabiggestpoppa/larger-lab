---
name: openclaw-structural-anchor
description: CG-3 OpenClaw Structural Anchor — augments OpenClaw's planning loop with topology thinking, dependency awareness, and structural validation. NOT a replacement — an overlay.
---

# OpenClaw Structural Anchor (CG-3)

## Core Principle
OpenClaw already has: agent runtime, memory layer, tool layer, planning loop, workspace persistence, multi-session continuity, orchestration patterns, execution routing, autonomous workflows.

The issue is NOT lack of capability. The issue is lack of **structural operational cognition**.

CG-3 upgrades planning flow, dependency awareness, operational relationships, propagation reasoning, topology stability checks — INSIDE OpenClaw's established runtime loop.

## What This Skill Does

### 1. Topology Thinking Template
Before any planning operation, run this internal structure:

```
Objective: [What are we trying to achieve]
Nodes: [What components/agents/files are involved]
Dependencies: [What depends on what — map the graph]
Risks: [What breaks if X fails — propagation analysis]
Validation: [What checks pass before execution]
Execution: [Ordered sequence with rollback points]
```

### 2. Dependency Check Habit
Before ANY execution, answer:
- What depends on this?
- What breaks if this fails?
- What propagation cascades exist?
- What's the rollback path?

### 3. Execution Topology Memory
Store lessons in MEMORY.md:
- Failure propagation patterns (what broke what)
- Dependency lessons (what was missing)
- Rollback lessons (what recovery worked)
- Topology stability patterns (what configurations are stable)

### 4. Tool Sequencing Governance
Before using tools:
1. Check dependency completeness (are prerequisites met?)
2. Validate rollback presence (can we undo this?)
3. Assess propagation exposure (what else is affected?)
4. Gate execution (proceed only if checks pass)

### 5. Structural Validation Layer
Before any action, validate:
- [ ] Dependency completeness — all prerequisites present
- [ ] Rollback presence — recovery path exists
- [ ] Propagation exposure — downstream effects understood
- [ ] Continuity stability — system state preserved on failure

## OpenClaw Features to Leverage (NOT Replace)

| Feature | How CG-3 Uses It |
|---------|-----------------|
| AGENTS.md / SOUL.md / MEMORY.md | Inject topology cognition habits, execution flow, governance sequencing |
| Memory Layer | Store topology lessons, failure chains, dependency failures, rollback patterns |
| Tool Layer | Enhance tool selection/sequencing through dependency awareness and topology validation |
| Session + Workspace Model | Understand operational state, track repo topology, maintain continuity awareness |
| Planning Loop | Upgrade the structure of planning cognition itself |

## What Should NOT Happen
- NO OpenClaw runtime rewrites
- NO orchestration engine replacement
- NO giant topology systems
- NO recursive graph engines
- NO core framework mutation
- NO ontology bloat

## Correct Mental Model
```
OpenClaw Runtime → Memory + Tools + Planning
Planning → Topology Overlay → Governance + Validation → Improved Execution
```

This is AUGMENTATION. NOT replacement.

## Implementation Stack
```
AGENTS.md + SOUL.md + MEMORY.md → Planning Loop → Topology Overlay
→ Validation Layer → Tool Sequencing → Execution
```

## Integration with O2C-VAULT (Phase 00)
The vault is the persistent substrate for topology memory:
- `O2C-VAULT/ontology/` — topology patterns, dependency graphs
- `O2C-VAULT/failures/` — failure propagation patterns
- `O2C-VAULT/memory/` — dependency lessons, rollback lessons
- `O2C-VAULT/doctrine/` — governance rules, validation standards

## Usage in Agent Harness

When any agent starts a task:
1. Read this skill from `skills/openclaw-structural-anchor/SKILL.md`
2. Apply Topology Thinking Template to the task
3. Run Dependency Check before execution
4. Store topology lessons in O2C-VAULT after completion
5. Update MEMORY.md with structural insights
