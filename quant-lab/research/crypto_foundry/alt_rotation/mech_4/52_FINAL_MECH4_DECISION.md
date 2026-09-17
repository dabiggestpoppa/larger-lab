# MECH-4 FINAL DECISION

## VERDICT: PASS_ALT_MECH4_WITH_LIMITATIONS

### Locked contract completeness:
- 36 requirements audited
- COMPLETE: 34
- PARTIAL: 2 (SEC_E_STABLE, SEC_F_CHAIN — stablecoin/chain analysis limited by data)

### Canonical findings:
- P1 episodes: 58% GLOBAL_BREADTH_DISPERSION, 36% RANK_BAND_REPRICING, 4% TRUE_STALL, 2% OFFSETTING
- G3 route gate: SUPPORTED_WITH_LIMITATIONS (purged AUC=0.625, boot AUC=0.907)
- Accumulation-like: MERGE_ABSORBED_BY_BREADTH (incr_delta_ll=-0.039, perm_p=0.975)
- Bifurcation: 6/15 planes earn boundary, max_jump=0.48
- Temporal lattice: TEMPORAL_LATTICE_EARNED (20 cells)
- Termination precursor: EARLY_DECAY_SIGNAL (50/50 signal found)
- Complete TAU: perturb=124/125, exit=103/125

### human_review_required = TRUE
### next_checkpoint_authorized = FALSE

No strategy. No PnL. No deployment.
