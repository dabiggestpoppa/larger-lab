# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Protocol

**Repo:** dabiggestpoppa/larger-lab · **Branch:** capital-routing
**Base:** 5a79bf2323ac2657de74e3efa7c4a29d8715db33 (execution-translation planning -- MOSTLY COMPLETE, NOT implementation-safe)
**Parent scientific seal:** 40d237123ac2b709cc0ebce1d7f057bbfde25dab (Block III scale science FULLY SEALED -- DO NOT REOPEN)
**Type:** TRUTH REPAIR -- corrects the 1R->notional derivation, pip semantics,
account-impact units, account/product truth, and freezes the Account Control
Plane boundary. NO broker execution.

## Blocking defect (confirmed independently from sealed source)
The prior planning commit derived  N = E x f x 1e4/RISK  without the event
position term pos_t. The sealed construction (phase_r1_ledger.py) is
gross_pnl_bps = dir x pos_t x price_return_bps with pos_t = TARGET_VOL/rv_t,
so the corrected relationship (proven here at machine precision over all 890
events) is:

    N_t = Equity_t x admitted_f_decimal x pos_t x 10,000 / RISK_UNIT_BPS

and the underlying one-R PRICE move is event-specific:

    one_R_price_move_bps_t = RISK_UNIT_BPS / pos_t

## Frozen science (untouched)
890 events (A 432 / B 458); admission under A1_70_30 + H1-1.00-REJ:
826 ACCEPT_FULL (A 371 / B 455) and
64 REJECT_HEAT_CAP. requested_f A 0.70 / B 0.30;
f_total 1.00%; 1R = 24.4949 bps (expected-move unit, NOT a
hard stop). No alpha/allocation/H1/f_total/1R/cost/entry-exit change. No
clipping of pos/notional/leverage (that would be new science).

## No-go
Broker execution, MT5/TradeLocker calls, order placement, live capital,
Kelly, DD adaptation, risk optimization, cross-branch pushes (tb-forward-engine /
execution-runtime-foundation are READ-ONLY).

## Pass gate
1 pos_t proven part of live exposure parity  2 corrected formula derived from
source truth  3 gross parity on all accepted events  4 rejected events -> zero
exposure  5 one-R price move event-specific  6 pip semantics corrected
7 account-impact units corrected  8 unresolved account/product fields truthful
9 Account Control Plane boundary explicit  10 CR claims no generic broker
runtime  11 TB Forward acknowledged as engineering reference
12 execution-runtime-foundation = future generic execution dependency
13 Block III science unchanged  14 no broker execution.
