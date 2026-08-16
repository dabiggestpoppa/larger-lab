# R5 PROTOCOL (pre-registered)

**Task:** CR-RISK-BLOCK2-R5-FAMILY-QUALITY-ALLOCATION · **Base:** Block-I seal 8ca072d0d9390acf581770a99ce45b333deddd8c · branch `capital-routing`

## Frozen inputs
Sealed 890-event A/B book (A 432 / B 458) rebuilt from the SAME frozen inputs as
Block I (phase_03 panel, phase_05 events, P7_5_TRADES) and cross-checked against
`risk_block1/R1_EVENT_RISK_LEDGER.csv` (row counts, family counts, total PnL).

## Predefined grids (fixed BEFORE results)
- Allocations A/B: [(0, 100), (10, 90), (20, 80), (30, 70), (40, 60), (50, 50), (60, 40), (70, 30), (80, 20), (90, 10), (100, 0)] (11 ratios, total portfolio f held constant;
  50/50 at f=1% means 0.5% A + 0.5% B per R)
- Total f: [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]%
- Edge scenarios (A,B): (1,1) (0.75,1) (1,0.75) (0.75,0.75) (0.5,1) (1,0.5)
  (0.5,0.75) (0.75,0.5) (0.5,0.5) (0.25,0.25) (0.25,1) (1,0.25)
- Stress allocations: 0/100, 30/70, 50/50, 70/30, 100/0

## Allowed
Descriptive A/B comparison; family distributional analysis; dependency /
correlation; temporal stability; overlap/marginal-risk analysis; the predefined
allocation surface; bootstrap/MC comparison; edge degradation by family; tail
stress by family; portfolio frontier mapping.

## Forbidden
Searching arbitrary weights for max CAGR; optimizing Sharpe/Calmar; selecting a
"best weight"; Kelly; dynamic allocation; signal filtering; family suppression;
threshold changes. No alpha/entry/exit/trade-management change. 1R unchanged.

## Quality-matrix ordinal rules (preregistered)
- expectancy_quality: STRONG mean_R>=0.30 / NEUTRAL >=0.20 / WEAK else
- left_tail_quality: STRONG breach_1R<=10% / NEUTRAL <=14% / WEAK else
- temporal_stability: STABLE/MIXED/UNSTABLE from year+half A>B ranking share
  (>=80% STABLE, 50-80% MIXED, else UNSTABLE)
- dependency_benefit: STRONG if 50/50 total-f=1% max DD < 0.9 * min(solo DD)
  (material diversification); NEUTRAL if within 10%; WEAK if no DD reduction
- edge_resilience: STRONG if 50%-edge exp CAGR >= 50% of full-edge at f=1%;
  NEUTRAL >= 20%; WEAK else
- marginal_dd_contribution: STRONG if removing the family raises pooled DD
  materially (it diversifies); NEUTRAL small; WEAK if it adds DD

## Determinism
Fixed seeds (MC_SEED=20260815); chronological block + R1 episode block joint
bootstrap (10,000 paths allocation MC, 5,000 stress); iid only as reference.
All probabilities in [0,1]; byte-identical re-runs verified by tests.
