# MEMORY.md — Hermes Agent Memory

> Tier 1 memory. Loaded at every session start. Max ~2,200 chars.

## Workspace Conventions

### Tools & Skills Discovery
- **WORKSPACE_TOOLS_AND_SKILLS.md** — Complete guide to available tools and skills
- Skills are in `.agents/skills/` and `.github/skills/`
- Tools are Python scripts in `tools/`
- Use `ls .agents/skills/ | grep <keyword>` to find relevant skills

### Key Tools
- `phase-gate.py` — Phase transitions
- `progress-sync.py` — Sync agent progress
- `create_tool.py` — GitHub repo → agent tool pipeline
- `md2html.py` — Markdown to HTML conversion
- `html_viewer.py` — Local HTTP server for docs

### Key Skills by Domain
- **Web/API**: web-coder, fastapi-python, nodejs-backend-patterns
- **Data**: pandas-pro, senior-data-scientist, quantitative-research
- **Trading**: vectorbt-expert, mt5-strategy-tester, tradingview-quantitative
- **Pine Script**: pine-developer, pine-debugger, pine-manager
- **MCP**: mcp-builder, mcp-cli, claude-hermes-mcp

### Phase 9 Status
- **Current Phase**: PHASE_9 (Entropy Economics)
- **Success Criteria**: 6 items (all false currently)
- **Next**: AS/PM/RL to implement coherence-per-resource optimization

### Gateway Status
- **OC1** (port 18789): Deprecated — not in use
- **OC2** (port 18790): ✅ Operational — sole OpenClaw gateway
- **Hermes** (port 8642): Configured, awaiting activation