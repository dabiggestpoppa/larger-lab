# MECH-2 SUMMARY — CONDITIONAL PROPAGATION, CAUSAL HIERARCHY & FIELD GEOMETRY

Terrain research only. No strategy, no PnL, no optimization, no deployment.
Parent: MECH-1 `b3083df1` (PASS_ALT_MECHANISM_ANATOMY).

## 1. What structures survived

- **Chain-liquidity → native-asset hierarchy (SUPPORTED, L3).** 77/258 chain-flow
  cells survive FDR q<0.05. TVL→stablecoin, TVL→DEX, and velocity→native-improvement
  links are positive across chains; chain TVL carries incremental transfer-entropy
  about native asset improvement (p=0.005, J). The propagation pathway
  `chain TVL → native token / velocity → breadth` is the checkpoint's cleanest
  empirical structure.
- **Conditional (state-dependent) lead/lag (SUPPORTED, L2).** 151 state-conditioned
  cells; the signature example: band 51-100 rank velocity leads 101-200 by 1 day
  under BTC_DOWN (corr +0.64) and VOL_HIGH (+0.67), while the unconditional pair is
  *oppositely signed* (−0.30). Regime conditioning flips the propagation direction.
- **Rank-migration precursors (WEAK, L1).** Success rates 0.46–0.51 across bands —
  barely above coin-flip; event vs control differences are small (e.g. win7 rank
  velocity events +2.9 vs controls −1.2 for 101-200). Migration is weakly
  pre-signaled; the pre-migration signature is modestly positive relative return and
  positive rank velocity in mid bands.
- **Leader-first sector propagation (SUPPORTED at same-day, L1).** 6,783 episodes
  with tracked peers; median same-day peer corr 0.29, delayed corr ≈ 0. Leaders are
  identified at episode start and peers confirm **contemporaneously** — there is no
  measurable 1-day+ delayed spread within sectors.
- **Persistence geometry (SUPPORTED, L1).** Concentration and mixed states are
  near-absorbing (self-transition 0.78 / 0.74); band persistence reproduces
  MECH-1's rank persistence.

## 2. What disappeared after common-factor removal

- **Band return "cascade".** Raw band returns are 0.97–0.98 correlated at lag 0;
  after residualizing on market/BTC/ETH/vol/breadth/stablecoin factors (R²
  0.75–0.87), the relationships remain contemporaneous — there is no sequential
  band cascade in returns. Only 6/126 cells were pure common-field effects, but the
  surviving structure is *synchrony*, not *propagation*.
- **BTC→ETH→alt routing as a mechanism.** Routing states confirm MECH-1: no clean
  BTC-first sequence; BTC_CONCENTRATION and MIXED dominate (26% / 35% of days).
  Routing state transitions are coarse (2-state basin), not a ladder.

## 3. Strongest propagation pathways

1. `chain TVL (+14d) → stablecoin on-chain` — Cronos 0.468, Solana 0.393 (q=0.025-0.050)
2. `chain TVL (+3d/+7d) → stablecoin` — Cronos 0.408 (q=0.025)
3. `native velocity (+1d) → native improvement` — PulseChain 0.466, Polygon 0.427,
   Sui 0.392, Avalanche 0.392 (q=0.025)
4. `stablecoin (+14d) → chain TVL` — Avalanche 0.411 (q=0.025)
5. `CHAIN_TVL → NATIVE_IMPROVING` transfer entropy 1.109 nats, p=0.005 (J)

## 4. Strongest failed pathways

- **SMALL_CAP_ROTATION**: 6/2,196 days — small-cap rotation is not a real state.
- **LOWER_RANK_ACCELERATION** (lower ranks accelerate while leaders stall): 0 pattern
  days — never occurs in the Top-500.
- **STABLECOIN → breadth**: TE p=0.542 — no informational content.
- **STABLECOIN → band velocity**: p=0.075 — marginal only.
- **Delayed sector propagation**: all 1-14d peer-delay correlations ≈ 0.
- **Connectivity as a leading indicator**: band/sector graphs are dense (0.95/0.88)
  at all times; no topology change precedes rotation.

## 5. Exhaustion signatures (workstream F)

- `VELOCITY_WITHOUT_SHARE` (rank velocity up, mcap share not following): pattern
  assets' forward 14d return 0.0259 vs complement 0.0300 — mildly weaker, i.e. a
  weak exhaustion signal, NOT a reversal trigger.
- `BREADTH_AND_CONCENTRATION` (breadth up + concentration up): forward 30d BTC
  +0.092 vs complement +0.023 at 7d window — expansion-with-concentration is
  *risk-on continuation* (top-heavy rallies), the opposite of exhaustion.
- Net: exhaustion in this data is rank-level (MECH-1's 37% 14-day band reversal),
  not flow-level; flow-failure signatures are weak.

## 6. Discovered hierarchy

Variance decomposition of 169 clusters (sector/chain clusters vs global factor):
median shares — **idiosyncratic 0.61, sector-incremental 0.11, chain-incremental
0.07, global 0.09**. Global market factor explains ~9% of cluster variance; sector
explains more than chain at the median. Exceptions: Ethereum chain → 99.5% ecosystem
variance (assets are Ethereum-ecosystem tokens), binance-ecosystem → 25% global,
Solana → 29% sector. There is **no single global reference frame**: some clusters
are ecosystem-bound (ETH), others market-bound (binance-ecosystem).

## 7. Recurring morphisms

32/201 motifs recurring (16%); the recurring geometry is **persistence self-loops**
(MIXED, BTC_CONCENTRATION, BROAD_RISK_EXPANSION) plus **concentration as pivot**
(MIXED↔BTC_CONC two-step loops, 5/5 subperiods). 71% of motifs are cycle-specific —
states recur, token routes don't.

## 8. Causal evidence levels (see 11_CAUSALITY_LADDER.csv)

| claim | level |
|---|---|
| CHAIN_FLOW_HIERARCHY | L3 (conditional, robust to common factors, FDR) |
| BAND_LEAD_LAG_STRUCTURAL | L3 (but contemporaneous — see caveat in 04) |
| STATE_CONDITIONED_LEAD_LAG | L2 |
| INFORMATION_FLOW (chain TVL→native) | L2 |
| RANK_MIGRATION_PRECURSORS / LEADER_FIRST / FAILURE_SIGNATURES / MORPHISMS | L1 |
| HIERARCHY_GLOBAL_DOMINANCE | L0 (no dominant global reference frame) |

Nothing reaches L4+ (subperiod-robust, leave-one-cycle-out, quasi-causal) this
checkpoint; regime stability was assessed descriptively via morphism subperiod
counts.

## 9. What still looks like mere correlation

- All band-vs-band return relationships (contemporaneous co-movement).
- Same-day sector leader→peer confirmation (contemporaneous, no delay).
- TVL↔stablecoin two-way links (both directions significant → cycle, not arrow).
- Precursor event-vs-control differences (near coin-flip success).

## 10. What deserves the next terrain checkpoint

1. **State-conditional propagation depth** (B): the BTC_DOWN/VOL_HIGH flip of
   51-100→101-200 velocity lead deserves finer treatment — more states, longer
   horizons, leave-one-cycle-out stability.
2. **Chain-liquidity → native-asset timing** (E/J): which chains lead reliably, and
   does the TVL→native arrow hold out-of-cycle (2025-26 vs 2020-24)?
3. **Concentration pivot dynamics**: what precedes entry into / exit from
   BTC_CONCENTRATION (the field's only real bifurcation point).

## 11. Decision

**PASS_ALT_TERRAIN_WITH_LIMITATIONS** — conditional propagation structure exists
(B), the common factor is separated (A), chain hierarchy is empirically supported
(E/J), nulls are preserved, but: no sequential band cascade in returns, no delayed
sector spread, weak precursor discrimination, no small-cap state, and only 16% of
morphisms recurring. The terrain map is real but coarse; deeper mapping is justified
at the three points above, not across the whole field.
