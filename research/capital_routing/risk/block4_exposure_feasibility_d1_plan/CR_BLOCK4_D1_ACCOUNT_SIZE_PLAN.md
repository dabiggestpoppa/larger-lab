# CR-BLOCK4-D1 ACCOUNT SIZE PLAN

## Principle

- Ideal economic target multiples (`target_notional / equity`) are account-size
  INVARIANT.
- Quantity discretization (lot min/step, absolute limits, absolute margin) is
  account-size DEPENDENT.
- An account size is never selected because it improves performance.

## Scenarios

- Use ACTUAL intended account sizes first (truth class per size).
- A small illustrative grid may be added only if useful, each entry labeled with
  its truth class.
- Do not optimize f by account size; f_total remains frozen at 1.0%.

## Matrix to build in D1.2 (after instrument truth)

Per account size and family: one-R budget, median/p95/p99/max target notional,
median/p95/max notional/equity, historical worst observed account impact.
