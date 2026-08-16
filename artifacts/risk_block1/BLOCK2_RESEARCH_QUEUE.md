# BLOCK-II RESEARCH QUEUE (defined, NOT authorized)

Sequence derived from Block-I evidence. No phase starts until human review
clears Block I and authorizes the individual checkpoint.

| phase | question | inputs | allowed outputs | forbidden optimization | review gate |
|---|---|---|---|---|---|
| R5 Family quality/allocation anatomy | Is B's extra downside real per unit of edge, and does A/B risk separation justify unequal sizing? | R1 ledger, R2/R3 family tables, R4 family frontier | family risk/return quality tables, allocation *descriptions* | any allocation change to the strategy | human review before any weighting |
| R6 Concurrency / episode-aware sizing | Do clustered events or overlap states warrant per-state risk scaling? | R1 concurrency + episodes, R2/R3 overlap/rank tables | exposure-state risk tables | implementing heat caps or rank filters | human review |
| R7 Drawdown-adaptive sizing | Does reducing f after DD improve survival vs static? | R4 MC paths, R4 DD distributions | simulated DD-adaptive comparisons | choosing a DD rule from holdout | human review |
| R8 Kelly / fractional Kelly | What is the theoretical growth-optimal f under the measured dependency structure? | R4 expectancy/var/cov, R2 streaks, R1 clusters | Kelly estimates with dependency caveats | applying Kelly live | human review |
| R9 Hybrid risk engine | Which static/dynamic policies combine best? | R5-R8 outputs | policy tournament on development data | any parameter chosen on OOS | human review + forward shadow validation |

Priority rationale: family and dependency structure must be understood before
Kelly; DD adaptation needs the MC/ruin baseline first; the hybrid engine is the
final comparison layer.
