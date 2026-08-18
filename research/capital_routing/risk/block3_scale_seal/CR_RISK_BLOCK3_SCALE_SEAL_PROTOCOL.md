# CR-RISK-BLOCK-III-SCALE-SEAL -- Protocol (frozen before synthesis)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** a58f84833b920175f88a5e5c6c127a12bd5cdafe (CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER)
**Type:** SYNTHESIS CHECKPOINT -- no new optimization, no new Monte Carlo.

## Mission
Freeze the scientifically-supported STATIC SCALE OPERATING REGION from the
completed Block-III frontier.  The output is an OPERATING BAND (never a best
cell), plus a single PREFERRED RESEARCH DEFAULT only if the evidence supports
a clear stable midpoint (for future demo translation -- NOT production sizing).

## Frozen inputs (all written by the frontier checkpoint)
MC surface (1680 rows), historical surface (560), edge survival, knee
analysis, paired H1-vs-H0 (common random numbers), dependency sensitivity,
region classification, frontier decision + nonregression JSONs.  SHA-256 of
every input is recorded in CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json.

## Scale bands (pre-registered form, confirmed by frontier evidence)
- CONSERVATIVE: 0.25-0.50  (ROBUST_LOW_SCALE)
- ROBUST CORE:  0.75-1.00   (ROBUST_GROWTH_REGION)
- AGGRESSIVE:   1.50-2.00    (AGGRESSIVE_FRAGILE)
- STRESS ONLY:  3.00        (never promoted)

## Allocation principle
Prefer diversified allocation when its tail/risk efficiency is close to (or
better than) A-only.  Do NOT choose A-only because headline CAGR is larger.
A0 50/50, A1 70/30 are operating; A2 100/0 A is a concentration reference
(diagnostic alongside A3 B-only) unless its tail efficiency is competitive.

## Heat seal principle
Retain H1 only when paired common-random-number evidence shows repeatable
meaningful tail reduction for a reasonable growth cost.  H1 caps that never
bind buy nothing and are not retained as operating layers.  Possible
conclusions: H0 sufficient / H1 preferred / H1 optional safety layer -- the
paired evidence decides.  H0 is always retained as the documented
unconstrained diagnostic.

## Edge retention
Operating band must survive 100% and 75% retained edge robustly (block AND
episode), have interpretable 50% behavior, and 25% is recorded as the
ALPHA-LOSS BOUNDARY (not required to survive).

## Dependency agreement
Block and episode are co-primary.  A band is not sealable if block says
robust but episode says fragile (or vice versa).  Require directional
agreement on growth, tail DD, DD probabilities, edge-decay behavior.

## Knee + adjacent scale
Knee band = modal interval from the frozen knee analysis (expected
[1.00, 1.50]); the robust core must sit below the knee start.  Adjacent
scale steps 0.50->0.75, 0.75->1.00, 1.00->1.50, 1.50->2.00 report incremental
median CAGR, p95 DD, P(DD>=10), P(DD>=15).  The seal identifies where
marginal risk accelerates faster than marginal growth (expected at
1.00->1.50, NOT inside the robust core).

## No best cell
No single maximum-CAGR selection.  No Sharpe/Calmar/PF optimization.  No
dynamic sizing, no Kelly, no DD-adaptive sizing, no live deployment, no
broker sizing, no MT5.  No $ risk / lot size / broker orders.

## Pass gate
block3_scale_seal_pass = true ONLY IF: frontier nonregression PASS;
block+episode agreement PASS within the robust core (no dependency-sensitive
cells in the band); knee seal PASS (robust core below knee); adjacent scale
seal PASS (no tail acceleration inside the core, acceleration at the
1.00->1.50 boundary); 100%+75% edge survival in the band; no best-cell
selection; no Kelly / DD-adaptive / production / deployment / MT5
authorization.
