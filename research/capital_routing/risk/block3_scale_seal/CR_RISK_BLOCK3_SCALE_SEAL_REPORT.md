# CR-RISK-BLOCK-III-SCALE-SEAL -- Report

- **Status:** PASS  
- **Base commit:** a58f84833b920175f88a5e5c6c127a12bd5cdafe (frontier 0edb1c72f2a42ab6305ae9cd34071019d47f29a2)  
- Events 890 (A 432 / B 458); episodes 482; max concurrency 3  

## Sealed operating bands (evidence-backed)

| region | scale band | frontier classification |
|---|---|---|
| CONSERVATIVE | 0.25-0.50 | ROBUST_LOW_SCALE |
| **ROBUST CORE** | **0.75-1.00** | ROBUST_GROWTH_REGION |
| AGGRESSIVE | 1.50-2.00 | AGGRESSIVE_FRAGILE |
| STRESS ONLY | 3.00 | stress / never promoted |

## Knee band

- Knee interval: **[1.0, 1.5]** (modal over recommendation allocs x primary schemes; 53 cells)  
- Robust core (0.75-1.00) sits at or below the knee start -> knee_seal_pass = True  

## Adjacent-scale cost (incremental, operating heat, 100% edge)

| step | d median CAGR | d p95 DD | d P(DD>=10) | d P(DD>=15) | flag |
|---|---|---|---|---|---|
| 0.50->0.75 | +0.1818 | +0.0156 | +0.0000 | +0.0000 | OK |
| 0.75->1.00 | +0.2058 | +0.0155 | +0.0003 | +0.0000 | OK |
| 1.00->1.50 | +0.4955 | +0.0305 | +0.0273 | +0.0001 | OK |
| 1.50->2.00 | +0.6319 | +0.0300 | +0.2176 | +0.0062 | TAIL_ACCELERATION |

Table shows A1_70_30 / block (preferred research default). The seal evaluates ALL operating cells (A0+A1 x block+episode): the boundary jump at 1.00->1.50 is present for every operating cell under the relative rule (boundary P(DD>=10) exceeds the inside-core max for the same alloc+scheme); the 1.50->2.00 step accelerates absolutely under the pre-declared 5pp threshold.

- Adjacent-scale seal: core accelerating cells 0 (must be 0); boundary accelerating cells 3 (must be > 0); boundary scheme agreement True -> adjacent_scale_seal_pass = True  

## Allocation review (f=1.00, operating heat, block+episode)

| alloc | hist CAGR% | hist maxDD% | blk med CAGR | ep med CAGR | blk p95 DD | ep p95 DD | P(DD>=10) | P(DD>=15) | tail eff | 75% surv |
|---|---|---|---|---|---|---|---|---|---|---|
| A0_50_50 | 70.6 | 5.2 | 0.704 | 0.702 | 0.076 | 0.083 | 0.0072 | 0.0000 | 8.84 | Y |
| A1_70_30 | 69.0 | 5.0 | 0.690 | 0.686 | 0.063 | 0.075 | 0.0024 | 0.0000 | 10.00 | Y |
| A2_100_0_A | 71.7 | 7.5 | 0.713 | 0.708 | 0.087 | 0.107 | 0.0463 | 0.0015 | 7.31 | Y |

Allocation transitions (50/50 -> 70/30 -> A-only, f=1.00):

- A0_50_50->A1_70_30: d median CAGR -0.015, d p95 DD -0.011, d P(DD>=10) -0.005, d P(DD>=15) +0.0000  
- A1_70_30->A2_100_0_A: d median CAGR +0.023, d p95 DD +0.028, d P(DD>=10) +0.044, d P(DD>=15) +0.0015  

## Heat review (paired common random numbers, operating band)

| heat | d median CAGR | d median DD | P(H1 DD < H0) | d P(DD>=10) | d P(DD>=15) | rej% | cap util | verdict |
|---|---|---|---|---|---|---|---|---|
| H1-1.00-REJ | -0.0023 | -0.0147 | 0.802 | -0.0078 | -0.0001 | 0.044 | 0.943 | RETAIN_OPERATING_REFERENCE |
| H1-1.50-REJ | +0.0008 | -0.0009 | 0.361 | -0.0014 | -0.0000 | 0.004 | 0.995 | NOT_RETAINED_NO_PROTECTION |
| H1-2.00-REJ | -0.0002 | -0.0004 | 0.317 | -0.0014 | -0.0000 | 0.002 | 0.997 | NOT_RETAINED_NO_PROTECTION |
| H1-3.00-REJ | +0.0000 | +0.0000 | 0.000 | +0.0000 | +0.0000 | 0.000 | 1.000 | NOT_RETAINED_NEVER_BINDS |

- Heat architecture status: **H1-1.00-REJ retained as operating reference; H0 documented sufficient**  

## Edge retention (operating band cells)

- survives_100: True  
- survives_75: True  
- survives_50: True  
- survives_25: False  
- 25% edge = ALPHA-LOSS BOUNDARY (not required to survive; risk controls are not expected to rescue destroyed expectancy)  

## Robust core risk contract

- median CAGR: [0.4814, 0.7038]  
- p95 max DD: [0.0474, 0.0829]  
- P(DD>=10): [0.0, 0.0072]  
- P(DD>=15): [0.0, 0.0]  
- P(technical ruin) max: 0.0  
- dependency-sensitive cells in band: 0  

## Dependency agreement (block vs episode)

- block_episode_agreement_pass = True  

## Preferred research default (NOT production sizing)

- {'allocation': 'A1_70_30', 'heat_architecture': 'H1-1.00-REJ', 'f_total_pct': 1.0, 'role': 'PREFERRED_RESEARCH_DEFAULT for demo/execution translation research ONLY -- not production sizing, not live authorization', 'justification': 'best tail-efficiency allocation (A1_70_30) at the top of the robust core (0.75-1.00), at the knee start [1.0, 1.5], under the operating heat H1-1.00-REJ'}  

## Authorizations (all locked)

- best cell selected: FALSE (band only)  
- Kelly used / DD-adaptive used: FALSE / FALSE  
- production scale / deployment / MT5: FALSE / FALSE / FALSE  

## Next checkpoint

- **CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING** (authorized: False)  