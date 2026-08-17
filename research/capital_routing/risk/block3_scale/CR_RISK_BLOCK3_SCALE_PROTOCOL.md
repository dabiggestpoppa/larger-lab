# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Protocol (frozen before results)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** 637d98cfde13de587b0a8ec30d3fe0957f134dca

## Mission
Design and freeze the scientific contract for studying ACCOUNT-LEVEL CAPITAL
SCALE on top of the already validated static risk architecture. This is the
laboratory for the next frontier run (CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER). It does NOT select the answer.

## Primary sizing variable
- **f_total** = TOTAL PORTFOLIO BASE RISK FRACTION (percent units;
  1.0 == 1% of account). Allocation distributes f_total between families:
  event fraction = family_weight(family) * f_total.
- 50/50 with f_total = 1.0% -> A receives 0.5%, B receives 0.5%.
- 70/30 with f_total = 1.0% -> A receives 0.7%, B receives 0.3%.
- f_total is NEVER interpreted as per-family risk.

## Frozen scale ladder (broad regions, not exact peaks)
0.25%, 0.50%, 0.75%, 1.00%, 1.50%, 2.00%; outer stress 3.00%.
No fine-grained optimization grid (0.01%, 0.02%, ...).

## Allocation references (no winner)
A0 50/50 (diversification), A1 70/30 (A-heavy robust), A2 100/0 A
(edge-resilience concentration). A3 0/100 B diagnostic only.

## Heat references (previously frozen R6 H1 configurations ONLY)
H0 (unconstrained diagnostic) + H1 gross caps at
H1-1.00-REJ, H1-1.50-REJ, H1-2.00-REJ, H1-3.00-REJ.
Cap units are multiples of f_total (the cap scales linearly with f_total).
No new heat-cap levels are created in this checkpoint.

## Edge retention states
100%, 75%, 50%, 25% — scenario states, no
subjective probabilities. Degradation reuses the sealed R5/R6 semantics:
positive returns scaled per family. It is a STRESS TRANSFORM on realized
outcome streams; it never feeds back into event selection or admission.

## Monte Carlo contract
Schemes: block + episode (primary, dependency-aware), iid (diagnostic only).
Primary path requirement: >= 10000 paths for frontier experiments
(frozen; executed in CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER). Seeds frozen and reported. This D0 checkpoint
runs a small deterministic pilot only.

## Empirical Kelly (diagnostic reference ONLY)
- Method: empirical expected-log-growth on the event return distribution.
- Fractions reported: full, 1/2, 1/4, 1/8.
- Uncertainty: bootstrapped (median / p10 / p25 / p75 / p90).
- Kelly is NEVER executed, NEVER selected, NEVER authorized.
- Kelly cannot override family allocation, the H1 heat limit, or hard risk
  constraints.

## Risk envelopes
Research envelopes E5 / E10 / E15 / E20 / E25 / E30 (max-DD percent).
For each scale/configuration report whether historical and resampled metrics
clear each envelope. Human review chooses the eventual production tolerance.

## Compounding
Geometric account equity; each admitted event impacts equity by its allocated
fraction * realized R. No additive-CAGR shortcuts. No mixing percent and
decimal units. Any path producing invalid equity is flagged INSOLVENT_PATH
(never clipped to zero silently).

## Causality (forbidden inputs to admission/sizing at event t)
Future returns, future episode labels, future DD, drawdown state, recent wins,
recent losses, future volatility. Only configuration, family, timestamp,
current equity, currently active admitted events, current gross heat.

## Forbidden in this checkpoint
New allocations, new caps, new policy families, DD-adaptive sizing, episode
budgets, H2/H3/H4/H5 optimization, changing alpha / trade management / family
definitions, running the full frontier, selecting a production configuration.

## Pass gate
block3_design_pass = true ONLY IF: Block-II static architecture unchanged;
890 events / 432 A / 458 B / 482 episodes reconcile; scale semantics explicit
and unit-tested (f_total vs family-f); compounding semantics explicit; H0/H1
frozen parity passes; scale ladder frozen; edge-retention states frozen;
dependency-aware MC contract frozen; >= 10k final-path requirement frozen;
risk-threshold ladder frozen; growth-efficiency metrics frozen; Kelly defined
only as diagnostic and NOT authorized; causality passes; future perturbation
passes; truncation passes; no new heat policy; no DD-adaptive sizing; no best
scale / allocation / production configuration selected; no deployment
authorization; tests pass.
