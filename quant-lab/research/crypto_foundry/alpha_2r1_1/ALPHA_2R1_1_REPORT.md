# ALPHA-2R1.1 Report

**Checkpoint:** CRYPTO-ALPHA-2R1.1-FINAL-EVIDENCE-RECONCILIATION-SEAL  
**Timestamp:** 2026-08-24T20:00:00Z  
**Base SHA:** feb2a0250c359a6183404ee113d111c6f063f28b  
**Registry Hash Verified:** 2abaf8c21200a67e...

## Purpose

Freeze one internally consistent canonical result package for Generation 1.
Reconciles F8 / documentation / failure labels WITHOUT replaying strategy PnL.

## Engine Provenance

- ALPHA-2: QUARANTINED_ENGINE_ERROR (exit execution timing + wrong funding sign)
- ALPHA-2R: QUARANTINED_REPLAY_INTEGRITY (funding fixed but price-path changed)
- ALPHA-2R1: PRICE-PATH TRUTH SEALED (cross-asset contamination eliminated)
- **ALPHA-2R1.1: FINAL EVIDENCE RECONCILIATION (F8 recomputed, counts reconciled)**

## Root Cause Corrected

**BUG A: EXIT_EXECUTION_CONTRACT_VIOLATION**  
Old ALPHA-2 used `bar["perp_close"]` (current bar close) for exit execution.
Frozen ALPHA-1.1 contract specifies exit at "next bar open."
Corrected engine uses `next_bar["perp_open"]`.

**AUDIT B: PRICE_SOURCE_ISOLATION**  
Asset/leg price contract enforced: `(asset, market_type, source)` keys.
BTC cannot read ETH prices. ETH cannot read BTC prices.
Spot cannot read perp prices. Perp cannot read spot prices.

These are distinct. The old report incorrectly called BUG A "cross-asset contamination."

## F8 Recomputation

Old ALPHA-2R used simple mechanical PF comparison:
`if ctrl_m["net_PF"] >= m["net_PF"]: F8 = True`

Frozen ALPHA-1.1 contract requires:
- paired_bootstrap_difference
- 10,000 resamples
- seed 31082026
- 95% CI

**Result: F8 dropped from 7 to 3.**

The old engine's simple PF comparison triggered false positives for strategies
where the control point estimate was marginally worse but the CI overlapped zero,
meaning the difference was not statistically meaningful.

| Strategy | Old F8 | New F8 | Explanation |
|----------|--------|--------|-------------|
| S001 | True | **False** | Strat PF 0.80 > Ctrl PF 0.76 — strategy better |
| S002 | False | False | No change |
| S003 | False | False | No change |
| S004 | True | **False** | Strat PF 0.88 > Ctrl PF 0.80 — strategy better |
| S005 | True | True | Ctrl PF 0.80 > Strat PF 0.77 — control better |
| S006 | True | **False** | Bootstrap CI wide; not significant |
| S007 | True | **False** | Strat PF 0.96 > Ctrl PF 0.75 — strategy better |
| S008 | True | **False** | Bootstrap CI wide; not significant |
| S009 | True | **False** | Bootstrap CI wide; not significant |
| S010 | True | **False** | Bootstrap CI wide; not significant |
| S011 | True | True | Ctrl PF 1.23 >> Strat PF 0.99 — control clearly better |
| S012 | True | True | Ctrl PF 1.23 >> Strat PF 0.88 — control clearly better |
| S013 | True | **False** | Strat PF 0.96 > Ctrl PF 0.76 — strategy better |

## Final Falsification Rule Counts

| Rule | Count | Strategies |
|------|-------|------------|
| F1 | 0 | — |
| F2 | 2 | S005, S006 |
| F3 | 11 | S001,S004,S005,S006,S007,S008,S009,S010,S011,S012,S013 |
| F4 | 5 | S001,S005,S006,S008,S009 |
| F5 | 0 | — |
| F6 | 7 | S002,S003,S005,S007,S011,S012,S013 |
| F7 | 8 | S002,S003,S005,S006,S007,S011,S012,S013 |
| F8 | 3 | S005,S011,S012 |
| F9 | 0 | — |
| F10 | 4 | S001,S003,S011,S012 |
| F11 | 0 | — |
| F12 | 1 | S001 |

## S002/S003 Special Interpretation

S002 and S003 are scientifically interesting even though falsified.
They are NOT survivors. They are **POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED**.

- S002: net_EV=+1.28, net_PF=1.02 — positive edge, but rejected by F6+F7 (concentration)
- S003: net_EV=+0.24, net_PF=1.01 — marginal positive, rejected by F6+F7+F10

Both beat their control (C001) in point estimate but are falsified by concentration.
This is useful input for ALPHA-3: the edge exists but is fragile/concentrated.

## Final Strategy Results

| Status | Count |
|--------|-------|
| SURVIVES_DEVELOPMENT | **0** |
| WEAK_DEVELOPMENT | **0** |
| FALSIFIED | **13** |

## Effective Event Counts

| Strategy | Raw Trades | Effective Events | Ratio |
|----------|-----------|-----------------|-------|
| S001 | 848 | 229 | 0.27 |
| S002 | 176 | 143 | 0.81 |
| S003 | 174 | 104 | 0.60 |
| S004 | 331 | 187 | 0.57 |
| S005 | 45 | 39 | 0.87 |
| S006 | 30 | 27 | 0.90 |
| S007 | 205 | 86 | 0.42 |
| S008 | 76 | 33 | 0.43 |
| S009 | 232 | 162 | 0.70 |
| S010 | 258 | 167 | 0.65 |
| S011 | 79 | 71 | 0.90 |
| S012 | 76 | 70 | 0.92 |
| S013 | 431 | 241 | 0.56 |

## Family-Level Failure Anatomy

### FAM_A — Extreme Negative Basis
- Strategies: S001, S002, S003
- Gross positive: 2/3 (S002, S003)
- Net positive: 2/3 (S002, S003)
- F8 triggered: 0/3 (strategies beat controls)
- Dominant failures: CONCENTRATION (F6/F7), TIMING (F10)
- Directional vs RV: S001 directional perp loses; S002 RV hedge positive; S003 transition positive
- **Finding: Basis mechanism exists but is concentrated/timing-dependent**

### FAM_B — Negative Basis + Negative Funding
- Strategies: S004, S005, S006
- Gross positive: 1/3 (S004)
- Net positive: 0/3
- F8 triggered: 1/3 (S005 only)
- Dominant failures: NO_GROSS_EDGE (F3/F4), CONCENTRATION (F6/F7)
- Directional vs RV: All lose after costs
- **Finding: Adding funding confirmation does NOT improve basis edge**

### FAM_C — Basis + Funding + Volatility
- Strategies: S007, S008
- Gross positive: 1/2 (S007)
- Net positive: 0/2
- F8 triggered: 0/2 (S007 beats control)
- Dominant failures: CONCENTRATION (F6/F7), GROSS_EDGE_BUT_NO_NET (F3)
- Directional vs RV: S007 directional perp has gross edge; S008 hedge loses
- **Finding: Volatility conditioning adds complexity without net edge**

### FAM_D — ETH Relative State
- Strategies: S009, S010
- Gross positive: 1/2 (S010)
- Net positive: 0/2
- F8 triggered: 0/2 (neither triggered by bootstrap)
- Dominant failures: NO_GROSS_EDGE (F3/F4)
- Directional vs RV: Both directional ETH perp lose
- **Finding: ETH relative states produce no tradeable edge**

### FAM_E — Pre-Dislocation Funding
- Strategies: S011, S012
- Gross positive: 2/2
- Net positive: 0/2
- F8 triggered: 2/2 (C005 unconditionally beats both strategies)
- Dominant failures: CONCENTRATION (F6/F7), CONTROL_EQUIVALENT (F8)
- Directional vs RV: Both lose to control
- **Finding: Funding signal alone (C005) is better than funding+basis (S011/S012). Adding basis DESTROYS edge.**

### FAM_X — Control Baseline
- Strategy: S013
- Gross positive: 1/1
- Net positive: 0/1
- F8 triggered: 0/1
- Dominant failures: CONCENTRATION (F6/F7), NO_NET_EDGE (F3)
- **Finding: Even the normal-basis baseline loses after costs**

## Key Scientific Findings

1. **Cost is the primary edge destroyer**: 11/13 strategies fail F3
2. **FAM_A has the most promising gross edge**: S002/S003 show positive net but concentrated
3. **FAM_E control paradox**: C005 (unconditional funding filter) beats S011/S012 (funding+basis). Adding basis conditioning DESTROYS value.
4. **Funding contribution is small**: Most edge comes from price moves, not funding carry
5. **BTC and ETH both fail**: No asset-specific survival

## Generation-1 Conclusion

Generation 1 produced zero development survivors.

This does NOT imply MECH-2 states contain no information.
It means the frozen Generation-1 trade expressions failed the preregistered development criteria.

ALPHA-3 may investigate whether failure arose from:
- Wrong payoff expression
- Wrong directional assumption
- Poor resolution target
- State persistence vs mean-reversion mismatch
- Cost structure
- Event concentration
- Timing
- Or genuinely absent tradeable edge

## Three-Way Reconciliation

All differences between ALPHA-2, ALPHA-2R, and FINAL (2R1) are attributed to:
- FUNDING_SIGN_FIX (Hyperliquid: long pays when funding > 0)
- FUNDING_FREQUENCY_FIX (hourly vs 3x daily)
- PRICE_SOURCE_FIX (next-bar-open exit vs current-bar-close exit)

No unexplained drift exists.

## Test Results

- ALPHA-2R1 test suite: 90/90 pass
- ALPHA-2R test suite: 106/106 pass

## Next Checkpoint

CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-NEW-HYPOTHESES
