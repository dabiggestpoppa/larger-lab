# ASIA-JPY-R1 — SESSION / MICROSTRUCTURE ANATOMY PROTOCOL

Checkpoint: SW-AJCF-R1-SESSION-AND-CONSTRAINT-ANATOMY
Base: f3c6aca28ae9bdc090ca32032f180995cf94a9b5
Parent: (program master plan — research/asia_jpy_foundry/ASIA_JPY_FOUNDRY_MASTER_PLAN.md)

THIS PROTOCOL IS WRITTEN BEFORE ANY STRATEGY ECONOMICS ARE OPENED.

## Mission

Determine whether each of the four candidates possesses a session-localized,
economically executable dislocation / resolution process, using NON-PNL
mechanism properties only. Candidate selection in R1 is NOT based on
strategy EV/PF/WR/Sharpe/drawdown.

## Candidates (fixed)

| ID | Triangle | Legs (A, B, C) | Basis b = ln(A) − ln(B) + ln(C) |
|----|----------|----------------|--------------------------------|
| A | AUD_NZD_JPY | AUDNZD, AUDJPY, NZDJPY | ln(AUDNZD) − ln(AUDJPY) + ln(NZDJPY) |
| B | USD_CHF_JPY | USDCHF, USDJPY, CHFJPY | ln(USDCHF) − ln(USDJPY) + ln(CHFJPY) |
| C | AUD_CAD_JPY | AUDCAD, AUDJPY, CADJPY | ln(AUDCAD) − ln(AUDJPY) + ln(CADJPY) |
| D | CAD_CHF_JPY | CADCHF, CADJPY, CHFJPY | ln(CADCHF) − ln(CADJPY) + ln(CHFJPY) |

## Data

- Authentic M5 data only, same data family as CTBT (quant-lab/data).
- Leg file mapping (audited; see CTBT_R1_DATA_AUDIT.csv):

| Leg | File | Timestamp format | Notes |
|-----|------|------------------|-------|
| AUDNZD | AUDNZD_PRO_M5.csv | "2015-10-11T20:00:00" | daily before ~2022-08, M5 after; spread col |
| AUDJPY | AUDJPY_PRO_M5.csv | same | daily before ~2022-08; spread col |
| NZDJPY | NZDJPY_PRO_M5.csv | same | daily before ~2022-08; spread col |
| AUDCAD | AUDCAD_PRO_M5.csv | same | daily before ~2022-08; spread col |
| CADJPY | CADJPY_PRO_M5.csv | same | daily before ~2022-08; spread col |
| CADCHF | CADCHF_PRO_M5.csv | same | daily before ~2022-08; spread col |
| USDCHF | USDCHFPRO_M5.csv | epoch seconds | M5 2023-07 onward; spread col |
| USDJPY | USDJPY_M5.csv | "2022-01-03 00:00:00" | real M5 2022-01+; no spread col |
| CHFJPY | CHFJPY_M5.csv | same | real M5 2022-01+; no spread col |

- DEVELOPMENT WINDOW (deterministic, before results):
  - Shared valid M5 window: 2022-09-01 through 2024-12-31 (largest common
    causally valid M5 window across required legs).
  - Candidate B is additionally constrained by USDCHF leg start (2023-07):
    B dev window = 2023-07-01 through 2024-12-31. Recorded as
    SHORTER_DEVELOPMENT_WINDOW — NOT treated as equal evidence to A/C/D.
  - 2025 is NOT consumed by R1 (reserved for R3 confirmation).
- No interpolation, no forward-fill, no synthetic bars.

## Session lenses (preregistered, fixed EST semantics)

Fixed EST (UTC-5), consistent with CEREBUS / canonical TB convention:
est_hour = (hour_utc − 5) mod 24. Three research lenses, same for all candidates:

| Lens | EST window | Rationale |
|------|-----------|-----------|
| ASIA_CORE | 19:00–04:00 | Tokyo/Sydney flow, JPY-native liquidity |
| TOKYO_CORE | 21:00–02:00 | Tokyo cash-session peak overlap |
| ASIA_LONDON_TRANSITION | 02:00–07:00 | Asia close → London open flow |

These are research lenses, NOT strategy variants. No session grid in R2.

## R1 metrics (NON-PNL mechanism properties)

Per candidate, per session lens:

1. DATA_VALIDITY — bar count, M5 fraction, duplicates, missing blocks, OHLC
   integrity, timestamp coverage, spread availability.
2. NATURAL_SESSION — per-lens basis volatility (std of basis changes), extreme
   event rate, displacement severity, time-to-resolution, cost ratio.
3. EXTREME_EVENT_FREQUENCY — rate of |z|>3 basis dislocations per week
   (rolling 200-bar causal z, ddof=0, current bar excluded).
4. DISPLACEMENT_SEVERITY — distribution of |basis deviation| in bps at extreme
   events (p50/p75/p90/p95/max).
5. TIME_TO_RESOLUTION — distribution of minutes for basis to revert within a
   fixed band (e.g., return below |z|<0.5) after an extreme excursion.
6. COST_RATIO — median gross excursion (bps) / basket crossing cost (bps).
   Preferred >= 1.5; strong >= 2.0.
7. ROLLOVER_CONTAMINATION — fraction of extreme events near rollover hours;
   basis jump stats at 21:00–23:00 UTC (17:00 EST fix).
8. MECHANISM_CLARITY — qualitative coherence of dislocation→resolution.

## Cost model (frozen, before results)

- Modeled basket round-trip cost (bps), canonical formula:
  sum over legs of (spread_pips + commission_pips) * pip_size / median_price * 1e4
  - commission_pips = 1.4 per leg (canonical frozen contract)
  - documented OxSecurities MT5 spreads (level 4) from
    quant-lab/config/spread_commission_config.py
  - pip sizes: non-JPY 0.0001; JPY 0.01
- Observed spread layer (level 2, provider bar spread column) where present:
  median/p75/p90/p95 of leg spread columns, converted to pips
  (JPY points ÷ 10).
- Kept as separate truth layers. No pooling. No fabrication.

## Early economic viability filter (before full strategy build)

- median gross-excursion / realistic basket cost:
  - >= 1.5 preferred
  - >= 2.0 strong
- Candidates structurally below ~1.0x should normally be killed before R2.

## R1 outputs per candidate

DATA_VALIDITY, NATURAL_SESSION, EXTREME_EVENT_FREQUENCY,
DISPLACEMENT_SEVERITY, TIME_TO_RESOLUTION, COST_RATIO,
ROLLOVER_CONTAMINATION, MECHANISM_CLARITY.

Final R1 state per candidate:
PROMOTE_TO_R2 | FAIL_MECHANISM | FAIL_COST | FAIL_DATA.

## R1 survivor limit

Max 3 survivors; preferred 2. If 0: STOP PROGRAM. Ranking uses mechanism
quality and cost geometry, NOT strategy PF.

## Deliverables (this directory)

- CTBT_R1_DATA_AUDIT.csv
- CTBT_R1_SESSION_ANATOMY.csv (per lens, per candidate)
- CTBT_R1_EXTREME_EVENTS.csv (event-level displacement/resolution)
- CTBT_R1_COST.csv (modeled + observed cost layers)
- CTBT_R1_CANDIDATE_DECISIONS.csv
- CTBT_R1_REPORT.md
- CTBT_R1_DECISION.json

## Hard boundaries

- R1 does NOT compute strategy PnL, PF, Sharpe, or drawdown.
- No parameter search. No session tuning after results. No filters.
- The running CTBT forward collector/dashboard is NOT touched (separate
  worktree; read-only data access).
