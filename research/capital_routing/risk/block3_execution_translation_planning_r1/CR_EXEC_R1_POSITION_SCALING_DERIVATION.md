# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Position-Scaling Derivation

## Sealed source chain (phase_r1_ledger.py + R1_EVENT_RISK_LEDGER.csv)
    mkt_bps_i      = dir_i x (ln P_exit - ln P_entry) x 1e4
    pos_i          = TARGET_VOL / rv_i                     (TARGET_VOL = 10.0)
    gross_pnl_bps  = mkt_bps_i x pos_i
    cost_pnl_bps   = cost_bps_i x pos_i                    (cost per position-unit)
    net_pnl_bps    = gross - cost_pnl_bps
    r_R            = net_pnl_bps / RISK_UNIT_BPS
    account_return = admitted_f_decimal x r_R

## Gross exposure parity (the proof)
Executed position of notional N_t on USDJPY (return in bps):
    account gross return = (N_t / Equity_t) x price_return_bps / 1e4.
Research gross account return = admitted_f x pos_t x price_return_bps / RISK.
Setting them equal and cancelling price_return_bps:

    N_t / Equity_t  =  admitted_f_decimal x pos_t x 10,000 / RISK_UNIT_BPS

=>  **N_t = Equity_t x admitted_f_decimal x pos_t x 10,000 / RISK_UNIT_BPS**

Verified: max |error| = 6.94e-18 across all
826 accepted events (machine precision). The old fixed formula
(max error 0.044900) is REJECTED.

## One-R underlying price move (event-specific)
1R PnL = pos_t x one_R_price_move_bps  =>  **one_R_price_move_bps_t = RISK / pos_t**.
Accepted-event distribution (bps): min 1.35,
p1 4.23, median 22.11,
p95 69.37, max 221.91.

## Position distribution (sealed ledger, all 890 events)
Pooled: min 0.110383, p1 0.208103,
p5 0.355539, p25 0.708625,
median 1.10902, p75 1.710361,
p95 3.6247, p99 5.73355,
max 18.187813.
A: median 1.179898, max 11.465802.
B: median 1.043367, max 18.187813.

## Corrected notional / equity (accepted events, equity-normalized)
Pooled: median 1.984x, p95
7.61x, p99
16.04x, max
32.77x.
A: median 3.351x, max 32.77x.
B: median 1.285x, max 22.28x.

## NO CLIPPING
pos / notional / leverage / exposure are NOT capped in this repair. Extreme
values are classified for later feasibility study
(EXECUTABLE_AS_IS / MARGIN_INFEASIBLE / BROKER_MAX_SIZE_INFEASIBLE /
MINIMUM_SIZE_INFEASIBLE / LEVERAGE_LIMIT_INFEASIBLE). A clipping rule would be
NEW SCIENCE (candidate: CR-RISK-BLOCK-IV-EXPOSURE-FEASIBILITY-AND-CLIPPING-STUDY,
NOT started).
