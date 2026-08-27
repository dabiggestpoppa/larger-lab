# OCE Quant Planning Reference Register

**Document ID:** OCE-QUANT-REF-001  
**Version:** 1.0  
**Status:** PLANNING EVIDENCE — NOT CANONICAL PERFORMANCE PROOF

## 1. Purpose

This register records the operator-provided references used to shape Blocks 7–9. A source can inform a contract or test without proving that a strategy, result, threshold, or implementation is correct. Every strategy claim still requires independent reproduction through OCE.

| Source | Planning concepts used | Applied in |
|---|---|---|
| `CEREBUS_FX_v4_Complete_Manual (3)(1).pdf` | Versioned doctrine, regime/tier filters, explicit stand-down states, sizing rules, slippage/spread awareness, claimed calibration and simulation separated from independent reproduction | B7.C2, B7.C4, B7.C5; B8 strategy dossiers |
| `Trading-Exchanges-Market-Microstructure-Practitioners Draft Copy.pdf` | Order types, order books, partial/non-fill, liquidity, explicit/implicit/missed-opportunity costs, market impact and best-execution ambiguity | B7.C2.S4; B9.C1–C4 |
| `349585448-Market-Microstructure-Theory-pdf.pdf` | Information asymmetry, price formation, liquidity and microstructure-dependent execution assumptions | B7 cost/fill stress; B8 mechanism critique |
| `Algorithmic-Trading-and-Direct-Market-Access.pdf` | Order lifecycle, venue/broker interfaces, latency, execution algorithms, risk and operational controls | B9 broker adapters, acknowledgements, fills and reconciliation |
| `Building-Algorithmic-Trading-Systems.pdf` | Out-of-sample evaluation, walk-forward analysis, realistic costs, position sizing, process discipline and live/paper distinction | B7.C3; B8 promotion; B9 staged execution |
| `WorldQuant_FindingAlphas.pdf` | Alpha registration, turnover/cost awareness, out-of-sample eligibility, overfitting and broad search risk | B7 validation; B8 bias/multiplicity controls |
| `A-First-Course-in-Probability.pdf` and `billingsley probability.pdf` | Probability foundations, conditional reasoning, random variables and convergence caution | B7 metric/statistical implementation references |
| `Casella_Berger_Statistical_Inference.pdf` | Estimation, testing, uncertainty and model/evidence distinction | B7 promotion and B8 comparative analysis |
| `the_misbehavior_of_markets_-_benoit_mandelbrot.pdf` | Heavy tails, scaling, non-Gaussian risk and regime fragility | B7 stress tests and portfolio limits |
| `The_evolution_of_risk_management.pdf` | Risk governance and evolution beyond a single metric | B7 risk kernel and B9 independent risk |

## 2. Source-use rules

1. Manuals and books are research inputs, not executable specifications.
2. Any numeric threshold copied into a strategy must cite source location, unit, instrument, timeframe, version and intended scope.
3. Reported win rates, returns, drawdowns or calibration are `SOURCE_CLAIM` until reproduced.
4. Reproduction uses point-in-time data, genuine engine path, realistic costs/fills, holdout, walk-forward, stress and independent evidence.
5. Contradictory sources remain visible; OCE does not average them into false consensus.
6. Copyrighted source payloads are not copied into the repository beyond minimal notes and permitted excerpts.
7. A failed reproduction does not erase the source; it records a falsification or scope mismatch.
8. Agent familiarity with a source never substitutes for a traceable citation and test.

## 3. Evidence labels

`SOURCE_CLAIM`, `FORMALIZED_DOCTRINE`, `REPRODUCTION_PENDING`, `REPRODUCED`, `PARTIALLY_REPRODUCED`, `FALSIFIED`, `SCOPE_MISMATCH`, `SUPERSEDED`, and `QUARANTINED`.
