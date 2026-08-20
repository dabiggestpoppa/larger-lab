# ASIA / JPY CONSTRAINT-RESOLUTION FOUNDRY — MASTER PLAN

Repository: dabigestpoppa/larger-lab
Branch: agent/asia-triangle-foundry
Base: f3c6aca28ae9bdc090ca32032f180995cf94a9b5 (T4.1 CTBT forward activation)

## Program Hypothesis

The canonical TB edge (AUD_GBP_NZD) may represent a broader mechanism:

1. TEMPORARY TRIANGULAR CONSTRAINT DISLOCATION
2. + SESSION-NATIVE LIQUIDITY / FLOW
3. + SUFFICIENT DISPLACEMENT
4. + CONVERGENCE / OVERSHOOT RESOLUTION
5. + GROSS EDGE LARGE ENOUGH TO SURVIVE THREE-LEG EXECUTION COST

Previous TB-X work showed generic triangular mean reversion is NOT enough.
This program therefore studies a tiny set of economically coherent JPY-centered
ecosystems — NOT an arbitrary triangle sweep.

## Fixed Candidate Set (max 4, no additions)

| ID | Triangle | Legs | Basis orientation |
|----|----------|------|-------------------|
| A (PRIMARY) | AUD_NZD_JPY | AUDNZD, AUDJPY, NZDJPY | b = ln(AUDNZD) − ln(AUDJPY) + ln(NZDJPY) |
| B | USD_CHF_JPY | USDCHF, USDJPY, CHFJPY | b = ln(USDCHF) − ln(USDJPY) + ln(CHFJPY) |
| C | AUD_CAD_JPY | AUDCAD, AUDJPY, CADJPY | b = ln(AUDCAD) − ln(AUDJPY) + ln(CADJPY) |
| D (RESERVE) | CAD_CHF_JPY | CADCHF, CADJPY, CHFJPY | b = ln(CADCHF) − ln(CADJPY) + ln(CHFJPY) |

NO fifth triangle. NO recursive discovery. NO "nearby" generation.

## Program Structure — Exactly 4 Rounds

- R1 — SESSION / MICROSTRUCTURE ANATOMY (mechanism before PnL; no strategy PnL ranking)
- R2 — FROZEN MECHANISM SCREEN (canonical lifecycle, ONE frozen session per survivor)
- R3 — ONE-SHOT CONFIRMATION (frozen windows, bootstrap, BH-FDR)
- R4 — REAL COST REALITY + FINAL SEAL (observed provider cost vs historical edge)

No Round 5 rescue. A scientific failure is not an engineering bug.

## Stop Conditions

- R1: 0 survivors → STOP PROGRAM.
- R2: 0 survivors → STOP. Max R2 survivors = 2.
- R3: 0 confirm → STOP_ASIA_JPY_FAMILY.
- R4: only HISTORICALLY_CONFIRMED_COST_PLAUSIBLE may proceed to forward-shadow.

## Truth Vocabulary (mandatory)

HYPOTHESIS / DESCRIPTIVE / DEVELOPMENT / CONTRACT_SPECIFIC_CONFIRMATION /
HOLDOUT (only if truly untouched) / FORWARD_SHADOW / DEMO_EXECUTION /
PRODUCTION_AUTHORIZED.

Never upgrade evidence vocabulary for presentation.

## Promotion Rules

- R1: promote on mechanism quality + cost geometry, NOT strategy PF.
- R2: promote because mechanism + cost + stability + causality agree, not because PF is spectacular.
- R3: 0 → STOP; 1 → SINGLE_ASIA_JPY_ENGINE; 2 → FOCUSED_ASIA_JPY_FAMILY.
- R4: only COST_PLAUSIBLE may be recommended for forward-shadow preregistration.

## Portfolio Role

TIME-SESSION DIVERSIFICATION and CURRENCY-EXPOSURE DIVERSIFICATION relative to
the GBP/London-heavy CTBT family. Report descriptive event/currency/session
overlap. Do NOT optimize portfolio weights.

## Causality Contract

Closed completed M5 bar; current bar excluded from z; next executable bar
semantics; run future-perturbation invariance and tail-truncation invariance
for every promoted engine.

## Hard Boundaries

- Existing forward-shadow family (CANONICAL TB, CTBT-EUR-GBP-USD-v1,
  CTBT-GBP-NZD-USD-v1) is FROZEN. No parameter changes, no contamination,
  no PnL pooling, no interruption of collectors/dashboards.
- This program runs in a SEPARATE git worktree (larger-lab-asia-jpy).
- 0, 1, or 2 truthful answers are all valid outcomes. 0 is a valid answer.
