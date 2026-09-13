# RECURSIVE GEOMETRY REPORT (Workstream G)

## Question

Does the same expansion geometry appear at multiple scales — asset, sector, chain,
rank band, whole market — and does it recur across cycles? Form-matching, not
token-matching.

## Method

Daily market states (from MECH-1 routing anatomy + MECH-2 state definitions) are
compressed into 3-day state triples (motifs). 201 motifs total across 2,196 days.
Each motif is classified RECURRING (≥3 occurrences in ≥4 of 5 fixed subperiods),
PARTIALLY_RECURRING (≥3 in 2-3 subperiods), or CYCLE_SPECIFIC (otherwise).
Full catalog: `12_MORPHISM_CATALOG.{json,csv}`.

## Findings

| classification | motifs | share |
|---|---|---|
| RECURRING | 32 | 15.9% |
| PARTIALLY_RECURRING | 27 | 13.4% |
| CYCLE_SPECIFIC | 142 | 70.6% |

### The dominant recurring geometry is PERSISTENCE (self-loop), at every scale

1. **Market-level self-loop** — `MIXED→MIXED→MIXED` (459 occurrences, 5/5 subperiods):
   the market spends most of its time in a no-clear-route state.
2. **Concentration self-loop** — `BTC_CONCENTRATION→BTC_CONCENTRATION→BTC_CONCENTRATION`
   (364, 5/5): concentration is a persistent attractor, strongest in 2023/2025-2026.
3. **Broad risk-on self-loop** — `BROAD_RISK_EXPANSION³` (145, 5/5): broad expansion
   clusters in 2020-2021 (65) and is rare after 2022.
4. **Parking self-loop** — `STABLECOIN_PARKING³` (99, 3/5; 70 in 2020-2021): parking
   was a 2020-2021 phenomenon, partially returning in 2025-2026.
5. **Exit self-loop** — `CAPITAL_EXIT³` (69, 2/5; 47 in 2022): true capital flight is
   almost exclusively 2022 + 2025-2026 episodes.
6. **Sector-scale geometry** — sector leader-first episodes repeat recursively inside
   sectors (MECH-1: 55k episodes; MECH-2 workstream D: 6,783 with tracked peers;
   median same-day peer corr 0.29, delayed corr ≈ 0): *leader→same-day peer
   confirmation*, not leader→1-day-later spread.

### Cross-scale self-similarity test

The **same geometry — a persistent state that must be exited by an outside impulse —
appears at band level (MECH-1: band persistence, 37% 14-day reversal), sector level
(leader-first with contemporaneous breadth confirmation), and market level (the
self-loop motifs above)**. Self-similarity is therefore *partially supported*:
persistence-plus-exogenous-break is the recurring form. What does NOT repeat
self-similarly is the *sequence* (e.g. expansion→concentration→exit): the only
multi-state transitions that recur across ≥4 subperiods are two-step loops into or
out of BTC_CONCENTRATION (`MIXED→BTC_CONC→BTC_CONC`, `BTC_CONC→BTC_CONC→MIXED`,
`BTC_CONC→MIXED→MIXED`, each 5/5 subperiods), i.e. concentration is the pivot.

### Cycle-specificity

71% of motifs are cycle-specific — the *names* of the leaders and the specific
alt-rotation routes are not stable. The stable objects are the *states* (especially
concentration and mixed), not the tokens or routes.

## Limitations

- Motifs are descriptive 3-day compression; they describe recurrence of state, not of
  capital amounts.
- Subperiod partition is fixed (2020-21 / 2022 / 2023 / 2024 / 2025-26) and coarse;
  within-cycle seasonality is not modeled.
