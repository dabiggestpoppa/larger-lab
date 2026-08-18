# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Quantity-Formula Contract

## The proven chain (1R -> notional)

    admitted_f_pct        (from H1 causal admission; A 0.70, B 0.30)
    one_R_budget_usd   = equity_at_admission x admitted_f_pct / 100
    target_notional_usd = one_R_budget_usd / (RISK_UNIT_BPS / 10000)

    RISK_UNIT_BPS / 10000 = 0.00244949
    1 / (RISK_UNIT_BPS / 10000) = 408.2483  (USD of notional per USD of 1R budget)

## Proof from the sealed construction (why this formula, not pos)
The sealed contract is account_return = r x f with r = net_bps / 1R_bps.
For a position of notional N on USDJPY:  dollar PnL = N x (price move in bps)/1e4.
A 1R price move is 24.4949 bps.  For that move to produce f x equity:

    N x 24.4949/10000 = f x E   ->   N = E x f / (24.4949/10000)   (proven)

The research pos = TARGET_VOL/rv is the R-normalization device (so 1R is
comparable across volatility regimes); executing pos would make 1R worth only
0.245% of equity, violating the sealed f contract.  The
formula above is the unique notional realizing account% = r x f.

## Per-event multipliers under the preferred research default (f_total 1.00%, A1_70_30)
| state | requested_f | notional / equity |
|---|---|---|
| A alone | 0.70 | 2.8577 |
| B alone | 0.30 | 1.2247 |
| A + B | 1.00 | 4.0825 |
| B + B | 0.60 | 2.4495 |
| B + B + B | 0.90 | 3.6742 |
| A + A | 1.40 requested -> second A REJECTED by H1 | -- |

## Instrument-native move unit
For USDJPY: 1R = 24.4949 bps of price return = 0.002449 fractional move
~= 0.4 pips at 150.00 (quote-side).  Broker tick/pip
conventions must be mapped per broker spec (MISSING until broker chosen).

## Interface (DESIGN ONLY -- not built)

    translate_allocation_to_quantity(event, admitted_f_pct, account_state,
                                     instrument_spec, market_snapshot)
      -> equity_reference, admitted_f_pct, one_R_budget_account_ccy,
         one_R_move_native, target_notional_account_ccy, target_notional_native,
         raw_quantity, rounded_quantity, rounded_notional,
         realized_one_R_budget, realized_f_pct, rounding_error_pct,
         margin_required, buying_power_after, translation_status, block_reason
