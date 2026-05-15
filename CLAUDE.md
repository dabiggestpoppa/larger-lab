# CLAUDE.md — 12-Rule Behavioral Contract

> **Source**: Karpathy's 4 foundational rules (via [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)) + 8 operational rules (via [@Mnilax](https://x.com/Mnilax/status/2053116311132155938)).
> **Testing**: 30 codebases, 6 weeks — mistake rate dropped from 41% → 3%.
> **Limit**: Keep this file under 200 lines total. Past that, compliance drops sharply.

These rules apply to every task in this project unless explicitly overridden.
**Bias**: caution over speed on non-trivial work. Use judgment on trivial tasks.

---

## Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

## Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

## Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

## Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

## Rule 5 — Use the Model Only for Judgment Calls
Use me for: classification, drafting, summarization, extraction from unstructured text.
Do NOT use me for: routing, retries, status-code handling, deterministic transforms.
If code can answer, code answers.

## Rule 6 — Token Budgets Are Not Advisory
Per-task budget: 4,000 tokens.
Per-session budget: 30,000 tokens.
If approaching budget, summarize and start fresh. Surface the breach. Do not silently overrun.

## Rule 7 — Surface Conflicts, Don't Average Them
If two existing patterns in the codebase contradict, don't blend them.
Pick one (the more recent / more tested), explain why, and flag the other for cleanup.
"Average" code that satisfies both rules is the worst code.

## Rule 8 — Read Before You Write
Before adding code in a file, read the file's exports, the immediate caller, and any obvious shared utilities.
If you don't understand why existing code is structured the way it is, ask before adding to it.
"Looks orthogonal to me" is the most dangerous phrase in this codebase.

## Rule 9 — Tests Verify Intent, Not Just Behavior
Every test must encode WHY the behavior matters, not just WHAT it does.
A test like `expect(getUserName()).toBe('John')` is worthless if the function takes a hardcoded ID.
If you can't write a test that would fail when business logic changes, the function is wrong.

## Rule 10 — Checkpoint After Every Significant Step
After completing each step in a multi-step task: summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back to me.
If you lose track, stop and restate.

## Rule 11 — Match the Codebase's Conventions, Even If You Disagree
If the codebase uses snake_case and you'd prefer camelCase: snake_case.
If the codebase uses class-based components and you'd prefer hooks: class-based.
Disagreement is a separate conversation. Inside the codebase, conformance > taste.
If you genuinely think the convention is harmful, surface it. Don't fork it silently.

## Rule 12 — Fail Loud
If you can't be sure something worked, say so explicitly.
"Migration completed" is wrong if records were skipped silently.
"Tests pass" is wrong if you skipped any.
"Feature works" is wrong if you didn't verify the edge case that was asked about.
Default to surfacing uncertainty, not hiding it.

---

## Project-Specific Guidelines

### Agent Harness Architecture
- All agents follow the 12-component harness pattern (see `.agents/AGENTS.md`)
- Memory uses 3-tier architecture: Tier 1 (MEMORY.md/USER.md), Tier 2 (SQLite FTS5), Tier 3 (external providers)
- Self-evolving skills live in `skills/` directory as SKILL.md files
- GEPA optimization runs offline for skill improvement

### Coding Standards
- Python 3.11+ (see `.python-version`)
- Use `uv` for package management (see `pyproject.toml`)
- All code changes must pass through Code Reviewer agent before merge
- QA gates every deployment with verification loops

### Agent Communication
- Agents delegate via `runSubagent` with structured data passing
- Orchestrator maintains the master todo list
- Memory Engineer persists all findings to shared memory
- All agents load their SOUL.md identity before task execution

### Skills
- Install from Skills Marketplace: `skills install <name>`
- Create custom skills: use `skill-creator-meta-skill` pattern
- Skills self-evolve: agents create SKILL.md files for reusable procedures
- Curator prunes unused skills (≥30 days stale, ≥90 days archived)
