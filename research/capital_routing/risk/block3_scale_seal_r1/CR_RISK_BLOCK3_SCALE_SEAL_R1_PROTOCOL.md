# CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE -- Protocol

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Authoritative base:** 78dca3a7453205241bdbe935b985e3e7be7b8144 (CR-RISK-BLOCK-III-SCALE-SEAL -- ACCEPTED)
**Type:** GOVERNANCE REPAIR -- NO new MC, NO frontier change, NO science change.

## Mission
Perform ONLY a fail-closed truth-gate repair of the final decision/governance
mechanics.  The scientific result is FROZEN and ACCEPTED:

- CONSERVATIVE 0.25-0.50 / ROBUST CORE 0.75-1.00 / AGGRESSIVE 1.50-2.00 /
  STRESS ONLY 3.00
- KNEE 1.00-1.50
- ALLOWED A0_50_50, A1_70_30; DIAGNOSTIC ONLY A2_100_0_A, A3_0_100_B
- OPERATING HEAT H1-1.00-REJ
- PREFERRED RESEARCH DEFAULT A1_70_30 / H1-1.00-REJ / f=1.00 (NOT production)
- ROBUST CORE RISK CONTRACT: median CAGR 0.4814-0.7038; p95 DD 0.0474-0.0829;
  P(DD>=10) 0.0-0.0072; P(DD>=15) 0.0
- Edge: 100/75/50 SURVIVE; 25 DOES NOT SURVIVE (alpha-loss boundary)

## Defect 1 -- nonregression not in the final pass expression
block3_scale_seal_pass = true ONLY IF ALL required gates pass:
frontier_nonregression_pass AND block_episode_agreement_pass AND
knee_seal_pass AND adjacent_scale_seal_pass AND survives_100_edge AND
survives_75_edge AND no prohibited authorization state.

## Defect 2 -- status hardcoded
status is DERIVED: PASS iff block3_scale_seal_pass == true; otherwise FAIL
with explicit reasons in status_reason / seal_gate_failures.

## Fail-closed authorization invariants
No PASS while any of kelly_used, dd_adaptive_used, production_scale_selected,
deployment_authorized, mt5_authorized is true.  All remain FALSE.

## Gate reasons
Every decision carries machine-readable seal_gate_failures and
seal_gate_passes lists (failures = [] on PASS).

## Negative tests (exercise the gate, not the artifact)
1 frontier_nonregression=false -> seal=false -> status != PASS
2 block_episode_agreement=false -> seal=false
3 knee_seal=false -> seal=false
4 adjacent_scale_seal=false -> seal=false
5 survives_100=false -> seal=false
6 survives_75=false -> seal=false
7 kelly_used=true -> seal=false
8 dd_adaptive_used=true -> seal=false
9 production_scale_selected=true -> seal=false
10 deployment_authorized=true -> seal=false
11 mt5_authorized=true -> seal=false

## Positive nonregression
On the frozen inputs the scientific outputs must reproduce EXACTLY the
ACCEPTED values listed above (recomputed from the frozen frontier artifacts
via the same pure functions, compared to the sealed artifacts AND the frozen
brief expectations).

## Not done here
No re-run of MC, no band/allocation/heat/f_total/edge-logic changes, no
preferred-default change, no Kelly, no DD adaptation, no deployment, no MT5,
no execution translation.
