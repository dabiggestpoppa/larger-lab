# CR-RISK-BLOCK-II-INTERMEDIATE-SEAL — Protocol (pre-registered)

**Task:** CR-RISK-BLOCK-II-INTERMEDIATE-SEAL · **Base:** 0cb3b510 · R6 1e8cc01f ·
R5 150a93de · Block-I 8ca072d0 · branch `capital-routing`

## Purpose
Synthesize and freeze the Block-II findings (R5 family quality/allocation +
R6 episode/heat sizing) and decide whether simple static family allocation +
simple static simultaneous-heat caps already solve the material
portfolio-risk problem. This is a SEAL / DECISION checkpoint — NOT a new
optimization phase. No new policy grids, no new allocations, no new cap
values, no DD-adaptive / Kelly / hybrid runs, no alpha/entry/exit changes.

## Frozen inputs (R5/R6/Block-I artifacts only)
R5_DECISION.json, R5_FAMILY_DISTRIBUTIONS.csv, R5_ALLOCATION_FRONTIER.csv,
R5_FAMILY_DEPENDENCY.csv, R5_FAMILY_EDGE_DEGRADATION.csv,
R6_DECISION.json, R6_EVENT_EPISODE_LEDGER.csv, R6_OVERLAP_ANATOMY.csv,
R6_HEAT_POLICY_FRONTIER.csv, R6_HEAT_POLICY_MONTE_CARLO.csv,
R6_NONDOMINATED_HEAT_FRONTIER.csv, R6_EVIDENCE_STATUS_MATRIX.csv,
R6_POLICY_COMPLEXITY_MATRIX.csv, R1_EVENT_RISK_LEDGER.csv,
R1_CONCURRENCY_SUMMARY.csv, BLOCK1_DECISION.json.

## Integrity recheck (deterministic, frozen artifacts only)
890 events / 482 episodes / max concurrency 3; R1 ledger row count;
H0 baseline reproduction (50/50 f=1% ~71.2%/5.2%, f=2% ~190.3%/10.2%,
70/30 ~74.6%/7.0%, 100/0 ~79.2%/10.3%); R5 family metrics; R6 corrected MC
(zero duplicate policy/scheme/alloc/f keys); corrected frontier (H0
block-MC 50/50 f=1 DOMINATED); single-position share of in-DD loss ~84.7%
vs multi-position ~15.3%.

## Five seal questions (Q1-Q5)
Q1 family-allocation conclusions actually supported; Q2 heat controls
actually supported; Q3 episode budgeting necessary?; Q4 B-specific treatment
necessary?; Q5 enough unresolved state-dependent risk to justify R7
DD-adaptive? Q5 is NOT assumed YES.

## Classification vocabulary
ADOPT_AS_REFERENCE / SUPPORTED / OPTIONAL / REDUNDANT / DEFERRED / REJECTED.
Complexity must earn its place: LEVEL 0 H0 < LEVEL 1 gross cap < LEVEL 2
same-direction / B-family < LEVEL 3 episode budget < LEVEL 4 combined.

## Forbidden
Selecting best allocation / best heat policy / best size; running new
policies; DD-adaptive testing; Kelly; deployment authority; MT5; any alpha
change. The seal defines a SUPPORTED DESIGN REGION, never one production
point.

## PASS gate
R5 frozen correctly; R6 frozen correctly; corrected MC/frontier used;
890/482/3 reconcile; H0 baseline preserved; every component classification
explicit; episode budget REDUNDANT unless evidence changed; no best policy;
no DD-adaptive; no Kelly; no deployment; complexity pruning complete; R7
necessity explicitly assessed; repo tests pass.
