# Research Agents Work Stream — Progress Tracker

> **Created:** May 15, 2026
> **Parent:** `PROJECT_PROGRESS.md` → Research Agents
> **Purpose:** Track development of Twitter Research Agent and GitHub Discovery Agent.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete / Operational |
| ⏳ | In Progress |
| 📋 | Planned / Not Started |
| ⚪ | Deferred / Skipped |

---

## 1. Twitter Research Agent

**Location:** `agent-lab/agents/research/twitter-research/`

| Component | Status | Notes |
|-----------|--------|-------|
| `twitter_research_agent.py` | ✅ Complete | Full implementation with OPH overlap channel |
| `config.json` | ✅ Complete | Agent configuration and command definitions |
| `SKILL.md` | ✅ Complete | Hermes skill definition |
| `workspace/` directory | ✅ Created | Knowledge DB, discoveries log, seen cache |
| Twitter API integration | ⏳ Needs token | `TWITTER_BEARER_TOKEN` env var required |
| `/twitter-research` command | ✅ Implemented | Supports keywords, hours, max params |
| `/twitter-top` command | ✅ Implemented | Shows top insights by relevance |
| `/twitter-search` command | ✅ Implemented | Searches existing knowledge base |
| `--extract-tools` flag | ✅ Implemented | Extracts tool/repo mentions from tweets |
| OPH overlap channel | ✅ Implemented | Writes to `shared/overlap-log.jsonl` |
| Scheduled cron job | 📋 Not configured | Set up via Hermes when ready |

### Test Commands (once token is set)
```bash
# Search for AI agent frameworks
TWITTER_BEARER_TOKEN=xxx python twitter_research_agent.py --keywords "AI agent framework" --max 50

# Extract tools from results
TWITTER_BEARER_TOKEN=xxx python twitter_research_agent.py --extract-tools

# Search existing knowledge
python twitter_research_agent.py --search "vector database"
```

---

## 2. GitHub Discovery Agent

**Location:** `agent-lab/agents/research/github-discovery/`

| Component | Status | Notes |
|-----------|--------|-------|
| `github_discovery_agent.py` | ✅ Complete | Full implementation with scoring + OPH |
| `config.json` | ✅ Complete | Agent configuration and command definitions |
| `SKILL.md` | ✅ Complete | Hermes skill definition |
| `workspace/` directory | ✅ Created | Known repos DB, discoveries log |
| GitHub API integration | ⏳ Needs token | `GITHUB_TOKEN` env var required |
| `/github-discover` command | ✅ Implemented | Multi-strategy search with scoring |
| `/github-discover --niche` | ✅ Implemented | Finds lesser-known repos |
| `/github-known` command | ✅ Implemented | Searches already-discovered repos |
| `/github-stats` command | ✅ Implemented | Shows agent statistics |
| Scoring algorithm | ✅ Implemented | Recency, stars, license, topics, ratio |
| 8 search strategies | ✅ Implemented | Diverse query patterns for coverage |
| OPH overlap channel | ✅ Implemented | Writes to `shared/overlap-log.jsonl` |
| Scheduled cron job | 📋 Not configured | Set up via Hermes when ready |

### Test Commands (once token is set)
```bash
# Discover AI frameworks
GITHUB_TOKEN=xxx python github_discovery_agent.py "autonomous agent framework"

# Niche discovery
GITHUB_TOKEN=xxx python github_discovery_agent.py "vector database" --niche

# Check stats
GITHUB_TOKEN=xxx python github_discovery_agent.py --stats

# Search known repos
python github_discovery_agent.py --known-search "RAG"
```

---

## 3. Shared Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| `shared/` directory | ✅ Created | For overlap channel files |
| `shared/README.md` | ✅ Created | Documents overlap protocol |
| `overlap-log.jsonl` | 📋 Created on first write | Append-only observation log |
| Reconciliation engine | 📋 Not started | `reconcile.py` — future phase |
| Consensus state | 📋 Not started | `consensus-state.json` — future phase |

---

## 4. OPH Integration Status

| OPH Layer | Status | Implementation |
|-----------|--------|----------------|
| Observer Patches | ✅ | Twitter + GitHub agents are separate patches |
| Local State | ✅ | Each agent has own workspace/ directory |
| Overlap Channel | ✅ | `shared/overlap-log.jsonl` |
| Overlap Hash | ✅ | SHA256-based content addressing |
| Reconciliation | 📋 Future | Needs `reconcile.py` engine |
| Consensus | 📋 Future | Needs `consensus-engine.py` |
| Identity Continuity | 📋 Future | Needs `identity.py` |

---

## 5. Next Steps

### Immediate (This Week)
- [ ] Set up Twitter Bearer Token → test Twitter agent
- [ ] Set up GitHub Token → test GitHub agent
- [ ] Run first discovery cycle for current project topics
- [ ] Verify overlap channel writes correctly

### Short Term (Week 2)
- [ ] Configure Hermes cron jobs for both agents
- [ ] Build `reconcile.py` for cross-patch reconciliation
- [ ] Test cross-patch correlation (Twitter tool mention ↔ GitHub repo)

### Medium Term (Week 3–4)
- [ ] Build consensus engine
- [ ] Add identity continuity layer
- [ ] Integrate with CEREBUS trading strategies (market sentiment from Twitter)
- [ ] Feed discovered GitHub tools into agent skill recommendations

---

## 6. Weekly Log

### Week 1 (May 15, 2026)
- [x] Twitter Research Agent — full implementation created
- [x] GitHub Discovery Agent — full implementation created
- [x] Both agents follow OPH observer-patch pattern
- [x] Shared overlap channel infrastructure created
- [x] SKILL.md files follow existing Hermes skill conventions
- [x] Config files define commands, schedules, and OPH alignment
- [ ] Set up API tokens and run first tests — NEXT