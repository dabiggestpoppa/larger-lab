# Agent Integration Points — Phase 6-9 Resources

> Source: CODEMAP.md (line 28 area)
> Phase: 6-9 Resources

## OpenClaw Gateway
- **URL:** `ws://127.0.0.1:18789`
- **Config:** `~/.openclaw/openclaw.json`
- **Skills:** `.hermes/skills/` + `nautilus/`

## Hermes Telegram Bot
- **Interface:** Telegram messages
- **Skills:** `.hermes/skills/`
- **Memory:** `.hermes/MEMORY.md`

## Nautilus Trader
- **Strategies:** `nautilus/strategies/`
- **Data:** `nautilus/data/` (parquet format)
- **Reports:** `nautilus/reports/`

## SRRA-OPH Components
- **Core:** `srrs_opc/` (25 Python files)
- **Tests:** `srrs_opc/tests/`
- **Docs:** `srrs_opc/docs/`
- **Phase 1:** CollarLayer + 4 patches + AgentBridge
- **Phase 2:** Recovery anchors, drift detector, consistency validator, reconstruction synthesizer
- **Phase 3:** Dynamic coupling, topological router, distributed consensus
- **Phase 3 Book 2:** Active collar fields, local consensus, capability fields, trajectory fields
- **Phase 4:** Workspace integration (Active)
