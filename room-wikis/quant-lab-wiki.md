# Quant Lab Room Wiki

> **Purpose:** Resource hub for the Quant Lab. The team's bible for strategy development.

## Team
- **Manager:** labmanagercheckpoint (active)
- **Strategists:** (spawned as needed via POLYGENT)

## Strategy Bible
- quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md â€” Full manual (140+ pages)
- quant-lab/research/151-trading-strategies-reference.md â€” Kakushadze & Serur
- quant-lab/research/arxiv/paper-summaries.md â€” 6 ArXiv papers
- quant-lab/research/rohonchain/strategy-guide.md â€” RohOnChain methodology

## Key Files
| File | Purpose |
|------|---------|
| quant-lab/results/cost-validation-2026-05-18.md | Cost validation (2/10 survive) |
| quant-lab/research/BSC_GAP_ANALYSIS.md | BSC 64pp gap analysis |
| quant-lab/results/spread-analysis.json | Spread data for 12 pairs |
| quant-lab/conversions/strategy-code/ | 7 Python strategy files |
| quant-lab/conversions/pinescript/ | 7 PineScript files |
| quant-lab/conversions/mql5/ | 7 MQL5 files |
| quant-lab/progress/manager-progress.md | Manager checkpoint progress |

## Cost Model
- Spread: 0.2 pips (forex) â€” CSV SPREAD column / 10
- Commission: /lot round-turn
- Slippage: 1 pip entry + 1 pip exit
- Position sizing: 5% of equity per trade
- Total cost: ~2.9 pips/trade

## 10 Strategies Status
| Strategy | PF (after costs) | Status |
|----------|-----------------|--------|
| Deep_Mean_Reversion | ~45 | âœ… Production ready |
| Composite_Alpha | ~285 | âš ï¸ Needs forward test |
| Failure_Repair | 0.82 | ðŸ”´ Fails |
| Dual_Engine | 0.62 | ðŸ”´ Fails |
| Blind_Structural_Chain | 0.52 | ðŸ”´ Fails (gap analysis done) |
| P90P_Distribution | 0.68 | ðŸ”´ Fails |
| Two_Plays | 0.55 | ðŸ”´ Fails |
| Fractal_Resolution | 0.35 | ðŸ”´ Fails |
| Stall_Harvest | 0.52 | ðŸ”´ Fails |
| Constraint_Anchor | 0.42 | ðŸ”´ Fails |

## Data Files
- C:\Users\wifik\Downloads\ â€” 27 CSV files (tab-separated)
- Columns: DATE/TIME/OPEN/HIGH/LOW/CLOSE/TICKVOL/VOL/SPREAD
- Pairs: EUR/USD, USD/CHF, GBP/USD, USD/JPY, USD/CAD, AUD/USD, NZD/USD, CHF/JPY
- Indices: DE30, FR40, US500, USTEC100
- Timeframes: M1, M5

## Key Findings
- Exit bug in optimizer_v2: SL/TP arguments swapped (fixed in v4)
- Stall_Harvest 100% WR was a reporting artifact â€” real performance 26-60% WR
- BSC gap root cause: no time exit + wide invalidation + no trend filter
- Best session: 7-11 across all pairs. Worst: 2-4 (Asian session)

## Tools
- TradingView MCP (stdio-based, needs MCP client)
- Supertonic TTS (on-device, 31 languages)

---
*Last updated: 2026-05-18 by OWL*
*Maintained by: RA (Resource Adapter)*
