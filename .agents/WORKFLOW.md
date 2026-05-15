# Agent Workflow Guide

> **Architecture**: All phases follow the **12-component Agent Harness** pattern. See `AGENTS.md` for the full component reference.
> **Behavioral Contract**: All agents operate under the 12-rule `CLAUDE.md`. See `SOUL.md` for identity layer.

## Complex Agentic System Development Workflow

This guide describes how the 8 specialized agents collaborate to build, debug, and deploy complex agentic systems — with harness-aware practices at every phase.

---

## Phase 1: Discovery & Design

**Lead Agents:** Research Agent + Architect

1. **Research Agent** investigates the problem domain
   - Gathers requirements from stakeholders
   - Researches existing solutions and best practices (primary → secondary → tertiary sources)
   - Identifies constraints and technical risks
   - **Harness focus**: Context management strategy, memory requirements, tool needs

2. **Architect** creates system blueprint
   - Defines component boundaries and interfaces (map to 12 harness components)
   - Designs data flow and state management
   - Selects technology stack (consider agent ecosystem compatibility)
   - Creates architecture diagrams
   - **Harness focus**: Thin harness preference, verification-first design, subagent isolation strategy

**Output:** Architecture spec, technology decisions, implementation plan, harness component mapping

---

## Phase 2: Environment & Infrastructure

**Lead Agent:** DevOps Agent

1. Sets up development environment (support multi-agent local development)
2. Configures containerization (Docker) with volume mounts for memory/skills
3. Establishes CI/CD pipeline with harness integrity checks
4. Manages secrets and environment variables across agent profiles
5. Sets up monitoring and logging for agent systems (token usage, error rates, skill utilization)
6. **Harness focus**: Memory persistence (Tier 1/2/3), skills directory backup, cron scheduler config

**Output:** Running dev environment, deployment pipeline, monitoring dashboards

---

## Phase 3: Core Development

**Lead Agent:** Orchestrator (coordinates the team)

1. **Memory Engineer** builds the knowledge layer
   - Designs memory schemas (episodic, semantic, procedural, meta)
   - Implements 3-tier storage (Tier 1: MEMORY.md/USER.md, Tier 2: SQLite FTS5, Tier 3: vector store)
   - Sets up retrieval patterns (by context, similarity, recency)

2. **Code Reviewer** reviews each module as it's built
   - Catches bugs early
   - Enforces coding standards and Karpathy 12-rule compliance
   - Ensures testability and harness integration

3. **Debugger** fixes issues as they arise
   - Classifies errors (transient/LLM-recoverable/user-fixable/unexpected)
   - Applies targeted fixes with regression checks
   - Documents reusable fixes as SKILL.md entries

4. **Self-Evolving Skills** emerge during development
   - Agents create SKILL.md files for complex procedures (≥5 tool calls)
   - Curator runs background maintenance (unused ≥30d → stale, ≥90d → archived)

**Output:** Working codebase with passing tests, initial skill library

---

## Phase 4: Testing & Quality

**Lead Agent:** QA Agent

1. Writes comprehensive test suite (unit, integration, E2E, harness-level)
2. Validates environment configuration and harness component integrity
3. Runs performance benchmarks under realistic agent load
4. Checks security posture
5. Measures code coverage and identifies gaps
6. **Verification Loops** (3 types):
   - **Rules-based**: Tests, linters, type checkers for deterministic correctness
   - **Visual**: Screenshots/diff comparison for UI tasks
   - **LLM-as-Judge**: Separate subagent evaluates semantic quality against rubric
7. **Karpathy 12-Rule Compliance Audit**: Check every rule against the codebase

**Output:** Test report, coverage metrics, known issues list, compliance audit

---

## Phase 5: Deployment & Monitoring

**Lead Agent:** DevOps Agent

1. Deploys to staging/production with harness component verification
2. Configures health checks for all 12 harness components
3. Sets up alerting (token budget breaches, error rate spikes, skill failures)
4. Documents deployment procedures including harness configuration
5. **GEPA Pipeline**: Schedule offline skill optimization for production skill library

**Output:** Live system, monitoring dashboards, runbooks, GEPA optimization schedule

---

## Phase 6: Continuous Improvement

**Lead Agent:** Memory Engineer + Research Agent + Orchestrator

1. Agent learns from production data; Memory Engineer updates knowledge base
2. Research Agent tracks new developments (Skills Marketplace, agent ecosystem)
3. Architect plans next iteration based on production insights
4. **Curator** prunes stale skills and memory entries
5. **GEPA** optimizes high-value skills based on execution traces
6. Orchestrator updates workflow patterns based on lessons learned

---

## Emergency Response Workflow

For production incidents:

```
Debugger (diagnose + classify error type)
  → Research Agent (investigate root cause)
    → Code Reviewer (validate fix + Karpathy compliance)
      → QA (regression test + verification loops)
        → DevOps (deploy hotfix + monitoring)
```

**Checkpoint requirement** (Rule 10): After each step, summarize what was done, what's verified, what's left.

## Daily Standup Template

Each agent reports:
- What I completed yesterday
- What I'm working on today
- Any blockers or dependencies
- Confidence level (High/Medium/Low)
- **Harness status**: Any component issues (memory, tools, context, errors)

## Skill Lifecycle

```
Created (agent-authored) → Used (loaded on demand) → Maintained (Curator)
  → Optimized (GEPA offline) → Archived (unused ≥90 days) → Recovered (if needed)
```

- Skills are **model-invoked** (AI decides when to use them based on context)
- Skills are **modular** and designed to work together
- All skills use the open **SKILL.md** standard (compatible with Claude Code, Cursor, Codex CLI)
- Install from [Skills Marketplace](https://skillsmp.com) or custom GitHub repos