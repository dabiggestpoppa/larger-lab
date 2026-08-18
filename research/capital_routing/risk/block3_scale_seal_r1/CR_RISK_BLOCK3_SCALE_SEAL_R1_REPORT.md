# CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE -- Report

- **Status:** PASS  
- **block3_scale_seal_pass:** True  
- **Base commit:** 78dca3a7453205241bdbe935b985e3e7be7b8144  

## Defects repaired

- **Defect 1:** `block3_scale_seal_pass` now requires `frontier_nonregression_pass` AND every other required gate (block/episode agreement, knee seal, adjacent-scale seal, 100% edge, 75% edge) plus no prohibited authorization state.  
- **Defect 2:** `status` is DERIVED from the pass -- never hardcoded.  
- **Fail-closed auth invariants:** kelly / DD-adaptive / production / deployment / MT5 all remain FALSE and any TRUE blocks PASS.  
- **Gate reasons:** `seal_gate_failures` / `seal_gate_passes` are explicit machine-readable fields.  

## Positive nonregression (science frozen)

- nonregression_pass = True (18 fields recomputed from the frozen frontier inputs and compared to the sealed artifacts AND the frozen brief expectations)  

- conservative_scale_band: recomputed [0.25, 0.5] | expected [0.25, 0.5] | matches_expected True | matches_sealed True  
- robust_core_scale_band: recomputed [0.75, 1.0] | expected [0.75, 1.0] | matches_expected True | matches_sealed True  
- aggressive_scale_band: recomputed [1.5, 2.0] | expected [1.5, 2.0] | matches_expected True | matches_sealed True  
- stress_scale_band: recomputed [3.0, 3.0] | expected [3.0, 3.0] | matches_expected True | matches_sealed True  
- knee_band: recomputed [1.0, 1.5] | expected [1.0, 1.5] | matches_expected True | matches_sealed True  
- allowed_allocations: recomputed ['A0_50_50', 'A1_70_30'] | expected ['A0_50_50', 'A1_70_30'] | matches_expected True | matches_sealed True  
- operating_heat: recomputed H1-1.00-REJ | expected H1-1.00-REJ | matches_expected True | matches_sealed True  
- preferred_allocation: recomputed A1_70_30 | expected A1_70_30 | matches_expected True | matches_sealed True  
- preferred_heat: recomputed H1-1.00-REJ | expected H1-1.00-REJ | matches_expected True | matches_sealed True  
- preferred_f_total_pct: recomputed 1.0 | expected 1.0 | matches_expected True | matches_sealed True  
- robust_core_median_cagr_range: recomputed [0.4814, 0.7038] | expected [0.4814, 0.7038] | matches_expected True | matches_sealed True  
- robust_core_p95_dd_range: recomputed [0.0474, 0.0829] | expected [0.0474, 0.0829] | matches_expected True | matches_sealed True  
- robust_core_p_dd_ge_10_range: recomputed [0.0, 0.0072] | expected [0.0, 0.0072] | matches_expected True | matches_sealed True  
- robust_core_p_dd_ge_15_range: recomputed [0.0, 0.0] | expected [0.0, 0.0] | matches_expected True | matches_sealed True  
- survives_100_edge: recomputed True | expected True | matches_expected True | matches_sealed True  
- survives_75_edge: recomputed True | expected True | matches_expected True | matches_sealed True  
- survives_50_edge: recomputed True | expected True | matches_expected True | matches_sealed True  
- survives_25_edge: recomputed False | expected False | matches_expected True | matches_sealed True  

## Gate test (11 negative injections)

- positive control: pass=True status=PASS  
- all negative tests fail closed = True  

| injection | seal pass | status | recorded failure |
|---|---|---|---|
| frontier_nonregression_pass=False | False | FAIL | ['frontier_nonregression_pass'] |
| block_episode_agreement_pass=False | False | FAIL | ['block_episode_agreement_pass'] |
| knee_seal_pass=False | False | FAIL | ['knee_seal_pass'] |
| adjacent_scale_seal_pass=False | False | FAIL | ['adjacent_scale_seal_pass'] |
| survives_100_edge=False | False | FAIL | ['survives_100_edge'] |
| survives_75_edge=False | False | FAIL | ['survives_75_edge'] |
| kelly_used=True | False | FAIL | ['kelly_used'] |
| dd_adaptive_used=True | False | FAIL | ['dd_adaptive_used'] |
| production_scale_selected=True | False | FAIL | ['production_scale_selected'] |
| deployment_authorized=True | False | FAIL | ['deployment_authorized'] |
| mt5_authorized=True | False | FAIL | ['mt5_authorized'] |

## Decision

- status: PASS  
- seal_gate_failures: []  
- seal_gate_passes: ['frontier_nonregression_pass', 'block_episode_agreement_pass', 'knee_seal_pass', 'adjacent_scale_seal_pass', 'survives_100_edge', 'survives_75_edge']  
- bands: CONSERVATIVE [0.25, 0.5] / ROBUST CORE [0.75, 1.0] / AGGRESSIVE [1.5, 2.0] / STRESS [3.0, 3.0]  
- allowed allocations: ['A0_50_50', 'A1_70_30']  
- operating heat: H1_OPTIONAL_SAFETY_LAYER_RETAINED  
- preferred research default: {'allocation': 'A1_70_30', 'heat_architecture': 'H1-1.00-REJ', 'f_total_pct': 1.0, 'role': 'PREFERRED_RESEARCH_DEFAULT for demo/execution translation research ONLY -- not production sizing, not live authorization', 'justification': 'best tail-efficiency allocation (A1_70_30) at the top of the robust core (0.75-1.00), at the knee start [1.0, 1.5], under the operating heat H1-1.00-REJ'}  
- robust core contract: CAGR [0.4814, 0.7038] | p95 DD [0.0474, 0.0829] | P(DD>=10) [0.0, 0.0072] | P(DD>=15) [0.0, 0.0]  

## Authorizations (all locked)  

- kelly_used=False / dd_adaptive_used=False / production_scale_selected=False / deployment_authorized=False / mt5_authorized=False  
- next_checkpoint_recommended: CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING (authorized: False)  