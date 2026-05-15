---
name: goal-mode
description: >
  Activate for autonomous task execution via /goal command. Use when the user wants
  an agent to work independently toward a defined outcome without manual intervention.
  Works in Claude Code, Codex CLI, and Hermes Agent.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# Goal Mode Skill

## Overview

`/goal` allows AI agents to work in a "loop" to complete tasks without needing
permission or manual intervention. It's the autonomous execution pattern that
replaces the human-in-the-loop bottleneck.

## When to Use

- Long-running tasks that require multiple steps (research → code → debug → verify)
- Tasks where the agent should validate its own work before returning
- Multi-file changes that need to be coherent
- Research + implementation pipelines
- Scheduled/cron jobs that need autonomous execution

## Prompt Template

```
/goal [do the work] until [measurable end state] without [constraints that must hold]
```

### Three Required Components

1. **Goal**: The task in one line — what to do
2. **Measurable End State**: Define what "done" actually looks like (test exits 0, file exists, API returns 200)
3. **Constraints**: Rules the model must abide by (don't modify files outside X, don't install new dependencies, etc.)

## Examples

```
/goal fix every failing test until npm test exits 0 without modifying any file outside the /auth directory
```

```
/goal research the best vector database for our agent memory system and write a comparison report until the report.md file exists with benchmarks for ChromaDB, Pinecone, and Qdrant
```

```
/goal add a dark/light theme toggle to this project, persist the choice in localStorage, update the UI styles to support both themes, and verify it works in the browser
```

```
/goal improve the README so a new contributor can install, run, test, and understand the project
```

## Advanced Prompt Structure

For complex projects, include:
- **Context**: Background information the agent needs
- **Success criteria**: Specific, measurable outcomes
- **Constraints**: What the agent must NOT do
- **Checklist**: Step-by-step verification items
- **Output format**: What the final deliverable should look like

## Pro Tips

- Only one `/goal` can be set at a time — use it wisely
- `/goal` shines on long-running work; for small one-offs, a normal prompt is enough
- Pair with `/plan`: workflow is `/goal` → `/plan` → `/goal clear`
- Use `/pause` to pause goals, `/goal clear` to reset
- Give the agent `.md` files for tracking progress
- The agent can set its own `/goal` — it will likely write better prompts than you
- Provide a "checklist" in your prompts for complex tasks

## Workflow Integration

1. Set `/goal` with clear end state + constraints
2. Agent works autonomously, validating each step
3. Agent returns with final product + summary
4. Review output, provide feedback
5. If corrections needed: either correct directly or set a new `/goal`

## Verification

The agent should verify its own work before returning:
- Run tests and confirm they pass
- Check that the end state is actually met
- Validate constraints were not violated
- Report any uncertainty or edge cases encountered
