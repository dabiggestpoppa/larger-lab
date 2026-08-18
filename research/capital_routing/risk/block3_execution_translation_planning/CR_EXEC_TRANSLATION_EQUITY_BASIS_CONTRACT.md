# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Equity-Basis Contract

## Frozen choice (scientific expectation)
**equity_source: CURRENT ACCOUNT EQUITY AT CAUSAL ADMISSION TIME**

The sealed research model compounds account return multiplicatively per event
(E_{t+1} = E_t x (1 + f x r_t)); the correct dollar base is the equity at the
moment the event is admitted, not start-of-day, not a static baseline.

## Contract fields
| field | value |
|---|---|
| equity_source | current account equity at causal admission (NAV of owned resources) |
| equity_timestamp | same decision_time as the H1 admission decision (known-time, no future state) |
| currency | account currency (repository truth: USD proposed -- pair base; see account-currency section) |
| staleness tolerance | equity older than a frozen threshold (e.g. 5 min for an FX account) -> STALE_ACCOUNT_STATE, fail closed |
| behavior if unavailable | NO_ACCOUNT_STATE / STALE_ACCOUNT_STATE -> block new admission |

## Critical active-heat continuity
For an OPEN event, freeze at admission:
event_id, family, requested_f_pct, admitted_f_pct, equity_at_admission,
initial_r_budget_usd, initial_target_notional, actual_quantity.

Do NOT dynamically resize an open position because account equity moves
afterward, and do NOT mark-to-market admitted_f.  Future H1 decisions use the
SEALED admitted heat-unit state of active events (admission is a contract
snapshot, not a revaluation).  Any dynamic heat revaluation is new science and
is NOT authorized.

## Account currency
- Repository truth: the sealed universe is 100% USDJPY; PnL is expressed in
  bps; there is no explicit account-currency field in the sealed artifacts.
- Proposal (scientific expectation): account currency = USD (the pair base).
  Recorded as PROPOSED, not frozen, until the executable environment is known.
- For non-account-currency instruments: design PnL/notional/margin conversion
  using CAUSAL prices only (future engine contract; no such instrument exists
  in the sealed universe today).
