# MECH-6 SUMMARY

**Checkpoint:** CRYPTO-ALT-MECH-6 — MICRO-STATE SEQUENCE ATLAS, BREADTH
TRANSMISSION, LOCAL MOTIFS & RESEARCH-TO-ALPHA ROLE MAPPING
**Empirical parent:** MECH-5 `244ca246` (PASS_MECH5_FAILURE_ANATOMY)
**Role:** AGENT 1 — CANONICAL FIELD CARTOGRAPHER. Terrain research ONLY.
**Verdict:** PASS_MECH6_MICROSTATE_SEQUENCE_ATLAS (see 22_MECH6_DECISION.md)

---

## 1. Micro-state event atlas (WS1)

- 1,244 event-horizon observations (125 canonical releases × 10 horizons:
  0,1,2,3,5,7,10,14,21,30) in `03_MICROSTATE_EVENT_PANEL.parquet`.
- Per horizon: canonical state, composite micro-state, breadth/rank/
  concentration/ETH/BTC axis atoms, acceleration/exhaustion/divergence flags,
  and 30 continuous coordinates (breadth, velocity, acceleration, dispersion,
  rank-depth, leadership width, TVL, DEX, stablecoins, vol). Definitions in
  `02_STATE_ATOM_DICTIONARY.md`.

## 2. Local sequence discovery (WS2) — 2 sequences promoted

**Promoted LOCAL_SEQUENCE (≥50 effective, 5/5 subperiods, FDR q=0.0):**

| seq | n_eff | lift (95% CI) | p30 success | p30 reentry |
|---|---|---|---|---|
| BREADTH_EXPANSION→BREADTH_FADE→BREADTH_EXPANSION | 56 | 2.81 | 0.16 | 0.30 |
| BREADTH_FADE→BREADTH_EXPANSION→BREADTH_FADE | 51 | 2.65 | 0.13 | 0.27 |

These are the two directions of one recurring motif: **breadth oscillation**
(expansion→fade→re-expansion) as a distinct micro-state sequence in the daily
panel, ~2.7× more frequent than the marginal-product baseline, present in every
subperiod. Its +30D outcome is dominated by reentry/mixed (no propagation),
i.e. oscillation is a *non-directional* field motion.

**Event-anchored release sequences remain DESCRIPTIVE (n≤33 < 50 bar):**

- BREADTH_EXPANDING→EXPANDING→EXPANDING (0-1-3D): n=18, lift 2.84, q=0.0004,
  p_success 0.444 vs 0.216 overall — persistent release-day breadth expansion
  is the strongest release-conditioned descriptor, but below the naming bar.
- BREADTH_FADING→FADING→FADING: n=23, p_success 0.043, p_reentry 0.391.
- Canonical MIXED→BTC_CONCENTRATION→BTC_CONCENTRATION: n=25, p_reentry 0.92 —
  the canonical boundary-oscillation path is near-deterministic reentry.
- 160/244 candidates LOW_SAMPLE_CURIOSITY; all retained in `20_NULL_AND_FAILED_RESULTS.csv`.

## 3. Breadth transmission anatomy (WS3)

- **Q1 — what changes first:** breadth level, velocity, dispersion,
  pos_ret_share and BTC 30D return already separate success/failure at release
  (+0D, FDR); breadth *acceleration* separates only at +5D. Transmission order:
  level/velocity → dispersion → acceleration.
- **Q2 — best discriminator:** breadth level AUC 0.875 at release; BTC 30D
  0.855; velocity 0.745; dispersion 0.704. Depth-rel and leadership-width are
  weak (AUC ≈ 0.51). Breadth level remains the dominant route coordinate.
- **Q3 — sufficiency:** BREADTH_EXPANDING at release → 65.2% sustained success
  (n=23, Fisher q=0.00008) vs 21.6% overall. Expansion+rank-recruitment
  n=5-7 (too small to conclude).
- **Q4 — stall before failure:** failures carry negative breadth velocity at
  release (median −0.024 vs +0.046 for successes), converging only by +5-7D.
- **Q5 — acceleration beyond level:** nested chronological logistic —
  level test AUC 0.883, +velocity 0.879, +accel 0.886; Δlogloss ≈ 0.0003-0.0015.
  **Breadth acceleration adds no material incremental information beyond level.**
- **Q6 — late decay:** among sustained episodes, median breadth change
  confirmation→end +0.004, then −0.020 in the 5 days after end. Breadth holds
  through confirmation; decay appears *after* the state ends (coincident, not
  an early warning).
- **Q7 — class signatures:** SUCCESS median breadth 0.76 at release (stays
  high through +14D); EARLY_SNAPBACK starts at 0.20 but breadth rises to 0.61
  by +14D (reentry despite improving breadth); BREADTH_FADE decays 0.29→0.12;
  MIXED flat at ≈0.18.

## 4. Failure motif refinement (WS4) — no promoted subfamilies

- EARLY_SNAPBACK (n=28): median time-to-reentry 1D; breadth at release median
  0.197 (low); rank recruitment present in only 3.6%; concentration rebuilds
  (top3_chg7 +0.009 by +3D); BTC_UP in only 39% — snapback is not BTC-specific.
  Subfamily splits (BTC_UP, VOL_HIGH × rebuild speed) not significant after FDR.
- BREADTH_FADE (n=23): breadth peaks fast (median time-to-peak 1D), decays
  −0.19 over 5D; rank 51-200 participation collapses (−0.164); market drifts
  slightly negative during fade; fade precedes route failure in 61%.
- Both n < 50 → motifs stay LOCAL_NODE / DESCRIPTIVE; **no subfamily promoted.**

## 5. Two-clock prospective competing-risk (WS5) — EARNED

Final cumulative incidence by day 30 (all 125 events resolve within 30D):

- REENTRY 0.416 · MIXED 0.352 · PROPAGATION 0.216 · OTHER 0.016.

**Reentry incidence (0.42) is roughly double propagation (0.22): the fast
failure clock vs the slow propagation clock, now estimated prospectively with
proper competing-risk accounting.** State-conditioned hazards:

- rank_recruit_lo at release → reentry 0.107 in days 1-3 vs propagation 0.000.
- CONC_RISING → reentry 0.107 (1-3D) vs propagation 0.018.
- BREADTH_EXPANDING → propagation 0.189 in days 4-7 (gate opens later).
- VOL_HIGH → highest early propagation 0.111 (1-3D) — with breadth, volatility
  behaves like an ignition/intensity coordinate, not a direction.

## 6. Termination microsequences (WS6) — DESCRIPTIVE_ONLY

First-decline coordinate before propagation end (n=27): **BREADTH_FIRST 17
(63%)**, ETH_FIRST 5 (19%), CONC_REBUILD_FIRST 3 (11%), DISP_FIRST 2 (7%).
Breadth-first deterioration is the dominant local termination motif, but n=27
< 50 → descriptive only; the global early-decay-signal remains NOT earned.

## 7. Conditional local rules (WS7)

350 sequence×condition cells; 65 significant after FDR. Persistent release-day
breadth expansion sequences concentrate under BREADTH_EXPANDING / BTC_UP /
VOL_HIGH / ETH_STRONG ("all aligned" states); fade sequences concentrate under
VOL_HIGH. Breadth-expansion sequences are GLOBAL-but-enriched; no sequence is
strictly condition-gated.

## 8. Alpha-role registry (WS8)

`17_ALPHA_ROLE_REGISTRY.csv`: every earned statistic tagged with role(s)
(TRANSITION_GATE, PROPAGATION_DEPTH, FAILURE_FILTER, TEMPORAL_DELIVERY,
DECAY_TERMINATION, RISK_CONTEXT, LOCAL_CLUSTER, …) plus evidence level, n,
conditionality, known nulls, data limits, causal level, redundancies.
**Research preparation only — no trades, no thresholds, no weights, no PnL.**

## 9. Node graph update (WS9)

`18_NODE_EDGE_UPDATE.csv`: 30 nodes / 10 edges. New MECH-6 nodes:
BREADTH_OSCILLATION (promoted), BREADTH_DIVERGENCE_* (6 coordinates),
BREADTH_TRANSMISSION_STAGE, TWO_CLOCK_PROSPECTIVE, TERMINATION_* signatures.

## 10. Answers to the checkpoint questions

1. **Recurring micro-state sequences ≥50:** BREADTH_OSCILLATION (both
   directions), 51-56 effective episodes, all 5 subperiods, FDR q=0.
2. **Global vs local vs conditional:** promoted oscillation = GLOBAL (no
   condition-gating); release-conditioned sequences DESCRIPTIVE (n≤33);
   65/350 condition cells significant → enrichment, not gating.
3. **Breadth transmission stages:** level/velocity at +0D → dispersion → 
   acceleration (+5D); breadth level is the dominant coordinate (AUC 0.875).
4. **Between breadth expansion and rank recruitment:** dispersion/velocity
   bridge; depth-rel and leadership-width add little (AUC ≈ 0.51).
5. **ES/BF homogeneity:** no FDR-significant subfamilies; both n<50 → no
   promoted subfamilies (ES median reentry 1D; BF median time-to-peak 1D).
6. **Prospective two-clock:** EARNED — CIF reentry 0.416 vs propagation 0.216;
   conditioned hazards show fast reentry under rank_recruit_lo/CONC_RISING and
   slower propagation under breadth expansion.
7. **Local termination motifs:** BREADTH_FIRST termination (63%) is a real
   local motif but n=27 → DESCRIPTIVE_ONLY.
8. **Alpha roles:** registry in `17_ALPHA_ROLE_REGISTRY.csv` (research prep).
9. **Merged/dissolved/promoted:** `19_NEW_NODE_MERGE_DISSOLVE.csv` —
   promoted: BREADTH_OSCILLATION, BREADTH_T
RANSMISSION_STAGE,
   TWO_CLOCK_PROSPECTIVE; MERGE: ACCUMULATION_LIKE (into breadth);
   DISSOLVE: VOLATILITY_INCREMENTAL_GATE; NULL: MOTIF_SUBFAMILY.
10. **Topology change:** BREADTH_OSCILLATION added as a recurring micro-state
    node; breadth level reinforced as the route-gate primitive; two-clock
    mechanism now prospectively estimated; release-conditioned sequences stay
    below the naming bar (honest null).

**human_review_required = TRUE · next_checkpoint_authorized = FALSE**

No strategy. No PnL. No deployment.
