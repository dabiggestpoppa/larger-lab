# PFT-B3 — Mathematical Conformance

## Formula coverage

- formulas in register: 19
- every formula has an implementation target: True
- reference fixtures: 177 tests, 0 failures, 0 errors -> PASS

## Fail-closed behavior

Every unresolved state emits a reason code and disables the affected kernel (see TEST_COVERAGE_MATRIX.csv failure_behavior column); no silent algorithm substitution (e.g., K3 OLS never falls back to pseudoinverse/ridge).

## Activation census (DEVELOPMENT, descriptive only)

| kernel   |   activation_count |   activation_rate |   mean_duration_h |   median_duration_h |
|:---------|-------------------:|------------------:|------------------:|--------------------:|
| K1       |                  0 |           0       |             0     |                   0 |
| K2       |               3955 |           0.22609 |             2.452 |                   2 |
| K3       |                  0 |           0       |             0     |                   0 |
| K4       |                  0 |           0       |             0     |                   0 |

## Signal funnel (DEVELOPMENT, descriptive only)

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

## Status

`math_conformance_pass = True`
