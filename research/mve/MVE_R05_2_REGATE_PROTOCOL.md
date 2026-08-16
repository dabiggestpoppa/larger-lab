# MVE R0.5.2 — INDEPENDENT CAUSALITY REGATE PROTOCOL

> **Checkpoint:** MVE-R0.5.2-CAUSALITY-REGATE · 2026-08-15
> **Base:** `30d4f1adf5ce58b6be4445537b9c5ab22d85ed73` (R0.5.1 repair)
> **Prior gate:** `cb0020cee33a493abf358991effb1a7bf74d1c3f` (R0.5 gate)
>
> This is a VERIFICATION gate. No repairs, no threshold/anchor/signal changes,
> no P4 science, no holdout access. If any executable component fails the
> regate, this checkpoint STOPS with `REGATE_FAIL_REPAIR_REQUIRED` — no repair
> is performed in place.

## Frozen protocol (written before any measurement runs)

| Parameter | Value |
|---|---|
| Source commit | `30d4f1adf5ce58b6be4445537b9c5ab22d85ed73` (verified at run start) |
| Data slice | 2023-07-03 00:00 → 2024-03-31 23:00 UTC (H1), the exact prior dev slice — NOT expanded |
| Holdout | `FINAL_HOLDOUT_PENDING`; 2026 never sliced; `holdout_rows_accessed_for_research = 0` |
| Canonical source | `quant-lab/data/EURUSDPRO_M5_2023_2026.csv` (SHA-256 `630b8a40…d3f77`), M5 → H1 via `resample_m5_to_h1` |
| Mutation seeds | `[5001, 5002]` (fresh seeds, never used by R0.5.1 measurements) |
| Mutation magnitudes | `exp(U(-m, +m))` per row, `m ∈ {3, 6, 9}`; **signed** (half the tail rows flip sign → inverted path shapes). Implemented by a FRESH mutation routine in the regate generator (not `mve.causality.future_perturbation_check`), for independence |
| Truncation cutoffs | `0.35, 0.65, 0.85` of the slice + RKEY-B special cases (before breakout / at breakout / during retest wait / exactly at confirmation / after confirmation, synthetic fixture) |
| Tolerance | 0.0 for all executable causal components; `1e-9` only where floating-point accumulation is mathematically expected (none expected here) |
| Executable components (gate-eligible) | volatility (7 estimators), pivots (delayed), support/resistance/trend/volume/time/vol anchors, morphic coordinates (live/frozen), sigma states, occupancy, acceptance primitives, RKEY-A, RKEY-B (delayed), RKEY-C, Models A/B/C |
| Excluded components (measured but not gate-eligible) | Model D (`BLOCKED_LOGIC_SPEC`), Model E (`BLOCKED_LOGIC_SPEC` — whole-sample Q repaint expected and re-measured) |
| PASS criteria | every executable component: max historical mutation diff = 0.0 across ALL cutoff×seed×magnitude combinations AND truncation invariance = 0.0; delayed events schema-valid; RKEY-B never backdated; pipeline aggregate uncontaminated; causal→ex-post dependency count = 0; full test suite passes |
| Fail handling | any executable failure → `mve_r05_2_regate_pass = false`, `scientific_phase4_ready = false`, STOP with `REGATE_FAIL_REPAIR_REQUIRED` |

## Independent re-measurement method

For every component classified causal/delayed:

1. `base = fn(full_data)`
2. For each (cutoff t, seed, magnitude m):
   - `mutated = full_data.copy()`; rows after t × `exp(U(-m,m))`, half sign-flipped
   - `alt = fn(mutated)`
   - compare `base[:t]` vs `alt[:t]` (NaN-masked), record max abs diff
3. Truncation: `trunc = fn(data[:t])`; compare `base[:t]` vs `trunc[:t]`

Delayed components (pivots, RKEY-B): comparisons are knowledge-filtered —
values whose event time + confirmation window <= t must be invariant; values
inside the not-yet-known window may legitimately differ (that is the delayed
confirmation behavior being verified, not a leak).

## Independence from prior artifacts

- All measurements are recomputed from source in a fresh Python process.
- Prior JSON/CSV outputs are read ONLY for post-hoc comparison, never as inputs.
- The mutation routine is re-implemented in the regate generator, not reused
  from `mve.causality`.
