# MECH-2 DECISION

## DECISION: PASS_ALT_TERRAIN_WITH_LIMITATIONS

Date: 2026-08-26 · Checkpoint: CRYPTO-ALT-MECH-2 (CONDITIONAL PROPAGATION, CAUSAL
HIERARCHY & FIELD-GEOMETRY MAPPING) · Parent: MECH-1 `b3083df1` (PASS_ALT_MECHANISM_ANATOMY).

## Why PASS (not FAIL)

- **Conditional propagation structure exists.** 151 state-conditioned lead/lag cells;
  regime conditioning *flips* propagation direction in the strongest case (51-100 →
  101-200 velocity: +0.64 under BTC_DOWN vs −0.30 unconditional). This is genuine
  conditional structure, not a common-factor artifact (A residualization).
- **Common market beta separated.** Returns are 75–87% common factor and remain
  contemporaneous after residualization — correctly classified as synchrony, not
  cascade. Rank velocity is 88–99% band-idiosyncratic.
- **Important hierarchy/pathways empirically supported.** Chain-liquidity →
  native-asset improvement survives FDR (77/258 cells) and transfer-entropy
  confirmation (p=0.005).
- **Null and failed pathways preserved.** 17_NULL_AND_FAILED_RESULTS.csv retains all
  non-significant cells; F includes never-fired patterns (small-cap rotation,
  lower-rank acceleration); G reports 142 cycle-specific motifs.
- **Evidence stable across time/regime** at the state level: concentration/mixed
  persistence, concentration pivot, and chain-flow direction recur across 5 fixed
  subperiods (12_MORPHISM_CATALOG.json subperiod counts).
- **No PIT leakage** (truth lock all-pass), no multiple-testing collapse, no causal
  claim beyond the assigned ladder level (11_CAUSALITY_LADDER.csv, max L3).

## Why WITH_LIMITATIONS (not full PASS_ALT_CONDITIONAL_PROPAGATION_MAP)

1. **No sequential band cascade in returns** — band co-movement is contemporaneous
   (lag 0, |corr| 0.97+); "what changes first" at band level has no clean answer in
   returns. Propagation lives in rank velocity and flow, not returns.
2. **Sector leader-first is same-day only** — delayed peer confirmation ≈ 0
   (07_SECTOR_PROPAGATION.csv); there is no exploitable 1-14d spread structure.
3. **Rank-migration precursors are weak** — success rates 0.46–0.51; event-vs-control
   differences are small and mostly descriptive (L1).
4. **Information-flow support is narrow** — 1 of 3 TE pairs significant; stablecoin
   channel stays WEAK.
5. **No dominant global reference frame** — median cluster variance is 61%
   idiosyncratic; only ecosystem-bound clusters (Ethereum 99%) are strongly
   explained (10_HIERARCHY_MAP.json). L0 for hierarchy dominance.
6. **Morphisms mostly cycle-specific** — 71% of state motifs do not recur across
   cycles; only persistence/concentration-pivot geometry is stable.

## PASS criteria compliance

| criterion | status |
|---|---|
| conditional propagation structure exists | YES (B, 151 conditioned cells) |
| common market beta separated | YES (A residualization, R² reported per band/metric) |
| important hierarchy/pathways empirically supported | YES (E: 77 FDR-sig; J: p=0.005) |
| null and failed pathways preserved | YES (17, 08 non-sig cells, F, G) |
| evidence stable across time/regime for deeper mapping | PARTIAL (states stable; routes not) |

## Fail-condition audit (all clear)

- Apparent lead-lag collapses after common-factor removal? **No** — residual
  structure persists (110 STRUCTURAL cells; rank-velocity structure is orthogonal).
- Results driven by one cycle? **No** — top recurring motifs span 5/5 subperiods;
  cycle-specificity is *reported*, not hidden.
- PIT leakage materially affects findings? **No** — truth lock all-pass; no future
  columns (structural tests).
- Multiple-testing correction eliminates structure? **No** — 77/258 chain cells
  survive BH-FDR; 123/126 A cells.
- Causal claims exceed evidence? **No** — ladder caps at L3; no causality language
  beyond conditional-lead/lag.
- Advanced math creates structure invisible to simpler tests? **No** — TE (J) only
  confirms E's simpler correlations; topology found no new structure and says so.
- Data quality cannot support the question? **No** — flow gaps handled; Meteora
  pool-level explicitly deferred.

## Scope guardrails (unchanged)

**NO STRATEGY DESIGN, NO PNL, NO DEPLOYMENT.** This is mechanism research only.
NOT authorized by this decision: strategy
construction, entry/exit/stops, Kelly sizing, PnL selection, ML predictors,
backtesting of trading rules, capital deployment, live execution. All of those
require explicit human approval.

## Next checkpoint (human-reviewed)

1. **CRYPTO-ALT-MECH-3 — STATE-CONDITIONED PROPAGATION TIMING**: deepen B (BTC_DOWN /
   VOL_HIGH velocity leads), E/J chain-TVl→native arrows with leave-one-cycle-out
   stability.
2. Then, only if mechanisms hold: **CRYPTO-ALT-ALPHA-1** simple-strategy
   preregistration (still requires human go-ahead).

No checkpoint is auto-started.
