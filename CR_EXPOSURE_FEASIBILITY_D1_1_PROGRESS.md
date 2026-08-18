# CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE — PROGRESS

**Status:** PASS — committed, pushed, other checkout synced.

## What was built

Lane A of the D1 feasibility plan, executed on the sealed 826-event economic
target book through a new pure engine
(`src/capital_routing/feasibility/notional_feasibility.py`):

- `assess_notional_cap(EconomicTargetRef, max_notional_multiple)` — pure,
  deterministic, fail-closed (0 / negative / NaN / inf caps rejected; NaN /
  inf targets rejected), account-size invariant (equity cancels out of m_t)
- frozen grid EXACTLY [0.5, 1, 2, 4, 8, 16, 32, 64]; replication of the D1
  preregistered counts 39 / 178 / 417 / 655 / 786 / 817 / 825 / 826 — PASS
- family coverage replication (A 0.54 → 100%, B 8.13 → 100%) — PASS
- distortion surfaces: family (share shifts), pos (orig/surv/blocked), frozen
  quantile bins, subperiod (split / year / quarter), regime (session /
  severity; volatility bucket & signal subtype = NOT_AVAILABLE_IN_SEALED_LEDGER),
  episode (482 @ 12h; fully preserved / partial / eliminated; orig max
  concurrency 3)
- equity invariance (5k / 25k / 100k): m_t and classification identical
- performance diagnostic (blocked → 0, survivor keeps sealed normalized
  return), all 8 cells reported, NO selection — `preferred_cap_selected =
  false`, `performance_based_selection = false`, `production_cap_selected =
  false`
- scenario IDs: canonical schema-versioned sorted-key JSON + SHA-256 binding
  study version / grid generation / ledger hash / cap / truth class /
  translation_id; no random UUID
- truth class: HYPOTHETICAL_DIAGNOSTIC everywhere; 22-field missing-truth
  register carried forward UNKNOWN / blocking; no broker / margin / lot /
  rounding / clipping / partial sizing
- cross-workstream heads recorded read-only after fetch: foundation
  `b94fbbae` (QL-EXEC-R3-GENERIC-SINGLE-INSTANCE-RUNTIME), TB `b48fd352`
  (TB-R6.1D), main `9f612886` (OCE Block 0) — diagnostic only

## Evidence

- 20 artifacts in
  `research/capital_routing/risk/block4_exposure_feasibility_d1_1/`
- tests: `tests/test_exposure_feasibility_d1_1.py` — 62 tests
- combined checkpoint suites: 195/195 (D1.1 + D1 + D0.1 + D0 + R1.1B + R1.1)
  plus R1 / scale-seal suites 66/66 → 261/261
- determinism: byte-identical artifact regeneration

## Key descriptive results (no selection made)

| L | surviving | A cov | B cov |
|---|---|---|---|
| 0.5 | 39 (4.72%) | 0.54% | 8.13% |
| 1 | 178 (21.55%) | 4.58% | 35.38% |
| 2 | 417 (50.48%) | 20.75% | 74.73% |
| 4 | 655 (79.30%) | 61.19% | 94.07% |
| 8 | 786 (95.16%) | 89.76% | 99.56% |
| 16 | 817 (98.91%) | 97.84% | 99.78% |
| 32 | 825 (99.88%) | 99.73% | 100% |
| 64 | 826 (100%) | 100% | 100% |

A-share shift is negative at every cap (A's larger economic notional demand is
filtered first): -0.3979 at L=0.5 → 0 at L=64.

## Next

CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN —
PLAN FIRST, `d1_2_authorized = false` until human review. Requires frozen
intended account / broker / USDJPY product / contract size / volume
min-step-max / account currency with provenance.
