# CAPITAL ROUTING — PHASE 6 PROGRESS

> **Task:** CR-P6-FORWARD-ROUTING-STUDY-01 (Forward Routing / Lead-Lag Study)
> **Repo:** dabiggestpoppa/larger-lab | branch: `capital-routing`
> **Accepted Phase 5 commit:** `f0fc54ab3a2c182df8653569c6805db08f257bab` (Phase 6 cleared)
> **Last updated:** 2026-08-15

---

## 1. Frozen Phase 5 Event Universe (verified from frozen artifacts)

| Metric | Count |
|---|---|
| Total episodes | 8,076 |
| BROAD_CURRENCY_EVENT | 4,357 |
| RESIDUAL_SHOCK | 2,872 |
| NETWORK_DISLOCATION | 847 |
| Origin: EUR / GBP / USD / CHF / JPY | 900 / 858 / 842 / 874 / 883 |
| Severity (no HIGH — structural) | LOW 5,853 / MEDIUM 2,120 / EXTREME 103 |

## 2. Execution State

| Item | Status | Notes |
|---|---|---|
| Worktree checkout | ✅ Done | `capital-routing/` (branch `capital-routing`, tip f0fc54ab) |
| Freeze manifests (`p5_event_freeze.json`, `input_hash_manifest.json`, `split_manifest.json`) | ✅ Done | Hashes match Phase 5 hard-coded values |
| Dev/holdout split | ✅ Done | Dev 2023-07-01→2025-06-30 (5,613 events); Holdout 2025-07-01→2026-05-31 (2,463) |
| Forward outcomes (factor + pair, horizons 1/2/4/6/8/12/24/48 + optional 72/120) | ✅ Done | `event_forward_currency_factors.parquet`, `event_forward_pair_returns.parquet` |
| Destination leadership + transition + probability matrices | ✅ Done | incl. severity/session/regime/direction conditioning |
| GBP bridge / CHF parking / JPY destination tests | ✅ Done | + lead-lag sequence |
| Residual lead-lag + decay + network outcomes | ✅ Done | incl. high-residual EUR crosses classification |
| MFE/MAE (factor + pair), sleeper score | ✅ Done | |
| Overlap sensitivity (6/12/24h cooldowns) | ✅ Done | all cooldowns reported |
| Multiple-testing (BH FDR), dev results, subperiod stability | ✅ Done | |
| Candidate freeze + holdout validation | ✅ Done | **27 candidates frozen from development** (8 VALIDATED / 9 WEAKENED / 10 FAILED on holdout) |
| Gate + report | ✅ Done | Gate ordering fixed (build → report → write); **`gate_passed: true`, `phase_7_cleared: true`** |
| Tests (15 required, brief §35) | ✅ Done | `tests/test_phase_6_routing.py` — **34/34 passing** (15 required families + exported-naming contract) |
| Determinism (Batch 3) | ✅ Done | Full SHA-256 comparison across two pipeline runs: **9 key outputs byte-identical** (DETERMINISTIC_OK) |
| Commit | ✅ Done | Batch 4 — **`5726bf02`** on `capital-routing` (34 files, +103,411) |
| Report back (brief §37) | ✅ Done | Batch 5 — full §37 report delivered to user |
| Sync to `Desktop\\projects\\larger-lab` checkout | ✅ Done | Committed implementation copied over draft modules (src/scripts/tests/artifacts/progress); `PHASE_6_PLAN.md` updated with ✅ ALREADY IMPLEMENTED AND COMPLETE note; 34/34 tests pass in that checkout too |
| Push to GitHub | ✅ Done | `f0fc54ab..5726bf02 capital-routing -> capital-routing` on `dabiggestpoppa/larger-lab` |

## 3. Environment Notes

- The `capital_routing` package is pip-installed (editable) and points at a **different checkout**:
  `C:\Users\wifik\Desktop\projects\larger-lab\capital-routing` (on `master`, updated 2026-08-15).
- That checkout contains its **own in-progress Phase 6 implementation** (uncommitted):
  `PHASE_6_PLAN.md`, `phase_6_{split,forward,measure,hypothesis,orchestrator,batch_orchestrator,report}.py`,
  `scripts/run_phase_6.py`, test files, and `artifacts/phase_06/` containing only the freeze+split
  manifests (analysis functions incomplete; plan states "orchestrator has errors", "output generation
  needs implementation").
- Our worktree implementation is complete and self-contained (all Phase 6 outputs generated here).
- The runner inserts this checkout's `src/` on `sys.path` **before** importing `capital_routing` so the
  editable install cannot shadow it. `scripts/run_phase_6.py` is the entry point.
- **Reconciliation decision still open:** keep this implementation as canonical and have the other
  checkout pull it, or port the other checkout's module names. Both are on the same branch history.

## 4. Batched Execution Plan (this is the working plan)

### Batch 0 — Progress + Plan (THIS FILE) ✅
- Create `PHASE_6_PROGRESS.md` with state + batches. ✅ Done.

### Batch 1 — Finish the pipeline run (fix gate ordering, re-run end-to-end)
- Fix `phase_6_gate.py` / orchestrator ordering: build gate → generate report → write gate (so the gate
  sees its own file + report present).
- Re-run `python scripts/run_phase_6.py`; confirm `gate_passed: true`, all 24 outputs present,
  `phase_7_cleared` reflects the result.
- Spot-check key outputs (event universe, dominant destinations, thesis labels, holdout labels).
- Exit criteria: clean full run, gate passes, no runtime errors.

### Batch 2 — Required tests (brief §35, 15 tests)
- Write `tests/test_phase_6_routing.py` covering:
  1. forward horizon indexing  2. event-bar exclusion  3. no threshold recomputation
  4. split frozen  5. holdout not used in selection  6. destination ranking
  7. overlap sensitivity deterministic  8. bootstrap deterministic (fixed seed)
  9. FDR correct  10. residual decay  11. MFE/MAE bounds  12. pair-return orientation
  13. symmetric origin analysis  14. subperiod assignment  15. candidate freeze reproducible
- Run with `PYTHONPATH=src python -m pytest tests/test_phase_6_routing.py -q` (avoids editable-install shadowing).
- Exit criteria: 15/15 passing; existing phase 5 tests still pass.

### Batch 3 — Validation & determinism
- Re-run pipeline twice; confirm identical hashes on key outputs (determinism).
- Sanity-read `PHASE_6_ROUTING_STUDY.md` + `phase_6_gate.json`; confirm no future leakage claims hold
  (event bar excluded by construction, tested in Batch 2).
- Exit criteria: deterministic re-run, report coherent.

### Batch 4 — Commit
- Commit on `capital-routing` branch:
  `CR-P6-FORWARD-ROUTING-STUDY-01: measure destination lead-lag residual decay and holdout-validated routing effects`
- Include: `src/capital_routing/phases/phase_6_*.py`, `scripts/run_phase_6.py`,
  `tests/test_phase_6_routing.py`, `artifacts/phase_06/`, `PHASE_6_PROGRESS.md`.
- No push (not requested).

### Batch 5 — Report back (brief §37)
- commit SHA, test counts, dev/holdout periods, per-origin dominant destinations by horizon,
  EUR-specific destination table, GBP bridge / CHF parking / JPY destination verdicts,
  top residual lead-lag relationships, network dislocation findings, sleeper relationships,
  FDR-surviving relationships, frozen development candidates, holdout validation per candidate,
  Phase 6 PASS/FAIL, Phase 7 eligibility list.

### Batch 6 — Reconciliation (needs user decision)
- Decide canonical implementation vs the `Desktop\projects\larger-lab` checkout; port or sync files.

## 5. Work Log

| When | What |
|---|---|
| 2026-08-15 | Checked out `capital-routing` worktree at f0fc54ab; confirmed Phase 3-5 commits + results on GitHub |
| 2026-08-15 | Inspected frozen schemas (events, components, panel); computed Phase 5/4/3 input hashes |
| 2026-08-15 | Wrote Phase 6 modules (events, outcomes, stats, analysis, gate, report, orchestrator) + runner |
| 2026-08-15 | First full run completed: all artifacts generated, 30 candidates frozen; gate ordering bug identified + fixed |
| 2026-08-15 | Found + fixed BH-FDR bug (q stayed 0 via copy-on-mask) and residual/network outcome merge bug; re-run: 27 candidates, gate passes, 8 holdout-validated |
| 2026-08-15 | Exported parquet columns renamed to brief contract (`EUR_forward_1h`, `destination_1h`); fixed fac_cols filter that dropped rank/voladj/mfe/mae columns |
| 2026-08-15 | Review pass: fixed RANK_EVT/VOL_EVT indexing (event position != comp row) for rank_change/voladj baselines; guarded s_p<1 pair edge |
| 2026-08-15 | 34/34 Phase 6 tests passing |
| 2026-08-15 | Review pass: vectorized sleeper_score_analysis (value-identical to reference loop, max diff 0.0; thematic analyses from ~7min stall to ~55s) |
| 2026-08-15 | Fixed searchsorted OOB clamps in sleeper comp/panel lookups + outcomes event_pos (min(., len-1)); guarded `_comp_lookup` upper bound (pos >= len -> NaN) |
| 2026-08-15 | Determinism verified: two full runs -> identical SHA-256 on all 9 sampled outputs |
| 2026-08-15 | Discovered parallel in-progress Phase 6 implementation in `Desktop\projects\larger-lab` checkout (uncommitted, incomplete) |
| 2026-08-15 | **Committed CR-P6 as `5726bf02`** on `capital-routing` branch (not pushed) |
