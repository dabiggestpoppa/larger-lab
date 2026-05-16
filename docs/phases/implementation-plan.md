# 🚀 Implementation Plan — Post-Build Integrations

> Analysis of 5 external resources and what we can extract/implement now vs post-build.

---

## Resource 1: VILA-Lab/Dive-into-Claude-Code

**What it is:** Deep architectural analysis of Claude Code (1,884 files, ~512K lines). Reverse-engineered from leaked source.

### Key Insights We Can Use NOW:

| Insight | Current State | Implementation |
|---------|---------------|----------------|
| **98.4% infrastructure, 1.6% AI** | Our agents are model-heavy, harness-light | Build deterministic harness layer: permission gates, tool routing, context compaction |
| **5-layer context compaction** | No compaction — context grows unbounded | Implement: budget reduction → snip → microcompact → context collapse → auto-compact |
| **7 safety layers** | Basic file permissions | Add: tool pre-filtering, deny-first rules, auto-mode classifier, shell sandbox, non-restoration on resume, hook interception |
| **4 extension mechanisms by cost** | Ad-hoc skill loading | Formalize: hooks (zero cost) → skills (low) → plugins (medium) → MCP (high) |
| **Subagent sidechain files** | Subagents return full context | Write subagent transcripts to sidechain files, return only summaries |
| **Single queryLoop for all interfaces** | Separate code paths per agent | Unify: one agent loop, multiple interface adapters (Telegram, CLI, Discord, VS Code) |
| **9-step turn pipeline** | Ad-hoc turn execution | Formalize: settings → state → context → shapers → model → tools → permission → execution → stop check |

### Post-Build Implementation:
- Full 5-layer subsystem decomposition for our agent harness
- 7-layer safety system for Hermes/PM
- Context compaction pipeline (5 stages)
- Unified queryLoop for all agent interfaces

---

## Resource 2: HKUDS/CLI-Anything

**What it is:** Framework to auto-generate CLIs for any GUI software. 34.9k stars, 2,280 tests, 18+ applications.

### Key Insights We Can Use NOW:

| Insight | Current State | Implementation |
|---------|---------------|----------------|
| **7-phase CLI generation pipeline** | Manual tool building | Use pipeline: analyze → design → implement → plan tests → write tests → document → publish |
| **Dual-mode: REPL + subcommand** | Most tools are one-shot | Build stateful REPL for NautilusTrader, VectorBT |
| **--json flag on every command** | Inconsistent output formats | Standardize: all tool commands support `--json` for agent consumption |
| **Real software integration** | Toy implementations | Integrate real backends: NautilusTrader for backtesting, real market data |
| **Session management with undo/redo** | No session state | Add: project state files, undo/redo history, session locking |
| **SKILL.md per CLI** | Skills are ad-hoc | Auto-generate SKILL.md for each tool we build |
| **Agent-Hub for discovery** | Manual skill finding | Create local skill registry with auto-discovery |

### What We Can Clone & Adapt:
- `cli-anything-plugin/repl_skin.py` → unified REPL interface for our tools
- `cli-anything-plugin/HARNESS.md` → SOP for building agent tools
- `skill_generator.py` → auto-generate SKILL.md files
- Test patterns from existing harnesses (2,280 tests across 18 apps)

### Post-Build Implementation:
- Full CLI-Anything pipeline for NautilusTrader
- Auto-generated CLIs for all trading tools
- Agent-Hub for skill discovery

---

## Resource 3: Ole Lehmann's 9 Hermes Workflows (X post)

**What it is:** 9 production-tested workflows for a Chief of Staff AI agent.

### Implementable NOW:

| # | Workflow | Tools Needed | Priority |
|---|----------|-------------|----------|
| 1 | **Daily Brief** — calendar + email + weather + headlines → Telegram | Google Calendar API, Gmail API, weather API, RSS | 🔴 HIGH |
| 2 | **Viral Swipe File** — auto-extract engaging posts → structured file | X API, LinkedIn API, Threads API | 🟡 MEDIUM |
| 3 | **Trending Workflows Radar** — scan Reddit/X/AI forums → ranked list | Reddit API, X API, web scraping | 🔴 HIGH |
| 4 | **Meeting Prep Briefing** — 30min before: attendees + context → Telegram | Google Calendar, LinkedIn API, Gmail | 🔴 HIGH |
| 5 | **The Humanizer** — audit text for AI tells → rewrite naturally | Local LLM skill | 🔴 HIGH |
| 6 | **Bookmark Inbox** — X bookmarks → summarize → tag → Obsidian | X API, Obsidian API | 🟡 MEDIUM |
| 7 | **Customer Support Cron** — scan inbox → categorize → Discord | Gmail API, Discord webhook | 🟡 MEDIUM |
| 8 | **Weekly Business Report** — Stripe + newsletter + content → dashboard | Stripe API, newsletter API, analytics | 🟡 MEDIUM |
| 9 | **Obsidian LLM Wiki** — daily reports → Obsidian vault | Obsidian API, Telegram/Discord | 🔴 HIGH |

### Post-Build:
- All 9 workflows as Hermes cron jobs
- Integration with our existing Telegram bot
- Obsidian vault as second brain

---

## Resource 4: Akshay Pachaar's Claude Code Analysis (X post)

**What it is:** Summary of the VILA-Lab paper with key takeaways.

### Key Takeaways for Our Build:
1. **Harness > Model** — Invest in infrastructure, not model switching
2. **Permission system with ML classifier** — Auto-approve 93% of safe prompts
3. **Context compaction is critical** — 5 layers, cheapest first
4. **Extension cost ordering** → hooks < skills < plugins < MCP
5. **Subagent sidechain files** — Don't pollute parent context
6. **Trust re-established every session** — No persistent permissions

---

## Resource 5: Alvaro Cintas — agentmemory (X post)

**What it is:** Tool that records agent sessions, compresses with AI, injects context next session. 4,000+ stars.

### Implementation:
```bash
# Clone and integrate
git clone https://github.com/anthropics/agentmemory.git
```

### What it does:
- Records what agent does every session
- Compresses with AI
- Injects right context when next session starts

### Our Integration:
- Add to Hermes' session startup
- Add to PM's session startup
- Compress daily, inject on resume

---

## 📋 Implementation Priority

### Phase A — Can Do Now (During Build):
1. ✅ Copy `repl_skin.py` from CLI-Anything → `tools/repl_skin.py`
2. ✅ Copy `HARNESS.md` SOP → `docs/agent-harness-sop.md`
3. ✅ Implement 5-layer context compaction for Hermes
4. ✅ Build `--json` flag standard for all tool commands
5. ✅ Create subagent sidechain file pattern
6. ✅ Implement Ole Lehmann's workflows 1, 3, 4, 5, 9 (highest priority)
7. ✅ Add agentmemory integration

### Phase B — Post-Build:
1. Full 7-layer safety system
2. Unified queryLoop for all agent interfaces
3. CLI-Anything pipeline for NautilusTrader
4. Agent-Hub for skill discovery
5. All 9 Ole Lehmann workflows as cron jobs
6. Full 5-layer subsystem decomposition
