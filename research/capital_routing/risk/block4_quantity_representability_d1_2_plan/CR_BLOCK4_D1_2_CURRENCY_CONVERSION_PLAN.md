# CR-BLOCK4-D1.2 CURRENCY CONVERSION PLAN

## Research vs executable

- research reporting currency: USD
- executable account currency: UNRESOLVED_UNTIL_ACCOUNT_BINDING
- research instrument: USDJPY (FX pair, base USD / quote JPY)

## Quantity semantics (USDJPY, USD account)

- The EconomicTarget account-currency notional must be mapped to native
  instrument quantity using broker contract semantics — conversion is NOT
  assumed trivial even for USD accounts.
- Required causal conversion price(s): entry-side price at translation time
  for notional -> units; margin-currency conversion deferred to D1.3.
- No future price, no stale fixed conversion unless explicitly a labeled
  scenario fixture.

## Long / short

Symmetry is CHECKED against the instrument contract, not assumed.  If
asymmetric, side-specific conversion is preserved.

## States

CURRENCY_CONVERSION_UNRESOLVED while the causal conversion source is unknown;
ACCOUNT_CURRENCY_UNRESOLVED until account binding.
