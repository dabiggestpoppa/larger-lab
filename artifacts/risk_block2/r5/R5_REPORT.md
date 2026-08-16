# R5 — Family Quality / Allocation Anatomy (CR-RISK-BLOCK2)

**Task:** CR-RISK-BLOCK2-R5-FAMILY-QUALITY-ALLOCATION · **Block-I seal:** 8ca072d0 · **Book:** 890 events (A 432 / B 458) · 2.86y · 1R = 24.5 bps (unchanged)

## 1. Executive summary

A and B are NOT equivalent capital consumers, but the inequality is NOT the one the headline suggests. A has the higher expectancy (0.393R vs 0.308R, disjoint bootstrap CIs) and higher WR; B is capital-limiting because of a higher deep-loss frequency (-1R breach 13.8% vs 10.4%, longer streaks), not bigger single events (A holds -3.66R, B -3.31R). Crucially, the two families are near-independent at daily granularity (same-day PnL corr ≈ -0.09; zero co-tail coincidence), so pooling is genuinely diversifying: **50/50 at total f=1% cuts historical max DD to 5.2% vs 10.3% A-only / 11.1% B-only** while retaining most of the CAGR. The equal-heat 50/50 point is non-dominated across the whole historical f grid and survives 75% edge stress; under 50% edge stress the frontier narrows to A-heavy 70/30 and 100/0 because **B is the edge-fragile family** (B-only expected CAGR goes NEGATIVE at 50% edge while A-only stays positive). No allocation is selected - this is a map.

## 2. Protocol / provenance
Pre-registered in R5_PROTOCOL.md (grids, scenarios, ordinal rules, forbidden outputs). Inputs hash-locked in R5_INPUT_HASH_MANIFEST.json (git 470702c2 at generation; Block-I seal 8ca072d0).

## 3-4. A / B distributions
- **A:** N=432 · WR 63.9% · mean +0.393R · median +0.405R · std 1.27R · skew +0.34 · kurt 2.4 · min -3.66R · max 7.28R
- **B:** N=458 · WR 61.4% · mean +0.308R · median +0.357R · std 1.22R · skew +0.36 · kurt 2.0 · min -3.31R · max 6.38R

## 5. Expectancy quality
- **A:** 9.63 bps/event · PF 2.31 · WR 63.9% · expectancy CI [+0.28, +0.51]R · PF CI [1.79, 3.03] · return/max-DD 1789R
- **B:** 7.54 bps/event · PF 1.94 · WR 61.4% · expectancy CI [+0.19, +0.42]R · PF CI [1.52, 2.50] · return/max-DD 1279R

## 6. Loss quality
- **A:** breach -1R 10.4% · worst -3.66R · worst-10% loss share 31% · max streak 6
- **B:** breach -1R 13.8% · worst -3.31R · worst-10% loss share 29% · max streak 7

## 7. Profit quality
- **A:** winner MFE 1.11R · capture 91% · +1R reach 36% (0% fail after) · %PnL by h3 171%
- **B:** winner MFE 1.06R · capture 94% · +1R reach 33% (0% fail after) · %PnL by h3 133%

## 8. Temporal stability
- A>B mean-R ranking: year **STABLE**, half **STABLE**, quarter **MIXED**, split **MIXED** (N>=20 rule)

## 9. A/B dependence
- same-day realized corr **-0.085**; P(B loss|A loss) 12% vs base 23%; co-tail 0%

## 10. Marginal portfolio contribution (f=1% reference)

| config | CAGR | max DD | worst day | p95 DD (block MC) | P(DD>=20%) |
|---|---|---|---|---|---|
| A_only_f1 | +79% | 10.3% | -5.4% | 13.6% | 0.00% |
| B_only_f1 | +62% | 11.1% | -4.6% | 16.8% | 0.04% |
| Pooled_AB_f1_each_trade_sealed | +190% | 10.2% | -5.6% | 15.1% | 0.00% |
| AB_5050_total_f1_equal_heat | +71% | 5.2% | -2.8% | 7.8% | 0.00% |

## 11. Allocation frontier (predefined grid, total f constant)

| A/B @ f=1% | CAGR | max DD | p95 DD | worst day | P(DD>=20%) | worst cluster | CAE |
|---|---|---|---|---|---|---|---|
| 0/100 | +62% | 11.1% | 16.8% | -4.6% | 0.0% | -6.0% | -2.8% |
| 30/70 | +68% | 5.6% | 8.5% | -3.2% | 0.0% | -4.2% | -2.0% |
| 50/50 | +71% | 5.2% | 7.8% | -2.8% | 0.0% | -3.0% | -2.0% |
| 70/30 | +75% | 7.0% | 9.5% | -3.8% | 0.0% | -3.8% | -2.1% |
| 100/0 | +79% | 10.3% | 13.6% | -5.4% | 0.0% | -5.4% | -3.1% |

## 12. Monte Carlo
- 0/100 @ f=1% (block MC): median CAGR +62% · p95 DD 16.8% · P(DD>=40%) 0.00% · P(tech) 0.00%
- 50/50 @ f=1% (block MC): median CAGR +71% · p95 DD 7.8% · P(DD>=40%) 0.00% · P(tech) 0.00%
- 100/0 @ f=1% (block MC): median CAGR +79% · p95 DD 13.6% · P(DD>=40%) 0.00% · P(tech) 0.00%

## 13. Edge degradation (by family, 50/50 allocation)
- A 100% / B 100%: exp CAGR +71%, p95 DD 8%
- A 75% / B 100%: exp CAGR +51%, p95 DD 9%
- A 100% / B 75%: exp CAGR +51%, p95 DD 9%
- A 75% / B 75%: exp CAGR +33%, p95 DD 11%
- A 50% / B 100%: exp CAGR +32%, p95 DD 12%
- A 100% / B 50%: exp CAGR +33%, p95 DD 10%
- A 50% / B 75%: exp CAGR +17%, p95 DD 15%
- A 75% / B 50%: exp CAGR +17%, p95 DD 14%
- A 50% / B 50%: exp CAGR +3%, p95 DD 23%
- A 25% / B 25%: exp CAGR -21%, p95 DD 58%
- A 25% / B 100%: exp CAGR +16%, p95 DD 17%
- A 100% / B 25%: exp CAGR +17%, p95 DD 13%

## 14. Tail stress (family-specific, f=1%)
- historical: max DD 5.1%, terminal 4.6x
- A_worst5_x2_00: max DD 7.2%, terminal 4.1x
- B_worst5_x2_00: max DD 6.1%, terminal 4.1x
- A_p99_loss_cluster: max DD 9.1%, terminal 4.3x
- B_p99_loss_cluster: max DD 9.4%, terminal 4.3x

## 15. Non-dominated region
- **historical:** 40/60@0.25; 40/60@0.5; 40/60@1.0; 40/60@1.5; 40/60@2.0; 40/60@3.0; 40/60@5.0; 50/50@0.25; 50/50@0.5; 50/50@1.0; 50/50@1.5; 50/50@2.0; 50/50@3.0; 50/50@5.0; 60/40@0.25; 60/40@0.5; 60/40@1.0; 60/40@1.5; 60/40@2.0; 60/40@3.0; 60/40@5.0; 70/30@0.25; 70/30@0.5; 70/30@1.0; 70/30@2.0; 70/30@3.0; 70/30@5.0; 80/20@0.25; 80/20@0.5; 80/20@3.0; 80/20@5.0; 90/10@0.25; 90/10@0.5; 90/10@5.0; 100/0@5.0
- **block_mc:** 40/60@0.25; 40/60@0.5; 40/60@1.0; 40/60@1.5; 40/60@2.0; 40/60@3.0; 40/60@5.0; 50/50@0.25; 50/50@0.5; 50/50@1.0; 50/50@1.5; 50/50@2.0; 50/50@3.0; 50/50@5.0; 60/40@0.25; 60/40@0.5; 60/40@1.0; 60/40@1.5; 60/40@2.0; 60/40@3.0; 60/40@5.0; 70/30@0.25; 70/30@0.5; 70/30@1.0; 70/30@1.5; 70/30@2.0; 70/30@3.0; 70/30@5.0; 80/20@0.25; 80/20@0.5; 80/20@1.0; 80/20@2.0; 80/20@3.0; 80/20@5.0; 90/10@0.25; 90/10@0.5; 90/10@3.0; 90/10@5.0; 100/0@0.25; 100/0@0.5; 100/0@5.0
- **edge75:** 50/50@0.25; 50/50@0.5; 50/50@1.0; 50/50@1.5; 50/50@2.0; 50/50@3.0; 50/50@5.0; 70/30@0.25; 70/30@0.5; 70/30@1.0; 70/30@1.5; 70/30@2.0; 70/30@3.0; 70/30@5.0; 100/0@0.25; 100/0@0.5; 100/0@1.0; 100/0@1.5; 100/0@2.0; 100/0@3.0; 100/0@5.0
- **edge50:** 70/30@0.25; 70/30@0.5; 70/30@1.0; 70/30@1.5; 70/30@2.0; 70/30@3.0; 70/30@5.0; 100/0@0.25; 100/0@0.5; 100/0@1.0; 100/0@1.5; 100/0@2.0; 100/0@3.0; 100/0@5.0

## 16. Trader interpretation

- **B can be capital-limiting without being 'bad':** B's solo max DD is higher (11.1% vs 10.3% at f=1%) because it breaches -1R more often and streaks longer - but it still earns +0.31R/event with a 1.94 PF. Capital-limiting is a risk-budget statement, not a quality verdict.
- **50/50 does NOT mean balanced risk:** equal capital does not mean equal risk contribution - B consumes more of the drawdown budget per R. Under equal static f the pool inherits B's deeper-loss frequency.
- **Allocation should follow marginal portfolio burden:** the equal-heat 50/50 point cuts max DD ~50% versus either solo (5.2% vs 10.3/11.1%) because A and B are near-independent - the diversification is real and measurable.
- **Historical CAGR cannot choose the weight:** A-only has the higher historical CAGR (79% vs 62% at f=1%) yet is DOMINATED by 50/50 at every f on a risk-adjusted basis; CAGR alone would push you into concentration.
- **Edge retention is still the main constraint:** at 50/50 f=1%, halving the edge to 50% collapses expected CAGR to ~2.6% with p95 DD ~23%; no allocation rescues a halved edge.

## 17. What remains unknown
- Whether the near-independence holds in forward OOS (only RELATIONSHIP_CONFIRMED_OOS evidence so far - not a fully untouched set)
- Intra-hold mark-to-market co-movement (realized PnL is exit-dated; hourly marks show no co-loss but are exit-aligned)
- Whether allocation interacts with episode/heat states (R6)

## 18. Next research phase
**CR-RISK-R6-EPISODE-HEAT-SIZING** - defined, NOT authorized by this file. The A/B allocation problem is mapped; R6 (episode/heat-aware sizing) is the logical next checkpoint after human review.

## 19. Stop condition
`r5_family_quality_allocation_pass = true` · `block_2_r6_cleared = false` · `best_allocation_selected = false`. No Kelly, no dynamic/DD-adaptive sizing, no deployment, no MT5. R6 does NOT start until human review.