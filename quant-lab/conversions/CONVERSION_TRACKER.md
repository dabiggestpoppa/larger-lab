# 📋 Strategy Conversion Tracker

> **Created:** 2026-05-18 01:34 EDT | **Manager:** Lab Manager v6
> **Mission:** Convert all 7 profitable strategies → PineScript + MQL5 → TradingView

## Status Legend
- 🔲 Not Started
- 🔄 In Progress
- ✅ Code Done
- ✅ Pine Done
- ✅ MQL5 Done
- 📺 TV Pushed
- ⚠️ TV Push Blocked — Needs MAD/OWL Action

## Strategies

| # | Strategy | WR | P&L | PF | Code | Pine | MQL5 | TV Push |
|---|----------|----|-----|----|----|------|------|---------|
| 1 | Composite_Alpha | 98.6% | +3537p | 703 | ✅ | ✅ | ✅ | ⚠️ |
| 2 | Deep_Mean_Reversion | 91.8% | +8746p | 112 | ✅ | ✅ | ✅ | ⚠️ |
| 3 | Failure_Repair | 50.0% | +817p | 1.81 | ✅ | ✅ | ✅ | ⚠️ |
| 4 | Dual_Engine | 51.2% | +757p | 1.60 | ✅ | ✅ | ✅ | ⚠️ |
| 5 | Blind_Structural_Chain | 43.1% | +2248p | 1.14 | ✅ | ✅ | ✅ | ⚠️ |
| 6 | P90P_Distribution | 20.0% | +150p | 1.14 | ✅ | ✅ | ✅ | ⚠️ |
| 7 | Two_Plays | 42.3% | +53p | 1.04 | ✅ | ✅ | ✅ | ⚠️ |

## Output Files

### Strategy Code (Python)
- `strategy-code/composite_alpha.py`
- `strategy-code/deep_mean_reversion.py`
- `strategy-code/failure_repair.py`
- `strategy-code/dual_engine.py`
- `strategy-code/blind_structural_chain.py`
- `strategy-code/p90p_distribution.py`
- `strategy-code/two_plays.py`

### PineScript (v5)
- `pinescript/Composite_Alpha.pine`
- `pinescript/Deep_Mean_Reversion.pine`
- `pinescript/Failure_Repair.pine`
- `pinescript/Dual_Engine.pine`
- `pinescript/Blind_Structural_Chain.pine`
- `pinescript/P90P_Distribution.pine`
- `pinescript/Two_Plays.pine`

### MQL5
- `mql5/Composite_Alpha.mq5`
- `mql5/Deep_Mean_Reversion.mq5`
- `mql5/Failure_Repair.mq5`
- `mql5/Dual_Engine.mq5`
- `mql5/Blind_Structural_Chain.mq5`
- `mql5/P90P_Distribution.mq5`
- `mql5/Two_Plays.mq5`

## Conversion Log

| Timestamp | Strategy | Action | Status |
|-----------|----------|--------|--------|
| 2026-05-18 01:34 | ALL | Tracker created | ✅ |
| 2026-05-18 01:35 | ALL | Strategy code isolated (7 files) | ✅ |
| 2026-05-18 01:38 | ALL | PineScript v5 written (7 files) | ✅ |
| 2026-05-18 01:42 | ALL | MQL5 written (7 files) | ✅ |
| 2026-05-18 01:43 | ALL | TV push via MCP attempted | ⚠️ |
| 2026-05-18 01:50 | ALL | TV push via browser attempted | ⚠️ |

## TV Push Blockers

### MCP Approach
- `tradingview-mcp-server` is a stdio-based MCP server
- Requires MCP client (JSON-RPC over stdin/stdout)
- Not invocable as CLI tool
- **Needs:** OpenClaw MCP client or manual invocation

### Browser Automation Approach
- TradingView Pine Editor uses Monaco editor
- Monaco API not exposed globally (`window.monaco` undefined)
- Editor element found but interaction via refs times out
- **Needs:** Extended browser automation session or manual paste

### Recommended Next Steps for MAD
1. **Manual paste:** Open each `.pine` file, copy content, paste into TradingView Pine Editor
2. **MCP client:** Use OpenClaw's MCP client to connect to TV-MCP server
3. **Extended browser session:** Spawn dedicated browser automation sub-agent with longer timeout

---

## V2 Fixes — Post Cost-Validation (2026-05-18 ~14:30 EDT)

After Phase 0 cost validation showed 8/10 strategies fail under real costs, v2 fixes were applied:

| Strategy | v2 Pine | v2 MQL5 | Key Fix |
|----------|---------|---------|---------|
| Blind_Structural_Chain | ✅ | ✅ | Time exit, 60% invalidation, trend filter |
| Failure_Repair | 🔲 | 🔲 | Needs v2 conversion |
| Dual_Engine | 🔲 | 🔲 | Needs v2 conversion |
| P90P_Distribution | 🔲 | 🔲 | Needs v2 conversion |
| Two_Plays | 🔲 | 🔲 | Needs v2 conversion |
| Fractal_Resolution | 🔲 | 🔲 | Needs v2 conversion |
| Stall_Harvest | 🔲 | 🔲 | Needs v2 conversion |
| Constraint_Anchor | 🔲 | 🔲 | Needs v2 conversion |

**Note:** Only BSC v2 has been converted so far. Remaining 7 v2 strategies need PineScript + MQL5 conversion.

## V3 Fixes — Cost-Optimized (2026-05-18 ~16:30 EDT)

After v2 fixes proved insufficient for 5 strategies, v3 cost-optimized fixes were written:

| Strategy | v3 Code | v3 Pine | v3 MQL5 | Key Fix |
|----------|---------|---------|----------|----------|
| Failure_Repair | ✅ | 🔲 | 🔲 | Wider TP (0.75x AR), stronger 2nd signal (2.0x), session filter (4-10 AM EST) |
| Dual_Engine | ✅ | 🔲 | 🔲 | Wider TP (0.80x AR), ADX > 25, session filter, 2h time exit |
| Two_Plays | ✅ | 🔲 | 🔲 | Cost-optimized parameters |
| Stall_Harvest | ✅ | 🔲 | 🔲 | Cost-optimized parameters |
| Constraint_Anchor | ✅ | 🔲 | 🔲 | Cost-optimized parameters |

**5 v3 code files written. 5/10 v3 PineScript conversions done. 0/10 v3 MQL5 conversions done.**

## V3 PineScript Status
| Strategy | v3 Pine | v3 MQL5 |
|----------|---------|----------|
| Deep_Mean_Reversion | ✅ | 🔲 |
| Composite_Alpha | ✅ | 🔲 |
| Blind_Structural_Chain | ✅ | 🔲 |
| P90P_Distribution | ✅ | 🔲 |
| Fractal_Resolution | ✅ | 🔲 |
| Failure_Repair | 🔲 | 🔲 |
| Dual_Engine | 🔲 | 🔲 |
| Two_Plays | 🔲 | 🔲 |
| Stall_Harvest | 🔲 | 🔲 |
| Constraint_Anchor | 🔲 | 🔲 |

---
*Last updated: 2026-05-18 16:50 EDT by OWL heartbeat*
