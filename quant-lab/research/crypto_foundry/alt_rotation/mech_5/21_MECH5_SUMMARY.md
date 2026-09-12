# MECH-5 SUMMARY

## CHECKPOINT: CRYPTO-ALT-MECH-5
FAILURE ANATOMY, ROTATION SURVIVAL, TEMPORAL DIVERGENCE & TERMINATION PRECURSORS
**Role:** AGENT 1 — CANONICAL FIELD CARTOGRAPHER

## Canonical Event Cohort (WS preamble)
Canonical 125 concentration-release events preserved from MECH-4 ledger.
- 52 REENTRY BTC_CONCENTRATION (FAILURE)
- 44 MIXED_NO_CLEAR_ROUTE (FAILURE)
- 18 BROAD_RISK_EXPANSION (SUCCESS)
- 4 LARGE_ALT + 4 MID_CAP + 1 ETH_BROADENING (SUCCESS, 9 alt-family)
- 1 CAPITAL_EXIT + 1 STABLECOIN_PARKING (OTHER)
- Family totals: SUCCESS=27, FAILURE=96, OTHER=2
Reconciles 100% with MECH-4 (125/125).

## 1. First-Divergence Analysis (WS1)
16 variables showing earliest statistically significant separation between
success (n=27) and failure (n=96), FDR-corrected.

### Earliest-divergence timeline (FIRST_DIVERGENCE_DAY):
- **+0D (release day):** btc_return_30d (r=0.51), top3_share_chg7 (r=-0.20)
- **+1D:** top500_breadth_30d (r=0.53), top500_breadth_7d (r=0.36), top500_dispersion_7d
- **+2D:** eth_btc_relative_return_30d (r=0.25)
- **+3D:** btc_return_7d (r=0.32), top500_dispersion_30d (r=0.36)
- **+5D:** eth_btc_relative_return_7d
- **+7D:** chain_tvl_med_chg7 (r=0.37)
- **+10D:** btc_dom_chg30 (r=-0.43)
- **+14D:** med_ret30_201_500 (rank 201-500 velocity, r=0.49)
- **+21D:** med_ret30_11_50, med_ret30_51_200, total_mcap_chg30
- **+30D:** top3_share

**Interpretation:** BTC 30D return and breadth (+1D) separate fastest and are
the largest effects. BTC dominance (negative) and rank-band velocity separate
later (10-21D). Breadth leads; rank participation lags — consistent with
MECH-4 route-gate (breadth as gate, rank depth as consequence).

## 2. Success vs Failure Weight Map (WS2)
Incremental logistic blocks (5-fold CV):
| model | n_feat | CV AUC | perm_p | ΔAUC |
|---|---|---|---|---|
| M0 current state | 10 | 0.8575 | 0.002 | — |
| M1 +breadth | 14 | 0.8633 | 0.002 | +0.006 |
| M2 +volatility | 15 | 0.8633 | 0.002 | 0.000 |
| M3 +rank participation | 18 | **0.8912** | 0.002 | **+0.028** |
| M4 +conc/btc/eth | 23 | 0.8891 | 0.002 | -0.002 |
| M5 +timing | 24 | 0.8672 | 0.002 | -0.022 |
| M6 +chain/sector | 26 | 0.8689 | 0.002 | +0.002 |

**Largest incremental gain is M3 (rank-band participation): +0.028 AUC.**
Volatility adds nothing (M2 Δ=0). State age/timing (M5) actually HURTS
(overfit / no incremental info). Final best CV AUC = 0.869 (all).

## 3. RETEST_RELOAD Internal Anatomy (WS3)
RETEST_RELOAD (n=14) vs FAILED_IGNITION (n=52), comparing retracement-phase
retention (+1D to +5D):
- **0/8 variables significant after FDR.** Raw (pre-FDR) p<0.05 for
  top500_dispersion_30d (media 1.06 vs 0.98) and med_ret30_51_200 (1.22 vs 0.74)
  but neither survives FDR.
- **Conclusion:** RETEST_RELOAD is NOT structurally distinguishable from
  FAILED_IGNITION on the observable common pullback sequence. The motif is
  descriptive only; small n and coordinate overlap preclude promotion.
  Classified LOCAL_MOTIF / DESCRIPTIVE_ONLY.

## 4. Two-Clock Temporal Mechanism (WS4)
Escape / propagation / failure hazards across 1-30D:
- **Escape** (not reentry): 84% at 1D dropping to 58% by 21-30D.
  Escape resolves EARLY; remaining risk decays gradually.
- **Failure reentry** (among failures): 20% at 1D → 53% by 21-30D.
- **Sustained propagation** (among successes): 22% confirmed by 1D, 74% by 7D,
  100% by 21D. Propagation CONFIRMS more slowly than escape.

**Two distinct clocks supported:** escape resolves fast (most entropy in 1-5D);
propagation confirmation is slower (reaches 74% only by 7D).

### Temporal window refinement
Narrowest discriminative windows:
- **14-30D:** top500_breadth_30d diverges HARD (median_suc -0.26 vs fail +0.002,
  p_fdr=0.0) — breadth bleeding late is the strongest success/failure differentiator.
- **7-14D:** vol_med divergence (p_fdr=0.040)
- **0-3D:** weak breadth/vol signals (1-3D p_fdr ~0.06-0.11)
No single narrow window beats the full lattice; the 14-30D breadth signal is
the dominant late differentiator.

## 5. Early Decay / Termination Reconstruction (WS5)
For 27 successful propagation episodes, tracked -14D→+3D around termination:
- **Only vol_med shows early decline >30%** (n=14, 57%, median start 6.5D).
- Most variables (breadth30, breadth7, TVL, btc_ret, rank velocity) do NOT
  show a consistent >30% decline within 7D of termination.
- **Interpretation:** MECH-4's EARLY_DECAY_SIGNAL is NOT reproduced at the
  >30% threshold. The propagation-termination signal is dominated by volatility
  change, not breadth/leadership decay. Classified DESCRIPTIVE_ONLY, not a
  robust early-decay node.

## 6. Failure-Sequence Clustering (WS6)
Recurring failure motifs across all 125 events:
- EARLY_SNAPBACK 28 (22%), SUCCESS 27 (22%), BREADTH_FADE 23 (18%),
  BREADTH_DIVERSITY_NO_ROUTE 16 (13%), MID_SNAPBACK 16 (13%),
  LATE_SNAPBACK 8 (6%), STABLE_NO_ROUTE 5 (4%), UNCLASSIFIED 2.
**Failure is dominated by EARLY_SNAPBACK (≤3D reentry) and BREADTH_FADE**
(breadth collapses while price lingers) — two distinct failure geometries.
Confirmed as recurring motifs.

## 7. Conditional Rescue Test (WS7)
Success rate by regime at release (overall = 21.6%):
- **BREADTH_EXPANDING: 59.5% success (vs 21.6% overall, p_fdr<0.001)**
- BREADTH_CONTRACTING: 5.7% (p_fdr=0.008)
- RISK_OFF: 4.8% (p_fdr=0.025), BTC_DOWN: 4.5% (p_fdr=0.025)
- VOL_HIGH: 37.0%, BTC_UP: 33.8% (not significant after FDR)
**BREADTH is the dominant gate coordinate**: expanding breadth triples success
probability; contracting breadth / risk-off / BTC-down kill it.

## 8. Causality Ladder
- All WS1 divergences: L1_TEMPORAL_ORDERING (separation timing, not causality)
- WS2 weight map: L0_DESCRIPTIVE (predictive separation only)
- WS3 retest/reload: L0_NULL (not separable)
- WS4 hazards: L1_TEMPORAL_ORDERING (descriptive hazard)
- WS5 decay: L1_TEMPORAL_ORDERING (narrow, vol-only)
- WS6 motifs: L0_DESCRIPTIVE (taxonomy)
- WS7 rescue: **L2_CONDITIONAL_LEAD_LAG** (regime-conditioned success, 4/10 sig)

## Answers to Final Questions
1. Earliest divergence: **BTC return (30D) & breadth (+0D/+1D)**; effect sizes
   r=0.51/0.53, largest of all.
2. Most incremental info: **rank-band participation family (M3)**.
3. RETEST_RELOAD distinct from FAILED_IGNITION? **No** (0/8 after FDR).
4. What survives pullback in reloads? **Not observable distinct** on these
   coordinates.
5. Escape vs propagation clock? **Yes — escape fast, propagation slow.**
6. Narrower temporal lattice? **14-30D breadth is dominant; no narrow window
   fully substitutes.**
7. Reproducible early-decay? **Only volatility; breadth decay not reproduced.**
8. Warning to end? **~6D on volatility; other coordinates weaker.**
9. Recurring failure motifs? **Yes: EARLY_SNAPBACK, BREADTH_FADE.**
10. Global/conditional/local/null: WS1/WS7 global-conditional; WS3 null;
    WS5 local (vol); WS4 descriptive.
11. Emergent primitive? **BREADTH as route-gate primitive is reinforced**
    (dominant divergence, root of rescue, and strongest success/failure driver).
    No forced new primitive.
