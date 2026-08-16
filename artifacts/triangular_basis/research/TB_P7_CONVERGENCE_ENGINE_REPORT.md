# TB-P7 — CONVERGENCE ENGINE REPORT

**Phase:** TB-P7-CONVERGENCE-ENGINE-01 (exit research only).
**Base:** master 31e7ad5e + P6.5 repair a7a1fddd.
**Protocol:** TB_P7_PROTOCOL.md (pre-registered).
**Reproduce:** python quant-lab/engines/tb_p7_convergence.py --phase all + python quant-lab/engines/tb_p7_tests.py.
**Decision:** TB_P7_DECISION.json.

## P7.1 — Convergence target

P7_EXIT_Z_SURFACE.csv (7 targets x 2 entries x 5 models) + P7_EXIT_CAPTURE_REPORT.md.

## P7.2 — Hold survival

P7_CONVERGENCE_SURVIVAL.csv + P7_REMAINING_EXPECTANCY_SURFACE.csv + P7_HOLD_ANATOMY_REPORT.md.

## P7.3 — Profit giveback

P7_PROFIT_GIVEBACK.csv + P7_CAPTURE_EFFICIENCY.csv + P7_PROFIT_CAPTURE_REPORT.md (hypotheses only).

## P7.4 — Structural invalidation

P7_INVALIDATION_SURFACE.csv + P7_RECOVERY_CLIFFS.md + P7_STRUCTURAL_INVALIDATION_REPORT.md.

## P7.5 — Candidate exit engines

Configs: P7_ENGINE_CONFIGS.json; full metrics: P7_EXIT_ENGINE_COMPARISON.csv.

| engine | entry | model | grade | EV | EV vs E0 | CI | PF | net pips | maxDD | hold h | pips/hr | basis | BE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | 2.5 | TB-B | **D** | 17.86 | +0.00 | [+0.0,+0.0] | 12.42 | 7234 | -35 | 3.4 | 5.26 | 104% | 2.75x |
| E0 | 2.5 | TB-C-10% | **D** | 15.45 | +0.00 | [+0.0,+0.0] | 8.97 | 6257 | -47 | 3.4 | 4.55 | 101% | 2.51x |
| E0 | 2.5 | TB-C-2.5% | **D** | 17.26 | +0.00 | [+0.0,+0.0] | 11.49 | 6989 | -37 | 3.4 | 5.08 | 103% | 2.69x |
| E0 | 2.5 | TB-C-5% | **D** | 16.65 | +0.00 | [+0.0,+0.0] | 10.65 | 6745 | -40 | 3.4 | 4.90 | 103% | 2.63x |
| E0 | 3 | TB-B | **D** | 23.07 | +0.00 | [+0.0,+0.0] | 18.05 | 4475 | -35 | 3.4 | 6.88 | 103% | >=3.0 |
| E0 | 3 | TB-C-10% | **D** | 20.15 | +0.00 | [+0.0,+0.0] | 12.60 | 3910 | -48 | 3.4 | 6.01 | 101% | 2.98x |
| E0 | 3 | TB-C-2.5% | **D** | 22.34 | +0.00 | [+0.0,+0.0] | 16.79 | 4334 | -37 | 3.4 | 6.66 | 103% | >=3.0 |
| E0 | 3 | TB-C-5% | **D** | 21.61 | +0.00 | [+0.0,+0.0] | 15.52 | 4192 | -40 | 3.4 | 6.44 | 102% | >=3.0 |
| E1 | 2.5 | TB-B | **A** | 19.60 | +1.74 | [+1.1,+2.1] | 13.40 | 7881 | -35 | 3.7 | 5.37 | 104% | 2.92x |
| E1 | 2.5 | TB-C-10% | **A** | 17.05 | +1.60 | [+1.0,+2.0] | 9.68 | 6854 | -48 | 3.7 | 4.67 | 101% | 2.67x |
| E1 | 2.5 | TB-C-2.5% | **A** | 18.96 | +1.71 | [+1.0,+2.1] | 12.41 | 7622 | -37 | 3.7 | 5.19 | 103% | 2.86x |
| E1 | 2.5 | TB-C-5% | **A** | 18.32 | +1.67 | [+1.0,+2.1] | 11.50 | 7366 | -40 | 3.7 | 5.02 | 102% | 2.80x |
| E1 | 3 | TB-B | **A** | 24.86 | +1.79 | [+1.0,+2.6] | 19.03 | 4823 | -35 | 3.6 | 6.83 | 103% | >=3.0 |
| E1 | 3 | TB-C-10% | **A** | 21.80 | +1.65 | [+0.9,+2.4] | 13.29 | 4229 | -62 | 3.6 | 5.99 | 101% | >=3.0 |
| E1 | 3 | TB-C-2.5% | **A** | 24.09 | +1.75 | [+1.0,+2.5] | 17.69 | 4674 | -41 | 3.6 | 6.62 | 102% | >=3.0 |
| E1 | 3 | TB-C-5% | **A** | 23.32 | +1.71 | [+1.0,+2.5] | 16.35 | 4524 | -48 | 3.6 | 6.41 | 102% | >=3.0 |
| E3 | 2.5 | TB-B | **D** | 17.63 | -0.23 | [-0.5,+1.2] | 7.39 | 7370 | -80 | 3.5 | 5.11 | 104% | 2.73x |
| E3 | 2.5 | TB-C-10% | **D** | 15.27 | -0.18 | [-0.5,+1.1] | 5.84 | 6384 | -89 | 3.5 | 4.42 | 101% | 2.50x |
| E3 | 2.5 | TB-C-2.5% | **D** | 17.03 | -0.22 | [-0.5,+1.1] | 6.98 | 7120 | -82 | 3.5 | 4.93 | 103% | 2.67x |
| E3 | 2.5 | TB-C-5% | **D** | 16.44 | -0.21 | [-0.5,+1.1] | 6.59 | 6873 | -84 | 3.5 | 4.76 | 103% | 2.61x |
| E3 | 3 | TB-B | **D** | 22.71 | -0.36 | [-1.7,+1.3] | 9.67 | 4451 | -72 | 3.5 | 6.55 | 104% | >=3.0 |
| E3 | 3 | TB-C-10% | **D** | 19.91 | -0.25 | [-1.4,+1.3] | 7.57 | 3902 | -92 | 3.5 | 5.75 | 102% | 2.95x |
| E3 | 3 | TB-C-2.5% | **D** | 22.00 | -0.34 | [-1.7,+1.3] | 9.13 | 4312 | -77 | 3.5 | 6.35 | 103% | >=3.0 |
| E3 | 3 | TB-C-5% | **D** | 21.29 | -0.32 | [-1.6,+1.3] | 8.61 | 4173 | -82 | 3.5 | 6.15 | 103% | >=3.0 |

## P7.5 gate repair (same class as TB-P6.5)

The first P7.5 pass graded every candidate C/D because the significance test was the two-sample bootstrap/permutation reused from the P6 entry grid. That test is correct for the P6 threshold comparison (genuinely different trade sets) but wrong for exit engines: E1/E3 re-use E0's matched signal set (only the exit rule differs), so the correct statistic is the per-trade difference. Example, TB-B entry 2.5: the unpaired CI was [-1.2, +4.7] (p=0.24, grade C) while the matched-pairs CI on the same data is [+1.07, +2.17] (sign-flip p<0.001). No gate was changed after seeing results - only the statistic was corrected to respect the matched design. E_new trades that merge E0 re-entries or split E0 trades into legs are aligned to the E0 trade whose window they enter, so sum(diffs) == total PnL delta exactly.

## Decision

The frozen exit architecture is retained unless a robust exit engine improves the validated strategy without changing its underlying edge.

## STOP FOR HUMAN REVIEW

No P8 structural geometry work begins. Review TB_P7_DECISION.json + this report before any exit change is adopted.
