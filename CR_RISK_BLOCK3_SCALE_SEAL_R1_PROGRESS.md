# CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE — Progress

**Repo:** dabiggestpoppa/larger-lab · **Branch:** capital-routing
**Base:** `78dca3a7` (CR-RISK-BLOCK-III-SCALE-SEAL — ACCEPTED)
**Checkpoint:** `CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE`

## Status: COMPLETE ✅

- **Nonregression (science frozen):** 18/18 fields reproduce EXACTLY the
  ACCEPTED values (bands, knee [1.0,1.5], allowed allocations, operating heat
  H1-1.00-REJ, preferred default A1_70_30/H1-1.00-REJ/1.00, robust-core
  contract 0.4814-0.7038 / 0.0474-0.0829 / 0.0-0.0072 / 0.0, edge 100/75/50
  survive, 25 does not) — verified against BOTH the sealed artifacts and the
  frozen brief expectations.
- **Gate test:** positive control PASS + all 11 mandated negative injections
  fail closed (seal=false, status=FAIL, exact failure recorded).
- **Tests:** 35 new (`tests/test_risk_block3_scale_seal_r1.py`) exercising the
  decision gate directly (not the artifact) · seal suite 51/51.

## Defects repaired

1. **Defect 1 — nonregression now in the pass expression.**
   `block3_scale_seal_pass = true` ONLY IF all required gates pass:
   `frontier_nonregression_pass AND block_episode_agreement_pass AND
   knee_seal_pass AND adjacent_scale_seal_pass AND survives_100_edge AND
   survives_75_edge AND no prohibited authorization state`.
2. **Defect 2 — status derived.** `status` is computed from
   `block3_scale_seal_pass` by `fail_closed_gate()`; never hardcoded.
3. **Fail-closed auth invariants.** kelly / dd-adaptive / production /
   deployment / MT5 all remain FALSE; any TRUE blocks PASS.
4. **Gate reasons.** Every decision carries machine-readable
   `seal_gate_failures` / `seal_gate_passes` / `authorization_invariants_failed`.

## Where the repair lives

- `src/capital_routing/capital_scale_seal.py` — new pure `fail_closed_gate()`
  and `build_scale_seal_decision()` (single decision path, shared by the
  canonical seal runner and the R1 runner).
- `scripts/run_risk_block3_scale_seal.py` — `_decision()` now delegates to the
  builder (mechanics repaired in code; frozen artifacts untouched).
- `scripts/run_risk_block3_scale_seal_r1.py` — R1 runner: frozen protocol,
  input hashes (frontier + sealed artifacts), positive nonregression,
  11-injection gate test, repaired decision, report.
- `tests/test_risk_block3_scale_seal_r1.py` — 35 tests.

## Artifacts (research/capital_routing/risk/block3_scale_seal_r1/)

- CR_RISK_BLOCK3_SCALE_SEAL_R1_PROTOCOL.md
- CR_RISK_BLOCK3_SCALE_SEAL_R1_INPUT_HASHES.json
- CR_RISK_BLOCK3_SCALE_SEAL_R1_NONREGRESSION.json
- CR_RISK_BLOCK3_SCALE_SEAL_R1_GATE_TEST.json
- CR_RISK_BLOCK3_SCALE_SEAL_R1_REPORT.md
- CR_RISK_BLOCK3_SCALE_SEAL_R1_DECISION.json

## Decision (R1)

status=PASS · block3_scale_seal_pass=true · seal_gate_failures=[] ·
seal_gate_passes=[frontier_nonregression_pass, block_episode_agreement_pass,
knee_seal_pass, adjacent_scale_seal_pass, survives_100_edge, survives_75_edge]
· authorizations all FALSE · next_checkpoint_recommended =
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING (not authorized).

## Scope honored

No new MC · no frontier change · no band/allocation/heat/f_total/edge-logic
change · no preferred-default change · no Kelly · no DD adaptation · no
deployment · no MT5. **BLOCK III IS FULLY SEALED.** Stopped for human review.
