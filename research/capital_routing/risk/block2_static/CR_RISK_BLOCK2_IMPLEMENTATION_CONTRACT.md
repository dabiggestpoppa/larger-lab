# CR-RISK-BLOCK2-STATIC-ARCHITECTURE — Implementation Contract

## Module
`src/capital_routing/static_risk_architecture.py`

## Typed / static portfolio-risk contract
Per candidate event, required inputs:
- event_id
- family
- timestamp (entry)
- direction
- base_risk_fraction (base_f)
- active_positions (derived from prior admitted events)
- active_gross_heat
- family_active_heat

Required output: ADMIT / SCALE / REJECT.

The default architecture prefers simple deterministic behavior: H0
(unconstrained) and H1 (gross cap with REJECT, optionally SCALE) are the
canonical primitives. No episode-memory state, no drawdown state.

## The module MUST NOT
- calculate alpha
- change entries or exits
- perform broker execution
- calculate Kelly
- inspect future episode membership
- adapt to drawdown
- adapt to previous PnL

## Causal admission rule
At event time t, known: family, direction, configured family allocation,
configured total risk, currently active positions, currently active gross
heat. Unknown / forbidden: future events, future episode membership, future
returns, future DD path.
