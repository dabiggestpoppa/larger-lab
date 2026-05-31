# Team Roster — Agent Network

TYPE: agent
SUMMARY: Complete roster of all agents, their roles, and current status.
CAUSE: Every agent needs to know who's on the team and what they do.
FUNCTION: Quick reference for agent capabilities and delegation.

## Active Agents

| Tag | Agent | Role | Status |
|-----|-------|------|--------|
| 🔵 CC | Claude Code | Overseer / Architecture | Active |
| 🟠 OC2 | OWL | Primary Operator / Orchestrator | Active |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality | Standby |
| 🔴 PM | Polymorph | Debugger / Tool Builder | Active |
| 🔴 PM2 | Polymorph 2 | Experimental Track / Frontend | Active |
| 🟢 RL | OWL (Research Lead) | Research / DSPy | Standby |
| 🟢 HR | Hermes | Execution / Backtesting | Active |

## Agent Responsibilities

### CC (Claude Code) 🔵
- Oversees architecture and system design
- Translates MAD intent into task briefs
- Reviews quality before merge
- Certifies builds and writes certification reports
- Does NOT execute routine tasks — delegates to workers

### OC2 (OWL) 🟠
- Primary orchestrator of the unified field
- Manages O2C pipeline (distillation, journal, skills)
- Coordinates agent network
- Writes to Obsidian vault
- Monitors system health and entropy

### AS (Assistant Manager) 🟡
- Context monitoring across agents
- Quality assurance and documentation
- Stands by for quality review tasks

### PM (Polymorph) 🔴
- Debugging and tool building
- Frontend debugging and testing
- Infrastructure maintenance

### PM2 (Polymorph 2) 🔴
- Experimental track development
- Frontend development (Phase 00/01 panels)
- UI/UX implementation

### RL (Research Lead) 🟢
- Research and DSPy optimization
- Pattern analysis and alpha generation

### HR (Hermes) 🟢
- Execution and backtesting
- Trade execution monitoring
- Report generation

## Communication Protocol
- All agents check `shared-conversations/team-chat.md` before starting work
- After every code edit: Update own progress file + memory file
- After every 5 code edits: Post summary to team-chat.md
- Memory auto-syncs every 7 updates

RELATIONSHIPS: [[OC2 Identity]] [[System Architecture]] [[Foundational Principles]]

STATUS: active
SOURCE: AGENTS.md, team-chat.md
