# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Defect Audit

## Defect 1 -- notional formula omitted pos_t (CONFIRMED)
Old planning formula:  target_notional = E x f x 1e4 / RISK  (no pos).
Verified failure: max |translated - research| gross account return error over
accepted events = **0.044900** (up to ~4.5pp of
account return per event); only exact for pos = 1.
Corrected formula (proven): N = E x f x pos_t x 1e4 / RISK -- gross parity max
error **6.94e-18** (machine precision).

## Defect 2 -- fixed 24.4949 bps price move (CONFIRMED WRONG)
1R is a NORMALIZED PnL unit: 1R PnL = pos_t x price_move_bps, so the underlying
price move for +1R is RISK/pos_t -- event-specific. Across accepted events:
min 1.35 bps, median
22.11 bps, max
221.91 bps. The old statement
"a 1R USDJPY price move is always 24.4949 bps" is REMOVED.

## Defect 3 -- account-impact units 100x (CONFIRMED)
Old matrix reported A worst 255.88 / B 99.39 under *_account_impact_pct. Sealed
semantics: account impact % = r_multiple x admitted_f_pct. Corrected:
A worst -3.6554 x 0.70% = **-2.5588%**;
B worst -3.3130 x 0.30% = **-0.9939%**
(signed; renamed historical_worst_observed_account_impact_pct; never
"maximum possible loss").

## Defect 4 -- account currency truth
research_reporting_currency = USD (sealed pair base) is distinct from
executable_account_currency = UNRESOLVED_UNTIL_ACCOUNT_BINDING. The prior
decision marked account_currency_resolved = true -- repaired.

## Defect 5 -- product identity truth
research_instrument = USDJPY (class FX_PAIR) is distinct from broker
product type / symbol / contract / margin (UNRESOLVED until account binding).

## Cost scaling (re-audited, see cost-scaling audit)
cost_pnl_bps = cost_bps x pos_t (per-position-unit cost), NOT a flat 1.2 bps
against raw notional. Net parity with the frozen research cost is proven;
execution-level net parity remains broker-dependent.
