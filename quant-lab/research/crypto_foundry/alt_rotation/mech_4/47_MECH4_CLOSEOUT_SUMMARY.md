# MECH-4 CLOSEOUT SUMMARY

## Contract: 26 requirements — see 41_LOCKED_CONTRACT_COMPLETENESS_AUDIT.md

## P1 Pseudoreplication
- CHAIN_LEVEL: n=797, prop30=0.2043
- GLOBAL_DEDUP: n=72, prop30=0.1944
- CHAIN_BOOTSTRAP_95CI: n=797, prop30=nan
- LEAVE_ONE_CHAIN_OUT: n=12, prop30=nan

## Transient vs Sustained (7D/14D for PROP targets)
- BROAD_RISK_EXPANSION @7D: touch=66.7%, sustain≥5D=22.2%
- ETH_BROADENING @7D: touch=100.0%, sustain≥5D=100.0%
- LARGE_ALT_ROTATION @7D: touch=100.0%, sustain≥5D=50.0%
- MID_CAP_ROTATION @7D: touch=100.0%, sustain≥5D=75.0%
- BROAD_RISK_EXPANSION @14D: touch=88.9%, sustain≥5D=77.8%
- ETH_BROADENING @14D: touch=100.0%, sustain≥5D=100.0%
- LARGE_ALT_ROTATION @14D: touch=100.0%, sustain≥5D=100.0%
- MID_CAP_ROTATION @14D: touch=100.0%, sustain≥5D=100.0%

## Temporal: 125 events, tau_reroute observed=125, tau_total observed=123

## RETEST_RELOAD: base={'FAILED_IGNITION': 52, 'FULL_FAILURE': 45, 'IMMEDIATE_DELIVERY': 14, 'RETEST_RELOAD': 14}, alt_def={'FAILED_IGNITION': 53, 'FULL_FAILURE': 45, 'RETEST_RELOAD': 14, 'IMMEDIATE_DELIVERY': 13}

## Accumulation-Like: base_AUC=0.7537792894935752, ctrl_AUC=0.9043839758125471, incremental=True

## Bifurcation: verdict=BIFURCATION_BOUNDARY_EARNED, max_jump=0.48

## Purged CV (G3)
- CHRONO_70_30: AUC=0.7426, delta=0.0787
- PURGED: AUC=0.625, delta=0.0308
- LOCO: AUC=nan, delta=nan
- BOOTSTRAP: AUC=nan, delta=nan

## Permutation Corrections
- G1_perm_p: raw=0.8500 → corrected=0.8507
- G3_perm_p: raw=0.0000 → corrected=0.0050
- path_memory_perm_p: raw=0.8700 → corrected=0.8706

## Node Review
- **ROUTE_GATE**: NULL (NOT_EARNED)
- **DURATION_STRUCTURED_ESCAPE**: NEW_NODE (NARROW_FORM)
- **RETEST_RELOAD**: LOCAL_NODE (SURVIVES_ALT_DEF)
- **ACCUMULATION_LIKE**: MERGE (ABSORBED_BY_BREADTH)
- **BIFURCATION**: BIFURCATION_BOUNDARY_EARNED (BOUNDARY)
- **VOLATILITY_LIFECYCLE**: LOCAL_NODE (STAGE_CONDITIONAL)
- **HYSTERESIS_PREDICTIVE**: DISSOLVE (DEAD)
- **STATE_ROUTING_GRAPH**: DESCRIPTIVE_ONLY (NOT_EARNED_AT_THRESHOLD)
