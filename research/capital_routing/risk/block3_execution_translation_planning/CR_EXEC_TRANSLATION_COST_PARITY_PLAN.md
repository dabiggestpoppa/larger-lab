# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Cost-Parity Plan

## Research modeled cost (frozen)
- One-way USDJPY spread+commission = 0.6 bps (phase_7_families.ONE_WAY_COST_BPS).
- Round trip = 1.2 bps, charged at entry, plus signed swap (proxy policy-rate
  differential, phase_7_families swap table).
- pnl_bps in the sealed ledger is NET of this modeled cost.

## Three cost lines (future engine)
1. research_modeled_cost   -- the 1.2 bps + swap above (already in pnl_bps).
2. broker_estimated_cost   -- broker spread/commission model at translation time.
3. actual_execution_cost   -- realized fills, recorded after the fact.

## Rules
- No double charging: executed PnL accounting must use research_modeled_cost
  for parity and report broker/actual cost as deltas, not add both to the
  research PnL.
- No ignoring: if the broker cannot deliver the modeled 1.2 bps round trip,
  the delta is a translation cost-drift line item.
- Notional scaling: the modeled cost is linear in notional (bps).  ANY fixed
  per-order fee (e.g. $/lot flat commissions) violates pure linear scaling and
  must be flagged as NON_LINEAR_COST in the cost ledger.
- Slippage was NOT in research: any execution slippage is an observed extra
  cost, never back-filled into the sealed pnl_bps.
