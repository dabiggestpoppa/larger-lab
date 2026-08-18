# CR-BLOCK4-D1 QUANTITY TRANSLATION PLAN

## Lane B / D: economic notional -> raw quantity -> representable quantity

Generic contract (designed in D1, implemented only in D1.2+ after instrument
spec truth is frozen):

    raw_quantity = target_notional_account_ccy / price_account_ccy_per_unit

- price semantics: causal entry-side price, frozen source (see currency plan)
- units: account-currency notional / account-currency price per unit
- representable_quantity = raw_quantity rounded per frozen policy
- actual_notional = representable_quantity x price
- exposure_ratio and relative_exposure_error computed from actual vs target

## Product-type awareness

No single generic formula is assumed valid for every product. Product-specific
contracts are required per product type (spot FX / CFD / future / etc.); the
research instrument USDJPY's broker representation is unresolved until binding.

## Fail states

- target below min quantity  -> MIN_QUANTITY_BLOCKED (default; no auto round-up)
- target above max quantity -> MAX_QUANTITY_BLOCKED (default; no silent clipping)
- missing spec field -> *_UNRESOLVED / MISSING_REQUIRED_EXECUTION_TRUTH

## Unit safety

Quantity math must be unit-safe and covered by unit tests (e.g. bps/10000,
ccy per unit, lot vs base units) — never mixed silently.
