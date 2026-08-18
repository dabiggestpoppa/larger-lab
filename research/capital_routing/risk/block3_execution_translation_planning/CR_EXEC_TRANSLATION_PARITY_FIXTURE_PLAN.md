# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- 890-Event Parity Fixture Plan

## Parity requirement
The future engine must demonstrate that, BEFORE rounding/margin effects, the
execution translation layer preserves the sealed research admission on the
exact 890 events:
- family assignments unchanged (A 432 / B 458)
- requested_f unchanged (A 0.70, B 0.30)
- H1 decisions unchanged ({'ACCEPT_FULL': 826, 'REJECT_HEAT_CAP': 64})
- event ordering unchanged (chronological, deterministic)
- accepted/rejected event set unchanged (826 accepted: A 371
  + B 455; 64 rejected)

This becomes a regression fixture (golden CSV of per-event admission), locked
before any execution code is written.

## Hand-calculated unit fixtures (design)
simple long / simple short / fractional-share product / whole-share-only
product / futures contract / non-account-currency instrument / minimum-
quantity rejection / rounding-down case / margin-blocked case / A+B
concurrency / A+A rejection / three-B concurrency.  Synthetic fixtures may
test generic mechanics but may NOT replace actual product validation on the
real USDJPY contract (once a broker is selected).
