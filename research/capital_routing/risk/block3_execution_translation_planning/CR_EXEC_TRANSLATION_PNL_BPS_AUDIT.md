# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- pnl_bps Audit

## Exact construction (frozen, phase_r1_ledger.py)

    mkt_bps      = dir x (ln P_exit - ln P_entry) x 1e4
    pos          = TARGET_VOL / rv                 (rv = entry-window hourly vol)
    gross_pnl    = mkt_bps x pos
    net (pnl_bps)= gross_pnl - cost_bps x pos      (cost = 2 x one-way spread/comm + signed swap)
    r_multiple   = pnl_bps / 1R

Answers to the audit questions:

| question | answer |
|---|---|
| return on gross instrument notional? | NO -- bps of a vol-normalized position (pos = 10/rv) |
| direction already applied? | YES -- dir multiplies the return before PnL |
| transaction costs deducted? | YES -- in pnl_bps (net) and cost_pnl_bps |
| commissions included? | YES -- one-way USDJPY 0.6 bps, round trip 1.2 bps (phase_7_families.ONE_WAY_COST_BPS) |
| spread included? | YES -- same one-way cost bundle |
| slippage included? | NO -- not modeled; recorded for the cost-parity plan |
| 6h hold always fixed? | YES -- hold_h = 6 for every sealed event |
| entry-to-exit percentage return? | YES -- log return x 1e4 over [entry, exit] window |
| long/short symmetric in construction? | YES -- dir x return; cost applied identically |
| economic PnL reconstructible from entry/exit/direction/notional? | YES -- see fixtures below |

## Hand-calculated fixture 1 (verified against the ledger)
See Risk-Unit Audit fixture: entry 142.131 -> exit 141.479,
dir +1, pos 0.4428: gross -20.36 bps,
net -20.99 bps, r -0.8568.  All match the frozen ledger.

## Fixture 2 (synthetic long/short symmetry)
- Long USDJPY 150.000 -> 150.100 (dir +1, pos 1.0): mkt = ln(150.1/150) x 1e4 =
  +6.66 bps -> gross +6.66 bps; net = +6.66 - 1.2 - swap = +5.46 bps (no swap).
- Short USDJPY 150.100 -> 150.000 (dir -1, pos 1.0): mkt = -6.66 bps -> gross
  +6.66 bps -> same net.  Symmetric by construction.

## Cost contract for translation (see cost-parity plan)
Research modeled cost = 2 x 0.6 bps (spread+commission) + signed swap.
Broker execution must NOT re-charge these on top (no double charge) and must
record any ADDITIONAL execution slippage as a separate observed-cost line.
Fixed per-order fees would violate pure linear notional scaling -- flag them.
