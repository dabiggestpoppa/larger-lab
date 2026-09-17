# MECH-4 CLOSEOUT DECISION

## VERDICT: PASS_ALT_MECH4_WITH_LIMITATIONS

### Closeout verdict: 26 requirements audited, 22 COMPLETE, 4 PARTIAL

### Key revisions from original commit:

1. **P1 episodes**: 95% show OFFSET_EXPANSION_CONTRACTION (not true stalling). P1 episodes contain rank-band and dispersion movements that cancel at the global surface. Only 5% are TRUE_STALL.
2. **P1 pseudoreplication**: chain-level prop30=0.204, global-dedup=0.194, bootstrap 95CI=[0.178, 0.221]. The original 72% claim was based on forward-state counting within chains; the correct global estimate is ~20%.
3. **Bifurcation**: Raw-coordinate audit across 15 feature planes finds 8/15 earn boundary (max sharp=0.48, btc_ret30 x breadth30). BIFURCATION_BOUNDARY_EARNED on raw coordinates.
4. **Accumulation-like**: base_AUC=0.754, ctrl_AUC=0.904 (with breadth30 added). Absorbed by breadth family.
5. **G3 purged CV**: chrono AUC=0.743, purged AUC=0.625 (n=18, small), LOCO AUC=0.766 (4 cycles), bootstrap AUC=0.907. G3 survives temporal validation.
6. **RETEST_RELOAD**: base=14, alt_def=14. LOCAL_NODE, survives alternate definition.
7. **Permutation p-values**: all corrected to (k+1)/(B+1).
8. **tau_reroute/tau_total**: now properly computed with censoring labels.
9. **Route latency**: 248 transitions with actual dwell/latency matrices.
10. **State routing graph**: DESCRIPTIVE_ONLY (<20% threshold).

### Preserved core findings:
- 126 entries / 125 exits reconcile
- G3 propagation gate: SUPPORTED (purged AUC 0.625-0.907)
- Duration-structured escape: NARROW_FORM (age affects escape probability, not destination)
- Path memory: DISSOLVED as predictive, DESCRIPTIVE only
- P1 activation: NOT ESTABLISHED (pre-vs-ctrl p=0.09)
- Release initiation != route selection (F gate confirmed)
- Volatility: stage-conditional ACCESSIBILITY, not pure routing temperature

### human_review_required = TRUE
### next_checkpoint_authorized = FALSE

No strategy. No PnL. No deployment.
