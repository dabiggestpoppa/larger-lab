# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Core Module Contract

## Module
`src/capital_routing/translation/capital_translation_core.py` (version
D0-1, science R1.1)

## Inputs (immutable, frozen contracts)
| component | key fields |
|---|---|
| A_StrategyEventReference | event_id, strategy_id, family (A|B, upstream), direction (LONG|SHORT, upstream), instrument_research_identity (USDJPY), entry_known_timestamp, pos_t, risk_unit_bps, translation_science_version |
| B_CapitalDecisionReference | decision_id, policy_id, requested_f_pct, admitted_f_pct, status (ACCEPT_FULL|REJECT_HEAT_CAP), model_heat_before, model_heat_after, decision_timestamp, configuration_hash |
| C_AccountBindingReference | account_id, portfolio_group_id (ONE shared A+B portfolio master), account_role |
| D_BoundAccountSnapshot | account_id, account_currency, equity_at_admission (FROZEN snapshot), observed_at, staleness_status (FRESH|STALE|UNKNOWN), profile_config_hash |

## Output (EconomicExposureTarget — pure; NO broker fields)
event_id, account_id, strategy_id, family, direction, research_instrument,
admitted_f_pct, pos_t, risk_unit_bps, equity_reference, account_currency,
one_R_budget_account_ccy, target_notional_account_ccy, one_R_price_move_bps,
capital_policy_id, translation_version, known_time, status
(ECONOMIC_TARGET|NO_EXPOSURE), translation_id (idempotency key).

## Behavior
- REJECT_HEAT_CAP -> NO_EXPOSURE: zero budget / zero notional / zero price
  move, WITHOUT independently reconsidering H1.
- Fail-closed errors: StaleAccountStateError (snapshot not FRESH),
  UnknownInstrumentSpecError (not in sealed universe), AccountBindingMismatchError,
  MissingAccountEquityError, UnresolvedAccountCurrencyError, InvalidPositionError,
  InvalidDecisionStatusError.
- Pure/deterministic/idempotent: identical inputs -> identical output;
  translation_id = sha256(event_id | decision_id | policy_id |
  configuration_hash | translation_version). Equity is consumed ONLY from the
  frozen snapshot: no internal state, no revaluation of opened events, no
  dynamic resizing (that would be new science).
