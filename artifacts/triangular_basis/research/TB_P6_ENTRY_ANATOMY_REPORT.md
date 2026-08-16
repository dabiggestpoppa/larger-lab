# TB-P6 — ENTRY ANATOMY REPORT

**Phase:** TB-P6-ENTRY-ANATOMY-01 (ENTRY RESEARCH ONLY).
**Base:** commit `7868a67d624931d3afc56910de8b805510eabcc7` (TB-P5 accepted).
**Protocol:** `TB_P6_PROTOCOL.md` (pre-registered split/metrics/gates).
**Reproduce:** `python quant-lab/engines/tb_p6_anatomy.py --phase all` + `python quant-lab/engines/tb_p6_tests.py` (deterministic, seed 42).
**Decision:** `TB_P6_DECISION.json` · Candidates: `P6_CANDIDATE_ENTRY_RULES.json`.

## 1. Entry-threshold surface (P6.1)

Full grid: `P6_ENTRY_THRESHOLD_SURFACE.csv` (11 z values x 6 models, full metric set). 
Plateau analysis: `P6_ENTRY_THRESHOLD_PLATEAUS.md`.

| z | N | EV TB-B | EV TB-C5% | PF TB-B | WR | maxDD | MFE | MAE |
|---|---|---|---|---|---|---|---|---|
| 1.50 | 1341 | 10.36 | 9.49 | 5.27 | 78.2% | -62 | 10.6 | -17.0 |
| 1.75 | 1054 | 12.75 | 11.76 | 6.82 | 81.1% | -64 | 13.2 | -16.3 |
| 2.00 | 787 | 14.36 | 13.25 | 8.19 | 83.2% | -52 | 14.7 | -16.2 |
| 2.25 | 576 | 16.05 | 14.86 | 10.18 | 84.5% | -52 | 15.7 | -15.6 |
| 2.50 | 405 | 17.86 | 16.65 | 12.42 | 85.9% | -35 | 17.7 | -15.7 |
| 2.75 | 272 | 20.07 | 18.76 | 13.87 | 85.3% | -50 | 19.1 | -15.4 |
| 3.00 | 194 | 23.07 | 21.61 | 18.05 | 88.1% | -35 | 21.7 | -14.9 |
| 3.25 | 134 | 22.94 | 21.53 | 17.64 | 88.1% | -49 | 22.0 | -13.1 |
| 3.50 | 79 | 24.73 | 22.97 | 13.92 | 87.3% | -49 | 24.7 | -13.3 |
| 3.75 | 49 | 27.74 | 25.92 | 14.35 | 89.8% | -40 | 27.9 | -12.3 |
| 4.00 | 32 | 34.44 | 32.04 | 18.85 | 93.8% | -35 | 32.0 | -11.7 |

## 2. Further-extension anatomy (P6.2)

Per-trade paths: `P6_FURTHER_EXTENSION_PATHS.csv`; convergence surface: 
`P6_EXTENSION_CONVERGENCE_SURFACE.csv`; full write-up: 
`P6_EXTENSION_ANATOMY_REPORT.md` (hypotheses A-D tested quantitatively).

## 3. Session clock (P6.3)

`P6_TIME_OF_DAY_STUDY.csv` + `P6_SESSION_CLOCK_REPORT.md`. Headlines:
- Best half-hour: 60-90 min after London open (EV TB-B 33.91, N=20).
- Dead zones: ['half_hour=12', 'half_hour=13', 'quarter_hour=26'].

## 4. Dislocation-quality fingerprint (P6.4)

Per-trade causal features: `P6_DISLOCATION_FINGERPRINT.csv`; conditionals: 
`P6_QUALITY_CONDITIONALS.csv`. No future information enters any feature 
(tested in tb_p6_tests.py).

## 5. Cost stress + execution translation (P6.4)

Cost stress (1.0-3.0x, break-even): `P6_COST_STRESS.csv`. Lot translation 
(TB-B / TB-C-5%, $5k-$100k): `P6_EXECUTION_TRANSLATION.csv`.

| model | z=2.5 break-even | z=3.00 break-even | z=3.50 break-even |
|---|---|---|---|
| TB-B | 2.75x | nanx | nanx |
| TB-C-5% | 2.63x | nanx | nanx |

## 6. Candidate entry rules (classification)

Full detail: `P6_CANDIDATE_ENTRY_RULES.json` (gates, CIs, FDR q, block EVs, 
holdout, plateau, cost, basis, top-5% independence).

| candidate | grade | N | coverage | EV uplift | CI | q | D/C/H | holdout | plateau | BE | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TB-B @ 1.50 | **D** | 1341 | 331% | -7.50 | [-9.65,-5.27] | 0.000 | -8.1/-7.0/-6.2 | False | False | 2.02x | 104% |
| TB-B @ 1.75 | **D** | 1054 | 260% | -5.11 | [-7.27,-2.92] | 0.000 | -5.2/-5.2/-4.7 | False | False | 2.25x | 104% |
| TB-B @ 2.00 | **D** | 787 | 194% | -3.50 | [-5.93,-1.01] | 0.005 | -3.5/-4.1/-2.7 | False | False | 2.41x | 103% |
| TB-B @ 2.25 | **D** | 576 | 142% | -1.81 | [-4.50,+0.68] | 0.175 | -2.3/-1.8/-0.5 | False | False | 2.57x | 103% |
| TB-B @ 2.75 | **D** | 272 | 67% | +2.21 | [-1.24,+5.57] | 0.175 | +2.2/+1.2/+3.3 | True | True | 2.97x | 104% |
| TB-B @ 3.00 | **B** | 194 | 48% | +5.21 | [+1.51,+8.89] | 0.013 | +4.8/+5.4/+6.2 | True | True | nanx | 103% |
| TB-B @ 3.25 | **B** | 134 | 33% | +5.08 | [+0.95,+9.43] | 0.014 | +3.6/+6.9/+7.6 | True | True | nanx | 104% |
| TB-B @ 3.50 | **B** | 79 | 20% | +6.87 | [+0.94,+13.14] | 0.013 | +5.5/+8.1/+8.9 | True | True | nanx | 99% |
| TB-B @ 3.75 | **C** | 49 | 12% | +9.88 | [+1.56,+18.08] | 0.005 | +10.5/+8.9/+8.1 | None | False | nanx | 101% |
| TB-B @ 4.00 | **C** | 32 | 8% | +16.58 | [+6.44,+27.93] | 0.000 | +18.0/+13.4/+15.1 | None | False | nanx | 96% |
| TB-C-10% @ 1.50 | **D** | 1341 | 331% | -6.83 | [-8.82,-4.80] | 0.000 | -7.4/-6.1/-5.7 | False | False | 1.85x | 102% |
| TB-C-10% @ 1.75 | **D** | 1054 | 260% | -4.66 | [-6.72,-2.62] | 0.000 | -4.9/-4.4/-4.3 | False | False | 2.06x | 102% |
| TB-C-10% @ 2.00 | **D** | 787 | 194% | -3.29 | [-5.48,-0.99] | 0.005 | -3.5/-3.5/-2.5 | False | False | 2.19x | 101% |
| TB-C-10% @ 2.25 | **D** | 576 | 142% | -1.77 | [-4.23,+0.55] | 0.157 | -2.3/-1.5/-0.6 | False | False | 2.34x | 101% |
| TB-C-10% @ 2.75 | **D** | 272 | 67% | +2.00 | [-1.22,+5.13] | 0.195 | +2.1/+0.7/+3.1 | True | True | 2.71x | 102% |
| TB-C-10% @ 3.00 | **A** | 194 | 48% | +4.70 | [+1.16,+8.16] | 0.014 | +4.7/+3.9/+5.7 | True | True | 2.98x | 101% |
| TB-C-10% @ 3.25 | **B** | 134 | 33% | +4.65 | [+0.76,+8.62] | 0.019 | +3.6/+5.5/+7.0 | True | True | 2.97x | 102% |
| TB-C-10% @ 3.50 | **B** | 79 | 20% | +5.72 | [+0.34,+11.60] | 0.030 | +4.2/+7.0/+8.0 | True | True | nanx | 99% |
| TB-C-10% @ 3.75 | **C** | 49 | 12% | +8.59 | [+0.89,+16.17] | 0.008 | +9.2/+6.4/+8.0 | None | False | nanx | 101% |
| TB-C-10% @ 4.00 | **C** | 32 | 8% | +14.17 | [+4.77,+24.52] | 0.000 | +15.7/+9.2/+14.0 | None | False | nanx | 96% |
| TB-C-2.5% @ 1.50 | **D** | 1341 | 331% | -7.33 | [-9.45,-5.15] | 0.000 | -7.9/-6.8/-6.0 | False | False | 1.97x | 104% |
| TB-C-2.5% @ 1.75 | **D** | 1054 | 260% | -5.00 | [-7.16,-2.86] | 0.000 | -5.1/-5.0/-4.6 | False | False | 2.20x | 103% |
| TB-C-2.5% @ 2.00 | **D** | 787 | 194% | -3.45 | [-5.80,-1.03] | 0.005 | -3.5/-3.9/-2.7 | False | False | 2.35x | 103% |
| TB-C-2.5% @ 2.25 | **D** | 576 | 142% | -1.81 | [-4.40,+0.64] | 0.172 | -2.3/-1.7/-0.5 | False | False | 2.51x | 103% |
| TB-C-2.5% @ 2.75 | **D** | 272 | 67% | +2.16 | [-1.26,+5.45] | 0.176 | +2.2/+1.1/+3.3 | True | True | 2.90x | 104% |
| TB-C-2.5% @ 3.00 | **B** | 194 | 48% | +5.08 | [+1.43,+8.69] | 0.014 | +4.8/+5.0/+6.0 | True | True | nanx | 103% |
| TB-C-2.5% @ 3.25 | **B** | 134 | 33% | +4.99 | [+0.91,+9.28] | 0.014 | +3.6/+6.6/+7.5 | True | True | nanx | 103% |
| TB-C-2.5% @ 3.50 | **B** | 79 | 20% | +6.61 | [+0.82,+12.82] | 0.014 | +5.2/+7.9/+8.7 | True | True | nanx | 99% |
| TB-C-2.5% @ 3.75 | **C** | 49 | 12% | +9.58 | [+1.42,+17.61] | 0.005 | +10.2/+8.3/+8.1 | None | False | nanx | 101% |
| TB-C-2.5% @ 4.00 | **C** | 32 | 8% | +16.00 | [+6.02,+27.21] | 0.000 | +17.4/+12.4/+14.9 | None | False | nanx | 96% |
| TB-C-5% @ 1.50 | **D** | 1341 | 331% | -7.17 | [-9.23,-5.03] | 0.000 | -7.8/-6.6/-5.9 | False | False | 1.93x | 103% |
| TB-C-5% @ 1.75 | **D** | 1054 | 260% | -4.89 | [-7.02,-2.83] | 0.000 | -5.0/-4.8/-4.5 | False | False | 2.15x | 103% |
| TB-C-5% @ 2.00 | **D** | 787 | 194% | -3.40 | [-5.69,-1.02] | 0.004 | -3.5/-3.8/-2.6 | False | False | 2.30x | 102% |
| TB-C-5% @ 2.25 | **D** | 576 | 142% | -1.80 | [-4.33,+0.60] | 0.168 | -2.3/-1.7/-0.6 | False | False | 2.46x | 102% |
| TB-C-5% @ 2.75 | **D** | 272 | 67% | +2.11 | [-1.24,+5.34] | 0.181 | +2.2/+0.9/+3.2 | True | True | 2.84x | 103% |
| TB-C-5% @ 3.00 | **B** | 194 | 48% | +4.95 | [+1.36,+8.50] | 0.015 | +4.7/+4.6/+5.9 | True | True | nanx | 102% |
| TB-C-5% @ 3.25 | **B** | 134 | 33% | +4.88 | [+0.90,+9.04] | 0.018 | +3.6/+6.2/+7.2 | True | True | nanx | 103% |
| TB-C-5% @ 3.50 | **B** | 79 | 20% | +6.32 | [+0.65,+12.37] | 0.020 | +4.9/+7.6/+8.4 | True | True | nanx | 99% |
| TB-C-5% @ 3.75 | **C** | 49 | 12% | +9.27 | [+1.24,+17.17] | 0.006 | +9.9/+7.7/+8.1 | None | False | nanx | 100% |
| TB-C-5% @ 4.00 | **C** | 32 | 8% | +15.39 | [+5.62,+26.26] | 0.000 | +16.8/+11.3/+14.6 | None | False | nanx | 96% |
| TB-C-7.5% @ 1.50 | **D** | 1341 | 331% | -7.00 | [-9.03,-4.92] | 0.000 | -7.6/-6.3/-5.8 | False | False | 1.89x | 102% |
| TB-C-7.5% @ 1.75 | **D** | 1054 | 260% | -4.79 | [-6.87,-2.70] | 0.000 | -5.0/-4.6/-4.4 | False | False | 2.10x | 102% |
| TB-C-7.5% @ 2.00 | **D** | 787 | 194% | -3.35 | [-5.58,-1.01] | 0.005 | -3.5/-3.6/-2.6 | False | False | 2.25x | 102% |
| TB-C-7.5% @ 2.25 | **D** | 576 | 142% | -1.79 | [-4.28,+0.54] | 0.161 | -2.3/-1.6/-0.6 | False | False | 2.40x | 102% |
| TB-C-7.5% @ 2.75 | **D** | 272 | 67% | +2.05 | [-1.23,+5.24] | 0.192 | +2.1/+0.8/+3.2 | True | True | 2.77x | 103% |
| TB-C-7.5% @ 3.00 | **B** | 194 | 48% | +4.82 | [+1.27,+8.30] | 0.016 | +4.7/+4.2/+5.8 | True | True | nanx | 102% |
| TB-C-7.5% @ 3.25 | **B** | 134 | 33% | +4.76 | [+0.86,+8.86] | 0.019 | +3.6/+5.9/+7.1 | True | True | nanx | 102% |
| TB-C-7.5% @ 3.50 | **B** | 79 | 20% | +6.03 | [+0.49,+11.94] | 0.023 | +4.5/+7.3/+8.2 | True | True | nanx | 99% |
| TB-C-7.5% @ 3.75 | **C** | 49 | 12% | +8.95 | [+1.05,+16.64] | 0.006 | +9.6/+7.1/+8.1 | None | False | nanx | 100% |
| TB-C-7.5% @ 4.00 | **C** | 32 | 8% | +14.78 | [+5.12,+25.38] | 0.000 | +16.2/+10.3/+14.3 | None | False | nanx | 96% |

## 7. Decision

**p7_convergence_optimization_cleared = True**

A/B candidates must improve expectancy or downside profile, survive 
confirmation and the frozen holdout, retain meaningful coverage, lie on a stable 
plateau, preserve basis-reversion attribution, and remain executable.

## 8. STOP FOR HUMAN REVIEW

P6 is ENTRY RESEARCH ONLY. No exit/hold/stop/pyramiding/scaling/risk/deployment 
work begins. Review `TB_P6_DECISION.json` + this report before any P7 work.
