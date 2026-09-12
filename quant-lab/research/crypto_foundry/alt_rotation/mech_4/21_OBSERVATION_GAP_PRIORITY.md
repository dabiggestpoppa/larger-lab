# OBSERVATION-GAP PRIORITY MAP — MECH-4

## What the route-selection gap looks like after MECH-4

MECH-4 shows observables close part of the **escape-timing** gap but not the
**route-selection** gap:

| Phenomenon | Base R² | Extended R² | Net gain |
|---|---|---|---|
| CONCENTRATION_EXIT within 7D | 0.076 (MECH-3 8-var) | **0.195** (+ path memory/age/route/p1/interactions, WS 20) | **+0.12 (closed)** |
| ROUTING propagation (G3 outcome, held-out) | AUC 0.77 (M0 current-state logistic) | +path memory → AUC flat, log-loss worse | **NOT closed** |

So the currently-observed path/history variables improve *whether* the field exits
concentration, but do NOT explain *which route* (propagation vs not, or depth) it
takes (`HYSTERESIS_DESCRIPTIVE`, WS C). Route selection remains largely outside the
observation layer.

## Priority map (mechanistic relevance / PIT feasibility / historical availability /
likely incremental info / integration cost — each 1-5; priority = relevance + avail + info − cost)

| Sensor | Mech relevance | PIT feas | Hist avail | Likely info | Int cost | Priority | Notes |
|---|---|---|---|---|---|---|---|
| Perp OI / open interest | 5 | 3 | 2 | 4 | 2 | 8 | direct leverage-demand signal for ignition/depth |
| Perp funding rate | 5 | 3 | 2 | 3 | 2 | 7 | crowding/overlap of propagation |
| Per-chain stablecoin supply | 4 | 3 | 2 | 4 | 3 | 6 | decomposes the aggregated stablecoin coordinate |
| Bridge inflows/outflows | 4 | 2 | 1 | 4 | 3 | 4 | chain-hopping route selection |
| Exchange inflow/outflow | 4 | 2 | 1 | 4 | 2 | 5 | on/off-ramp directional signal |
| Active addresses / tx activity | 3 | 4 | 3 | 3 | 3 | 7 | usage vs price decoupling (activation coordinate) |
| Wallet-cohort / holder structure | 4 | 1 | 1 | 5 | 5 | 1 | highest info, lowest PIT feasibility (identity UNOBSERVED) |
| Lending / collateral TVL | 3 | 2 | 2 | 3 | 3 | 3 | leverage collateral channel |
| Venue depth / order-flow | 4 | 1 | 1 | 4 | 4 | 1 | execution microstructure (mostly UNOBSERVED) |
| Staking flows | 2 | 2 | 2 | 2 | 3 | 1 | marginal for route selection |

## Explicitly UNOBSERVED (documented, never filled with narrative)

- Private OTC / treasury flows, hidden market-maker inventory, incomplete wallet
  identity, unpublished institutional positioning, most venue depth.
- **Participant intent** (accumulation vs distribution) is unobservable with current
  data; only an ACCUMULATION-LIKE observable fingerprint is tested (34), and intent
  interpretation is explicitly NOT claimed.

## Ranking conclusion

The single highest-priority additions for route selection are **per-ecosystem
stablecoin supply + perp OI/funding + active-address counts** (feasible PIT,
directly target the activation/ignition/depth questions). Wallet-cohort and venue
order-flow are highest-info but currently PIT-infeasible / heavily UNOBSERVED and
rank below the feasible sensors. No claim that adding these will close the gap —
that must be empirically tested (per constitution).