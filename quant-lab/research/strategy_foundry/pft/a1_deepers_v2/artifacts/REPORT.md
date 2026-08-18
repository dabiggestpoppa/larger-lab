# PFT-B3 — Math & Causality Conformance — REPORT

## Trader summary

The laboratory is built and every equation of the frozen Deepers v2.2 specification is proven correct, causal, and reproducible (177 tests, bit-exact determinism and truncation invariance on the real panel). The first scientific finding from the mechanism census is that the RAW engine is mathematically dormant on the DEVELOPMENT panel: K1 never finds an eligible DMD mode, K3 never produces a topology hole, and K4's gate never reaches the neutral threshold - so the frozen engine never generates a nonzero target. This is a property of the submitted spec at its frozen scales on this data, not a code defect, and not a license to re-tune. It is exactly the kind of mechanism truth that must be known before any economic testing is discussed.

- checkpoint: `PFT-B3-MATH-CAUSALITY-CONFORMANCE`
- branch: `agent/deepers-strategy-foundry`
- generated: 2026-08-18T18:41:36.221874+00:00
- data: PFT-DATA-GEN-001 | engine: PFT-ENGINE-GEN-001

## Evidence

- all_formulas_mapped: True
- all_formulas_implemented: True
- reference_fixtures_pass: True
- causality_tests_pass: True
- determinism_bit_exact: True
- truncation_bit_exact: True
- partition_guard_enforced: True
- no_pnl_columns: True
- protected_partitions_raise: True
- invalid_state_ledger_recorded: True
- null_registry_registered: True

### DEVELOPMENT pipeline: 17493 slots (2023-01-03T03:00:00+00:00 -> 2024-12-31T23:00:00+00:00)

### Kernel activation (descriptive, not performance)

| kernel   |   activation_count |   activation_rate |
|:---------|-------------------:|------------------:|
| K1       |                  0 |           0       |
| K2       |               3955 |           0.22609 |
| K3       |                  0 |           0       |
| K4       |                  0 |           0       |

### Signal funnel (pre-economic)

| stage                    |   count |   fraction_of_total |
|:-------------------------|--------:|--------------------:|
| total_h1_slots           |   17493 |            1        |
| synchronized_valid_slots |   12915 |            0.738295 |
| K4_cluster_active        |       0 |            0        |
| K1_valid                 |       0 |            0        |
| K2_active                |    3955 |            0.22609  |
| K3_topology_nonzero      |       0 |            0        |
| nonzero_target           |       0 |            0        |
| gross_cap_applied        |       0 |            0        |
| fade_adjusted            |       0 |            0        |
| DD_adjusted              |       0 |            0        |
| leg_stop_adjusted        |       0 |            0        |
| executable_target        |       0 |            0        |

## Derived status: **PASS**

## Gate

`human_review_required = true`
`next_checkpoint_authorized = false`
`economic_pnl_computed = false`
`parameter_optimization_performed = false`
`confirmation_consumed = false`
`holdout_consumed = false`
