# CR-BLOCK4-D1.2A1 REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION
**Base:** `052223762034d1fe4bf974698501ab955504a18d` · **Status:** PASS

## Collection result

- actual account observed: True (Ox
  Securities demo, USD @ 1:500, equity 25,254.35)
- actual USDJPY observed: True —
  broker symbol **USDJPY.PRO**, contract_size 100,000, volume 0.01/0.01/200.0
- truth class: ACTUAL_OBSERVED · environment DEMO

## Quantity conversion (resolved)

`raw_volume = target_USD_notional / 100000` — account currency == base
currency (USD), direct base-USD mapping; no FX conversion price needed.
Tick-value cross-check consistent (0.626731 vs
observed 0.626731).

## Completeness

- quantity_minimum_complete: **True** →
  SEALED_ACTUAL_QUANTITY_COMPLETE
- margin_complete: False (leverage/margin metadata collected; symbol
  leverage/tiers + hedging/netting remain for D1.3)
- long/short symmetric: **true** (no side-dependent volume fields observed)

## Profile seal

PHYSICAL_PROFILE_GENERATION_G1 · profile_id OX_DEMO_USDJPY_PRO_G1 ·
hash `125ba55dd8890519...`

## Nonregression

890 / 826 / 371 / 455 / 64 · book hash `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` · 1% fidelity
tolerance · ROUND_DOWN_TOWARD_ZERO · no clipping · no upward rounding —
all unchanged.  No order attempted, no broker write.

## Decision

`d1_2b_ready = True` · `d1_2b_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE (starts only after human
review).
