# CR-P8 — CEREBUS Routing Overlay Discovery Report

> Task: CR-P8-CEREBUS-ROUTING-OVERLAY-DISCOVERY-01
> Base: Phase 7.5 sealed baseline `7bc1c0242cd05a205da62b34904d7308c63f2acb` (ACCEPTED)
> STOPPED after primitive discovery + candidate classification.

## 1. Frozen baseline (untouched)

| Family | Signal | Trade | Entry | Hold |
|--------|--------|-------|-------|------|
| A | EUR ACCUMULATION | LONG USDJPY | t0+2h | 6h |
| B | EUR LIQUIDATION | SHORT USDJPY | t0+1h | 6h |

Event universe (valid baseline windows): A = 432, B = 458; discovery = 459, confirmation = 149, RELATIONSHIP_CONFIRMED_OOS = 280.

## 2. Canonical CEREBUS primitives (frozen)

- **Daily tier** (Pine get_tier): T1 <20, T2 20-30, T3 30-45, NO-GO >=45 pips of the 
  19:00-03:00 EST Asian range (USDJPY pip = 0.01); NA before 03:00 EST.
- **P90 print**: M5 candle body >= hour-bucket threshold (4.1-6.2 pips) in 2-11 AM EST.
- **Tier impulse**: P90 print that also breaches the Asian band (dual-engine overlap).
- **Asian midpoint**: (ar_high + ar_low) / 2; crosses/reclaims in the window.
- **Rekey**: 132% Asian-range violation (canonical violation_long/short).

Observation window: t0 -> t0+120m in causal buckets 0-15/15-30/30-45/45-60/60-90/90-120.

## 3. Coverage context

Daily tier distribution (discovery, A+B): NO-GO 221, NA 100, T3 69, T2 56, T1 13
Events inside the 2-11 AM EST P90 window: 282/459 = 61%.
Any P90 print: 48% | any tier impulse: 26% | any rekey: 10% | any midpoint cross: 36%.

## 4. Candidate classification (brief section 26)

| id | class | function | disc N | cov | exp | base | uplift | p | q | conf exp | OOS exp | verdict |
|----|-------|----------|--------|-----|-----|------|--------|---|---|----------|---------|---------|
| A_aligned_tier_impulse | D | ACTIVATION | 23 | 0.11 | 12.85 | 9.95 | 2.90 | 0.65 | 0.954 | -3.36 | 18.84 | EXPLORATORY_LOW_SUPPORT |
| A_tier_count_ge2 | D | REGIME | 34 | 0.16 | 6.32 | 9.95 | -3.63 | 0.51 | 0.954 | 8.82 | 17.31 | CONFIRMATION_LOW_SUPPORT |
| A_aligned_p90 | B | ACTIVATION | 77 | 0.37 | 12.65 | 9.95 | 2.70 | 0.48 | 0.954 | 6.54 | 10.96 | CONFIRMED |
| A_p90_count_ge2 | B | EXIT | 78 | 0.37 | 10.19 | 9.95 | 0.24 | 0.95 | 0.954 | 7.03 | 13.08 | CONFIRMED |
| A_no_tier_60m | B | VETO | 174 | 0.83 | 10.59 | 9.95 | 0.64 | 0.84 | 0.954 | 8.43 | 8.92 | CONFIRMED |
| A_tier_no_p90_60m | D | VETO | 9 | 0.04 | 25.31 | 9.95 | 15.36 | nan | None | 7.37 | 13.76 | EXPLORATORY_LOW_SUPPORT |
| A_tier_p90_no_midpoint | D | VETO | 42 | 0.20 | 10.64 | 9.95 | 0.69 | 0.90 | 0.954 | 5.84 | 14.30 | CONFIRMATION_LOW_SUPPORT |
| A_opposed_rekey_after_aligned | D | EXIT | 0 | 0.00 | nan | 9.95 | nan | nan | None | nan | nan | EXPLORATORY_LOW_SUPPORT |
| A_rekey_present | D | REGIME | 21 | 0.10 | -1.63 | 9.95 | -11.58 | 0.08 | 0.954 | -6.94 | 6.78 | EXPLORATORY_LOW_SUPPORT |
| A_aligned_rekey | D | SIZING | 2 | 0.01 | -22.54 | 9.95 | -32.49 | nan | None | nan | 10.35 | EXPLORATORY_LOW_SUPPORT |
| A_midpoint_aligned_60m | D | TIMING | 51 | 0.24 | 8.44 | 9.95 | -1.51 | 0.76 | 0.954 | 27.69 | 10.72 | CONFIRMATION_LOW_SUPPORT |
| A_midpoint_start_aligned | D | REGIME | 77 | 0.37 | 6.17 | 9.95 | -3.78 | 0.36 | 0.954 | 1.09 | 7.93 | CONFIRMATION_LOW_SUPPORT |
| A_tier_t1 | D | REGIME | 4 | 0.02 | -15.70 | 9.95 | -25.65 | nan | None | nan | 8.14 | EXPLORATORY_LOW_SUPPORT |
| A_tier_t3 | D | REGIME | 33 | 0.16 | 11.36 | 9.95 | 1.41 | 0.81 | 0.954 | 16.23 | 1.81 | CONFIRMATION_LOW_SUPPORT |
| A_score_ge2 | D | ACTIVATION | 9 | 0.04 | 15.80 | 9.95 | 5.85 | nan | None | 7.37 | 19.35 | EXPLORATORY_LOW_SUPPORT |
| A_score_le_m2 | D | VETO | 16 | 0.08 | 11.91 | 9.95 | 1.96 | 0.80 | 0.954 | 4.32 | 13.92 | EXPLORATORY_LOW_SUPPORT |
| A_commitment_ge50 | D | ACTIVATION | 39 | 0.19 | 16.00 | 9.95 | 6.05 | 0.24 | 0.954 | 8.68 | 11.07 | CONFIRMATION_LOW_SUPPORT |
| A_opposition_ge50 | D | VETO | 48 | 0.23 | 11.74 | 9.95 | 1.79 | 0.70 | 0.954 | 5.93 | 18.22 | CONFIRMATION_LOW_SUPPORT |
| A_high_density | D | EXIT | 48 | 0.23 | 6.86 | 9.95 | -3.09 | 0.49 | 0.954 | 6.04 | 12.87 | CONFIRMATION_LOW_SUPPORT |
| B_aligned_tier_impulse | D | ACTIVATION | 32 | 0.13 | 9.90 | 7.56 | 2.33 | 0.70 | 0.926 | 8.51 | 22.05 | CONFIRMATION_LOW_SUPPORT |
| B_tier_count_ge2 | D | REGIME | 47 | 0.19 | 9.52 | 7.56 | 1.96 | 0.70 | 0.926 | 8.54 | 11.79 | CONFIRMATION_LOW_SUPPORT |
| B_aligned_p90 | D | ACTIVATION | 105 | 0.42 | 8.90 | 7.56 | 1.34 | 0.72 | 0.926 | 7.06 | 12.29 | CONFIRMATION_LOW_SUPPORT |
| B_p90_count_ge2 | D | EXIT | 102 | 0.41 | 9.11 | 7.56 | 1.55 | 0.69 | 0.926 | 6.33 | 9.78 | CONFIRMATION_LOW_SUPPORT |
| B_no_tier_60m | B | VETO | 194 | 0.78 | 7.46 | 7.56 | -0.10 | 0.98 | 0.979 | 9.99 | 4.77 | CONFIRMED |
| B_tier_no_p90_60m | D | VETO | 3 | 0.01 | 13.27 | 7.56 | 5.71 | nan | None | 38.04 | 39.90 | EXPLORATORY_LOW_SUPPORT |
| B_tier_p90_no_midpoint | D | VETO | 54 | 0.22 | 8.80 | 7.56 | 1.24 | 0.81 | 0.926 | 12.94 | 15.93 | CONFIRMATION_LOW_SUPPORT |
| B_opposed_rekey_after_aligned | D | EXIT | 0 | 0.00 | nan | 7.56 | nan | nan | None | nan | nan | EXPLORATORY_LOW_SUPPORT |
| B_rekey_present | D | REGIME | 25 | 0.10 | 3.86 | 7.56 | -3.71 | 0.56 | 0.926 | 6.53 | 1.66 | EXPLORATORY_LOW_SUPPORT |
| B_aligned_rekey | D | SIZING | 13 | 0.05 | 11.01 | 7.56 | 3.44 | 0.71 | 0.926 | nan | 31.41 | EXPLORATORY_LOW_SUPPORT |
| B_midpoint_aligned_60m | D | TIMING | 51 | 0.20 | 8.90 | 7.56 | 1.34 | 0.79 | 0.926 | -4.31 | 6.99 | CONFIRMATION_LOW_SUPPORT |
| B_midpoint_start_aligned | B | REGIME | 85 | 0.34 | 7.06 | 7.56 | -0.50 | 0.90 | 0.959 | 7.40 | 9.05 | CONFIRMED |
| B_tier_t1 | D | REGIME | 9 | 0.04 | -2.18 | 7.56 | -9.74 | nan | None | nan | 3.32 | EXPLORATORY_LOW_SUPPORT |
| B_tier_t3 | D | REGIME | 36 | 0.14 | -1.64 | 7.56 | -9.21 | 0.09 | 0.926 | 64.10 | 6.49 | CONFIRMATION_LOW_SUPPORT |
| B_score_ge2 | D | ACTIVATION | 13 | 0.05 | 19.19 | 7.56 | 11.63 | 0.19 | 0.926 | 7.37 | 29.08 | EXPLORATORY_LOW_SUPPORT |
| B_score_le_m2 | D | VETO | 14 | 0.06 | 17.31 | 7.56 | 9.75 | 0.26 | 0.926 | 32.68 | 1.46 | EXPLORATORY_LOW_SUPPORT |
| B_commitment_ge50 | D | ACTIVATION | 48 | 0.19 | 12.93 | 7.56 | 5.36 | 0.29 | 0.926 | 9.37 | 5.63 | CONFIRMATION_LOW_SUPPORT |
| B_opposition_ge50 | D | VETO | 56 | 0.22 | 11.15 | 7.56 | 3.58 | 0.44 | 0.926 | 8.44 | 10.83 | CONFIRMATION_LOW_SUPPORT |
| B_high_density | D | EXIT | 62 | 0.25 | 5.58 | 7.56 | -1.98 | 0.65 | 0.926 | 16.23 | 9.14 | CONFIRMATION_LOW_SUPPORT |

## 5. Key findings

1. **No primitive materially improves expectancy at research grade.** phase_9_optimization_cleared = false. Every candidate fails the materiality gate (|uplift| >= 2 bps AND discovery p <= 0.10) with coverage >= 30% plus confirmation/OOS agreement.
2. **Rekey (132% violation) is the strongest negative primitive.** In family A, rekey present in the window => expectancy collapse (-11.6 bps relative, p=0.084, n=21, coverage 10%). Directionally consistent in B. Under-powered; a Phase-9 VETO/EXIT candidate, not a promotion.
3. **T3 (wide Asian range) degrades EUR liquidation routing.** Family B T3 expectancy 4.58 vs ALL 8.66 bps (candidate B_tier_t3: -9.2, p=0.088). Supports the 'T3 = exhausted variance' hypothesis directionally; not significant.
4. **T1 is structurally absent** in this USDJPY sample (16/890 events). The canonical T1 bucket (<20 pip Asian range) rarely occurs; the edge cannot concentrate on T1 because T1 barely exists. NO-GO (>45 pips) is the modal day state (58%).
5. **Equal-weight primitive score is monotonically increasing** (Spearman 0.40 family A / 0.45 family B, discovery). Score 2 cells: A +15.8 bps (89% win, n=9), B +20.3 bps (100% win, n=10) vs score 0 A +8.9 / B +7.3. Per brief section 20, the score is marked as a Phase-9 optimization candidate -- no weights optimized here.
6. **P90 adds no incremental information beyond the tier impulse.** Tier impulse = P90 body + band breach, so the +p90 stage is identical to the +tier stage by construction (P8_INCREMENTAL_INFORMATION.csv).
7. **Sequence grammar is midpoint-dominated and empty at support.** No sequence with N >= 30; the top cells are small (n <= 10) and unstable. Repeated opposed rekey (RO-RO-RO-RO) shows 40% win rate.
8. **Saturation:** no monotone benefit from more prints; tier/P90 count cells are flat-to-noisy (P8_SATURATION_STUDY.csv). More prints do not monotonically help.

## 6. Statistical discipline

- Discovery (2023-07-01..2024-12-31) only for pattern search; confirmation (2025-01-01..2025-06-30) for frozen-candidate check; RELATIONSHIP_CONFIRMED_OOS (2025-07-01..2026-05-31) evaluated ONCE.
- Bootstrap 90% CIs (fixed seed, event-level) on every reported estimate.
- BH-FDR within each family's logical test group (q reported per candidate).
- Subperiod stability (2023H2/2024H1/2024H2/2025H1) for candidates.
- No train/test shuffle; no repeated OOS probing; no parameter rescue.

## 7. Decision

- **phase_9_optimization_cleared = FALSE**
- Strong (A): 0 | Conditional (B): 5 | Exploratory (C): 0 | Reject (D): 33
- Eligible for human review as Phase-9 optimization candidates (not promoted): A_rekey_present (VETO/EXIT), B_tier_t3 (REGIME), A/B commitment_ge50 and aligned P90 (ACTIVATION), equal-weight primitive score (SIZING/ACTIVATION).

## 8. Stop condition

STOPPED per brief section 27: no threshold optimization, no strategy assembly, no CEREBUS filters applied to the sealed baseline, no deploy, no MT5. Awaiting human review for Phase 9 direction.
