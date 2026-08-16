# MVE R0.5 — FINAL INFRASTRUCTURE SEAL

> **Sealed:** 2026-08-15 · **Branch:** `cerebus-mve-implementation`
> **Checkpoint:** MVE-R0.5.2-CAUSALITY-REGATE (PASS) · `infrastructure_sealed = true`
> **R0.5 commits:** `e92505e2b` (truth repair) → `b92e14272` (source/import) →
> `a3a5c81ce` (data pipeline) → `feed1fb65` (runner/persistence) →
> `cb0020cee` (causality gate) → `30d4f1adf` (stub causal repair) →
> **this checkpoint** (independent regate).
>
> **What this seal means:** the CEREBUS MVE research infrastructure is now
> causally clean and deterministic enough to begin implementing scientific
> Phase 4. **It does NOT mean the MVE strategy works, and it does NOT authorize
> P4.** `scientific_phase4_ready = true` only means: infrastructure is ready to
> IMPLEMENT P4. P4 science requires separate human authorization.

## Frozen state

### DATA
- Canonical dev source: `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`
  (SHA-256 `630b8a4052fe962bc7d87c6d49d83bc1524c7ddd83cd15e902fe504c998d3f77`,
  verified fail-closed at every load — no fallback, no alternate-file selection).
- Timeframe: M5 → H1 via the committed resampler (open=first, high=max,
  low=min, close=last, volume=sum; empty weekend hours dropped; no
  forward-fill; `source_bar_count` recorded). Deterministic.
- Missing-data behavior: fail-closed on hash/size/schema/timestamp/OHLC
  violations; no synthetic substitution anywhere in the research path.
- Authorized ranges: development 2023-07-03..2024-12-31, confirmation
  2025-01-01..2025-12-31. Slicing beyond → `DataPipelineError`.

### TIME
- Bar timing frozen in `MVE_R05_BAR_TIMING_CONVENTIONS.md`: event time ≤
  evidence complete ≤ known ≤ action (standard schema
  `MVE_SCIENTIFIC_EVENT_TIME_SCHEMA.json`, validator-enforced).
- Pivot delay semantics: event at i, known at i+window; consumption must use
  `apply_anchor_delay(pivots, window)`.

### VOLATILITY
- Causal estimators eligible for future science (all future-mutation and
  truncation invariant, max diff 0.0): close_to_close, EWMA, Parkinson,
  Garman-Klass, ATR-normalized, MAD, GARCH (rolling-std stand-in — fidelity
  of the GARCH *specification* is unverified; not a causality issue).
- Ex-post quality analyzers (`analyze_estimator_quality`) excluded from
  causal execution.

### ANCHORS
- Realtime causal: support/resistance, trend-line, volume-profile, time-based,
  volatility-based (all 0.0).
- Delayed: pivot high/low (0.0 knowledge-filtered; consumption only via
  `apply_anchor_delay`).
- Ex-post/blocked: anchor quality metrics (`evaluate_anchor_quality` family)
  are descriptive only.

### COORDINATES
- `calculate_morphic_coordinates` is causal given causal anchors/sigma
  (0.0). Frozen-sigma and live-sigma fields are causal and cannot repaint
  their history.

### SIGMA STATES
- `classify_sigma_states` / `detect_sigma_events` causal (0.0); state at t
  uses only anchor/sigma/price ≤ t.

### ACCEPTANCE PRIMITIVES
- `calculate_occupancy` / `classify_acceptance` causal (0.0).
- **P4 acceptance science itself has NOT been run.** The causal schema
  (`MVE_ACCEPTANCE_CAUSAL_SCHEMA.json`) is frozen for P4 to implement
  against: `state_event_time ≤ evidence_complete_time ≤ acceptance_known_time`.

### REKEY
- RKEY-A: causal (0.0). RKEY-B: delayed causal (0.0; no backdated anchor).
- RKEY-C: causal + NaN-robust (0.0).
- Schema frozen (`MVE_REKEY_CAUSAL_SCHEMA.json`).

### SIGNALS
- Model A: causal delayed (0.0). Model B: causal realtime (0.0). Model C:
  causal delayed (0.0).
- Model D: `BLOCKED_LOGIC_SPEC` (contradictory conditions; excluded).
- Model E: `BLOCKED_LOGIC_SPEC` (whole-sample Q repaint, measured 1.0;
  excluded). `generate_all_signals` is a `BLOCKED_AGGREGATE` until E is
  resolved.

### EX-POST
Strictly separated: 14 sites classified `EX_POST_ONLY`; causal→ex-post
dependency count = 0. Static leakage re-audit: 0 unclassified, 0 violations.

### HOLDOUT
`FINAL_HOLDOUT_PENDING` — untouched (`holdout_rows_read = 0`). No 2026
access, no relabeling. `MVE_R05_2_HOLDOUT_GUARD.json`.

## Classification summary

| Checkpoint | Status |
|---|---|
| Data truth | `data_truth_pass = true` |
| Source integrity | `source_integrity_pass = true` |
| Runner / persistence | `runner_pass = true` |
| Causality | `causality_pass = true` (independent regate, fresh measurements) |
| Holdout | `holdout_truthful = true` |
| Scientific P4 ready | `scientific_phase4_ready = true` (infrastructure only) |

Evidence: `MVE_R05_2_DECISION.json`, `MVE_R05_2_REGATE_REPORT.md`,
`MVE_R05_2_FUTURE_PERTURBATION_RESULTS.json`,
`MVE_R05_2_TRUNCATION_INVARIANCE.csv`, `MVE_R05_2_COMPONENT_MATRIX.csv`,
`MVE_R05_2_PIPELINE_CONTAMINATION_AUDIT.json`,
`MVE_R05_2_INPUT_HASH_MANIFEST.json`, `MVE_R05_2_DATA_ACCESS_LEDGER.json`.

## Pending before P4 science
1. Human authorization to implement `MVE-P4-CAUSAL-ACCEPTANCE-ENGINE`.
2. Model D and Model E remain BLOCKED and are flagged as P6/P7
   prerequisites (Model D: timeframe-mapping resolution; Model E: per-bar Q
   definition), not P4 prerequisites.
