# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Cost-Scaling Audit

## Research cost construction (proven from source + fixtures)
cost_pnl_bps = cost_bps x pos_t, where cost_bps = 2 x one-way spread/comm +
signed swap (phase_7_families: USDJPY one-way 0.6 bps -> 1.2 round trip; swap
varies per event). Fixture: event EUR_ORIGIN_202307101100, pos
0.4428, cost_bps 1.4226 ->
cost_pnl_bps 0.6299 (matches ledger).

So the research cost is per POSITION-UNIT, i.e. it scales with pos_t -- NOT a
flat 1.2 bps against raw live notional.

## What broker cost must be for net parity
Executed net account return = (N/E) x (price_ret - broker_cost_bps)/1e4.
With N/E = f x pos x 1e4/RISK, parity with f x r requires
**broker_cost_bps = cost_bps (the event-specific per-unit research cost)**.
Research-modeled net parity (using the frozen cost_bps): max |error| =
6.94e-18 -> PROVEN.
Execution-level net parity: BROKER_DEPENDENT_UNRESOLVED until the broker cost
model is frozen (spread/commission/swap/slippage are broker-specific).

## Rules
- No double charging (research cost already in pnl_bps; execution reports
  broker/actual cost as deltas).
- Any fixed per-order fee violates pure linear (bps) scaling -- flag as
  NON_LINEAR_COST.
- Slippage was NOT in research; record as observed extra cost, never back-filled.
