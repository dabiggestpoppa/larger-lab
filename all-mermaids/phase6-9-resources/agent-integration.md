# Agent Integration Points — Phase 6-9 Resources

> Source: CODEMAP.md (line 28 area)
> Phase: 6-9 Resources | Updated: 2026-05-18

## OpenClaw 2 (OC2) Gateway
- **URL:** `ws://127.0.0.1:18790`
- **Config:** `.openclaw/` (cleaned up - tmp files removed)
- **Status:** Running in read-only mode (Telegram/OpenRouter connectivity issues)
- **Watchdog:** 60s health checks
- **Context Monitor:** 75%/90%/95% alerts

## Hermes Agent v0.14.0
- **Interface:** Telegram @OC2BLRBOT
- **Config:** `.hermes/config/config.yaml`
- **Model:** `openrouter/owl-alpha`
- **Curator:** Enabled with prompt_caching TTL 5m
- **Status:** Healthy (doctor verified)

## Nautilus Trader
- **Strategies:** `nautilus/strategies/`
- **Data:** `nautilus/data/` (parquet format)
- **Reports:** `nautilus/reports/`

## SRRA-OPH Components
- **Core:** `srrs_opc/` (33 Python files)
- **Tests:** `srrs_opc/tests/` (57 tests)
- **Docs:** `srrs_opc/docs/`
- **Phase 1:** CollarLayer + 4 patches + AgentBridge (7 modules, 139 tests)
- **Phase 2:** Recovery anchors, drift detector, consistency validator, reconstruction synthesizer (5 modules, 52 tests)
- **Phase 3:** Dynamic coupling, topological router, distributed consensus
- **Phase 3 Book 2:** Active collar fields, local consensus, capability fields, trajectory fields
- **Phase 4:** Workspace integration (8 modules)
- **Phase 5:** Long-horizon continuity & temporal compression (8 modules)
- **Phase 6:** Recursive topology introspection (4 modules)
- **Phase 7:** Multi-scale cognitive fields (7 modules, 70 tests)
- **Phase 8:** Operator coevolution (8 modules, 76 tests)
- **Phase 9:** Sovereign field emergence (6 modules, 169 tests)
- **Phase 10:** Recursive field computation (5 modules, 23 tests) ✅ COMPLETE
