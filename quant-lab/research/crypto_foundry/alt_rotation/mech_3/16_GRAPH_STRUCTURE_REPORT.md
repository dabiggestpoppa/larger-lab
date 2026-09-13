# MECH-3 GRAPH STRUCTURE REPORT (WORKSTREAM K)

**Question:** Does the surviving chain-liquidity structure have stable clusters,
repeatable bridges, persistent components, bottleneck nodes, or isolated liquidity
islands — such that graph theory (and eventually topology) is EARNED?

## 1. Construction (preregistered §12)

- Nodes: top-12 chains by merged coverage (Tron, Ethereum, Solana, Arbitrum,
  Avalanche, Polygon, OP Mainnet, Bitcoin, Sui, Hyperliquid L1, PulseChain, Cronos).
- Edge (i,j) if |corr(vel7_i, vel7_j)| ≥ 0.50 over the full sample (vel7 = native
  median rank velocity 7D, PIT).
- Metrics: connected components (union-find), density, articulation points (Tarjan),
  component-membership persistence across the 5 fixed subperiods.

## 2. Full-sample graph

| Metric | Value |
|---|---|
| Nodes | 12 |
| Edges | 6 |
| Density | 0.091 |
| Mean \|corr\| | 0.218 |
| Connected components | 8 |
| Articulation points | Ethereum |

Components (full sample):

1. **{Ethereum, Arbitrum, Avalanche, Polygon, Solana}** — the one multi-chain cluster
2. {Tron}, {OP Mainnet}, {Bitcoin}, {Sui}, {Hyperliquid L1}, {PulseChain}, {Cronos} — 7 singletons

Interpretation: the chain-level connectivity graph is **sparse and star-like**.
Ethereum is the single articulation point joining Arbitrum/Avalanche/Polygon/Solana
to the rest. 7 of 12 chains are liquidity islands (no |r| ≥ 0.50 velocity link to any
other chain). Bitcoin is an island — its velocity does NOT co-move with the
chain-liquidity group at this threshold.

## 3. Subperiod persistence

| Subperiod | Components | Multi-node clusters |
|---|---|---|
| 2020-2021 | 10 | {Ethereum, Polygon, Tron} |
| 2022 | 12 | — (all singletons) |
| 2023 | 11 | {Bitcoin, Solana} |
| 2024 | 3 | {Arbitrum, Avalanche, Cronos, Ethereum, Hyperliquid, Polygon, PulseChain, Solana, Sui, Tron} |
| 2025-2026 | 7 | {Arbitrum, Avalanche, Bitcoin, Ethereum, Polygon, Solana} |

The **Ethereum–Polygon–Solana core persists**: the pair (Ethereum, Polygon)
co-clusters in 2020-21, 2024, and 2025-26 (3 of 5 subperiods); the 2024–25-26
cluster also consistently includes Arbitrum, Avalanche, Solana. 2022 is a total
fragmentation event (12/12 singletons), and 2024 is a near-total fusion
(1 cluster of 10). Connectivity itself is regime-dependent: it collapses in
bear/fragmentation regimes and fuses in expansion regimes.

## 4. Topology readiness verdict

**TOPOLOGY_EARNED = YES (conditional).**

- A persistent multi-chain component with ≥ 3 nodes exists and ≥ 2 of its members
  co-cluster in ≥ 3 of 5 subperiods (Ethereum–Polygon core) → cluster persistence
  criterion met.
- Graph density 0.091 < 0.90 → the graph is not trivially complete.
- Ethereum is a **repeatable bottleneck/bridge node** across the full sample and in
  every fused subperiod.
- Caveat: 2022 breaks all connectivity, so "persistent topology" is a regime-relative
  statement, not a constant of the field.

**Earned methods (in order):** connected components, articulation/bridge analysis,
cluster-persistence tracking. **Not yet earned:** persistent homology — the object
here is a small, sparse, regime-switching graph whose persistent structure is fully
described by the component/bridge statistics above; a filtration-based analysis
would add no resolution at this scale.

## 5. NEW_NODE / MERGE / DISSOLVE

- NEW_NODE: chain-level velocity graph with an Ethereum bottleneck and 7 liquidity
  islands (new structural fact, MECH-2 did not build this graph).
- DISSOLVE: any prior assumption of a densely connected chain field — density 0.09,
  most chains are islands.
- Observation limit: edges are velocity co-movement, not capital-flow edges; bridge
  data (actual liquidity routing) is UNOBSERVED, so "Ethereum bridge" here means
  co-movement bottleneck, not verified capital conduit.
