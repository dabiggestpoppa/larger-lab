# ALPHA-2R1.2 Report

**Checkpoint:** CRYPTO-ALPHA-2R1.2-F8-TRUTH-AND-RESOURCE-ARCHITECTURE-FREEZE  
**Timestamp:** 2026-08-24T21:00:00Z  
**Base SHA:** 4a903a7c3d6e5ad357e3ff9f95945462f5d80c23

## Part A: F8 Evidence Truth Repair

### Bug Found

ALPHA-2R1.1 reconciliation script computed `pf_condition = obs_diff >= 0` where `obs_diff` was the bootstrap paired net_R mean difference. This is NOT the PF point-estimate comparison the frozen contract specifies.

### Corrected PF Comparisons

| Strat | Strat PF | Ctrl PF | Ctrl >= Strat | Old Script | Bug? |
|-------|----------|---------|---------------|------------|------|
| S006 | 0.59 | 0.80 | TRUE | FALSE | YES |
| S008 | 0.62 | 0.75 | TRUE | FALSE | YES |
| S009 | 0.71 | 0.74 | TRUE | FALSE | YES |
| S010 | 0.73 | 0.74 | TRUE | FALSE | YES |

4 strategies had their PF condition incorrectly recorded as False.

### F8 Canonical Status

The frozen contract text `control_net_PF >= strategy_net_PF (CI overlap)` is ambiguous. The parenthetical could be a conjunction gate, method descriptor, or primary condition.

Under fail-closed ambiguity rule: **F8_CANONICAL_STATUS = AMBIGUOUS_NON_DECISIVE**

F8 retained as descriptive evidence only. No strategy classification depends solely on F8.

### Impact

**ZERO** — all 13 strategies independently falsified by F3/F4/F6/F7/F10/F12.

### Corrected Counts

- PF condition TRUE: 7 strategies (S005, S006, S008, S009, S010, S011, S012)
- PF condition FALSE: 6 strategies (S001, S002, S003, S004, S007, S013)
- Old script count: 3 (S005, S011, S012)

### Generation-1 Status Preserved

- SURVIVORS: 0
- FALSIFIED: 13
- S002: POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED (F6+F7)
- S003: POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED (F6+F7+F10)

## Part B: Crypto Resource Architecture Freeze

Four new resources documented for future crypto research:

1. **DefiLlama** — onchain/DeFi/capital-flow backbone
2. **Boros by Pendle** — funding-rate/fixed-vs-floating yield market
3. **PERPDEXLIST** — perp venue discovery + cross-venue dislocation discovery
4. **Derivatives Monkey** — options analytics discovery + cross-venue volatility crosscheck

### Resource Authority Hierarchy (Frozen)

| Level | Authority | Examples |
|-------|-----------|----------|
| 1 | Native venue/protocol API | Hyperliquid, Binance, Deribit |
| 2 | High-quality aggregated fundamental | DefiLlama |
| 3 | Specialized analytics/discovery | Derivatives Monkey, PERPDEXLIST |
| 4 | Prior art/ideas/social | Research papers, Twitter |

No lower-level source may override higher-level venue truth.

### Future Lanes Documented

- **CRYPTO-RATES**: funding, carry, fixed-vs-floating, Boros YU
- **CRYPTO-OPTIONS**: IV, term structure, skew, GEX, options flow
- **CRYPTO-CAPITAL-FLOW**: TVL, stablecoins, DEX volume, yield conditions

### Payoff Router Concept

Documented future conceptual router:
MARKET → STATE → CONSTRAINT → DISLOCATION → RESOLUTION PATH → PAYOFF OBJECT → EXECUTION COST → CAPITAL ROUTING

**NOT IMPLEMENTED. Plan only.**

## Test Results

- All existing test suites pass unchanged (67/67)
- No PnL replayed
- No strategies modified

## Next Checkpoint

CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-NEW-HYPOTHESES
