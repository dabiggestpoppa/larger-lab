# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Protocol

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0
**Base:** 991d8126ae9822e3b5457000c560626ea590a3a0 (R1.1B provenance seal) · **Branch:** capital-routing
**Parent science:** Block III scale seal R1 (fail-closed) at `40d23712`
**Type:** PURE deterministic capital translation core (no broker/runtime code)

## Scope
Sealed capital decision + account binding input + event pos_t ->
EconomicExposureTarget, using the R1-corrected formula:

    one_R_budget_account_ccy    = E x admitted_f_pct / 100
    target_notional_account_ccy = E x (admitted_f_pct/100) x pos_t x 1e4 / RISK
    one_R_price_move_bps        = RISK / pos_t                (event-specific)

Provenance: gross exposure parity (translated account gross return ==
admitted_f x pos x price_ret / RISK) was proven at machine precision over all
826 accepted events in R1 (00bef1b5); D0 re-proves it through the actual
pure core on the full 890-event ledger.

## Boundary (this checkpoint does NOT own)
broker connections, runtime supervision, MT5/TradeLocker, generic
reconciliation, account registry, orders/fills, margin/buying power -> those
belong to execution-runtime-foundation. Capital Translation Core NEVER
recomputes H1, family, or model heat (immutable upstream CapitalDecision).
No dynamic sizing, no Kelly, no DD adaptation, no clipping of pos/notional.

## Frozen science (untouched)
890 events (A 432 / B 458); A1_70_30 + H1-1.00-REJ admission: 826 ACCEPT_FULL
(A 371 / B 455) / 64 REJECT_HEAT_CAP; requested_f A 0.70 / B 0.30; f_total
1.00%; 1R = 24.49489742783178 bps = NORMALIZED EXPECTED-MOVE UNIT, NOT a hard
stop / max loss / broker stop.

## Pass gate
admission parity preserved · rejected -> NO_EXPOSURE zero exposure · gross
parity machine precision · research net parity · idempotency · fail-closed
validation · no broker fields · no broker execution · science unchanged.
