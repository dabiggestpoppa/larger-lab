# CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN — Progress

**Base:** `3fde3bb1cf590c554241c23daa14e3d2242998aa` (D0.1)
**Status:** PASS (preregistration; no feasibility engine, no broker)

## What was done

- Verified base commit + clean tree; `git fetch` at checkpoint start; recorded
  cross-workstream heads read-only:
  - execution-runtime-foundation `52e39b13` (QL-EXEC-R2.1-MT5-FILL-POLICY-AND-RESULT-TRUTH-REPAIR)
  - tb-forward-engine `b48fd352` (TB-R6.1D-BOOT-FLOW-STACK)
  - main `dfdca6ac`
- Engine-verified frozen science: 890 events (A 432 / B 458), 826 ACCEPT_FULL
  (A 371 / B 455), 64 REJECT_HEAT_CAP, 1R 24.49489742783178 bps.
- Engine-recomputed frozen economic target distribution from the R1 notional
  multiplier ledger — matches the brief exactly (pooled median 1.984234123119,
  p95 7.610483704796, p99 16.036374775248, max 32.766258738096; A median
  3.351336289995; B median 1.284996946428).
- Verified concurrency truth from frozen sources: max concurrency 3, hours
  2/3/4+ = 565/20/0, max gross exposure 18.1878 f-units, episodes (12h) = 482.
- Inspected execution-runtime-foundation contracts read-only for interface
  evidence (AccountObservedState, BrokerCapabilities tri-state, SymbolInfo
  mapping incl. contract_size/volume_min/step/max/tick, AccountState, FakeMT5
  fixture contract) — nothing imported, nothing modified.
- Preregistered the notional diagnostic grid anchored mechanically to the
  observed pooled distribution: L ∈ {0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0}
  (pooled survival 4.72% / 21.55% / 50.48% / 79.30% / 95.16% / 98.91% /
  99.88% / 100%). Grid is a stress surface; all cells shown;
  `diagnostic_grid_optimized_on_performance = false`.
- Generated 31 artifacts in
  `research/capital_routing/risk/block4_exposure_feasibility_d1_plan/`
  (protocol, SHA manifest, scientific question, source hierarchy, truth-class
  schema, instrument-spec schema + requirements CSV, account physical contract
  schema, feasibility-state schema, faithfulness metrics, grid, quantity /
  rounding / margin / currency / account-size plans, concurrency-episode plan,
  coverage / family / pos / time-regime distortion plans, performance
  reconstruction, counterfactual lanes, falsification criteria, missing-truth
  register (22 fields, all UNKNOWN, all blocking), runtime handoff,
  implementation sequence (D1.1..D1.6), test plan, component status, report,
  decision).
- Tests: 20 new (`tests/test_exposure_feasibility_d1_plan.py`); all 6
  checkpoint suites combined = **164/164 pass**; runner byte-identical
  determinism verified.

## Decision highlights

- d1_plan_pass = true, d1_1_ready = true, **d1_1_authorized = false**
- production_authorized = false, broker_execution_performed = false,
  strategy_science_changed = false, human_review_required = true
- Next recommended (not started): CR-RISK-BLOCK-IV-D1.1-
  BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE
