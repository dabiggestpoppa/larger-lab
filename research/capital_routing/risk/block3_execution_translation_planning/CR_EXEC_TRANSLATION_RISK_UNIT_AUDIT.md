# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Risk-Unit Audit (1R)

## Definition (frozen, from phase_r4_common.py / phase_r1_ledger.py)

    1R = TARGET_VOL x sqrt(HOLD) = 24.49489742783178 bps
        TARGET_VOL = 10.0 bps/hour (Phase 7.5 vol-normalization target)
        HOLD       = 6.0 hours (fixed sealed hold)

1R is the one-sigma move of the VOL-NORMALIZED position over the full hold:

    PnL_sigma = pos x rv x sqrt(hold) = TARGET_VOL x sqrt(hold) = 24.4949 bps

It is an EXPECTED-MOVE / NORMALIZED unit -- **NOT a stop-loss distance, not a
maximum loss, not a broker stop**.  Historical losses materially exceed -1R:
worst A -3.66R (-89.5 bps), worst B -3.31R
(-81.2 bps).

## Economic meaning
The sealed account contract is:

    account_return ~= r_multiple x f

where f = static account fraction per R.  A -1R event at f = 1.00% costs about
-1% of equity; worst A at A weight 0.70 costs 0.70 x 3.66
= 2.56% of equity.

## Why the executed notional is NOT pos = TARGET_VOL/rv
pos is the research normalization device that makes R units comparable across
different volatility regimes.  Executing pos x equity would make a 1R move
cost only 0.245% of equity (the sigma of the normalized
position), NOT f.  The sealed f contract (account% = r x f) is the economic
definition; the notional that realizes it is derived in the quantity-formula
contract: N = E x f / (1R_bps/1e4).

## Fixture proof (first sealed ledger event, hand-calculated)
Event EUR_ORIGIN_202307101100 (family A, dir +1):
- entry 142.131 / exit 141.479 ->
  price_return_bps = ln(P_exit/P_entry) x 1e4 = -45.98
- pos = 0.4428  (rv = 10/pos bps/h)
- gross_pnl = dir x pos x price_return = -20.36 bps  (matches ledger)
- net = gross - cost 0.63 = -20.99 bps
- r_multiple = net / 1R = -20.9873 / 24.4949 = -0.8568  (matches ledger)
