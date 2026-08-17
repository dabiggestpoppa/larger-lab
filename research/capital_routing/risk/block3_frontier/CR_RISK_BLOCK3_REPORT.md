# CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER -- Report

- **Status:** PASS  
- **Base commit:** 0edb1c72f2a42ab6305ae9cd34071019d47f29a2  
- Events 890 (A 432 / B 458); episodes 482  

## Integrity

- R6 MC regression: PASS (max_abs_diff 2.78e-17)  
- H0 reference nonregression: PASS  
- MC convergence: PASS  
- Common random numbers: PASS (one canonical bank per scheme)  

## Surface

- Historical cells: 560  
- MC rows: 1680 (560 cells x 3 schemes)  
- Paths: block 10000 / episode 10000 / iid 2000  

## Edge survival (both primary schemes must survive)

| alloc | heat | f% | 100% | 75% | 50% | 25% | region |
|---|---|---|---|---|---|---|---|
| A0_50_50 | H0 | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-1.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-1.50-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-2.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-3.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H0 | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-1.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-1.50-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-2.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-3.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H0 | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-1.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-1.50-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-2.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-3.00-REJ | 0.25 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H0 | 0.25 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.00-REJ | 0.25 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.50-REJ | 0.25 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-2.00-REJ | 0.25 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-3.00-REJ | 0.25 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A0_50_50 | H0 | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-1.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-1.50-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-2.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A0_50_50 | H1-3.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H0 | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-1.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-1.50-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-2.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A1_70_30 | H1-3.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H0 | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-1.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-1.50-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-2.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A2_100_0_A | H1-3.00-REJ | 0.50 | Y | Y | Y | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H0 | 0.50 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.00-REJ | 0.50 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.50-REJ | 0.50 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-2.00-REJ | 0.50 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-3.00-REJ | 0.50 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A0_50_50 | H0 | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-1.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-1.50-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-2.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-3.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H0 | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-1.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-1.50-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-2.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-3.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H0 | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-1.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-1.50-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-2.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-3.00-REJ | 0.75 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A3_0_100_B | H0 | 0.75 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.00-REJ | 0.75 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-1.50-REJ | 0.75 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-2.00-REJ | 0.75 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A3_0_100_B | H1-3.00-REJ | 0.75 | Y | Y | n | n | ROBUST_LOW_SCALE |
| A0_50_50 | H0 | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-1.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-1.50-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-2.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A0_50_50 | H1-3.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H0 | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-1.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-1.50-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-2.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A1_70_30 | H1-3.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H0 | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-1.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-1.50-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-2.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A2_100_0_A | H1-3.00-REJ | 1.00 | Y | Y | Y | n | ROBUST_GROWTH_REGION |
| A3_0_100_B | H0 | 1.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.00-REJ | 1.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.50-REJ | 1.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-2.00-REJ | 1.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-3.00-REJ | 1.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A0_50_50 | H0 | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.50-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-2.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-3.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H0 | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.50-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-2.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-3.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H0 | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.50-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-2.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-3.00-REJ | 1.50 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A3_0_100_B | H0 | 1.50 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.00-REJ | 1.50 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.50-REJ | 1.50 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-2.00-REJ | 1.50 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-3.00-REJ | 1.50 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A0_50_50 | H0 | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.50-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-2.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-3.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H0 | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.50-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-2.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-3.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H0 | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.50-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-2.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-3.00-REJ | 2.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A3_0_100_B | H0 | 2.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.00-REJ | 2.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.50-REJ | 2.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-2.00-REJ | 2.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-3.00-REJ | 2.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A0_50_50 | H0 | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-1.50-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-2.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A0_50_50 | H1-3.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H0 | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-1.50-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-2.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A1_70_30 | H1-3.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H0 | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-1.50-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-2.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A2_100_0_A | H1-3.00-REJ | 3.00 | Y | Y | Y | n | AGGRESSIVE_FRAGILE |
| A3_0_100_B | H0 | 3.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.00-REJ | 3.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-1.50-REJ | 3.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-2.00-REJ | 3.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |
| A3_0_100_B | H1-3.00-REJ | 3.00 | Y | Y | n | n | FRAGILE_HIGH_SCALE |

## Risk envelopes (consensus = block AND episode)

- consensus_p95_E5: FAIL  
- consensus_p99_E5: FAIL  
- consensus_p95_E10: FAIL  
- consensus_p99_E10: FAIL  
- consensus_p95_E15: FAIL  
- consensus_p99_E15: FAIL  
- consensus_p95_E20: FAIL  
- consensus_p99_E20: FAIL  
- consensus_p95_E25: FAIL  
- consensus_p99_E25: FAIL  
- consensus_p95_E30: FAIL  
- consensus_p99_E30: FAIL  

## Dependency-sensitive cells: 12 of 560  

## Selections / authorizations (all locked)

- best scale / allocation / heat cap selected: **FALSE**  
- production configuration selected: **FALSE**  
- deployment / MT5 authorized: **FALSE**  
- Kelly: **UNSTABLE_REFERENCE**, not used for selection, not authorized  

## Next checkpoint

- **CR-RISK-BLOCK-III-SCALE-SEAL** (authorized: False)  