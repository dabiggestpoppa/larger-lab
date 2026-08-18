# CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION — PROGRESS

**STATUS:** PASS — real read-only physical truth collected and sealed.

## What happened

- Live MT5 terminal on this machine was already connected to **Ox Securities
  demo** (`OxSecurities-Demo`, USD @ 1:500, equity 25,254.35).
- Using ONLY read-only MetaTrader5 API calls (account_info, symbol_select
  [Market Watch only], symbol_info, symbol_info_tick, terminal_info) captured
  the **USDJPY.PRO** product spec: contract_size 100,000 (OBSERVED, not
  assumed), volume 0.01/0.01/200.0, digits 3, tick 0.001, tick_value
  0.626731 USD, base USD / profit JPY / margin USD, calc mode 0.
- No mutating calls: no order_send, no order_check, no modification, no
  close/cancel, no account mutation.
- Evidence frozen in `_raw_observation.json` (sanitized: pseudonymous
  account id `OX-DEMO-<sha256(login)[:12]>`, personal name REDACTED, no
  login, no credentials).
- Quantity conversion RESOLVED: `raw_volume = target_USD_notional / 100000`
  — account currency == base currency (USD), direct base-USD mapping, no FX
  conversion price needed. Tick-value cross-check consistent.
- Long/short symmetric = true (no side-dependent volume/contract fields).
- Profile sealed: **PHYSICAL_PROFILE_GENERATION_G1**,
  `OX_DEMO_USDJPY_PRO_G1`, SEALED_ACTUAL_QUANTITY_COMPLETE,
  quantity_minimum_complete=true, margin_complete=false (D1.3).
- `d1_2b_ready=true` · `d1_2b_authorized=false` (human gate) ·
  `production_authorized=false` · `human_review_required=true`.

## Nonregression

890 / 826 / 371 / 455 / 64 · book hash
`b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` · 1%
fidelity tolerance · ROUND_DOWN_TOWARD_ZERO · no clipping · no upward
rounding — all unchanged. No broker order, no broker write.

## Deliverables

14 artifacts in
`research/capital_routing/risk/block4_physical_truth_collection_d1_2a1/`
+ `_raw_observation.json` frozen evidence. 56 new tests; combined
**430/430 across 13 suites**; determinism byte-identical; offline runner
(evidence-driven, no network/MT5 dependency in code).

## Next

CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE — **not started**,
awaiting human authorization.
