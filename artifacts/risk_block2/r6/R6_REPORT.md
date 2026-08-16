# R6 â€” Episode / Heat Sizing (CR-RISK-BLOCK2)

**Task:** CR-RISK-BLOCK2-R6-EPISODE-HEAT-SIZING · **Block-I seal:** 8ca072d0 · **R5:** 150a93de · **Book:** 890 events (A 432 / B 458) · max concurrency 3 · 1R = 24.5 bps (unchanged)

## 1. Executive summary
Overlap is real but bounded in the sealed book: max concurrency 3, 26.5% of events enter with an active position, and only 20h carry 3 positions. 84.7% of in-drawdown hourly loss occurs in single-position hours, so overlap is NOT the dominant historical DD driver at 50/50. It does worsen single-day risk: the worst day (-2.8%) and worst 24h (-3.3%) both occur with 2-3 concurrent positions. Simple heat caps reduce that state-dependent risk mainly where events pile up: at A-heavy 70/30 a 1.0x gross cap cuts block-MC p95 max DD from 9.5% to 6.3% and P(DD>=10%) from 3.6% to 0.0% at ~7% CAGR cost, while at 50/50 the same cap binds only on the rare 3-position state (historical max DD unchanged at 5.2%; worst day -2.8% -> -2.6%). Same-direction caps (H2) match gross caps without being systematically better; episode budgets (H4) are redundant with H1 (H4-1.0x is strictly worse); B-family caps (H3) trim the capital-limiting family but are weaker than an equal gross cap at 70/30. Caps reject approximately fair events (WR 57-66%, positive mean R), so they buy DD reduction by cutting exposure, not by cherry-picking losers. Under 50% edge retention every policy collapses - heat caps do not rescue a halved edge. No policy is selected; the mapping is descriptive, and a Block-II seal is recommended before R7.

## 2. Provenance
Pre-registered in R6_PROTOCOL.md; inputs hash-locked in R6_INPUT_HASH_MANIFEST.json (git 1e8cc01f at generation).

## 3. Episode truth
- 12h episodes: **482**; mean events/episode 1.85; max events in one episode 10
- events in a concurrent state at entry: **27%** (2+ concurrent: 2%, 3 concurrent: 0%)
- same-direction overlap hours 367h · opposing 228h

## 4. Heat definitions
Seven concepts locked in R6_HEAT_DEFINITION_LOCK.md (per-event f, gross, net directional, family, episode, realized episode loss, CAE). Caps are multiples of base per-event f; admission is causal and f-invariant.

## 5. Baseline reproduction
H0 (unconstrained) reproduces the sealed baselines: 50/50 @ f=1% -> CAGR 71%, max DD 5.2% (R5: 71% / 5.2%); 50/50 @ f=2% -> 190% / 10.2% (R4 pooled f=1%: 190% / 10.2%); 70/30 @ f=1% -> 75% / 7.0% (R5 70/30).

## 6. Policy surface
28 pre-registered configurations: H0 + H1 gross (4 caps), H2 same-direction (3), H3 family-B (3), H4 episode budget (4), H5 hybrid (2), x treatments (REJECT full grid / SCALE subset). See R6_PROTOCOL.md.

## 7. Admission behavior (50/50, reference f=1%)
- H1-1.0x: 14/890 events rejected (2%), net R missed +1.13R, positive rejected 8, negative avoided 6

## 8. Historical frontier

| policy @ 50/50 | f | CAGR | max DD | worst day | worst ep | gross heat max |
|---|---|---|---|---|---|---|
| H0 | 1% | +71% | 5.2% | -2.8% | -3.1% | 1.50x |
| H1-1.00-REJ | 1% | +71% | 5.2% | -2.6% | -3.1% | 1.00x |
| H1-1.50-REJ | 1% | +71% | 5.2% | -2.8% | -3.1% | 1.50x |
| H2-1.00-REJ | 1% | +71% | 5.2% | -2.6% | -3.1% | 1.50x |
| H3-0.50-REJ | 1% | +63% | 5.2% | -2.8% | -2.7% | 1.50x |
| H4-1.00-REJ | 1% | +53% | 5.4% | -2.6% | -2.5% | 1.00x |
| H5-1.50-REJ | 1% | +71% | 5.2% | -2.6% | -3.1% | 1.50x |

## 9. Same/opposing-direction overlap
- **same_direction:** N=276 · mean R +0.28 · loss prob 42% · tail prob 16.3% · share of negative R 37%
- **opposing:** N=172 · mean R +0.35 · loss prob 41% · tail prob 12.2% · share of negative R 18%
- **no_overlap:** N=481 · mean R +0.41 · loss prob 34% · tail prob 9.4% · share of negative R 48%

## 10. Family episode structure
- **A_A:** 46 clusters · 108 events · mean R +0.19 · loss prob 40% · neg-R share 15%
- **A_B:** 123 clusters · 396 events · mean R +0.40 · loss prob 38% · neg-R share 43%
- **A_only:** 128 clusters · 128 events · mean R +0.40 · loss prob 36% · neg-R share 12%
- **B_B:** 59 clusters · 132 events · mean R +0.35 · loss prob 38% · neg-R share 17%
- **B_only:** 126 clusters · 126 events · mean R +0.34 · loss prob 34% · neg-R share 13%

## 11. Monte Carlo (block bootstrap, 50/50, f=1%)
- H0: median CAGR +71% · p95 max DD 7.8% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H1-1.00-REJ: median CAGR +71% · p95 max DD 7.6% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H1-1.50-REJ: median CAGR +71% · p95 max DD 7.8% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H2-1.50-REJ: median CAGR +71% · p95 max DD 7.8% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H3-0.75-REJ: median CAGR +63% · p95 max DD 6.9% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H4-1.50-REJ: median CAGR +70% · p95 max DD 7.8% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%
- H5-1.50-REJ: median CAGR +70% · p95 max DD 7.6% · P(DD>=20%) 0.0% · P(DD>=40%) 0.00% · tech ruin 0.00%

## 12. Edge degradation (50/50, f=1%, block MC)
- H0 A 100%/B 100%: exp CAGR +72% · p95 DD 8%
- H0 A 75%/B 75%: exp CAGR +33% · p95 DD 10%
- H0 A 50%/B 100%: exp CAGR +32% · p95 DD 11%
- H0 A 100%/B 50%: exp CAGR +33% · p95 DD 10%
- H0 A 50%/B 50%: exp CAGR +3% · p95 DD 23%
- H0 A 25%/B 25%: exp CAGR -21% · p95 DD 58%
- H0 A 75%/B 50%: exp CAGR +17% · p95 DD 13%
- H0 A 50%/B 75%: exp CAGR +17% · p95 DD 14%
- H1-1.50-REJ A 100%/B 100%: exp CAGR +72% · p95 DD 8%
- H1-1.50-REJ A 75%/B 75%: exp CAGR +33% · p95 DD 10%
- H1-1.50-REJ A 50%/B 100%: exp CAGR +32% · p95 DD 11%
- H1-1.50-REJ A 100%/B 50%: exp CAGR +33% · p95 DD 10%
- H1-1.50-REJ A 50%/B 50%: exp CAGR +3% · p95 DD 23%
- H1-1.50-REJ A 25%/B 25%: exp CAGR -21% · p95 DD 58%
- H1-1.50-REJ A 75%/B 50%: exp CAGR +17% · p95 DD 13%
- H1-1.50-REJ A 50%/B 75%: exp CAGR +17% · p95 DD 14%

## 13. Tail stress (50/50, f=1%)
- H0 insert_worst_1: max DD 5.2%
- H1-1.00-REJ insert_worst_1: max DD 5.2%
- H2-1.50-REJ insert_worst_1: max DD 5.2%

## 14. Rejected-event audit
- H1-1.0x rejected: N=14 · mean R +0.16 · WR 57% · PF 1.59 · share B 64%

## 15. Temporal stability
Rejection behavior is stable across inner_sel/inner_val/OOS and years (see R6_HEAT_TEMPORAL_STABILITY.csv); no policy helps only one period.

## 16. Non-dominated policies
- **historical_50:** H0; H1-1.50-REJ; H1-2.00-REJ; H1-3.00-REJ; H1-1.50-SCA; H1-2.00-SCA; H2-1.50-REJ; H2-2.00-REJ; H2-1.50-SCA; H5-2.00-REJ; H5-2.00-SCA; H3-0.75-SCA
- **historical_70:** H1-1.00-SCA; H2-1.00-REJ; H3-0.50-SCA; H4-1.00-REJ; H4-3.00-REJ; H5-1.50-REJ
- **blockmc_50:** H3-0.75-REJ; H5-1.50-REJ; H1-1.00-REJ; H1-2.00-REJ; H3-0.50-REJ; H4-1.00-REJ
- **blockmc_70:** H1-1.50-REJ; H0; H2-1.00-REJ; H3-0.50-REJ
- **edge75:** H0; H1-1.00-REJ; H1-1.50-REJ; H2-1.50-REJ; H3-0.75-REJ
- **edge50:** H1-1.00-REJ; H3-0.75-REJ
- **tail_insert:** H0; H1-1.50-REJ; H2-1.50-REJ

## 17. Complexity comparison
Levels: H0=0, H1=1, H2/H3=2, H4=3, H5=4. Simpler rules deliver most of the benefit; H4 (episode budget) is largely redundant with H1.

## 18. Trader interpretation
- **'1% event risk' with 2 trades overlapping** means ~2% gross heat: a -3R trade at 1% event f costs ~-3%; two simultaneous -3R trades cost ~-6% of the account. The worst day at 50/50 f=1% is -2.8% (2 concurrent) and the worst 24h is -3.3% (3 concurrent) - overlap makes single-day risk worse than single-position days.
- **Opposing trades are not free:** A (long) and B (short) overlap carries the same gross heat; R5 showed the families are near-independent so opposing overlap does not cancel risk - it adds two independent bets (12.2% tail-loss prob vs 9.4% for non-overlapping events).
- **When heat becomes dangerous:** three concurrent events occur only ~20h in the whole book and drive 1.0% of in-drawdown loss at 50/50; a 1.0x gross cap removes the 3-position state, but the historical max DD (5.2%) is set by single/2-position days and does not move.
- **Where caps DO matter:** in resampled space at A-heavy 70/30, where event piles can repeat - a 1.0x gross or same-direction cap cuts block-MC p95 DD 9.5% -> 6.3% and P(DD>=10%) 3.6% -> 0.0% at ~7% CAGR cost.
- **B heat treatment:** B is capital-limiting (R5), but H3 is weaker than an equal gross cap at 70/30 (p95 DD 9.07% vs 6.26%) and costs ~11% CAGR at 50/50 - B-specific caps are supported but not required.
- **What caps sacrifice:** at 50/50 f=1%, H1-1.0x rejects only the 14 events entering the 3-way state (net +1.1R missed); H3-0.5x rejects 73 (net +14.6R missed); H4-1.0x rejects 180 (net +31.9R missed) and is dominated - caps buy tail reduction, not return preservation.
- **Are simple caps sufficient:** yes - a single static 1.0x gross/same-direction cap plus family allocation addresses the material overlap risk; episode budgets add nothing and B-specific treatment is optional.
- **Why Kelly still comes later:** heat caps are exposure limits, not growth rules; Kelly (R8) sits after R7 (DD-adaptive) and both remain unauthorized.

## 19. What remains unknown
- whether caps retain their relative ranking in forward OOS (only RELATIONSHIP_CONFIRMED_OOS evidence so far)
- interaction of heat caps with DD-adaptive / Kelly sizing (R7/R8)
- microstructure slippage under concurrent entries (not modeled)

## 20. R7 readiness
Simple static 1.0x heat caps + family allocation address the material overlap risk (the resampled 70/30 tail collapses with a static cap), so per plan XXXIV the recommended next step is a **Block-II intermediate seal**, not an automatic R7. R7 (DD-adaptive) remains defined and researchable but is NOT authorized by this file.

## 21. Stop condition
`r6_episode_heat_sizing_pass = true` · `best_heat_policy_selected = false` · `R7_authorized = false`. No Kelly, no DD-adaptive, no deployment, no MT5. R7 does NOT start until human review.

## 22. Required questions (XXVII, Q1-Q14)
**Q1.** 71% of events participate in a multi-event 12h episode; 27% enter while at least one other position is already active.
**Q2.** 15.3% of in-drawdown hourly loss occurs with 2+ concurrent positions (84.7% is single-position). Multi-event overlap is NOT the dominant historical DD driver.
**Q3.** MIXED. Gross heat materially worsens single-day/24h tail risk (worst day -2.8% with 2 concurrent, worst 24h -3.3% with 3 concurrent) but is not the dominant hourly-DD driver (85% of in-drawdown loss is single-position).
**Q4.** Conditional. At A-heavy 70/30 a 1.0x gross cap cuts block-MC p95 max DD 9.5% -> 6.3% and P(DD>=10%) 3.6% -> 0.0% at 5.4pp median-CAGR cost; at 50/50 it barely binds (14 events, worst day -2.8% -> -2.6%, max DD unchanged at 5.2%).
**Q5.** Same-direction overlap is the worst overlap class: tail-loss prob 16.3% vs opposing 12.2% vs no-overlap 9.4%; mean R +0.28 vs +0.35 vs +0.41. Yes, it is materially worse than opposing overlap.
**Q6.** YES. Opposing positions still consume meaningful tail risk: opposing tail-loss prob 12.2% vs no-overlap 9.4% - near-independent families do not cancel.
**Q7.** MIXED. A B-family cap is supported as a mechanism (B is capital-limiting) but is weaker than an equal gross cap at 70/30 (p95 DD 9.1% vs 6.3%) and costs ~8pp CAGR at 50/50 - supported, not required.
**Q8.** YES at 50/50. H3-0.5x rejects 73 events (net +14.6R missed) and costs ~8pp CAGR (71% -> 63%) with no max-DD reduction (5.2%), i.e. it destroys A/B diversification without buying tail reduction.
**Q9.** No. Episode budgets are redundant with instantaneous gross caps: H4-1.0x is strictly worse than H1-1.0x (rejects 180 vs 14, CAGR 53% vs 71%, max DD 5.4% vs 5.2%).
**Q10.** Net R missed at 50/50 f=1% (tightest cap per family): H1 gross +1.13R, H2 same-direction +1.21R, H3 B-family +14.57R, H4 episode +31.88R, H5 combined +1.21R.
**Q11.** Non-dominated at 75% retained edge: H0, H1-1.00-REJ, H1-1.50-REJ, H2-1.50-REJ, H3-0.75-REJ.
**Q12.** Non-dominated at 50% retained edge: H1-1.00-REJ, H3-0.75-REJ.
**Q13.** No. No heat constraint materially outperforms static 50/50 or 70/30 family allocation; the most state-dependent policy (H4) is redundant or worse than a static gross cap.
**Q14.** No. Simple static heat caps + family allocation address the material overlap risk, so the evidence supports a Block-II intermediate seal rather than automatically building R7 drawdown-adaptive sizing.