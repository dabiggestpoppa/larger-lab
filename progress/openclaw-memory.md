# 🟣 OpenClaw — Working Memory

> **Auto-synced** from `progress/openclaw-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

---

## Current Context (2026-05-16 20:11:36 UTC)

### Status
🟢 Active

### Active Phase
P90 Pine → Nautilus Conversion + Backtest Engine

### Pending Tasks
- Tune P90 parameters (TP levels, SL multipliers, cascade windows)
- Run P90 on all pairs (GBPUSD, USDJPY, AUDUSD)
- Parse CEREBUS manual for Option A/B rules
- Coordinate with Hermes for execution tasks
- FMP Protocol: Add CØD logging to MEMORY.md
- SCOPE Protocol: Create scope_chain.py
- GSP-Lite: Define GlyphMessage schema

### Recent Activity
#### 🟣 [OC] 2026-05-15 18:27:00Z — P90 Unified Engine Bug Fix + Results
- **Bug found**: `est_h == 3` classification was DEAD CODE inside Asian session block
  - Asian block: `if est_h >= 19 or est_h < 3` — est_h==3 never enters this block
  - `ar_pips` was never set → all entry signals skipped
  - Fixed by moving classification OUTSIDE the Asian block
- **Fixed all 3 strategies**: cascade_combo, cascade_only, base
- **Results on EUR/USD (50k bars)**:
  - P90_Cascade_Combo: 34.2% WR, -7.71p P&L, 263 trades
  - P90_Cascade: 33.9% WR, -40.51p P&L, 257 trades
  - P90_Base: 35.6% WR, -138.47p P&L, 486 trades
- **Root cause of losses**: Only 11 trades hit TP2 (-50% AR), 143+ hit SL
  - Mean reversion target too far for most trades
  - Need parameter tuning or TP logic adjustment
- **Files**: `nautilus/strategies/p90_unified.py` (unified engine)
- **Results saved**: `nautilus/results/p90_unified_20260515_182727.json`

#### 🟣 [OC] 2026-05-15 20:44:00Z — Initial Setup
- OpenClaw gateway running on ws://127.0.0.1:18789
- Model routing configured with fallbacks
- Skills loaded from `.hermes/skills/` + `nautilus/`
- SRRA-OPH Phase 1 directives added to openclaw_prompt.md

#### 🟣 [OC] 2026-05-15 22:25:00Z — Discord Bot Setup Complete
- **blrr city** bot connected to Discord gateway
- Slash commands registered: `/hermes`, `/openclaw`, `/agent_status`
- @mention routing working — responds as active agent (Hermes default)
- Agent switching via `/hermes` and `/openclaw` commands
- Webhooks pre-configured in .env (Hermes + OpenClaw)
- Windows encoding fix applied (UTF-8 stdout)
- Bot running as background process on blrrr host
- **Note**: Separate Hermes/OpenClaw bot tokens still needed for independent bot instances

---

## Sync Metadata
- **Last Sync:** 2026-05-16 20:11:36 UTC
- **Progress File:** `progress/openclaw-progress.md`
- **Working Memory:** `progress/openclaw-memory.md`
- **Sync Threshold:** 7 updates
