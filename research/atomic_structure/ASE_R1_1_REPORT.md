# ASE-1.1 — Generation-A Contract Reproduction

## Trader review

1. **218.4p day:** valid observed development session; it is retained, not deleted.
2. **NO-GO:** yes. It is outside the calibration domain and carries `AR_NO_GO_STATE=true`.
3. **AR_MAX:** executable Generation-A sources use `AR > 45` as NO-GO. Equality at 45 remains T3; the conflicting equality fixture is disclosed in `ASE_AR_MAX_BOUNDARY_AUDIT.md`.
4. **Repaired centroids:** 13.7137p, 22.5500p, 34.6273p from 432 permitted calibration sessions.
5. **Raw AUs:** 6.8568p, 11.2750p, 17.3136p.
6. **Operational AUs:** 10p, 12p, 15p.
7. **Operational triggers:** 12p, 15p, 19p. Raw triggers are 8.2282p, 13.5300p, 20.7764p.
8. **Python vs TradingView / Quant Bible:** the session, AR gate, operational boundaries, AU and trigger mapping now reproduce the source-backed Generation-A contract. Exact 45p remains a disclosed source/fixture ambiguity, resolved to the executable wording.
9. **NO-GO sessions:** 10 of 442 valid development sessions; calibration n=432.
10. **Prior AU/state/time findings:** AU normalization, state differentiation, time contraction, and causality were recomputed on corrected tiers. The terrain run passes all five ASE evidence categories under the existing transparent labels.
11. **ASE-2:** not authorized. Human review is required before any next phase.

## Technical record

- Branch: `agent/atomic-structure-foundry`
- Checkpoint: `ASE-1.1-CEREBUS-GENERATION-A-CONTRACT-REPRODUCTION`
- Dataset: `EURUSDPRO_M5_2023_2025.csv`
- Dataset SHA256: `46e81261f5799fdebb4a2d2aed045c91ad5f2bbe3324c0275cb3cc322f18b13b`
- Development: `2023-01-03` through `2024-12-31`
- Timeframe: M5; timezone `America/New_York` with DST
- Total valid sessions: 442
- Calibration sessions: 432
- NO-GO sessions: 10
- Loops after repaired AU/tier namespace: 11,252
- Raw all-days control: 16.9003 / 33.4579 / 218.4000p
- Gated k=3: 13.7137 / 22.5500 / 34.6273p
- Operational boundaries: T1 `<20`, T2 `20-<30`, T3 `30-<=45`, NO-GO `>45`
- Causality: PASS (future perturbation, tail truncation, head truncation, prefix consistency)
- Tests: 20 passed, 0 failed

## Evidence matrix

`SCALE=PASS`, `NORMALIZATION=PASS`, `STATE=PASS`, `TIME=PASS`, `CAUSALITY=PASS`.

The scale result is now based on the Generation-A gated calibration population rather than the invalid heavy-tail all-days fit. This is contract reproduction, not a PnL result.

## Guardrails

- `strategy_pnl_computed = false`
- `optimization_performed = false`
- `confirmation_consumed = false`
- `holdout_consumed = false`
- `ASE2_authorized = false`

The existing ASE-1 empirical report and raw control remain preserved as historical evidence. This report is the repair lane and does not rewrite the original trail.
