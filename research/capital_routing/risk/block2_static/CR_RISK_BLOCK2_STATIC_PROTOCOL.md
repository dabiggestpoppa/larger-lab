# CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — Protocol (frozen before results)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** 8abb7c21e907254f75618deb3c9095c971c6b9be

## Mission
Freeze the simplest portfolio-risk architecture supported by R1-R6 evidence.
This is a synthesis / seal / decision checkpoint — NOT a new science checkpoint.

## Target architecture (candidate to freeze)
```
VALID ALPHA EVENTS
  -> FAMILY CLASSIFICATION
  -> STATIC FAMILY ALLOCATION
  -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT
  -> PORTFOLIO
```
No dynamic drawdown rule, no episode memory budget, no Kelly, no hybrid
policy, no state machine for sizing.

## Frozen definitions
- **Per-event f** = base_f * family_weight(family). base_f in percent units
  (1.0 == 1% of account). 1R is one-sigma expected 6h move, NOT a stop-loss.
- **Gross heat** = sum of admitted active event fractions.
- **Canonical heat mechanism** = H1_SIMPLE_GROSS_HEAT_CAP.
- **Causal admission**: before admitting a new event, only information known at
  entry time is inspected (active positions that entered strictly earlier).
  Decisions: ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP.

## Frozen reference allocations (no winner)
50/50 (diversification), 70/30 (A-heavy robust), 100/0 A (edge-resilience
concentration). 0/100 B remains diagnostic only.

## Reference parity targets (frozen R6 corrected frontier)
- H0 50/50 f=1%: CAGR ~71.21%, max DD ~5.19%
- H0 50/50 f=2%: CAGR ~190.31%, max DD ~10.17%
- H0 70/30 f=1%: CAGR ~74.57%, max DD ~6.97%
- H0 100/0 A f=1%: CAGR ~79.15%, max DD ~10.30%
- H1 70/30 1.0x: reproduce frozen R6 admission decisions (64 rejected events)
  and corrected block-MC (p95 DD ~9.5% -> ~6.3%, P(DD>=10%) ~3.6% -> 0.0%).

## Frozen policy roles
- H0: KEEP_AS_UNCONSTRAINED_CONTROL
- H1: ADOPT_AS_CANONICAL_SIMPLE_HEAT_MECHANISM
- H2: PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY
- H3: SECONDARY_OPTIONAL
- H4: PRUNED_REDUNDANT
- H5: DEFERRED_COMPLEXITY

## Forbidden
No new allocations, no new caps, no new policy families, no R7 (DD-adaptive),
no Kelly, no hybrid sizing, no CAGR/DD search, no alpha/entry/exit changes.
No production allocation / cap / size selection.

## Pass gate
cr_risk_block2_static_architecture_seal_pass = true ONLY IF: Block-I chain
intact; R5/R6 findings reproduced; 890 events / 432 A / 458 B / 482 episodes /
max concurrency 3 reconcile; static allocation + H1 gross cap explicitly
defined; no final allocation/cap/size selected; H2/H3/H4/H5 roles frozen
correctly; edge-retention constraint frozen; no R7/Kelly work; alpha unchanged;
reference parity passes; causal admission passes; tests pass.
