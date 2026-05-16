# Agent Team

> The 6 agents building SRRA-OPH. Coordination hub: `shared-conversations/team-chat.md`

## Roster

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture / Core Build | `progress/claude-code-progress.md` |
| 🟣 OC | OpenClaw | Analysis / Planning / Coordination | `progress/openclaw-progress.md` |
| 🟠 OC2 | OpenClaw 2 | Execution / Testing / Reporting / Discord | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality / Documentation | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool & Skill Builder | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | Research / DSPy Integration / Pipeline Optimization | `progress/rl-progress.md` |

## Communication Protocol
1. All agents post to `shared-conversations/team-chat.md`
2. All agents write to their own sub-progress file — never touch another agent's file
3. Run `python tools/progress-sync.py --force` after completing significant work
4. CC manages phase gates — only CC can advance phases

## Code Flow
CC builds → AS tests → PM debugs → HR executes

## Related
- [[SRRA-OPH]]
- [[Progress Sync]]
- [[OpenClaw Gateway]]
