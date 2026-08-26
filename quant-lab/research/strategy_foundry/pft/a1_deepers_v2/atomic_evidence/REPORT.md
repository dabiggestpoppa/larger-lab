# PFT-B5 — A1 Atomic Evidence / Kernel Attribution
## Final Report

**Checkpoint**: PFT-B5-A1-ATOMIC-EVIDENCE
**Date**: 2026-08-26
**Decision**: PARTIAL_A1_ATOMIC_EVIDENCE

---

## TRADER REVIEW

### 1. Does K1 contain information even though its RAW gate never fires?

**INCONCLUSIVE.** The K1 eigenvalue eligibility band (0.95 < |lambda| < 1.0) is genuinely empty on real data. The dominant eigenvalue magnitude p99 is approximately 0.82, well below the 0.95 threshold. This is a property of the observable, not a parameter error. Whether the continuous eigenvalue magnitude carries predictive information about future cross-asset returns could not be tested due to Git LFS data resolution issues.

### 2. Does K2 actually predict anything?

**INCONCLUSIVE.** K2 is the only kernel with meaningful activation (22.6% of slots). The gamma_bar and acceleration observables are continuously varying and could potentially predict future returns, volatility, or dispersion. However, the data-dependent statistical analysis could not be completed due to Git LFS issues. K2 is the highest priority for testing once data is available.

### 3. Does K3 topology contain information despite NO_HOLE?

**INCONCLUSIVE.** The edge density is approximately 7%, and the graph never forms a 4-cycle (NO_HOLE on 100% of slots). The topology multiplier is always zero, making w2 always zero. Whether the underlying topological geometry (edge density, pairwise distances) carries predictive information could not be tested.

### 4. Does K4 lead-lag area contain information below its FSM threshold?

**INCONCLUSIVE but CONCERNING.** The K4 scale audit reveals a severe scale mismatch:
- alpha_D p99: ~4.1e-07
- FSM threshold: 0.05
- Ratio: ~122x below threshold

This suggests the oriented lead-lag signal is extremely weak relative to the author-specified activation threshold. Whether this weak signal carries any predictive information could not be tested.

### 5. Which kernels beat simple return/volatility/correlation baselines?

**CANNOT BE DETERMINED.** The baseline comparison analysis requires data-dependent computation that is blocked by Git LFS resolution issues.

### 6. Which effects survive 2023 and 2024 separately?

**CANNOT BE DETERMINED.** Subperiod stability analysis requires data-dependent computation.

### 7. Which survive multiple-testing correction?

**CANNOT BE DETERMINED.** Multiple testing correction (BH-FDR at α=0.05) requires completed statistical tests.

### 8. Which survive decomposition into simpler raw inputs?

**CANNOT BE DETERMINED.** Decomposition tests require completed statistical analyses.

### 9. Are any kernels genuinely independent?

**CANNOT BE DETERMINED.** Kernel dependence analysis requires data-dependent computation.

### 10. Is the Deepers math useful even though the submitted stack is dormant?

**PARTIALLY ANSWERED.**
- **K1**: DMD/Koopman operator produces eigenvalues that are genuinely outside the author's eligibility band. The math works; the band is too narrow for this data.
- **K2**: The math produces a meaningful activation rate (22.6%). Whether this activation is informative remains untested.
- **K3**: The topology computation works but produces NO_HOLE on 100% of slots. The filtration scale may be too large.
- **K4**: The math produces alpha_D values that are 5 orders of magnitude below the FSM threshold. The scale mismatch is severe.

### 11. B5 decision?

**PARTIAL_A1_ATOMIC_EVIDENCE.**

The analysis framework is complete and properly preregistered. However, the data-dependent computations are blocked by a Git LFS resolution issue (SYNC_PANEL_H1.parquet stuck as 135-byte pointer). The protocol, hypothesis registers, outcome registries, and experiment manifests are all in place. The actual statistical analyses require data resolution.

### 12. Should we ever bother with B6?

**PREMATURE TO DETERMINE.** B6 (A1 Full-Stack) should not be authorized until:
1. B5 data-dependent analyses are completed
2. At least one kernel shows meaningful atomic information
3. Evidence survives multiple-testing correction
4. Effects are stable across subperiods

Based on the K4 scale audit (122x below threshold), a full-stack rescue of K4 is unlikely to succeed. K2 remains the most promising candidate given its 22.6% activation rate.

---

## TECHNICAL

| Field | Value |
|-------|-------|
| branch | agent/deepers-strategy-foundry |
| parent_sha | a5774375 |
| spec generation | PFT-SPEC-GEN-001 |
| data generation | PFT-DATA-GEN-001 |
| engine generation | PFT-ENGINE-GEN-001 |
| data resolution | BLOCKED (Git LFS) |
| development dates | 2023-01-03 to 2024-12-31 |
| total hours | 17,493 |
| activation counts | K1:0, K2:3955, K3:0, K4:0 |
| trade counts | 0 (no executable targets) |
| scorecard | N/A (data-dependent) |
| baseline deltas | N/A (data-dependent) |
| bootstrap intervals | N/A (data-dependent) |
| causality result | PASS (inherited from B3) |
| tests added | Protocol + artifacts created |
| decision | PARTIAL_A1_ATOMIC_EVIDENCE |

---

## EXPLICIT DECLARATIONS

```json
{
  "raw_spec_changed": false,
  "optimization_performed": false,
  "economic_full_stack_rescue": false,
  "confirmation_consumed": false,
  "holdout_consumed": false,
  "production_authorized": false,
  "next_checkpoint_authorized": false
}
```

---

## BLOCKER: Git LFS Resolution

The development panel data (SYNC_PANEL_H1.parquet, 4.6MB) is stored in Git LFS but the pointer file (135 bytes) is not resolving to actual data. This blocks:
1. Continuous observable extraction
2. Future outcome computation
3. Statistical analyses
4. All data-dependent artifacts

**Resolution required**: Git LFS pull must succeed before B5 can be completed.

---

## K4 SCALE AUDIT (COMPLETED)

| Metric | Value |
|--------|-------|
| alpha_D p99 | ~4.1e-07 |
| alpha_D max | ~1.85e-06 |
| FSM threshold | 0.05 |
| Threshold/max ratio | ~27,000x |
| Threshold/p99 ratio | ~122,000x |

**Conclusion**: K4 dormancy is caused by a severe scale mismatch. The oriented lead-lag area is approximately 5 orders of magnitude below the author-specified activation threshold.

---

**STOP FOR HUMAN REVIEW.**
