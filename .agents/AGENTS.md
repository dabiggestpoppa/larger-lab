# AGENTS.md — Agent Team Manifest

> **Architecture**: All agents follow the **Agent Harness** pattern — a production-grade system of 12 components (orchestration loop, tools, memory, context management, prompt construction, output parsing, state management, error handling, guardrails, verification loops, subagent orchestration). Each agent has an identity layer (`SOUL.md`), tiered memory, and access to self-evolving skills via the `skills/` directory.
>
> **Coding Standards**: All agent behavior is governed by the **12-rule CLAUDE.md** at the repo root (Karpathy's 4 foundational rules + 8 operational rules for multi-step agent workflows). See `CLAUDE.md` for the full behavioral contract.

## Team Roster

| Agent | Role | File | Key Responsibilities |
|-------|------|------|---------------------|
| 🎯 **Orchestrator** | Workflow coordinator & task routing | `orchestrator.agent.md` | Decomposes tasks, maps dependencies, runs parallel subagents, manages todo lists, triggers GEPA optimization |
| 🐛 **Debugger** | Bug diagnosis & fix specialist | `debugger.agent.md` | Error triage, stack trace analysis, hypothesis testing, regression checks, harness error classification |
| 🏗️ **Architect** | System design & blueprint creation | `architect.agent.md` | Component decomposition, data flow design, harness architecture, scalability planning |
| 🧠 **Memory Engineer** | Knowledge management & vector stores | `memory-engineer.agent.md` | 3-tier memory (Tier 1: MEMORY.md/USER.md, Tier 2: SQLite FTS5, Tier 3: external providers), vector stores, retrieval patterns |
| ✅ **QA Agent** | Testing, validation & quality gates | `qa-agent.agent.md` | Test planning/writing, Karpathy rule compliance, verification loops, coverage analysis, performance benchmarks |
| 🚀 **DevOps Agent** | Deployment, infra & CI/CD | `devops-agent.agent.md` | Environment setup, containerization, CI/CD, secrets management, monitoring |
| 🔍 **Research Agent** | Investigation & analysis | `research-agent.agent.md` | Deep research, source validation, competitive intelligence, knowledge structuring |
| 📝 **Code Reviewer** | Code quality & refactoring | `code-reviewer.agent.md` | Static analysis, Karpathy 12-rule enforcement, performance review, security audit |

## Agent Identity (SOUL.md)

Every agent profile has a `SOUL.md` — a static identity file that is **slot #1 in the system prompt**. It defines personality, tone, communication style, and hard limits. All memory and skills are filtered through this identity lens.

- Repo root `SOUL.md` → default agent identity
- Per-profile `~/.hermes/profiles/<name>/SOUL.md` → specialized identity (designer, programmer, researcher, etc.)

## Memory Architecture (3 Tiers)

| Tier | Storage | Capacity | Use Case |
|------|---------|----------|----------|
| **Tier 1** | `MEMORY.md` (~2.2K chars) + `USER.md` (~1.4K chars) | Tiny, always in context | Environment notes, project conventions, user preferences |
| **Tier 2** | SQLite with FTS5 full-text search | Unlimited, on-demand | Session history search across weeks of conversations |
| **Tier 3** | External memory providers (8 plugins) | Deep persistent | Vector stores, knowledge graphs, long-term recall |

## Self-Evolving Skills

Agents create their own `SKILL.md` files autonomously when they:
- Complete complex tasks (≥5 tool calls)
- Hit errors and find working paths
- Receive user corrections
- Discover non-trivial workflows

The **Curator** runs background maintenance: unused skills ≥30 days → stale, ≥90 days → archived. Never auto-deletes — archival is recoverable.

## Hermes 5 Pillars (Mental Model)

All agents in this workspace follow the Hermes 5-Pillar model:

| Pillar | Description | Implementation |
|--------|-------------|----------------|
| **Memory** | Wake up with context, never stateless | Tier 1 (MEMORY.md/USER.md), Tier 2 (SQLite FTS5), Tier 3 (external) |
| **Skills** | Procedural memory — reusable playbooks | SKILL.md files with YAML frontmatter, progressive disclosure |
| **Soul** | Personality layer — shapes tone and behavior | SOUL.md (slot #1 in system prompt), evolves with feedback |
| **Crons** | Scheduled automation — natural language scheduling | Isolated sessions, CONTEXTFROM chaining, NOAGENT for scripts |
| **Self-Improving Loop** | Do work → get feedback → save → repeat | Auto-extract facts, create skills from patterns, GEPA optimization |

## Multi-Agent Org Structure

**When to spin up a new agent:**
- Needs its own credentials, secrets, or tools → **New agent**
- Needs its own long-term memory → **New agent**
- Ongoing, repeated work that's basically a separate role → **New agent**
- Otherwise → Keep it in the main personal agent

**Bad pattern**: One mega-agent with every API key, every skill, every cron. High confusion, high blast radius.

**Good pattern**: Main personal agent + split-off agents per vertical (marketing, finance, content). Each in own Docker container with scoped keys and own `.env`.

## /goal Autonomous Execution Pattern

For long-running autonomous tasks, use the `/goal` pattern:

```
/goal [do the work] until [measurable end state] without [constraints]
```

Example: `/goal fix every failing test until npm test exits 0 without modifying files outside /auth`

- **Goal**: What to do (one line)
- **Measurable end state**: What "done" looks like
- **Constraints**: Rules the agent must abide by
- Pair with `/plan`: workflow is `/goal` → `/plan` → `/goal clear`
- Use `/pause` to pause, `/goal clear` to reset

## GEPA (Genetic-Pareto Prompt Evolution)

Offline skill optimization pipeline (`hermes-agent-self-evolution`):
1. Read current skill + execution traces
2. Generate evaluation dataset (synthetic + real history)
3. Run evolutionary search for candidate variants
4. Evaluate with LLM-as-judge scoring
5. Apply constraint gates (100% tests pass, <15KB, semantic stability)
6. Best variant → PR, never direct commit

Cost: ~$2–10/run. No GPU required.

## How to Use This Team

### Single-Agent Mode
Pick the agent that matches your current need and invoke it:
- "Debugger, this code is throwing X error — fix it"
- "Architect, design a system for Y"
- "Research Agent, investigate Z technology"

### Multi-Agent Pipeline (Orchestrator-Led)
For complex projects, invoke the Orchestrator first:
1. **Orchestrator** decomposes the task into sub-tasks
2. Assigns sub-tasks to appropriate specialists
3. Runs independent tasks in parallel
4. Aggregates results and tracks progress

### Common Workflow Patterns

**Build a new feature:**
```
Architect → designs system → Code Reviewer validates → QA tests → DevOps deploys
```

**Debug a production issue:**
```
Debugger diagnoses → Research Agent investigates root cause → Code Reviewer reviews fix → QA validates
```

**Set up a new project:**
```
Architect creates blueprint → DevOps sets up environment → Memory Engineer configures knowledge base → Orchestrator coordinates
```

**Research & prototype:**
```
Research Agent investigates → Architect designs solution → Orchestrator builds pipeline → QA validates
```

## Agent Communication Protocol
- Agents delegate via `runSubagent` with structured data passing
- Orchestrator maintains the master todo list and progress tracking
- Memory Engineer ensures all findings persist to shared memory
- All code changes go through Code Reviewer before merge
- QA gates every deployment with verification loops

## Skill Installation

From the [Skills Marketplace](https://skillsmp.com) or custom repos:
```bash
# Install from SkillsMP
skills install <skill-name>

# Add custom GitHub repo as skill tap
hermes skills tap add <owner>/<skills-repo>
hermes skills install <owner>/<skills-repo>/<skill-name>
```

Key skills for this workspace:
- `code-review-skill` — Automated code quality checks
- `workflow-automation-agent` — Task decomposition and tool mapping
- `skill-creator-meta-skill` — Generate new skills from goals
- `deep-research-synthesizer` — Synthesize large research datasets
- `devops-assistant` — Version control and deployment guidance
- `goal-mode` — Autonomous task execution via `/goal` command
- `hermes-maintenance` — Agent hygiene, audit routines, compaction handling
- `github-backup` — Automated backup of memory/skills to private repo

## MCP Server Integration

The MT5 MCP server (`mt5-mcp/`) provides 13 tools for strategy building. Any MCP-compatible client can connect:

- **Hermes** — via MCP stdio (Telegram bridge) or SSE transport
- **Claude Code** — via MCP stdio (desktop IDE)
- **OpenClaw** — via MCP stdio or SSE (remote)

### Connection Configurations

#### Option A: Stdio (local, recommended for Claude Code / Cursor)

Create `mcp-config-stdio.json` in your project root:
```json
{
  "mcpServers": {
    "mt5": {
      "command": "python",
      "args": ["C:/path/to/larger-lab/mt5-mcp/mt5_mcp_server.py"]
    }
  }
}
```

#### Option B: SSE (remote/headless, for Hermes or OpenClaw)

Start with SSE transport:
```bash
python mt5_mcp_server.py --transport sse --port 50051
```

Then connect via:
```json
{
  "mcpServers": {
    "mt5": {
      "url": "http://localhost:50051/mcp"
    }
  }
}
```

### Connection Workflow

1. **Start the MT5 MCP server**:
   ```bash
   python mt5_mcp_server.py
   ```

2. **Configure your agent** to use the stdio or SSE transport as shown above.

3. **Use the tools** (e.g., `mt5_create_ea`, `mt5_backtest_python`) in your agent prompts.

**Note**: The MT5 MCP server must have MetaTrader 5 running for live data and trading operations.

## Maintenance Rules (Agent Hygiene)

Keep agents sharp with these rules:
- **Wrong twice on same thing** → Correct immediately + update skill/memory
- **Same instruction twice** → Ask agent to write a skill for it
- **Verbose or off-tone** → Edit SOUL.md
- **New scheduled task** → Build a skill, then schedule it
- **Something breaks** → Check MEMORY.md first (stale memory = #1 cause of weird behavior)
- **Audit routine**: "Read me your memory file. Read me your soul file." Cut what's wrong.

## Security Model (Treat Agents Like New Hires)

- Each agent gets its own accounts (Gmail/agent mail), not yours
- Each agent gets its own API keys, scoped tight
- Named API keys per agent for spend tracking
- Least privilege: only credentials and tools needed for the job
- Marketing agent doesn't need read access to QuickBooks
- Set up firewall on VPS, restrict to your IP, block unused ports
- Build a skill that runs a nightly security audit
- Never paste API keys in chat — use config commands that write to `.env`

## Hermes vs Claude Code vs OpenClaw

These are complementary tools, not replacements:

| Tool | Role | Best For |
|------|------|----------|
| **Claude Code** | Desk-based coding assistant | File operations, git, deep coding at terminal |
| **Hermes** | On-the-go agent via Telegram | Scheduled jobs, quick tasks, voice, pocket agent |
| **OpenClaw** | Messaging-first agent | Multi-platform messaging, on-the-go automation |

All three can run side-by-side on the same repo. Business context, skills, and memory live in version control. Each agent understands its own conventions (CLAUDE.md vs AGENTS.md vs Hermes files). Tell it "make this repo work for you" and it adapts.

**CLI vs Telegram (Hermes):**
- **CLI** = cockpit. Deep work, coding, full context visibility, slash commands.
- **Telegram** = remote control. Scheduled jobs, quick tasks, voice. Don't vibe code from Telegram (context rot risk).