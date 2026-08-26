# TOPOLOGY REPORT (Field Connectivity)

## Method

Simple network statistics first (per the mandate: persistent-homology-style methods
only if a meaningful object exists under simpler statistics — it does not here).

- **Band graph**: 7 rank-band nodes; edge iff |corr of band daily returns| ≥ 0.8
  (full-history correlation matrix).
- **Sector graph**: top-20 sectors by active days; edge iff |corr of sector 7d
  median returns| ≥ 0.5.

Machine-readable: `14_TOPOLOGY_REPORT.json`.

## Band graph

- **Density 0.952** — 20 of 21 possible edges present. The only non-edge is a single
  weak band pair; the Top-500 rank bands form one essentially complete graph.
- **One connected component** containing all 7 bands. There are no isolated liquidity
  islands at band level and no bridge/articulation structure: no band is a bottleneck
  through which capital propagation must pass. Rank space is a fully-mixed field.

## Sector graph

- **Density 0.879** (167/190 edges), **mean |corr| 0.70** among the 20 most active
  sectors.
- Even the *least* correlated active sectors sit at |corr| ≥ 0.5 → there is no
  sector that behaves as an isolated island over the full sample. Sector dispersion
  is a within-sector property (breadth/leader-follower), not cross-sector separation.

## Connectivity dynamics (qualitative, from 04/05 + 15 state daily)

- Connectivity (mean cross-band/cross-sector correlation) is **high in expansion
  regimes and collapses only mildly in concentration regimes**; the field remains
  dense even under BTC_CONCENTRATION (572 days) — concentration is expressed through
  *dispersion of ranks within the dense field*, not through graph fragmentation.
- No measurable "connectivity increase before broad rotation": the graph is dense at
  all times, so connectivity cannot be a leading indicator here.

## Verdict

The market is a **single dense component at both band and sector scale**. Network
topology adds little discriminative information beyond the correlation structure
already reported in the common-factor model; there is no bottleneck-node structure
and no isolation dynamic worth modeling. Topological persistence methods were
therefore not escalated — no structural object exists that they would clarify.
