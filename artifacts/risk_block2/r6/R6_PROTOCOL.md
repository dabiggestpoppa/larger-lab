# R6 PROTOCOL (pre-registered)

**Task:** CR-RISK-BLOCK2-R6-EPISODE-HEAT-SIZING · **Base:** Block-I seal 8ca072d0 · R5 150a93de ·
branch `capital-routing`

## Frozen inputs
Sealed 890-event A/B book (A 432 / B 458) rebuilt from the SAME frozen inputs
as Block-I/R5 and cross-checked against R1_EVENT_RISK_LEDGER.csv. Episodes use
the R1 12h cluster framework (interval_h = 12); cluster membership reconciled
with R1_ROUTING_EPISODES.csv.

## Predefined policy surface (VIII, frozen BEFORE results)
H0 unconstrained; H1 gross heat cap; H2 same-direction heat cap; H3 family-B
heat cap; H4 12h episode budget; H5 hybrid (gross + same-direction).
Cap multiples: H1 1.0/1.5/2.0/3.0x, H2 1.0/1.5/2.0x, H3 0.5/0.75/1.0x,
H4 1.0/1.5/2.0/3.0x, H5 (1.5,1.0)/(2.0,1.5)x. Treatments: REJECT_NEW on the
full grid; SCALE_NEW_TO_REMAINING_CAP on a pre-registered subset (H1 1.0/1.5/2.0,
H2 1.0/1.5, H3 0.5/0.75, H4 1.0/1.5, H5 both). 28 core configurations <= 50.
No post-hoc additions.

## Allocations (X)
50/50 (primary), 70/30, 100/0 (reference). Total portfolio heat held
comparable: an event requests base_f x w_family.

## f levels (VII)
Historical frontier: 0.25/0.50/0.75/1.00/1.50/2.00%. MC: 0.50/1.00/2.00%.

## Monte Carlo (XVIII, XIX) â€” pre-registered path counts
- 50/50: 11 policies; block bootstrap 8000 paths
  (core {H0, H1-1.5, H2-1.5, H3-0.75, H4-1.5, H5-1.5}), 4,000 for the rest;
  episode bootstrap 3000 paths.
- 70/30: 8 policies (same core split).
- iid: reference only (H0, 50/50, 3,000 paths).
- Edge degradation: 50/50, f=1%, block 2,000 paths, 8 scenarios
  {(1,1),(0.75,0.75),(0.5,1),(1,0.5),(0.5,0.5),(0.25,0.25),(0.75,0.5),(0.5,0.75)}.
- Deterministic seed 20260815 everywhere.

## Tail / cluster stress (XX, frozen)
worst5_x1_5 and worst5_x2 (worst 5% losses scaled x1.5 / x2), insert_worst_1,
insert_p99_loss_cluster (5 p99-magnitude loss bleeds), worstA_cluster /
worstB_cluster / mixed_AB_cluster (worst 12h clusters by composition).
Adversarial episode patterns (XXI): A loss->B loss, B loss->B loss,
A loss->A loss->B loss, 3 same-direction losses, mixed-direction losses,
B-heavy, A+B cluster. Reported per variant: max DD, p95 DD, worst day /
worst episode, CAE, technical-ruin probability, return sacrifice.

## Temporal partitions (XXIII, frozen)
split (inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS) and calendar year;
per partition report rejection rate, mean admitted f, max gross heat, CAGR,
max DD, worst episode, tail loss; classified STABLE / MIXED / UNSTABLE.

## Admission semantics (XI)
Chronological by entry; active heat computed immediately BEFORE entry; ties
ordered by (entry, exit, event_id) (documented, deterministic). Decisions:
ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP with exact reason. Existing
positions are never modified.

## Evaluation metrics (XIII)
CAGR, total return, max DD, Calmar, Sortino, worst day/24h/48h, worst episode,
ulcer index, recovery factor, p95/p99 DD, P(DD>=10/15/20/30/40%), technical
ruin, gross-heat distribution.

## Allowed / forbidden
Allowed: episode reconstruction, heat definitions, causal admission,
historical frontier, directional/family overlap anatomy, dependency-aware MC,
edge/tail stress, rejected-event audit, temporal stability, non-dominated
frontier mapping. Forbidden: searching policies for max Calmar/CAGR,
optimizing cap multiples, selecting a "best policy", Kelly, DD-adaptive or
dynamic sizing, episode-aware sizing, deployment, MT5, any alpha/entry/exit/
trade-management change.

## PASS criteria (XXX)
Episode reconstruction reconciles with R1; policies causal; heat accounting
exact; H0 reproduces the sealed baseline; surface complete; MC complete;
edge/tail stress complete; temporal stability complete; non-dominated frontier
complete; no best policy selected; repo tests pass. A null result is
acceptable: if heat caps do not materially help, that is the finding.
