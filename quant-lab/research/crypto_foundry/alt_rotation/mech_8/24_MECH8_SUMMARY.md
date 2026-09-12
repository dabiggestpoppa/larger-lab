# CRYPTO-ALT-MECH-8 — SUMMARY

**Field-state deepening: breadth×dispersion transition lattice, pre-event
isolated-downside buildup, breadth architecture, rank-health context &
cross-agent synthesis support.**

**PARENTS:** MECH-6 `9c3dcd32` · MECH-7 `1a9c565e` · LOWER-FIELD-2 `af2ed678` ·
LOWER-FIELD-3 `0a0eee7e`
**VERDICT:** **PASS_MECH8_FIELD_STATE_DEEPENING** (see `25_MECH8_DECISION.md`)

---

## 0. Headline interpretation

1. **The isolated-downside reversal-vs-continuation divergence is NOT
   meaningfully pre-detectable before ~t0.** Under the extended −30D lattice with
   FDR, only ONE pre-event coordinate survives: `rank_depth_rel` first separates
   at −21D (q=0.095, effect −0.007). MECH-7's headline −14D dispersion separation
   (med 0.347 vs 0.293) does **not** survive FDR under the extended lattice
   (raw p=0.046 → q=0.264). Direction is consistent, robustness is not earned.
   This **corrects MECH-7**: the reversal-vs-continuation distinction on these
   global coordinates is essentially contemporaneous (t0 and after), not a
   multi-day pre-event build.

2. **Breadth×dispersion is a genuine 4-state transition system.** Full 16-cell
   matrix with dwell, forward tails, propagation/reentry outcomes. HH is the
   most persistent cell (p=0.899, median dwell 13D) and the strongest
   propagation cell (fwd7 prop 0.51).

3. **State age matters.** In HH, fwd7 propagation probability rises from 0.23
   (DAY_1) to 0.67 (DAY_15_PLUS) while P(leave) falls 0.27 → 0.04. The same cell
   means different things at different ages. This is the first earned
   early/mature state-age distinction.

4. **Rank health and price recovery are separable clocks.** Among
   RANK_DETERIORATING isolated downsides (n=672), 64% recover in price but only
   44% recover in rank; the PRICE_RECOVERY_RANK_DECAY population is real (29% of
   the class). A rebound is NOT structural health — the operator's core
   question is answered affirmatively.

5. **Breadth architecture is real but NOT predictive beyond level.** Two
   architectures cluster (leader-driven vs broad-based, silhouette 0.46, 5
   subperiods), but every composition block fails the incremental test for
   upper propagation (all Δlogloss > 0). **MERGE** into breadth level.

6. **M7 vs LF3 rank-deterioration disagreement is definition-driven**, resolved
   by documentation + the harmonized pre_rank_state split used here.

## 1. Isolated-downside pre-event buildup (−30D) & effect curves (WS1/WS2)

- 510 variable×lag cells tested; 71 FDR-significant (q<0.1) — but only **1**
  is pre-event (lag < 0): `rank_depth_rel@-21` (q=0.095).
- Raw p<0.05 pre-event cells: 5/270 — directionally consistent with MECH-7
  (dispersion higher pre-event among reversals at −14/−10), but none survive
  FDR except rank_depth_rel@−21.
- t0/post-event: 70/240 FDR-significant cells — divergence is real and strong,
  but it is detected **at and after** the shock, not before.
- Pre-event sequence atlas: no atom clears FDR. The closest (VOL_HIGH, lift
  1.06, q=0.58) is noise. No repeated pre-event "shape" distinguishes reversal
  from continuation on current global coordinates.
- **Answer to Q1/Q2**: divergence does NOT begin before −14D in a robust sense;
  the −30D buildup is largely indistinguishable between reversal and
  continuation classes. MECH-7's −14D claim is downgraded to DIRECTIONAL-ONLY.

## 2. Breadth×dispersion 4-state transition matrix (WS3, PRIMARY)

Diagonals (persistence):
- HIGH_HIGH → HIGH_HIGH: p=0.899, n=677, med dwell 13D — most persistent, fwd7
  prop 0.514, fwd7 reentry 0.239.
- HIGH_LOW → HIGH_LOW: p=0.748, n=244, dwell 3D — fragile.
- LOW_HIGH → LOW_HIGH: p=0.758, n=207, dwell 6D.
- LOW_LOW → LOW_LOW: p=0.876, n=709, dwell 11D.

Key off-diagonals (n≥10):
- HIGH_LOW → LOW_LOW (p=0.141): fwd7 prop 0.130, reentry 0.391 — breadth-loss
  snapback path.
- LOW_LOW → HIGH_LOW (p=0.056): fwd7 prop 0.222, reentry 0.444.
- HIGH_LOW → HIGH_HIGH (p=0.098): fwd7 prop 0.344 — dispersion arrival into an
  already-broad field is a propagation-adjacent move.
- HIGH_HIGH → HIGH_LOW (p=0.039): fwd7 prop 0.310.

Interpretation: the system is dominated by persistence (all four cells are
sticky). Breadth loss from HIGH_LOW is the fastest route to low participation;
HIGH_HIGH → HIGH_LOW is the most common HH exit and still propagates (0.31).

## 3. State age / maturity (WS4)

- HH: P(leave) 0.27 (DAY_1) → 0.04 (DAY_15_PLUS); fwd7 prop 0.23 → 0.67.
  Mature HH is where propagation lives; young HH is still coin-flip.
- HIGH_LOW: P(leave) roughly flat 0.23–0.33 — no maturity gradient.
- LOW_HIGH: DAY_1 leave 0.47 (fragile disorder), DAY_15_PLUS 0.16.
- LOW_LOW: DAY_1 leave 0.40 → DAY_15_PLUS 0.07 (compression is sticky).

**Earned:** state age materially changes the meaning of the HH cell
(early/mature gradient). Not earned for other cells.

## 4. HIGH_BREADTH + HIGH_DISPERSION full lifecycle (WS5)

- 367 HH episodes pooled; median dwell ~2–13D by path.
- Entry order: BRD_FIRST (n=33) is the only ≥30-episode entry path; DISP_FIRST
  and SYNCHRONOUS are below naming bar.
- Exit order: DISP_FIRST_EXIT (n=31) dominates; COUPLED_EXIT present.
- **No lifecycle path clears the ≥50-episode naming bar → DESCRIPTIVE.**
  The choreography exists but remains too thin to promote.

## 5. Rank health vs price recovery (WS8, PRIORITY)

Forward-rank-corrected matrix (rank outcome uses t+7 rank velocity via
self-join):

| pre_rank_state | n | P(price rec) | P(rank rec) | dominant cross-state |
|---|---|---|---|---|
| RANK_IMPROVING | 316 | 0.53 | 0.44 | PRICE_DECAY_RANK_DECAY (0.32) |
| RANK_STABLE | 35 | 0.60 | 0.43 | PRICE_RECOVERY_RANK_RECOVERY (0.34) |
| RANK_DETERIORATING | 672 | **0.64** | 0.44 | PRICE_RECOVERY_RANK_DECAY (0.29) |

- **PRICE_RECOVERY_RANK_DECAY is a real, reproducible population** (n=197 among
  deteriorating; also present in improving, n=76).
- Deteriorating-rank shocks bounce in price (median price-recovery day = 1D,
  fastest of all classes) without recovering structural rank — the temporary
  shock / structural weakness distinction survives at the asset level.
- Temporal order: price recovers first (median 1–2D); rank recovery is a
  slower, separate clock.

## 6. Failed-recovery stress-response pilot (WS9)

- Among deteriorating-rank isolated downsides with a field-improving window
  (n=649): 45.6% RESPONDS in price, 17.7% weak/delayed, 36.7% no response;
  rank recovers in only 42.7% while 52.2% keep decaying.
- The pilot supports the queued stress-response concept descriptively (a
  rebound ≠ health), but a field-improving control group (no-improvement
  windows, n<30) could not be built → DATA_LIMITED for the contrast.

## 7. Active liquidity / volume (WS10)

- Volume adds **nothing robust** for recovery (Δlogloss +0.0015, AUC −0.006,
  perm p=0.003 on the wrong side) or reversal (Δ≈0, perm p=1.0) after
  controlling rank/breadth/dispersion/BTC/vol/age/amplitude.
- LF3's higher-volume early-recovery loners do not transfer to a robust
  incremental field-context role → **DESCRIPTIVE_ONLY**.

## 8. SHMC / SHHM (WS11)

- SHMC (n=23,364): lower breadth (0.224 vs 0.53), lower dispersion, cell mode
  LOW_LOW, higher reversal (0.583 vs 0.561, ranksum p=7e-7) — reversion-like.
- SHHM (n=79,755): broad field context (cell mode HIGH_HIGH), continuation-like.
- **Reversion vs continuation local roles confirmed descriptively.** SHMC
  tail-activation stays DISSOLVED; the reversion role is LOCAL_DESCRIPTIVE.

## 9. Volatility (WS12, parked)

- HH persistence: VOL_HIGH days have longer HH runs (44 vs 18D) and higher P(in
  HH) — intensity context only.
- Early 1σ recovery: VOL_HIGH rate 0.47 vs 0.37 (p=0.008); VOL_LOW 0.35 vs 0.43.
- Coordinated-up retention: mixed signs, tiny effects (Δ≤0.008).
- **Conclusion: volatility remains an intensity/retention context, not an
  incremental gate** — consistent with MECH-5/6/7.

## 10. Agent1/Agent2 reconciliation (WS13)

- rank_deterioration_reversal: M7 0.591 vs LF3 0.536 → **definition-driven
  disagreement** (event gate, rank-velocity threshold, reversal definition).
- event_gate / sign_convention: resolved by documentation.
- isolation_definition: complementary (M7 canonical field context, LF3 local).
- Harmonized estimate: use z1≥2 ISOLATED + pre_rank_state split (this
  checkpoint's WS8/WS9 numbers).

## 11. Breadth architecture (WS6/WS7)

- Components: rank layers contribute roughly uniformly (R1_25 0.05 share →
  R251_500 0.38); age/liquidity/vol cohorts nearly flat pos-rates (0.48–0.54);
  rank-health splits pos-rate strongly (IMPROVING 0.61 vs DETERIORATING 0.43);
  strong-move share: 2σ movers 86% positive.
- Clustering: 2 classes (leader-driven R1_25 share 0.80 vs broad-based 0.24;
  silhouette 0.46; both 5 subperiods, n=537/540).
- **Incremental audit (purged CV, 125 releases): every composition block hurts
  or ties breadth level (Δlogloss ≥ 0, best ΔAUC +0.005 for strong-move share).**
  → **MERGE composition into breadth level.**

## 12. Cross-agent export (WS15)

- `20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet`: 177,866 rows, 144 cols, keyed
  by event_id/asset_id/date, with t0 field context + lagged coordinates at
  −30/−21/−14/−10/−7/−5/−3/−2/−1 + 2×2 cell + architecture components.
  No forward fields → no target leakage. Schema: `20b_...`.

## 13. Nodes (see 22_PROMOTE_MERGE_DISSOLVE.csv)

- PROMOTE: BREADTH_DISP_4STATE_MACHINE (transition system earned)
- NEW_NODE: STATE_AGE_MATURITY (HH age gradient), PRICE_RANK_HEALTH_SPLIT
  (priority matrix), ISOLATED_DOWN_PRE_EVENT_BUILDUP (as DIRECTIONAL, not robust)
- MERGE: BREADTH_ARCHITECTURE → breadth level; BREADTH_FADE → transition lattice
- DISSOLVE: SHMC tail activation (kept as local reversion role)
- PARK: VOLATILITY (intensity context), ACTIVE_LIQUIDITY (descriptive)
- QUEUED: HH lifecycle choreography (n<50), RETEST_RELOAD, termination motif,
  stress-response contrast (DATA_LIMITED)

## 14. Nulls (see 23_NULL_AND_FAILED_RESULTS.csv)

- Pre-event reversal/continuation discrimination (beyond rank_depth_rel@−21):
  NULL under FDR.
- Breadth composition incremental: NULL.
- Stable breadth architectures predictive: NULL (clustering descriptive).
- HH lifecycle named paths ≥50: DESCRIPTIVE (n<50).
- Active liquidity incremental: NULL.
- Volatility incremental gate: NULL.
- SHMC tail activation: NULL.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT
