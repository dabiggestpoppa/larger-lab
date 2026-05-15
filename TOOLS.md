# TOOLS.md — OpenClaw Agent Tools Reference

> This file is auto-loaded by OpenClaw as part of the workspace context.
> It defines available tools, MCP servers, and agent capabilities.

## MCP Servers

### MT5 MCP Server
- **Name**: `mt5`
- **Transport**: stdio
- **Command**: `python mt5-mcp/mt5_mcp_server.py`
- **Tools**: 13 tools for MT5 strategy building
  - `mt5_connect` — Connect to MT5 terminal
  - `mt5_get_account_info` — Account details
  - `mt5_get_market_data` — OHLCV candle data
  - `mt5_get_symbols` — List available symbols
  - `mt5_create_indicator` — Generate MQL5 indicator
  - `mt5_create_ea` — Generate MQL5 Expert Advisor
  - `mt5_write_mql5` — Write raw MQL5 code
  - `mt5_compile_file` — Compile via MetaEditor
  - `mt5_backtest_python` — Python simulation backtest
  - `mt5_backtest_terminal` — Full MT5 Strategy Tester
  - `mt5_optimize` — Parameter optimization
  - `mt5_open_trade` — Open live/demo trade
  - `mt5_get_positions` — View open positions
  - `mt5_close_trade` — Close a position
  - `mt5_get_last_report` — Fetch backtest report
  - `mt5_list_files` — List MQL5 files

## Agent Team

See `.agents/AGENTS.md` for the full team roster. Key agents:
- **Orchestrator** — Task decomposition, dependency mapping, parallel execution
- **Architect** — System design, component decomposition
- **Debugger** — Error diagnosis and fix
- **Memory Engineer** — Knowledge management, 3-tier memory
- **QA Agent** — Testing, verification loops
- **DevOps Agent** — Deployment, CI/CD
- **Research Agent** — Investigation, analysis
- **Code Reviewer** — Code quality, Karpathy 12-rule compliance

## Skills Directory

Skills are loaded from:
- `.hermes/skills/` — Hermes-compatible skills (goal-mode, hermes-maintenance, github-backup)
- `mt5-mcp/skills/` — MT5 strategy builder skill
- `skills/` — General workspace skills

## Behavioral Contract

All agents operate under the 12-rule CLAUDE.md at the repo root.
See `SOUL.md` for identity layer, `.agents/AGENTS.md` for team manifest.

## Workspace Structure

```
larger-lab/
├── .agents/           # Agent specifications
├── .hermes/           # Hermes config (MEMORY.md, USER.md, SOUL.md, skills/)
├── mt5-mcp/           # MT5 MCP server + skills
├── nautilus/          # Nautilus Trader backtest engine
├── strategies/        # Trading strategies
├── data/              # Market data
├── CLAUDE.md          # 12-rule behavioral contract
├── SOUL.md            # Agent identity
└── TOOLS.md           # This file
```
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
