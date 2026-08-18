# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 — Progress

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0
**Status:** PASS · **Base:** `991d8126` (R1.1B) · **Branch:** capital-routing

## What was built

The **PURE deterministic capital translation core** —
`src/capital_routing/translation/capital_translation_core.py` (v D0-1, science
R1.1). It converts a sealed `CapitalDecision` + `AccountBinding` + event
`pos_t` into an `EconomicExposureTarget` using the R1-corrected formula:

    one_R_budget_account_ccy    = E x admitted_f_pct / 100
    target_notional_account_ccy = E x (f/100) x pos_t x 1e4 / RISK
    one_R_price_move_bps        = RISK / pos_t            (event-specific)

Driven over the **full 890-event sealed ledger** (equity-normalized E = 1.0)
through the actual core — not a vectorized shortcut:

- **Admission parity:** 826 ACCEPT_FULL (A 371 / B 455) / 64 REJECT_HEAT_CAP —
  consumed as IMMUTABLE upstream CapitalDecision inputs; the core never
  recomputes H1, family, or model heat (source-level test proves no
  admit_book/run_policy in the module).
- **Rejected → NO_EXPOSURE:** all 64 rejected events translate to zero budget /
  zero notional / zero price move, without reconsidering H1.
- **Gross parity:** translated (N/E) x ret/1e4 == admitted_f x pos x ret/RISK,
  max err **9.35e-15** across every accepted event (machine precision).
- **Research-modeled net parity** (frozen cost_bps): max err **9.39e-15**;
  execution-level net stays BROKER_DEPENDENT_UNRESOLVED.
- **Idempotency:** pure deterministic `translate()` — same inputs → identical
  output; `translation_id` = canonical hash (event | decision | policy |
  config-hash | version). Equity comes ONLY from the frozen
  BoundAccountSnapshot: no internal state, no dynamic resizing, no
  mark-to-market (fixture-tested).
- **Fail-closed validation:** stale snapshot, unknown instrument, binding
  mismatch, missing equity, unresolved currency, invalid pos/status all raise
  typed TranslationErrors.
- **Purity:** EconomicExposureTarget carries zero broker fields; no broker
  calls; science unchanged (890 / 826 / 64; canonical notional stats locked).

## Artifacts

`research/capital_routing/risk/block4_capital_translation_core_d0/` — PROTOCOL,
CORE_DOC, EVENT_TRANSLATIONS.csv, PARITY_890, H1_PARITY, REJECTED_ZERO_EXPOSURE,
IDEMPOTENCY, TEST_AUDIT, SOURCE_SHA_MANIFEST, REPORT, DECISION.
Tests: `tests/test_capital_translation_core_d0.py` (32); combined suites
95/95 (R1 + R1.1 + R1.1B + D0); determinism byte-identical.

## Decision

status PASS (fail-closed from gates) · core_is_pure (no H1/family/heat
recompute) · admission_parity_pass = true · rejected_zero_exposure_pass = true ·
gross_parity_pass = true · research_net_parity_pass = true ·
idempotency_pass = true · broker_execution_performed = false ·
broker_authorized / deployment_authorized / mt5_authorized = false ·
implementation_ready = true · implementation_authorized = false ·
production_authorized = false · human_review_required = true.

**Next (recommended, NOT started):** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D1
(instrument-spec + rounding engine, pending account-binding truth).
