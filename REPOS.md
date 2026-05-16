# REPOS.md — GitHub Repos & Tools Inventory

> **Last Updated:** 2026-05-16
> **Purpose:** Central registry of all cloned GitHub repos, installed skills, and external tools in the lab.

---

## 📦 Cloned GitHub Repos

### Active Development Repos
| Repo | GitHub URL | Location | Purpose |
|------|-----------|----------|---------|
| **larger-lab** | `dabiggestpoppa/larger-lab` | `~/projects/larger-lab` | Main workspace — agent network, trading, research |
| **dydx-nautilus-bot** | `dabiggestpoppa/dydx-nautilus-bot` | `~/projects/dydx_nautilus_bot` | Dydx trading bot (NautilusTrader) |
| **backtesterpublic** | `dabiggestpoppa/backtesterpublic` | `~/projects/backtesterpublic` | Public backtesting framework |
| **market-structure** | `dabiggestpoppa/market-structure` | `~/projects/market-structure` | Market structure analysis tools |
| **react-agent** | `dabiggestpoppa/react-agent` | `~/projects/react-agent` | React-based agent UI |
| **rose-research** | `dabiggestpoppa/rose-research` | `~/projects/rose-research` | Research agent framework |
| **unsloth** | `dabiggestpoppa/unsloth` | `~/projects/unsloth` | ML model fine-tuning |

### External Tools & Frameworks
| Repo | GitHub URL | Location | Purpose |
|------|-----------|----------|---------|
| **openclaw** | `OpenClaw/openclaw` | `~/projects/openclaw` | OpenClaw gateway & agent platform |
| **CLI-Anything** | `HKUDS/CLI-Anything` | `~/projects/CLI-Anything` | CLI tooling framework |
| **Dive-into-Claude-Code** | `VILA-Lab/Dive-into-Claude-Code` | `~/projects/Dive-into-Claude-Code` | Claude Code deep-dive resources |

### Other Project Directories
| Directory | Location | Notes |
|-----------|----------|-------|
| **backtesting-py-2022** | `~/projects/backtesting-py-2022` | Legacy backtesting (dabiggestpoppa) |
| **cooperative-agent-lab** | `~/projects/cooperative-agent-lab` | Agent collaboration experiments |
| **mini-quant-lab** | `~/projects/mini-quant-lab` | Quant research sandbox |
| **larger-db** | `~/projects/larger-db` | Database storage |
| **quant-lab** | `~/projects/quant-lab` | Quant lab workspace |
| **memory-bank** | `~/projects/memory-bank` | Memory storage |

---

## 🛠️ Installed ClawHub Skills

> Located in `~/projects/larger-lab/skills/`

| Skill | Source | Purpose |
|-------|--------|---------|
| `twitter-bookmarks` | Custom | Twitter/X bookmarks reader via browser automation |
| `social-media-agent` | ClawHub | X/Twitter autonomous management (no API keys) |
| `godfery-tw` | ClawHub | X/Twitter search & post (SkillBoss API) |
| `use-my-browser` | ClawHub | Control real Chrome via Tampermonkey |
| `agent-team-workflow` | Custom | Multi-agent team workflow |
| `as-code-review` | Custom | Code review skill |
| `srra-oph-build` | Custom | SRRA-OPH build skill |
| `hermes-workflows` | Custom | Hermes agent workflows |
| `context-compaction` | Custom | Context compaction for agents |
| `agent-harness-sop` | Custom | Agent harness SOP |
| `subagent-manager` | Custom | Subagent management |

---

## 🔧 Key External Tools & Services

### OpenClaw Ecosystem
| Tool | Type | Purpose |
|------|------|---------|
| **OpenClaw Gateway** | Daemon | Agent gateway (ws://127.0.0.1:18789) |
| **Telegram Bot** | Channel | `@finalstrawclawbot` — remote agent access |
| **xurl** | CLI | X/Twitter API CLI (`@xdevplatform/xurl`) |
| **agentmemory** | Python pkg | Infinite memory for AI agents (ChromaDB-backed) |

### Trading & Quant
| Tool | Purpose |
|------|---------|
| **NautilusTrader** | Backtesting & live trading framework |
| **VectorBT** | Vectorized backtesting |
| **MT5** | MetaTrader 5 (deprecated, migration in progress) |
| **Oanda** | Forex broker API |

### AI/ML
| Tool | Purpose |
|------|---------|
| **Claude Code** | AI coding agent (desk) |
| **Hermes** | On-the-go engineer agent (Telegram) |
| **OpenClaw** | Analyst/planner agent (CLI + Gateway) |

---

## 📋 GitHub Repos to Explore / Add Later

> Bookmarked for future evaluation

| Repo | GitHub URL | Purpose | Status |
|------|-----------|---------|--------|
| **DroidDesk** | `orailnoor/DroidDesk` | Turn old Android into Linux desktop (Termux + X11 + Proot) | ⏳ Evaluate |
| **agentmemory** | `AgentMemory/agentmemory` | AI agent memory compression & injection | ✅ Installed (pip) |

---

## 🔄 Maintenance

- **Sync repos:** `git pull` in each directory periodically
- **Update skills:** `openclaw skills update` for ClawHub skills
- **Add new repos:** Clone to `~/projects/`, add entry above
