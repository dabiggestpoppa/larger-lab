# PFT-B5 — Next Plan

**Checkpoint**: PFT-B5-A1-ATOMIC-EVIDENCE
**Decision**: PARTIAL_A1_ATOMIC_EVIDENCE
**Date**: 2026-08-26

## Current Status

The B5 analysis framework is complete but data-dependent computations are blocked by Git LFS resolution issues.

## Required Actions Before Re-Running B5

1. **Resolve Git LFS**
   - Ensure SYNC_PANEL_H1.parquet (4.6MB) resolves from LFS pointer
   - Verify data loads correctly into pandas
   - Confirm 17,493 H1 slots for development period

2. **Complete Data-Dependent Analyses**
   - Extract continuous observables for K1/K2/K3/K4
   - Compute future outcome targets at frozen horizons
   - Run kernel-by-kernel statistical analyses
   - Apply baseline comparisons
   - Run decomposition tests
   - Apply multiple testing correction (BH-FDR)
   - Run subperiod stability (2023/2024)
   - Run regime slice analysis
   - Run dependency-aware bootstrap
   - Create kernel dependence matrix

3. **Generate Missing Artifacts**
   - K1_OBSERVABLES.parquet
   - K1_ATOMIC_EVIDENCE.csv
   - K1_BASELINE_COMPARISON.csv
   - K2_EVENT_LEDGER.parquet
   - K2_ATOMIC_EVIDENCE.csv
   - K2_BASELINE_COMPARISON.csv
   - K3_OBSERVABLES.parquet
   - K3_ATOMIC_EVIDENCE.csv
   - K3_BASELINE_COMPARISON.csv
   - K4_OBSERVABLES.parquet
   - K4_ATOMIC_EVIDENCE.csv
   - K4_BASELINE_COMPARISON.csv
   - A1_BOOTSTRAP.csv

4. **Finalize Decision**
   - Update DECISION.json with data-dependent results
   - Update REPORT.md with complete findings
   - Update A1_ATOMIC_INFORMATION_SCORECARD.csv

## Priority Analysis

1. **K2** (highest priority): 22.6% activation rate; most likely to show predictive information
2. **K1**: Eigenvalue magnitude may carry information despite band being empty
3. **K3**: Edge density and pairwise distances may predict future dispersion
4. **K4**: Scale mismatch is severe; lower priority

## Implications for B6

- B6 should NOT be authorized until B5 is completed with data
- K4 full-stack rescue is unlikely given 122x scale mismatch
- K2 is the only kernel with meaningful activation; focus B6 on K2 if atomic evidence supports it

## Timeline

1. Resolve Git LFS issue
2. Re-run B5 analysis script
3. Complete all artifacts
4. Re-commit with updated decision

---

**STOP FOR HUMAN REVIEW.**
