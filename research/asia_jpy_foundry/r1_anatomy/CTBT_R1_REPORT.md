# SW-AJCF-R1 — SESSION / MICROSTRUCTURE ANATOMY — REPORT

Checkpoint: SW-AJCF-R1-SESSION-AND-CONSTRAINT-ANATOMY
Base: f3c6aca28ae9bdc090ca32032f180995cf94a9b5
Date: 2026-08-20

## Summary

R1 studied the four fixed JPY-centered candidates using NON-PNL mechanism
properties (basis vol, extreme-event rate, displacement severity,
time-to-resolution, cost geometry) as preregistered. Two candidates survive on
mechanism + cost grounds; two fail on cost economics.

## Data family correction (important)

The plain `*_M5.csv` files (USDJPY, CHFJPY) are NOT cross-synchronized with the
PRO/fetched family. Mixing them produced phantom 200-350 bps triangular
violations during the 2022-12-20 BOJ YCC shock. Switched JPY legs to the
`*_M5_fetched.csv` family (the same family CTBT uses for JPY legs). With the
corrected mapping all four triangles satisfy the identity (mean basis ~ -1 bps;
BOJ-window violations < 2.3 bps). This correction does NOT rescue any candidate
— it was necessary to make any reading truthful.

## Key mechanism finding

For ALL four triangles, extreme dislocations cluster in **NY morning
(13-15 EST)**, NOT the Tokyo/Asia session. The preregistered Asia lenses
(ASIA_CORE 19-04, TOKYO_CORE 21-02, ASIA_LONDON_TRANSITION 02-07) contain
<1.5% of all |z|>3 events. JPY crosses dislocate most when NY flow meets
carry/funding pressure. R2 session translation must freeze the NY_MORNING
window — the "Asia-native" hypothesis is falsified by anatomy.

## R1 results (development window 2022-09-01 → 2024-12-31)

| Candidate | Data validity | Best natural session | Event freq (epw) | Median dislocation | Median resolution | Modeled cost | Observed cost | Gross-excursion/cost | Rollover contam. | Mechanism clarity | R1 decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AUD_NZD_JPY | VALID | NY_MORNING 13-15 EST | 20.3 | 3.49 bps | 75 min | 5.99 bps | AUDNZD 0.5 pips med | **0.58x** | 1.4% | Weak (tight constraint) | **FAIL_COST** |
| USD_CHF_JPY | VALID (shorter window) | NY_MORNING 13-15 EST | 10.3 | 11.22 bps | 60 min | 4.80 bps | USDCHF 0.4 pips med | **2.34x** (NY 2.59x) | 1.0% | Clear | **PROMOTE_TO_R2** |
| AUD_CAD_JPY | VALID | NY_MORNING 13-15 EST | 14.2 | 4.38 bps | 35 min | 5.33 bps | AUDCAD 0.7 pips med | **0.82x** | 2.0% | Weak (tight constraint) | **FAIL_COST** |
| CAD_CHF_JPY | VALID | NY_MORNING 13-15 EST | 10.6 | 12.06 bps | 60 min | 5.49 bps | CADCHF 0.3 pips med | **2.20x** (NY 2.43x) | 1.5% | Clear | **PROMOTE_TO_R2** |

Observed cost = median provider-bar spread column where present (JPY legs on the
fetched family have no spread column → observed layer NOT_AVAILABLE there; no
fabrication).

## Why the AUD triangles fail

AUD_NZD_JPY and AUD_CAD_JPY have extremely tight triangular constraints
(basis std 1.6-2.9 bps). Their dislocations (3.5-4.4 bps median) are simply too
small to cover a three-leg basket cost (5.3-6.0 bps) even before slippage.
This is the same lesson as TB-X: generic triangular mean reversion is not
enough. The mechanism exists; the economics do not.

## Why the CHF triangles pass

USD_CHF_JPY and CAD_CHF_JPY dislocate 11-13 bps at |z|>3 (basis std 3.3-3.4 bps
in the corrected family) and resolve in ~60 min. Cost coverage 2.2-2.6x at the
median — above the preferred 1.5x and strong 2.0x thresholds.

## Session lens anatomy (all-hours baseline included)

See CTBT_R1_SESSION_ANATOMY.csv. Key numbers (all-hours baseline):

- AUD_NZD_JPY: 2471 events, 20.3/wk, cost ratio 0.58
- USD_CHF_JPY: 804 events, 10.3/wk, cost ratio 2.34 (NY 13-15: 2.59)
- AUD_CAD_JPY: 1731 events, 14.2/wk, cost ratio 0.82
- CAD_CHF_JPY: 1291 events, 10.6/wk, cost ratio 2.20 (NY 13-15: 2.43)

## R1 decision

- Survivors (2): **USD_CHF_JPY**, **CAD_CHF_JPY**
- Failed (2): AUD_NZD_JPY (FAIL_COST), AUD_CAD_JPY (FAIL_COST)
- Program NOT stopped. R2 recommended with the two CHF survivors, session
  translation = NY_MORNING 13:00-16:00 EST (frozen at R2 start, no tuning).
- USD_CHF_JPY carries SHORTER_DEVELOPMENT_WINDOW (USDCHF leg starts 2023-07);
  its R2 evidence will be ~1.5 years, not ~2.25.

## Boundaries respected

- No strategy PnL / PF / Sharpe / drawdown computed anywhere in R1.
- No parameter search, no session tuning after results, no filters.
- 2025 data NOT consumed (reserved for R3 confirmation).
- CTBT forward collector/dashboard untouched (separate worktree; read-only data).

## Artifacts

- CTBT_R1_DATA_AUDIT.csv
- CTBT_R1_SESSION_ANATOMY.csv
- CTBT_R1_EXTREME_EVENTS.csv
- CTBT_R1_COST.csv
- CTBT_R1_CANDIDATE_DECISIONS.csv
- CTBT_R1_REPORT.md
- CTBT_R1_DECISION.json

Next: SW-AJCF-R2-FROZEN-MECHANISM-SCREEN (human review required).

---

## ERRATA — SW-AJCF-R1.1-SESSION-TRUTH-AND-LABEL-REPAIR (2026-08-20)

Original R1 text corrected by the R1.1 session-truth repair. Original evidence
above is preserved verbatim; the corrected truth is authoritative.

1. **Session label.** The window 13:00–15:00/16:00 EST was labeled
   "NY_MORNING". That is a mislabel: 13:00–16:00 EST is afternoon.
   Corrected identifier: **NY_AFTERNOON_13_16_EST** (fixed EST, UTC−5,
   no DST).

2. **Asia event-fraction claim.** The statement "the preregistered Asia
   lenses contain <1.5% of all |z|>3 events" is INCORRECT as a blanket
   claim. Per-lens and unique-union audit (no double counting):
   - USD_CHF_JPY: ASIA_CORE 0.5%, TOKYO_CORE 0.4%,
     ASIA_LONDON_TRANSITION 4.9%, union 5.2% (42/804 events).
   - CAD_CHF_JPY: ASIA_CORE 0.8%, TOKYO_CORE 0.4%,
     ASIA_LONDON_TRANSITION 6.1%, union 6.8% (88/1291 events).
   Correct statement: Asia lenses contain ~5–7% of all extreme events
   (unique union). Asia is present but sparse.

3. **Asia hypothesis classification.** Both survivors are classified
   **ASIA_PRESENT_BUT_SPARSE** (not "Asia has no mechanism"). Asia events
   are economically real (median displacement 10.0 / 10.9 bps) but low
   frequency.

4. **R2 session freeze.** ONE session per survivor, from NON-PNL anatomy:
   **NY_AFTERNOON_13_16_EST** (13:00–16:00 EST, 120-min runway, hard exit
   16:00 EST; entries 13:00–14:00 EST keep clear of the 16:00 EST rollover
   fix zone). No session grid in R2.

See AJCF_R11_HOURLY_ANATOMY.csv, AJCF_R11_ASIA_EVENT_FRACTION_AUDIT.json,
AJCF_R11_TIME_SEMANTICS.json, AJCF_R11_SESSION_FREEZE.json,
AJCF_R11_DATA_FAMILY_FREEZE.json, AJCF_R11_REPORT.md, AJCF_R11_DECISION.json.
