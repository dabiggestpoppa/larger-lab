# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Report

**Status:** PASS · **Base:** 637d98cfde13de587b0a8ec30d3fe0957f134dca

## 1. Integrity recheck
- Events: **890** (A 432 / B 458) · Episodes: **482** · Max concurrency: **3**
- R1 12h episodes reconcile: True · Block-II static seal intact: True

## 2. Engine validation (frozen parity)
| allocation | f_total | policy | CAGR % | max DD % | match |
|---|---|---|---|---|---|
| A0_50_50 | 1.00 | H0 | 71.21 | 5.19 | True |
| A0_50_50 | 2.00 | H0 | 190.31 | 10.17 | True |
| A1_70_30 | 1.00 | H0 | 74.57 | 6.97 | True |
| A2_100_0_A | 1.00 | H0 | 79.15 | 10.30 | True |

Admission parity (static engine vs frozen R6 ledger): 15/15 configurations exact (decisions + admitted f).

## 3. Causality audit
- Future perturbation (mutate returns after cutoff 2025-04-01 07:48:00+00:00): admission identical = True, equity before cutoff identical = True, after cutoff differs = True → **PASS**
- Truncation (534 events through cutoff): decisions True, equity through cutoff True → **PASS**

## 4. Monte Carlo pilot (deterministic pipeline proof)
- Schemes: block / episode / iid · paths block=250 episode=150 iid=150 · seed 20260815
- Pilot rows: 6 · total paths: 1100
- H0 50/50 f=1.00 block: median CAGR 70.6%, p95 max DD 8.27%, P(DD≥10%) 0.8%
- H0 50/50 f=1.00 episode: median CAGR 71.3%, p95 max DD 8.19%, P(DD≥10%) 0.7%
- H0 50/50 f=1.00 iid: median CAGR 70.9%, p95 max DD 7.61%, P(DD≥10%) 0.7%
- H1-1.00-REJ 70/30 f=1.00 block: median CAGR 69.2%, p95 max DD 6.34%, P(DD≥10%) 0.0%
- H1-1.00-REJ 70/30 f=1.00 episode: median CAGR 68.8%, p95 max DD 7.15%, P(DD≥10%) 0.0%
- H1-1.00-REJ 70/30 f=1.00 iid: median CAGR 73.3%, p95 max DD 8.24%, P(DD≥10%) 2.7%

## 5. Kelly diagnostic reference (NOT authorized)
Empirical expected-log-growth Kelly f* (percent of account) with bootstrapped uncertainty. Diagnostic only — never executed, never selected.

| edge | scope | f* % | 1/2 % | 1/4 % | 1/8 % | med % | p10 % | p90 % | class |
|---|---|---|---|---|---|---|---|---|---|
| 25% | A_only | 0.1 | 0.1 | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 | UNSTABLE_REFERENCE |
| 25% | B_only | 0.1 | 0.1 | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 | UNSTABLE_REFERENCE |
| 25% | pooled | 0.1 | 0.1 | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 | UNSTABLE_REFERENCE |
| 50% | A_only | 5.6 | 2.8 | 1.4 | 0.7 | 4.2 | 0.1 | 11.4 | UNSTABLE_REFERENCE |
| 50% | B_only | 0.1 | 0.1 | 0.0 | 0.0 | 0.1 | 0.1 | 6.2 | UNSTABLE_REFERENCE |
| 50% | pooled | 6.2 | 3.1 | 1.6 | 0.8 | 5.3 | 0.1 | 14.8 | UNSTABLE_REFERENCE |
| 75% | A_only | 16.9 | 8.5 | 4.2 | 2.1 | 16.4 | 11.4 | 21.4 | UNSTABLE_REFERENCE |
| 75% | B_only | 13.1 | 6.6 | 3.3 | 1.6 | 13.1 | 6.6 | 18.7 | UNSTABLE_REFERENCE |
| 75% | pooled | 26.5 | 13.2 | 6.6 | 3.3 | 26.1 | 20.3 | 30.0 | UNSTABLE_REFERENCE |
| 100% | A_only | 21.8 | 10.9 | 5.5 | 2.7 | 21.3 | 17.6 | 26.0 | UNSTABLE_REFERENCE |
| 100% | B_only | 19.8 | 9.9 | 5.0 | 2.5 | 20.0 | 14.7 | 24.2 | UNSTABLE_REFERENCE |
| 100% | pooled | 30.0 | 15.0 | 7.5 | 3.8 | 30.0 | 29.9 | 30.0 | UNSTABLE_REFERENCE |

- Kelly is diagnostic only: kelly_execution_authorized = False. Full Kelly sits at/above the grid boundary in several cells (UNSTABLE_REFERENCE) — consistent with the sealed conclusion that edge retention, not leverage, is the binding constraint.

## 6. Frozen experimental contract
- Scale ladder: 0.25, 0.50, 0.75, 1.00, 1.50, 2.00 · outer stress 3.00%
- Allocations: A0_50_50, A1_70_30, A2_100_0_A, A3_0_100_B (A3 diagnostic only)
- Heat: H0 + frozen R6 H1 gross caps (H1-1.00-REJ, H1-1.50-REJ, H1-2.00-REJ, H1-3.00-REJ)
- Edge states: 100%, 75%, 50%, 25%
- MC: block + episode primary, iid diagnostic; >= 10000 paths required for the frontier checkpoint
- Risk envelopes: E5, E10, E15, E20, E25, E30

## 7. Decision
- block3_design_pass = True
- No best scale / allocation / heat cap / production configuration selected (all false).
- No DD-adaptive logic, no new heat policy, no alpha science (all false).
- Deployment / MT5 not authorized. Kelly execution not authorized.
- Next checkpoint: **CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER** (ready but NOT authorized — requires human approval).
