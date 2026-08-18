# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Report

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 · **Status:** PASS
**Base:** 991d8126ae9822e3b5457000c560626ea590a3a0

## What was built
The PURE capital translation core (`src/capital_routing/translation/`):
sealed CapitalDecision + AccountBinding + event pos_t ->
EconomicExposureTarget, with the corrected R1 formula
N = E x (f/100) x pos_t x 1e4/RISK. Driven over the full 890-event sealed
ledger (equity-normalized E = 1.0). NO broker fields, NO H1/family recompute,
NO dynamic resizing, NO broker execution.

## Admission parity (immutable upstream decisions consumed, never recomputed)
890 events · A 432 / B 458 ·
826 ACCEPT_FULL (A 371 / B 455) ·
64 REJECT_HEAT_CAP. requested_f A 0.70 /
B 0.30; f_total 1.00%.

## Parity through the core (equity-normalized)
- notional: PASS (max err 4.98e-13)
- gross account return: PASS (max err 9.35e-15) — translated
  (N/E) x ret/1e4 == admitted_f x pos x ret/RISK
- research-modeled net (frozen cost_bps): PASS (max err 9.39e-15)
- execution-level net: BROKER_DEPENDENT_UNRESOLVED (broker cost not frozen)

## Rejected events
64 REJECT_HEAT_CAP -> all NO_EXPOSURE with zero budget /
zero notional / zero price move (True).

## H1 examples (upstream authority; D0 consumes, never recomputes)
[
  {
    "case": "A_then_A_over_cap",
    "got_decisions": [
      "ACCEPT_FULL",
      "REJECT_HEAT_CAP"
    ],
    "admission_matches": true,
    "max_gross_heat_f_units": 0.7
  },
  {
    "case": "A_then_B_exact_cap",
    "got_decisions": [
      "ACCEPT_FULL",
      "ACCEPT_FULL"
    ],
    "admission_matches": true,
    "max_gross_heat_f_units": 1.0
  },
  {
    "case": "B_then_B_then_B",
    "got_decisions": [
      "ACCEPT_FULL",
      "ACCEPT_FULL",
      "ACCEPT_FULL"
    ],
    "admission_matches": true,
    "max_gross_heat_f_units": 0.8999999999999999
  }
]

## Idempotency + snapshot contract
{
  "idempotency_pass": true,
  "n_repeated": 25,
  "translation_ids_stable": true,
  "snapshot_driven_scaling_pass": true
} —
translate() is pure: same inputs -> same output; equity comes only from the frozen BoundAccountSnapshot (no dynamic resizing, no mark-to-market, no internal state)

## Decision
core_is_pure = true (translator_recomputes_h1/family/model_heat = false) ·
admission_parity_pass = true · rejected_zero_exposure_pass = true ·
gross_parity_pass = true · research_net_parity_pass = true ·
idempotency_pass = true · broker_execution_performed = false ·
implementation_ready = true · implementation_authorized = false ·
production_authorized = false · human_review_required = true.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D1
(instrument-spec + rounding engine, pending account-binding truth).
