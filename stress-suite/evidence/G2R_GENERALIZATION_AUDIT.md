# G2R Generalization Audit

**Scope:** G2R-01 (§2) — the one-policy claim; G2R-12 scenario-rename metamorphic; cross-policy contract generalization (§11); no-scenario-literal static guard.

## 1. Primary evidence: ONE shared policy

All six scenario packs (S01, S01_WEAK, S02, S03, S04, S05) execute under `scenarios/policies/G2_CORE_PHASE_POLICY.json` (policy_id `G2_CORE_PHASE_POLICY`, status `PROVISIONAL_SCENARIO_TEST_POLICY`). Each pack's `scenario.json` carries `policy_ref` pointing at that single file; the loader (`engine/scenariolib.py`) resolves it and `run_scenario` records `policy_id` per run — every receipt shows `policy_id: G2_CORE_PHASE_POLICY`.

The archived per-scenario policies under `scenarios/archive/per-scenario-policies/` are retained for **forensic comparison only**; the test `test_no_primary_pass_depends_on_archived_per_scenario_policies` proves none of the six primary runs is a pass of an S0X-policy.

## 2. What the shared policy may and may not inspect

Allowed (all generic evidence properties):

- channel grade with canonical LOW/MEDIUM/HIGH ordering (inherited thresholds from the frozen evaluation contract);
- explicit persistence windows;
- structural level (`L1..L6`) and **derived** same-signature recurrence;
- dependency centrality as a **rigour modulator** (more rigor, never immunity);
- data-quality blocker labels (generic vocabulary such as `DATA_QUALITY_DEFECT`);
- unresolved-pattern state;
- prior review history;
- lineage diversity counts;
- explicit resolution conditions.

Forbidden (asserted by static tests `test_shared_policy_file_has_no_scenario_literals` and `test_shared_policy_rules_contain_no_literal_predicates`, which scan every rule's predicates):

- `scenario_id` and any S0X token;
- literal causal signatures (`SIG_C`, …) and literal scopes (`@PARSER`, …);
- mechanism names and expected terminal states.

## 3. Behavioral differences come from evidence/context/contract, not policy specialization

- S01 vs S02: both open WATCH on material tension; only S01 accumulates **persistent, lineage-supported or patch-derived structural** evidence → TRANSFORMATION_WINDOW → RECONSOLIDATION → NEW_STABLE; S02's `DATA_QUALITY_DEFECT` blocker reverses the claim at ESCALATION_REVIEW → NO_CHANGE → STABLE. Same rules, different observable evidence.
- S03 vs S04: the same `core.repair.*` and `core.structural.patch` rules see derived same-signature recurrence ≥3 at L3 in S03 (escalation) vs a single L1 affected surface in S04 (local repair retained).
- S01 vs S05: the same reconsolidation rules produce NEW_STABLE only when a `REPLACEMENT_VALIDATED` resolution exists (S01), and PLURAL_MODEL_STATE only under `PLURAL_NON_DOMINATION` (S05).
- S01 vs S01_WEAK: identical CORE centrality, weaker/non-persistent contradiction → no transformation. Centrality is never the cause.

## 4. Cross-contract generalization (G2X under the shared policy)

`tests/test_g2x_audit.py` replays each scenario A under every other scenario's frozen evaluation contract B (same shared policy, same evidence):

- contract fingerprints always differ between contracts;
- foreign contracts remain frozen and byte-stable before/during/after the replay;
- the foreign run's `behavior_fingerprint` differs from the own-contract run's whenever semantics differ;
- any foreign-run PASS occurs only when behavior is byte-identical to the own-contract run — **no silent inheritance of foreign semantics**;
- with G2R-06 admissibility enforcement, an M5-legal but contract-forbidden edge is stopped at propose time and **recorded** as a `CONTRACT_INADMISSIBLE` hold (never silently dropped, never applied).

The G2X audit test `test_audit_covers_all_pairs` verifies every ordered pair of the main scenarios is exercised.

## 5. Scenario-rename metamorphic (G2R-12)

`test_rename_scenario_preserves_behavior_fingerprint` reruns S01 with `scenario_id` replaced by `RANDOM_NAME_937`, leaving every decision-grade input identical:

- `run-identity fingerprint` (which legitimately includes `scenario_id` for artifact identity) **does change**;
- `behavior_fingerprint` (excludes `scenario_id` and post-hoc expectations) **does not change**;
- the phase trace, holds, applied transitions and terminal knowledge states are identical.

## 6. Expected-trace and hidden-ground-truth sealing

`decision_view()` strips `hidden_ground_truth`, `expected_phase_path`, `expected_terminal_knowledge` and `terminal_states` from the spec before the run; `evaluate_expectation()` applies expectations strictly after execution. G2-era metamorphic tests (wrong expected trace / changed hidden ground truth) still pass on the G2R engine under the shared policy — flipping either never alters the actual trace.

## 7. Verdict

**PASS.** One shared, scenario-agnostic policy reproduces all six designed outcomes from evidence; behavioral divergence is carried by evidence/context/frozen-contract semantics; scenario rename is behavior-neutral.