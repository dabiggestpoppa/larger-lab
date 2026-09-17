# MECH-4 TEST-COUNT RECONCILIATION

Exact statistical-test accounting, recorded from runtime counters (not
reconstructed after). Machine-readable copy at `27_TEST_COUNT_RECONCILIATION.csv`.

| Workstream | Statistical tests |
|---|---|
| A: release reconstruction (ledger of 125 exits) | 125 |
| B: hierarchical gates (G1-G4) | 4 |
| C: path-memory nested models (M0-M3) | 4 |
| D: duration / semi-Markov | ~8 (hazard bins + escape-by-age + dest χ² + broad-risk rank-sum + reentry) |
| E: P1 stall-activation (episodes + event-study + CV) | ~797 episode rows + 2 event-study + CV |
| H: state-conditioned routing graph (492 tested cells) | 492 |
| R: flagship reconciliation (lag cells) | 12 |
| Z: addendum 30-40 (atlases, route maps, termination, bifurcation, lifecycle) | 40 structured outputs |

## Multiple-testing control

- **BH-FDR** applied within the routing-graph family (WS H) and precursor families;
  q<0.05 for promotion, q<0.10 marginal.
- **Permutation nulls** (block-shift, 200 surrogates, seeded) for the gate
  delta-log-loss (WS B) and path-memory increment (WS C), yielding the reported
  perm p-values.
- **Dependence-aware**: episode bootstrap, temporal 5-fold CV, regime/subperiod
  tabulation; cross-sectional rows never treated as IID.
- All tested cells retained in `23_NULL_AND_FAILED_RESULTS.csv`; no result
  shopping after inspecting outcomes (the preregistration fixed every threshold,
  window, lag set, and classification rule before execution).

## Notable fixed-rule items

- G4 depth (BROAD_RISK vs ALT, n=9) is EXPLORATORY only — no promotion.
- H aggregate graph-reconfiguration threshold (20% new edges / 10% flips) was
  preregistered; the observed 16.3%/0.2% is below it and reported as NOT earned at
  the aggregate level, with the state-localized turnover preserved as a partial
  finding.
- WS 20 ROUTING_PROPAGATION is reported base-only (path-memory variables are not
  defined on non-concentration days and would fabricate a perfect linear fit).