# CR-BLOCK4-D1 CURRENCY CONVERSION PLAN

## Research vs executable currency

- research reporting currency: USD (frozen, pair-base evidence)
- executable account currency: UNRESOLVED_UNTIL_ACCOUNT_BINDING
- research instrument: USDJPY (FX pair)

## Causal conversion contract

If account currency / contract currency / margin currency differ, the required
conversion price must be a CAUSAL price (no future price, no stale fixed
conversion unless explicitly a labeled scenario fixture):

- PnL conversion, notional conversion and margin conversion each use their own
  causal price at the relevant timestamp.
- `CURRENCY_CONVERSION_UNRESOLVED` is the honest state while the account
  currency is unresolved.

## Non-account-currency instruments

Design (not implement) conversion via causal prices; never force everything to
USD if the executable environment differs.
