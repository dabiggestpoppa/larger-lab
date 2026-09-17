# MECH-3 TEST-COUNT RECONCILIATION

**Rule (prereg §19):** exact counts of hypotheses, states, lags, windows, groups and
total tests are recorded from run-time counters into
`23_TEST_COUNT_RECONCILIATION.csv`, not reconstructed afterwards. All tested cells
are retained; no result shopping.

## 1. Statistical tests executed (run-time counters)

| Workstream | Counter | Statistical tests |
|---|---|---|
| A chain-liquidity redundancy | 792 | per (chain, variable-pair) Spearman correlations across 12 chains × 66 pairs |
| B perturbation | 1,146 | per (chain, link, ablation, lag) correlation tests (12 chains × 5 links × up to 7 ablations × 4 lags) |
| D routing flip | 110 | per (relationship, state, best-lag) conditional correlations |
| E pivot precursors | 130 | per (event type × window × precursor) Wilcoxon rank-sum tests |
| F pivot boundary | 20 | per (coordinate × exit/enter) Spearman monotonicity tests |

**Total statistical tests: 2,198** (A 792 + B 1,146 + D 110 + E 130 + F 20).

## 2. Non-counted descriptive outputs

These produce artifacts but are descriptive (no formal hypothesis test counted):

- C multi-view reconstruction: incremental R² per (chain, view group) — 12 chains ×
  5 steps; agreement/disagreement inventories are descriptive.
- G release route map: 125 exit events, per-event coordinates/first-changed
  observable — descriptive; no significance test.
- H information plateau: 3 phenomena × 8 variables — incremental R², descriptive.
- I field plateau: 922 episodes — descriptive episode statistics.
- J primitive audit: 8 candidates × (redundancy, materiality, substitution,
  recurrence) — descriptive classification per fixed rule; the underlying R² deltas
  are descriptive.
- K topology: graph statistics — descriptive.
- L dynamical system: transition matrices (5 subperiods), basin self-transitions,
  1 hysteresis chi-square (n=125).
- M morphism survival: descriptive comparison of RECURRING vs CYCLE_SPECIFIC.

## 3. Multiple-testing control applied

- BH-FDR within each workstream family with ≥ 10 tests:
  - A: FDR computed on per-pair Spearman p (all 66 pooled pairs; q reported on
    classification thresholds rather than raw p — see 05).
  - B: classification rule (SURVIVES/WEAKENED/DISSOLVES/LOCAL/NO_RELATION) is
    threshold-based on per-ablation p<0.05; no single FDR pool — conservative by
    construction (survival requires ≥ 4 of 5 ablations significant, same sign).
  - D: BH-FDR across all 110 (relationship, state) cells; q<0.05 used for
    routing-flip promotion.
  - E: BH-FDR across all 130 precursor cells; q<0.05 for entry/exit precursor
    claims.
  - F: monotonicity ρ reported with the fixed |ρ| ≥ 0.80 rule (prereg) plus
    subperiod consistency (≥ 3/5) — 6 of 10 coordinates met |ρ| ≥ 0.50 descriptive
    threshold; boundary promotion uses the stricter prereg rule.

## 4. Dependence control

- Correlations: block bootstrap (20-day) via M2 helpers; conditional tests use
  block-shift permutation surrogates (200, seeded) — no IID assumption on
  cross-sectional or daily rows.
- Event studies (E/G): control samples matched per (month-year, state family),
  seeded; Wilcoxon p reported with cluster counts (events, controls), never treated
  as IID observations.
- Flow features shifted per-chain AVAILABLE_NEXT_DAY before all tests.

## 5. Null retention

All non-significant cells are retained:
- B: 135 NO_RELATION + 130 WEAKENED + 25 DISSOLVES + 5 LOCAL = 295 non-promoted
  (of 300 chain-link rows).
- D: 33 LOST + 35 SAME_SIGN + 27 REVERSED-not-q + 15 GAINED-not-q retained in
  `08_ROUTING_FLIP_MAP.csv`; promoted cells = 16 at q<0.05.
- E: 111 of 130 precursor cells non-significant at q<0.05, retained in
  `11_CONCENTRATION_PIVOT_ANATOMY.csv`.
- `20_NULL_AND_FAILED_RESULTS.csv` aggregates the null classes.

## 6. Consistency check

The 2,198 counted tests exclude the descriptive outputs above (which are documented
as non-tests). No cell that was run and not significant was dropped from any artifact.
