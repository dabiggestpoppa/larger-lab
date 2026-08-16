# MVE R0.5 — CAUSALITY GATE REPORT

> Checkpoint: MVE-R0.5-CAUSALITY-GATE · 2026-08-15
> Data: canonical EURUSD (`630b8a40…d3f77`), bounded dev slice
> 2023-07-03..2024-03-31 (4,652 H1 bars). 2026 holdout untouched.

## Verdict

**`causality_gate_pass = false`** — with a clear split:

- **Infrastructure causality: PASS.** The loader, resampler, volatility
  estimators (7), morphic coordinates, sigma classification, sigma events,
  occupancy/acceptance, regime labeling, runner, and persistence are all
  future-mutation invariant and truncation invariant.
- **Scientific stubs: 4 recorded violations** in `BLOCKED_SCIENTIFIC_IMPLEMENTATION`
  code (RKEY-B repaint; signal Models A/B/C 1-bar backdating) + 2 robustness
  defects (RKEY-C `int(NaN)` crash; Model E undefined `n`).

Per the pass gate, "no unresolved critical violation" anywhere in the MVE
source is required — so the gate formally fails until the violations are
repaired under human authorization.

## What was proven (all measured on real data)

| Component group | Future perturbation | Truncation invariance |
|---|---|---|
| volatility (7 estimators) | 0.0 (all) | 0.0 (all cutoffs) |
| morphic coordinates (causal anchors) | 0.0 | 0.0 |
| frozen sigma | 0.0 | 0.0 |
| live sigma history | 0.0 | 0.0 |
| sigma state classification / occupation | 0.0 | 0.0 |
| occupancy / acceptance classification | 0.0 | 0.0 |
| RKEY-A | 0.0 | 0.0 |
| RKEY-C | 0.0 | 0.0 |
| MTF signal (Model D) | 0.0 | n/a |
| pivot confirmed (knowledge-filtered) | 0.0 | 0.0 |
| **RKEY-B** | **1.033 (VIOLATION)** | n/a |
| escape signal (Model A) | 0.0 measured (saturated slice); **violation proven on fixtures + statically** | n/a |

## The four violations (exact)

1. **`_rekey_variant_b`** — `for j in range(i + 1, min(i + 5, len))` scans
   future bars, then `rekey_anchor = current_coord` assigns the anchor at bar i.
   Future data moves a historical rekey earlier (measured repaint). Fix when
   authorized: anchor at the retest bar j (documented intent: "re-anchor only
   after breakout + successful retest").
2. **`generate_sigma_escape_signals` (A)** — signal at i suppressed/emitted
   using bar i+1's close. Fix: emit at i+1 (confirmation bar).
3. **`generate_accepted_sigma_breakout_signals` (B)** — same 1-bar backdate.
4. **`generate_recursive_morphic_trend_signals` (C)** — entry at i decided by
   bar i+1. Fix: emit at i+1.

Robustness defects (blocked, not causality): RKEY-C and Model D crash on
warm-up NaN (`int(NaN)`); Model E references undefined `n` (NameError).

## Delayed-confirmation components (exposed delay)

- **Pivot high/low**: event at i, known at i+window. `apply_anchor_delay(pivots, window)`
  is the mandatory consumption path (first `window` rows NaN).

## Ex-post-only components (labeling only, never live)

~25 methods across volatility/anchors/coordinates/regime/sigma/acceptance/rekey
analyze_* families use whole-sample statistics or forward returns for
descriptive/event-study work. See `MVE_CAUSALITY_CONTRACT.md` for the full
table.

## Holdout

`FINAL_HOLDOUT_PENDING` preserved. The causality slice is entirely inside the
development range; `slice_data` rejects any 2026 access (tested).

## Files produced

- `MVE_CAUSALITY_CONTRACT.md` · `MVE_ACCEPTANCE_CAUSAL_SCHEMA.json` ·
  `MVE_REKEY_CAUSAL_SCHEMA.json` · `MVE_R05_ANCHOR_CAUSALITY.md` ·
  `MVE_R05_BAR_TIMING_CONVENTIONS.md` · `MVE_R05_STATIC_LEAKAGE_AUDIT.md` ·
  `MVE_R05_FUTURE_PERTURBATION_RESULTS.json` ·
  `MVE_R05_TRUNCATION_INVARIANCE.csv` · `MVE_R05_CAUSALITY_RESULTS.json` ·
  `MVE_R05_FINAL_DECISION.json` · `src/mve/causality.py` ·
  `tests/mve/test_causality.py` (35 tests) · `r0_tools/generate_causality_outputs.py`

## Next step (requires human authorization)

Repair the 4 violations (each preserves documented intent, ~1-3 lines:
emit delayed-confirmation signals at the confirmation bar; anchor RKEY-B at
the retest bar), then re-run this gate → if clean, `MVE-R0.5-INFRASTRUCTURE-SEAL`
can set `scientific_phase4_ready = true`.
