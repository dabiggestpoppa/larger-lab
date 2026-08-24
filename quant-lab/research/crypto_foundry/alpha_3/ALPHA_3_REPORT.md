# ALPHA-3 Report

**Checkpoint:** CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-GENERATION-2-HYPOTHESIS-BOOK  
**Base SHA:** a2f226135bfdaf9723315b224a226ccaf8a12f06

## Generation-1 Summary

- 13 strategies tested
- 0 development survivors
- 13 falsified
- 6 controls run

## Main Failure Modes

### 1. COST DOMINATION (11/13 strategies)
The primary destroyer. 11 strategies fail F3 (net PF ≤ 1) after transaction costs.
Only 5 strategies have positive gross EV. All positive-gross strategies lose after costs.

### 2. WRONG DIRECTIONAL ASSUMPTION (S001, S005, S006, S008, S009, S010)
Strategies went LONG when the state information was NEGATIVE (price drops).
S009/S010: ETH lead state is a NEGATIVE predictor (SMD=-0.26) but strategies went LONG.

### 3. EVENT CONCENTRATION (S002, S003, S007, S011, S012)
Edge exists but is concentrated in few months/episodes. F6+F7 triggered.

### 4. CONTROL EQUIVALENCE (S005, S006, S008, S009, S010, S011, S012)
Strategy does not beat its control. State adds no value.

### 5. TIMING MISMATCH (S001, S003, S011, S012)
Mean holding < 2 bars. State signal is transient but price effect persists longer.

## Family Diagnoses

### FAM_A — Extreme Negative Basis
**Mechanism:** SUPPORTED. B4 state has SMD = -0.94 to -1.14.
**Expression:** WEAK. Directional perp fails. Spot/perp basis (S002) has gross edge but concentrated.
**Key finding:** Basis information IS real. The issue is the PAYOFF OBJECT — directional perp doesn't capture basis normalization.

### FAM_B — Negative Basis + Funding
**Mechanism:** NOT_SUPPORTED for directional. Adding funding destroys basis edge.
**Expression:** FALSIFIED.
**Key finding:** C005 (unconditional funding filter, net PF=1.23) beats S011/S012 (funding+basis). Adding basis to funding DESTROYS edge.

### FAM_C — Basis + Funding + Volatility
**Mechanism:** WEAK.
**Expression:** FALSIFIED.
**Key finding:** Complexity adds no edge. Volatility filter reduces event count without improving quality.

### FAM_D — ETH Relative State
**Mechanism:** NOT_SUPPORTED for directional.
**Expression:** FALSIFIED.
**Key finding:** ETH lead is a NEGATIVE predictor. Gen-1 went LONG. This is a DIRECTIONAL ERROR.

### FAM_E — Pre-Dislocation Funding
**Mechanism:** SUPPORTED for funding information.
**Expression:** WEAK. Both strategies lose to C005.
**Key finding:** C005 (unconditional funding filter) net PF=1.23. The funding signal IS informative. But Gen-1 expression (directional perp) is WRONG PAYOFF OBJECT.

### FAM_X — Baseline
**Mechanism:** SUPPORTED (baseline has gross edge).
**Expression:** FALSIFIED.
**Key finding:** Even the baseline gross edge (PF=1.13) doesn't survive costs.

## S002 Diagnosis
**Status:** POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED
- Net EV = +1.28 bps, Net PF = 1.016
- Gross EV = +13.45 bps, Gross PF = 1.184
- Falsified by F6 (single event domination) and F7 (one period domination)
- Edge exists but is concentrated: payoff ratio = 0.91, mean_R = +0.013
- Spot/perp hedge expression has correct carrier but needs more events
- Control C001 net PF = 0.80 — strategy clearly beats control

## S003 Diagnosis
**Status:** POSITIVE_NET_BUT_STRUCTURALLY_FALSIFIED
- Net EV = +0.24 bps, Net PF = 1.009
- Gross EV = +5.16 bps, Gross PF = 1.22
- Falsified by F6, F7, F10 (timing)
- Transition entry is interesting but too concentrated and too fast
- Median hold = 1h, mean hold = 1.48h

## Mean-Reversion vs Persistence Findings

| State | Resolution | Timeframe |
|-------|-----------|-----------|
| B4 extreme negative | MEAN REVERSION | 4-24h but price moves first |
| B3 elevated negative | MEAN REVERSION | 4-24h |
| F negative elevated | PERSISTENCE | 5+ hours |
| F negative extreme | PERSISTENCE | 2.5+ hours |
| ETH LED | PERSISTENCE | 2+ hours |
| B4+F_NEG_ELEVATED | STRONG PERSISTENCE | 24h+ |

## Cost Anatomy

| Category | Strategies |
|----------|-----------|
| NO_GROSS_EDGE | S001, S005, S006, S008, S009 |
| GROSS_EDGE_BUT_COST_NEGATIVE | S002, S003, S004, S007, S010, S011, S012, S013 |

**8 strategies have gross edge. 0 survive after costs.**
**Only S002 has gross EV > total transaction costs.**

## Payoff-Mismatch Findings

| Current Payoff | Correct Candidate | Strategies |
|----------------|-------------------|------------|
| DIRECTIONAL_PERP | SPOT_PERP_BASIS | S001, S003, S007 |
| DIRECTIONAL_PERP | FUNDING_CARRY | S011 |
| DIRECTIONAL_PERP | STAND_DOWN | S005, S006, S009, S010 |
| SPOT_PERP_BASIS | SPOT_PERP_BASIS | S002, S008 |
| SPOT_PERP_BASIS | FUNDING_CARRY | S012 |

## Gen-2 Hypothesis Summary

- **10 hypotheses** generated
- **3** SUPPORTED_FOR_PREREGISTRATION (H001, H002, H007)
- **6** REQUIRES_DATA (H003, H004, H006, H008, H009, H010)
- **1** REJECTED_AT_ANATOMY (H005 — Gen-1 rehash)

### Top Pre-PNL Priorities
1. **H007** (Stand-down filter) — null hypothesis for Gen-2
2. **H001** (Spot/perp basis RV) — correct carrier for basis information
3. **H002** (Basis transition directional) — correct timing for basis events

## Resource Updates
- ASX Capital added to resource registry
- CRYPTO-RWA lane defined
- Resource registry version: 1.1

## Next Checkpoint
Based on highest-priority hypothesis prerequisites, recommend:
**CRYPTO-ALPHA-3.1-PREREGISTRATION** (existing data already supports H001, H002, H007)

Human chooses next lane.
