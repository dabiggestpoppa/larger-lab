# MVE P4 — CAUSAL ACCEPTANCE ENGINE — REPORT

Checkpoint: `MVE-P4-CAUSAL-ACCEPTANCE-ENGINE`  ·  generated 2026-08-16T05:29:48.379772+00:00
Status: **PASS**  ·  causality: perturb PASS / trunc PASS / schema PASS

- Events (dev): 15771 across 965 episodes; schema problems: 0; dedup: PASS
- FDR family: 324 tests at q=0.10, 314 discoveries
- Promoted to P5: ['A2_2of3', 'A2_3of4', 'A2_3of5', 'A3_n2', 'A3_n3', 'A3_n4', 'A4_R1']

## Per-variant dev summary (pooled, h=6)

| variant | N | cont_6 | rej_6 | med_disp_6 | coverage | grade |
|---|---|---|---|---|---|---|
| A0 | 3995 | 0.4653 | 0.7730 | -0.0099 | HIGH_COVERAGE | D |
| A1 | 1648 | 0.6024 | 0.6116 | -0.0244 | HIGH_COVERAGE | B |
| A2_2of3 | 1170 | 0.6935 | 0.4735 | 0.0314 | HIGH_COVERAGE | A |
| A2_3of4 | 967 | 0.7492 | 0.3813 | -0.0418 | HIGH_COVERAGE | A |
| A2_3of5 | 967 | 0.7492 | 0.3813 | -0.0418 | HIGH_COVERAGE | A |
| A3_n2 | 1170 | 0.6935 | 0.4735 | 0.0314 | HIGH_COVERAGE | A |
| A3_n3 | 967 | 0.7492 | 0.3813 | -0.0418 | HIGH_COVERAGE | A |
| A3_n4 | 852 | 0.7885 | 0.3278 | -0.0778 | HIGH_COVERAGE | A |
| A4_R1 | 996 | 0.6576 | 0.5217 | 0.0000 | HIGH_COVERAGE | A |
| A4_R2 | 692 | 0.6246 | 0.5754 | -0.0604 | HIGH_COVERAGE | B |
| A5 | 2347 | 0.3691 | 0.8862 | 0.0000 | HIGH_COVERAGE | D |

## Incremental information (logit on continuation_6 vs A0)

| variant | coef | p | FDR sig | stratified lift |
|---|---|---|---|---|
| A1 | 0.0863 | 0.1925 | False | 0.0655 |
| A2_2of3 | 0.2211 | 0.0076 | True | 0.1382 |
| A2_3of4 | 0.3157 | 0.0010 | True | 0.1860 |
| A2_3of5 | 0.3157 | 0.0010 | True | 0.1860 |
| A3_n2 | 0.2211 | 0.0076 | True | 0.1382 |
| A3_n3 | 0.3157 | 0.0010 | True | 0.1860 |
| A3_n4 | 0.3505 | 0.0011 | True | 0.2144 |
| A4_R1 | 0.1922 | 0.0203 | True | 0.1115 |
| A4_R2 | 0.1047 | 0.2546 | False | 0.0776 |

## Confirmation pass (2025)

| variant | conf N | conf cont_6 | dev cont_6 | delta |
|---|---|---|---|---|
| A0 | 1043 | 0.4602 | 0.4654 | -0.0052 |
| A1 | 468 | 0.5812 | 0.6052 | -0.0240 |
| A2_2of3 | 344 | 0.6686 | 0.6940 | -0.0254 |
| A2_3of4 | 291 | 0.7113 | 0.7525 | -0.0412 |
| A2_3of5 | 291 | 0.7113 | 0.7525 | -0.0412 |
| A3_n2 | 344 | 0.6686 | 0.6940 | -0.0254 |
| A3_n3 | 291 | 0.7113 | 0.7525 | -0.0412 |
| A3_n4 | 254 | 0.7480 | 0.7943 | -0.0463 |
| A4_R1 | 310 | 0.6516 | 0.6605 | -0.0089 |
| A4_R2 | 221 | 0.6154 | 0.6282 | -0.0128 |
| A5 | 575 | 0.3617 | 0.3667 | -0.0050 |

## Causality audit

- A0: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A1: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A2_2of3: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A2_3of4: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A2_3of5: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A3_n2: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A3_n3: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A3_n4: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A4_R1: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A4_R2: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)
- A5: perturb max_diff=0.0 (PASS), trunc max_diff=0.0 (PASS)

## Notes
- Rebalancing fraction: NOT_CAUSALLY_DEFINED (recorded per protocol, not computed).
- Forward-return sanity is EX_POST_EVALUATION_ONLY.
- No trading rule was selected; no PnL optimization was performed.
