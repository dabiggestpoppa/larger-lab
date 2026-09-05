# MECH-3 SUMMARY — CHAIN-LIQUIDITY ANATOMY, REGIME-ROUTING & CONCENTRATION PIVOT MAPPING

**AGENT 1 — MAIN FIELD CARTOGRAPHER.** Terrain research only. No strategy, no PnL,
no optimization, no deployment.
**Parents:** MECH-1 `b3083df1` · MECH-2 `8636370a` · HEAD at run start `04a09016`.
**Decision:** PASS_ALT_MECH3_WITH_LIMITATIONS (see 25_DECISION.md).

## 1. Chain-liquidity components that survived (WS A/B)

- **Chain liquidity is NOT one latent quantity.** Across the 66 pairwise
  combinations of 12 chain-liquidity coordinates (pooled over 12 chains), **0 pairs
  are REDUNDANT_PROXY** (|r| ≥ 0.85), only 4 are PARTIAL_PROXY (0.60–0.85), 3 are
  LOCAL_COORDINATE, 6 DISTINCT_INFORMATION, and **53 CANDIDATE_DISTINCT** (|r| < 0.20).
  The strongest relationships: `imp_share–vel7` (0.81, PARTIAL_PROXY),
  `sc_chg7–sc_chg30` (0.76), `tvl_lvl–tvl_share` (0.68), `tvl_chg7–tvl_chg30` (0.50).
  The TVL family, the native-family, and the global-flow family are **separate
  coordinates** — removing any one family leaves the others carrying distinct
  information.
- **What survives perturbation (WS B, 5 links × 12 chains × 7 ablations):**
  - `VELOCITY→NATIVE_IMPROVING` **SURVIVES on Solana (5/5 ablation variants)**, and
    the pooled link is robust: LOO_CHAIN corr range 0.32–0.35 (no single chain
    drives it), LOO_CYCLE range 0.26–0.46 (positive in all 5 subperiods; weakest
    2025-26 at 0.26, strongest 2022 at 0.46).
  - `TVL→NATIVE_IMPROVING` and `TVL→NATIVE_VELOCITY` are mostly NO_RELATION /
    WEAKENED — TVL level change is NOT a reliable native-asset precursor once
    residuals are conditioned. This refines MECH-2: the surviving arrow is
    **velocity→breadth**, not **TVL→price**.
  - `STABLECOIN→TVL` **DISSOLVES** (0 SURVIVES, 10 DISSOLVES, 30 NO_RELATION):
    global stablecoin change is NOT a universal chain-liquidity driver.
  - `TVL→DEX` is weak (0 SURVIVES, 30 WEAKENED).

## 2. Which components were redundant (WS A)

- Only 4 PARTIAL_PROXY pairs; **no REDUNDANT_PROXY pair exists** in the
  chain-liquidity family. Redundancy is modest and pair-specific (imp_share≈vel7,
  sc_chg7≈sc_chg30, tvl_lvl≈tvl_share). MERGE decision: the TVL family does NOT
  collapse into one node; instead each TVL coordinate is a LOCAL coordinate with a
  distinct partner (level↔share; 7D↔30D change). The native family is a 2-node
  family (imp_share≈vel7), both distinct from TVL.

## 3. Strongest candidate primitives (WS J)

- **VOLATILITY is the only GLOBAL_CANDIDATE_PRIMITIVE** of the 8 tested:
  removal ΔR² = 0.0054 on the concentration-exit reconstruction (above the 0.005
  preregistered bar), max |r| with other candidates 0.61 (< 0.85), and it ranks
  top-3 by |beta| in **5/5 subperiods**.
- BREADTH and ETH_RELATIVE are LOCAL_PRIMITIVES (material in some subperiods only).
- DEPLOYABLE_LIQUIDITY (stablecoin), CAPITAL_CONCENTRATION, RANK_DISPERSION,
  CHAIN_LIQUIDITY, DEX_ACTIVITY are NOT_PRIMITIVE for the concentration-exit
  phenomenon — consistent with WS B's stablecoin DISSOLVE.

## 4. Strongest routing flips (WS D)

16 of 110 (relationship × state) cells are REVERSED/GAINED at q<0.05.

- **The flagship MECH-2 flip reproduces and generalizes:** `51-100→101-200` rank
  velocity lead is GAINED under **11 states** (uncond +0.13 → **BTC_DOWN +0.63,
  VOL_HIGH +0.67, ETH_WEAK +0.58, RISK_OFF +0.58**; all q<0.05). The mid-band
  propagation lead is strongest when the broad field is weak or risk-off.
- **NEW flip (REVERSED):** `201-300→301-500` velocity — unconditional **−0.40**
  (higher band leads with opposite sign) flips to **+0.24 under CONC_FALLING**
  (q=0.032): when concentration is falling, the lower bands lead the 201-300 band
  positively. Concentration state reverses the sign of this relationship.
- `26-50→51-100` GAINED under BREADTH_CONTRACTING (−0.14 → −0.37).

## 5. Concentration entry anatomy (WS E)

126 entry events. Entry is preceded (all q<0.05, FDR over 130 cells) by:

- **Falling BTC dominance change** (7D: −0.006 vs controls), **falling BTC 30D
  return** (−0.039), **falling breadth** (−0.093 at 3D), **falling top-3 share
  change** (−0.0012 at 14D).
- Interpretation: **BTC_CONCENTRATION is entered AFTER BTC/leadership weakness** —
  it is a *defensive/reflexive* concentration (breadth collapsing, BTC relatively
  strong only in the return-rank sense), not a strength rally. Entry precursors are
  robust across windows 1–30D (15 significant cells).

## 6. Concentration exit anatomy (WS E)

125 exit events. Exit is preceded by (q<0.05):

- **Rising BTC 30D return** (+0.017 at 1D, +0.022 at 3D vs controls) and **rising
  breadth** (+0.086 at 1D, +0.071 at 3D).
- Exit is *strength-triggered*: concentration releases when BTC and breadth
  simultaneously improve — the mirror image of entry (which follows weakness).
- Exit precursors are short-window only (1–3D; nothing significant at 7–30D):
  exits are fast events, entries are slow-build events. **Asymmetry in pivot
  anatomy** — an important structural fact.

## 7. Release route hierarchy (WS G)

125 exits; destination (first state held ≥ 5 days):

1. **MIXED_NO_CLEAR_ROUTE 44 (35%)** — the dominant release: concentration
   dissipates into no-clear-route, not into a directional alt rotation.
2. **REENTRY to BTC_CONCENTRATION 52 (42%)** — many exits are *oscillations* across
   the concentration boundary (median time-to-destination 3D; 25th pct 1D).
3. **BROAD_RISK_EXPANSION 18 (14%)** — the main genuine release route.
4. LARGE_ALT 4, MID_CAP 4, ETH_BROADENING 1, CAPITAL_EXIT 1, STABLECOIN_PARKING 1.

Route hierarchy: **concentration→mixed (dissipation) ≫ concentration→broad-risk
(real release) ≫ concentration→alt rotation (rare)**. Alt-rotation release is
almost nonexistent (9/125); MECH-2's "no small-cap rotation" null extends to
"no large/mid/eth alt-rotation release either". Release routes are stable across
subperiods (mixed+reentry dominate in 4 of 5; broad-risk release appears in all 5).

**First-changed observable before release:** top3_share_chg7 and chain_tvl_med_chg7
tie for first (28 each), then breadth30 (19), btc_ret7 (14). Route selection
predictability: exits into BROAD_RISK_EXPANSION most often show chain_tvl_med_chg7
or top3_share_chg7 as first mover; no single precursor strongly discriminates the
route before it develops (terrain inference, NOT a trading signal).

## 8. Information plateau (WS H)

| Phenomenon | Plateau R² | Plateau reached at |
|---|---|---|
| CHAIN_EXPANSION | 0.292 | chain_tvl_med_chg7 (5th variable) |
| ROUTING_FLIP_REALIZED | 0.041 | stablecoin (4th) |
| CONCENTRATION_EXIT_7D | 0.076 | chain_tvl_med_chg7 (5th) |

- Chain expansion is the most reconstructable phenomenon (R² 0.29) but still ~71%
  unexplained; breadth+stablecoin+chain TVL carry most information; top3/vol/eth-rel
  add < 0.004 each (information plateau at 5 variables).
- Concentration exit is weakly reconstructable (R² 0.076) — exits are
  **not predictable from the 8 global observables**; consistent with fast/short
  exit anatomy (WS E).
- Routing-flip state is nearly unpredictable (R² 0.041) — the flip is
  state-dependent but not state-explainable from these coordinates.

## 9. Field plateau (WS I)

922 plateau episodes:

- **P1 CHAIN_LIQ_NO_NATIVE** (TVL up, native weak): 797 episodes, median duration
  4D. Release trigger = **imp_share** (315) / tvl_chg7 (243) / vel7 (224): the
  plateau releases when native improving-share moves first.
- **P2 VELOCITY_NO_BREADTH**: only 14 episodes (rare), trigger chain_tvl_med_chg7
  or btc_return_30d.
- **P3 CONC_NO_ROUTE** (concentration flat, no route): 111 episodes, median 4D,
  trigger **top3_share_chg7** (66) / eth_rel30 (19) / btc_dominance (13): the
  plateau releases on a concentration-coordinate move first.

Field plateaus are real and distinct from information plateaus: the market stalls
(P1: 797 episodes) while the *observables* still predict the stall poorly (H R² low).

## 10. Graph/topology readiness (WS K)

**TOPOLOGY_EARNED = YES (conditional).** Sparse velocity graph (density 0.09,
8 components, 7 liquidity islands): one persistent Ethereum–Polygon–Solana core
(≥2 members co-cluster in 3/5 subperiods), **Ethereum is the sole articulation
point** (bottleneck), 2022 = total fragmentation, 2024 = near-total fusion.
Persistent homology NOT earned — components/bridges fully describe the small graph.

## 11. Dynamical-system readiness (WS L)

**ATTRACTOR-LIKE = YES (descriptive, L1).** Concentration/mixed basin self-
transition 0.87–0.94 in ALL 5 subperiods (0.868–0.942). BTC_CONCENTRATION
self-transition 0.72–0.88. **Hysteresis confirmed**: exit route depends on entry
route (chi-square p < 0.001, n=125) — path dependence at the pivot.

## 12. Morphism readiness (WS M)

**CATEGORY_STYLE_FORMALIZATION_EARNED = NO.** Recurring morphisms (16%) are
persistence self-loops (56%) + concentration-starting sequences (16%) — the
*stays*, not the *routes*. Generic archetype order is preserved at 96.9% but that's
an ordering constraint, not recurring composition. The recurring object is a
persistence/pivot state machine (WS L), not category-style composition.

## 13. Observation limits (WS N → 03_OBSERVATION_LIMITS.md)

Per-chain stablecoin, bridge flows, perp OI/funding, lending TVL, staking,
addresses, exchange flows, wallets — UNOBSERVED everywhere. "Ethereum bottleneck"
is co-movement evidence, not verified capital routing. Route-selection mechanism
UNOBSERVED.

## 14. NEW_NODE / MERGE / DISSOLVE (19_NEW_NODE_MERGE_DISSOLVE.csv)

- **NEW_NODE**: TVL family as 4 separate local coordinates (no REDUNDANT pair);
  concentration pivot boundary coordinates (6/10 with |ρ|≥0.5 monotonicity);
  VOLATILITY as the sole global candidate primitive; Ethereum articulation node;
  pivot hysteresis.
- **MERGE**: recurring morphisms → persistence/pivot family; native
  imp_share≈vel7 as a 2-node native family.
- **DISSOLVE**: global stablecoin as universal chain-liquidity driver; any prior
  "dense chain field" notion (density 0.09); alt-rotation as a concentration
  release route (9/125).

## 15. What still looks like mere correlation

- TVL↔stablecoin two-way links (no clean arrow).
- Same-day native velocity↔improving-share (contemporaneous family).
- All band-return co-movement (carried from MECH-2).
- Concentration-exit predictability is essentially nil (R² 0.076) — the pivot exit
  anatomy is descriptive, not predictive.

## 16. Decision

**PASS_ALT_MECH3_WITH_LIMITATIONS** — chain liquidity is decomposed (no single
latent quantity; velocity→native arrow survives perturbation; LOO-stable), routing
flips are mapped with the flagship flip generalized across 11 states plus one new
REVERSED relationship, concentration pivot anatomy is materially improved (entry =
weakness, exit = strength, asymmetric windows, hysteresis), release routes are
empirically described (dissipation ≫ broad-risk ≫ alt-rotation), primitives are
narrowed to VOLATILITY as the sole global candidate, nulls preserved, no causal
overclaiming (max ladder level L3), higher mathematics earned only where simple
structure supports them (topology conditional-YES, dynamics descriptive-YES,
category-style NO). Limits: chain-liquidity support weakens under basic perturbation
for most links (only velocity→native survives), routing flips are stable but
unpredictable (H R² 0.04), no reproducible *predictive* exit precursor geometry
(only descriptive anatomy), and primitives mostly collapse toward beta proxies.
