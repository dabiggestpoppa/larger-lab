# CR-BLOCK4-D1.2A1 QUANTITY CONVERSION CONTRACT (RESOLVED)

## Observed contract (ACTUAL_OBSERVED, 2026-08-18T18:22:00Z)

- broker symbol: **USDJPY.PRO** (Ox Securities MT5)
- 1.0 volume = **100000.0 base units (USD)** — OBSERVED via
  trade_contract_size, NOT assumed from FX convention
- base currency **USD** == account currency **USD**
- trade_calc_mode **0** (FX_DEPTH): margin in account
  currency, profit in quote currency

## Rule

    raw_volume = target_USD_notional / trade_contract_size

Because account currency == base currency (USD), the target USD notional maps
DIRECTLY to base units.  NO FX conversion price is required for
notional->units on this contract.

## Verification

Tick-value cross-check: contract_size x tick_size / reference_price =
0.626731 vs observed trade_tick_value
0.626731 — consistent (reference ask
159.558 at 2026-08-18T18:22:00Z).

## Causality

Instrument spec observed at 2026-08-18T18:22:00Z (frozen); account equity
snapshot at the same observation; entry-side conversion is used for any
later price-dependent step.  No future price, no stale conversion.

## Margin note

Margin / buying-power semantics (leverage 500,
margin_mode 2, margin currency
USD) are COLLECTED METADATA only — margin feasibility is
D1.3, not D1.2B.
