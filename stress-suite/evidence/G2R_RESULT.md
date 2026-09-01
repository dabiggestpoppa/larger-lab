# G2R — Generalization + Evidence-Integrity Hardening

**STATUS: `PASS_G2R_GENERALIZATION_AND_EVIDENCE_INTEGRITY`**

## Gate bookkeeping

| field | value |
|---|---|
| starting SHA | `3bca154b` (actual branch head — includes the `STRESS-G2PR` exec-bit repair; the prompt's stated `38b3e031` predates it) |
| ending SHA | `e691a316` code head; terminal receipt pinned by `STRESS-G2RR2` (see receipt) |
| prior status | `PASS_G0_PLANNING_INGESTION` → `PASS_G1_HARNESS_CONTRACTS` → `PASS_G1R_HARNESS_HARDENING` → `PASS_G2_CORE_PHASE_CONTROL` |
| tests | **278 / 278** — 224 old preserved + 1 legacy renamed with documented rationale + 54 new adversarial regressions |
| cost | $0 (local only; no model calls, no cloud) |
| mutations | cloud=0 · production=0 · capital=0 · authority=NONE |

## What G2R changed

1. **G2R-01 — one shared policy.** All six packs (S01, S01_WEAK, S02, S03, S04, S05) now execute under a single `G2_CORE_PHASE_POLICY` whose predicates are purely generic evidence properties — channel grades, persistence floors from the frozen contract, structural level, **derived** causal-signature recurrence, dependency centrality as a rigour modulator, data-quality blocker labels, unresolved-pattern state, prior review history, lineage diversity, explicit resolution conditions. No `scenario_id`, no literal `SIG_C` / `@PARSER` / mechanism names, no outcome-shaped ladders. Per-scenario policies are archived for forensics only and no primary PASS depends on them (asserted by test).
2. **G2R-02 — execution-grade evidence registry.** `observable_evidence.json` is no longer informational: every `evidence_ref` resolves against a governed `EvidenceRegistry` built before adjudication. Unknown refs fail closed; duplicate conflicting ids fail closed; provenance survives.
3. **G2R-03 — derived patch recurrence.** Recurrence is computed from the ordered exact-signature patch history. A caller lying `recurrence=99` on one event gets a derived `1`; four same-signature events fire the structural gate only at derived count 4; unrelated signatures never aggregate.
4. **G2R-04/07/08 — role-to-action + operator-required.** M5 phase mutation is the GOVERNOR path only; `WORKER`/`PO` actors with legitimately-seeded enum levels cannot drive the phase machine. `operator_required` transitions are truly permission-gated by `OPERATOR_AUTHORIZE` (bound to `to_state`), grant action permission only, and never mutate evidence or authority.
5. **G2R-05/09 — ratification integrity.** Ratifying a grant that was never proposed fails closed (`NO_PRIOR_PROPOSAL`); broker risk-class grants require the same operator ratification as deployment/destructive/capital.
6. **G2R-06/10 — contracts fully semantic.** `hysteresis_rules` are structured, machine-readable and participate (minimum-persistence floors per phase family; `stronger_than_watch`; `independent_exit_predicate`); prose-as-rule fails closed; a non-empty `admissible_phase_transitions` list blocks M5-legal edges at propose time with a recorded `CONTRACT_INADMISSIBLE` hold.
7. **G2R-11/12 — audit + fingerprints.** Every applied transition carries a full linkage audit (`explain_transition`): refs exist, permitted input objects, contract + policy fingerprints, valid authority actor, authorized role, contract-admissible, M5-topology-legal. `behavior_fingerprint` excludes `scenario_id` and expectations; a rename changes nothing about behavior.
8. **G2R-09 label.** Scripted M4 lifecycle actions in S01/S02/S05 are marked `FIXTURE_SIDE_EFFECT` — the harness proves those actions are *legal and evidence-bound*, not that OCE autonomously discovered the knowledge disposition.
9. **AMB-13.** Resolution semantics are represented through `ResolutionCondition` (PROVISIONAL_TEST_OBJECT: `REPLACEMENT_VALIDATED`, `PLURAL_NON_DOMINATION`) — no A-010 channel invented, AMB-13 stays OPEN.

## Scenario outcomes under the shared core policy

| scenario | terminal | trace | verdict |
|---|---|---|---|
| S01 Old Theory Dies Slowly | `NEW_STABLE` | STABLE→WATCH→STABLE→WATCH→ESCALATION_REVIEW→TRANSFORMATION_CANDIDATE→TRANSFORMATION_WINDOW→RECONSOLIDATION→NEW_STABLE | PASS (centrality raises rigour, never immunity; TC via **derived patch pressure** SIG_M L3 ×4 — a signature-recurrence topology, not an independent-confirmation claim) |
| S01_WEAK (same CORE centrality, weak contradiction) | `STABLE` | STABLE→WATCH→STABLE→WATCH→STABLE | PASS — **no transformation**: centrality is not the cause |
| S02 False Revolution | `STABLE` | STABLE→WATCH→ESCALATION_REVIEW→NO_CHANGE→STABLE | PASS — `DATA_QUALITY_DEFECT` blocker reverses the claim; anomaly + lineage retained; claim DEMOTED with reopen condition |
| S03 Patch Maze | `TRANSFORMATION_CANDIDATE` | …→HOMEOSTATIC_REPAIR ×2 cycles…→ESCALATION_REVIEW→TC | PASS — L3 same-signature (derived 8) escalates; unrelated SIG_X with lying `recurrence=99` never aggregates; no L6 |
| S04 Leaf Failure | `STABLE` | STABLE→WATCH→ESCALATION_REVIEW→HOMEOSTATIC_REPAIR→STABLE | PASS — L1 affected surface repaired locally; no ontology mutation |
| S05 Two Non-Dominated Models | `STABLE` + plural knowledge | STABLE→WATCH→ESCALATION_REVIEW→TC→TRANSFORMATION_WINDOW→RECONSOLIDATION→PLURAL_MODEL_STATE→STABLE | PASS — no averaging, no forced winner; M_A + M_B both ACTIVE (M4/M5 separation intact) |

All runs: `forbidden_attempts=0`, `evidence_ref_violations=0`, evaluation contract frozen before the first adjudicated decision, fingerprints byte-reproducible across reruns.

## Legacy corrections (each with inline rationale in the test source; none weakened)

- `test_g2p0::test_operator_actor_can_ratify_with_valid_grant` — ratification now requires a **prior proposal** (old behavior fabricated a grant at ratification time — exactly G2R-05's defect).
- `test_g2x_audit::test_s02_under_s01_contract_keeps_entry_but_changes_nothing_critical` → renamed `…_diverges_on_admissibility` — the old claim became false once G2R-06 made admissible lists enforceable; the new test asserts the recorded `CONTRACT_INADMISSIBLE` hold.
- `test_g2_scenarios` — scenario runs bind the governed evidence registry (G2R-02); receipt-consistency still compares fresh runs byte-for-byte.
- smoke `illegal_transition_smoke` — M5 attempts now come from a GOVERNOR-level actor so the smoke's intent is topology rejection, not role rejection.

## Open architecture questions (carried forward, NOT resolved)

CON-02 (PO posture vs Governor) · CON-03 (threshold transparency vs Goodhart) · AMB-03 (authoritative independence aggregation) · AMB-08 (reversible low-scope transformation boundary) · AMB-11 (automated causal-signature discovery) · AMB-13 (replacement-validated resolution semantics — represented, not solved).

## Recommended next action

`AUTHORIZE_G3` — cognitive ecology (S06–S09), where the independence-lineage vector built here becomes the testable surface.