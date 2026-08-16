# MVE R0.5.2 — INDEPENDENT CAUSALITY REGATE REPORT

> **Checkpoint:** MVE-R0.5.2-CAUSALITY-REGATE · 2026-08-15
> **Base (repair commit):** `30d4f1adf5ce58b6be4445537b9c5ab22d85ed73`
> **Prior gate commit:** `cb0020cee33a493abf358991effb1a7bf74d1c3f`
> **Verdict:** **PASS** — `mve_r05_2_regate_pass = true` · `infrastructure_sealed = true` ·
> `scientific_phase4_ready = true` (infrastructure only; P4 NOT authorized)
>
> This is a VERIFICATION checkpoint. No code was modified. The repaired
> R0.5.1 candidate was re-measured independently (fresh process, fresh
> mutation routine, protocol frozen BEFORE any run).

## Protocol (frozen before the run — `MVE_R05_2_REGATE_PROTOCOL.md`)

| Parameter | Value |
|---|---|
| Source commit | `30d4f1adf…` (verified at run start; see `MVE_R05_2_INPUT_HASH_MANIFEST.json`) |
| Data slice | 2023-07-03 00:00 → 2024-03-31 23:00 UTC (H1), 4,652 bars — exact prior dev slice, not expanded |
| Mutation | fresh `regate_mutate`: per-row `exp(U(-m,+m))`, `m ∈ {3,6,9}`, half the tail rows sign-flipped; seeds `[5001, 5002]` (never used before) |
| Cutoffs | 0.35 / 0.65 / 0.85 of the slice (3 cutoffs × 2 seeds × 3 magnitudes = **18 combos per component**) |
| Tolerance | 0.0 for every executable component |
| Gate-eligible components | 28 (7 volatility estimators, 8 anchors incl. delayed pivots, morphic coords + frozen/live sigma, sigma states ×2, acceptance ×2, regime state map, RKEY-A/B/C, Models A/B/C) |
| Excluded (measured, not gate-eligible) | Model D, Model E — both `BLOCKED_LOGIC_SPEC` |

## Evidence

### Future-perturbation matrix — **PASS** (`MVE_R05_2_FUTURE_PERTURBATION_RESULTS.json`)
Every one of the 28 gate-eligible components shows **max historical mutation
diff = 0.0 across all 18 cutoff×seed×magnitude combinations** (504
measurements). The only nonzero diff in the entire matrix is Model E
(`signals/model_E_trend_score`, max = 1.0) — the expected whole-sample-Q
repaint, recorded as a BLOCKED finding, not a pass.

### Truncation invariance — **PASS** (`MVE_R05_2_TRUNCATION_INVARIANCE.csv`)
28 eligible components × 3 cutoffs = 84 rows, all `max_abs_diff = 0.0`.
RKEY-B special cases (before breakout / at breakout / during retest wait /
exactly at confirmation / after confirmation) are in the RKEY-B audit: no
active rekey before the retest bar, activation exactly at the confirmation
bar, and history identical across truncations.

### Event-time schema — **PASS** (`MVE_R05_2_EVENT_SCHEMA_AUDIT.json`)
Scientific-event, acceptance, and rekey validators accept valid realtime +
delayed fixtures and reject (fail closed): known < evidence, action < known,
missing fields, and NaT timestamps. 3,803 real-data RKEY-B events validate.

### Pivot delay — **PASS** (`MVE_R05_2_PIVOT_DELAY_AUDIT.json`)
`apply_anchor_delay(pivots, window=5)` produces NaN in the first 5 rows (no
consumption before confirmation); knowledge-filtered raw pivots and delayed
coordinate consumption are invariant (0.0). On this slice no pivot's
confirmation window straddles the 0.65 cutoff, so even the raw (undelayed)
comparison is 0.0 on real data — the no-delay-filter repaint is demonstrated
on the adversarial fixture in `tests/mve/test_causality.py::test_anchors_consumed_only_after_confirmation`.

### RKEY-B — **PASS, no backdating** (`MVE_R05_2_RKEY_B_AUDIT.json`)
Deterministic fixture: breakout at bar 40, retest confirmation at bar 43.
Truncating before/at breakout or during the retest wait yields NO active
rekey (identity); truncating at 43 activates only then; future mutation after
43 cannot move the anchor earlier. All 77 synthetic + 3,803 real events obey
`event <= evidence <= known <= active`; `new_anchor` formula unchanged
(coordinate at the scan-origin bar).

### Models A / B / C — **PASS**
- **Model A** (`MVE_R05_2_MODEL_A_AUDIT.json`): LONG crossing at i emits at
  i+1 only; SHORT mirror at i+1; invalidating next bar emits nothing;
  future mutation after the known time does not repaint known history.
- **Model B** (`MVE_R05_2_MODEL_B_AUDIT.json`): accepted-state signal at i is
  unchanged when bar i+1 (and beyond) is radically mutated → realtime.
- **Model C** (`MVE_R05_2_MODEL_C_AUDIT.json`): entry known only at the
  +2-sigma confirmation bar (never the crossing bar); confirmed entry
  correctly takes priority over a same-bar exit.

### RKEY-C robustness — **PASS** (`MVE_R05_2_RKEY_C_ROBUSTNESS.json`)
Leading-NaN warm-up, isolated NaN, and NaN runs: no crash, NaN positions stay
NaN, no synthetic rekeys, identity until the first valid window, full
recovery. (First-bar/partial-warm-up/first-valid-window coverage per spec.)

### Model D / E exclusion — **BLOCKED, correctly excluded**
- **Model D** (`MVE_R05_2_MODEL_D_EXCLUSION_AUDIT.json`): NaN warm-up no
  longer crashes; contradictory conditions untouched; not in the eligible
  pipeline; `runner.py` has no signal path (phases 4–7 remain
  `BLOCKED_SCIENTIFIC_IMPLEMENTATION`).
- **Model E** (`MVE_R05_2_MODEL_E_EXCLUSION_AUDIT.json`): measured repaint
  max diff 1.0 confirmed; `generate_all_signals` includes
  `morphic_trend_score`, so that aggregate is itself classified
  `BLOCKED_AGGREGATE` (not gate-eligible) until Model E is resolved; runner
  cannot enable it; blocked status machine-readable in
  `MVE_R05_1_STUB_CLASSIFICATION.json`.

### Pipeline contamination — **PASS** (`MVE_R05_2_PIPELINE_CONTAMINATION_AUDIT.json`)
The full eligible pre-P4 aggregate (loader → resampler → volatility →
anchors → coordinates → sigma states → occupancy/acceptance → RKEY-A/B/C →
Models A/B/C) has **max historical mutation diff = 0.0**. Injecting Model E
into the same aggregate produces diff 1.0 — the gate provably catches
blocked-module leakage. M5→H1 hour-boundary invariance also holds (a closed
H1 bar is unaffected by future M5 rows).

### Static leakage re-audit — **clean** (`MVE_R05_2_STATIC_LEAKAGE_SUMMARY.json`)
24 pattern hits in `src/mve`: 14 `EX_POST_ONLY` (descriptive
forward-return/transition analyzers, preserved per R0.5.1-N), 6
`CAUSAL_DELAYED_CONFIRMATION` (pivot right-window, Model A i+1), 3
`SAFE_CAUSAL` (unused `find_peaks` imports), 1 `BLOCKED_LOGIC_SPEC`
(Model E whole-sample Q). **0 unclassified, 0 violations.**

### Ex-post separation — **PASS** (`MVE_R05_2_EXPOST_DEPENDENCY_AUDIT.json`)
21 causal entry points audited; **causal→ex-post dependency count = 0**. No
gate-eligible component calls any forward-return/`analyze_*` helper.

### Holdout — **untouched** (`MVE_R05_2_HOLDOUT_GUARD.json`)
`FINAL_HOLDOUT_PENDING` unchanged; `holdout_rows_read = 0`; slicing 2026
fails closed. Every measurement used only the 2023-07-03..2024-03-31 dev
slice (ledger: `MVE_R05_2_DATA_ACCESS_LEDGER.json`).

## Tests

```
collected: 82
passed:    82
failed:    0
skipped:   0
```

(`python -m pytest tests/mve/ -q` — the MVE suite: 35 causality + 21
data-pipeline + 14 runner + 3 import + 9 repaired-regression tests. The
repo-wide suite additionally contains 38 pre-existing failures in
`tests/test_observer/` and `tests/pm2_po_field_test.py` — unrelated to MVE,
outside this checkpoint's scope, not touched.)

## Final status per component

| Component | Classification | Future-perturbation | Truncation | Eligible | Status |
|---|---|---|---|---|---|
| RKEY-A | CAUSAL_REALTIME | 0.0 | 0.0 | yes | **PASS / ELIGIBLE** |
| RKEY-B | CAUSAL_DELAYED_CONFIRMATION | 0.0 | 0.0 | yes | **PASS / DELAYED_ELIGIBLE** |
| RKEY-C | CAUSAL_REALTIME | 0.0 | 0.0 | yes | **PASS / ELIGIBLE** |
| Model A | CAUSAL_DELAYED_CONFIRMATION | 0.0 | 0.0 | yes | **PASS / DELAYED_ELIGIBLE** |
| Model B | CAUSAL_REALTIME | 0.0 | 0.0 | yes | **PASS / ELIGIBLE** |
| Model C | CAUSAL_DELAYED_CONFIRMATION | 0.0 | 0.0 | yes | **PASS / DELAYED_ELIGIBLE** |
| Model D | BLOCKED_LOGIC_SPEC | 0.0 | n/a | no | **BLOCKED (excluded)** |
| Model E | BLOCKED_LOGIC_SPEC | **1.0 (expected repaint)** | n/a | no | **BLOCKED (excluded)** |

Full 31-row machine-readable matrix: `MVE_R05_2_COMPONENT_MATRIX.csv`.
Decision: `MVE_R05_2_DECISION.json`.

## Seal

Per the pass gate, the R0.5 infrastructure seal is written:
`MVE_R05_INFRASTRUCTURE_SEAL.md` + `MVE_R05_INFRASTRUCTURE_SEAL.json`
(see next file). `scientific_phase4_ready = true` means the infrastructure is
ready to IMPLEMENT Phase 4 — **not** that P4 science exists.

## STOP

Stopping per the spec. P4 (`MVE-P4-CAUSAL-ACCEPTANCE-ENGINE`) requires
separate human authorization.
