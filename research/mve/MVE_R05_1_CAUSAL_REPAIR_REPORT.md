# MVE R0.5.1 — SCIENTIFIC-STUB CAUSAL REPAIR REPORT

> Checkpoint: MVE-R0.5.1-SCIENTIFIC-STUB-CAUSAL-REPAIR · 2026-08-15
> Base: `cb0020cee33a493abf358991effb1a7bf74d1c3f`

## Result

**`r05_1_causal_repair_pass = true` · `r05_2_causality_regate_cleared = true` ·
`scientific_phase4_ready = false` (unchanged).**

All four R0.5-gate causality violations are repaired. The same harness
(future perturbation + truncation invariance, same dev slice
2023-07-03..2024-03-31) now shows **max historical mutation diff 0.0 for
every repaired component**, including on real data. Two components remain
BLOCKED and are excluded from future scientific execution per the pass gate.

## Repairs (authorized mechanical, preserving documented intent)

| Component | Repair | Why it is causal now |
|---|---|---|
| **RKEY-B** | anchor activation moved from scan-origin bar i to the retest bar j (anchor value formula unchanged: coordinate at the scan-origin bar) | rekey values at t depend only on bars <= t; future data can no longer move an emitted historical anchor earlier (was diff 1.033 → now 0.0) |
| **Model A** | signal KNOWN time moved to the confirmation bar i+1; documented "SHORT = mirror" implemented (the prior elif was dead code with an identical condition) | signal at i+1 uses bars <= i+1; no backdating |
| **Model B** | cosmetic next-bar read removed; realtime accepted-state signal; last-bar suppression artifact removed | output never depended on bar i+1; now provably realtime. Docstring retest-entry was never implemented → BLOCKED_LOGIC_SPEC |
| **Model C** | entry KNOWN time moved to the +2-sigma confirmation bar; confirmed entry takes priority over a same-bar exit | entry at i uses bars <= i; exit already used a trailing window |
| **RKEY-C** | NaN ready-guard (no int(NaN)); not-ready bars emit no rekey, NaN never coerced, no synthetic values | no crash; no invented science |
| **Model D** | NaN robustness guard only; contradictory conditions UNTOUCHED | no crash; logic classified BLOCKED_LOGIC_SPEC (audit in MVE_R05_1_MODEL_D_AUDIT.md) |

## Record corrections (supersede, not erase)

1. **Model E "undefined n" was a misreading.** The `boundary = n * step` line
   seen in the R0.5 gate audit belongs to `_calculate_occupancy(coords, step, n)`
   (a helper with `n` as a parameter), not to Model E. Model E runs without a
   NameError. Its real defect: the **Q component is a whole-sample scalar**
   (`(coords.diff().abs() > step).sum()/len`) broadcast into every bar —
   measured repaint under future mutation → BLOCKED_LOGIC_SPEC, excluded.
2. **Model D additionally crashed on warm-up NaN** (`int(NaN)`) — now guarded.

## Verified on real data (4,652 H1 bars, dev slice)

- Future perturbation: **only violation left is `signals/model_E_trend_score`**
  (Q whole-sample, BLOCKED/excluded). All repaired components: 0.0.
- Truncation invariance: **all_pass = true** (volatility ×7, coordinates,
  frozen sigma, sigma states, occupancy/acceptance, RKEY-A/B/C, Models A/B/C).
- `detect_rekey_events` emits schema-valid RKEY-B events (event_time <=
  evidence <= known <= active) — validated by `validate_rekey_events`.

## Final classifications (MVE_R05_1_STUB_CLASSIFICATION.json)

| Component | Classification |
|---|---|
| RKEY-A | CAUSAL_IMPLEMENTABLE |
| RKEY-B | CAUSAL_DELAYED_IMPLEMENTABLE |
| RKEY-C | CAUSAL_IMPLEMENTABLE |
| Model A | CAUSAL_DELAYED_IMPLEMENTABLE |
| Model B | CAUSAL_IMPLEMENTABLE (retest-entry semantic BLOCKED) |
| Model C | CAUSAL_DELAYED_IMPLEMENTABLE |
| Model D | BLOCKED_LOGIC_SPEC (excluded) |
| Model E | BLOCKED_LOGIC_SPEC (excluded) |

## Tests

New/updated in this checkpoint (in `tests/mve/test_causality.py`):
RKEY-B causal + truncation-before-retest + event-schema; Model A knowledge-time
i+1 (long/short/invalidation); Models B/C causal; RKEY-C NaN robustness;
Model E Q-leak detection; Model D NaN + untouched logic; scientific event
schema validation. Full-suite numbers reported at commit.

## Scientific changes

Only the authorized mechanical semantic clarifications listed above
(RKEY-B activation timing, Models A/B/C known times, Model A mirror per
documentation, NaN guards). No hypothesis, threshold, boundary, or parameter
changes. No P4/P5/P6/P7 science. No holdout access — the dev slice is
unchanged and 2026 remains `FINAL_HOLDOUT_PENDING`.

## Next authorized checkpoint

`MVE-R0.5.2-CAUSALITY-REGATE` — independent re-run of the repaired causality
gate + the R0.5 infrastructure seal. P4 stays blocked until then.
