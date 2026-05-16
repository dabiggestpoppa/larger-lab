# Harness Engineering Skill

## Purpose
Build reliable agent systems by constraining AI behavior with explicit rules, boundaries, and verification loops. The harness is everything AROUND the model — the 98.4% of infrastructure that makes the 1.6% AI decision logic actually work.

## Core Principle
**A harness doesn't make the model smarter — it establishes a closed-loop working system for the model.**

From Anthropic/OpenAI/Claude Code research:
- Constrain agent behavior with explicit rules and boundaries
- Maintain context across long-running, multi-session tasks
- Stop agents from declaring victory too early
- Verify work using full-pipeline tests and self-reflection
- Make runtime observable and debuggable

## When to Use
- Starting any new project or multi-step task
- Delegating to sub-agents
- Any task that takes >5 steps
- Any task where failure is expensive

## The Harness Loop

```
┌─────────────────────────────────────────────────────────────┐
│                     HARNESS LOOP                             │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  DEFINE   │───▶│ EXECUTE  │───▶│ VERIFY   │              │
│  │  (rules)  │    │ (agent)  │    │ (tests)  │              │
│  └──────────┘    └──────────┘    └────┬─────┘              │
│       ▲                               │                     │
│       │         ┌──────────┐          │                     │
│       └─────────│  REPAIR  │◀─────────┘                     │
│                 │ (iterate)│                                │
│                 └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## 1. DEFINE Phase — Set Up the Harness

Before the agent starts working, define:

### A. Rules (AGENTS.md / project rules)
```markdown
## Project: <name>
- Scope: What's in / out of scope
- Constraints: What the agent must NEVER do
- Requirements: What "done" looks like
- Verification: How to check the work
```

### B. Boundaries (what to protect)
- Files that must not be modified
- Commands that must not be run
- Paths that are off-limits
- External services that must not be called

### C. Success Criteria (what "done" looks like)
- Specific, testable outcomes
- Not "it works" but "these tests pass"
- Include edge cases

### D. Context Injection
- Load relevant project conventions
- Load environment facts
- Load relevant memory/knowledge
- Load previous session state if continuing

## 2. EXECUTE Phase — Run the Agent

### Sub-agent Delegation Pattern
When delegating to sub-agents:
1. Give clear task definition with success criteria
2. Specify what tools they can use
3. Set timeout expectations
4. Define output format
5. Include verification steps in the task itself

### Progress Tracking
- Use `update_plan()` to track progress
- Mark steps as pending/in_progress/completed
- If stuck >30 min, stop and read the logs (don't guess)

### Context Management
- For long tasks: periodically summarize state
- Use `sessions_yield()` to wait for sub-agents
- Don't poll — use push-based completion events

## 3. VERIFY Phase — Check the Work

### Quality Gates (must pass before declaring done)
1. **Build passes** — code compiles/runs without errors
2. **Tests pass** — all existing + new tests pass
3. **Linting clean** — no style/formatting issues
4. **Manual inspection** — spot-check critical logic
5. **Integration test** — end-to-end verification

### Self-Reflection Pattern
Before declaring a task complete:
1. Read what was actually produced
2. Compare against success criteria
3. Check for edge cases
4. Verify no regressions
5. Document what was learned

## 4. REPAIR Phase — Iterate

If verification fails:
1. Read the actual error log (not the health check)
2. Identify root cause (not symptom)
3. Fix ONE thing at a time
4. Re-verify after each fix
5. Document the fix pattern for future

## Harness Patterns

### Pattern 1: Baseline vs Minimal Harness
Always compare:
- **Baseline**: Agent works with just a prompt
- **Minimal Harness**: Agent works with prompt + rules + verification
- Measure: completion rate, error rate, time to complete

### Pattern 2: Stop Agent From Declaring Victory Too Early
- Require explicit verification before "done"
- Use PostToolUse hooks to run tests
- Use Stop hooks to check quality gates
- Never trust "it works" without evidence

### Pattern 3: Long-Running Task Management
- Break into discrete steps with checkpoints
- Save state at each checkpoint
- Use sub-agents for parallel work
- Maintain a progress file

### Pattern 4: Multi-Session Continuity
- Write session summaries to memory
- Include context needed to resume
- Document decisions made and why
- Note what's pending vs complete

## Integration with OpenClaw

### Hooks (when available)
- `SessionStart`: Load project context
- `PreToolUse`: Validate commands against denylist
- `PostToolUse`: Run tests after file edits
- `Stop`: Check quality gates before completion
- `SessionEnd`: Write audit log

### Skills + Tools + Prompts
- **Prompts**: Guidance (model may or may not follow)
- **Skills**: Structured guidance with examples
- **Tools**: Deterministic capabilities
- **Hooks**: ALWAYS-RUN enforcement

**Rule**: If a rule says "always", "never", "block", "record", "run", or "verify" — it belongs in a hook or tool, NOT just in a prompt.

## Templates

### Minimal Harness Pack
Copy to new projects:
- `AGENTS.md` — Project rules and conventions
- `feature_list.json` — Tracked features/tasks
- `progress.md` — Current state and next steps

### Sub-agent Task Template
```
Task: <clear description>
Success Criteria: <testable outcomes>
Tools Allowed: <specific tools>
Output Format: <expected output>
Verification: <how to check>
Timeout: <max time>
```

## Metrics to Track
- Task completion rate
- Average time to complete
- Error/retry rate
- Context usage efficiency
- Sub-agent delegation success rate

## Related
- System Health Skill — periodic self-audit
- Agent Hooks Skill — deterministic control
- Context Compaction Skill — context management
